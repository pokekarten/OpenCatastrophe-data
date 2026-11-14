# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""TWIA Q4-2025 county/class aggregate preflight, research only.

Only consumes human-normalized, exact-schema CSVs in a rights-cleared working
area. This script never fetches/extracts a provider PDF or verifies that a
normalized row reproduces original provider data. No insurer property positions,
insured TIV, model loss distributions, treaty arrangements or licensing claim.

Two distinct input grains are required to make accidental double counting and
policies-versus-risks misinterpretation visible. Source: official 2025-12-31
TWIA Quarterly Liability Report, https://www.twia.org/about-us/financial-reports/
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

AS_OF = "2025-12-31"
COUNTIES = (
    "Aransas", "Brazoria", "Calhoun", "Cameron", "Chambers", "Galveston",
    "Harris", "Jefferson", "Kenedy", "Kleberg", "Matagorda", "Nueces",
    "Refugio", "San Patricio", "Willacy",
)
CLASSES = ("Commercial", "Manufactured Home", "Residential")
COUNTY_FIELDS = (
    "record_kind", "report_as_of", "county", "policies_in_force",
    "direct_liability_usd", "ytd_written_premium_usd",
)
CLASS_FIELDS = (
    "record_kind", "report_as_of", "county", "policy_class",
    "policies_in_force", "risks_in_force", "direct_liability_usd",
    "indirect_liability_usd", "ytd_written_premium_usd",
)
METRICS = (
    "policies_in_force", "risks_in_force", "direct_liability_usd",
    "indirect_liability_usd", "ytd_written_premium_usd",
)
# Official aggregate control figures, NOT a downloaded/provider-byte verification.
# Page 5 of 5: use 'SUM' in-force totals, never 'Risks Written YTD'.
PUBLISHED_CLASSES = {
    "Commercial": (8099, 16719, 11584286100, 226802179, 117408620),
    "Manufactured Home": (1850, 1850, 140801200, 0, 3739524),
    "Residential": (274897, 274897, 114730637300, 14569652580, 699716387),
}
PUBLISHED_TOTAL = (284846, 293466, 126455724600, 14796454759, 820864531)


class TWIAReconciliationError(ValueError):
    """Malformed or semantically unsafe normalized source extract."""


def _nonnegative_integer(value: str | None, field: str) -> int:
    if not isinstance(value, str) or len(value) > 18 or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise TWIAReconciliationError(f"{field}: require unsuppressed nonnegative integer without separators")
    return int(value)


def _read_csv(path: Path, expected_fields: tuple[str, ...], record_kind: str) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_bytes()
    if not raw or len(raw) > 2_000_000:
        raise TWIAReconciliationError("normalized CSV must be nonempty and <=2 MB")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TWIAReconciliationError("normalized CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(decoded, newline=""), strict=True)
    if reader.fieldnames != list(expected_fields):
        raise TWIAReconciliationError("unexpected header/order, duplicate or missing columns")
    seen: set[tuple[str, ...]] = set()
    result = []
    for row in reader:
        if None in row or any(val is None for val in row.values()):
            raise TWIAReconciliationError("malformed CSV with inconsistent row length")
        if row["record_kind"] != record_kind or row["report_as_of"] != AS_OF:
            raise TWIAReconciliationError("unexpected record kind or report snapshot")
        county = row["county"]
        if county not in COUNTIES:
            raise TWIAReconciliationError("unknown TWIA county (including partial Harris scope)")
        if record_kind == "county_class":
            policy_class = row["policy_class"]
            if policy_class not in CLASSES:
                raise TWIAReconciliationError("unknown TWIA liability-report class")
            key = (county, policy_class)
        else:
            key = (county,)
        if key in seen:
            raise TWIAReconciliationError("duplicate normalized source grain")
        seen.add(key)
        parsed = {x: _nonnegative_integer(row[x], x) for x in METRICS if x in row}
        parsed["county"] = county
        if record_kind == "county_class":
            parsed["policy_class"] = policy_class
            if parsed["risks_in_force"] < parsed["policies_in_force"]:
                raise TWIAReconciliationError("risk count cannot be less than policy count in a class")
            if policy_class != "Commercial" and parsed["risks_in_force"] != parsed["policies_in_force"]:
                raise TWIAReconciliationError("source report expects 1 risk per manufactured/residential policy")
        result.append(parsed)
    n = len(COUNTIES) * (len(CLASSES) if record_kind == "county_class" else 1)
    if len(result) != n:
        raise TWIAReconciliationError(f"incomplete {record_kind}: expected {n} unique rows")
    return result, hashlib.sha256(raw).hexdigest()


def _totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: sum(row.get(field, 0) for row in rows) for field in METRICS}


def _numeric_tuple(totals: dict[str, int]) -> tuple[int, ...]:
    return tuple(totals[field] for field in METRICS)


def reconcile(county_csv: Path, class_csv: Path, *, mode: str = "synthetic") -> dict[str, Any]:
    if mode not in {"synthetic", "published-2025"}:
        raise TWIAReconciliationError("unknown comparison mode")
    counties, county_sha = _read_csv(county_csv, COUNTY_FIELDS, "county")
    classes, class_sha = _read_csv(class_csv, CLASS_FIELDS, "county_class")
    county_index = {r["county"]: r for r in counties}
    class_totals = _totals(classes)
    county_totals = _totals(counties)
    mismatched_counties: list[str] = []
    for county in COUNTIES:
        from_classes = _totals([r for r in classes if r["county"] == county])
        given = county_index[county]
        if any(from_classes[field] != given[field] for field in (
            "policies_in_force", "direct_liability_usd", "ytd_written_premium_usd",
        )):
            mismatched_counties.append(county)
    observed_class_control_failures: list[str] = []
    if mode == "published-2025":
        for cls in CLASSES:
            cls_actual = _numeric_tuple(_totals([r for r in classes if r["policy_class"] == cls]))
            if cls_actual != PUBLISHED_CLASSES[cls]:
                observed_class_control_failures.append(cls)
        total_control_failed = _numeric_tuple(class_totals) != PUBLISHED_TOTAL
    else:
        total_control_failed = False  # no external official control applied to made-up study
    ok = not mismatched_counties and not observed_class_control_failures and not total_control_failed
    if county_totals["policies_in_force"] != class_totals["policies_in_force"]:
        ok = False
    if county_totals["direct_liability_usd"] != class_totals["direct_liability_usd"]:
        ok = False
    if county_totals["ytd_written_premium_usd"] != class_totals["ytd_written_premium_usd"]:
        ok = False
    return {
        "profile": "twia-q4-2025-normalized-county-class-reconciliation-v0",
        "report_as_of": AS_OF,
        "mode": mode,
        "scope": "TWIA wind-and-hail 14 Texas counties plus eligible part of Harris County",
        "county_rows": len(counties),
        "county_class_rows": len(classes),
        "normalization_county_sha256": county_sha,
        "normalization_class_sha256": class_sha,
        "total_policies_in_force": class_totals["policies_in_force"],
        "total_risks_in_force": class_totals["risks_in_force"],
        "total_direct_liability_usd": class_totals["direct_liability_usd"],
        "total_indirect_liability_usd": class_totals["indirect_liability_usd"],
        "total_ytd_written_premium_usd": class_totals["ytd_written_premium_usd"],
        "county_mismatches": mismatched_counties,
        "published_class_control_mismatches": observed_class_control_failures,
        "published_grand_total_mismatch": total_control_failed,
        "reconciled_at_normalized_grain": ok,
        "original_provider_bytes_verified": False,
        "source_licensing_admitted": False,
        "observed_insured_building_positions": False,
        "model_input_approved": False,
        "gross_net_reinsurance_verified": False,
        "note": "No actual PDF-to-row proof. Direct liability is NOT automatic building TIV; indirect liability is not another physical stock; policies differ from risks. No insurer-level GIS or CAT modelling approval.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--county-csv", required=True, type=Path)
    parser.add_argument("--county-class-csv", required=True, type=Path)
    parser.add_argument("--mode", choices=("synthetic", "published-2025"), default="synthetic")
    args = parser.parse_args()
    result = reconcile(args.county_csv, args.county_class_csv, mode=args.mode)
    print(json.dumps(result, sort_keys=True, indent=2))
    if not result["reconciled_at_normalized_grain"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
