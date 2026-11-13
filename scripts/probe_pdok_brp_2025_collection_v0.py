#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One manually opted-in RVO/PDOK BRP live collection metadata GET only.

No feature/items/crop geometry, no linked URL traversal, no credentials,
no retries/redirects, no response-body persistence and no model admission.
The mutable 'latest' collection does NOT prove an immutable 2025 snapshot.
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
from urllib import error, request
from urllib.parse import urlsplit

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "nl.rvo.brp-gewaspercelen.2025.ogc-collection"
SOURCE_ID = "nl.rvo.brp-gewaspercelen.2025"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
BASE = "https://api.pdok.nl"
COLLECTION_PATH = "/rvo/gewaspercelen/ogc/v1/collections/brpgewas"
URL = BASE + COLLECTION_PATH + "?f=json"
MAX_BYTES = 131072
TIMEOUT = 20
CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
EPSG28992 = "http://www.opengis.net/def/crs/EPSG/0/28992"

class BRPBlocked(ValueError):
    """Fail closed on rights, contract, source or transport drift."""

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BRPBlocked("redirect outside exact reviewed PDOK route")

def verify_reviewed_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    rights = c["rights_and_policy"]
    parsed = urlsplit(URL)
    if (c["access_id"] != ACCESS_ID
            or c["source_ids"] != [SOURCE_ID]
            or c["interface_type"] != "ogc_api"
            or c["status"] != "probe_ready"
            or c["service_root"] != BASE
            or c["access_scope"] != ["metadata"]
            or c["request_contract"]["allowed_operations"] != ["collection_metadata_get"]
            or c["request_contract"]["path_templates"] != [COLLECTION_PATH]
            or c["authentication"]["mode"] != "none"
            or c["probe_contract"]["mode"] != "metadata_get"
            or c["probe_contract"]["operation"] != "collection_metadata_get"
            or c["probe_contract"]["requires_credentials"] is not False
            or rights["dataset_rights_status"] != "verified"
            or rights["api_terms_status"] != "separate_reviewed"
            or rights["commercial_automation_status"] != "allowed"
            or rights["terms_url"] != "https://www.pdok.nl/veelgestelde-vragen-over-pdok-services"
            or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
            or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
            or c["operational_constraints"]["retry_policy"] != "none"
            or parsed.scheme != "https" or parsed.netloc != "api.pdok.nl"
            or parsed.path != COLLECTION_PATH or parsed.query != "f=json"
            or parsed.username or parsed.password or parsed.fragment):
        raise BRPBlocked("PDOK exact collection reviewed scope changed")

def _strict_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = {}
    for k,v in pairs:
        if k in out:
            raise BRPBlocked("duplicate original PDOK JSON key")
        out[k] = v
    return out

def _reject_nonfinite(value: str) -> None:
    raise BRPBlocked("nonfinite PDOK collection JSON value")

def inspect_collection(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not raw or len(raw)>MAX_BYTES:
        raise BRPBlocked("PDOK collection response byte limit")
    try:
        item=json.loads(raw.decode("utf-8"),object_pairs_hook=_strict_mapping,parse_constant=_reject_nonfinite)
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise BRPBlocked("invalid original PDOK collection JSON") from exc
    if (type(item) is not dict or item.get("id")!="brpgewas"
            or item.get("title")!="BRP Gewaspercelen" or item.get("itemType")!="feature"):
        raise BRPBlocked("wrong RVO BRP collection identity")
    desc=item.get("description")
    if type(desc) is not str or "landbouwpercelen" not in desc.casefold() or "gewas" not in desc.casefold():
        raise BRPBlocked("incorrect agricultural parcel semantics")
    if item.get("storageCrs")!=EPSG28992:
        raise BRPBlocked("wrong original storage CRS")
    crs=item.get("crs")
    if type(crs) is not list or CRS84 not in crs or EPSG28992 not in crs:
        raise BRPBlocked("mandatory output/storage coordinate systems missing")
    spatial=item.get("extent")
    if type(spatial) is not dict or type(spatial.get("spatial")) is not dict:
        raise BRPBlocked("source spatial extent absent")
    bbox=spatial["spatial"].get("bbox")
    if type(bbox) is not list or len(bbox)!=1 or type(bbox[0]) is not list or len(bbox[0])!=4:
        raise BRPBlocked("unexpected collection bounding boxes")
    west,south,east,north=bbox[0]
    if (not all(type(x) in {int,float} and math.isfinite(x) for x in (west,south,east,north))
            or not -180<=west<east<=180 or not -90<=south<north<=90
            or not (west<=8 and east>=3 and south<=54 and north>=50)):
        raise BRPBlocked("source extent does not include the Netherlands")
    if spatial["spatial"].get("crs") != CRS84:
        raise BRPBlocked("bbox must be expressed in OGC CRS84")
    links=item.get("links")
    if type(links) is not list or sum(
        type(x) is dict and x.get("rel")=="self"
        and x.get("href")==URL and x.get("type")=="application/json"
        for x in links) !=1:
        raise BRPBlocked("canonical collection self-link absent or repeated")
    # Do not follow any provider-returned link, query items, or log their body.
    return {
        "collection_id_verified":"brpgewas",
        "collection_title_verified":"BRP Gewaspercelen",
        "spatial_crs84_and_epsg28992_verified":True,
        "bbox_overlaps_netherlands_verified":True,
        "original_feature_requests":0,
        "original_parcel_geometry_downloaded":False,
        "frozen_2025_vintage_proven":False,
        "model_input_approved":False,
    }

def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req,timeout=timeout)

def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    verify_reviewed_contract()
    req=request.Request(URL,method="GET",headers={
        "Accept":"application/json",
        "Accept-Encoding":"identity",
        "User-Agent":"OpenCatastrophe-data/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)"
    })
    try:
        with open_request(req,TIMEOUT) as response:
            if response.status!=200 or response.geturl()!=URL:
                raise BRPBlocked("PDOK HTTP 200/fixed URL expected")
            media=response.headers.get("Content-Type","").split(";",1)[0].strip().lower()
            if media!="application/json":
                raise BRPBlocked("PDOK JSON media type mismatch")
            if response.headers.get("Content-Encoding","identity").strip().lower()!="identity":
                raise BRPBlocked("unreviewed compressed response")
            stated=response.headers.get("Content-Length")
            if stated is not None and (not stated.isascii() or not stated.isdecimal() or int(stated)>MAX_BYTES):
                raise BRPBlocked("PDOK stated Content-Length invalid or over limit")
            raw=response.read(MAX_BYTES+1)
            if stated is not None and int(stated)!=len(raw):
                raise BRPBlocked("PDOK response body length mismatch")
    except BRPBlocked:
        raise
    except (error.HTTPError,error.URLError,OSError,TimeoutError) as exc:
        raise BRPBlocked("reviewed original PDOK collection GET failed") from exc
    summary=inspect_collection(raw)
    now=clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise BRPBlocked("UTC-aware clock required")
    return {
        "profile":"oc-pdok-brp-2025-metadata-only-v0",
        "source_id":SOURCE_ID,
        "access_id":ACCESS_ID,
        "retrieval_utc":now.astimezone(timezone.utc).isoformat(),
        "request_sha256":hashlib.sha256(("GET "+URL).encode("ascii")).hexdigest(),
        "response_sha256":hashlib.sha256(raw).hexdigest(),
        "response_bytes":len(raw),
        "source_access_contract_sha256":hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "source_probe_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **summary,
        "original_response_body_persisted":False,
        "model_input_admitted":False,
    }

def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true",help="one exact reviewed PDOK collection-metadata GET")
    args=parser.parse_args(argv)
    if not args.live:
        parser.error("no network by default; --live required")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (BRPBlocked,ValueError,OSError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
