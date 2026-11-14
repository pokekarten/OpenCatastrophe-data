# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Zensus-2022 original 400-Kreis physical opportunities -> fictional 2025 RVA book.

Published Kreis *building* counts and national R+V Allgemeine 2025
year-end contracts/GWP are observed in separate populations. Their county
link, regional affinity, insured locations, TIV, peril endorsements, RI,
actual CAT losses and OEP/AEP are NOT observed and NOT claimed.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import tomllib

from synthetic_regional_property_book_v0 import SyntheticBookError, allocate_synthetic_regional_book

ROOT=Path(__file__).resolve().parents[1]
CENSUS=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
HGB=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
CODE=re.compile(r"(?:0[1-9]|1[0-6])[0-9]{3}\Z")
ORIGINAL_SHA="82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551"
CANONICAL_SOURCE_SHA="a48c2d17a6e00c97fb4a151b1d990df78642de17dfd6ddf932479357e2589ca1"
SCENARIOS={
 "PHYSICAL_ALL_RESIDENTIAL_USE":("geb_mit_wohnraum",0),
 "RESIDENTIAL_NON_DORMITORY":("wohngebaeude_ohne_wohnheime",0),
 "MIXED_USE_OVERWEIGHT_5X":("wohngebaeude_ohne_wohnheime",5),
}

def blocked(s):
    raise SyntheticBookError(s)

def validate_kreis_original(c):
    if (c.get("schema_version")!="ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGGREGATES_V0"
        or c.get("publisher")!="Statistisches Bundesamt (Destatis) / Statistische Aemter des Bundes und der Laender"
        or c.get("original_full_file_sha256")!=ORIGINAL_SHA
        or c.get("source_values_canonical_sha256")!=CANONICAL_SOURCE_SHA
        or c.get("source_event_date")!="2022-05-15"
        or c.get("source_original_reported_date_raw")!="20220515"
        or c.get("original_source_sheet")!="CSV-Gebäude"
        or c.get("source_geography")!="Stadtkreis/kreisfreie Stadt/Landkreis"
        or c.get("source_geo_key")!="_RS"
        or c.get("source_category_total")!="GEBAEUDEART_SYS_1"
        or c.get("source_category_residential")!="GEBAEUDEART_SYS_11"
        or c.get("source_category_residential_nondormitory")!="GEBAEUDEART_SYS_111"
        or c.get("source_category_residential_dormitory")!="GEBAEUDEART_SYS_112"
        or c.get("source_category_mixeduse")!="GEBAEUDEART_SYS_12"
        or c.get("license")!="Datenlizenz Deutschland – Namensnennung – Version 2.0"):
        blocked("original Zensus 2022 Kreis source identity/edition/rights changed")
    if not c.get("source_verification_workflow","").endswith("/41907363439"):
        blocked("original source verification workflow receipt missing")
    for k in ("physical_building_count_2022_is_insurer_contract_count_2025",
              "observed_rva_kreis_policies", "observed_rva_site_coordinates",
              "observed_rva_tiv", "observed_rva_flood_coverage",
              "real_insurer_model_admitted"):
        if c.get(k) is not False:
            blocked("physical 2022 census falsely presented as company 2025 exposure")
    rows=c.get("kreise",[])
    if c.get("region_rows")!=400 or len(rows)!=400:
        blocked("official source not full 400 Kreis")
    if len({r.get("ags") for r in rows})!=400 or len({r.get("ags","")[:2] for r in rows})!=16:
        blocked("duplicate, missing or mis-keyed Kreis")
    stats={"geb_mit_wohnraum":0,"wohngebaeude":0,"wohngebaeude_ohne_wohnheime":0,
           "wohnheime":0,"sonstige_gebaeude_mit_wohnraum":0}
    coverage={k:0 for k in stats}
    for r in rows:
        ags=r.get("ags")
        if not isinstance(ags,str) or not CODE.fullmatch(ags):
            blocked("not original five-digit 2022 Kreis")
        for k in stats:
            v=r.get(k)
            if v=="missing" and k!="geb_mit_wohnraum":
                continue
            if type(v) is not int or v<0 or v>10000000:
                blocked("wrongly replaced suppressed Zensus building count")
            stats[k]+=v
            coverage[k]+=1
        e=r["geb_mit_wohnraum"]
        if e==0: blocked("Census physical opportunity cannot be zero")
        for k in ("wohngebaeude","wohngebaeude_ohne_wohnheime","wohnheime",
                  "sonstige_gebaeude_mit_wohnraum"):
            v=r[k]
            if v!="missing" and v>e+10:
                blocked("unreasonable 2022 source hierarchy beyond Cell-Key tolerance")
    if (stats["geb_mit_wohnraum"]!=19957288
            or stats["wohngebaeude"]!=19488949
            or stats["sonstige_gebaeude_mit_wohnraum"]!=468301
            or coverage["geb_mit_wohnraum"]!=400 or coverage["wohngebaeude"]!=400
            or coverage["wohngebaeude_ohne_wohnheime"]!=400
            or coverage["sonstige_gebaeude_mit_wohnraum"]!=400
            or coverage["wohnheime"]!=393
            or c.get("dormitories_non_numeric_kreise")!=7):
        blocked("published primary source totals/coverage drift")
    if (c.get("original_printed_kreis_total_buildings_with_residential_use")!=stats["geb_mit_wohnraum"]
            or c.get("original_printed_kreis_total_residential_buildings")!=stats["wohngebaeude"]
            or c.get("original_printed_kreis_total_mixeduse")!=stats["sonstige_gebaeude_mit_wohnraum"]):
        blocked("typed source numeric subtotal not reconciled")
    return {"original_2022_kreis_count":len(rows),"original_land_count":16,
            "original_2022_kreis_buildings_total":stats["geb_mit_wohnraum"],
            "original_2022_kreis_residential":stats["wohngebaeude"],
            "original_2022_kreis_mixeduse":stats["sonstige_gebaeude_mit_wohnraum"],
            "original_2022_wohnheim_numeric_counties":coverage["wohnheime"],
            "published_kreis_sum_minus_separate_national_print":stats["geb_mit_wohnraum"]-19957268,
            "source_printed_CKM_region_sums_are_exact_underlying_counts":False}

def compare_real_census_fictional_rva(c,h):
    cmeta=validate_kreis_original(c)
    if (h.get("entity")!="R+V Allgemeine Versicherung AG" or
        h.get("entity_kind")!="solo_direct_insurer" or
        h.get("accounting_basis")!="HGB_Gebuchte_Bruttobeitraege" or
        h.get("premium_unit")!="thousand_eur" or
        h.get("company_geo_exposure_observed") is not False):
        blocked("wrong solo insurer company scope")
    pol=[r for r in h["building_contract_observations"]["years"] if r.get("year")==2025]
    fin=[r for r in h["years"] if r.get("year")==2025]
    if len(pol)!=1 or len(fin)!=1 or pol[0].get("contracts")!=1060546 or fin[0].get("connected_buildings_self_written")!=997710:
        blocked("insurer original 2025 national controls moved")
    total=pol[0]["contracts"]
    cents=fin[0]["connected_buildings_self_written"]*100000
    source=sorted(c["kreise"],key=lambda x:x["ags"])
    outputs={}
    for name,(primary,mixed_multiplier) in SCENARIOS.items():
        regions=[]
        for x in source:
            # Fictional regional policy-to-building and insurer affinity.
            # Source E/G/I values are factual 2022 population opportunities.
            weight=x[primary]+mixed_multiplier*x["sonstige_gebaeude_mit_wohnraum"]
            if type(weight) is not int or weight<=0:
                blocked("unsupported zero or nonnumeric physical opportunity")
            regions.append({
                "region_code":"KREIS_"+x["ags"],
                "hypothetical_contract_capacity":str(x["geb_mit_wohnraum"]*2),
                "contract_prior_weight":str(weight),
                "premium_relativity":"1",
                # Zero here means intentionally NOT estimated, not zero RVA cover.
                "hypothetical_market_elemental_share":"0",
                "assumed_carrier_uptake_multiplier":"0",
            })
        payload={
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
            "regions":regions,
        }
        out=allocate_synthetic_regional_book(payload)
        if (out["synthetic_total_contracts_conserved"] is not True
                or out["synthetic_total_annual_written_gwp_cents_conserved"] is not True
                or out["model_input_approved"] is not False
                or out["has_true_risk_site_coordinates"] is not False
                or out["has_insured_tiv"] is not False):
            blocked("synthetic allocator lost national mass or false insured geography")
        totals={}
        county={}
        for v in out["regions"]:
            code=v["region_code"][6:]
            state=code[:2]
            row=totals.setdefault(state,{"hypothetical_contracts":0,
                                          "hypothetical_written_gwp_eur_cents":0})
            row["hypothetical_contracts"]+=v["synthetic_contracts_at_year_end"]
            row["hypothetical_written_gwp_eur_cents"]+=v["hypothetical_regional_annual_gwp_eur_cents"]
            county[code]=v["synthetic_contracts_at_year_end"]
        if sum(x["hypothetical_contracts"] for x in totals.values())!=total or sum(x["hypothetical_written_gwp_eur_cents"] for x in totals.values())!=cents:
            blocked("synthetic 16 state check lost money or contracts")
        outputs[name]={"original_source_opportunity_basis":primary,
                       "invented_mixed_use_affinity_multiplier":mixed_multiplier,
                       "regions_400":out["regions"],
                       "hypothetical_2025_land_summaries":dict(sorted(totals.items())),
                       "county_count":len(county),
                       "issuer_count_and_premium_conserved":True,
                       "regional_carrier_contracts_observed":False,
                       "natural_peril_coverage_measured":False}
    base={r["region_code"]:r["synthetic_contracts_at_year_end"] for r in outputs["PHYSICAL_ALL_RESIDENTIAL_USE"]["regions_400"]}
    for name,case in outputs.items():
        a={r["region_code"]:r["synthetic_contracts_at_year_end"] for r in case["regions_400"]}
        l1=sum(abs(a[k]-base[k]) for k in base)
        if l1%2: blocked("county conservation mismatch")
        case["shifted_hypothetical_policies_vs_physical_all"]=l1//2
        case["county_total_variation_vs_physical_all"]=format(
            (Decimal(l1//2)/Decimal(total)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP),"f")
    return {"schema_version":"RVA_2025_400_KREIS_CENSUS_REAL_PRIOR_FICTIONAL_BOOK_V0",
            "target_insurer":h["entity"],
            "original_census_2022_source":cmeta,
            "observed_solo_2025_national_contract_count":total,
            "observed_solo_2025_national_written_premium_eur_cents":cents,
            "hypothetical_geographical_cases":outputs,
            "admission":{"true_rva_county_policy_shares_observed":False,
                         "true_2025_geocoded_rva_sites":False,"true_rva_building_tiv":False,
                         "true_rva_flood_endorsement_mix":False,
                         "full_native_oasis_loss_run":False,
                         "oep_aep_gross_net_calibrated":False,
                         "model_input_approved":False},
            "limitations":"Census Kreis 2022 building opportunities are authentic, issuer 2025 national contracts and GWP observed. Their regional association is a fictional counterfactual, not R+V actual exposures."
            }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--census",type=Path,default=CENSUS)
    p.add_argument("--issuer",type=Path,default=HGB)
    p.add_argument("--full-county",action="store_true",help="Include all fictional county allocations in stdout")
    args=p.parse_args()
    try:
        cb,hb=args.census.read_bytes(),args.issuer.read_bytes()
        if len(cb)>1000000 or len(hb)>1000000: blocked("input outside bounds")
        census,issuer=tomllib.loads(cb.decode("utf-8")),tomllib.loads(hb.decode("utf-8"))
        out=compare_real_census_fictional_rva(census,issuer)
        out["input_sha256"]={"public_census_400_kreis_toml":hashlib.sha256(cb).hexdigest(),
                              "observed_solo_company_hgb_toml":hashlib.sha256(hb).hexdigest()}
        if not args.full_county:
            for case in out["hypothetical_geographical_cases"].values():
                case.pop("regions_400")
        print(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2))
    except (OSError,UnicodeError,ValueError) as exc:
        p.exit(status=2,message="BLOCKED: "+str(exc)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
