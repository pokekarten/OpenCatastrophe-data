# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare independently normalized Florida MIR statewide and county-ZIP research exports.

This tool does not fetch the OIR portal or certify that the source exports are
original, unfiltered, legally reusable, or CAT-model inputs. It enforces
matching date/scope/company/policy keys, preserving ZIPs that span counties.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

BASE_FIELDS = (
    "report_as_of", "scope_token", "naic_code", "reported_policy_type",
    "policies_in_force", "wind_structure_exposure_usd",
)
ZIP_FIELDS = BASE_FIELDS + ("county_key", "zip5")
CENT = Decimal("0.01")


class ExposureReconciliationError(ValueError):
    """Normalized input cannot be compared with sufficient semantic confidence."""


def _nonempty(text: str | None, name: str) -> str:
    if text is None or not text.strip():
        raise ExposureReconciliationError(f"missing {name}")
    return text.strip()


def _count(value: str) -> int:
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)", value):
        raise ExposureReconciliationError("policy count must be a nonnegative integer (no suppression codes)")
    return int(value)


def _money(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ExposureReconciliationError("wind structure exposure must be numeric USD") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ExposureReconciliationError("wind structure exposure must be finite nonnegative USD at <=2 decimals")
    return amount


def _read(path: Path, *, zip_scope: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExposureReconciliationError("CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    expected = ZIP_FIELDS if zip_scope else BASE_FIELDS
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ExposureReconciliationError("missing or duplicate header")
    if set(reader.fieldnames) != set(expected):
        raise ExposureReconciliationError(f"expected exact normalized columns: {','.join(expected)}")
    keys: set[tuple[str, ...]] = set()
    totals: dict[tuple[str, str], tuple[int, Decimal]] = {}
    periods: set[str] = set()
    scopes: set[str] = set()
    count_rows = 0
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ExposureReconciliationError("malformed CSV row or inconsistent column count")
        day = _nonempty(row["report_as_of"], "report_as_of")
        try:
            parsed_date = date.fromisoformat(day)
        except ValueError as exc:
            raise ExposureReconciliationError("report_as_of must be ISO date") from exc
        if parsed_date.isoformat() != day or day < "2025-01-01":
            raise ExposureReconciliationError("invalid Florida MIR monthly report date")
        period = day
        scope = _nonempty(row["scope_token"], "scope_token")
        if not re.fullmatch(r"[0-9]{5}", _nonempty(row["naic_code"], "naic_code")):
            raise ExposureReconciliationError("NAIC code must be exactly 5 digits")
        naic = row["naic_code"].strip()
        lob = _nonempty(row["reported_policy_type"], "reported_policy_type")
        count = _count(_nonempty(row["policies_in_force"], "policies_in_force"))
        value = _money(_nonempty(row["wind_structure_exposure_usd"], "wind_structure_exposure_usd"))
        key = (naic, lob)
        if zip_scope:
            county = _nonempty(row["county_key"], "county_key")
            zip5 = _nonempty(row["zip5"], "zip5")
            if not re.fullmatch(r"[0-9]{5}", zip5):
                raise ExposureReconciliationError("zip5 must be exactly 5 digits; preserve leading zeroes")
            unique_key = (period, scope, naic, lob, county, zip5)
        else:
            unique_key = (period, scope, naic, lob)
        if unique_key in keys:
            raise ExposureReconciliationError("duplicate normalized grain; do not double count")
        keys.add(unique_key)
        old = totals.get(key, (0, Decimal(0)))
        totals[key] = (old[0] + count, old[1] + value)
        periods.add(period)
        scopes.add(scope)
        count_rows += 1
    if count_rows == 0:
        raise ExposureReconciliationError("normalized source contains no observations")
    if len(periods) != 1 or len(scopes) != 1:
        raise ExposureReconciliationError("a normalized file must have one report date and one explicit selection scope")
    return {
        "source_rows": count_rows,
        "source_file_sha256": hashlib.sha256(raw).hexdigest(),
        "period": next(iter(periods)),
        "scope_token": next(iter(scopes)),
        "totals": totals,
    }


def reconcile(statewide: Path, county_zip: Path) -> dict[str, Any]:
    state = _read(statewide, zip_scope=False)
    regional = _read(county_zip, zip_scope=True)
    if state["period"] != regional["period"] or state["scope_token"] != regional["scope_token"]:
        raise ExposureReconciliationError("report date/selection scope differ; stop before comparing")
    a, b = state["totals"], regional["totals"]
    shared = a.keys() & b.keys()
    missing = a.keys() - b.keys()
    extra = b.keys() - a.keys()
    count_mismatch = sum(a[k][0] != b[k][0] for k in shared)
    wind_value_mismatch = sum(abs(a[k][1] - b[k][1]) > CENT for k in shared)
    passed = not missing and not extra and not count_mismatch and not wind_value_mismatch
    return {
        "schema": "fl-oir-company-county-zip-marginal-preflight-v0",
        "research_stage": "NORMALIZED_SOURCE_RECONCILIATION_ONLY",
        "report_as_of": state["period"],
        "source_selection_scope": state["scope_token"],
        "statewide_rows": state["source_rows"],
        "county_zip_rows": regional["source_rows"],
        "company_policy_keys_in_statewide": len(a),
        "matched_company_policy_keys": len(shared),
        "statewide_keys_missing_in_zip": len(missing),
        "zip_keys_missing_in_statewide": len(extra),
        "policy_count_mismatches": count_mismatch,
        "wind_structure_exposure_mismatches": wind_value_mismatch,
        "normalized_statewide_file_sha256": state["source_file_sha256"],
        "normalized_county_zip_file_sha256": regional["source_file_sha256"],
        "reconciled_at_normalized_grain": passed,
        "model_input_approved": False,
        "original_provider_bytes_verified": False,
        "individual_building_tiv_observed": False,
        "note": "A match checks only supplied normalized marginals. It cannot certify completeness, ZIP location, official provenance, commercial rights, insured building TIV, or CAT model readiness.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statewide-csv", type=Path, required=True)
    parser.add_argument("--county-zip-csv", type=Path, required=True)
    args = parser.parse_args()
    result = reconcile(args.statewide_csv, args.county_zip_csv)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    if not result["reconciled_at_normalized_grain"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
