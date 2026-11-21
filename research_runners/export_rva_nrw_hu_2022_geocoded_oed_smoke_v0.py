# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three public physical HU 2022 WGS84 source points -> fictional OED smoke.

Original SHP/DBF *prefix* is not full original-source authenticated; physical
features are not checked for residential use, never actual R+V insurer sites.
No native Germany hazard/vulnerability, financial coverage or treaty model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys

from rva_nrw_hu_2022_first_polygons_v0 import probe

PORT="HU2022-NRW-SYNTHETIC-FINANCIAL-TEST-NOT-RV"
SITE_COUNT=3
FICTITIOUS_BUILDING_VALUE_EUR=450000
FIELDS_LOC=("PortNumber","AccNumber","LocNumber","LocGroup","CountryCode",
            "Latitude","Longitude","LocCurrency","LocPerilsCovered","BuildingTIV",
            "ContentsTIV","BITIV","OtherTIV","NumberOfBuildings","OEDVersion")
FIELDS_ACC=("PortNumber","AccNumber","PolNumber","AccCurrency","PolPerilsCovered","OEDVersion")


def export_coordinates_audited(source:dict,out:Path)->dict:
    if (not isinstance(source,dict) or
        source.get("schema")!="NRW_HU_2022_ORIGINAL_FIRST_PHYSICAL_POLYGON_SMOKE_V0" or
        source.get("actual_source_geometry_reprojected_to_wgs84") is not True or
        source.get("source_original_zip_sha256_verified") is not False or
        source.get("actual_RV_insured_site_location_verified") is not False or
        source.get("model_input_approved") is not False or
        source.get("observed_original_example_physical_polygons_count")!=SITE_COUNT or
        source.get("bounded_original_prefix_audit",{}).get("shp_records_inspected")!=250):
        raise ValueError("source proof or original admission boundary changed")
    coords=source.get("physical_source_only_sample_wgs84_coordinates")
    counties=source.get("original_example_county_codes")
    if not isinstance(coords,list) or len(coords)!=SITE_COUNT or not isinstance(counties,list) or len(counties)!=SITE_COUNT:
        raise ValueError("source preview original geometry count mismatch")
    for loc,ags in zip(coords,counties):
        if (not isinstance(loc,dict) or type(loc.get("lat")) not in (int,float)
            or type(loc.get("lon")) not in (int,float)
            or not 50<loc["lat"]<53 or not 5<loc["lon"]<10
            or not isinstance(ags,str) or len(ags)!=5 or not ags.startswith("05")
            or not ags.isdecimal()):
            raise ValueError("original preview physical coordinate or county changed")
    if out.exists() or not out.parent.is_dir():
        raise ValueError("fresh output directory required")
    out.mkdir(mode=0o700)
    try:
        with (out/"location.csv").open("x",encoding="utf8",newline="") as lf, \
             (out/"account.csv").open("x",encoding="utf8",newline="") as af:
            lw=csv.DictWriter(lf,fieldnames=FIELDS_LOC,lineterminator="\n");lw.writeheader()
            aw=csv.DictWriter(af,fieldnames=FIELDS_ACC,lineterminator="\n");aw.writeheader()
            for i,(loc,ags) in enumerate(zip(coords,counties),1):
                ident=f"FICT-HU22-{i:03}"
                lw.writerow({
                    "PortNumber":PORT,"AccNumber":ident,"LocNumber":ident,
                    "LocGroup":"KREIS-"+ags,"CountryCode":"DE",
                    "Latitude":format(loc["lat"],".6f"),"Longitude":format(loc["lon"],".6f"),
                    "LocCurrency":"EUR","LocPerilsCovered":"WW2",
                    "BuildingTIV":str(FICTITIOUS_BUILDING_VALUE_EUR),
                    "ContentsTIV":"0","BITIV":"0","OtherTIV":"0",
                    "NumberOfBuildings":"1","OEDVersion":"5.0.0",
                })
                aw.writerow({
                    "PortNumber":PORT,"AccNumber":ident,"PolNumber":ident,
                    "AccCurrency":"EUR","PolPerilsCovered":"WW2","OEDVersion":"5.0.0",
                })
        manifest={
            "schema":"NRW_HU_2022_ORIGINAL_PREFIX_PHYSICAL_POINTS_FICTITIOUS_OED_V0",
            "source_status":"PREFIX_ONLY_NOT_FULL_SOURCE_AUTHENTICATED",
            "2022_physical_geometry_source":"Geobasis NRW historical HU shapefile (original ZIP partial ranges)",
            "source_original_publisher_archive":"https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip",
            "source_original_zip_full_sha256_verified":False,
            "sample_source_physical_coordinate_WGS84_from_transformed_original":True,
            "original_source_geometry_residential_use_verified":False,
            "fictitious_insurance_contracts":SITE_COUNT,
            "fictitious_building_tiv_per_location_eur":FICTITIOUS_BUILDING_VALUE_EUR,
            "fictitious_total_tiv_eur":SITE_COUNT*FICTITIOUS_BUILDING_VALUE_EUR,
            "actual_RV_insured_buildings_verified":False,
            "actual_RV_policy_or_coverage_observed":False,
            "actual_insurer_PV_installed_at_sites":False,
            "germany_model_vulnerability_lookup_verified":False,
            "native_oasis_GUL_IL_RI_OEP_AEP_verified":False,
            "germany_CAT_model_input_approved":False,
            "source_transformation_receipt":source,
            "output_sha256":{
                fn:hashlib.sha256((out/fn).read_bytes()).hexdigest()
                for fn in ("location.csv","account.csv")
            },
        }
        (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf8")
        return manifest
    except Exception:
        shutil.rmtree(out)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir",type=Path)
    parser.add_argument("--live",action="store_true",help="explicit bounded official source geometry prefix lookup")
    options=parser.parse_args()
    if not options.live:
        parser.exit(2,"BLOCKED: --live must be explicitly selected\n")
    receipt=export_coordinates_audited(probe(),options.output_dir)
    from ods_tools import __version__ as ver
    from ods_tools.oed import OedExposure
    if ver!="5.0.8":
        raise ValueError("pinned official ODS Tools 5.0.8 required")
    OedExposure(location=str(options.output_dir/"location.csv"),
                account=str(options.output_dir/"account.csv"),check_oed=True)
    print(json.dumps({
       "status":"OED_FORMAT_OK_PHYSICAL_SOURCE_ONLY_FICTITIOUS_INSURANCE_NO_HAZARD_MODEL",
       "fictional_geocoded_location_count":SITE_COUNT,
       "source_zip_full_sha_verified":False,
       "actual_rv_insurer_sites":False,
       "OED_location_SHA256":receipt["output_sha256"]["location.csv"],
       "OED_account_SHA256":receipt["output_sha256"]["account.csv"],
    },sort_keys=True))
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except (OSError,ValueError) as exc:
        print("NRW_HU22_GEOCODED_OED_SMOKE_BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(2)
