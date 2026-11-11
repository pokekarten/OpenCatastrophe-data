# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative 10k original NRW HU WGS84 OED -> NextGen C3S spatial handoff.

Compatible with the named crosswalk fields of NextGen research/
c3s_wind_footprint_stage_v0.py; NOT a complete C3S conditional loss call:
no official C3S NetCDF source cells, gust field, real wind VLT, event/year
frequency or carrier policy/RI. Grid input MUST be explicitly labelled a
fabricated spatial fixture, so no synthetic coordinate-grid alignment can
be mistaken for provider authenticated model geography.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tomllib
import zipfile

from rva_nrw_hu_gfk_residential_candidate_v0 import classify_gfk

SOURCE_SHA = "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
SOURCE_SCHEMA = "RVA_NRW_2022_HU_STRATIFIED_PHYSICAL_CANDIDATES_GEO_OED_V0"
GRID_SCHEMA = "RVA_NRW_SYNTHETIC_ERA5_STYLE_GRID_DEMO_NOT_SOURCE_C3S_V0"
OUTPUT_SCHEMA = "RVA_NRW_SOURCE_GEO_TO_NEXTGEN_UNADMITTED_C3S_GRID_V0"
SITES = 10000
COUNTIES = 53
FILES = {"location.csv", "account.csv", "physical_candidate_evidence.csv", "manifest.json"}
NEXTGEN_KEYS = {"asset_id", "cedant_id", "country_iso2", "taxonomy",
                "lon_e6", "lat_e6", "col", "row", "cell_id"}
NEXTGEN_GRID_KEYS = {"grid_id", "west_lon_e6", "south_lat_e6", "width_e6",
                     "height_e6", "num_lon", "num_lat", "crs"}

class CrosswalkBlocked(ValueError):
    pass


def _read_csv(z:zipfile.ZipFile,name:str)->list[dict]:
    blob=z.read(name)
    if len(blob)>12_000_000:
        raise CrosswalkBlocked("bounded OED data exceeds source byte budget")
    text=io.StringIO(blob.decode("utf-8"),newline="")
    reader=csv.DictReader(text)
    if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
        raise CrosswalkBlocked("missing or duplicate original CSV headers")
    out=list(reader)
    return out


def _source(z:zipfile.ZipFile,expected_sites:int,expected_counties:int):
    if set(z.namelist())!=FILES or z.testzip() is not None:
        raise CrosswalkBlocked("unexpected source OED members or archive CRC mismatch")
    info=json.loads(z.read("manifest.json"))
    if (info.get("schema")!=SOURCE_SCHEMA
        or info.get("status")!="GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED"
        or info.get("source_original_2022_HU_complete_archive_SHA256")!=SOURCE_SHA
        or info.get("source_original_2022_HU_full_CRCs_verified") is not True
        or info.get("physical_building_candidates_selected")!=expected_sites
        or info.get("fictional_policy_count")!=expected_sites
        or info.get("real_source_counties_represented")!=expected_counties
        or info.get("model_input_approved") is not False
        or info.get("physical_building_footprints_are_actual_RV_insured_sites") is not False
        or info.get("insurer_building_TIV_observed") is not False):
        raise CrosswalkBlocked("full original source provenance or scientific admission changed")
    listed=info.get("output_file_SHA256",{})
    for file in FILES-{"manifest.json"}:
        if not isinstance(listed,dict) or hashlib.sha256(z.read(file)).hexdigest()!=listed.get(file):
            raise CrosswalkBlocked("source file SHA-256 mismatch: "+file)
    loc=_read_csv(z,"location.csv")
    accounts=_read_csv(z,"account.csv")
    physical=_read_csv(z,"physical_candidate_evidence.csv")
    if len(loc)!=expected_sites or len(accounts)!=expected_sites or len(physical)!=expected_sites:
        raise CrosswalkBlocked("source 10k population count inconsistent")
    aids=[r.get("LocNumber") for r in loc]
    rids=[r.get("AccNumber") for r in accounts]
    eids=[r.get("LocNumber") for r in physical]
    if (len(set(aids))!=expected_sites or len(set(rids))!=expected_sites
        or len(set(eids))!=expected_sites or set(aids)!=set(rids) or set(aids)!=set(eids)
        or len({r.get("SourceOiSHA256") for r in physical})!=expected_sites):
        raise CrosswalkBlocked("duplicate or missing physical/policy crosswalk")
    return loc,{r["LocNumber"]:r for r in physical},info


def _grid(spec:dict)->dict:
    if not isinstance(spec,dict) or set(spec)!={"schema","spatial_status","grid"}:
        raise CrosswalkBlocked("exact demo grid wrapper required")
    if (spec["schema"]!=GRID_SCHEMA
        or spec["spatial_status"]!="INVENTED_RECTANGULAR_GRID_NOT_AUTHENTICATED_C3S"):
        raise CrosswalkBlocked("actual C3S field requires independent extractor and admission")
    grid=spec["grid"]
    if not isinstance(grid,dict) or set(grid)!=NEXTGEN_GRID_KEYS or grid["crs"]!="EPSG:4326":
        raise CrosswalkBlocked("NextGen grid schema or CRS mismatch")
    if (not isinstance(grid["grid_id"],str) or not grid["grid_id"].startswith("SYNTH-NRW-")
        or len(grid["grid_id"])>128):
        raise CrosswalkBlocked("grid must remain explicitly synthetic")
    for k in ("west_lon_e6","south_lat_e6","width_e6","height_e6","num_lon","num_lat"):
        if type(grid[k]) is not int:
            raise CrosswalkBlocked("integer microdegree grid values required")
    if (grid["width_e6"]!=250000 or grid["height_e6"]!=250000
        or not 1<=grid["num_lon"]<=64 or not 1<=grid["num_lat"]<=64
        or grid["num_lon"]*grid["num_lat"]>4096
        or not -180_000_000<=grid["west_lon_e6"]<180_000_000
        or not -90_000_000<=grid["south_lat_e6"]<90_000_000
        or grid["west_lon_e6"]+grid["num_lon"]*250000>180_000_000
        or grid["south_lat_e6"]+grid["num_lat"]*250000>90_000_000):
        raise CrosswalkBlocked("unsupported rectangular 0.25-degree research grid")
    return grid


def _coordinate(raw:str,minimum:int,maximum:int)->tuple[int,Decimal]:
    try:
        number=Decimal(raw)
        original=number*1_000_000
        e6=int(original.to_integral_value(rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError,TypeError) as exc:
        raise CrosswalkBlocked("original OED location nonnumeric") from exc
    if not original.is_finite() or not minimum<original<maximum:
        raise CrosswalkBlocked("public physical WGS84 coordinates outside region")
    if abs(original-Decimal(e6))>Decimal("0.5"):
        raise CrosswalkBlocked("microdegree rounding exceeds half-unit")
    return e6,original


def _cell(orig:Decimal,rounded:int,start:int,step:int,n:int)->int:
    # Recompute exact cell index using the source's seven-decimal physical
    # coordinate; reject the numerical half-microdegree ambiguity at a boundary.
    x=int((orig-Decimal(start))//Decimal(step))
    y=(rounded-start)//step
    if x!=y or not 0<=x<n:
        raise CrosswalkBlocked("source physical site falls outside or on ambiguous grid boundary")
    if min(orig-(start+x*step), (start+(x+1)*step)-orig)<=Decimal("0.5"):
        raise CrosswalkBlocked("source physical coordinate too close to grid boundary")
    return x


def build(zippath:Path,grid_spec:dict,*,expected_sites:int=SITES,expected_counties:int=COUNTIES)->dict:
    if (type(expected_sites) is not int or not 1<=expected_sites<=10000
        or type(expected_counties) is not int or not 1<=expected_counties<=53):
        raise CrosswalkBlocked("bounded source-population expectations required")
    if zippath.is_symlink() or not zippath.is_file() or zippath.stat().st_size>50_000_000:
        raise CrosswalkBlocked("explicit bounded existing original-derived OED artifact required")
    g=_grid(grid_spec)
    with zipfile.ZipFile(zippath) as z:
        locations,physical,src=_source(z,expected_sites,expected_counties)
    allocations=[]
    values=[]
    per_cell=Counter()
    per_county=Counter()
    per_gfk=Counter()
    total=0
    for r in locations:
        ident=r["LocNumber"]
        evidence=physical[ident]
        source_gfk=evidence.get("SourceGFK","")
        if (r.get("AccNumber")!=ident
            or r.get("CountryCode")!="DE" or r.get("LocPerilsCovered")!="WW2"
            or r.get("OEDVersion")!="5.0.0"
            or evidence.get("SourcePhysicalCandidateNotInsuredSite")!="true"
            or evidence.get("KreisAGS2022")!="".join(r.get("LocGroup","").split("KREIS-"))
            or classify_gfk(source_gfk)[0]!="residential_function_candidate_only"):
            raise CrosswalkBlocked("source OED/GFK/counties or insurer nonadmission inconsistent")
        try:
            amount=int(r["BuildingTIV"])
        except (ValueError,TypeError) as exc:
            raise CrosswalkBlocked("fictional TIV not an integer") from exc
        if not 1<=amount<=500_000_000 or str(amount)!=r["BuildingTIV"]:
            raise CrosswalkBlocked("source BuildingTIV lacks bounded exact EUR value")
        x_raw,x_original=_coordinate(r["Longitude"],5_000_000,10_500_000)
        y_raw,y_original=_coordinate(r["Latitude"],49_500_000,53_000_000)
        col=_cell(x_original,x_raw,g["west_lon_e6"],g["width_e6"],g["num_lon"])
        row=_cell(y_original,y_raw,g["south_lat_e6"],g["height_e6"],g["num_lat"])
        cell=f"{g['grid_id']}:x{col:05d}:y{row:05d}"
        assignment={
            "asset_id":ident,
            "cedant_id":"FICTITIOUS_RVA_LIKE_NRW_NOT_OBSERVED",
            "country_iso2":"DE",
            # The historical HU building function is NOT masonry/light,
            # material/roof/specific physical damage vulnerability class.
            "taxonomy":"UNMAPPED_HU22_GFK_"+source_gfk,
            "lon_e6":x_raw,"lat_e6":y_raw,
            "col":col,"row":row,"cell_id":cell,
        }
        if set(assignment)!=NEXTGEN_KEYS:
            raise CrosswalkBlocked("NextGen contract field drift")
        allocations.append(assignment)
        values.append({"asset_id":ident,"replacement_cost_eur":amount})
        per_cell[cell]+=1
        per_county[r["LocGroup"][6:]]+=1
        per_gfk[source_gfk]+=1
        total+=amount
    if (len(per_county)!=expected_counties or len(allocations)!=expected_sites
        or len({x["asset_id"] for x in allocations})!=expected_sites
        or sum(per_cell.values())!=expected_sites):
        raise CrosswalkBlocked("NextGen C3S spatial crosswalk or county support drift")
    allocations.sort(key=lambda a:a["asset_id"])
    values.sort(key=lambda a:a["asset_id"])
    handoff={"grid":g,"crosswalk_assignments":allocations,"insured_asset_values":values}
    receipt={
        "schema":OUTPUT_SCHEMA,
        "status":"SPATIAL_CROSSWALK_SHAPE_ONLY_NO_ADMITTED_C3S_MODEL",
        "source_original_HU_2022_full_SHA256":SOURCE_SHA,
        "source_OED_zip_SHA256":hashlib.sha256(zippath.read_bytes()).hexdigest(),
        "source_physical_synthetic_OED_count":expected_sites,
        "original_NRW_counties":expected_counties,
        "source_2022_HU_building_functions_are_not_2025_RV_insured_occupancy":True,
        "fictional_cedant_not_actual_RV_observed":True,
        "insurer_TIV_observed":False,
        "synthetic_source_building_TIV_eur":total,
        "grid_is_fictional_not_C3S_NetCDF":True,
        "actual_C3S_NetCDF_original_bytes_authenticated":False,
        "physical_wind_gust_grid_provided":False,
        "source_specific_wind_vulnerability_taxonomy_mapped":False,
        "wind_damage_probability_law_supplied":False,
        "event_year_frequency_and_period_weights_verified":False,
        "gross_insured_net_reinsurance_or_EP_executed":False,
        "NextGen_staged_C3S_signature_only":True,
        "counts_by_demo_grid_cell":dict(sorted(per_cell.items())),
        "counts_by_real_source_Kreis":dict(sorted(per_county.items())),
        "physical_GFK_candidate_counts":dict(sorted(per_gfk.items())),
    }
    return {"handoff":handoff,"receipt":receipt}


def write_zip(result:dict,out:Path)->dict:
    if out.exists() or not out.parent.is_dir():
        raise CrosswalkBlocked("fresh output ZIP path required")
    payload=json.dumps(result["handoff"],sort_keys=True,ensure_ascii=True,separators=(",",":"),allow_nan=False).encode()
    receipt=dict(result["receipt"])
    receipt["handoff_json_sha256"]=hashlib.sha256(payload).hexdigest()
    try:
        with zipfile.ZipFile(out,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
            z.writestr("nextgen_c3s_spatial_handoff.json",payload)
            z.writestr("source_boundary_receipt.json",json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    except Exception:
        out.unlink(missing_ok=True)
        raise
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_geocoded_nrw_oed_zip",type=Path)
    parser.add_argument("synthetic_c3s_grid_fixture_toml",type=Path)
    parser.add_argument("output_zip",type=Path)
    args=parser.parse_args()
    try:
        if args.synthetic_c3s_grid_fixture_toml.stat().st_size>16384:
            raise CrosswalkBlocked("bounded explicit SPDX-tagged demo TOML required")
        grid=tomllib.loads(args.synthetic_c3s_grid_fixture_toml.read_text(encoding="utf-8"))
        receipt=write_zip(build(args.source_geocoded_nrw_oed_zip,grid),args.output_zip)
        print(json.dumps({k:receipt[k] for k in ("schema","status","source_physical_synthetic_OED_count",
            "original_NRW_counties","synthetic_source_building_TIV_eur",
            "actual_C3S_NetCDF_original_bytes_authenticated","gross_insured_net_reinsurance_or_EP_executed",
            "handoff_json_sha256")},sort_keys=True))
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        parser.exit(2,"NRW_C3S_SPATIAL_ONLY_BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    sys.exit(main())
