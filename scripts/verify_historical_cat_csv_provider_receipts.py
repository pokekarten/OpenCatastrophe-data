#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reproduce exact provider CSV-byte receipts for two nonadmitted CAT inputs.

--fetch accesses only two version-pinned Zenodo API URLs; it never persists
raw provider rows. Offline mode accepts explicitly downloaded source files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research_runners.historical_cat_benchmark_csv_preflight_v0 import (  # noqa: E402
    SourcePreflightError, inspect_hanze_v302, inspect_residential_v2025,
)

from research_runners.historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT  # noqa: E402
PROFILE = {
    "hanze_v3_0_2_beta": inspect_hanze_v302,
    "residential_v2025": inspect_residential_v2025,
}
MAX_BYTES = 2_000_000


def read_receipt() -> dict:
    record = SOURCE_RECEIPT
    if record.get("schema_version") != "research-source-byte-receipt-v0":
        raise SourcePreflightError("unsupported provider-byte receipt schema")
    if set(record.get("sources", {})) != set(PROFILE):
        raise SourcePreflightError("unexpected source identities in receipt")
    return record


def fetch_pinned(record: dict) -> bytes:
    url = record["api_url"]
    if not url.startswith("https://zenodo.org/api/records/"):
        raise SourcePreflightError("untrusted publisher URL")
    req = urllib.request.Request(url, headers={"User-Agent": "OpenCatastropheResearchReceipts/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        if not response.geturl().startswith("https://zenodo.org/"):
            raise SourcePreflightError("source redirected outside official publisher")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise SourcePreflightError("source exceeds size limit")
    return raw


def verify_one(key: str, raw: bytes, record: dict) -> dict:
    if key not in PROFILE:
        raise SourcePreflightError("unknown source")
    if type(raw) is not bytes or len(raw) != record["bytes"]:
        raise SourcePreflightError(f"{key}: byte length mismatch")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != record["observed_sha256"]:
        raise SourcePreflightError(f"{key}: SHA256 mismatch")
    md5 = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    if md5 != record["publisher_md5"]:
        raise SourcePreflightError(f"{key}: publisher MD5 mismatch")
    profile = PROFILE[key](raw, digest)
    for field, expected in record["required_profile"].items():
        if profile.get(field) != expected:
            raise SourcePreflightError(f"{key}: observed profile drift in {field}")
    if profile.get("source_admitted") or profile.get("provider_rows_exported"):
        raise SourcePreflightError("non-admission invariant violated")
    return {"source": key, "bytes": len(raw), "sha256": digest,
            "profile": profile, "model_admission": False}


def verify_pair(hanze: bytes, residential: bytes, receipt: dict) -> dict:
    return {
        "schema_version": "research-source-byte-receipt-check-v0",
        "source_admitted": False,
        "insured_loss_or_asset_tiv_created": False,
        "results": [
            verify_one("hanze_v3_0_2_beta", hanze, receipt["sources"]["hanze_v3_0_2_beta"]),
            verify_one("residential_v2025", residential, receipt["sources"]["residential_v2025"]),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="fetch only pinned public provider URLs")
    mode.add_argument("--hanze-csv", type=Path, help="offline source path")
    parser.add_argument("--residential-csv", type=Path)
    parser.add_argument("--output", type=Path, help="optional metadata-only output file")
    args = parser.parse_args(argv)
    records = read_receipt()
    if args.fetch:
        if args.residential_csv is not None:
            parser.error("--fetch cannot be combined with offline CSV arguments")
        hanze = fetch_pinned(records["sources"]["hanze_v3_0_2_beta"])
        residential = fetch_pinned(records["sources"]["residential_v2025"])
    else:
        if args.residential_csv is None:
            parser.error("--residential-csv required with --hanze-csv")
        hanze = args.hanze_csv.read_bytes()
        residential = args.residential_csv.read_bytes()
    report = verify_pair(hanze, residential, records)
    output = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
