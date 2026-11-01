#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exactly two official Berlin WFS2.0 bounded *hits-only* source requests.

Never download feature coordinates, attribute values or IDs. Compare true
in-query BBOX counts so independent top-five samples are not accidentally
treated as representative spatial coverage or a valid complete join.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Callable, Any
from urllib import parse, request, error
from xml.etree import ElementTree

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import BBOX

SOURCES = (
    ("alkis", "https://gdi.berlin.de/services/wfs/alkis_gebaeude",
     "alkis_gebaeude:gebaeude"),
    ("height_2022", "https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen",
     "ua_gebaeudehoehen:gebaeudehoehen"),
)
URLS = {
    name: root+"?"+parse.urlencode((
        ("service","WFS"),("version","2.0.0"),
        ("request","GetFeature"),("typeNames",type_name),
        ("resultType","hits"),("count","1"),
        ("srsName","EPSG:25833"),
        ("bbox",",".join(str(v) for v in BBOX)+",EPSG:25833"),
    ))
    for name,root,type_name in SOURCES
}
MAX_BYTES = 131_072
MAX_MATCHED = 2_000_000
TIMEOUT=35
PROFILE="oc-berlin-alkis-vs-lod2-two-exact-200m-bbox-hits-v0"


class WfsCountError(ValueError):
    """Unexpected original official WFS count schema or source identity."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WfsCountError("fixed source count metadata redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(request.ProxyHandler({}),NoRedirect(),
       request.HTTPSHandler(context=ssl.create_default_context())).open(req,timeout=timeout)


def parse_hits(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:
        raise WfsCountError("empty/oversized hits response")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise WfsCountError("unsafe WFS entity/doctype")
    try:
        root=ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise WfsCountError("invalid original WFS hits XML") from exc
    if root.tag!="{http://www.opengis.net/wfs/2.0}FeatureCollection":
        raise WfsCountError("not WFS 2.0 FeatureCollection hits")
    value=root.get("numberMatched")
    returned=root.get("numberReturned")
    if type(value) is not str or not re.fullmatch(r"[0-9]{1,8}",value):
        raise WfsCountError("WFS numberMatched must be a bounded exact integer")
    count=int(value)
    if count>MAX_MATCHED:
        raise WfsCountError("unreasonably high source result count")
    if returned not in ("0",None):
        raise WfsCountError("hits-only response unexpectedly returned individual features")
    # A failed server implementation might send individual gml features
    # even when it claims numberReturned=0: reject any element member.
    if any(e.tag.rsplit("}",1)[-1] in ("member","featureMember","featureMembers")
           for e in root.iter()):
        raise WfsCountError("hits-only source leaks actual feature objects")
    if len(list(root.iter()))>200:
        raise WfsCountError("unbounded WFS metadata content")
    return {
        "numberMatched":count,
        "numberReturned":0,
        "feature_geometry_bytes_retrieved":False,
    }


def _one(url: str, opener: Callable) -> bytes:
    req=request.Request(url,method="GET",
                        headers={"Accept":"application/xml, text/xml;q=0.9"})
    try:
        with opener(req,TIMEOUT) as response:
            if response.status!=200 or response.geturl()!=url:
                raise WfsCountError("wrong official service or status")
            media=response.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if media not in ("application/xml","text/xml","application/gml+xml"):
                raise WfsCountError("wrong WFS hits XML media type")
            body=response.read(MAX_BYTES+1)
    except WfsCountError:
        raise
    except (OSError,error.URLError,TimeoutError) as exc:
        raise WfsCountError("provider WFS hits operation failed") from exc
    return body


def probe(*,opener:Callable=_fetch,
          clock:Callable[[],datetime]=lambda:datetime.now(timezone.utc))->dict:
    results={}
    for name in ("alkis","height_2022"):
        raw=_one(URLS[name],opener)
        checked=parse_hits(raw)
        results[name]={
            "original_metadata_sha256":hashlib.sha256(raw).hexdigest(),
            "original_metadata_bytes":len(raw),
            **checked,
        }
    ts=clock()
    if not isinstance(ts,datetime) or ts.tzinfo is None or ts.utcoffset() is None:
        raise WfsCountError("count evidence requires timezone-aware UTC")
    return {
        "profile":PROFILE,
        "source_urls":URLS,
        "fixed_epsg25833_bbox_dimensions_m":[200,200],
        "retrieved_at_utc":ts.astimezone(timezone.utc).isoformat(),
        "original_source_requests":2,
        "count_receipts":results,
        "first_five_WFS_features_are_not_exhaustive":any(
            row["numberMatched"]>5 for row in results.values()
        ),
        "actual_geometry_or_height_values_obtained":False,
        "in_box_buildings_vs_parts_completeness_verified":False,
        "original_feature_bytes_persisted":False,
        "staged_insurer_or_CAT_db_modified":False,
        "reviewed_script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    o=p.parse_args(argv)
    if not o.live:
        p.error("two bounded source requests only with --live")
    try:
        print(json.dumps(probe(),indent=2,sort_keys=True,allow_nan=False))
        return 0
    except (WfsCountError,ValueError,OSError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
