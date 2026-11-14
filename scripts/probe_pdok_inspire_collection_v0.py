#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exactly one reviewed, bounded original PDOK INSPIRE Gewaspercelen metadata GET.

This separate INSPIRE collection is not an immutable 2025 file and does not
admit farm parcels, farmer attributes, geometry or model source data.
No network without --live; no links followed, no retries, no redirects.
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

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "nl.rvo.brp-gewaspercelen.2025"
ACCESS_ID = "nl.rvo.brp-gewaspercelen.2025.inspire-collection"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
BASE = "https://api.pdok.nl"
COLLECTION_PATH = "/rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen"
URL = BASE + COLLECTION_PATH + "?f=json"
CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
EPSG28992 = "http://www.opengis.net/def/crs/EPSG/0/28992"
EPSG4258 = "http://www.opengis.net/def/crs/EPSG/0/4258"
TIMEOUT = 20
MAX_BYTES = 65536


class InspireBlocked(ValueError):
    """Unsafe provider identity, response or licence scope."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise InspireBlocked("reviewed INSPIRE endpoint forbids redirect")


def verify_reviewed_contract() -> None:
    c = validate_path(CONTRACT_PATH)
    p = c["rights_and_policy"]
    if (c["access_id"] != ACCESS_ID or c["source_ids"] != [SOURCE_ID]
            or c["interface_type"] != "ogc_api" or c["status"] != "probe_ready"
            or c["service_root"] != BASE or c["access_scope"] != ["metadata"]
            or c["request_contract"]["allowed_operations"] != ["collection_metadata_get"]
            or c["request_contract"]["path_templates"] != [COLLECTION_PATH]
            or c["authentication"]["mode"] != "none"
            or c["probe_contract"]["mode"] != "metadata_get"
            or c["probe_contract"]["operation"] != "collection_metadata_get"
            or c["probe_contract"]["requires_credentials"] is not False
            or p["dataset_rights_status"] != "verified"
            or p["api_terms_status"] != "separate_reviewed"
            or p["commercial_automation_status"] != "allowed"
            or p["redistribution_status"] != "unknown"
            or p["terms_url"] != "https://www.pdok.nl/how-to-faq"
            or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
            or c["operational_constraints"]["max_sample_bytes"] != MAX_BYTES
            or c["operational_constraints"]["retry_policy"] != "none"
            or c["operational_constraints"]["timeout_seconds"] != TIMEOUT):
        raise InspireBlocked("exact INSPIRE metadata licence or path contract changed")


def _strict_map(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in pairs:
        if k in result:
            raise InspireBlocked("duplicate source JSON key")
        result[k] = v
    return result


def _reject_constant(value: str) -> None:
    raise InspireBlocked("nonfinite source JSON value")


def inspect_collection(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not raw or len(raw) > MAX_BYTES:
        raise InspireBlocked("invalid original body size")
    try:
        item = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_map,
                          parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InspireBlocked("invalid source JSON") from exc
    if (type(item) is not dict or item.get("id") != "gewaspercelen"
            or item.get("title") != "Gewaspercelen"
            or item.get("itemType") != "feature"):
        raise InspireBlocked("wrong harmonised INSPIRE collection")
    desc = item.get("description")
    if type(desc) is not str or "gewas" not in desc.lower() or "percelen" not in desc.lower():
        raise InspireBlocked("unexpected INSPIRE agricultural semantics")
    if item.get("storageCrs") != EPSG4258:
        raise InspireBlocked("original INSPIRE storage CRS changed")
    crs = item.get("crs")
    if type(crs) is not list or any(k not in crs for k in (CRS84, EPSG28992, EPSG4258)):
        raise InspireBlocked("INSPIRE output coordinate systems changed")
    extent = item.get("extent")
    if type(extent) is not dict or type(extent.get("spatial")) is not dict:
        raise InspireBlocked("missing original spatial extent")
    spatial = extent["spatial"]
    bbox = spatial.get("bbox")
    if spatial.get("crs") != CRS84 or type(bbox) is not list or len(bbox) != 1:
        raise InspireBlocked("wrong original bounding-box CRS/shape")
    if type(bbox[0]) is not list or len(bbox[0]) != 4:
        raise InspireBlocked("wrong original bounding-box shape")
    west, south, east, north = bbox[0]
    if (not all(type(v) in (int, float) and math.isfinite(v)
                for v in (west, south, east, north))
            or not -180 <= west < east <= 180 or not -90 <= south < north <= 90
            or not (west <= 7.4 and east >= 3 and south <= 54 and north >= 51)):
        raise InspireBlocked("INSPIRE bbox not in Dutch extent")
    links = item.get("links")
    if type(links) is not list or sum(
            type(x) is dict and x.get("rel") == "self"
            and x.get("href") == URL and x.get("type") == "application/json"
            for x in links) != 1:
        raise InspireBlocked("source self link changed, missing or duplicated")
    # This metadata body advertises items/schema URLs. Never traverse any URL.
    return {
        "collection_id_verified": True,
        "inspire_ogc_storage_crs_epsg4258_verified": True,
        "crs84_epsg28992_epsg4258_verified": True,
        "bbox_overlaps_netherlands_verified": True,
        "feature_rows_requested": 0,
        "parcel_geometry_acquired": False,
        "historical_2025_original_sha_verified": False,
        "independent_rvo_source_verified": False,
        "model_input_approved": False,
    }


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    verify_reviewed_contract()
    req = request.Request(
        URL, method="GET",
        headers={"Accept": "application/json", "Accept-Encoding": "identity",
                 "User-Agent": "OpenCatastrophe-data/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data)"})
    try:
        with open_request(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise InspireBlocked("exact original PDOK HTTP 200 required")
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise InspireBlocked("unexpected source media type")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise InspireBlocked("compressed source response not reviewed")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isascii() or not length.isdecimal()
                                       or int(length) > MAX_BYTES):
                raise InspireBlocked("invalid or excessive original Content-Length")
            raw = response.read(MAX_BYTES + 1)
            if length is not None and int(length) != len(raw):
                raise InspireBlocked("source original Content-Length drift")
    except InspireBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise InspireBlocked("one reviewed INSPIRE original GET failed") from exc
    checks = inspect_collection(raw)
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise InspireBlocked("timezone-aware UTC required")
    return {
        "profile": "oc-pdok-inspire-gewaspercelen-exact-metadata-only-v0",
        "source_id": SOURCE_ID,
        "access_id": ACCESS_ID,
        "retrieval_utc": now.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "source_access_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "source_probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **checks,
        "original_response_body_persisted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="one strictly reviewed original metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no original provider network by default; --live is required")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (InspireBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
