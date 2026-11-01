#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed official Hessen ALKIS 2D building GeoJSON bounding-box canary.

Read-only, five-feature cap within previously verified WorldCover block185.
Never print source feature IDs/attributes/coordinates, export original
footprint bytes, infer a particular insured asset or admit CAT model data.
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
from urllib import error, request
from urllib.parse import urlsplit

COLLECTION = "bu-core2d:Building"
SOURCE = "de.hessen.inspire-alkis-2d-buildings.ogcapi"
HOST = "https://www.geoportal.hessen.de"
PATH = "/spatial-objects/711/collections/bu-core2d:Building/items"
BBOX = (9.427, 50.489, 9.511, 50.573)
LIMIT = 5
QUERY = "f=json&limit=5&bbox=9.427,50.489,9.511,50.573"
URL = HOST + PATH + "?" + QUERY
HOSENFELD_BBOX = (9.479, 50.512, 9.487, 50.521)
HOSENFELD_QUERY = "f=json&limit=5&bbox=9.479,50.512,9.487,50.521"
HOSENFELD_URL = HOST + PATH + "?" + HOSENFELD_QUERY
MAX_BYTES = 262_144
MAX_COORDINATE_PAIRS = 10_000
TIMEOUT_SECONDS = 60
RIGHTS_URL = "https://www.geoportal.hessen.de/spatial-objects/711"
DATA_VINTAGE = "mutable_original_ALKIS_exact_survey_date_unknown"


class HessenSourceBlocked(ValueError):
    """An unapproved source, service response or geometry was rejected."""


def no_duplicates(pairs):
    value={}
    for key, item in pairs:
        if key in value:
            raise HessenSourceBlocked("duplicate GeoJSON object key")
        value[key]=item
    return value


def validate_exact_review():
    parsed=urlsplit(URL)
    if (HOST!="https://www.geoportal.hessen.de"
            or parsed.scheme!="https" or parsed.netloc!="www.geoportal.hessen.de"
            or parsed.path!=PATH or parsed.query!=QUERY or parsed.fragment
            or COLLECTION!="bu-core2d:Building" or LIMIT!=5
            or BBOX!=(9.427,50.489,9.511,50.573)
            or HOSENFELD_BBOX!=(9.479,50.512,9.487,50.521)
            or HOSENFELD_QUERY!="f=json&limit=5&bbox=9.479,50.512,9.487,50.521"
            or HOSENFELD_URL!=HOST+PATH+"?"+HOSENFELD_QUERY
            or not (9+5*1024/12000 < BBOX[0] < BBOX[2] < 9+6*1024/12000)
            or not (51-6*1024/12000 < BBOX[1] < BBOX[3] < 51-5*1024/12000)):
        raise HessenSourceBlocked("unreviewed service URL, region, collection or limit")


def _coordinates(geometry):
    if type(geometry) is not dict:
        raise HessenSourceBlocked("unexpected GeoJSON geometry container")
    geom_type=geometry.get("type")
    if geom_type not in ("Polygon","MultiPolygon"):
        raise HessenSourceBlocked("only original 2D Polygon/MultiPolygon are supported")
    raw=geometry.get("coordinates")
    if type(raw) is not list or not raw:
        raise HessenSourceBlocked("missing polygon coordinate arrays")
    polygons=[raw] if geom_type=="Polygon" else raw
    if type(polygons) is not list or not polygons:
        raise HessenSourceBlocked("empty multipolygon")
    pairs=[]
    for polygon in polygons:
        if type(polygon) is not list or not polygon:
            raise HessenSourceBlocked("missing polygon rings")
        for ring in polygon:
            if type(ring) is not list or len(ring)<4:
                raise HessenSourceBlocked("polygon ring requires four or more coordinates")
            first=None
            last=None
            for coordinate in ring:
                if (type(coordinate) is not list or len(coordinate)!=2 or
                    any(type(v) not in (int,float) or not math.isfinite(v) for v in coordinate)):
                    raise HessenSourceBlocked("unreviewed coordinates, nonfinite or not 2D")
                lon,lat=coordinate
                if not (7.0 <= lon <= 11.0 and 49.0 <= lat <= 52.0):
                    raise HessenSourceBlocked("GeoJSON coordinates outside Hessen WGS84 range")
                p=(lon,lat)
                if first is None:
                    first=p
                last=p
                pairs.append(p)
                if len(pairs)>MAX_COORDINATE_PAIRS:
                    raise HessenSourceBlocked("unbounded building polygon coordinate count")
            if first!=last:
                raise HessenSourceBlocked("building polygon ring is not closed")
    return pairs, geom_type


def inspect_geojson(raw: bytes, *, query_bbox=BBOX) -> dict:
    if query_bbox not in (BBOX,HOSENFELD_BBOX):
        raise HessenSourceBlocked("unreviewed bbox used for GeoJSON validation")
    if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:
        raise HessenSourceBlocked("original bounded GeoJSON byte cap exceeded")
    try:
        payload=json.loads(raw.decode("utf-8"),
                           object_pairs_hook=no_duplicates,
                           parse_constant=lambda s: (_ for _ in ()).throw(
                               HessenSourceBlocked("nonfinite GeoJSON numeric constant")))
    except (UnicodeError, ValueError) as exc:
        raise HessenSourceBlocked("invalid original JSON response") from exc
    if type(payload) is not dict or payload.get("type")!="FeatureCollection":
        raise HessenSourceBlocked("source response is not GeoJSON FeatureCollection")
    if payload.get("crs") is not None:
        raise HessenSourceBlocked("unexpected embedded CRS; no reprojecting invented")
    features=payload.get("features")
    if type(features) is not list or len(features)>LIMIT:
        raise HessenSourceBlocked("building service exceeded fixed five-feature cap")
    count_geoms={"Polygon":0,"MultiPolygon":0}
    coordinate_pairs=0
    bboxes_matching=0
    for feature in features:
        if type(feature) is not dict or feature.get("type")!="Feature":
            raise HessenSourceBlocked("non-Feature building entry")
        # Attributes and feature IDs must NEVER leave transient source memory.
        if type(feature.get("properties")) is not dict:
            raise HessenSourceBlocked("building attributes field is not an object")
        pairs,typ=_coordinates(feature.get("geometry"))
        coordinate_pairs+=len(pairs)
        if coordinate_pairs>MAX_COORDINATE_PAIRS:
            raise HessenSourceBlocked("too many building coordinate pairs")
        count_geoms[typ]+=1
        xs=[p[0] for p in pairs]
        ys=[p[1] for p in pairs]
        if min(xs)<=query_bbox[2] and max(xs)>=query_bbox[0] and min(ys)<=query_bbox[3] and max(ys)>=query_bbox[1]:
            bboxes_matching+=1
    if bboxes_matching!=len(features):
        raise HessenSourceBlocked("source returned feature envelope outside reviewed BBOX")
    more=any(link.get("rel")=="next" for link in payload.get("links",[]) if type(link) is dict)
    matched=payload.get("numberMatched")
    if type(matched) is not int or matched<0:
        matched=None
    return {
        "returned_bounded_feature_count":len(features),
        "reported_number_matched_if_integer":matched,
        "polygon_count":count_geoms["Polygon"],
        "multipolygon_count":count_geoms["MultiPolygon"],
        "coordinate_pairs_inspected":coordinate_pairs,
        "returned_geometry_envelope_intersects_exact_bbox":True if features else None,
        "geometry_available_in_this_sample":len(features)>0,
        "pagination_next_link_present_not_followed":more,
        "complete_building_inventory_proven":False,
        "original_geometry_validity_topology_verified":False,
        "real_building_worldcover_overlap_verified":False,
        "model_input_approved":False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HessenSourceBlocked("redirect not reviewed")


def _open(req, timeout):
    client=request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return client.open(req, timeout=timeout)


def probe(*, open_request=_open, hosenfeld: bool = False) -> dict:
    validate_exact_review()
    if type(hosenfeld) is not bool:
        raise HessenSourceBlocked("only the two reviewed explicit bbox profiles are allowed")
    url=HOSENFELD_URL if hosenfeld else URL
    query_bbox=HOSENFELD_BBOX if hosenfeld else BBOX
    req=request.Request(
        url,method="GET",
        headers={"Accept":"application/geo+json,application/json",
                 "Accept-Encoding":"identity",
                 "User-Agent":"OpenCatastrophe-Hessen-ALKIS-5-Features/0.1"},
    )
    try:
        with open_request(req,TIMEOUT_SECONDS) as response:
            if response.status!=200 or response.geturl()!=url:
                raise HessenSourceBlocked("original exact API URL/status drift")
            mime=response.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if mime not in ("application/geo+json","application/json"):
                raise HessenSourceBlocked("source returned unreviewed GeoJSON transport MIME")
            if response.headers.get("Content-Encoding","identity").lower()!="identity":
                raise HessenSourceBlocked("unreviewed compressed HTTP transport")
            size=response.headers.get("Content-Length")
            if size is not None and (not size.isdigit() or int(size)>MAX_BYTES):
                raise HessenSourceBlocked("upstream Content-Length outside reviewed bound")
            raw=response.read(MAX_BYTES+1)
    except HessenSourceBlocked:
        raise
    except (error.HTTPError,error.URLError,OSError,TimeoutError) as exc:
        raise HessenSourceBlocked("official Hessen ALKIS bounded API unavailable") from exc
    data=inspect_geojson(raw,query_bbox=query_bbox)
    return {
        "profile":("oc-hessen-alkis-2d-building-5-features-hosenfeld-bbox-v0"
                   if hosenfeld else
                   "oc-hessen-alkis-2d-building-5-features-original-bbox-v0"),
        "source_id":SOURCE,
        "official_catalogue":RIGHTS_URL,
        "upstream_operation":"OGC_API_Features_5_2D_buildings_one_fixed_bbox",
        "source_metadata_vintage":DATA_VINTAGE,
        "retrieved_utc":datetime.now(timezone.utc).isoformat(),
        "http_status":200,
        "source_original_response_bytes":len(raw),
        "source_response_sha256":hashlib.sha256(raw).hexdigest(),
        "fixed_request_sha256":hashlib.sha256(("GET "+url).encode("ascii")).hexdigest(),
        "execution_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "provider_catalogue_license_label":"dl-de-zero-2.0",
        "source_raw_geometry_or_attributes_persisted":False,
        "raw_identifiers_addresses_or_coordinates_printed":False,
        **data,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    p.add_argument("--hosenfeld",action="store_true",
                   help="reviewed second fixed town-centre BBOX, at most five geometries")
    args=p.parse_args(argv)
    if not args.live:
        p.error("official provider request disabled unless --live explicitly supplied")
    try:
        print(json.dumps(probe(hosenfeld=args.hosenfeld),sort_keys=True,allow_nan=False))
    except (HessenSourceBlocked,ValueError,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "model_input_approved":False}),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
