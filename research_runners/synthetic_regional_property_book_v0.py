# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conserve fictional residential-building contract stocks and gross written premiums.

Independent synthetic sensitivity study ONLY. Year-end contracts are not
physical buildings; annual written gross premiums / end-year contracts are
not actuarial rates; market elemental penetration does not reveal a carrier's
elemental penetration. No real risk sites, insurer TIV, CAT losses or treaties.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re


class SyntheticBookError(ValueError):
    """A scenario is semantically invalid, infeasible or underidentified."""


_DIGITS = re.compile(r"(?:0|[1-9][0-9]{0,15})\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,6})?\Z")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_FIELDS = {"schema_version", "scenario_kind", "reporting_scope", "year_end",
           "contract_population", "premium_population", "geography_status",
           "take_up_status", "synthetic_total_year_end_contracts",
           "synthetic_total_written_gwp_eur_cents", "regions"}
_REGION_FIELDS = {"region_code", "hypothetical_contract_capacity",
                  "contract_prior_weight", "premium_relativity",
                  "hypothetical_market_elemental_share", "assumed_carrier_uptake_multiplier"}


def _integer(value: object, name: str, ceiling: int) -> int:
    if not isinstance(value, str) or not _DIGITS.fullmatch(value):
        raise SyntheticBookError(f"{name}: nonnegative integer decimal string required")
    n = int(value)
    if n > ceiling:
        raise SyntheticBookError(f"{name}: bounded synthetic limit exceeded")
    return n


def _fraction(value: object, name: str, ceiling: str = "1000000000000",
              positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise SyntheticBookError(f"{name}: bounded nonnegative decimal required")
    n = Decimal(value)
    if n > Decimal(ceiling) or (positive and not n > 0):
        raise SyntheticBookError(f"{name}: outside supported synthetic range")
    return n


def _capped_contracts(total: int, prior: dict[str, Decimal],
                      capacity: dict[str, int]) -> dict[str, int]:
    """Deterministic weighted water fill + exact capacity-safe Hamilton rounding."""
    if total > sum(capacity.values()):
        raise SyntheticBookError("contract total exceeds all regional capacities")
    result = {k: 0 for k in sorted(prior)}
    available = {k for k in prior if capacity[k] > 0}
    remaining = total
    while remaining:
        if not available:
            raise SyntheticBookError("insufficient geographic capacity")
        denominator = sum((prior[k] for k in available), Decimal(0))
        ideal = {k: Decimal(remaining) * prior[k] / denominator for k in available}
        saturated = [k for k in available if ideal[k] >= capacity[k] - result[k]]
        if saturated:
            for k in sorted(saturated):
                increment = capacity[k] - result[k]
                result[k] += increment
                remaining -= increment
                available.remove(k)
            continue
        floors = {k: int(v.to_integral_value(rounding=ROUND_FLOOR))
                  for k, v in ideal.items()}
        for k in floors:
            result[k] += floors[k]
        residual = remaining - sum(floors.values())
        if not 0 <= residual <= len(available):
            raise SyntheticBookError("integer residual failed")
        ranked = sorted(available, key=lambda k: (-(ideal[k] - floors[k]), k))
        for k in ranked[:residual]:
            if result[k] >= capacity[k]:
                raise SyntheticBookError("integer residual violates capacity")
            result[k] += 1
        remaining = 0
    if sum(result.values()) != total or any(result[k] > capacity[k] for k in result):
        raise SyntheticBookError("contract conservation failed")
    return result


def _exact_cent_split(total: int, weights: dict[str, Decimal]) -> dict[str, int]:
    """Distribute whole euro-cents exactly without creating premium."""
    result = {k: 0 for k in sorted(weights)}
    positive = {k: w for k, w in weights.items() if w > 0}
    if total and not positive:
        raise SyntheticBookError("no positive support for annual written premiums")
    if not total:
        return result
    denominator = sum(positive.values(), Decimal(0))
    ideal = {k: Decimal(total) * w / denominator for k, w in positive.items()}
    for k, v in ideal.items():
        result[k] = int(v.to_integral_value(rounding=ROUND_FLOOR))
    remainder = total - sum(result.values())
    ranked = sorted(ideal, key=lambda k: (-(ideal[k] - result[k]), k))
    for k in ranked[:remainder]:
        result[k] += 1
    if sum(result.values()) != total:
        raise SyntheticBookError("annual written premium conservation failed")
    return result


def allocate_synthetic_regional_book(raw: dict) -> dict:
    """No data admission and NO claim of actual company geography or CAT cover."""
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise SyntheticBookError("scenario must exactly match synthetic region v0 schema")
    if (raw["schema_version"] != "0.1.0"
            or raw["scenario_kind"] != "fully_synthetic_test_only"
            or raw["reporting_scope"] != "fictional_solo_direct_residential_building"
            or raw["contract_population"] != "at_least_one_year_contracts_at_year_end_not_buildings"
            or raw["premium_population"] != "annual_direct_gross_written_eur_cents_not_tariff"
            or raw["geography_status"] != "hypothetical_not_insurer_observed"
            or raw["take_up_status"] != "hypothetical_market_reference_not_carrier_observed"):
        raise SyntheticBookError("unsupported source authority, geography or accounting semantics")
    year = raw["year_end"]
    if not isinstance(year, str):
        raise SyntheticBookError("year_end must be ISO 31 December")
    try:
        if date.fromisoformat(year).isoformat() != year or not year.endswith("-12-31"):
            raise ValueError("non-calendar end")
    except ValueError as exc:
        raise SyntheticBookError("year_end must be ISO 31 December") from exc
    count = _integer(raw["synthetic_total_year_end_contracts"], "contract_count", 1_000_000_000)
    cents = _integer(raw["synthetic_total_written_gwp_eur_cents"], "written_gwp", 1_000_000_000_000_000)
    if not count or not cents:
        raise SyntheticBookError("positive fictional contract total and written gross premium required")
    regions = raw["regions"]
    if not isinstance(regions, list) or not 2 <= len(regions) <= 500:
        raise SyntheticBookError("expected 2..500 fictional regions")
    capacity, weights, premium_weights, market, company_uplift = {}, {}, {}, {}, {}
    for row in regions:
        if not isinstance(row, dict) or set(row) != _REGION_FIELDS:
            raise SyntheticBookError("invalid fictional region row")
        name = row["region_code"]
        if not isinstance(name, str) or not _CODE.fullmatch(name) or name in capacity:
            raise SyntheticBookError("duplicate or invalid fictional region code")
        capacity[name] = _integer(row["hypothetical_contract_capacity"], name+"/capacity", 1_000_000_000)
        weights[name] = _fraction(row["contract_prior_weight"], name+"/weight", positive=True)
        premium_weights[name] = _fraction(row["premium_relativity"], name+"/premium_weight", positive=True)
        market[name] = _fraction(row["hypothetical_market_elemental_share"], name+"/market_share", ceiling="1")
        company_uplift[name] = _fraction(row["assumed_carrier_uptake_multiplier"], name+"/carrier_multiplier", ceiling="10")
    contract_counts = _capped_contracts(count, weights, capacity)
    premiums = _exact_cent_split(cents, {k: Decimal(contract_counts[k])*premium_weights[k]
                                         for k in contract_counts})
    rows = []
    for k in sorted(capacity):
        # This is NOT an observed company take-up: the multiplier is arbitrary.
        share = min(Decimal(1), market[k]*company_uplift[k])
        covered = int((Decimal(contract_counts[k])*share).to_integral_value(rounding=ROUND_HALF_UP))
        rows.append({"region_code": k,
                     "synthetic_contracts_at_year_end": contract_counts[k],
                     "hypothetical_regional_annual_gwp_eur_cents": premiums[k],
                     "hypothetical_elemental_cover_contract_equivalents": covered,
                     "hypothetical_region_risk_sites_observed": False})
    digest = hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")).hexdigest()
    return {"schema_version":"0.1.0", "scenario_kind":"fully_synthetic_test_only",
            "scenario_sha256": digest, "year_end": year, "regions": rows,
            "synthetic_total_contracts_conserved": sum(contract_counts.values()) == count,
            "synthetic_total_annual_written_gwp_cents_conserved": sum(premiums.values()) == cents,
            "contract_count_is_insured_building_count": False,
            "market_elemental_take_up_is_insurer_take_up": False,
            "regional_contract_counts_are_observed": False, "regional_premiums_are_observed": False,
            "annual_written_premium_per_year_end_contract_is_tariff": False,
            "has_true_risk_site_coordinates": False, "has_insured_tiv": False,
            "has_event_or_cat_losses": False, "has_reinsurance_treaties": False,
            "model_input_approved": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()
    try:
        if args.scenario.stat().st_size > 1_000_000:
            raise SyntheticBookError("scenario larger than 1 MB")
        scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
        result = allocate_synthetic_regional_book(scenario)
    except (OSError, UnicodeError, json.JSONDecodeError, SyntheticBookError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
