#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict source-pinned research: 1m inward polygon sensitivity of LiDAR proxy.

The ORIGINAL 2026 building shapes are clipped to the exact public Luxembourg
100m study area. Shared-polygon pixels are permanently excluded from *both*
the baseline and inset cohorts; shrinking cannot make shared pixels eligible.
Only aggregate results leave the process: no original IDs, polygon geometries,
raster samples or source-specific height medians.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

from research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 import (
    BANDS, BIN_NAMES, BuildingProxyError, GEOBASE_COUNT, GEOBASE_LAYER,
    GEOBASE_SHA, MAX_POLYGONS, MAX_RASTER_PIXELS, MIN_UNIQUE_VALID_PIXELS,
    aggregate, exact_area_candidates, original_window,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, sample as sample_gpkg,
)
from research_runners.luxembourg_lidar2024_bounded_cog_window_v0 import (
    CogWindowError, bounded_window_from_source,
)
from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    FILES, OFFICIAL_BASE, read_header_range,
)

INSET_METRES = 1.0
CHANGE_THRESHOLD_METRES = 2.0
EXPECTED_ORIGINAL_SAMPLE = 104
EXPECTED_BASELINE_ELIGIBLE = 97


def sensitivity(polygons, dtm, dsm, affine, roi, *, inset=INSET_METRES):
    """Return only aggregate stability statistics; no per-building output."""
    import numpy as np
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping

    if (not isinstance(polygons,list) or not 1<=len(polygons)<=MAX_POLYGONS
        or not isinstance(inset,(int,float)) or not math.isfinite(inset)
        or inset < 0.5 or inset > 2.0
        or dtm.ndim!=2 or dtm.shape!=dsm.shape
        or not 1<=dtm.size<=MAX_RASTER_PIXELS):
        raise BuildingProxyError("unbounded or invalid sensitivity inputs")
    # Reuse original analysis to apply its complete geometry, source coverage,
    # raster elevation and row-count safety gates.
    baseline=aggregate(polygons,dtm,dsm,affine,roi)
    clipped=[g.intersection(roi) for g in polygons]
    masks=[geometry_mask([mapping(g)],out_shape=dtm.shape,
                         transform=affine,invert=True,all_touched=False)
           for g in clipped]
    occupancy=np.zeros(dtm.shape,dtype=np.uint16)
    for mask in masks:
        occupancy+=mask.astype(np.uint16)
    shared=occupancy>1
    unshared=occupancy==1

    a=np.asarray(dtm.data,dtype=np.float64)
    b=np.asarray(dsm.data,dtype=np.float64)
    valid=(~np.ma.getmaskarray(dtm)) & (~np.ma.getmaskarray(dsm))
    valid &= (np.isfinite(a)&np.isfinite(b)
              &(a>=-1000)&(a<=4000)&(b>=-1000)&(b<=4000))
    diff=b-a
    if int(np.count_nonzero(shared))!=baseline["raster_pixel_occupancy"]["multiply_assigned_raster_pixels"]:
        raise BuildingProxyError("pixel-ambiguity accounting changed")
    if not np.isfinite(diff[valid]).all():
        raise BuildingProxyError("invalid original surface-terrain pixels")

    def score(mask):
        owned=mask & unshared
        possible=int(np.count_nonzero(owned))
        good=owned&valid
        available=int(np.count_nonzero(good))
        if available<MIN_UNIQUE_VALID_PIXELS or available*2<possible:
            return None
        median=float(np.median(diff[good]))
        return median if math.isfinite(median) and median>=0 else None

    old=[]
    inner=[]
    vanished=0
    for polygon,baseline_mask in zip(clipped,masks):
        old.append(score(baseline_mask))
        core=polygon.buffer(-float(inset),join_style=2)
        if core.is_empty or core.area<=0:
            vanished+=1
            inner.append(None)
            continue
        if not core.is_valid or core.geom_type not in ("Polygon","MultiPolygon"):
            raise BuildingProxyError("inward footprint geometry invalid")
        narrowed=geometry_mask([mapping(core)],out_shape=dtm.shape,
                               transform=affine,invert=True,all_touched=False)
        # The inset cannot reintroduce any original shared pixel. Also the
        # unchanged baseline unshared mask is required to prevent mask drift.
        if np.any(narrowed & ~baseline_mask):
            raise BuildingProxyError("inset leaked outside original footprint pixel mask")
        inner.append(score(narrowed))

    old_ok=sum(x is not None for x in old)
    inner_ok=sum(x is not None for x in inner)
    shared_ok=sum(x is not None and y is not None for x,y in zip(old,inner))
    lost=sum(x is not None and y is None for x,y in zip(old,inner))
    became=sum(x is None and y is not None for x,y in zip(old,inner))
    if (became!=0 or old_ok!=baseline["objects_with_bounded_raster_proxy"]
        or old_ok!=shared_ok+lost or inner_ok!=shared_ok):
        raise BuildingProxyError("baseline/inset comparability invariants violated")

    drift={"within_0_5m":0,"above_0_5_to_1m":0,
           "above_1_to_2m":0,"above_2m":0}
    bins={name:0 for name in BIN_NAMES}
    same_bin=0
    crossing=0

    def band(value):
        return next((i for i in range(len(BANDS)-1)
                     if BANDS[i]<=value<BANDS[i+1]),None)

    for before,after in zip(old,inner):
        if after is not None:
            index=band(after)
            if index is None:
                raise BuildingProxyError("inset proxy outside observed research bins")
            bins[BIN_NAMES[index]]+=1
        if before is None or after is None:
            continue
        delta=abs(after-before)
        if delta<=0.5:
            drift["within_0_5m"]+=1
        elif delta<=1.0:
            drift["above_0_5_to_1m"]+=1
        elif delta<=CHANGE_THRESHOLD_METRES:
            drift["above_1_to_2m"]+=1
        else:
            drift["above_2m"]+=1
        if band(before)==band(after):
            same_bin+=1
        else:
            crossing+=1

    if (sum(drift.values())!=shared_ok or same_bin+crossing!=shared_ok
        or sum(bins.values())!=inner_ok
        or sum(baseline["proxy_median_bins_metres_not_surveyed_heights"].values())!=old_ok):
        raise BuildingProxyError("sensitivity or bins fail conservation")
    return {
        "schema_version":"lu-2026-geobase-lidar2024-inner-footprint-sensitivity-v0",
        "source_polygons_in_fixed_study":len(polygons),
        "inward_offset_metres":float(inset),
        "baseline_eligible_objects":old_ok,
        "inset_eligible_objects":inner_ok,
        "baseline_eligible_lost_after_inset":lost,
        "previously_ineligible_becoming_eligible":became,
        "inset_empty_geometry_count":vanished,
        "both_eligible_objects":shared_ok,
        "absolute_inset_vs_baseline_proxy_median_drift_bands":drift,
        "same_proxy_median_height_band_both_eligible":same_bin,
        "proxy_median_band_changed_both_eligible":crossing,
        "baseline_proxy_median_bins_not_building_heights":
            baseline["proxy_median_bins_metres_not_surveyed_heights"],
        "inset_proxy_median_bins_not_building_heights":bins,
        "original_shared_raster_pixels_excluded_in_both":int(np.count_nonzero(shared)),
        "individual_building_id_or_proxy_exported":False,
        "surveyed_building_height_established":False,
        "vegetation_or_roof_ground_truth_removed":False,
        "original_source_rights_reviewed":False,
        "production_exposure_or_cat_model_admitted":False,
        "warning":(
            "Inward 1m polygon mask only tests sensitivity to footprint borders. "
            "The proxy still mixes canopy and other MNS surfaces, 2024 vs 2026 "
            "vintages, unverified CRS axis/vertical control and ACT shared source "
            "lineage. Source TIFF entire SHA is not verified."
        ),
    }


def run_original(geobase_path:Path):
    import rasterio
    from shapely.geometry import shape

    roi=original_window()
    meta,db=inspect_gpkg(geobase_path,expected_sha256=GEOBASE_SHA)
    try:
        layer=next((x for x in meta["layers"] if x["table"]==GEOBASE_LAYER),None)
        if layer is None or layer["feature_count"]!=GEOBASE_COUNT or layer["srs_id"]!=2169:
            raise BuildingProxyError("official full source population or CRS changed")
        with tempfile.TemporaryDirectory(prefix="oc-lu-lidar-inset-sensitivity-") as temp:
            tmp=Path(temp)/"source-sample.geojson"
            n=sample_gpkg(db,layer,id_field="BU_BuildingID",bbox=roi.bounds,
                          limit=MAX_POLYGONS,output=tmp)
            shapes=json.loads(tmp.read_text(encoding="utf-8"))
            candidates=[shape(feature["geometry"]) for feature in shapes["features"]]
            if len(candidates)!=n:
                raise BuildingProxyError("source RTree candidate count drifted")
            polygons=exact_area_candidates(candidates,roi)
            if len(polygons)!=EXPECTED_ORIGINAL_SAMPLE or n!=107:
                raise BuildingProxyError("frozen original 100m area footprint population drifted")
            receipts={name:read_header_range(name) for name in ("MNT","MNS")}
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                CPL_VSIL_CURL_CHUNK_SIZE="65536",
                CPL_VSIL_CURL_CACHE_SIZE="1048576",
                GDAL_HTTP_MAX_RETRY="0",GDAL_HTTP_TIMEOUT="20",
                GDAL_CACHEMAX=8,VSI_CACHE="FALSE",
            ):
                grids={}
                for name in ("MNT","MNS"):
                    with rasterio.open("/vsicurl/"+OFFICIAL_BASE+FILES[name]) as src:
                        window=bounded_window_from_source(src,roi.bounds)
                        values=src.read(1,window=window,masked=True,boundless=False)
                        if values.size>MAX_RASTER_PIXELS:
                            raise BuildingProxyError("source raster pixel budget exceeded")
                        grids[name]=(values,src.window_transform(window))
                a,ta=grids["MNT"]
                b,tb=grids["MNS"]
                if a.shape!=b.shape or any(abs(x-y)>1e-6 for x,y in zip(ta,tb)):
                    raise BuildingProxyError("original COG pixel grids misaligned")
                result=sensitivity(polygons,a,b,ta,roi)
                if (result["baseline_eligible_objects"]!=EXPECTED_BASELINE_ELIGIBLE
                    or result["baseline_proxy_median_bins_not_building_heights"]!={ 
                      "below_3m":0,"3_to_6m":2,"6_to_10m":5,
                      "10_to_15m":28,"15_to_25m":62,"25m_and_above":0,
                    }):
                    raise BuildingProxyError("original baseline PR957 proxy distribution drifted")
    finally:
        db.close()
    return {
        "geo_original_gpkg_sha256":GEOBASE_SHA,
        "lidar_public_range_prefixes_checked":True,
        "complete_lidar_source_sha256_verified":False,
        "approximate_same_100m_city_area_as_PR957":True,
        "source_bytes_and_footprint_individuals_persisted":False,
        **result,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geobase-gpkg",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        report=run_original(args.geobase_gpkg)
    except (BuildingProxyError,GeoPackageGateError,CogWindowError,OSError,ValueError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
