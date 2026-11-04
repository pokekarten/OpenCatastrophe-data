# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""53 NRW Kreis public PV unit × 2022 Census building-age context; NO R+V company exposure.

Registered PV generating units from a MaStR-derived secondary public CSV are
NOT insured buildings/roofs. Original 2022 Census physical building count
is NOT 2025 R+V policies; county code join is the only common evidence.
"""
from __future__ import annotations

from collections import Counter
import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tomllib
import urllib.request

from research_runners import rva_nrw_mastr_derived_municipal_crosswalk_v0 as ma
from research_runners import rva_nrw_original_rooftop_pv_xlsx_v0 as nrw

ROOT = Path(__file__).resolve().parents[1]
BUILDINGS = ROOT / "research" / "observations" / "zensus2022_400_kreis_original_building_aggregates_v0.toml"
AGE = ROOT / "research" / "observations" / "zensus2022_400_kreis_original_building_age_cohorts_v0.toml"
CROSSWALK_RECEIPT = ma.RECEIPT_PATH
EXPECTED_KREIS_NRW = 53
SOURCE_ORIGINAL_CENSUS_SHA = "82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551"


def load_public_county_context(*, building_file: Path = BUILDINGS, age_file: Path = AGE):
    b = tomllib.loads(building_file.read_text(encoding="utf-8"))
    a = tomllib.loads(age_file.read_text(encoding="utf-8"))
    if (
        b.get("schema_version") != "ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGGREGATES_V0"
        or a.get("schema_version") != "ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGE_COHORTS_V0"
        or b.get("original_full_file_sha256") != SOURCE_ORIGINAL_CENSUS_SHA
        or a.get("original_workbook_full_sha256") != SOURCE_ORIGINAL_CENSUS_SHA
        or len(b.get("kreise", [])) != 400 or len(a.get("kreise", [])) != 400
        or b.get("source_event_date") != "2022-05-15"
        or a.get("source_date") != "2022-05-15"
        or b.get("real_insurer_model_admitted") is not False
        or a.get("insurer_model_input_admitted") is not False
    ):
        raise ValueError("CENSUS_2022_KREIS_ORIGINAL_SOURCE_OR_PERIMETER_INVALID")
    bd={r["ags"]:r for r in b["kreise"] if r["ags"].startswith("05")}
    ag={r["ags"]:r for r in a["kreise"] if r["ags"].startswith("05")}
    if len(bd)!=EXPECTED_KREIS_NRW or set(bd)!=set(ag):
        raise ValueError("CENSUS_NRW_53_KREIS_MATCH_FAILED")
    for code in bd:
        if ag[code]["buildings_mit_wohnraum_2022"]!=bd[code]["geb_mit_wohnraum"]:
            raise ValueError("CENSUS_AGE_BUILDING_2022_TOTAL_MISMATCH")
        bands=ag[code]["age_bands_source_order"]
        if (len(bands)!=10 or any(type(v) is not int or v<0 for v in bands)
            or abs(sum(bands)-bd[code]["geb_mit_wohnraum"])>20):
            raise ValueError("CENSUS_AGE_CELLKEY_PRECISION_VIOLATION")
    return bd,ag


def aggregate_NRW_Kreise(secondary_bytes: bytes, original_nrw_ags: set[str],
                         county_buildings: dict, county_ages: dict) -> dict:
    source=ma.inspect_secondary(secondary_bytes,pin_blob=True)
    exact=ma.crosswalk(source, original_nrw_ags)
    if exact["join_exact_AGS_count"]!=396 or len(county_buildings)!=EXPECTED_KREIS_NRW:
        raise ValueError("COUNTY_MUNICIPAL_SOURCE_NOT_COMPLETE")
    county={code:{"AGS_Kreis":code,"municipality_rows":0,
        "active_PV_generating_units":0,"building_PV_generating_units":0,
        "balcony_PV_generating_units":0,"freefield_PV_generating_units":0,
        "other_PV_generating_units":0,"all_PV_installed_kWp":Decimal(0)}
        for code in county_buildings}
    reader=csv.DictReader(io.StringIO(secondary_bytes.decode("utf-8-sig"),newline=""))
    seen=set()
    for row in reader:
        ags=row["ags"]
        if not ags.startswith("05"):
            continue
        if ags in seen or ags not in original_nrw_ags:
            raise ValueError("NRW_KREIS_SECONDARY_MUNICIPALITY_INVALID")
        seen.add(ags)
        code=ags[:5]
        if code not in county:
            raise ValueError("NRW_2026_MUNICIPALITY_2022_KREIS_CODE_NOT_RECONCILED")
        r=county[code]
        r["municipality_rows"]+=1
        for target,field in (
            ("active_PV_generating_units","einheiten_in_betrieb"),
            ("building_PV_generating_units","gebaeudesolaranlagen"),
            ("balcony_PV_generating_units","balkonkraftwerke"),
            ("freefield_PV_generating_units","freiflaeche"),
            ("other_PV_generating_units","sonstige")
        ):
            r[target]+=ma.parse_count(row[field])
        r["all_PV_installed_kWp"]+=ma.parse_power(row["kwp"])
    if len(seen)!=396 or set(county)!=set(county_buildings) or any(
        r["municipality_rows"]<=0 for r in county.values()
    ):
        raise ValueError("NRW_53_KREIS_COVERAGE_INCOMPLETE")
    out=[]
    for code in sorted(county):
        row=county[code]
        buildings=county_buildings[code]
        age=county_ages[code]
        if sum(row[k] for k in (
            "building_PV_generating_units","balcony_PV_generating_units",
            "freefield_PV_generating_units","other_PV_generating_units"
        ))!=row["active_PV_generating_units"]:
            raise ValueError("NRW_KREIS_PV_CLASS_NONADDITIVE")
        total=buildings["geb_mit_wohnraum"]
        if type(total) is not int or total<=0:
            raise ValueError("NRW_PUBLISHED_COUNTY_BUILDING_INVALID")
        out.append({
            **{k:v for k,v in row.items() if k!="all_PV_installed_kWp"},
            "all_PV_installed_kWp":format(row["all_PV_installed_kWp"].quantize(Decimal("0.001"),rounding=ROUND_HALF_UP),"f"),
            "zensus2022_published_buildings_with_living_space":total,
            "zensus2022_residential_buildings":buildings["wohngebaeude"],
            "zensus2022_mixeduse_buildings_with_living_space":buildings["sonstige_gebaeude_mit_wohnraum"],
            "zensus2022_pre1950_age_cells":sum(age["age_bands_source_order"][:2]),
            "zensus2022_2000plus_age_cells":sum(age["age_bands_source_order"][7:]),
            # May be *multiple units per roof*; do not label as penetration.
            "ecological_2026_registered_building_PV_units_per_1000_2022_living_space_buildings":
                format((Decimal(row["building_PV_generating_units"])*1000/Decimal(total)).quantize(Decimal("0.001"),rounding=ROUND_HALF_UP),"f"),
        })
    totals={
        "active_PV_generating_units":sum(x["active_PV_generating_units"] for x in out),
        "building_PV_generating_units":sum(x["building_PV_generating_units"] for x in out),
        "balcony_PV_generating_units":sum(x["balcony_PV_generating_units"] for x in out),
        "freefield_PV_generating_units":sum(x["freefield_PV_generating_units"] for x in out),
        "other_PV_generating_units":sum(x["other_PV_generating_units"] for x in out),
        "zensus2022_published_buildings_with_living_space":
            sum(x["zensus2022_published_buildings_with_living_space"] for x in out),
    }
    if (totals["active_PV_generating_units"]!=1180822
        or totals["building_PV_generating_units"]!=876684
        or totals["balcony_PV_generating_units"]!=302851
        or totals["zensus2022_published_buildings_with_living_space"]!=4042220
        or sum(x["municipality_rows"] for x in out)!=396):
        raise ValueError("NRW_2022_2026_COUNTY_AGGREGATE_DID_NOT_RECONCILE")
    return {
        "schema":"NRW_53_KREIS_2022_CENSUS_2026_MASTR_DERIVED_PHYSICAL_CONTEXT_V0",
        "NRW_Kreise":len(out),
        "secondary_municipalities":396,
        "official_2022_Census_original_sha256":SOURCE_ORIGINAL_CENSUS_SHA,
        "derived_2026_MaStR_original_sha256":source["secondary_csv_full_sha256"],
        "official_2026_NRW_PV_potential_sha256":nrw.EXPECTED_SHA256,
        "observed_public_summary_counts":totals,
        "2025_RV_company_policy_locations_estimated_from_these_data":False,
        "two_source_vintages_statistically_aligned":False,
        "installed_unit_count_equals_roof_or_insured_building":False,
        "actual_coverage_PV_tiv_or_treaty_observed":False,
        "hazard_loss_model_admitted":False,
        "kreis_aggregates":out,
    }


def fetch_secondary_with_bounded_retry(*, fetch=ma.fetch_secondary) -> bytes:
    # Exact source Git-blob and sha256 checks still happen after acquisition.
    # Retry transient network errors only, never semantic/schema/hash failures.
    last_error = None
    for _ in range(2):
        try:
            return fetch(open_url=lambda request, timeout: urllib.request.urlopen(
                request, timeout=75
            ))
        except (OSError, TimeoutError) as exc:
            last_error = exc
    raise TimeoutError("PINNED_SECONDARY_SOURCE_NETWORK_UNAVAILABLE") from last_error


RECORDED_53_KREIS = (ROOT / "research" / "observations" /
    "rva_nrw_53_kreis_census2022_pv2026_source_bridge_v0.toml")
COUNTY_FIELDS = (
    "AGS_Kreis", "municipality_rows", "active_PV_generating_units",
    "building_PV_generating_units", "balcony_PV_generating_units",
    "freefield_PV_generating_units", "other_PV_generating_units",
    "all_PV_installed_kWp", "zensus2022_published_buildings_with_living_space",
    "zensus2022_residential_buildings",
    "zensus2022_mixeduse_buildings_with_living_space",
    "zensus2022_pre1950_age_cells", "zensus2022_2000plus_age_cells",
    "ecological_2026_registered_building_PV_units_per_1000_2022_living_space_buildings",
)


def verify_persisted_53_county_public_source(result: dict, *, register=None) -> dict:
    if register is None:
        register=tomllib.loads(RECORDED_53_KREIS.read_text(encoding="utf-8"))
    if (
        register.get("schema_version")!="RVA_NRW_53_KREIS_REAL_2022_BUILDINGS_2026_DERIVED_PV_CONTEXT_V0"
        or register.get("original_census_date")!="2022-05-15"
        or register.get("secondary_mastr_registry_date")!="2026-10-02"
        or register.get("original_census_publisher_sha256")!=SOURCE_ORIGINAL_CENSUS_SHA
        or register.get("secondary_MaStR_derived_pinned_sha256")!=result["derived_2026_MaStR_original_sha256"]
        or register.get("official_NRW_roof_potential_sha256")!=nrw.EXPECTED_SHA256
        or register.get("nrw_original_census_county_rows")!=53
        or register.get("nrw_secondary_pv_municipality_rows")!=396
        or register.get("source_data_are_public_county_aggregates") is not True
        or register.get("no_individual_municipality_or_pv_operator_rows") is not True
        or any(register.get(k) is not False for k in (
            "secondary_source_is_primary_BNetzA_XML",
            "company_RV_insurer_county_policies_observed",
            "company_RV_insured_pv_geography_or_TIV_observed",
            "same_year_insurer_covariate_universes",
            "insured_pv_policy_coverage_vulnerability_or_loss_known",
            "native_cat_and_RI_model_admitted",
        ))
    ):
        raise ValueError("RVA_NRW_53_COUNTY_ORIGINAL_OR_INSURER_SCOPE_CHANGED")
    rows=result.get("kreis_aggregates",[])
    recorded=register.get("kreise",[])
    if len(rows)!=53 or len(recorded)!=53:
        raise ValueError("RVA_NRW_53_COUNTY_SOURCE_COUNT_DRIFT")
    if {x.get("AGS_Kreis") for x in recorded}!={x.get("AGS_Kreis") for x in rows}:
        raise ValueError("RVA_NRW_53_COUNTY_AGGREGATE_KEYS_CHANGED")
    orig={x["AGS_Kreis"]:x for x in rows}
    for entry in recorded:
        actual=orig[entry["AGS_Kreis"]]
        if set(entry)!=set(COUNTY_FIELDS):
            raise ValueError("RVA_NRW_53_COUNTY_PUBLISHED_FIELDS_CHANGED")
        if any(entry[key]!=actual[key] for key in COUNTY_FIELDS):
            raise ValueError("RVA_NRW_53_COUNTY_PUBLISHED_VALUES_CHANGED")
    for name,number in result["observed_public_summary_counts"].items():
        if register.get("national_NRW_"+name)!=number:
            raise ValueError("RVA_NRW_53_COUNTY_NATIONAL_SOURCE_SUM_DRIFT")
    return {
        "53_Kreis_public_source_aggregates_match_original":True,
        "insurer_and_CAT_model_source_admitted":False,
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--county-rows",action="store_true",
        help="Include ONLY PUBLIC 53 Landkreis aggregate rows, never 396 municipality rows")
    x=p.parse_args()
    b,a=load_public_county_context()
    secondary=fetch_secondary_with_bounded_retry()
    official=ma.official_nrw_ags(nrw.fetch_official())
    result=aggregate_NRW_Kreise(secondary,official,b,a)
    result["public_original_source_receipt"]=verify_persisted_53_county_public_source(result)
    if not x.county_rows:
        result.pop("kreis_aggregates")
    print(json.dumps(result,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,TimeoutError) as exc:
        print(f"NRW_53_KREIS_PHYSICAL_BRIDGE_BLOCKED: {type(exc).__name__}: {str(exc)[:70]}",file=sys.stderr)
        sys.exit(2)
