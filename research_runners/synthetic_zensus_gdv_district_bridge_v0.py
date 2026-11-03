# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only Zensus-vintage -> insurer-scenario *assumption* bridge.

This adapter does not retrieve, parse, redistribute or automatically mine
GDV data. It consumes ONLY independent fictional regional controls, with a
2022-05-15 Zensus-like building-stock universe and 2025-12-31 GDV-like
insurance penetration assumptions. It reconciles two alternative geographic
prior scenarios to the same fictional 2025 insurer contract and gross-written
premium totals. It MUST NOT represent actual insured building positions.

No real Census/GDV/insurer file has been acquired or admitted here.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re

from synthetic_regional_property_book_v0 import (
    SyntheticBookError, allocate_synthetic_regional_book,
)

_FIELDS = {"schema_version", "scenario_kind", "country", "geo_scope",
           "zensus_vintage", "market_cover_vintage", "company_reporting_year_end",
           "zensus_population", "market_cover_population",
           "issuer_population", "gwp_basis", "gdv_extraction_status",
           "source_bytes_status", "fictional_carrier_contract_count",
           "fictional_annual_direct_gwp_eur_cents", "districts"}
_DISTRICT_FIELDS = {"kreis_ags_2022", "fictional_residential_buildings_2022",
                    "hypothetical_building_growth_factor_to_2025",
                    "hypothetical_contract_equivalents_per_building_capacity",
                    "carrier_prior_affinity_a", "carrier_prior_affinity_b",
                    "hypothetical_market_elemental_cover_share",
                    "hypothetical_carrier_elemental_multiplier",
                    "hypothetical_written_premium_relativity"}
_NUM = re.compile(r"(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,6})?\Z")
_COUNT = re.compile(r"(?:0|[1-9][0-9]{0,14})\Z")
_KREIS = re.compile(r"(?:0[1-9]|1[0-6])[0-9]{3}\Z")


def _decimal(value: object, field: str, *, lo: str = "0",
             hi: str = "10", strict: bool = False) -> Decimal:
    if not isinstance(value, str) or not _NUM.fullmatch(value):
        raise SyntheticBookError(field + ": nonnegative bounded decimal string required")
    n = Decimal(value)
    if n < Decimal(lo) or n > Decimal(hi) or (strict and n == 0):
        raise SyntheticBookError(field + ": scenario factor outside permitted range")
    return n


def _int(value: object, field: str, hi: int) -> int:
    if not isinstance(value, str) or not _COUNT.fullmatch(value):
        raise SyntheticBookError(field + ": canonical integer string required")
    n = int(value)
    if n > hi:
        raise SyntheticBookError(field + ": unsupported synthetic size")
    return n


def _six(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


def compare_fictional_district_priors(raw: dict) -> dict:
    """Calculate two alternative 2025 books from a declared 2022/25 bridge.

    All building counts, market take-up shares, issuer marginals, growth
    factors, mapping of contracts/buildings and company geographic shares
    must be INVENTED fixtures for this version. This isolates a meaningful
    scientific nonidentifiability test while source licences remain gated.
    """
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise SyntheticBookError("regional evidence bridge requires exact synthetic schema")
    contract = {
        "schema_version": "0.1.0",
        "scenario_kind": "fully_synthetic_test_only",
        "country": "DE", "geo_scope": "kreis_ags_as_of_2022_05_15",
        "zensus_vintage": "2022-05-15", "market_cover_vintage": "2025-12-31",
        "company_reporting_year_end": "2025-12-31",
        "zensus_population": "buildings_with_residential_use_not_dwellings",
        "market_cover_population": "hypothetical_industry_full_elemental_cover_not_carrier",
        "issuer_population": "fictional_year_end_annual_duration_contracts_not_buildings",
        "gwp_basis": "fictional_annual_direct_gross_written_eur_cents",
        "gdv_extraction_status": "no_gdv_original_data_mining_or_acquisition",
        "source_bytes_status": "no_real_source_bytes_used",
    }
    if any(raw.get(k) != v for k, v in contract.items()):
        raise SyntheticBookError("source year / rights / geographic / population semantics mismatch")
    count = _int(raw["fictional_carrier_contract_count"], "issuer_contracts", 1_000_000_000)
    cents = _int(raw["fictional_annual_direct_gwp_eur_cents"], "issuer_gwp", 1_000_000_000_000_000)
    if not count or not cents:
        raise SyntheticBookError("fictional national company controls must both be positive")
    districts = raw["districts"]
    if not isinstance(districts, list) or not 2 <= len(districts) <= 500:
        raise SyntheticBookError("expected 2..500 explicit fictional district controls")
    cases = {"A": [], "B": []}
    ages = set()
    support = {}
    for row in districts:
        if not isinstance(row, dict) or set(row) != _DISTRICT_FIELDS:
            raise SyntheticBookError("district needs exact building/cover/capacity/affinity fields")
        district = row["kreis_ags_2022"]
        if not isinstance(district, str) or not _KREIS.fullmatch(district) or district in ages:
            raise SyntheticBookError("invalid or duplicate 2022 five-digit Kreis AGS")
        ages.add(district)
        buildings = _int(row["fictional_residential_buildings_2022"], "residential_buildings", 50_000_000)
        if buildings == 0:
            raise SyntheticBookError("zero/suppressed building population cannot establish a positive prior")
        growth = _decimal(row["hypothetical_building_growth_factor_to_2025"],
                          "2022-to-2025 growth", lo="0.5", hi="2", strict=True)
        contracts_per_building = _decimal(row["hypothetical_contract_equivalents_per_building_capacity"],
                                           "contract-to-building assumption", lo="0.1", hi="5", strict=True)
        market = _decimal(row["hypothetical_market_elemental_cover_share"],
                           "industry market elemental cover", hi="1")
        carrier = _decimal(row["hypothetical_carrier_elemental_multiplier"],
                            "company-vs-market elemental cover", hi="10")
        relativity = _decimal(row["hypothetical_written_premium_relativity"],
                               "premium relativity", lo="0.01", hi="10", strict=True)
        cap = int((Decimal(buildings) * growth * contracts_per_building).to_integral_value(
                  rounding=ROUND_CEILING))
        if cap > 1_000_000_000:
            raise SyntheticBookError("hypothetical contract capacity exceeds simulation bounds")
        support[district] = {
            "fictional_building_stock_2022": buildings,
            "hypothetical_2025_contract_equivalent_capacity": cap,
        }
        for case in ("A", "B"):
            affinity = _decimal(row[f"carrier_prior_affinity_{case.lower()}"],
                                "carrier geographic affinity", lo="0.01", hi="10", strict=True)
            prior = Decimal(buildings) * growth * affinity
            region = {
                "region_code": "KREIS_" + district,
                "hypothetical_contract_capacity": str(cap),
                "contract_prior_weight": _six(prior),
                "premium_relativity": _six(relativity),
                "hypothetical_market_elemental_share": _six(market),
                "assumed_carrier_uptake_multiplier": _six(carrier),
            }
            cases[case].append(region)
    if count > sum(x["hypothetical_2025_contract_equivalent_capacity"] for x in support.values()):
        raise SyntheticBookError("fictional insurer count exceeds regional assumed capacity")
    result = {}
    for case in ("A", "B"):
        scenario = {
            "schema_version": "0.1.0", "scenario_kind": "fully_synthetic_test_only",
            "reporting_scope": "fictional_solo_direct_residential_building",
            "year_end": "2025-12-31",
            "contract_population": "at_least_one_year_contracts_at_year_end_not_buildings",
            "premium_population": "annual_direct_gross_written_eur_cents_not_tariff",
            "geography_status": "hypothetical_not_insurer_observed",
            "take_up_status": "hypothetical_market_reference_not_carrier_observed",
            "synthetic_total_year_end_contracts": str(count),
            "synthetic_total_written_gwp_eur_cents": str(cents),
            "regions": cases[case],
        }
        result[case] = allocate_synthetic_regional_book(scenario)
    a = {x["region_code"]: x for x in result["A"]["regions"]}
    b = {x["region_code"]: x for x in result["B"]["regions"]}
    moved = sum(abs(a[k]["synthetic_contracts_at_year_end"] -
                    b[k]["synthetic_contracts_at_year_end"]) for k in a) // 2
    # Half-L1 is integer for two conserved integer vectors.
    if sum(abs(a[k]["synthetic_contracts_at_year_end"] -
               b[k]["synthetic_contracts_at_year_end"]) for k in a) != 2 * moved:
        raise SyntheticBookError("invalid regional contraction conservation")
    payload_digest = hashlib.sha256(json.dumps(
        raw,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")).hexdigest()
    return {
        "schema_version": "0.1.0",
        "study_kind": "two_independent_fully_synthetic_regional_priors",
        "input_sha256": payload_digest,
        "district_count": len(support),
        "synthetic_national_contract_count": count,
        "synthetic_national_direct_written_gwp_eur_cents": cents,
        "hypothetical_contracts_shifted_between_priors": moved,
        "total_variation_geographic_share": _six(Decimal(moved)/Decimal(count)),
        "cases": result,
        "zensus_2022_original_data_consumed": False,
        "gdv_2025_original_data_consumed": False,
        "original_insurer_records_consumed": False,
        "different_vintages_reconciled_by_observation": False,
        "building_to_contract_mapping_is_observed": False,
        "regional_insurer_allocation_is_observed": False,
        "cat_losses_observed": False,
        "model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario",type=Path)
    args=parser.parse_args()
    try:
        if args.scenario.stat().st_size > 2_000_000:
            raise SyntheticBookError("input exceeds 2 MB")
        raw=json.loads(args.scenario.read_text(encoding="utf-8"))
        out=compare_fictional_district_priors(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, SyntheticBookError) as exc:
        parser.exit(status=2,message=f"BLOCKED: {exc}\n")
    print(json.dumps(out,ensure_ascii=True,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
