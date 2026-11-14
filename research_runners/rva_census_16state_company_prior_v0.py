# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""16-Land Zensus 2022 *physical opportunity* -> R+V 2025 synthetic HGB mass.

The 2022 census building/ownership counts are real published state aggregates.
The 2025 insurer contracts and booked premium are real published SOLO national
controls. Their relationship and EVERY regional insurer contract is unobserved
and wholly hypothetical, as are policy-to-building links and sum insured.
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
ISSUER = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
CENSUS = ROOT / "research/observations/zensus2022_16_state_residential_use_buildings_v0.toml"
ORIGINAL = "https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/THMonografie_derivate_00000684/Aufsatz-05a-2025.pdf"
STATES = {f"{n:02}" for n in range(1, 17)}
OWNERSHIP = ("owned_by_private_persons", "owned_by_apartment_owner_associations",
             "owned_by_housing_companies", "owned_by_other")
MODELS = {
    "PHYSICAL_BUILDING_OPPORTUNITY": ("buildings_with_residential_use_2022",),
    "PRIVATE_OWNER_OPPORTUNITY": ("owned_by_private_persons",),
    "CO_OWNED_AND_HOUSING_COMPANY_OPPORTUNITY": (
        "owned_by_apartment_owner_associations", "owned_by_housing_companies"),
}


def blocked(s: str):
    raise SyntheticBookError(s)


def validate_state_census(c: dict) -> dict:
    if (c.get("schema_version") != "ZENSUS2022_GERMANY_16_LAENDER_BUILDINGS_WITH_RESIDENTIAL_USE_V0"
            or c.get("publisher") != "Thueringer Landesamt fuer Statistik"
            or c.get("source_url") != ORIGINAL
            or c.get("printed_document_page") != 29
            or c.get("published_year") != 2025 or c.get("census_date") != "2022-05-15"
            or c.get("statistical_universe") != "Gebaeude_mit_Wohnraum_including_other_buildings_with_dwellings_NOT_only_residential_buildings"
            or c.get("geographical_grain") != "16_laender_AGS_2digit_as_of_2022"
            or c.get("numbers_are_original_public_statistical_office_aggregates") is not True):
        blocked("unexpected official 2022 Census origin or building universe")
    for k in ("original_pdf_byte_sha256_verified_in_this_research",
              "source_district_level_data_extracted","company_insured_buildings_observed",
              "company_policyholder_by_ownership_observed","company_state_market_shares_observed",
              "geocoded_risk_sites_observed","year_2025_building_stock_observed",
              "insurer_tiv_or_natural_perils_coverage_observed"):
        if c.get(k) is not False:
            blocked("Zensus aggregate falsely promoted to insured company risk exposure")
    rows = c.get("states", [])
    if len(rows) != 16 or {x.get("state_ags") for x in rows} != STATES:
        blocked("need exactly 16 disjoint 2022 Bundesland AGS observations")
    if len({x.get("state_label") for x in rows}) != 16:
        blocked("missing or duplicated German state identity")
    for row in rows:
        if row.get("insurance_company_observed_in_this_row") is not False:
            blocked("Census state cannot reveal actual R+V policy counts")
        for k in ("buildings_with_residential_use_2022", *OWNERSHIP):
            if type(row.get(k)) is not int or row[k] < 0:
                blocked("Census building/ownership count must be original nonnegative integer")
        building = row["buildings_with_residential_use_2022"]
        if not 0 < building <= 10_000_000:
            blocked("invalid Bundesland building population")
        if abs(building-sum(row[x] for x in OWNERSHIP)) > 6:
            blocked("state ownership attribution exceeds published display non-additivity")
    printed = c["national_publisher_printed"]
    state_sum = sum(r["buildings_with_residential_use_2022"] for r in rows)
    if printed.get("buildings_with_residential_use_2022") != 19957268 or state_sum != 19957266:
        blocked("official source's 2-building reported summation discrepancy changed")
    ownership_delta = {}
    for k in OWNERSHIP:
        national = printed.get(k)
        if type(national) is not int or national <= 0:
            blocked("missing official national ownership category")
        s=sum(row[k] for row in rows)
        delta=s-national
        if abs(delta)>10:
            blocked("published ownership sum mismatch exceeds stated source precision")
        ownership_delta[k]=delta
    return {
        "observed_publisher_national_2022_buildings_with_residential_use": printed["buildings_with_residential_use_2022"],
        "summed_16_state_2022_buildings_with_residential_use": state_sum,
        "printed_state_sum_minus_publisher_national": state_sum-printed["buildings_with_residential_use_2022"],
        "ownership_state_sum_minus_publisher_national": ownership_delta,
        "source_national_vs_state_additivity_exact": False,
        "original_2022_census_buildings_derived_from_insurer": False,
    }


def compare_state_priors(h: dict, c: dict) -> dict:
    census_audit = validate_state_census(c)
    if (h.get("entity") != "R+V Allgemeine Versicherung AG"
            or h.get("entity_kind") != "solo_direct_insurer"
            or h.get("accounting_basis") != "HGB_Gebuchte_Bruttobeitraege"
            or h.get("premium_unit") != "thousand_eur"
            or any(h.get(k) is not False for k in
                   ("company_geo_exposure_observed","company_insured_tiv_observed"))):
        blocked("insurer original source not approved solo HGB national contract control")
    policies = h.get("building_contract_observations", {}).get("years", [])
    py = [r for r in policies if r.get("year")==2025]
    fy = [r for r in h.get("years",[]) if r.get("year")==2025]
    if (len(py)!=1 or len(fy)!=1 or py[0].get("contracts") != 1060546
            or fy[0].get("connected_buildings_self_written") != 997710
            or py[0].get("source_report_year") != 2025):
        blocked("wrong original 2025 R+V SOLO report count/premium")
    total=py[0]["contracts"]
    cents=fy[0]["connected_buildings_self_written"]*100000
    states=sorted(c["states"],key=lambda x:x["state_ags"])
    cases={}
    for label,keys in sorted(MODELS.items()):
        scenario={
            "schema_version":"0.1.0",
            "scenario_kind":"fully_synthetic_test_only",
            "reporting_scope":"fictional_solo_direct_residential_building",
            "year_end":"2025-12-31",
            "contract_population":"at_least_one_year_contracts_at_year_end_not_buildings",
            "premium_population":"annual_direct_gross_written_eur_cents_not_tariff",
            "geography_status":"hypothetical_not_insurer_observed",
            "take_up_status":"hypothetical_market_reference_not_carrier_observed",
            "synthetic_total_year_end_contracts":str(total),
            "synthetic_total_written_gwp_eur_cents":str(cents),
            "regions":[{
                "region_code":"DE"+row["state_ags"],
                # Fictional opportunity cap: one building can carry many / few policies.
                "hypothetical_contract_capacity":str(row["buildings_with_residential_use_2022"]*2),
                "contract_prior_weight":str(sum(row[k] for k in keys)),
                "premium_relativity":"1",
                "hypothetical_market_elemental_share":"0",
                "assumed_carrier_uptake_multiplier":"0",
            } for row in states],
        }
        allocation=allocate_synthetic_regional_book(scenario)
        if (allocation["synthetic_total_contracts_conserved"] is not True
                or allocation["synthetic_total_annual_written_gwp_cents_conserved"] is not True
                or allocation["has_true_risk_site_coordinates"] is not False
                or allocation["model_input_approved"] is not False):
            blocked("fictional scenario inadvertently admitted or lost national mass")
        regional={x["region_code"]:x for x in allocation["regions"]}
        cases[label]={
            "prior_basis_2022": "+".join(keys),
            "simulated_rva_2025_contracts_are_observed":False,
            "census_source_vintage": "2022-05-15",
            "company_source_vintage":"2025-12-31",
            "source_vintage_alignment_achieved":False,
            "regional_2025_book":[
                {
                    "state_ags":row["state_ags"],
                    "state_label":row["state_label"],
                    "observed_2022_residential_use_building_opportunities":row["buildings_with_residential_use_2022"],
                    "hypothetical_2025_rva_policy_contracts":regional["DE"+row["state_ags"]]["synthetic_contracts_at_year_end"],
                    "hypothetical_2025_direct_written_gwp_eur_cents":regional["DE"+row["state_ags"]]["hypothetical_regional_annual_gwp_eur_cents"],
                    "not_company_observed_risk_locations":True,
                } for row in states
            ],
        }
    ref={x["state_ags"]:x["hypothetical_2025_rva_policy_contracts"]
         for x in cases["PHYSICAL_BUILDING_OPPORTUNITY"]["regional_2025_book"]}
    for label,case in cases.items():
        current={x["state_ags"]:x["hypothetical_2025_rva_policy_contracts"] for x in case["regional_2025_book"]}
        l1=sum(abs(current[k]-ref[k]) for k in STATES)
        if l1%2: blocked("alternative book violates exact contract count")
        case["shifted_hypothetical_contracts_vs_building_opportunity"]=l1//2
        case["total_variation_vs_building_opportunity"]=format(
            (Decimal(l1//2)/Decimal(total)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP),"f")
    return {
        "schema_version":"RVA_2025_SOLO_16_STATE_CENSUS_2022_OPPORTUNITY_NONIDENTIFICATION_V0",
        "target_issuer":h["entity"],
        "observed_national_2025_connected_building_contracts":total,
        "observed_national_2025_direct_booked_gwp_teuro":fy[0]["connected_buildings_self_written"],
        "census_2022_source_audit":census_audit,
        "three_source_based_opportunity_alternatives":cases,
        "limitations":{
            "regional_insurer_contracts_observed":False,
            "year_2025_physical_building_stock_observed":False,
            "insurer_site_geocodes_observed":False,
            "insurer_tiv_observed":False,
            "actual_insurer_flood_take_up_observed":False,
            "hazard_and_vulnerability_calibrated":False,
            "real_reinsurance_terms_or_oep_aep_observed":False,
            "native_oasis_output_produced":False,
            "model_input_approved":False,
        },
        "scientific_interpretation":"Actual 2022 Census state buildings/ownership + actual 2025 solo company national contracts/GWP, with entirely hypothetical 2025 insurer state policy distribution. No R+V observed state contracts or location/TIV."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hgb",type=Path,default=ISSUER)
    p.add_argument("--census",type=Path,default=CENSUS)
    args=p.parse_args()
    try:
        blobs=[args.hgb.read_bytes(),args.census.read_bytes()]
        if any(len(x)>1000000 for x in blobs):
            blocked("input larger than 1MB")
        h,c=[tomllib.loads(x.decode("utf-8")) for x in blobs]
        out=compare_state_priors(h,c)
        out["input_sha256"]={k:hashlib.sha256(x).hexdigest()
                              for k,x in zip(("issuer_HGB_TOML","official_Census_state_aggregate_TOML"),blobs)}
    except (OSError,UnicodeError,ValueError) as e:
        p.exit(status=2,message=f"BLOCKED: {e}\n")
    print(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
