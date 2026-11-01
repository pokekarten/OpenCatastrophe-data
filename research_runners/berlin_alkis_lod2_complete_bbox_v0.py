#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Complete-in-bbox (<=50 each) ALKIS vs 2022 LoD2 original polygon audit.

Exactly one bounded WFS2.0 GetFeature per official source and a fixed 200m
study region. Fail closed if the server reports more features than returned.
The product populations are different vintages; no source identifiers,
addresses, roof heights, features, or derived geometry are persisted.
"""
from __future__ import annotations

import argparse
from collections import Counter
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
    BBOX, _object, _reject_constant,
)

SERVICES=(
    ("alkis","https://gdi.berlin.de/services/wfs/alkis_gebaeude",
     "alkis_gebaeude:gebaeude"),
    ("loD2_2022","https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen",
     "ua_gebaeudehoehen:gebaeudehoehen"),
)
COUNT_LIMIT=50
MAX_BYTES=786_432
TIMEOUT=45
MIN_IOU=0.95
PROFILE="oc-berlin-200m-full-count-alkis-lod2-independent-geometry-v0"
URLS={
    name:root+"?"+parse.urlencode((
        ("service","WFS"),("version","2.0.0"),("request","GetFeature"),
        ("typeNames",layer),("count",str(COUNT_LIMIT)),("srsName","EPSG:25833"),
        ("bbox",",".join(str(n) for n in BBOX)+",EPSG:25833"),
        ("outputFormat","application/json"),
    )) for name,root,layer in SERVICES
}
FIELDS=("hoehe","role_txt","dachart","geschosse","quellebodenhoehe",
        "quelledachhoehe","quellelage","grundrissaktualitaet")
CRS=frozenset(("EPSG:25833","urn:ogc:def:crs:EPSG::25833",
               "urn:ogc:def:crs:EPSG:6.9:25833"))


# Candidate-only vocabulary: exact generic schema-class spellings, never
# a provider-approved translation and never production exposure labels.
# Do not echo arbitrary attribute strings (which may contain personal data).
_ROLE_DOMAIN_HINTS = {
    "gebäude":"publisher_german_gebaeude_literal",
    "bauteil":"publisher_german_bauteil_literal",
    "building":"citygml_building_literal_hypothesis",
    "buildingpart":"citygml_buildingpart_literal_hypothesis",
    "gebäudeteil":"german_gebaeudeteil_literal_hypothesis",
}
_ROLE_DOMAIN_OTHER = "unrecognized_not_echoed"


def _role_domain_counts(source_properties:list[dict])->dict[str,int]:
    """Safe aggregated vocabulary observations, not semantic approvals."""
    groups = {name:0 for name in _ROLE_DOMAIN_HINTS.values()}
    groups[_ROLE_DOMAIN_OTHER]=0
    for record in source_properties:
        role=record.get("role_txt")
        # Unknown values, including malicious personal/data-bearing strings,
        # are counted WITHOUT logging, hashing or serializing source text.
        key=role.strip().casefold() if type(role) is str else ""
        groups[_ROLE_DOMAIN_HINTS.get(key,_ROLE_DOMAIN_OTHER)]+=1
    return groups


class CompleteBboxError(ValueError):
    """Source count/geometry mismatch: cannot claim complete matched set."""


def _decode(raw:bytes, source:str)->tuple[list[Any],list[dict],dict,set[int]]:
    if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:
        raise CompleteBboxError("source original bytes are empty/oversized")
    try:
        doc=json.loads(raw.decode("utf-8"),object_pairs_hook=_object,
                       parse_constant=_reject_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CompleteBboxError("malformed strict GeoJSON source payload") from exc
    if type(doc) is not dict or doc.get("type")!="FeatureCollection":
        raise CompleteBboxError("not official WFS GeoJSON FeatureCollection")
    crs=doc.get("crs")
    # Full-population IoU cannot silently infer the response CRS from
    # srsName in a request; RFC 7946 CRS-less GeoJSON uses WGS84 degrees.
    if (type(crs) is not dict or crs.get("type")!="name"
        or type(crs.get("properties")) is not dict
        or crs["properties"].get("name") not in CRS):
        raise CompleteBboxError("source must explicitly declare EPSG:25833 CRS")
    fs=doc.get("features")
    if type(fs) is not list or not 1<=len(fs)<=COUNT_LIMIT:
        raise CompleteBboxError("source returned empty/over-limit geometry")
    matched=doc.get("numberMatched")
    returned=doc.get("numberReturned")
    if (type(matched) is not int or type(returned) is not int
        or matched!=len(fs) or returned!=len(fs)):
        raise CompleteBboxError("provider WFS count/pagination not complete within fixed bbox")
    from shapely.geometry import shape,box
    from shapely import get_coordinates
    scope=box(*BBOX)
    polygons=[]
    props=[]
    seen_ids=set()
    vertices=0
    for feat in fs:
        if type(feat) is not dict or feat.get("type")!="Feature":
            raise CompleteBboxError("bad source feature envelope")
        fields=feat.get("properties")
        if type(fields) is not dict:
            raise CompleteBboxError("invalid source feature properties")
        fid=feat.get("id")
        if fid is not None:
            if type(fid) not in (str,int) or (type(fid) is str and not fid.strip()):
                raise CompleteBboxError("invalid provider source feature identifier")
            typed=(type(fid).__name__,fid)
            if typed in seen_ids:
                raise CompleteBboxError("source repeats feature identity")
            seen_ids.add(typed)
        geom=feat.get("geometry")
        if type(geom) is not dict or geom.get("type") not in ("Polygon","MultiPolygon"):
            raise CompleteBboxError("not a polygonal building source")
        try:g=shape(geom)
        except (ValueError,TypeError,IndexError) as exc:
            raise CompleteBboxError("malformed original polygon") from exc
        if (g.is_empty or not g.is_valid or not 0<g.area<1_000_000
            or not all(math.isfinite(v) for v in g.bounds)
            or g.intersection(scope).area<=0):
            raise CompleteBboxError("invalid source building geometry or fixed bbox")
        xy=g.representative_point().coords[0]
        if not (300000<xy[0]<500000 and 5700000<xy[1]<5950000):
            raise CompleteBboxError("source projection/axis inconsistent with Berlin")
        vertices+=len(get_coordinates(g))
        if vertices>25000:
            raise CompleteBboxError("total source polygon vertex budget exceeded")
        polygons.append(g);props.append(fields)
    # A building and its source-defined subpart may legitimately have an
    # identical 2D footprint, so a duplicate is NOT automatically a bad
    # source record. Quarantine ALL members of such exact topology groups
    # from unique 1:1 research matches, not just whichever arrived second.
    groups:list[list[int]]=[]
    for index,g in enumerate(polygons):
        for group in groups:
            if g.equals(polygons[group[0]]):
                group.append(index)
                break
        else:
            groups.append([index])
    quarantined={index for group in groups if len(group)>1 for index in group}
    return polygons,props,{
        "features_verified_complete":len(polygons),
        "count_matches_returned_features":True,
        "source_name":source,
        "source_geometry_valid":True,
        "duplicate_footprint_group_count":sum(len(group)>1 for group in groups),
        "duplicate_footprint_source_feature_count":len(quarantined),
        "original_feature_values_logged":False,
    },quarantined


def evaluate(alkis_raw:bytes, height_raw:bytes)->dict:
    a,ap,aa,a_quarantine=_decode(alkis_raw,"alkis")
    h,hp,hh,h_quarantine=_decode(height_raw,"loD2_2022")
    candidates=[]
    for i,one in enumerate(a):
        if i in a_quarantine:
            continue
        for j,two in enumerate(h):
            if j in h_quarantine:
                continue
            if not one.intersects(two):continue
            inter=float(one.intersection(two).area)
            union=float(one.union(two).area)
            if not math.isfinite(inter) or not math.isfinite(union) or union<=0:
                raise CompleteBboxError("nonfinite projected building overlap")
            score=inter/union
            if score>=MIN_IOU:candidates.append((i,j))
    ac=Counter(i for i,j in candidates)
    hc=Counter(j for i,j in candidates)
    pairs=[(i,j) for i,j in candidates if ac[i]==1 and hc[j]==1]
    ambiguous=sum(count>1 for count in ac.values())+sum(count>1 for count in hc.values())
    non_null={field:0 for field in FIELDS}
    roles={"Gebäude":0,"Bauteil":0,"unknown":0}
    hpositive=0
    h3=0
    for p in hp:
        for field in FIELDS:
            v=p.get(field)
            if v is not None and v!="":
                if type(v) not in (str,int,float,bool):
                    raise CompleteBboxError("source field is unexpectedly complex")
                non_null[field]+=1
        role=p.get("role_txt")
        if type(role) is str and role.strip().casefold()=="gebäude":roles["Gebäude"]+=1
        elif type(role) is str and role.strip().casefold()=="bauteil":roles["Bauteil"]+=1
        else:roles["unknown"]+=1
        v=p.get("hoehe")
        if type(v) in (int,float) and math.isfinite(v) and 0<v<1000:
            hpositive+=1
            if math.isclose(v,3.0,rel_tol=0,abs_tol=1e-9):h3+=1
    # Per-match attribute triage stays internal and is only published as
    # aggregate counts, never indexed building rows, source values, or IDs.
    # A near-identical 2022 roof source footprint is NOT an insured asset
    # and a positive height that differs from 3m is NOT measured ground truth.
    matched_roles={"Gebäude":0,"Bauteil":0,"unknown":0}
    matched_height_positive=0
    matched_height_possible_3m=0
    matched_height_positive_not_3m=0
    matched_building_role_positive_not_3m=0
    matched_source_method_fields={k:0 for k in (
        "quellebodenhoehe","quelledachhoehe","quellelage"
    )}
    for _alkis_index, height_index in pairs:
        p=hp[height_index]
        label=p.get("role_txt")
        if type(label) is str and label.strip().casefold()=="gebäude":
            role="Gebäude"
        elif type(label) is str and label.strip().casefold()=="bauteil":
            role="Bauteil"
        else:
            role="unknown"
        matched_roles[role]+=1
        for key in matched_source_method_fields:
            if p.get(key) is not None and p[key]!="":
                matched_source_method_fields[key]+=1
        value=p.get("hoehe")
        if type(value) in (int,float) and math.isfinite(value) and 0<value<1000:
            matched_height_positive+=1
            if math.isclose(value,3.0,rel_tol=0,abs_tol=1e-9):
                matched_height_possible_3m+=1
            else:
                matched_height_positive_not_3m+=1
                if role=="Gebäude":
                    matched_building_role_positive_not_3m+=1

    return {
        "height_role_literal_domain_probe_counts":{
            "all_height_features":_role_domain_counts(hp),
            "uniquely_matched_height_features":_role_domain_counts(
                [hp[j] for _,j in pairs]
            ),
            "duplicate_footprint_quarantined_height_features":_role_domain_counts(
                [hp[j] for j in sorted(h_quarantine)]
            ),
        },
        "role_domain_candidate_terms_not_provider_approved":True,
        "unknown_role_terms_remain_unadmitted":True,
        "matched_height_source_role_counts":matched_roles,
        "matched_positive_numeric_height_count":matched_height_positive,
        "matched_exact_3m_possible_placeholder_count":matched_height_possible_3m,
        "matched_positive_non3m_height_count_not_proven_measured":matched_height_positive_not_3m,
        "matched_recognized_building_role_positive_non3m_count_research_only":matched_building_role_positive_not_3m,
        "matched_source_method_field_non_null_counts":matched_source_method_fields,
        "matched_source_height_admitted_to_insurer_exposure":0,
        "alkis_in_bbox":aa["features_verified_complete"],
        "loD2_2022_in_bbox":hh["features_verified_complete"],
        "duplicate_footprints_quarantined":True,
        "duplicate_footprint_groups_by_source":{
            "alkis":aa["duplicate_footprint_group_count"],
            "loD2_2022":hh["duplicate_footprint_group_count"],
        },
        "duplicate_source_features_quarantined_by_source":{
            "alkis":aa["duplicate_footprint_source_feature_count"],
            "loD2_2022":hh["duplicate_footprint_source_feature_count"],
        },
        "source_complete_feature_counts_verified":True,
        "overlap_iou_minimum":MIN_IOU,
        "unambiguous_one_to_one_footprints":len(pairs),
        "ambiguous_candidate_incidence":ambiguous,
        "unmatched_alkis_count":len(a)-len({i for i,j in pairs}),
        "unmatched_height_product_count":len(h)-len({j for i,j in pairs}),
        "height_field_non_null_counts":non_null,
        "height_positive_numeric_count":hpositive,
        "three_metre_possible_placeholder_count":h3,
        "height_role_text_counts":roles,
        "confirmed_height_values_assigned_to_CAT4":0,
        "source_vintage_equivalence_proven":False,
        "number_of_unique_real_buildings_proven":False,
        "source_feature_ids_or_attribute_values_exported":False,
        "model_input_admitted":False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise CompleteBboxError("original source redirected")


def _fetch(req:request.Request, timeout:int):
    return request.build_opener(request.ProxyHandler({}),NoRedirect(),
       request.HTTPSHandler(context=ssl.create_default_context())).open(req,timeout=timeout)


def _get(url:str,opener:Callable)->bytes:
    req=request.Request(url,method="GET",headers={"Accept":"application/json"})
    try:
        with opener(req,TIMEOUT) as resp:
            if resp.status!=200 or resp.geturl()!=url:
                raise CompleteBboxError("official WFS returned unexpected URL/status")
            media=resp.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if media not in ("application/json","application/geo+json"):
                raise CompleteBboxError("official source returned non-GeoJSON media")
            raw=resp.read(MAX_BYTES+1)
    except CompleteBboxError:raise
    except (OSError,error.URLError,TimeoutError) as exc:
        raise CompleteBboxError("official source in-bbox request failed") from exc
    if not 0<len(raw)<=MAX_BYTES:
        raise CompleteBboxError("original source exceeded byte budget")
    return raw


def probe(*,opener:Callable=_fetch,
          clock:Callable[[],datetime]=lambda:datetime.now(timezone.utc))->dict:
    a=_get(URLS["alkis"],opener)
    h=_get(URLS["loD2_2022"],opener)
    result=evaluate(a,h)
    when=clock()
    if not isinstance(when,datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise CompleteBboxError("source evidence UTC must be offset-aware")
    return {
        "profile":PROFILE,"source_urls":URLS,
        "utc_receipt":when.astimezone(timezone.utc).isoformat(),
        "source_requests":2,
        "alkis_original_bytes":len(a),"height_original_bytes":len(h),
        "alkis_original_sha256":hashlib.sha256(a).hexdigest(),
        "height_original_sha256":hashlib.sha256(h).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_provider_geometry_persisted":False,
        "CAT_or_other_persistent_db_modified":False,
        **result,
    }


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    opts=p.parse_args(argv)
    if not opts.live:p.error("offline by default; two reviewed source requests require --live")
    try:
        print(json.dumps(probe(),indent=2,sort_keys=True,allow_nan=False))
        return 0
    except (CompleteBboxError,ValueError,OSError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
