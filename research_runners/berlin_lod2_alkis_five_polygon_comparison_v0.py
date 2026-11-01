#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two frozen official Berlin WFS requests: bounded 2026 ALKIS vs 2022 LoD2.

Compares at most 5 polygons per service *geometrically* by independent
intersection-over-union. It does not match original feature IDs, addresses
or names, assume a common vintage, persist provider bytes or claim the five
features represent the complete 200m source query box.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import parse, request, error

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import (
    BBOX, MAX_BYTES, TIMEOUT, URL as ALKIS_URL,
    _object, _reject_constant, inspect_building_geojson,
)

HEIGHT_ROOT = "https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen"
HEIGHT_LAYER = "ua_gebaeudehoehen:gebaeudehoehen"
EPSG = "EPSG:25833"
HEIGHT_PARAMS = (
    ("service","WFS"),("version","2.0.0"),("request","GetFeature"),
    ("typeNames",HEIGHT_LAYER),("count","5"),("srsName",EPSG),
    ("bbox",",".join(str(x) for x in BBOX)+","+EPSG),
    ("outputFormat","application/json"),
)
HEIGHT_URL = HEIGHT_ROOT + "?" + parse.urlencode(HEIGHT_PARAMS)
PROFILE = "oc-berlin-lod2-2022-to-alkis-2026-frozen-five-pair-v0"
MAX_FEATURES = 5
# High threshold for near-identical source footprints, not a rule for
# associating separate buildings by proximity.
MIN_IOU = 0.95
SOURCE_CRS = frozenset((
    "EPSG:25833","urn:ogc:def:crs:EPSG::25833",
    "urn:ogc:def:crs:EPSG:6.9:25833",
))
HEIGHT_FIELDS = ("hoehe","role_txt","dachart","geschosse",
                 "quellebodenhoehe","quelledachhoehe","quellelage",
                 "grundrissaktualitaet")


class HeightPairError(ValueError):
    """Source source-identity/CRS, topology or evidence quality violation."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HeightPairError("fixed official WFS URL redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(request.ProxyHandler({}), NoRedirect(),
       request.HTTPSHandler(context=ssl.create_default_context())).open(req, timeout=timeout)


def _parse_height(raw: bytes) -> tuple[list[Any], list[dict]]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise HeightPairError("original height response empty or oversized")
    try:
        obj=json.loads(raw.decode("utf-8"),object_pairs_hook=_object,
                       parse_constant=_reject_constant)
    except (ValueError,UnicodeDecodeError) as exc:
        raise HeightPairError("invalid original height GeoJSON") from exc
    if type(obj) is not dict or obj.get("type") != "FeatureCollection":
        raise HeightPairError("not a height FeatureCollection")
    crs=obj.get("crs")
    if crs is not None:
        if (type(crs) is not dict or crs.get("type")!="name"
            or type(crs.get("properties")) is not dict
            or crs["properties"].get("name") not in SOURCE_CRS):
            raise HeightPairError("height source CRS differs from EPSG:25833")
    features=obj.get("features")
    if type(features) is not list or not 1<=len(features)<=MAX_FEATURES:
        raise HeightPairError("one-to-five exact source height features required")
    count=obj.get("numberReturned")
    if count is not None and (type(count) is not int or count!=len(features)):
        raise HeightPairError("inconsistent official height feature count")
    from shapely.geometry import shape, box
    box_fixed=box(*BBOX)
    geometries=[]
    props=[]
    seen_ids=set()
    for feat in features:
        if type(feat) is not dict or feat.get("type")!="Feature":
            raise HeightPairError("bad official height feature envelope")
        p=feat.get("properties")
        if type(p) is not dict:
            raise HeightPairError("height attributes are not a flat property object")
        fid=feat.get("id")
        if fid is not None:
            if type(fid) not in (str,int) or (type(fid) is str and not fid.strip()):
                raise HeightPairError("invalid provider feature id")
            typed=(type(fid).__name__, fid)
            if typed in seen_ids:
                raise HeightPairError("duplicate original height source feature ID")
            seen_ids.add(typed)
        geo=feat.get("geometry")
        if type(geo) is not dict or geo.get("type") not in ("Polygon","MultiPolygon"):
            raise HeightPairError("height data must be source polygons")
        try:
            g=shape(geo)
        except (ValueError,TypeError,IndexError) as exc:
            raise HeightPairError("invalid height polygon coordinates") from exc
        if (g.is_empty or not g.is_valid or not 0<g.area<1_000_000
            or not all(math.isfinite(v) for v in g.bounds)
            or g.intersection(box_fixed).area<=0):
            raise HeightPairError("bad source height polygons or unexpected bbox")
        x,y=g.representative_point().coords[0]
        if not 300000<x<500000 or not 5700000<y<5950000:
            raise HeightPairError("height layer axis/CRS sanity check failed")
        if any(g.equals(previous) for previous in geometries):
            raise HeightPairError("duplicate original height source geometry")
        geometries.append(g)
        props.append(p)
    return geometries,props


def compare_samples(alkis_raw: bytes, height_raw: bytes) -> dict:
    # The original ALKIS checker verifies five-or-fewer polygons, source
    # feature uniqueness, bbox overlap, WGS84 axis and finite coordinate values.
    alkis_report,_=inspect_building_geojson(alkis_raw)
    a=json.loads(alkis_raw.decode("utf-8"))
    from shapely.geometry import shape
    alkis=[shape(feat["geometry"]) for feat in a["features"]]
    heights,props=_parse_height(height_raw)
    best_pairs=[]
    for ai,g1 in enumerate(alkis):
        for hi,g2 in enumerate(heights):
            if not g1.intersects(g2):
                continue
            inter=float(g1.intersection(g2).area)
            union=float(g1.union(g2).area)
            iou=inter/union if union>0 else 0.0
            if iou>=MIN_IOU:
                best_pairs.append((ai,hi,iou))
    # A near-identical ALKIS footprint could be split in the height
    # product or vice versa. Do not guess matching identities.
    a_count={x:0 for x in range(len(alkis))}
    h_count={x:0 for x in range(len(heights))}
    for ai,hi,_ in best_pairs:
        a_count[ai]+=1
        h_count[hi]+=1
    clean=[(ai,hi,iou) for ai,hi,iou in best_pairs
           if a_count[ai]==1 and h_count[hi]==1]
    ambiguous=sum(n>1 for n in a_count.values())+sum(n>1 for n in h_count.values())
    non_null={k:0 for k in HEIGHT_FIELDS}
    height_numeric=0
    height_placeholder_3m=0
    roles={"building":0,"building_part":0,"unknown":0}
    for p in props:
        for field in HEIGHT_FIELDS:
            if field in p and p[field] is not None and p[field]!="":
                if type(p[field]) not in (int,float,str,bool):
                    raise HeightPairError("unexpected non-scalar height attribute")
                non_null[field]+=1
        height=p.get("hoehe")
        if height is not None and type(height) in (int,float) and math.isfinite(height) and 0<height<1000:
            height_numeric+=1
            if math.isclose(float(height),3.0,rel_tol=0,abs_tol=1e-9):
                height_placeholder_3m+=1
        role=p.get("role_txt")
        if type(role) is str and role.strip().casefold()=="gebäude":
            roles["building"]+=1
        elif type(role) is str and role.strip().casefold()=="bauteil":
            roles["building_part"]+=1
        else:
            roles["unknown"]+=1
    # A match is a geometry match, not permission to assign calculated
    # height to current ALKIS as an independent direct measurement.
    return {
        "sample_alkis_polygon_count":len(alkis),
        "sample_height_polygon_count":len(heights),
        "sample_alkis_total_footprint_m2":alkis_report["total_sample_polygon_area_m2_rounded"],
        "height_non_null_field_counts":non_null,
        "height_numeric_positive_count":height_numeric,
        "height_exact_3m_possible_placeholder_count":height_placeholder_3m,
        "height_source_role_counts":roles,
        "geometry_matches_iou_at_least_0_95":len(clean),
        "ambiguous_source_candidate_incidence_count":ambiguous,
        "some_unmatched_not_proof_of_missing_height":True,
        "field_provenance_loD2_2022_not_current_alkis":True,
        "three_metre_value_not_claimed_measured":True,
        "full_borough_count_or_completeness_inferred":False,
        "source_ids_or_feature_values_exported":False,
        "model_input_admitted":False,
    }


def _get_exact(url: str, opener: Callable, budget: int) -> bytes:
    req=request.Request(url,method="GET",headers={"Accept":"application/json"})
    try:
        with opener(req,TIMEOUT) as resp:
            if resp.status!=200 or resp.geturl()!=url:
                raise HeightPairError("unexpected WFS provider source redirect/status")
            media=resp.headers.get("Content-Type","").split(";",1)[0].strip().lower()
            if media not in ("application/json","application/geo+json"):
                raise HeightPairError("official original WFS did not send GeoJSON")
            raw=resp.read(budget+1)
    except HeightPairError:
        raise
    except (OSError,error.URLError,TimeoutError) as exc:
        raise HeightPairError("official building/height source fetch failed") from exc
    if not 0<len(raw)<=budget:
        raise HeightPairError("source response outside byte budget")
    return raw


def probe(*, opener: Callable=_fetch,
          clock: Callable[[],datetime]=lambda:datetime.now(timezone.utc)) -> dict:
    # Exactly two reviewed and independently bounded original source
    # operations. Both are current WFS responses; neither is immutable.
    a=_get_exact(ALKIS_URL,opener,MAX_BYTES)
    h=_get_exact(HEIGHT_URL,opener,MAX_BYTES)
    result=compare_samples(a,h)
    when=clock()
    if not isinstance(when,datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise HeightPairError("naive source timestamp")
    return {
        "profile":PROFILE,
        "alkis_source_url":ALKIS_URL,
        "height_source_url":HEIGHT_URL,
        "alkis_response_bytes":len(a),
        "height_response_bytes":len(h),
        "alkis_response_sha256":hashlib.sha256(a).hexdigest(),
        "height_response_sha256":hashlib.sha256(h).hexdigest(),
        "retrieved_at_utc":when.astimezone(timezone.utc).isoformat(),
        "reviewed_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "exact_original_source_requests":2,
        "raw_provider_features_persisted":False,
        "CAT_or_insurer_database_modified":False,
        **result,
    }


def main(argv: list[str]|None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("no external requests by default; --live only two bounded exact sources")
    try:
        print(json.dumps(probe(),indent=2,sort_keys=True,allow_nan=False))
        return 0
    except (HeightPairError,ValueError,OSError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
