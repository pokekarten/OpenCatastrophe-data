#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hash one complete original USGS WESM CSV in memory and count quality statuses.

One exact read-only provider GET, no copies or raw rows logged, no GeoPackage,
spatial join, raster pixels or CAT admission. The 2026-11-16 original 32KiB
prefix SHA/Content-Range from merged PR #1735 is a strict precondition.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import ssl
import sys
from typing import Callable
from urllib import request, error

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path
from scripts import probe_usgs_wesm_original_csv32k_v0 as historical
from research_runners.usgs_wesm_seamless_workunit_quality_v0 import CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/usgs.3dep.wesm.csv.full-original-once.json"
URL = historical.URL
OPERATION = "one_wesm_original_csv_full_verified"
EXPECTED_BYTES = 2267051
PREFIX_BYTES = historical.BYTES
PREFIX_SHA = "19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d"
# Independently verified full original provider body: Actions job 133638077985.
EXPECTED_FULL_SHA = "a5f56b54f26767311156116b4721d477bf5d7b6069056117127898852d2d1b83"
HEADER_NAMES_SHA = "c2893167ec1839f74db9c67704f9f3fbd3c4ed9d6d65359bf1914ce19abb2746"
TIMEOUT = 30
MEDIA = frozenset({"text/csv", "text/plain", "application/octet-stream",
                   "binary/octet-stream", "application/vnd.ms-excel"})
MAX_ROWS = 100000
PROFILE = "oc-usgs-3dep-wesm-one-full-original-csv-v0"


class Blocked(ValueError):
    """Source-original scientific identity or row quality is unverified."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("original USGS WESM full CSV redirected")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()))
    return opener.open(req, timeout=timeout)


def validate_contract(path: Path = CONTRACT) -> str:
    raw = path.read_bytes()
    c = validate_path(path)
    rights = c["rights_and_policy"]
    limits = c["operational_constraints"]
    r = c["request_contract"]
    p = c["probe_contract"]
    if (
        c["access_id"] != "usgs.3dep.wesm.csv.full-original-once"
        or c["source_ids"] != ["usgs.3dep.wesm.workunit-metadata"]
        or c["status"] != "probe_ready"
        or c["interface_type"] != "http_file"
        or c["service_root"] != historical.HOST
        or c["access_scope"] != ["sample"]
        or c["authentication"]["mode"] != "none"
        or c["authentication"]["credential_reference"] is not None
        or r["allowed_operations"] != [OPERATION]
        or r["path_templates"] != [historical.PATH]
        or limits["max_probe_bytes"] != EXPECTED_BYTES
        or limits["max_sample_bytes"] != EXPECTED_BYTES
        or limits["timeout_seconds"] != TIMEOUT
        or limits["retry_policy"] != "none"
        or set(c["response_contract"]["expected_media_types"]) != MEDIA
        or p["mode"] != "provider_specific"
        or p["operation"] != OPERATION
        or p["requires_credentials"] is not False
        or rights["dataset_rights_status"] != "verified"
        or rights["api_terms_status"] != "same_as_dataset"
        or rights["redistribution_status"] != "unknown"
        or rights["commercial_automation_status"] != "allowed"
        or c["implementation_decision"] != "build_adapter_now"
        or historical.EXPECTED_PREFIX_SHA != PREFIX_SHA
        or historical.EXPECTED_WHOLE_CSV_BYTES != EXPECTED_BYTES
    ):
        raise Blocked("complete original WESM CSV source contract changed")
    return hashlib.sha256(raw).hexdigest()


def summarize_original_csv(data: bytes) -> dict:
    """Privacy-restricted row aggregates only, with no individual work-unit IDs."""
    if type(data) is not bytes or not data:
        raise Blocked("empty or non-byte WESM source")
    # Source bytes are never saved by this routine. Validate native UTF-8 CSV.
    try:
        src = data.decode("utf-8-sig", "strict")
        table = csv.reader(io.StringIO(src, newline=""), strict=True)
        names = next(table)
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise Blocked("WESM original source CSV encoding/header invalid") from exc
    if len(names) != 28 or len(set(names)) != 28 or any(not x.isascii() for x in names):
        raise Blocked("unreviewed original WESM header field cardinality")
    digest = hashlib.sha256("\n".join(names).encode("ascii")).hexdigest()
    if digest != HEADER_NAMES_SHA:
        raise Blocked("original WESM source header name SHA drift")
    keys = {name.lower(): index for index, name in enumerate(names)}
    required = {"workunit_id","project_id","lpc_category","sourcedem_category",
                "seamless_category","seamless_reason"}
    if not required.issubset(keys):
        raise Blocked("original WESM workunit/quality source field missing")
    states = {name: 0 for name in sorted(CATEGORIES["seamless_category"])}
    states["unknown_or_blank"] = 0
    missing_identity = 0
    duplicates = 0
    seen_ids = set()
    seen_pairs = set()
    seen_project_for_id = {}
    seen_status_for_id = {}
    repeated_workunit_project_rows = 0
    cross_project_reused_workunit_occurrences = 0
    conflicting_workunit_status_occurrences = 0
    rows = 0
    try:
        for row in table:
            if not row:
                continue
            rows += 1
            if rows > MAX_ROWS or len(row) != len(names):
                raise Blocked("WESM CSV row count or column shape outside reviewed bound")
            if any(len(v) > 16384 for v in row):
                raise Blocked("WESM original CSV contains an oversized field")
            workunit = row[keys["workunit_id"]]
            project = row[keys["project_id"]]
            if not workunit or not project:
                missing_identity += 1
            elif workunit in seen_ids:
                duplicates += 1
            else:
                seen_ids.add(workunit)
            status = row[keys["seamless_category"]]
            if workunit and project:
                pair = (workunit, project)
                if pair in seen_pairs:
                    repeated_workunit_project_rows += 1
                else:
                    seen_pairs.add(pair)
                if workunit in seen_project_for_id and seen_project_for_id[workunit] != project:
                    cross_project_reused_workunit_occurrences += 1
                else:
                    seen_project_for_id.setdefault(workunit, project)
                if workunit in seen_status_for_id and seen_status_for_id[workunit] != status:
                    conflicting_workunit_status_occurrences += 1
                else:
                    seen_status_for_id.setdefault(workunit, status)
            states[status if status in CATEGORIES["seamless_category"] else "unknown_or_blank"] += 1
    except (UnicodeError, csv.Error) as exc:
        raise Blocked("original WESM CSV rows are malformed") from exc
    if rows == 0:
        raise Blocked("source CSV has no complete WESM work units")
    return {
        "original_wesm_data_row_count": rows,
        "original_wesm_header_name_sha256": digest,
        "original_wesm_header_columns": len(names),
        "original_wesm_seamless_quality_category_counts": states,
        "missing_workunit_or_project_id_count": missing_identity,
        "duplicate_workunit_id_occurrences": duplicates,
        "duplicate_workunit_project_row_occurrences": repeated_workunit_project_rows,
        "reused_workunit_id_other_project_occurrences": cross_project_reused_workunit_occurrences,
        "reused_workunit_id_conflicting_seamless_category_occurrences": conflicting_workunit_status_occurrences,
        "workunit_duplicate_structure_scientifically_resolved": False,
        "has_unrecognized_seamless_quality_status": states["unknown_or_blank"] != 0,
        "all_original_quality_rows_scientifically_approved": False,
        "original_record_values_logged": False,
    }


def observe(*, opener: Callable = _open,
            clock: Callable = lambda: datetime.now(timezone.utc),
            contract_path: Path = CONTRACT) -> dict:
    contract_hash = validate_contract(contract_path)
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/octet-stream",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-USGS-WESM-Full-Original/0.1",
    })
    try:
        with opener(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 200:
                raise Blocked("original complete WESM CSV did not return HTTP 200")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if mime not in MEDIA:
                raise Blocked("unknown provider WESM full CSV Content-Type")
            if response.headers.get("Content-Encoding", "identity").lower().strip() != "identity":
                raise Blocked("original WESM complete CSV transfer encoding unexpected")
            length = response.headers.get("Content-Length")
            if length is not None and (
                not length.isascii() or not length.isdecimal() or int(length) != EXPECTED_BYTES
            ):
                raise Blocked("original WESM complete CSV Content-Length drift")
            raw = response.read(EXPECTED_BYTES + 1)
            if len(raw) != EXPECTED_BYTES:
                raise Blocked("original WESM CSV complete byte length drift")
    except Blocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise Blocked("one reviewed full WESM CSV source request unavailable") from exc

    prefix_sha = hashlib.sha256(raw[:PREFIX_BYTES]).hexdigest()
    if prefix_sha != PREFIX_SHA:
        raise Blocked("original complete CSV differs from previously verified WESM 32KiB header")
    complete_sha = hashlib.sha256(raw).hexdigest()
    if complete_sha != EXPECTED_FULL_SHA:
        raise Blocked("complete original WESM CSV SHA256 changed despite matching prefix and length")
    analysis = summarize_original_csv(raw)
    timestamp = clock()
    if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
        raise Blocked("observation lacks timezone-aware original UTC")
    return {
        "profile": PROFILE,
        "source_id": "usgs.3dep.wesm.workunit-metadata",
        "original_url": URL,
        "original_http_status": 200,
        "retrieved_utc": timestamp.astimezone(timezone.utc).isoformat(),
        "original_complete_csv_bytes": len(raw),
        "original_complete_csv_sha256": complete_sha,
        "original_header_prefix_sha256": prefix_sha,
        "original_request_sha256": hashlib.sha256(("GET " + URL + "\n").encode("ascii")).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "contract_sha256": contract_hash,
        **analysis,
        "original_geopackage_spatial_geometry_verified": False,
        "source_workunit_to_exact_florida_s1m_tile_verified": False,
        "original_s1m_pixel_lidar_quality_verified": False,
        "original_raw_provider_csv_bytes_persisted": False,
        "neon_write_performed": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for full exact USGS WESM original CSV")
    try:
        print(json.dumps(observe(), sort_keys=True, allow_nan=False))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
