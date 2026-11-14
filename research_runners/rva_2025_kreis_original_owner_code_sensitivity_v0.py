# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""400 published 2022 Kreis owner source columns → 2025 fictional RVA sensitivity.

Ownership codes are UNLABELLED until independently crosswalked. Never claim
that building-owner classes identify actual R+V owners, policyholders, assets,
reinsurance, insured TIV, or loss model parameters.
"""
from __future__ import annotations
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
import argparse,hashlib,json,tomllib

from synthetic_regional_property_book_v0 import SyntheticBookError,allocate_synthetic_regional_book
from rva_2025_kreis_zensus_real_prior_fictional_book_v0 import validate_kreis_original

ROOT=Path(__file__).resolve().parents[1]
OWNER=ROOT/"research/observations/zensus2022_400_kreis_original_owner_code_aggregates_v0.toml"
BUILDINGS=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
ISSUER=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
CODES=[f"EIGENTUM__{i}" for i in range(1,9)]
HASH="47d572d216e603bc5643997f7d1ed7f593c50ec88b6a63d82730a3be3f4c380a"
COUNTS=[1771256,16944010,295192,353229,359057,140065,25345,68980]
COVERAGE=[400,400,390,400,400,400,394,400]
CASES={"ALL_PUBLISHED_BUILDINGS":None,"SOURCE_CODE1_EXTRA_50PCT":0,
       "SOURCE_CODE2_EXTRA_50PCT":1}


def fail(message):
    raise SyntheticBookError(message)


def validate_owner_source(o,b):
    bmeta=validate_kreis_original(b)
    if (o.get("schema_version")!="ZENSUS2022_400_KREIS_ORIGINAL_OWNER_CODE_AGGREGATES_V0"
        or o.get("source_original_sha256")!="82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551"
        or o.get("canonical_owner_records_sha256")!=HASH
        or o.get("original_audit_workflow")!="https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41929664598"
        or o.get("source_sheet")!="CSV-Gebäude"
        or o.get("source_date")!="2022-05-15"
        or o.get("source_ags_level")!="Stadtkreis/kreisfreie Stadt/Landkreis"
        or o.get("source_columns_original_order")!=CODES
        or o.get("individual_owner_code_name_mapping_confirmed") is not False
        or o.get("observed_owner_type_is_not_observed_insurer_policyholder") is not True):
        fail("unverified original ownership source or false semantic mapping")
    rows=o.get("kreise",[])
    if len(rows)!=400 or len({r.get("ags") for r in rows})!=400:
        fail("missing/duplicate exact original Landkreis owner observations")
    bmap={r["ags"]:r["geb_mit_wohnraum"] for r in b["kreise"]}
    if {r["ags"] for r in rows}!=set(bmap):fail("original building/owner county join not one to one")
    available=[0]*8
    coverage=[0]*8
    reconstructed=[]
    for r in rows:
        ags=r["ags"]
        values=r.get("original_owner_codes")
        if not isinstance(values,list) or len(values)!=8:
            fail("owner source must retain all eight categories per Kreis")
        v=[]
        for i,x in enumerate(values):
            if x=="missing":v.append(None);continue
            if type(x) is not int or x<0 or x>bmap[ags]+10:fail("not an original owner count")
            available[i]+=x
            coverage[i]+=1
            v.append(x)
        delta=sum(v)-bmap[ags] if all(x is not None for x in v) else None
        reconstructed.append({
            "ags":ags,"buildings_with_residential_use_2022":bmap[ags],
            "ownership_categories_2022":v,
            "ownership_fully_numeric":delta is not None,
            "original_owner_category_sum_minus_total":delta,
        })
    canonical=json.dumps(sorted(reconstructed,key=lambda x:x["ags"]),sort_keys=True,
                         ensure_ascii=False,separators=(",",":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest()!=HASH:
        fail("original published owner source values changed; SHA mismatch")
    if (available!=COUNTS or coverage!=COVERAGE
        or o.get("source_column_numeric_totals_available_only")!=COUNTS
        or o.get("source_column_numeric_kreise")!=COVERAGE
        or o.get("source_county_building_total")!=19957288
        or o.get("original_all_eight_numeric_kreise")!=385):
        fail("original 2022 owner source aggregate/coverage no longer reconciles")
    return bmeta,{r["ags"]:r for r in rows}


def simulate_owner_code_scenarios(o,b,h):
    bmeta,owners=validate_owner_source(o,b)
    if (h.get("entity")!="R+V Allgemeine Versicherung AG"
        or h.get("entity_kind")!="solo_direct_insurer"
        or h.get("accounting_basis")!="HGB_Gebuchte_Bruttobeitraege"
        or h.get("premium_unit")!="thousand_eur"
        or h.get("company_geo_exposure_observed") is not False):
        fail("wrong observed insurer national legal entity")
    p=[r for r in h["building_contract_observations"]["years"] if r.get("year")==2025]
    g=[r for r in h["years"] if r.get("year")==2025]
    if len(p)!=1 or len(g)!=1 or p[0].get("contracts")!=1060546 or g[0].get("connected_buildings_self_written")!=997710:
        fail("original issuer national 2025 company control changed")
    count=1060546
    cents=99771000000
    cases={}
    for name,owner_idx in CASES.items():
        region=[]
        for ags,r in sorted(owners.items()):
            building=next(x["geb_mit_wohnraum"] for x in b["kreise"] if x["ags"]==ags)
            # Source code 1 and 2 are numeric in every Kreis.
            # 2x base + 1x selected owner source class = 50% bonus for that
            # part of the physical opportunity population, NOT insurer truth.
            addition=0 if owner_idx is None else r["original_owner_codes"][owner_idx]
            if type(addition) is not int or addition<0:fail("selected owner source code not numeric")
            region.append({
                "region_code":"KREIS_"+ags,"hypothetical_contract_capacity":str(building*2),
                "contract_prior_weight":str(2*building+addition),
                "premium_relativity":"1",
                "hypothetical_market_elemental_share":"0",
                "assumed_carrier_uptake_multiplier":"0",
            })
        raw={
            "schema_version":"0.1.0","scenario_kind":"fully_synthetic_test_only",
            "reporting_scope":"fictional_solo_direct_residential_building",
            "year_end":"2025-12-31",
            "contract_population":"at_least_one_year_contracts_at_year_end_not_buildings",
            "premium_population":"annual_direct_gross_written_eur_cents_not_tariff",
            "geography_status":"hypothetical_not_insurer_observed",
            "take_up_status":"hypothetical_market_reference_not_carrier_observed",
            "synthetic_total_year_end_contracts":str(count),
            "synthetic_total_written_gwp_eur_cents":str(cents),
            "regions":region,
        }
        book=allocate_synthetic_regional_book(raw)
        if not book["synthetic_total_contracts_conserved"] or not book["synthetic_total_annual_written_gwp_cents_conserved"] or book["model_input_approved"]:
            fail("exact gross written premium/national contracts not conserved")
        states={}
        for r in book["regions"]:
            ags=r["region_code"][6:]
            state=states.setdefault(ags[:2],{"hypothetical_contracts":0,"hypothetical_gwp_eur_cents":0})
            state["hypothetical_contracts"]+=r["synthetic_contracts_at_year_end"]
            state["hypothetical_gwp_eur_cents"]+=r["hypothetical_regional_annual_gwp_eur_cents"]
        if sum(x["hypothetical_contracts"] for x in states.values())!=count or sum(x["hypothetical_gwp_eur_cents"] for x in states.values())!=cents:
            fail("state sums not conserved")
        cases[name]={"selected_original_owner_source_column":None if owner_idx is None else CODES[owner_idx],
                     "fictional_affinity_bonus_factor":"1.5" if owner_idx is not None else "1.0",
                     "state_rollups":dict(sorted(states.items())),
                     "county_allocations":book["regions"],
                     "company_policyholder_ownership_observed":False,
                     "actual_rva_2025_geo_exposure_observed":False}
    base={r["region_code"]:r["synthetic_contracts_at_year_end"] for r in cases["ALL_PUBLISHED_BUILDINGS"]["county_allocations"]}
    for v in cases.values():
        tv=sum(abs(r["synthetic_contracts_at_year_end"]-base[r["region_code"]]) for r in v["county_allocations"])
        if tv%2:fail("scenario relocation not exactly conserved")
        v["hypothetical_relocated_contracts_vs_baseline"]=tv//2
        v["hypothetical_total_variation"]=format((Decimal(tv//2)/Decimal(count)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP),"f")
    return {"schema_version":"RVA_2025_ORIGINAL_KREIS_OWNER_CODE_SENSITIVITY_V0",
            "issuer":"R+V Allgemeine Versicherung AG",
            "source_county_count":bmeta["original_2022_kreis_count"],
            "observed_solo_national_2025_contracts":count,
            "observed_solo_national_2025_booked_gwp_eur_cents":cents,
            "scenarios":cases,
            "admission":{"exact_owner_label_mapping_confirmed":False,
                         "rva_owner_type_policyholder_share_observed":False,
                         "rva_actual_geocoded_sites_or_tiv":False,
                         "rva_true_elemental_policy_mix":False,
                         "oasis_germany_gross_net_oep_aep_ready":False,
                         "model_input_approved":False}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner",type=Path,default=OWNER)
    p.add_argument("--buildings",type=Path,default=BUILDINGS)
    p.add_argument("--issuer",type=Path,default=ISSUER)
    p.add_argument("--all-counties",action="store_true")
    x=p.parse_args()
    try:
        blobs=[v.read_bytes() for v in (x.owner,x.buildings,x.issuer)]
        if any(len(v)>1000000 for v in blobs):fail("source too large")
        o,b,h=[tomllib.loads(v.decode("utf-8")) for v in blobs]
        r=simulate_owner_code_scenarios(o,b,h)
        if not x.all_counties:
            for c in r["scenarios"].values():c.pop("county_allocations")
        r["input_sha256"]={k:hashlib.sha256(v).hexdigest() for k,v in zip(("owner","building","insurer"),blobs)}
        print(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2))
    except (OSError,UnicodeError,ValueError) as e:p.exit(2,"BLOCKED: "+str(e)+"\n")

if __name__=="__main__":
    main()
