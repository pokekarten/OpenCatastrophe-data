# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-byte, read-only receipts for three selected Hazard Plain 2026-10 CSVs.

Acquires original public CSVs in bounded memory only; checks the frozen
publisher manifest and independently rehashes CSV bytes, records and header
columns. Does not persist input, emit data rows, or admit scientific/insurance
model input. A successful receipt is NOT independent empirical validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from urllib.parse import urlsplit

from research_runners.hazardplain_202610_manifest_preflight_v0 import (
    EXPECTED_FILES, fetch_official_manifest, inspect_manifest,
)

BASE_URL = "https://files.hazardplain.org/r/2026-10/bulk/"
EXPECTED_MANIFEST_BYTES = 59508
EXPECTED_MANIFEST_SHA256 = "e04a707ab5b96a71e81f6ac29a584f3cb43acb5ec88c5e9669e092b5076434b4"
MAX_SINGLE_CSV_BYTES = 32 * 1024 * 1024
MAX_COLUMNS = 256
MAX_RECORDS = 100_000


class OriginalCSVError(ValueError):
    """A source release, exact-byte identity, or CSV structure check failed."""


class SameOriginalHostRedirect(urllib.request.HTTPRedirectHandler):
    """Prevent fetching unknown redirect targets before an HTTP request is made."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != "files.hazardplain.org":
            raise OriginalCSVError("original CSV redirect outside pinned publisher host")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def validate_pinned_manifest(original: bytes) -> dict:
    if (type(original) is not bytes or len(original) != EXPECTED_MANIFEST_BYTES
            or hashlib.sha256(original).hexdigest() != EXPECTED_MANIFEST_SHA256):
        raise OriginalCSVError("original publisher manifest exact-byte pin mismatch")
    inspect_manifest(original)  # existing v0 pinned release/lineage/size/column contract
    try:
        payload = json.loads(original.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OriginalCSVError("original manifest could not be decoded") from exc
    tables = {}
    for table in payload["tables"]:
        name = table.get("name")
        if type(name) is not str or name in tables:
            raise OriginalCSVError("duplicate provider table identity")
        tables[name] = table
    return tables


def verify_original_csv(raw: bytes, *, expected_bytes: int, expected_sha256: str,
                        expected_rows: int, expected_columns: list[str]) -> dict:
    """Bytes, header, and exact CSV row check; accepts only strict reviewed expectations."""
    if (type(expected_bytes) is not int or not 1 <= expected_bytes <= MAX_SINGLE_CSV_BYTES
            or type(expected_rows) is not int or not 1 <= expected_rows <= MAX_RECORDS
            or type(expected_columns) is not list
            or not 1 <= len(expected_columns) <= MAX_COLUMNS
            or any(type(x) is not str or not x.strip() for x in expected_columns)
            or len(set(expected_columns)) != len(expected_columns)
            or type(expected_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise OriginalCSVError("invalid pinned expected CSV contract")
    if type(raw) is not bytes or len(raw) != expected_bytes:
        raise OriginalCSVError("original CSV byte length mismatch")
    sha256 = hashlib.sha256(raw).hexdigest()
    if sha256 != expected_sha256:
        raise OriginalCSVError("original CSV SHA-256 mismatch")
    try:
        original_text = raw.decode("utf-8-sig", errors="strict")
        reader = csv.reader(io.StringIO(original_text, newline=""), strict=True)
        columns = next(reader)
        if (len(columns) != len(expected_columns) or len(set(columns)) != len(columns)
                or set(columns) != set(expected_columns)):
            raise OriginalCSVError("original CSV header disagrees with pinned manifest schema")
        rows = 0
        for record in reader:
            if len(record) != len(columns):
                raise OriginalCSVError("original CSV has inconsistent field counts")
            rows += 1
            if rows > expected_rows:
                raise OriginalCSVError("original CSV row count exceeds pinned provider manifest")
    except (UnicodeError, StopIteration, csv.Error) as exc:
        raise OriginalCSVError("original CSV cannot be parsed as bounded UTF-8 records") from exc
    if rows != expected_rows:
        raise OriginalCSVError("original CSV row count disagrees with pinned provider manifest")
    return {
        "original_bytes": len(raw),
        "original_sha256_computed": sha256,
        "record_count_verified": rows,
        "header_columns_verified": columns,
        "provider_checksum_independently_recomputed": True,
        "source_cell_values_emitted": False,
    }


def fetch_original(path: str, *, opener=None) -> bytes:
    if path not in EXPECTED_FILES:
        raise OriginalCSVError("unapproved provider file path")
    if opener is None:
        opener = urllib.request.build_opener(SameOriginalHostRedirect()).open
    url = BASE_URL + path
    request = urllib.request.Request(url, headers={
        "User-Agent": "OpenCatastrophe-original-CSV-byte-receipt/0.1",
        "Accept": "text/csv,application/octet-stream;q=0.8",
    })
    budget = min(MAX_SINGLE_CSV_BYTES, EXPECTED_FILES[path]["bytes"])
    with opener(request, timeout=45) as response:
        parsed = urlsplit(response.geturl())
        if parsed.scheme != "https" or parsed.hostname != "files.hazardplain.org":
            raise OriginalCSVError("original CSV final host changed")
        size_hint = response.headers.get("Content-Length")
        if size_hint is not None:
            if not size_hint.isdecimal() or int(size_hint) > budget:
                raise OriginalCSVError("original CSV content length exceeds reviewed limit")
        buf = bytearray()
        while True:
            part = response.read(128 * 1024)
            if not part:
                break
            if len(buf) + len(part) > budget:
                raise OriginalCSVError("original CSV streaming byte limit exceeded")
            buf.extend(part)
    return bytes(buf)


def audit_originals(*, fetch_manifest=fetch_official_manifest,
                    fetch_data=fetch_original) -> dict:
    original_manifest = fetch_manifest()
    tables = validate_pinned_manifest(original_manifest)
    results = []
    for path, expected in sorted(EXPECTED_FILES.items()):
        table = tables.get(expected["table"])
        if not table or type(table.get("columns")) is not list:
            raise OriginalCSVError("provider manifest table columns missing")
        original_csv = fetch_data(path)
        receipt = verify_original_csv(
            original_csv,
            expected_bytes=expected["bytes"], expected_sha256=expected["sha256"],
            expected_rows=expected["rows"], expected_columns=table["columns"],
        )
        results.append({"path": path, "upstream_sources": sorted(expected["sources"]), **receipt})
    return {
        "status": "EXACT_PROVIDER_CSV_BYTE_IDENTITY_VERIFIED_RESEARCH_ONLY",
        "release": "2026-10",
        "manifest_sha256_independently_verified": EXPECTED_MANIFEST_SHA256,
        "dataset_receipts": results,
        "dataset_bytes_written_to_repo_or_artifacts": False,
        "model_input_admitted": False,
        "scientific_independence_established": False,
        "insured_event_loss_or_aep_oep_computed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-live", action="store_true", required=True)
    parser.parse_args()
    try:
        print(json.dumps(audit_originals(), indent=2, sort_keys=True))
    except (OSError, TimeoutError, OriginalCSVError) as exc:
        print("BLOCKED: " + str(exc)[:160], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
