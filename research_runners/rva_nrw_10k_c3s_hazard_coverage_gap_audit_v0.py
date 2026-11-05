# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only NRW 10k physical-OED to NextGen grid *coverage and exposure* audit.

The grid is deliberately synthetic, not a Copernicus footprint or a wind
hazard intensity/annual event measure. Source HU22 GFK is uncalibrated as a
material/roof wind-vulnerability code. Aggregate TIVs here are invented
replacement values, NOT licensed CAT losses or observed R+V insured amounts.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

INPUT_SCHEMA="RVA_NRW_SOURCE_GEO_TO_NEXTGEN_UNADMITTED_C3S_GRID_V0"
EXPECTED_HU_SHA="10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
EXPECTED_GRID="SYNTH-NRW-025DEG-NOT-C3S"
EXPECTED_COUNT=10000
EXPECTED_KREISE=53
EXPECTED_TOTAL_TIV=4826029500
FNAME="nextgen_c3s_spatial_handoff.json"
RNAME="source_boundary_receipt.json"
CELL_FIELDS=("CellId","GridColumn","GridRow","SyntheticAssetCount",
             "SyntheticBuildingTIVEUR","WindHazardMeasured",
             "WindVulnerabilityMapped")
GFK_FIELDS=("HU2022GFKCandidate","SyntheticAssetCount","SyntheticBuildingTIVEUR",
            "WindMaterialRoofVulnerabilityMapped")

class CoverageBlocked(ValueError):
    pass


def _canonical(obj)->bytes:
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()


def _csv(items,headers):
    output=io.StringIO(newline="")
    writer=csv.DictWriter(output,fieldnames=headers,lineterminator="\n")
    writer.writeheader();writer.writerows(items)
    return output.getvalue().encode()


def audit(path:Path,*,expected_count=EXPECTED_COUNT,expected_kreise=EXPECTED_KREISE,
          expected_tiv=EXPECTED_TOTAL_TIV)->dict:
    if (path.is_symlink() or not path.is_file() or path.stat().st_size>10_000_000
        or type(expected_count) is not int or not 1<=expected_count<=EXPECTED_COUNT
        or type(expected_kreise) is not int or not 1<=expected_kreise<=53
        or type(expected_tiv) is not int or not 1<=expected_tiv<=10**15):
        raise CoverageBlocked("bounded original-source-derived grid handoff required")
    with zipfile.ZipFile(path) as z:
        if set(z.namelist())!={FNAME,RNAME} or z.testzip() is not None:
            raise CoverageBlocked("unexpected corrupted handoff archive")
        original=z.read(FNAME)
        if len(original)>8_000_000:
            raise CoverageBlocked("research handoff JSON exceeds bound")
        receipt=json.loads(z.read(RNAME))
        if (receipt.get("schema")!=INPUT_SCHEMA
            or receipt.get("status")!="SPATIAL_CROSSWALK_SHAPE_ONLY_NO_ADMITTED_C3S_MODEL"
            or receipt.get("source_original_HU_2022_full_SHA256")!=EXPECTED_HU_SHA
            or receipt.get("source_physical_synthetic_OED_count")!=expected_count
            or receipt.get("original_NRW_counties")!=expected_kreise
            or receipt.get("synthetic_source_building_TIV_eur")!=expected_tiv
            or receipt.get("handoff_json_sha256")!=hashlib.sha256(original).hexdigest()
            or receipt.get("grid_is_fictional_not_C3S_NetCDF") is not True
            or receipt.get("actual_C3S_NetCDF_original_bytes_authenticated") is not False
            or receipt.get("source_specific_wind_vulnerability_taxonomy_mapped") is not False
            or receipt.get("wind_damage_probability_law_supplied") is not False
            or receipt.get("gross_insured_net_reinsurance_or_EP_executed") is not False):
            raise CoverageBlocked("original source / 10k / no-hazard receipt gate failed")
        data=json.loads(original)
    if not isinstance(data,dict) or set(data)!={"grid","crosswalk_assignments","insured_asset_values"}:
        raise CoverageBlocked("NextGen crosswalk handoff shape changed")
    grid=data["grid"]
    if (set(grid)!={"grid_id","west_lon_e6","south_lat_e6","width_e6",
                    "height_e6","num_lon","num_lat","crs"}
        or grid["grid_id"]!=EXPECTED_GRID or grid["crs"]!="EPSG:4326"
        or (grid["width_e6"],grid["height_e6"],grid["num_lon"],grid["num_lat"],
            grid["west_lon_e6"],grid["south_lat_e6"]) !=
           (250000,250000,20,13,5500000,50000000)):
        raise CoverageBlocked("not the explicitly unadmitted 0.25-degree grid fixture")
    sites=data["crosswalk_assignments"]
    values=data["insured_asset_values"]
    if (type(sites) is not list or type(values) is not list
        or len(sites)!=expected_count or len(values)!=expected_count):
        raise CoverageBlocked("unbalanced fictional source crosswalk")
    val_map={}
    for row in values:
        if (type(row) is not dict or set(row)!={"asset_id","replacement_cost_eur"}
            or not isinstance(row["asset_id"],str)
            or row["asset_id"] in val_map
            or type(row["replacement_cost_eur"]) is not int
            or not 1<=row["replacement_cost_eur"]<=500_000_000):
            raise CoverageBlocked("duplicate, invalid or non-fictitious replacement valuation row")
        val_map[row["asset_id"]]=row["replacement_cost_eur"]
    used=set()
    cell_n=Counter()
    cell_tiv=Counter()
    gfk_n=Counter()
    gfk_tiv=Counter()
    county_n=Counter()
    in_cell=defaultdict(set)
    for item in sites:
        if (type(item) is not dict
            or set(item)!={"asset_id","cedant_id","country_iso2","taxonomy","lon_e6","lat_e6","col","row","cell_id"}):
            raise CoverageBlocked("NextGen fixed site schema altered")
        aid=item["asset_id"]
        if aid in used or aid not in val_map:
            raise CoverageBlocked("duplicate or incomplete location-to-policy crosswalk")
        used.add(aid)
        if (not re.fullmatch(r"SYN-NRW-(05\d{3})-\d{2}-\d{6}",aid)
            or item["cedant_id"]!="FICTITIOUS_RVA_LIKE_NRW_NOT_OBSERVED"
            or item["country_iso2"]!="DE"
            or not re.fullmatch(r"UNMAPPED_HU22_GFK_31001_\d{4}",item["taxonomy"])):
            raise CoverageBlocked("site insurer/ground GFK identity would be overstated")
        if any(type(item[k]) is not int for k in ("lon_e6","lat_e6","col","row")):
            raise CoverageBlocked("source geocoordinates or cell indexes not precise integers")
        x=(item["lon_e6"]-grid["west_lon_e6"])//250000
        y=(item["lat_e6"]-grid["south_lat_e6"])//250000
        if ((x,y)!=(item["col"],item["row"])
            or not 0<=x<20 or not 0<=y<13
            or item["cell_id"]!=f"{EXPECTED_GRID}:x{x:05d}:y{y:05d}"):
            raise CoverageBlocked("source coordinates do not match synthetic cell math")
        cell=item["cell_id"];tiv=val_map[aid]
        county=aid.split("-")[2]
        cell_n[cell]+=1
        cell_tiv[cell]+=tiv
        county_n[county]+=1
        gfk_n[item["taxonomy"]]+=1
        gfk_tiv[item["taxonomy"]]+=tiv
        in_cell[cell].add(county)
    if (used!=set(val_map) or len(county_n)!=expected_kreise
        or len(used)!=expected_count or sum(cell_tiv.values())!=expected_tiv
        or len(cell_n)!=len(receipt.get("counts_by_demo_grid_cell",{}))
        or dict(cell_n)!=receipt["counts_by_demo_grid_cell"]
        or dict(county_n)!=receipt.get("counts_by_real_source_Kreis",{})):
        raise CoverageBlocked("source-receipt count, county or financial conservation failed")
    cellrows=[]
    for cell in sorted(cell_n):
        col,row=(int(v) for v in re.search(r":x(\d+):y(\d+)$",cell).groups())
        cellrows.append({
            "CellId":cell,"GridColumn":col,"GridRow":row,
            "SyntheticAssetCount":cell_n[cell],
            "SyntheticBuildingTIVEUR":cell_tiv[cell],
            "WindHazardMeasured":"false","WindVulnerabilityMapped":"false",
        })
    gfkrows=[
        {"HU2022GFKCandidate":k,"SyntheticAssetCount":gfk_n[k],
         "SyntheticBuildingTIVEUR":gfk_tiv[k],
         "WindMaterialRoofVulnerabilityMapped":"false"}
        for k in sorted(gfk_n)
    ]
    if sum(r["SyntheticBuildingTIVEUR"] for r in cellrows)!=expected_tiv:
        raise CoverageBlocked("cell-level TIV balance broken")
    summary={
        "schema":"NRW_2022_HU_10K_C3S_GRID_COVERAGE_ONLY_V0",
        "status":"SOURCE_GEOGRAPHY_ONLY_NO_REAL_WIND_MODEL_OR_INSURER_SITE_CLAIM",
        "original_full_HU22_SHA256":EXPECTED_HU_SHA,
        "source_handoff_zip_SHA256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_crosswalk_sha256":receipt["handoff_json_sha256"],
        "invented_grid_id":EXPECTED_GRID,
        "number_of_source_geocoded_fictional_sites":expected_count,
        "number_of_official_NRW_Kreis":expected_kreise,
        "number_of_occupied_invented_grid_cells":len(cell_n),
        "number_of_total_invented_grid_cells":260,
        "fictional_total_building_TIV_eur":expected_tiv,
        "max_exposed_toy_grid_cell_site_count":max(cell_n.values()),
        "max_exposed_toy_grid_cell_TIV_eur":max(cell_tiv.values()),
        "source_HU_GFK_function_count":len(gfkrows),
        "sites_with_wind_material_roof_vulnerability_mapped":0,
        "sites_with_actual_C3S_footprint_guessed_gust_values":0,
        "source_C3S_NetCDF_provider_bytes_verified":False,
        "year_period_event_frequency_known":False,
        "insurance_policy_limits_deductibles_or_RI_observed":False,
        "observed_RV_insured_geographies_or_values":False,
        "native_Germany_GUL_IL_RI_OEP_AEP_executed":False,
        "GFK_function_taxonomy_is_not_a_valid_wind_vulnerability_mapping":True,
    }
    return {"summary":summary,"cell_rows":cellrows,"gfk_rows":gfkrows}


def write_report(out:Path,study:dict)->dict:
    if out.exists() or not out.parent.is_dir():
        raise CoverageBlocked("fresh exact output path required")
    summary=dict(study["summary"])
    cell_bytes=_csv(study["cell_rows"],CELL_FIELDS)
    gfk_bytes=_csv(study["gfk_rows"],GFK_FIELDS)
    summary["output_sha256"]={
        "invented_grid_cell_exposure.csv":hashlib.sha256(cell_bytes).hexdigest(),
        "unknown_wind_taxonomy_exposure.csv":hashlib.sha256(gfk_bytes).hexdigest()
    }
    try:
        with zipfile.ZipFile(out,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            z.writestr("invented_grid_cell_exposure.csv",cell_bytes)
            z.writestr("unknown_wind_taxonomy_exposure.csv",gfk_bytes)
            z.writestr("summary.json",json.dumps(summary,sort_keys=True,indent=2)+"\n")
    except Exception:
        out.unlink(missing_ok=True)
        raise
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_10k_nextgen_handoff_zip",type=Path)
    p.add_argument("new_report_zip",type=Path)
    args=p.parse_args()
    try:
        print(json.dumps(write_report(args.new_report_zip,audit(args.original_10k_nextgen_handoff_zip)),
                         sort_keys=True,indent=2))
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        p.exit(2,"NRW_WIND_COVERAGE_BLOCKED: "+str(exc)+"\n")
    return 0

if __name__=="__main__":
    sys.exit(main())
