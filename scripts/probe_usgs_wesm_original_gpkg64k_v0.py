#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read one source-locked official WESM GeoPackage SQLite first-page prefix.

Authentic source 65536-byte HTTP 206 receipt only; never touches WESM polygons
or SQLite feature tables. A SQLite/OGC header is not complete GeoPackage T3,
Florida S1M workunit coverage, lidar accuracy or model input authorization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import struct
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/usgs.3dep.wesm.gpkg.original-65536-prefix.json"
HOST = "https://rockyweb.usgs.gov"
PATH = "/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg"
URL = HOST + PATH
OPERATION = "one_wesm_original_gpkg_65536_header"
COUNT = 65536
RANGE = "bytes=0-65535"
TIMEOUT = 30
MIN_TOTAL = COUNT + 1
MAX_TOTAL = 4 * 1024 * 1024 * 1024
# Explicit immutable original 206 Content-Range observed in GitHub run 43968198021.
# The size was checked without reading any original body bytes.
EXPECTED_TOTAL = 3827232768
# Independently observed authentic original first 65536-byte source SHA-256:
# https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968769537
EXPECTED_PREFIX_SHA = "0344f898d4946a915ca0c3a5d0078fd72dc222179c54d8e9413a067c8ce5be88"
CONTENT_RANGE = re.compile(r"bytes 0-65535/([1-9][0-9]{4,12})\Z")
MEDIA = frozenset((
    "application/octet-stream",
    "binary/octet-stream",
    "application/geopackage+sqlite3",
    "application/x-sqlite3",
    "application/vnd.sqlite3",
))
PROFILE = "usgs-wesm-gpkg-first-64k-original-v0"
MAGIC = b"SQLite format 3\x00"
GPKG_APPLICATION_ID = 0x47504B47


class Blocked(ValueError):
    """Source or scientific shape cannot be verified within reviewed scope."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("WESM original GeoPackage redirect disallowed")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def frozen_contract(path: Path = CONTRACT) -> str:
    raw = path.read_bytes()
    c = validate_path(path)
    rights, ops = c["rights_and_policy"], c["request_contract"]
    limits, p = c["operational_constraints"], c["probe_contract"]
    if (
        c["access_id"] != "usgs.3dep.wesm.gpkg.original-65536-prefix"
        or c["source_ids"] != ["usgs.3dep.wesm.workunit-metadata"]
        or c["interface_type"] != "http_file"
        or c["status"] != "probe_ready"
        or c["service_root"] != HOST
        or c["access_scope"] != ["sample"]
        or c["authentication"]["mode"] != "none"
        or c["authentication"]["credential_reference"] is not None
        or ops["allowed_operations"] != [OPERATION]
        or ops["path_templates"] != [PATH]
        or RANGE not in ops["parameter_rules"]
        or limits["timeout_seconds"] != TIMEOUT
        or limits["max_probe_bytes"] != COUNT
        or limits["max_sample_bytes"] != COUNT
        or limits["retry_policy"] != "none"
        or set(c["response_contract"]["expected_media_types"]) != MEDIA
        or p["mode"] != "provider_specific"
        or p["operation"] != OPERATION
        or p["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "same_as_dataset"
        or rights["commercial_automation_status"] != "allowed"
        or rights["redistribution_status"] != "unknown"
        or c["implementation_decision"] != "build_adapter_now"
    ):
        raise Blocked("official WESM GeoPackage original access review drift")
    return hashlib.sha256(raw).hexdigest()


def sqlite_original_header(prefix: bytes, advertised_total: int) -> dict[str, Any]:
    """Decode *only* fixed SQLite header integers; do not parse B-trees/geometry."""
    if type(prefix) is not bytes or len(prefix) != COUNT or prefix[:16] != MAGIC:
        raise Blocked("source prefix is not a complete 64 KiB SQLite3 database header")
    size_field = struct.unpack_from(">H", prefix, 16)[0]
    page_size = 65536 if size_field == 1 else size_field
    if page_size < 512 or page_size > 65536 or page_size & (page_size - 1):
        raise Blocked("invalid SQLite database page size")
    if prefix[18] not in (1, 2) or prefix[19] not in (1, 2):
        raise Blocked("unreviewed SQLite write/read format versions")
    if prefix[20:24] != bytes((0, 64, 32, 32)):
        raise Blocked("SQLite header reserved-byte and payload fraction violations")
    db_pages = struct.unpack_from(">I", prefix, 28)[0]
    schema_format = struct.unpack_from(">I", prefix, 44)[0]
    text_encoding = struct.unpack_from(">I", prefix, 56)[0]
    user_version = struct.unpack_from(">I", prefix, 60)[0]
    app_id = struct.unpack_from(">I", prefix, 68)[0]
    sqlite_version_number = struct.unpack_from(">I", prefix, 96)[0]
    if schema_format not in (1, 2, 3, 4) or text_encoding not in (1, 2, 3):
        raise Blocked("invalid original SQLite schema format or text encoding")
    if app_id != GPKG_APPLICATION_ID:
        raise Blocked("original SQLite application_id is not OGC GeoPackage GPKG")
    if not MIN_TOTAL <= advertised_total <= MAX_TOTAL:
        raise Blocked("original GeoPackage total bytes outside approved range")
    if advertised_total % page_size:
        raise Blocked("original GeoPackage size is not a whole SQLite page multiple")
    if not 1 <= db_pages <= (MAX_TOTAL // page_size):
        raise Blocked("invalid original SQLite database page count")
    if db_pages * page_size != advertised_total:
        raise Blocked("original SQLite file-header page count contradicts HTTP total size")
    return {
        "native_sqlite_format_3_verified": True,
        "native_ogc_gpkg_application_id_verified": True,
        "source_sqlite_page_size_bytes": page_size,
        "source_sqlite_declared_page_count": db_pages,
        "source_sqlite_schema_format": schema_format,
        "source_sqlite_text_encoding_code": text_encoding,
        "source_gpkg_application_id_hex": f"0x{app_id:08x}",
        "source_gpkg_user_version": user_version,
        "source_sqlite_header_library_version_number": sqlite_version_number,
        "original_entire_sqlite_pages_available_for_validation": False,
        "original_gpkg_contents_srs_geometry_verified": False,
        "original_wesm_workunit_polygon_count_verified": False,
    }


def observe(
    *,
    opener: Callable = _open,
    contract_path: Path = CONTRACT,
    clock: Callable = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    contract_sha = frozen_contract(contract_path)
    req = request.Request(URL, method="GET", headers={
        "Range": RANGE,
        "Accept": "application/octet-stream",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-USGS-WESM-Original-GPKG/0.1",
    })
    try:
        with opener(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 206:
                raise Blocked("official WESM GeoPackage did not return HTTP206 exact source range")
            content_range = response.headers.get("Content-Range", "").strip()
            matched = CONTENT_RANGE.fullmatch(content_range)
            if not matched:
                raise Blocked("original GeoPackage Content-Range does not match fixed GET")
            total = int(matched.group(1))
            if total != EXPECTED_TOTAL:
                raise Blocked(f"original WESM GeoPackage full-object size drift: provider advertised {total} vs frozen {EXPECTED_TOTAL}; no body read")
            media = response.headers.get("Content-Type", "").lower().split(";", 1)[0].strip()
            if media not in MEDIA:
                raise Blocked("unreviewed GeoPackage Content-Type")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise Blocked("unexpected original GeoPackage content encoding")
            length = response.headers.get("Content-Length")
            if length is not None and (
                not length.isascii() or not length.isdecimal() or int(length) != COUNT
            ):
                raise Blocked("unexpected original GeoPackage Content-Length")
            raw = response.read(COUNT + 1)
            if len(raw) != COUNT:
                raise Blocked("source did not provide exactly 65536 original bytes")
    except Blocked:
        raise
    except (OSError, TimeoutError, error.HTTPError, error.URLError) as exc:
        raise Blocked("one WESM original GeoPackage source request unavailable") from exc

    original_prefix_sha = hashlib.sha256(raw).hexdigest()
    if original_prefix_sha != EXPECTED_PREFIX_SHA:
        raise Blocked("authentic WESM GeoPackage 64KiB original prefix SHA drift")
    original_header = sqlite_original_header(raw, total)
    timestamp = clock()
    if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
        raise Blocked("source observation lacks timezone-aware UTC")
    return {
        "profile": PROFILE,
        "source_id": "usgs.3dep.wesm.workunit-metadata",
        "official_original_url": URL,
        "original_http_status": 206,
        "original_content_range": content_range,
        "original_prefix_bytes": len(raw),
        "original_prefix_sha256": original_prefix_sha,
        "original_total_bytes_advertised_not_full_hash": total,
        "observed_utc": timestamp.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(
            ("GET " + URL + "\nRange: " + RANGE + "\n").encode("ascii")).hexdigest(),
        "contract_sha256": contract_sha,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **original_header,
        "original_full_wesm_gpkg_sha256_verified": False,
        "original_wesm_csv_to_gpkg_version_parity_verified": False,
        "original_florida_s1m_source_workunit_spatial_join_verified": False,
        "original_geo_source_bytes_persisted": False,
        "neon_write_performed": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args(argv)
    if not args.live:
        ap.error("one original USGS WESM GeoPackage Range GET requires --live")
    try:
        print(json.dumps(observe(), sort_keys=True, allow_nan=False))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
