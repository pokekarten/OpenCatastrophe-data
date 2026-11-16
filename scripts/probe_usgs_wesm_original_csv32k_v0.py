#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One original USGS WESM.csv 32KiB bounded range, metadata-only.

Requires explicit --live. This is original provider CSV HEADER evidence only:
no full file, source row, WESM GPKG polygon, S1M tile join or model approval.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Callable
from urllib import request, error

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/usgs.3dep.wesm.csv.32k-original-prefix.json"
HOST = "https://rockyweb.usgs.gov"
PATH = "/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv"
URL = HOST + PATH
OPERATION = "one_wesm_original_csv_32768_header"
BYTES = 32768
TIMEOUT = 25
RANGE = "bytes=0-32767"
MEDIA = frozenset({"text/csv", "text/plain", "application/octet-stream",
                   "binary/octet-stream", "application/vnd.ms-excel"})
CONTENT_RANGE = re.compile(r"bytes 0-32767/([1-9][0-9]{4,10})\Z")
HEADER_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
PROFILE = "oc-usgs-3dep-wesm-original-csv32k-v0"
# Frozen actual original HTTP206 prefix: 2026-11-16 / Actions 43961768133.
# This is NOT a whole-WESM-file checksum; original CSV changes almost daily.
EXPECTED_PREFIX_SHA = "19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d"
EXPECTED_WHOLE_CSV_BYTES = 2267051


class Blocked(ValueError):
    """Original WESM source identity or contract cannot be trusted."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("USGS original WESM redirect is outside reviewed scope")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()))
    return opener.open(req, timeout=timeout)


def validate_contract(path: Path = CONTRACT) -> str:
    raw = path.read_bytes()
    data = validate_path(path)
    policy = data["rights_and_policy"]
    source = data["request_contract"]
    op = data["probe_contract"]
    limits = data["operational_constraints"]
    if (
        data["access_id"] != "usgs.3dep.wesm.csv.32k-original-prefix"
        or data["source_ids"] != ["usgs.3dep.wesm.workunit-metadata"]
        or data["status"] != "probe_ready"
        or data["interface_type"] != "http_file"
        or data["service_root"] != HOST
        or data["access_scope"] != ["sample"]
        or data["authentication"]["mode"] != "none"
        or data["authentication"]["credential_reference"] is not None
        or source["allowed_operations"] != [OPERATION]
        or source["path_templates"] != [PATH]
        or RANGE not in source["parameter_rules"]
        or limits["max_probe_bytes"] != BYTES
        or limits["max_sample_bytes"] != BYTES
        or limits["timeout_seconds"] != TIMEOUT
        or limits["retry_policy"] != "none"
        or set(data["response_contract"]["expected_media_types"]) != MEDIA
        or op["mode"] != "provider_specific"
        or op["operation"] != OPERATION
        or op["requires_credentials"] is not False
        or policy["dataset_rights_status"] != "verified"
        or policy["api_terms_status"] != "same_as_dataset"
        or policy["redistribution_status"] != "unknown"
        or policy["commercial_automation_status"] != "allowed"
        or data["implementation_decision"] != "build_adapter_now"
    ):
        raise Blocked("WESM original prefix request contract changed")
    return hashlib.sha256(raw).hexdigest()


def original_csv_column_header(raw: object) -> dict:
    """Keep only field names, never inspect or return the original data rows."""
    if type(raw) is not bytes or len(raw) != BYTES:
        raise Blocked("original source CSV prefix is not exactly 32768 bytes")
    end = raw.find(b"\n")
    if not 0 < end <= 8192:
        raise Blocked("no bounded first original CSV header line")
    header = raw[:end + 1]
    if b"\x00" in header:
        raise Blocked("original CSV header contains binary NUL")
    try:
        decoded = header.decode("utf-8-sig", "strict")
        names = next(csv.reader(io.StringIO(decoded), strict=True))
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise Blocked("invalid native USGS WESM original CSV header") from exc
    if not 5 <= len(names) <= 512 or len(set(names)) != len(names):
        raise Blocked("unbounded/ambiguous original USGS WESM column identifiers")
    if any(HEADER_NAME.fullmatch(x) is None for x in names):
        raise Blocked("unsupported or suspicious USGS CSV source column name")
    # Source work-unit quality logic is separately gated; do not assume the CSV
    # can be mapped to the exact 20260821 S1M Florida raster.
    return {
        "original_header_column_count": len(names),
        "original_header_names_sha256": hashlib.sha256(
            "\n".join(names).encode("ascii")).hexdigest(),
        "has_workunit_identity_field": any(
            n.lower() in {"workunit_id", "workunitid"} for n in names),
        "has_project_identity_field": any(
            n.lower() in {"project_id", "projectid"} for n in names),
        "has_seamless_quality_category_field": any(
            n.lower() in {"seamless_category", "seamlessstatus", "seamless_status"}
            for n in names),
        "original_data_row_values_read": False,
        "source_status_category_values_verified": False,
    }


def probe(
    *, opener: Callable = _open,
    clock: Callable = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT,
) -> dict:
    contract_sha = validate_contract(contract_path)
    req = request.Request(
        URL, method="GET", headers={
            "Range": RANGE,
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-USGS-WESM-Original-CSV/0.1",
        })
    try:
        with opener(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 206:
                raise Blocked("WESM original server did not honor exact HTTP206 Range")
            content_range = response.headers.get("Content-Range", "").strip()
            match = CONTENT_RANGE.fullmatch(content_range)
            if match is None:
                raise Blocked("invalid original WESM Content-Range")
            full_size = int(match.group(1))
            if not BYTES < full_size <= 2_000_000_000:
                raise Blocked("original WESM total bytes outside reviewed limits")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in MEDIA:
                raise Blocked("unexpected source MIME type for WESM CSV")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise Blocked("unreviewed WESM transfer content encoding")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isascii() or not length.isdecimal() or int(length) != BYTES):
                raise Blocked("unexpected WESM original Content-Length")
            raw = response.read(BYTES + 1)
            if len(raw) != BYTES:
                raise Blocked("unbounded or incomplete original WESM CSV prefix")
    except Blocked:
        raise
    except (OSError, TimeoutError, error.URLError) as exc:
        raise Blocked("one exact WESM original CSV request was unavailable") from exc
    observed_sha = hashlib.sha256(raw).hexdigest()
    if observed_sha != EXPECTED_PREFIX_SHA or full_size != EXPECTED_WHOLE_CSV_BYTES:
        raise Blocked("WESM original source prefix SHA or advertised entire-file size drift")
    columns = original_csv_column_header(raw)
    t = clock()
    if not isinstance(t, datetime) or t.utcoffset() is None:
        raise Blocked("source retrieval UTC not established")
    return {
        "profile": PROFILE, "source_id": "usgs.3dep.wesm.workunit-metadata",
        "original_url": URL, "original_range": RANGE,
        "retrieved_utc": t.astimezone(timezone.utc).isoformat(),
        "original_http_status": 206, "original_content_range": content_range,
        "original_prefix_bytes": len(raw),
        "original_prefix_sha256": observed_sha,
        "advertised_full_csv_bytes_not_full_hash": full_size,
        "request_sha256": hashlib.sha256(
            ("GET " + URL + "\nRange: " + RANGE + "\n").encode("ascii")).hexdigest(),
        "contract_sha256": contract_sha,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **columns,
        "full_original_wesm_csv_sha256_verified": False,
        "original_wesm_geopackage_verified": False,
        "florida_s1m_spatial_workunit_join_verified": False,
        "source_bytes_persisted": False, "neon_write_performed": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required before one exact USGS WESM GET")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
