# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""R+V 2025 observed SOLO national policy/premium constraints, fictional geography.

BVR source totals are checked only as an independent sales-channel observation.
BVR association categories are NOT mapped to Bundeslaender or insurer regions.
No observed insurer sites, flood cover, TIV, loss, Oasis execution or calibration.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import tomllib

from synthetic_regional_property_book_v0 import SyntheticBookError, allocate_synthetic_regional_book

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
BVR = ROOT / "research/observations/bvr_regional_association_counts_2024_2025_v0.toml"
SCENARIOS = ROOT / "research/scenarios/rva_solo_2025_company_anchored_macro_sensitivity_v0.toml"
REGIONS = {"DE_NORTH", "DE_EAST", "DE_SOUTH", "DE_WEST"}
HYPOTHESES = {"UNIFORM_HYPOTHESIS", "SOUTH_WEST_HYPOTHESIS", "NORTH_EAST_HYPOTHESIS"}
BVR_REGIONAL = {"Baden-Wuerttemberg", "Bayern", "Genoverband", "Weser-Ems"}


def reject(message: str):
    raise SyntheticBookError(message)


def verify_bvr(d: dict) -> dict:
    if (d.get("schema_version") != "BVR_2024_2025_REGIONAL_ASSOCIATION_COUNTS_V0"
            or d.get("publisher") != "Bundesverband der Deutschen Volksbanken und Raiffeisenbanken (BVR)"
            or d.get("source_url") != "https://berichte.bvr.de/jahresbericht-2025/ergebnisse/regionale-statistik/"
            or d.get("year_2025") != 2025 or d.get("year_2024") != 2024
            or d.get("observation_type") != "BVR_reporting_panel_region_association_and_institution_category"):
        reject("BVR issuer/vintage/association receipt mismatch")
    for key in ("associations_are_german_states", "all_cooperative_banks_are_ruv_partners",
                "membership_is_homeowner_population", "banks_are_ruv_insured_property_locations",
                "branch_counts_are_insured_locations", "derived_carrier_state_weights_admitted",
                "original_source_html_bytes_sha256_recorded"):
        if d.get(key) is not False:
            reject("BVR observation incorrectly promoted to insurer risk geography")
    cats = d.get("categories", [])
    if len(cats) != 7 or len({c.get("category_id") for c in cats}) != len(cats):
        reject("BVR association panels must contain distinct seven reported categories")
    if {c["category_id"] for c in cats if c.get("category_type") == "regional_audit_association"} != BVR_REGIONAL:
        reject("BVR regional association reporting scope changed")
    for c in cats:
        if c.get("category_type") not in {"regional_audit_association", "national_institution_category"}:
            reject("BVR category type unknown")
        if c.get("legal_state_count_or_nuts3_population_observed") is not False or any(
            c.get(k) is not False for k in (
                "ruv_insurance_contracts_in_category_observed",
                "ruv_residential_policies_in_category_observed")
        ):
            reject("BVR category cannot reveal real insurer positions")
    for year in (2024, 2025):
        targets = d.get(f"official_total_{year}", {})
        regional_targets = d.get(f"regional_subtotal_{year}", {})
        for source_key, cat_key in (
            ("banks", f"cooperative_banks_{year}"),
            ("branch_offices", f"bank_offices_{year}"),
            ("members", f"members_{year}"),
        ):
            values = [c.get(cat_key) for c in cats]
            if not all(type(v) is int and v >= 0 for v in values):
                reject("BVR regional measures must be original nonnegative integers")
            if sum(values) != targets.get(source_key):
                reject("BVR full reported subtotal does not reconcile")
            if sum(c[cat_key] for c in cats if c["category_id"] in BVR_REGIONAL) != regional_targets.get(source_key):
                reject("BVR regional subtotal does not reconcile")
    return {
        "banks_2025": d["official_total_2025"]["banks"],
        "branch_offices_2025": d["official_total_2025"]["branch_offices"],
        "members_2025": d["official_total_2025"]["members"],
        "branch_offices_2024": d["official_total_2024"]["branch_offices"],
        "branch_office_change_2025_minus_2024": (d["official_total_2025"]["branch_offices"]
                                                    - d["official_total_2024"]["branch_offices"]),
        "bvr_association_to_state_weights_available": False,
        "bvr_institution_is_carrier_partner_verified": False,
        "branch_offices_equal_to_all_bank_sites": False,
    }


def compare_company_anchored_macro(h: dict, bvr: dict, hypotheses: dict) -> dict:
    bank = verify_bvr(bvr)
    if h.get("entity") != "R+V Allgemeine Versicherung AG" or h.get("entity_kind") != "solo_direct_insurer":
        reject("wrong observed insurer legal entity")
    if h.get("accounting_basis") != "HGB_Gebuchte_Bruttobeitraege" or h.get("premium_unit") != "thousand_eur":
        reject("issuer accounting population/unit changed")
    observed = [r for r in h.get("building_contract_observations", {}).get("years", [])
                if r.get("year") == 2025]
    hgb = [r for r in h.get("years", []) if r.get("year") == 2025]
    if len(observed) != 1 or len(hgb) != 1:
        reject("missing 2025 national observed controls")
    count = observed[0].get("contracts")
    premium_teuro = hgb[0].get("connected_buildings_self_written")
    # Pin to issuer original public numbers to avoid silent source drift.
    if (type(count) is not int or count != 1060546
            or type(premium_teuro) is not int or premium_teuro != 997710
            or observed[0].get("source_report_year") != 2025
            or not observed[0].get("perimeter_break")):
        reject("exact issuer 2025 solo HGB residential count/premium controls altered")
    if h.get("company_geo_exposure_observed") is not False:
        reject("unobserved insurer geography falsely claimed")
    if (hypotheses.get("schema_version") != "RVA_SOLO_2025_MACRO_PRIOR_STRESS_V0"
            or hypotheses.get("target_legal_entity") != h["entity"]
            or hypotheses.get("issuer_year") != 2025
            or hypotheses.get("scenario_kind") != "national_observed_controls_entirely_fictional_geography"
            or hypotheses.get("issuer_contract_measure") != "connected_building_year_end_policies_not_buildings"
            or hypotheses.get("issuer_premium_measure") != "annual_HGB_direct_booked_connected_buildings_TEUR_not_insured_TIV"
            or hypotheses.get("geographical_region_definition") != "fictional_macro_bucket_not_verified_census_region"):
        reject("scenario pretends false geographic or accounting authority")
    for key in (
        "real_company_region_shares_observed",
        "original_zensus_regional_building_counts_admitted",
        "bvr_association_to_state_geography_verified",
        "bvr_indicators_used_as_company_weights", "issuer_peril_take_up_observed",
        "insurer_sites_and_tiv_observed", "model_input_approved",
    ):
        if hypotheses.get(key) is not False:
            reject("fictional geography/financial model falsely admitted")
    all_cases = hypotheses.get("hypotheses", [])
    if len(all_cases) != 3 or {x.get("name") for x in all_cases} != HYPOTHESES:
        reject("three explicit nonidentified alternative priors required")
    amount_cents = premium_teuro * 100000  # 1 thousand EUR = 100,000 EUR cents
    cases = {}
    for case in sorted(all_cases, key=lambda x: x["name"]):
        if case.get("status") != "invented_research_sensitivity" or len(case.get("regions", [])) != 4:
            reject("macro case does not explicitly acknowledge invented inputs")
        regions = case["regions"]
        if {x.get("region_code") for x in regions} != REGIONS:
            reject("four abstract macro regions must be unique and complete")
        if any(x.get("hypothetical_market_elemental_share") != "0"
               or x.get("assumed_carrier_uptake_multiplier") != "0" for x in regions):
            reject("no invented flood uptake presented as insurer premium calibration")
        scenario = {
            "schema_version": "0.1.0",
            "scenario_kind": "fully_synthetic_test_only",
            "reporting_scope": "fictional_solo_direct_residential_building",
            "year_end": "2025-12-31",
            "contract_population": "at_least_one_year_contracts_at_year_end_not_buildings",
            "premium_population": "annual_direct_gross_written_eur_cents_not_tariff",
            "geography_status": "hypothetical_not_insurer_observed",
            "take_up_status": "hypothetical_market_reference_not_carrier_observed",
            "synthetic_total_year_end_contracts": str(count),
            "synthetic_total_written_gwp_eur_cents": str(amount_cents),
            "regions": regions,
        }
        out = allocate_synthetic_regional_book(scenario)
        if out["synthetic_total_contracts_conserved"] is not True or out["synthetic_total_annual_written_gwp_cents_conserved"] is not True:
            reject("national observations not conserved")
        if any(x["hypothetical_elemental_cover_contract_equivalents"] != 0 for x in out["regions"]):
            reject("unsupported hypothetical flood coverage")
        cases[case["name"]] = out
    reference = {x["region_code"]:x["synthetic_contracts_at_year_end"]
                 for x in cases["UNIFORM_HYPOTHESIS"]["regions"]}
    shifted = {}
    for name, case in cases.items():
        region = {x["region_code"]:x["synthetic_contracts_at_year_end"] for x in case["regions"]}
        l1 = sum(abs(reference[k] - region[k]) for k in REGIONS)
        if l1 % 2: reject("regional conservation distance must be even")
        shifted[name] = {
            "hypothetical_contracts_shifted_from_uniform": l1//2,
            "total_variation_fraction": format((Decimal(l1//2)/Decimal(count)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP),"f")
        }
    return {
        "schema_version": "RVA_SOLO_PUBLIC_CONTROL_MACRO_HYPOTHESIS_RECEIPT_V0",
        "target_legal_entity": h["entity"],
        "observed_2025_national_connected_building_contract_count": count,
        "observed_2025_national_direct_booked_gwp_teuro": premium_teuro,
        "observed_2025_national_direct_booked_gwp_eur_cents": amount_cents,
        "bvr_observed_sales_channel_association_totals": bank,
        "regional_sensitivity_cases": cases,
        "difference_from_uniform": shifted,
        "limitations": {
            "insurer_company_geography_observed": False,
            "insurer_building_count_and_tiv_observed": False,
            "original_zensus_2022_building_count_used": False,
            "bvr_association_to_kreis_or_land_crosswalk": False,
            "bvr_weights_used_to_allocate_company_policies": False,
            "insurer_flood_cover_count_estimated": False,
            "real_peril_claims_or_reinsurance_calibrated": False,
            "native_oasis_oep_aep_produced": False,
            "model_input_approved": False
        },
        "interpretation": "Exact public national HGB company count and premium ONLY; every geography/coverage/value field is an invented sensitivity, not a statistical estimate of R+V site addresses."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history", type=Path, default=HISTORY)
    p.add_argument("--bvr", type=Path, default=BVR)
    p.add_argument("--hypotheses", type=Path, default=SCENARIOS)
    args=p.parse_args()
    raw=[x.read_bytes() for x in (args.history,args.bvr,args.hypotheses)]
    if any(len(x)>1000000 for x in raw):
        p.exit(status=2,message="BLOCKED: source larger than bound\n")
    try:
        h,b,s=[tomllib.loads(x.decode("utf-8")) for x in raw]
        out=compare_company_anchored_macro(h,b,s)
    except (OSError,ValueError,UnicodeError) as exc:
        p.exit(status=2,message=f"BLOCKED: {exc}\n")
    out["input_sha256"]={k:hashlib.sha256(v).hexdigest() for k,v in zip(("solo_hgb","bvr","fictional_priors"),raw)}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
