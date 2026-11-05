#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-pinned EuroCropsV2 crop-code ↔ HCAT4 hierarchy QA.

This tool does not download, fix, admit or redistribute source data.
Only aggregate counts and public taxonomy keys are written to stdout.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha1
import io
import json
from pathlib import Path
import re
import sys

MAP_HEADER = (
    "nuts", "original_code", "original_name", "translated_name",
    "hcat4_code", "hcat4_name", "usage_code", "usage_name",
)
HCAT_HEADER = ("hcat4_code", "hcat4_name", "seasonality_code", "seasonality_name")
MAX_BYTES = 2_000_000
# Publisher's commit-pinned mapping contains one blank original-code sentinel
# per region (18 in this exact version). A sentinel is NOT a joinable crop code.
UNKNOWN_SENTINEL = {
    "original_code": "",
    "original_name": "",
    "translated_name": "",
    "hcat4_code": "3390000000",
    "hcat4_name": "not_known_and_other",
    "usage_code": "0",
    "usage_name": "No specified use",
}


class Blocked(ValueError):
    """Fail closed when the original bytes or schema cannot be established."""


def git_blob_sha(raw: bytes) -> str:
    """Git blob SHA-1, not SHA-256 of the file; matches GitHub contents SHA."""
    return sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _read_rows(raw: bytes, expected_sha: str, columns: tuple[str, ...]) -> list[dict]:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise Blocked("expected exact Git blob SHA-1 required")
    if not raw or len(raw) > MAX_BYTES or git_blob_sha(raw) != expected_sha:
        raise Blocked("original codebook size or Git blob SHA mismatch")
    try:
        source = io.StringIO(raw.decode("utf-8-sig"), newline="")
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != columns:
            raise Blocked("unexpected original codebook column names or order")
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise Blocked("malformed source CSV row width")
            rows.append(row)
            if len(rows) > 50000:
                raise Blocked("original codebook unexpectedly exceeds row limit")
        if not rows:
            raise Blocked("original codebook empty")
    except (UnicodeError, csv.Error) as exc:
        raise Blocked("invalid original codebook text or CSV") from exc
    return rows


def audit(mapping_raw: bytes, mapping_git_sha: str,
          hierarchy_raw: bytes, hierarchy_git_sha: str) -> dict:
    mappings = _read_rows(mapping_raw, mapping_git_sha, MAP_HEADER)
    taxonomy = _read_rows(hierarchy_raw, hierarchy_git_sha, HCAT_HEADER)
    taxonomy_codes: set[str] = set()
    for row in taxonomy:
        code = row["hcat4_code"].strip()
        if not code or not code.isdecimal() or code in taxonomy_codes:
            raise Blocked("empty, non-numeric or duplicate HCAT4 hierarchy code")
        taxonomy_codes.add(code)
    observed_pairs: set[tuple[str, str]] = set()
    sentinel_regions: set[str] = set()
    per_region: Counter[str] = Counter()
    gaps = []
    for row in mappings:
        region = row["nuts"].strip()
        code = row["original_code"].strip()
        hcat = row["hcat4_code"].strip()
        if not re.fullmatch(r"[a-z][a-z0-9]{0,5}", region):
            raise Blocked("malformed regional original codebook region")
        per_region[region] += 1
        if not code:
            # One *exact* publisher-specified blank sentinel per region.
            # Never form a mapping key ("de4", "") and never infer a crop.
            if (any(row.get(k) != v for k, v in UNKNOWN_SENTINEL.items())
                    or region in sentinel_regions):
                raise Blocked("malformed or duplicate unknown-crop sentinel")
            if hcat not in taxonomy_codes:
                raise Blocked("publisher unknown-crop sentinel absent from HCAT4")
            sentinel_regions.add(region)
            continue
        if not hcat.isdecimal():
            raise Blocked("missing or malformed regional original code / HCAT4")
        key = region, code
        if key in observed_pairs:
            raise Blocked("duplicate NUTS+original_code mapping would multiply asset rows")
        observed_pairs.add(key)
        if hcat not in taxonomy_codes:
            gaps.append({
                "nuts": region,
                "original_code": code,
                "hcat4_code": hcat,
                "mapped_name": row["hcat4_name"],
            })
    return {
        "profile": "eurocrops-v2-original-codebook-crosswalk-qc-v0",
        "mapping_git_blob_sha1": mapping_git_sha,
        "hierarchy_git_blob_sha1": hierarchy_git_sha,
        "mapping_rows": len(mappings),
        "joinable_original_code_rows": len(observed_pairs),
        "unknown_cultivation_sentinel_rows_not_joinable": len(sentinel_regions),
        "unknown_cultivation_sentinel_regions": sorted(sentinel_regions),
        "hierarchy_rows": len(taxonomy),
        "region_count": len(per_region),
        "mapping_rows_by_region": dict(sorted(per_region.items())),
        "unresolved_hcat4_reference_count": len(gaps),
        "unresolved_hcat4_references": sorted(gaps, key=lambda r: (r["nuts"], r["original_code"])),
        "source_bytes_committed": False,
        "codebook_is_original_insurer_or_crop_field_data": False,
        "research_only_not_admitted": True,
        "safe_for_insured_value_or_cat_model": False,
    }



def sample_mapping_coverage(
    parcel_rows: list[dict], region: str,
    mapping_rows: list[dict], hierarchy_rows: list[dict],
) -> dict:
    """Return ONLY sample counts: never provider crop codes, names, parcel IDs or locations.

    Crop-code keys are exact region+original string; coercing numeric codes
    silently loses leading zeroes and can cross-classify other regions.
    """
    if not isinstance(region, str) or not re.fullmatch(r"[a-z][a-z0-9]{0,5}", region):
        raise Blocked("invalid source region")
    if not parcel_rows or len(parcel_rows) > 5000:
        raise Blocked("source sample must have 1..5000 rows")
    mapping = {}
    sentinel_regions: set[str] = set()
    for row in mapping_rows:
        if row["original_code"] == "":
            if (any(row.get(k) != v for k, v in UNKNOWN_SENTINEL.items())
                    or row["nuts"] in sentinel_regions):
                raise Blocked("malformed or duplicate unknown-crop sentinel")
            sentinel_regions.add(row["nuts"])
            continue
        key = (row["nuts"], row["original_code"])
        if key in mapping:
            raise Blocked("ambiguous source crop mapping")
        mapping[key] = row["hcat4_code"]
    if not any(key[0] == region for key in mapping):
        raise Blocked("region missing from original codebook")
    taxonomy = {row["hcat4_code"] for row in hierarchy_rows}
    result = {
        "sampled_rows": len(parcel_rows),
        "resolved_to_hcat4_rows": 0,
        "code_not_in_region_mapping_rows": 0,
        "mapping_to_missing_hcat4_rows": 0,
        "blank_or_nonstring_original_code_rows": 0,
    }
    for row in parcel_rows:
        code = row.get("original_code")
        if not isinstance(code, str) or not code or code.strip() != code:
            result["blank_or_nonstring_original_code_rows"] += 1
            continue
        hcat = mapping.get((region, code))
        if hcat is None:
            result["code_not_in_region_mapping_rows"] += 1
        elif hcat not in taxonomy:
            result["mapping_to_missing_hcat4_rows"] += 1
        else:
            result["resolved_to_hcat4_rows"] += 1
    if sum(v for k, v in result.items() if k != "sampled_rows") != len(parcel_rows):
        raise Blocked("crop crosswalk did not conserve parcel sample counts")
    return result


def _read_local(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise Blocked("input must be a bounded regular local file, not a symlink")
    return path.read_bytes()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mapping", type=Path, required=True)
    p.add_argument("--mapping-git-blob-sha1", required=True)
    p.add_argument("--hierarchy", type=Path, required=True)
    p.add_argument("--hierarchy-git-blob-sha1", required=True)
    args = p.parse_args(argv)
    try:
        result = audit(_read_local(args.mapping), args.mapping_git_blob_sha1,
                       _read_local(args.hierarchy), args.hierarchy_git_blob_sha1)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
