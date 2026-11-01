#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One bounded 250m Luxembourg city MNT/MNS COG source-height proxy experiment.

Original file URLs are fixed and publisher-hosted, both verified to support
HTTP Range/BigTIFF first 4KiB in merged #945. Only one raster band and a small
native EPSG2169 window may be read, no whole 40GB TIFF or LAZ download.
DSM-MNT contains *trees and nonbuilding objects*: never call it building height.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    FILES, OFFICIAL_BASE, read_header_range,
)

CENTER_LON, CENTER_LAT = 6.1319, 49.6116
HALF_WIDTH_METRES = 125.0
MAX_WINDOW_PIXELS = 1_000_000
EXPECTED_EPSG = 2169
EXPECTED_RESOLUTION = 0.5


class CogWindowError(ValueError):
    pass


def native_bbox():
    """Match exact 250m equal-area city-center study footprint from #924."""
    from pyproj import Transformer
    proj = Transformer.from_crs(4326, 3035, always_xy=True)
    native = Transformer.from_crs(3035, EXPECTED_EPSG, always_xy=True)
    cx, cy = proj.transform(CENTER_LON, CENTER_LAT)
    points = [native.transform(x,y) for x,y in (
        (cx-HALF_WIDTH_METRES,cy-HALF_WIDTH_METRES),
        (cx+HALF_WIDTH_METRES,cy-HALF_WIDTH_METRES),
        (cx+HALF_WIDTH_METRES,cy+HALF_WIDTH_METRES),
        (cx-HALF_WIDTH_METRES,cy+HALF_WIDTH_METRES),
    )]
    if not all(math.isfinite(q) for p in points for q in p):
        raise CogWindowError("Nonfinite official city study-area transform")
    return min(x for x,y in points), min(y for x,y in points), max(x for x,y in points), max(y for x,y in points)


def bounded_window_from_source(source, bbox):
    """Return a strict <=1M-pixel original COG read window."""
    import rasterio
    from rasterio.windows import from_bounds
    if source.crs is None or source.crs.to_epsg() != EXPECTED_EPSG:
        raise CogWindowError("Official source raster CRS differs from declared EPSG2169")
    if source.count != 1 or source.transform.b != 0 or source.transform.d != 0:
        raise CogWindowError("Unexpected non-north-up/non-singleband raster")
    xsize,ysize=source.res
    if not (0.49 <= xsize <= 0.51 and 0.49 <= ysize <= 0.51):
        raise CogWindowError("Raster pixel resolution differs from official 50cm")
    xmin,ymin,xmax,ymax=bbox
    if not (source.bounds.left <= xmin < xmax <= source.bounds.right
            and source.bounds.bottom <= ymin < ymax <= source.bounds.top):
        raise CogWindowError("Study-area extent outside official original raster")
    window=from_bounds(xmin,ymin,xmax,ymax,transform=source.transform)
    start_col=math.floor(window.col_off)
    start_row=math.floor(window.row_off)
    end_col=math.ceil(window.col_off+window.width)
    end_row=math.ceil(window.row_off+window.height)
    width,height=end_col-start_col,end_row-start_row
    if (width<=0 or height<=0 or width>1024 or height>1024
            or width*height > MAX_WINDOW_PIXELS):
        raise CogWindowError("Unbounded or invalid original COG window pixel count")
    if (start_col<0 or start_row<0
            or end_col>source.width or end_row>source.height):
        raise CogWindowError("Original window would require boundless extrapolation")
    return rasterio.windows.Window(start_col,start_row,width,height)


def compute_proxy(dtm, dsm) -> dict:
    """Compute joint valid-pixel DSM-DTM distribution without building identity."""
    import numpy as np
    if dtm.shape != dsm.shape or dtm.ndim != 2 or dtm.size > MAX_WINDOW_PIXELS:
        raise CogWindowError("Original sources have incompatible window dimensions")
    good=(~np.ma.getmaskarray(dtm)) & (~np.ma.getmaskarray(dsm))
    a=np.asarray(dtm.data,dtype=np.float64)
    b=np.asarray(dsm.data,dtype=np.float64)
    good &= np.isfinite(a) & np.isfinite(b) & (a>=-1000) & (a<=4000) & (b>=-1000) & (b<=4000)
    valid=int(np.count_nonzero(good))
    if valid == 0 or valid < dtm.size//2:
        raise CogWindowError("Original source valid data coverage insufficient")
    heights=(b-a)[good]
    if np.any(np.abs(heights)>200):
        raise CogWindowError("Nonphysical/uncalibrated original surface-terrain difference")
    # Negative MNS-MNT differences can arise from sampling artifacts; retain
    # them as-is, never clip/pretend all pixels correspond to a building.
    return {
        "pixels_in_both_original_source_windows": int(dtm.size),
        "valid_joint_pixels": valid,
        "valid_fraction_rounded_6dp": round(float(valid/dtm.size),6),
        "surface_minus_terrain_min_metres": round(float(np.min(heights)),3),
        "surface_minus_terrain_median_metres": round(float(np.median(heights)),3),
        "surface_minus_terrain_p90_metres": round(float(np.quantile(heights,0.9)),3),
        "surface_minus_terrain_max_metres": round(float(np.max(heights)),3),
        "fraction_valid_pixels_above_3m_rounded_6dp": round(float(np.mean(heights>3.0)),6),
    }


def run_live() -> dict:
    try:
        import rasterio
        import numpy as np
    except ImportError as exc:
        raise CogWindowError("Pinned optional Rasterio/Numpy/PyProj runtime required") from exc
    # No GDAL until exact official original source range gates succeed.
    sources={name:read_header_range(name) for name in ("MNT","MNS")}
    bbox=native_bbox()
    # Strict remote VSI: never enumerate neighbouring directories or cache big
    # provider datasets; only requested band/window is ever read by this code.
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        CPL_VSIL_CURL_CHUNK_SIZE="65536",
        CPL_VSIL_CURL_CACHE_SIZE="1048576",
        GDAL_HTTP_MAX_RETRY="0",
        GDAL_HTTP_TIMEOUT="20",
        GDAL_CACHEMAX="8",
        VSI_CACHE="FALSE",
    ):
        results={}
        for kind in ("MNT","MNS"):
            with rasterio.open("/vsicurl/"+OFFICIAL_BASE+FILES[kind]) as src:
                window=bounded_window_from_source(src,bbox)
                arr=src.read(1,window=window,masked=True,boundless=False)
                if arr.shape!=(window.height,window.width):
                    raise CogWindowError("Original partial raster payload shape drift")
                transform=src.window_transform(window)
                results[kind]={
                    "arr":arr, "transform":transform, "nodata_declared":src.nodata is not None,
                    "width":src.width,"height":src.height,
                    "window_rows":int(window.height),"window_columns":int(window.width),
                }
        first,second=results["MNT"],results["MNS"]
        if (first["arr"].shape!=second["arr"].shape
                or any(abs(x-y)>1e-6 for x,y in zip(first["transform"],second["transform"]))):
            raise CogWindowError("MNT/MNS original pixel grids misaligned; do not subtract pixels")
        dist=compute_proxy(first["arr"],second["arr"])
    return {
        "profile":"luxembourg-act-lidar2024-250m-original-bounded-cog-pixel-proxy-v0",
        "source_http_total_byte_sizes":{
            "MNT":sources["MNT"]["original_entire_file_bytes_declared_by_http"],
            "MNS":sources["MNS"]["original_entire_file_bytes_declared_by_http"]
        },
        "source_full_file_hashes_verified":False,
        "native_epsg":EXPECTED_EPSG,
        "native_raster_resolution_metres":EXPECTED_RESOLUTION,
        "study_window":"public Luxembourg city 250x250m equal-area reference; native raster bounding envelope",
        "source_raster_dimensions_only":{
            kind:{"rows":r["height"],"columns":r["width"],"nodata_declared":r["nodata_declared"]}
            for kind,r in results.items()
        },
        **dist,
        "tree_vegetation_and_nonbuilding_pixels_included":True,
        "per_building_heights_validated":False,
        "survey_vertical_datum_independently_verified":False,
        "model_input_admitted":False,
        "original_pixel_values_exported":False,
        "full_original_tiffs_downloaded":False,
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-luxembourg-window",action="store_true",required=True)
    parser.parse_args(argv)
    try:
        print(json.dumps(run_live(),sort_keys=True,indent=2,allow_nan=False))
    except (CogWindowError,OSError,ValueError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
