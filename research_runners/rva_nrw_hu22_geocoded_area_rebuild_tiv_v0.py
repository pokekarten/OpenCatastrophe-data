# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Derive 3 explicitly fictional rebuilding-value sensitivities from *measured
public footprint ground area* in the source-verified NRW 10k OED artifact.

Not actual floor area (height/stories unobserved), construction age, occupancy,
insurer exposure, actual R+V insured value or CAT vulnerability. Only BuildingTIV
is revised; location/account IDs, physical WGS84 coordinates and county remain
identical across scenarios. Requires pre-existing original full source SHA/CRC.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

SCENARIOS={
    "low_single_storey_1800_eur_per_m2":(1,1800),
    "central_two_storeys_2200_eur_per_m2":(2,2200),
    "high_three_storeys_3000_eur_per_m2":(3,3000),
}
SOURCE_FILES=("account.csv","location.csv","manifest.json","physical_candidate_evidence.csv")
EXPECTED_N=10000
EXPECTED_KREISE=53


def csvbytes(rows:list[dict],fieldnames:list[str])->bytes:
    s=io.StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=fieldnames,lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue().encode("utf-8")


def _read(z:zipfile.ZipFile,name:str)->tuple[list[dict],list[str]]:
    with z.open(name) as f:
        text=io.TextIOWrapper(f,encoding="utf-8",newline="")
        r=csv.DictReader(text)
        if r.fieldnames is None or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("missing or duplicate CSV columns "+name)
        rows=list(r)
        return rows,list(r.fieldnames)


def build(source_zip:Path,output_zip:Path)->dict:
    if output_zip.exists() or not output_zip.parent.is_dir():
        raise ValueError("output ZIP must not exist; parent must exist")
    if not source_zip.is_file() or source_zip.stat().st_size>50_000_000:
        raise ValueError("input original-derived OED artifact must be a bounded existing file")
    with zipfile.ZipFile(source_zip) as z:
        if set(z.namelist())!=set(SOURCE_FILES) or z.testzip() is not None:
            raise ValueError("unrecognized or corrupt full-original source OED artifact")
        manifest=json.loads(z.read("manifest.json"))
        if (manifest.get("schema")!="RVA_NRW_2022_HU_STRATIFIED_PHYSICAL_CANDIDATES_GEO_OED_V0"
            or manifest.get("status")!="GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED"
            or manifest.get("source_original_2022_HU_full_CRCs_verified") is not True
            or not re.fullmatch(r"[0-9a-f]{64}",str(manifest.get("source_original_2022_HU_complete_archive_SHA256")))
            or manifest.get("physical_building_candidates_selected")!=EXPECTED_N
            or manifest.get("real_source_counties_represented")!=EXPECTED_KREISE
            or manifest.get("fictional_policy_count")!=EXPECTED_N
            or manifest.get("model_input_approved") is not False
            or manifest.get("insurer_building_TIV_observed") is not False
            or manifest.get("physical_building_footprints_are_actual_RV_insured_sites") is not False):
            raise ValueError("source original full SHA/CRC/NRW-company nonadmission gate failed")
        for name,sha in manifest["output_file_SHA256"].items():
            if name not in SOURCE_FILES or hashlib.sha256(z.read(name)).hexdigest()!=sha:
                raise ValueError("source OED CSV SHA256 mismatch "+name)
        loc,lf=_read(z,"location.csv")
        account,af=_read(z,"account.csv")
        evidence,ef=_read(z,"physical_candidate_evidence.csv")
        if (len(loc),len(account),len(evidence))!=(EXPECTED_N,EXPECTED_N,EXPECTED_N):
            raise ValueError("10k physical site/account/evidence population mismatch")
        lmap={r["LocNumber"]:r for r in loc}
        amap={r["AccNumber"]:r for r in account}
        emap={r["LocNumber"]:r for r in evidence}
        if (len(lmap),len(amap),len(emap))!=(EXPECTED_N,EXPECTED_N,EXPECTED_N) or set(lmap)!=set(amap)!=set(emap):
            # Explicit compare avoids one-to-many or duplicate risk-site identity.
            raise ValueError("source one-account-one-site crosswalk broken")
        if set(lmap)!=set(amap) or set(lmap)!=set(emap):
            raise ValueError("source site/account/evidence keys mismatch")
        source_counties=set()
        area_by_loc={}
        for site in loc:
            ident=site["LocNumber"]
            ev=emap[ident]
            ags=site["LocGroup"]
            if (not ags.startswith("KREIS-05") or len(ags)!=11
                or ev["KreisAGS2022"]!=ags[6:]
                or ev["SourcePhysicalCandidateNotInsuredSite"]!="true"
                or not re.fullmatch(r"31001_\d{4}",ev["SourceGFK"])
                or not re.fullmatch(r"[0-9a-f]{64}",ev["SourceOiSHA256"])
                or site["CountryCode"]!="DE" or site["OEDVersion"]!="5.0.0"):
                raise ValueError("source geometry, code or hypothetical insurer association changed")
            lat,lon=Decimal(site["Latitude"]),Decimal(site["Longitude"])
            if not Decimal(50)<lat<Decimal("52.8") or not Decimal("5.5")<lon<Decimal(10):
                raise ValueError("source CRS/WGS84 coordinate outside NRW")
            area=Decimal(ev["SourceFootprintAreaM2"])
            if not area.is_finite() or not Decimal(20)<=area<=Decimal(100000):
                raise ValueError("source polygon footprint area missing or nonphysical")
            area_by_loc[ident]=area
            source_counties.add(ags)
        if len(source_counties)!=EXPECTED_KREISE:
            raise ValueError("source all 53 NRW Kreise missing")
        account_original=z.read("account.csv")
        source_hash=hashlib.sha256(source_zip.read_bytes()).hexdigest()
        output_summary={
            "schema":"RVA_NRW_2022_HU_10K_GEOCODED_FOOTPRINT_REBUILD_TIV_SENSITIVITY_V0",
            "status":"EXPLICITLY_FICTIONAL_REBUILDING_COST_SENSITIVITY_NOT_GERMAN_CAT_RUN",
            "original_public_HU2022_archive_SHA256":manifest["source_original_2022_HU_complete_archive_SHA256"],
            "source_geocoded_OED_artifact_SHA256":source_hash,
            "real_source_physical_footprint_ground_area_m2_from_2022_HU":True,
            "floor_area_or_storeys_observed":False,
            "EUR_per_m2_rebuild_cost_is_observed":False,
            "insured_RV_building_values_observed":False,
            "actual_RV_locations_observed":False,
            "model_input_approved":False,
            "native_German_Oasis_GUL_IL_RI_OEP_AEP":False,
            "fictional_policy_count":EXPECTED_N,
            "real_NRW_counties_represented":EXPECTED_KREISE,
            "scenario_case_results":{},
        }
        try:
            with zipfile.ZipFile(output_zip,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as target:
                for name,(floors,cost) in SCENARIOS.items():
                    changed=[]
                    values=[]
                    for site in loc:
                        amount=(area_by_loc[site["LocNumber"]]*Decimal(floors)*Decimal(cost)).quantize(
                            Decimal(1),rounding=ROUND_HALF_UP)
                        if not 0<amount<=Decimal(500_000_000):
                            raise ValueError("fictional footprint-TIV scenario outside explicit bound")
                        copy=dict(site)
                        copy["BuildingTIV"]=str(int(amount))
                        changed.append(copy)
                        values.append(int(amount))
                    prefix=name+"/"
                    location_bytes=csvbytes(changed,lf)
                    target.writestr(prefix+"location.csv",location_bytes)
                    target.writestr(prefix+"account.csv",account_original)
                    scenario_manifest={
                        "schema":"RVA_NRW_HU2022_FOOTPRINT_TOY_BUILDING_TIV_OED_V0",
                        "scenario":name,
                        "assumed_floor_count":floors,"assumed_rebuilding_cost_eur_per_m2":cost,
                        "source_ground_footprint_area_is_not_floor_area":True,
                        "source_original_zip_sha256":manifest["source_original_2022_HU_complete_archive_SHA256"],
                        "fictional_building_count":len(changed),
                        "fictional_total_building_TIV_EUR":sum(values),
                        "all_locations_from_real_public_physical_candidate_polygons":True,
                        "actual_insurer_building_TIV_or_policy_known":False,
                        "model_run_approved":False,
                        "output_SHA256":{
                            "location.csv":hashlib.sha256(location_bytes).hexdigest(),
                            "account.csv":hashlib.sha256(account_original).hexdigest(),
                        },
                    }
                    target.writestr(prefix+"manifest.json",json.dumps(scenario_manifest,sort_keys=True,indent=2)+"\n")
                    output_summary["scenario_case_results"][name]={
                        "assumed_storeys":floors,"assumed_cost_eur_per_m2":cost,
                        "synthetic_total_building_TIV_eur":sum(values),
                        "synthetic_mean_building_TIV_eur":round(sum(values)/EXPECTED_N),
                        "location_csv_sha256":scenario_manifest["output_SHA256"]["location.csv"],
                    }
                target.writestr("scenario_comparison.json",json.dumps(output_summary,sort_keys=True,indent=2)+"\n")
        except Exception:
            output_zip.unlink(missing_ok=True)
            raise
        return output_summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_geocoded_oed_zip",type=Path)
    p.add_argument("output_sensitivity_zip",type=Path)
    opts=p.parse_args()
    try:
        print(json.dumps(build(opts.source_geocoded_oed_zip,opts.output_sensitivity_zip),
                         sort_keys=True,indent=2,ensure_ascii=False))
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        p.exit(2,"BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    sys.exit(main())
