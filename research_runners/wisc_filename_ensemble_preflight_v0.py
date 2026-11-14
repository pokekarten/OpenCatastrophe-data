# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded, offline provenance preflight for WISC synthetic storm file identities.

Only checks explicitly supplied file-name/hash manifest *claims*, not original
NetCDF bytes or a complete annual catalogue. Never authorizes annual EP.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

DATASET = "copernicus.c3s.wisc.synthetic-windstorms.22980"
SHA = re.compile(r"[a-f0-9]{64}\Z")
# Original guide's prose specifies %Y%m%d%H (10 digits), but its Table 4
# contains many observed 12-digit footprint identifiers (e.g. 199311201800).
# Keep that contradiction explicit rather than interpreting dates loosely.
FILENAME = re.compile(
    r"(?:C3S_EvenSet_)?fp_ga3ups_(?P<time>\d{12})_"
    r"(?P<track>\d{4})_(?P<method>\d{2})(?P<member>[1-5])_v1\.nc\Z"
)
METHODS = {"00": "unresolved_legacy_set", "12": "1.2", "20": "2.0", "30": "3.0"}
# Original Met Office C3S WISC Product User Guide, July 2 2026.
# These are gaps in *simulated observation* windows, NOT zero-event years.
GAPS = (
    (4, 198810, 199811),
    (3, 198812, 199003),
    (4, 200210, 200211),
    (5, 200812, 201002),
)
VALID_MONTHS = {1, 2, 3, 4, 5, 9, 10, 11, 12}
MAX_MANIFEST_BYTES = 4_000_000
MAX_FILENAMES = 22_980


class CatalogueError(ValueError):
    """A source claim cannot safely be converted into physical-event identity."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    obj: dict[str, object] = {}
    for k, v in pairs:
        if k in obj:
            raise CatalogueError("duplicate JSON object key")
        obj[k] = v
    return obj


def reject_constant(value: str) -> None:
    raise CatalogueError("non-finite JSON value")


def strict_json(raw: bytes) -> object:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_MANIFEST_BYTES:
        raise CatalogueError("manifest must be bounded nonempty bytes")
    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogueError("invalid strict UTF-8 JSON") from exc


def parse_wisc_filename(filename: str) -> dict[str, object]:
    if type(filename) is not str:
        raise CatalogueError("filename must be text")
    match = FILENAME.fullmatch(filename)
    if match is None:
        raise CatalogueError(
            "unsupported WISC filename: require published-table 12-digit median "
            "timestamp, 4-digit track and 3-digit method/member code"
        )
    group = match.groupdict()
    if group["method"] not in METHODS:
        raise CatalogueError("unreviewed two-digit method code: no inferred calibration set")
    try:
        stamp = datetime.strptime(group["time"], "%Y%m%d%H%M")
    except ValueError as exc:
        raise CatalogueError("invalid simulated storm median timestamp") from exc
    if not 1986 <= stamp.year <= 2011 or stamp.month not in VALID_MONTHS:
        raise CatalogueError("timestamp outside official 1986-2011 September-May support")
    member = int(group["member"])
    year_month = stamp.year * 100 + stamp.month
    for bad_member, first_month, last_month in GAPS:
        if member == bad_member and first_month <= year_month <= last_month:
            raise CatalogueError("storm timestamp falls inside published missing ensemble window")
    return {
        "simulated_median_time": stamp.strftime("%Y-%m-%dT%H:%M"),
        "simulated_year": stamp.year,
        "simulated_month": stamp.month,
        "source_track_id": group["track"],
        "method_code_in_filename": group["method"],
        "method_from_code_provisional": METHODS[group["method"]],
        "ensemble_member_from_filename": member,
        "same_simulated_track_candidate_key": f"{group['time']}_{group['track']}_{member}",
        "filename_method_and_ensemble_independently_verified_against_original_netcdf": False,
    }


def inspect_catalogue(raw: bytes, expected_sha256: str) -> dict[str, object]:
    if type(expected_sha256) is not str or SHA.fullmatch(expected_sha256) is None:
        raise CatalogueError("require valid exact original manifest SHA-256")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha256:
        raise CatalogueError("source manifest bytes differ from exact SHA-256")
    doc = strict_json(raw)
    if type(doc) is not dict or set(doc) != {
        "schema_version", "source_dataset_id", "records"
    }:
        raise CatalogueError("invalid metadata-only source manifest schema")
    if doc["schema_version"] != "wisc-filename-catalogue-v0" or doc["source_dataset_id"] != DATASET:
        raise CatalogueError("unsupported WISC source dataset or schema")
    rows = doc["records"]
    if type(rows) is not list or not 1 <= len(rows) <= MAX_FILENAMES:
        raise CatalogueError("source file count empty or unbounded")

    identities: dict[str, dict[str, object]] = {}
    storms: dict[str, set[str]] = defaultdict(set)
    counts: Counter[str] = Counter()
    years: set[int] = set()
    has_unresolved_legacy_code = False
    for idx, row in enumerate(rows):
        if type(row) is not dict or set(row) != {"filename", "original_file_sha256_claim"}:
            raise CatalogueError(f"record {idx}: unexpected metadata keys")
        fname, file_sha = row["filename"], row["original_file_sha256_claim"]
        if type(file_sha) is not str or SHA.fullmatch(file_sha) is None:
            raise CatalogueError(f"record {idx}: original source hash claim malformed")
        parsed = parse_wisc_filename(fname)
        if fname in identities:
            raise CatalogueError(f"record {idx}: duplicate original source filename")
        identities[fname] = parsed
        method = str(parsed["method_code_in_filename"])
        storms[str(parsed["same_simulated_track_candidate_key"])].add(method)
        counts[method] += 1
        years.add(int(parsed["simulated_year"]))
        has_unresolved_legacy_code |= method == "00"

    alternative_view_keys = sorted(k for k, methods in storms.items() if len(methods) > 1)
    return {
        "profile": "wisc_filename_ensemble_provenance_preflight_v0",
        "status": "manifest_claims_parsed_not_original_assets_verified",
        "source_dataset_id": DATASET,
        "manifest_sha256_verified": actual_sha,
        "file_count_claimed": len(rows),
        "distinct_simulated_track_candidates": len(storms),
        "same_track_multiple_method_candidates": len(alternative_view_keys),
        "alternative_view_key_examples_max_10": alternative_view_keys[:10],
        "method_code_counts": dict(sorted(counts.items())),
        "unresolved_legacy_method_codes_present": has_unresolved_legacy_code,
        "simulated_years_with_at_least_one_filename": sorted(years),
        "all_published_ensemble_gaps_checked": True,
        "published_missing_ensemble_month_intervals": [
            {"ensemble_member": m, "first_year_month": f, "last_year_month": t}
            for m, f, t in GAPS
        ],
        "guide_10_vs_table_12_digit_filename_discrepancy_acknowledged": True,
        "source_asset_sha256_claims_not_original_bytes_verified": True,
        "complete_source_event_catalogue_verified": False,
        "complete_ensemble_months_or_zero_event_years_verified": False,
        "source_events_independent_annual_occurrences_verified": False,
        "same_track_different_method_views_independent_events": False,
        "return_period_weights_verified": False,
        "annual_oep_aep_authorized": False,
        "oasis_financial_loss_or_calibration_established": False,
        "source_data_licence_and_admission_verified": False,
    }


def read_manifest(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise CatalogueError("manifest must be a real local file")
    if not 0 < path.stat().st_size <= MAX_MANIFEST_BYTES:
        raise CatalogueError("manifest outside bounded byte budget")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CatalogueError("cannot read original manifest bytes") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        report = inspect_catalogue(read_manifest(args.manifest), args.manifest_sha256)
    except (OSError, CatalogueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
