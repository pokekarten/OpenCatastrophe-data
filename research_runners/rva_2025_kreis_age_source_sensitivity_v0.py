# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact 2022 public Kreis building age opportunities -> fictional 2025 R+V shares.

The observed data are physical building counts by construction-era cohort and
solo national insurance totals; company affinity by Kreis and Baujahr is not
observable. Three hypothetical conversion priors challenge identifiability.
No roof age, physical vulnerability, insurer location, TIV, CAT or RI model.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import tomllib

from synthetic_regional_property_book_v0 import (
    SyntheticBookError, allocate_synthetic_regional_book,
)
from rva_2025_kreis_zensus_real_prior_fictional_book_v0 import validate_kreis_original
from zensus_kreis_original_age_cohorts_v0 import CODES, BANDS, ORIGINAL_SHA256

ROOT=Path(__file__).resolve().parents[1]
BUILDINGS=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
AGE=ROOT/"research/observations/zensus2022_400_kreis_original_building_age_cohorts_v0.toml"
HGB=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
AGE_ROW_SHA="2cb3d015c9a55ac90c3e738f4f8feac0adb095ad661a76b2231e56a7867fffc3"
CASES={
    "PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY": (),
    "HISTORIC_PRE1950_AFFINITY_1_5X": (0,1),
    "MODERN_POST2000_AFFINITY_1_5X": (7,8,9),
}

def reject(message: str):
    raise SyntheticBookError(message)


def validate_original_building_age(buildings: dict, age: dict) -> tuple[dict,dict]:
    record=validate_kreis_original(buildings)
    if (age.get("schema_version")!="ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGE_COHORTS_V0"
            or age.get("original_workbook_full_sha256")!=ORIGINAL_SHA256
            or age.get("original_age_rows_canonical_sha256")!=AGE_ROW_SHA
            or age.get("source_original_url")!="https://www.destatis.de/static/DE/zensus/gitterdaten/Regionaltabelle_Gebaeude_Wohnungen.xlsx"
            or age.get("source_categories_url")!="https://ergebnisse.zensus2022.de/datenbank/online/statistic/3000G/table/3000G-1002"
            or age.get("source_workflow_url")!="https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41921131011"
            or age.get("source_sheet")!="CSV-Gebäude"
            or age.get("source_date")!="2022-05-15"
            or age.get("source_region_level")!="Stadtkreis/kreisfreie Stadt/Landkreis"
            or age.get("classification_population")!="Gebaeude_mit_Wohnraum_including_mixed_use"
            or age.get("license")!="Datenlizenz Deutschland – Namensnennung – Version 2.0"):
        reject("publisher original age source identity or rights changed")
    for k in ("actual_rva_contracts_by_building_year_observed",
              "actual_rva_kreis_site_addresses_observed","roof_vulnerability_or_wind_loss_observed",
              "insurer_model_input_admitted"):
        if age.get(k) is not False:
            reject("physical building age cannot claim actual insurer exposures/losses")
    if (age.get("age_labels_official_order")!=list(BANDS)
            or age.get("source_age_bands_original_column_order")!=list(CODES)
            or age.get("original_source_county_count")!=400
            or age.get("source_county_buildings_with_residential_use_2022")!=19957288
            or age.get("all_counties_have_numeric_ten_age_classes") is not True
            or age.get("source_age_band_sums_nonadditive_cell_key_method") is not True):
        reject("age 2022 population, classification, source completeness or CKM status changed")
    old={r["ags"]:r["geb_mit_wohnraum"] for r in buildings["kreise"]}
    rows=age.get("kreise",[])
    if len(rows)!=400 or len({r.get("ags") for r in rows})!=400:
        reject("age source must have exactly 400 unique Kreis")
    if set(old)!={r["ags"] for r in rows}:
        reject("age source county keys differ from original building distribution")
    expected=[]
    sums=[0]*10
    delta_total=0
    max_abs=0
    for r in rows:
        ags=r["ags"]
        n=r.get("buildings_mit_wohnraum_2022")
        ten=r.get("age_bands_source_order")
        if (type(n) is not int or n!=old[ags]
                or not isinstance(ten,list) or len(ten)!=10
                or any(type(x) is not int or x<0 or x>n+10 for x in ten)):
            reject("age band county physical source values not original numeric 2022 stock")
        for i,v in enumerate(ten): sums[i]+=v
        delta=sum(ten)-n
        max_abs=max(max_abs,abs(delta))
        delta_total+=delta
        expected.append({"ags":ags,"buildings_2022":n,"age_bands_2022":ten,
                         "all_age_bands_numeric":True,"complete_age_band_sum_minus_buildings":delta})
    canonical=json.dumps(sorted(expected,key=lambda x:x["ags"]),sort_keys=True,
                         ensure_ascii=False,separators=(",",":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest()!=AGE_ROW_SHA:
        reject("age source values changed from original SHA-256 canonical rows")
    if (age.get("source_national_age_band_available_numeric_sums")!=sums
        or sum(sums)!=19957171
        or age.get("source_age_band_county_sum_minus_building_count")!=delta_total
        or delta_total!=-117
        or age.get("source_max_absolute_county_delta")!=max_abs
        or max_abs!=20):
        reject("original age aggregate or Cell-Key non-additivity not reconciled")
    return record,{k:v for k,v in sorted(((r["ags"],r) for r in rows))}


def _hamilton(n: int, weights: list[int]) -> list[int]:
    if n<0 or len(weights)!=10 or any(type(x) is not int or x<0 for x in weights) or sum(weights)<=0:
        reject("invalid hypothetical cohort weights")
    denom=sum(weights)
    floors=[n*x//denom for x in weights]
    rem=n-sum(floors)
    # Sort by exact numerator remainder and source age cohort order.
    order=sorted(range(10),key=lambda i:(-(n*weights[i])%denom,i))
    # Explicitly sort by negative *remainder*, not modular negative.
    order=sorted(range(10),key=lambda i:(-((n*weights[i])%denom),i))
    for i in order[:rem]:
        floors[i]+=1
    if sum(floors)!=n:
        reject("cohort contract conservation failed")
    return floors


def simulate_age_prior(book: dict, age: dict, hgb: dict) -> dict:
    audit,by_ags=validate_original_building_age(book,age)
    if (hgb.get("entity")!="R+V Allgemeine Versicherung AG"
        or hgb.get("entity_kind")!="solo_direct_insurer"
        or hgb.get("accounting_basis")!="HGB_Gebuchte_Bruttobeitraege"
        or hgb.get("premium_unit")!="thousand_eur"
        or hgb.get("company_geo_exposure_observed") is not False):
        reject("unverified insurer legal entity or accounting basis")
    hgb_y=[x for x in hgb.get("years",[]) if x.get("year")==2025]
    contracts_y=[x for x in hgb.get("building_contract_observations",{}).get("years",[]) if x.get("year")==2025]
    if (len(hgb_y)!=1 or len(contracts_y)!=1
        or hgb_y[0].get("connected_buildings_self_written")!=997710
        or contracts_y[0].get("contracts")!=1060546):
        reject("original insurer national 2025 count and annual GWP not matched")
    count=1060546
    cents=997710*100000
    cases={}
    for label,boost in CASES.items():
        factors=[]
        for ags,r in sorted(by_ags.items()):
            ten=r["age_bands_source_order"]
            total=r["buildings_mit_wohnraum_2022"]
            # 2x base plus extra 1x of chosen 2022 cohort: e.g. 3/2=1.5.
            weight=2*total+sum(ten[i] for i in boost)
            factors.append({
                "region_code":"KREIS_"+ags,
                "hypothetical_contract_capacity":str(total*2),
                "contract_prior_weight":str(weight),
                "premium_relativity":"1",
                "hypothetical_market_elemental_share":"0",
                "assumed_carrier_uptake_multiplier":"0",
            })
        inp={
            "schema_version":"0.1.0",
            "scenario_kind":"fully_synthetic_test_only",
            "reporting_scope":"fictional_solo_direct_residential_building",
            "year_end":"2025-12-31",
            "contract_population":"at_least_one_year_contracts_at_year_end_not_buildings",
            "premium_population":"annual_direct_gross_written_eur_cents_not_tariff",
            "geography_status":"hypothetical_not_insurer_observed",
            "take_up_status":"hypothetical_market_reference_not_carrier_observed",
            "synthetic_total_year_end_contracts":str(count),
            "synthetic_total_written_gwp_eur_cents":str(cents),
            "regions":factors,
        }
        allocated=allocate_synthetic_regional_book(inp)
        if (allocated["synthetic_total_contracts_conserved"] is not True
            or allocated["synthetic_total_annual_written_gwp_cents_conserved"] is not True
            or any(allocated.get(k) is not False for k in (
                "regional_contract_counts_are_observed", "model_input_approved",
                "has_true_risk_site_coordinates", "has_insured_tiv", "has_event_or_cat_losses"))):
            reject("hypothetical 2025 insurer source admission/conservation failed")
        national=[0]*10
        state={}
        counties=[]
        for x in allocated["regions"]:
            ags=x["region_code"][6:]
            n=x["synthetic_contracts_at_year_end"]
            original=by_ags[ags]["age_bands_source_order"]
            weights=[v*(3 if i in boost else 2) for i,v in enumerate(original)]
            cohort=_hamilton(n,weights)
            if sum(cohort)!=n:
                reject("regional cohort split violates synthetic insurer national contract count")
            for i,z in enumerate(cohort):national[i]+=z
            st=state.setdefault(ags[:2],{"contract_count":0,"gwp_eur_cents":0,
                                          "age_classes_hypothetical_contracts":[0]*10})
            st["contract_count"]+=n
            st["gwp_eur_cents"]+=x["hypothetical_regional_annual_gwp_eur_cents"]
            for i,z in enumerate(cohort):st["age_classes_hypothetical_contracts"][i]+=z
            counties.append({"kreis_ags_2022":ags,"hypothetical_contracts_2025":n,
                             "hypothetical_age_contracts_2025":cohort,
                             "hypothetical_written_gwp_eur_cents":x["hypothetical_regional_annual_gwp_eur_cents"],
                             "company_county_exposure_observed":False})
        if sum(national)!=count or sum(x["contract_count"] for x in state.values())!=count or sum(x["gwp_eur_cents"] for x in state.values())!=cents:
            reject("national HGB population not conserved")
        cases[label]={
            "fictional_cohort_affinity_1_5x":list(boost),
            "national_hypothetical_insurer_contracts_by_source_age_cohort":national,
            "national_hypothetical_pre1950_contracts":national[0]+national[1],
            "national_hypothetical_post2000_contracts":sum(national[7:]),
            "nationwide_hypothetical_company_contracts":count,
            "nationwide_hypothetical_company_written_gwp_eur_cents":cents,
            "company_2025_kreis_age_distribution_observed":False,
            "2022_2025_population_equivalence_verified":False,
            "hypothetical_state_rollup":dict(sorted(state.items())),
            "hypothetical_county_rows":counties,
        }
    reference={r["kreis_ags_2022"]:r["hypothetical_contracts_2025"]
               for r in cases["PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY"]["hypothetical_county_rows"]}
    for label,data in cases.items():
        tv=sum(abs(x["hypothetical_contracts_2025"]-reference[x["kreis_ags_2022"]])
               for x in data["hypothetical_county_rows"])
        if tv%2: reject("nonconserving county comparison")
        data["hypothetical_policies_relocated_vs_baseline"]=tv//2
        data["hypothetical_county_total_variation_fraction"]=format(
            (Decimal(tv//2)/Decimal(count)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP),"f")
    return {
        "schema_version":"RVA_SOLO_2025_COUNTY_AGE_SOURCE_SENSITIVITY_V0",
        "issuer":"R+V Allgemeine Versicherung AG",
        "original_2022_county_building_audit":audit,
        "actual_2022_age_band_source_sha256":AGE_ROW_SHA,
        "official_age_labels":list(BANDS),
        "observed_national_2025_contracts":count,
        "observed_national_2025_annual_gwp_eur_cents":cents,
        "cases":cases,
        "admission":{
            "true_2025_rva_county_contract_share":False,
            "true_2025_insurer_building_age_mix":False,
            "actual_insurer_policy_age_or_renewal":False,
            "insurer_property_coordinates_or_tiv":False,
            "company_flood_cover_or_treaty_terms":False,
            "roof_or_peril_vulnerability_calibrated":False,
            "german_oasis_gross_net_oep_aep_run":False,
            "model_input_approved":False,
        }
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--building-source",type=Path,default=BUILDINGS)
    p.add_argument("--age-source",type=Path,default=AGE)
    p.add_argument("--issuer-source",type=Path,default=HGB)
    p.add_argument("--full-county",action="store_true")
    a=p.parse_args()
    try:
        blobs=[x.read_bytes() for x in (a.building_source,a.age_source,a.issuer_source)]
        if any(len(b)>1000000 for b in blobs):reject("source outside bound")
        inputs=[tomllib.loads(b.decode("utf-8")) for b in blobs]
        r=simulate_age_prior(*inputs)
        if not a.full_county:
            for case in r["cases"].values():
                case.pop("hypothetical_county_rows")
        r["input_sha256"]={k:hashlib.sha256(v).hexdigest() for k,v in zip(
            ("census_original_buildings","census_original_ages","solo_company_HGB"),blobs)}
        print(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2))
    except (ValueError,OSError,UnicodeError) as exc:
        p.exit(2,"BLOCKED: "+str(exc)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
