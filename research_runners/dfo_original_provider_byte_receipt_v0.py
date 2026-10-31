#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verify the original DFO FloodRecords v0.9.0 CSV from the versioned publisher.

Source bytes are never committed or written by this tool. The report is
aggregate *format/provenance* evidence, not scientific or licence admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

from research_runners.dfo_floodrecords_csv_preflight_v0 import (
    DFOPreflightError, parse_dfo_csv,
)

VERSION_URL = "https://zenodo.org/records/19288171"
BYTES_URL = "https://zenodo.org/api/records/19288171/files/Global_Flood_Records.csv/content"
PUBLISHER_MD5 = "8fe3cd72474abe8d4d83641e2d33266f"
PUBLISHER_SIZE = 428865
MAX_SOURCE_BYTES = 1_000_000
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def fetch_publisher_bytes() -> bytes:
    request = urllib.request.Request(
        BYTES_URL,
        headers={"User-Agent": "OpenCatastropheDFOProvenance/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if not response.geturl().startswith("https://zenodo.org/"):
            raise DFOPreflightError("DFO original source redirected outside approved publisher host")
        blob = response.read(MAX_SOURCE_BYTES + 1)
    if len(blob) > MAX_SOURCE_BYTES:
        raise DFOPreflightError("DFO source exceeds maximum bounded read")
    return blob


def verify_source_bytes(
    blob: bytes,
    *,
    expected_size: int = PUBLISHER_SIZE,
    expected_publisher_md5: str = PUBLISHER_MD5,
    expected_sha256: str | None = None,
) -> dict:
    """Compare publisher byte receipt, then run strictly versioned CSV parser."""
    if type(blob) is not bytes or type(expected_size) is not int or expected_size <= 0:
        raise DFOPreflightError("invalid byte provenance input")
    if not 0 < len(blob) <= MAX_SOURCE_BYTES or len(blob) != expected_size:
        raise DFOPreflightError("DFO original source byte length mismatch")
    if not isinstance(expected_publisher_md5, str) or not re.fullmatch(r"[0-9a-f]{32}", expected_publisher_md5):
        raise DFOPreflightError("invalid pinned publisher MD5 syntax")
    if hashlib.md5(blob, usedforsecurity=False).hexdigest() != expected_publisher_md5:
        raise DFOPreflightError("DFO original source disagrees with Zenodo published MD5")
    observed_sha256 = hashlib.sha256(blob).hexdigest()
    if expected_sha256 is not None and (
        not isinstance(expected_sha256, str) or not SHA256.fullmatch(expected_sha256)
        or observed_sha256 != expected_sha256
    ):
        raise DFOPreflightError("DFO source SHA256 mismatch")
    inspection = parse_dfo_csv(blob)
    return {
        "schema_version": "dfo-original-byte-receipt-v0",
        "evidence_stage": "publisher_bytes_format_review_only",
        "source_url": VERSION_URL,
        "source_filename": "Global_Flood_Records.csv",
        "source_version": "0.9.0",
        "bytes": len(blob),
        "publisher_md5_verified": True,
        "observed_sha256": observed_sha256,
        "independently_pinned_sha256_verified": expected_sha256 is not None,
        "reported_event_count": inspection["reported_event_count"],
        "observed_first_start_date": inspection["observed_first_start_date"],
        "observed_last_end_date": inspection["observed_last_end_date"],
        "publisher_declared_end_year": inspection["provider_declared_release_end_year"],
        "events_beyond_publisher_declared_end_year": inspection["event_rows_reaching_beyond_declared_end_year"],
        "release_date_consistent_with_original_csv": inspection["published_release_end_year_consistent_with_csv"],
        "original_rows_emitted": False,
        "source_data_redistributed": False,
        "country_names_geocoded": False,
        "flood_depths_verified": False,
        "insured_losses_verified": False,
        "scientific_review_complete": False,
        "source_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="fetch pinned original CSV from official Zenodo")
    mode.add_argument("--file", type=Path, help="verify independently downloaded original CSV")
    parser.add_argument("--expected-sha256", type=str, help="independently confirmed exact original SHA256")
    parser.add_argument("--out", type=Path, help="optional metadata-only JSON receipt path")
    args = parser.parse_args()

    if args.file is not None and args.out is not None and args.file.resolve() == args.out.resolve():
        raise DFOPreflightError("output cannot overwrite the original source")
    blob = fetch_publisher_bytes() if args.fetch else args.file.read_bytes()
    report = verify_source_bytes(blob, expected_sha256=args.expected_sha256)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
