# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verified original CLIMK–WINDS ERA5 v2 -> single-event Oasis hazard tile.

Research only: exact Zenodo 6,792,278-byte source or matching local original,
one indexed storm, up to 10,000 cells, no provider bytes committed. Does NOT
construct annual event probabilities, vulnerability or insured/reinsured losses.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_runners.wisc_netcdf_oasis_tile_v0 import (
    WiscTileError, bins_from_text, csv_content, number, strict_vector,
    MAX_TILE_CELLS,
)
from scripts.inspect_climk_winds_era5_v0 import (
    EXPECTED_DIMENSIONS, EXPECTED_FIELDS, PINNED_SHA256,
    PUBLISHED_SIZE, SOURCE_NAME, SOURCE_URL,
    verify_source_bytes, fetch_provider_bytes,
)

PROFILE = "climk-era5-v2-native-original-oasis-hazard-tile-v0"
BINS = "0,10,20,30,40,50,60,80,120,200"

class ClimkOasisError(ValueError):
    """Original provider identity or hazard support is not established."""


def _label(value: object, field: str) -> str:
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeError as exc:
            raise ClimkOasisError(f"{field} is not UTF-8") from exc
    if not isinstance(value, str) or not 0 < len(value) <= 120 or value != value.strip() or not value.isprintable():
        raise ClimkOasisError(f"{field} is missing, ambiguous or unbounded")
    return value


def build_tile(
    *,
    original_sha256: str,
    source_storm_index: int,
    storm_name: str,
    storm_date_label: str,
    latitudes: list[object],
    longitudes: list[object],
    gust_tile: list[list[object]],
    row_start: int,
    col_start: int,
    edges: list[Decimal],
) -> tuple[dict[str, bytes], dict[str, object]]:
    if original_sha256 != PINNED_SHA256:
        raise ClimkOasisError("not the pinned original CLIMK v2 ERA5 source")
    if type(source_storm_index) is not int or not 0 <= source_storm_index < 50:
        raise ClimkOasisError("storm index must be original zero-based 0..49")
    storm_name = _label(storm_name, "Storm_Names")
    storm_date_label = _label(storm_date_label, "Storm_Dates")
    if type(row_start) is not int or type(col_start) is not int or min(row_start, col_start) < 0:
        raise ClimkOasisError("invalid grid starting offset")
    if type(edges) is not list or len(edges) < 2 or not all(type(x) is Decimal for x in edges):
        raise ClimkOasisError("exact increasing decimal intensity bins required")
    if edges[0] != 0 or any(not x.is_finite() or x < 0 or x > 200 for x in edges) or any(b <= a for a, b in zip(edges,edges[1:])):
        raise ClimkOasisError("invalid intensity bin support")
    lat = strict_vector(latitudes, "latitude", -90, 90)
    lon = strict_vector(longitudes, "longitude", -180, 180)
    if (len(lat), len(lon)) != (181, 269):
        raise ClimkOasisError("not the pinned original 181x269 native ERA5 grid")
    if type(gust_tile) is not list or not gust_tile or any(type(row) is not list for row in gust_tile):
        raise ClimkOasisError("native gust tile missing")
    height,width = len(gust_tile), len(gust_tile[0])
    if width < 1 or height * width > MAX_TILE_CELLS or any(len(row)!=width for row in gust_tile):
        raise ClimkOasisError("unbounded or ragged gust tile")
    if row_start+height>len(lat) or col_start+width>len(lon):
        raise ClimkOasisError("tile exceeds original source grid")
    from bisect import bisect_right
    cells: list[list[object]] = []
    area: list[list[object]] = []
    missing=0
    event_id=source_storm_index+1
    for i,row in enumerate(gust_tile):
        for j,v in enumerate(row):
            if v is None or (type(v) is float and math.isnan(v)):
                missing += 1
                continue
            try:
                gust=number(v,"CLIMK original 10m max gust m/s",minimum=0,maximum=200)
            except WiscTileError as exc:
                raise ClimkOasisError(str(exc)) from exc
            value=Decimal(str(gust))
            if value>edges[-1]:
                raise ClimkOasisError("real wind gust outside declared intensity bins; no clipping")
            bin_id=min(bisect_right(edges,value),len(edges)-1)
            if bin_id<1:
                raise ClimkOasisError("gust outside all intensity bins")
            rr=row_start+i; cc=col_start+j
            area_peril=rr*269+cc+1
            cells.append([event_id,area_peril,bin_id,"1.0"])
            area.append([area_peril,repr(lat[rr]),repr(lon[cc]),rr,cc])
    if not cells:
        raise ClimkOasisError("source gust tile has no observed wind data")
    binrows=[
        [k,str(lo),str(hi),str((lo+hi)/2),1]
        for k,(lo,hi) in enumerate(zip(edges,edges[1:]),start=1)
    ]
    outputs={
        "events.csv":csv_content("events.csv",[[event_id]]),
        "footprint.csv":csv_content("footprint.csv",cells),
        "intensity_bin_dict.csv":csv_content("intensity_bin_dict.csv",binrows),
        "areaperil_dict.csv":csv_content("areaperil_dict.csv",area),
    }
    receipt={
        "profile":PROFILE,
        "status":"original_provider_bytes_verified_and_hazard_tile_derived_not_model_run",
        "publisher_record":"https://zenodo.org/records/15305753",
        "source_url":SOURCE_URL,
        "source_filename":SOURCE_NAME,
        "original_bytes_verified":PUBLISHED_SIZE,
        "original_sha256_verified":original_sha256,
        "storm_index_zero_based":source_storm_index,
        "local_experiment_event_id":event_id,
        "original_storm_name":storm_name,
        "original_storm_date_label":storm_date_label,
        "original_storm_date_label_not_trusted_annual_period":True,
        "original_event_count":50,
        "original_event_sample_extremes_only":True,
        "source_cross_model_independence_proven":False,
        "gust_variable":"absolute_maxwindgusts",
        "gust_units":"m s**-1",
        "wind_speed_m_s_at_source_native_grid":True,
        "grid_shape":[len(lat),len(lon)],
        "tile":{"row_start":row_start,"col_start":col_start,"height":height,"width":width},
        "tile_centroid_is_not_full_cell_polygon":True,
        "valid_gust_cells":len(cells),
        "unknown_weather_cells":missing,
        "one_conditional_wind_bin_per_valid_cell":True,
        "output_files":{k:{"sha256":hashlib.sha256(v).hexdigest(),"bytes":len(v)} for k,v in sorted(outputs.items())},
        "annual_oep_aep_authorized":False,
        "original_source_year_universe_complete":False,
        "reinsurance_financial_terms_verified":False,
        "source_hazard_calibration_and_vulnerability_verified":False,
        "real_insurer_exposure_or_damage_verified":False,
        "native_oasis_full_model_run_verified":False,
        "external_provider_bytes_committed":False,
    }
    return outputs,receipt


def source_to_tile(
    source: bytes, *, storm_index: int, row_start: int, col_start: int,
    height: int, width: int, edges: list[Decimal],
) -> tuple[dict[str,bytes],dict[str,object]]:
    from netCDF4 import Dataset
    import numpy as np
    evidence=verify_source_bytes(source,require_sha256=True)
    if type(storm_index) is not int or not 0<=storm_index<50:
        raise ClimkOasisError("storm index outside original 50 selections")
    if type(row_start) is not int or type(col_start) is not int or min(row_start,col_start)<0:
        raise ClimkOasisError("tile start must be nonnegative integers")
    if type(height) is not int or type(width) is not int or not 1<=height*width<=MAX_TILE_CELLS or min(height,width)<1:
        raise ClimkOasisError("tile dimensions outside bounded range")
    if row_start+height>181 or col_start+width>269:
        raise ClimkOasisError("tile exceeds frozen original grid")
    try:
        with Dataset("climk-v2-era5-native",mode="r",memory=source) as ds:
            if {k:len(v) for k,v in ds.dimensions.items()}!=EXPECTED_DIMENSIONS:
                raise ClimkOasisError("original NetCDF dimensions changed")
            for name,(dims,unit) in EXPECTED_FIELDS.items():
                if name not in ds.variables:
                    raise ClimkOasisError("missing mandatory original scientific variable")
                field=ds.variables[name]
                if field.dimensions!=dims or str(getattr(field,"units",""))!=unit:
                    raise ClimkOasisError(f"original variable axes or scientific units changed: {name}")
            wind=ds.variables["absolute_maxwindgusts"]
            lat=ds.variables["latitude"][:].tolist()
            lon=ds.variables["longitude"][:].tolist()
            name=_label(ds.variables["Storm_Names"][storm_index],"Storm_Names")
            label=_label(ds.variables["Storm_Dates"][storm_index],"Storm_Dates")
            tile=np.ma.asarray(wind[storm_index,row_start:row_start+height,
                                       col_start:col_start+width],dtype=float)
            # Masked values are unknown hazard. MaskedArray.tolist() preserves None.
            arr=tile.tolist()
            if height==1 and width==1 and not isinstance(arr,list):
                arr=[[arr]]
            elif height==1 and (not isinstance(arr,list) or (arr and not isinstance(arr[0],list))):
                arr=[arr]
    except ClimkOasisError:
        raise
    except (OSError,KeyError,IndexError,TypeError,ValueError,AttributeError) as exc:
        raise ClimkOasisError("original source NetCDF array extraction failed") from exc
    return build_tile(original_sha256=evidence["sha256_observed"],
                      source_storm_index=storm_index,storm_name=name,
                      storm_date_label=label,latitudes=lat,longitudes=lon,
                      gust_tile=arr,row_start=row_start,col_start=col_start,edges=edges)


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    inp=parser.add_mutually_exclusive_group(required=True)
    inp.add_argument("--fetch-original",action="store_true")
    inp.add_argument("--source-file",type=Path)
    parser.add_argument("--storm-index",type=int,default=0)
    parser.add_argument("--row-start",type=int,default=90)
    parser.add_argument("--col-start",type=int,default=130)
    parser.add_argument("--height",type=int,default=2)
    parser.add_argument("--width",type=int,default=3)
    parser.add_argument("--bin-edges",default=BINS)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink() or not args.out.parent.is_dir():
            raise ClimkOasisError("output must be a new folder under existing parent")
        if args.source_file is not None:
            if not args.source_file.is_file() or args.source_file.is_symlink():
                raise ClimkOasisError("source must be regular local original file")
            if args.source_file.stat().st_size!=PUBLISHED_SIZE:
                raise ClimkOasisError("original source file size changed")
            source=args.source_file.read_bytes()
        else:
            source=fetch_provider_bytes()
        files,receipt=source_to_tile(source,storm_index=args.storm_index,
            row_start=args.row_start,col_start=args.col_start,
            height=args.height,width=args.width,edges=bins_from_text(args.bin_edges))
        args.out.mkdir()
        for filename,body in sorted(files.items()):
            (args.out/filename).write_bytes(body)
        (args.out/"research_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        print(json.dumps(receipt,sort_keys=True))
        return 0
    except (ClimkOasisError,WiscTileError,OSError,ValueError) as exc:
        print(json.dumps({"status":"blocked","reason":str(exc)},sort_keys=True),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
