# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Attach public official physical NRW HU residential-function *candidate* sites to
a 10k fictional R+V-like NRW OED 5.0 research sample, strictly preserving
hypothetical account IDs, premium-year boundaries and toy BuildingTIV.

This is NOT real carrier site discovery. Source ZIP must be original-full-byte
authenticated; physical selection is deterministic across all 53 counties.
Actual physical footprints are NOT proven same as Zensus residential buildings,
actual insurer policies, actual 2025 building ages or catastrophe vulnerabilities.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys

from rva_nrw_hu_full_zip_stratified_reservoir_v0 import (
    sample_full_official_zip,SourceBlocked
)

EXPECTED_COUNT=10000
EXACT_NRW_COUNTIES=53
EVIDENCE_FIELDS=("LocNumber","KreisAGS2022","SourceOiSHA256","SourceGFK",
                 "SourceFootprintAreaM2","SourcePhysicalCandidateNotInsuredSite")
REQUIRED_OED=("PortNumber","AccNumber","LocNumber","LocGroup","CountryCode",
              "Latitude","Longitude","BuildingTIV","OEDVersion")


def _source_input(directory:Path,*,expected_count:int=EXPECTED_COUNT):
    location_file=directory/"location.csv"
    account_file=directory/"account.csv"
    if not directory.is_dir() or location_file.stat().st_size>7_000_000 or account_file.stat().st_size>3_000_000:
        raise SourceBlocked("synthetic OED input directory or file limits invalid")
    with location_file.open(encoding="utf8",newline="") as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        if not fields or not set(REQUIRED_OED).issubset(fields):
            raise SourceBlocked("original synthetic OED schema incomplete")
        location=list(reader)
    with account_file.open(encoding="utf8",newline="") as f:
        accounts=list(csv.DictReader(f))
    if len(location)!=expected_count or len(accounts)!=expected_count:
        raise SourceBlocked("synthetic NRW base location and account sample size drift")
    if (len({r["LocNumber"] for r in location})!=expected_count
        or len({r["AccNumber"] for r in location})!=expected_count
        or {r["AccNumber"] for r in accounts}!={r["AccNumber"] for r in location}):
        raise SourceBlocked("synthetic portfolio IDs missing or duplicate")
    if any(r["Latitude"]!="" or r["Longitude"]!="" or r["CountryCode"]!="DE"
           or r["OEDVersion"]!="5.0.0" or int(r["BuildingTIV"])<=0
           or r["LocPerilsCovered"]!="WW2"
           for r in location):
        raise SourceBlocked("only un-geocoded openly fictional OED 5.0 NRW building inputs allowed")
    county=Counter()
    for row in location:
        locgroup=row["LocGroup"]
        if (not locgroup.startswith("KREIS-")
            or len(locgroup)!=11 or not locgroup[6:].startswith("05")
            or not locgroup[6:].isdigit()):
            raise SourceBlocked("untrusted source building synthetic county group")
        county[locgroup[6:]]+=1
    if expected_count==EXPECTED_COUNT and (len(county)!=EXACT_NRW_COUNTIES or min(county.values())<1):
        raise SourceBlocked("synthetic 53-Kreis NRWs source county population changed")
    return location,accounts,fields,dict(county)


def build_geocoded_oed(directory:Path, selected:dict,source_audit:dict,out:Path,
                      *,expected_count:int=EXPECTED_COUNT)->dict:
    location,accounts,fields,target=_source_input(directory,expected_count=expected_count)
    if set(selected)!=set(target) or any(len(selected[c])!=target[c] for c in target):
        raise SourceBlocked("physical candidate county selection does not conserve fictional insurer sample")
    if out.exists() or not out.parent.is_dir():
        raise SourceBlocked("destination must be newly created")
    coords=[]
    evidence=[]
    bycounty={c:iter(sorted(selected[c],key=lambda x:x["original_OI_sha256"])) for c in selected}
    sitehashes=set()
    for row in location:
        county=row["LocGroup"][6:]
        item=next(bycounty[county])
        source_key=item["original_OI_sha256"]
        if source_key in sitehashes:
            raise SourceBlocked("same public physical object selected for more than one fictitious contract")
        sitehashes.add(source_key)
        lon,lat=item["lon"],item["lat"]
        if not (isinstance(lon,float) and isinstance(lat,float)
                and 5.5<lon<10 and 50<lat<52.8
                and item["source_gfk"].startswith("31001_")):
            raise SourceBlocked("physical candidate coordinate/GFK not independently source-valid")
        newrow=dict(row)
        newrow["Latitude"]=format(lat,".7f")
        newrow["Longitude"]=format(lon,".7f")
        coords.append(newrow)
        evidence.append({
            "LocNumber":row["LocNumber"],"KreisAGS2022":county,
            "SourceOiSHA256":source_key,"SourceGFK":item["source_gfk"],
            "SourceFootprintAreaM2":format(item["footprint_area_m2"],".2f"),
            "SourcePhysicalCandidateNotInsuredSite":"true",
        })
    if len(sitehashes)!=expected_count:
        raise SourceBlocked("source object uniqueness sample count invalid")
    if any(not r["Latitude"] or not r["Longitude"] for r in coords):
        raise SourceBlocked("not all fictional locations have physical sample source coordinates")
    out.mkdir(mode=0o700)
    try:
        with (out/"location.csv").open("x",encoding="utf8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
            w.writeheader()
            w.writerows(coords)
        with (out/"account.csv").open("x",encoding="utf8",newline="") as f:
            f.write((directory/"account.csv").read_text(encoding="utf8"))
        with (out/"physical_candidate_evidence.csv").open("x",encoding="utf8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=EVIDENCE_FIELDS,lineterminator="\n")
            w.writeheader()
            w.writerows(evidence)
        hashes={s:hashlib.sha256((out/s).read_bytes()).hexdigest()
                for s in ("location.csv","account.csv","physical_candidate_evidence.csv")}
        manifest={
            "schema":"RVA_NRW_2022_HU_STRATIFIED_PHYSICAL_CANDIDATES_GEO_OED_V0",
            "status":"GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED",
            "source_original_2022_HU_complete_archive_SHA256":
                source_audit.get("full_original_source_zip_sha256"),
            "source_original_2022_HU_full_CRCs_verified":
                source_audit.get("all_four_original_member_CRCs_verified_by_ZipExtFile_EOF") is True,
            "original_HU_2022_physical_source_records_scanned":
                source_audit.get("original_shp_and_dbf_records_scanned"),
            "physical_building_candidates_selected":len(sitehashes),
            "real_source_counties_represented":len(target),
            "2022_HU_residential_related_GFK_not_actual_insured_occupancy":True,
            "physical_building_ages_observed":False,
            "physical_building_footprints_are_actual_RV_insured_sites":False,
            "observed_RV_county_policies_or_NRW_market_share":False,
            "fictional_policy_count":expected_count,
            "fictional_policy_link_count_preserved":True,
            "insurer_building_TIV_observed":False,
            "origins_HU2022_Census2022_HGB2025_PV2026_not_joint_distribution":True,
            "OED_schema_and_model_vulnerability_validated":False,
            "native_German_Oasis_GUL_IL_RI_OEP_AEP":False,
            "model_input_approved":False,
            "source_geographic_assignment_is_independent_fictional_randomized_hypothesis":True,
            "source_full_zip_audit":source_audit,
            "input_file_SHA256":{
                s:hashlib.sha256((directory/s).read_bytes()).hexdigest()
                for s in ("location.csv","account.csv")
            },
            "output_file_SHA256":hashes,
        }
        (out/"manifest.json").write_text(
            json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
        return manifest
    except Exception:
        shutil.rmtree(out)
        raise


def run(original_zip:Path,oed_input:Path,output:Path)->dict:
    _,_,_,target=_source_input(oed_input)
    selected,audit=sample_full_official_zip(original_zip,target)
    return build_geocoded_oed(oed_input,selected,audit,output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-2022-hu-zip",required=True,type=Path,
                        help="EXISTING original 901MB official NRW zip: not downloaded by this script")
    parser.add_argument("--fictional-nrw-oed",required=True,type=Path,
                        help="fresh source-pinned 53-Kreis 10k OED location/account directory")
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    try:
        m=run(args.original_2022_hu_zip,args.fictional_nrw_oed,args.output)
        from ods_tools.oed import OedExposure
        from ods_tools import __version__
        if __version__!="5.0.8":
            raise SourceBlocked("pinned official ODS 5.0.8 version required")
        OedExposure(location=str(args.output/"location.csv"),
                    account=str(args.output/"account.csv"),check_oed=True)
        print(json.dumps({
            "status":m["status"],
            "source_original_full_zip_SHA256":m["source_original_2022_HU_complete_archive_SHA256"],
            "geocoded_fictional_contracts":m["fictional_policy_count"],
            "native_germany_CAT_model_ran":False,
            "R_V_actual_insured_locations_observed":False,
        },sort_keys=True,ensure_ascii=False))
    except (OSError,ValueError,KeyError,ImportError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    return 0

if __name__=="__main__":
    sys.exit(main())
