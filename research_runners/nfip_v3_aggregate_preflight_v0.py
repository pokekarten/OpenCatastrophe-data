#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, aggregate-only NFIP v3 source preflight; never a CAT input admission.

Accepts two *locally obtained, rights-cleared, bounded* original OpenFEMA JSON
API responses. No network, provider rows, individual identifiers, locations or
input bytes are written to output. This is NOT a full-market/in-force estimator:
a bounded API page is incomplete unless independently proven otherwise.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys

LIMIT = 20_000_000
MAX_ROWS = 20_000
COUNTY = re.compile(r"^[0-9]{5}$")
SOURCE = {
    "claims": ("NfipClaims", "fema.openfema.nfip-redacted-claims.v3"),
    "policies": ("NfipPolicies", "fema.openfema.nfip-redacted-policies.v3"),
}

class SourceError(ValueError):
    pass

def _object_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise SourceError("duplicate JSON key")
        result[key] = value
    return result

def _bad_constant(value):
    raise SourceError("non-finite number")

def _read(path: Path, expected: str, key: str):
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SourceError("expected SHA-256 must be 64 lowercase hex characters")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise SourceError("unsafe, absent or oversized source input")
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise SourceError("source SHA-256 mismatch")
    try:
        data = json.loads(raw.decode("utf-8"), parse_float=Decimal,
                          parse_constant=_bad_constant, object_pairs_hook=_object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, InvalidOperation) as exc:
        raise SourceError("malformed source JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise SourceError("wrong v3 provider envelope: expected " + key)
    rows = data[key]
    if not rows or len(rows) > MAX_ROWS:
        raise SourceError("source page must contain 1..20000 rows")
    if any(not isinstance(row, dict) for row in rows):
        raise SourceError("malformed source row")
    ids = [row.get("id") for row in rows]
    if any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != len(ids):
        raise SourceError("missing or duplicate provider row IDs")
    return rows, len(raw), actual

def _date(value):
    if not isinstance(value, str) or len(value) < 10:
        raise SourceError("missing source date")
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise SourceError("invalid source date") from exc

def _county(row):
    value = row.get("countyCode")
    if not isinstance(value, str) or not COUNTY.fullmatch(value):
        raise SourceError("countyCode must be five source digits; no geocoding")
    return value

def _money(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise SourceError("invalid source amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise SourceError("invalid amount") from exc
    if not amount.is_finite():
        raise SourceError("non-finite source amount")
    return amount

def _safe_total(group, key):
    return str(group[key]) if group["missing"] == 0 else None

def summarize(claims: list[dict], policies: list[dict], as_of: date,
              minimum: int = 10) -> dict:
    if minimum < 10:
        raise SourceError("aggregate disclosure threshold cannot be below 10")
    loss = defaultdict(lambda: {"records": 0, "missing": 0, "paid": Decimal(0)})
    cover = defaultdict(lambda: {"records": 0, "missing": 0, "insured": Decimal(0)})
    for row in claims:
        county = _county(row)
        year = row.get("yearOfLoss")
        if isinstance(year, bool) or not isinstance(year, int) or not (1978 <= year <= 2100):
            raise SourceError("invalid yearOfLoss")
        group = loss[(county, year)]
        group["records"] += 1
        building = _money(row.get("amountPaidOnBuildingClaim"))
        contents = _money(row.get("amountPaidOnContentsClaim"))
        if building is None or contents is None:
            group["missing"] += 1
        else:
            group["paid"] += building + contents

    for row in policies:
        county = _county(row)
        effective = _date(row.get("policyEffectiveDate"))
        termination = _date(row.get("policyTerminationDate"))
        if termination <= effective:
            raise SourceError("invalid policy coverage interval")
        if effective <= as_of < termination:
            group = cover[county]
            group["records"] += 1
            insured = _money(row.get("totalBuildingInsuranceCoverage"))
            if insured is None:
                group["missing"] += 1
            else:
                group["insured"] += insured

    claims_result = []
    for (county, year), group in sorted(loss.items()):
        if group["records"] < minimum:
            continue
        claims_result.append({
            "county_code": county, "loss_year": year,
            "source_record_count": group["records"],
            "missing_payment_record_count": group["missing"],
            "recorded_paid_building_and_contents_usd": _safe_total(
                {"paid": group["paid"], "missing": group["missing"]}, "paid"),
        })
    policies_result = []
    for county, group in sorted(cover.items()):
        if group["records"] < minimum:
            continue
        policies_result.append({
            "county_code": county, "as_of_date": as_of.isoformat(),
            "source_active_transaction_record_count": group["records"],
            "missing_building_coverage_record_count": group["missing"],
            "recorded_building_coverage_usd": _safe_total(
                {"insured": group["insured"], "missing": group["missing"]}, "insured"),
        })
    return {
        "profile": "nfip-v3-aggregate-only-preflight-v0",
        "scope": "bounded_local_api_pages_research_only",
        "claims_by_county_loss_year": claims_result,
        "policies_in_force_by_county": policies_result,
        "suppressed_claim_groups": len(loss) - len(claims_result),
        "suppressed_policy_groups": len(cover) - len(policies_result),
        "minimum_group_records": minimum,
        "no_individual_join": True,
        "no_location_points": True,
        "no_full_program_estimate": True,
        "no_insurer_specific_portfolio": True,
        "model_input_admitted": False,
        "data_rights_cleared_by_this_script": False,
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims-json", type=Path, required=True)
    parser.add_argument("--claims-sha256", required=True)
    parser.add_argument("--policies-json", type=Path, required=True)
    parser.add_argument("--policies-sha256", required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args(argv)
    try:
        as_of = _date(args.as_of)
        claim_rows, claim_bytes, claim_sha = _read(
            args.claims_json, args.claims_sha256, SOURCE["claims"][0])
        policy_rows, policy_bytes, policy_sha = _read(
            args.policies_json, args.policies_sha256, SOURCE["policies"][0])
        result = summarize(claim_rows, policy_rows, as_of)
        result["inputs"] = {
            "claims": {"source_id": SOURCE["claims"][1], "endpoint": "NfipClaims/v3",
                       "sha256": claim_sha, "bytes": claim_bytes, "sample_rows": len(claim_rows)},
            "policies": {"source_id": SOURCE["policies"][1], "endpoint": "NfipPolicies/v3",
                         "sha256": policy_sha, "bytes": policy_bytes, "sample_rows": len(policy_rows)},
        }
    except (SourceError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
