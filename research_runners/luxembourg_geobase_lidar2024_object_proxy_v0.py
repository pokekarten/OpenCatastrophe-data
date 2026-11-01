#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only aggregate 2026 GeoBase polygon × 2024 LiDAR MNS/MNT proxy.

Never output building IDs, geometries, pixels, or per-building proxy heights.
The proxy can include vegetation, non-roof objects and vertical datum drift.
No source licence approval, building identity or CAT source admission.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

from research_runners.luxembourg_geobase2026_eubucco_bounded_pair_v0 import (
    GEOBASE_SHA, GEOBASE_LAYER, GEOBASE_COUNT,
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

LON,LAT=6.1319,49.6116
HALFWIDTH_METRES=50.0
MAX_POLYGONS=400
MAX_RASTER_PIXELS=200_000
MIN_UNIQUE_VALID_PIXELS=8
BANDS=(0,3,6,10,15,25,float("inf"))
BIN_NAMES=("below_3m","3_to_6m","6_to_10m","10_to_15m",
           "15_to_25m","25m_and_above")


class BuildingProxyError(ValueError):
    """Original source or bounded spatial proxy not safely usable."""


def original_window():
    """Native CRS EPSG2169 four-corner polygon of predeclared equal-area 100m ROI."""
    from pyproj import Transformer
    from shapely.geometry import Polygon
    p=Transformer.from_crs(4326,3035,always_xy=True)
    t=Transformer.from_crs(3035,2169,always_xy=True)
    x,y=p.transform(LON,LAT)
    corners=[t.transform(a,b) for a,b in (
        (x-HALFWIDTH_METRES,y-HALFWIDTH_METRES),
        (x+HALFWIDTH_METRES,y-HALFWIDTH_METRES),
        (x+HALFWIDTH_METRES,y+HALFWIDTH_METRES),
        (x-HALFWIDTH_METRES,y+HALFWIDTH_METRES),
    )]
    geom=Polygon(corners)
    if not geom.is_valid or geom.area<=0 or not all(
        math.isfinite(q) for point in corners for q in point
    ):
        raise BuildingProxyError("invalid fixed equal-area source ROI")
    return geom


def aggregate(polygons, dtm, dsm, affine, study_polygon):
    """Two-pass raster masks exclude shared pixels before building-level medians.

    Return categorical counts ONLY. Actual within-polygon medians are never
    output or persisted, nor linked to original building identity.
    """
    import numpy as np
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping

    if (not isinstance(polygons,list) or not 1<=len(polygons)<=MAX_POLYGONS
        or dtm.ndim!=2 or dsm.shape!=dtm.shape
        or not 1<=dtm.size<=MAX_RASTER_PIXELS):
        raise BuildingProxyError("invalid sample size or original raster window")
    if not study_polygon.is_valid or study_polygon.area<=0:
        raise BuildingProxyError("invalid fixed research polygon")
    ground=np.asarray(dtm.data,dtype=np.float64)
    surface=np.asarray(dsm.data,dtype=np.float64)
    valid=(~np.ma.getmaskarray(dtm)) & (~np.ma.getmaskarray(dsm))
    valid &= (np.isfinite(ground) & np.isfinite(surface)
              & (ground>=-1000) & (ground<=4000)
              & (surface>=-1000) & (surface<=4000))
    diff=surface-ground
    if np.any(np.abs(diff[valid])>200):
        raise BuildingProxyError("original uncalibrated DSM-minus-DTM outlier")
    if np.count_nonzero(valid)<dtm.size//2:
        raise BuildingProxyError("raster source joint valid coverage insufficient")

    clipped=[]
    pixels=np.zeros(dtm.shape,dtype=np.uint16)
    for geom in polygons:
        if (geom.geom_type not in ("Polygon","MultiPolygon")
            or not geom.is_valid or geom.is_empty or geom.area<=0):
            raise BuildingProxyError("invalid source building footprint")
        g=geom.intersection(study_polygon)
        if g.is_empty or g.area<=0:
            raise BuildingProxyError("RTree candidate outside exact fixed ROI")
        if g.geom_type not in ("Polygon","MultiPolygon"):
            raise BuildingProxyError("degenerate geometry after region clipping")
        mask=geometry_mask([mapping(g)],out_shape=dtm.shape,
                           transform=affine,invert=True,all_touched=False)
        pixels+=mask.astype(np.uint16)
        clipped.append(g)
    occupancy={"unassigned_raster_pixels":int(np.count_nonzero(pixels==0)),
               "uniquely_assigned_raster_pixels":int(np.count_nonzero(pixels==1)),
               "multiply_assigned_raster_pixels":int(np.count_nonzero(pixels>1))}
    if sum(occupancy.values())!=dtm.size:
        raise BuildingProxyError("raster pixel occupancy not conserved")
    bins={k:0 for k in BIN_NAMES}
    eligible=0
    insufficient=0
    no_unique=0
    median_flags=0
    for g in clipped:
        mask=geometry_mask([mapping(g)],out_shape=dtm.shape,
                           transform=affine,invert=True,all_touched=False)
        unambiguous=mask & (pixels==1)
        available=int(np.count_nonzero(unambiguous))
        if not available:
            no_unique+=1
            continue
        usable=unambiguous & valid
        good=int(np.count_nonzero(usable))
        if good<MIN_UNIQUE_VALID_PIXELS or good*2<available:
            insufficient+=1
            continue
        median=float(np.median(diff[usable]))
        if not math.isfinite(median):
            raise BuildingProxyError("invalid polygon height-proxy median")
        if median<0:
            median_flags+=1
        pos=next((i for i in range(len(BANDS)-1)
                  if BANDS[i]<=median<BANDS[i+1]),None)
        if pos is None:
            # Under-zero medians are source quality anomalies, not zero heights.
            insufficient+=1
            continue
        bins[BIN_NAMES[pos]]+=1
        eligible+=1
    if eligible+insufficient+no_unique!=len(polygons):
        raise BuildingProxyError("source building count not conserved")
    if sum(bins.values())!=eligible:
        raise BuildingProxyError("height proxy bins not conserved")

    return {
        "original_building_polygons_in_study":len(polygons),
        "objects_with_bounded_raster_proxy":eligible,
        "objects_with_insufficient_unique_valid_pixels":insufficient,
        "objects_with_no_unique_raster_pixel":no_unique,
        "objects_with_negative_median_excluded":median_flags,
        "proxy_median_bins_metres_not_surveyed_heights":bins,
        "raster_pixel_occupancy":occupancy,
        "joint_source_valid_pixels":int(np.count_nonzero(valid)),
        "min_unique_valid_pixels_per_eligible_object":MIN_UNIQUE_VALID_PIXELS,
        "original_height_values_or_per_building_objects_exported":False,
        "building_heights_certified":False,
        "vegetation_separated":False,
        "overlap_pixels_double_counted":False,
        "original_source_rights_admitted":False,
        "cat_model_input_admitted":False,
    }


def run(geobase_path:Path):
    import numpy as np
    import rasterio
    from shapely.geometry import shape
    roi=original_window()
    bbox=roi.bounds
    original,db=inspect_gpkg(geobase_path,expected_sha256=GEOBASE_SHA)
    try:
        layer=next((x for x in original["layers"] if x["table"]==GEOBASE_LAYER),None)
        if (layer is None or layer["feature_count"]!=GEOBASE_COUNT
            or layer["srs_id"]!=2169):
            raise BuildingProxyError("source version or GeoBase original CRS drift")
        with tempfile.TemporaryDirectory(prefix="oc-lu-lidar-object-proxy-") as tmp:
            local=Path(tmp)/"sample-original.geojson"
            original_count=sample_gpkg(
                db,layer,id_field="BU_BuildingID",bbox=bbox,
                limit=MAX_POLYGONS,output=local,
            )
            sample=json.loads(local.read_text(encoding="utf-8"))
            rtree_candidates=[shape(x["geometry"]) for x in sample["features"]]
            if len(rtree_candidates)!=original_count:
                raise BuildingProxyError("sample length drift")
            # RTree searches the bounding rectangle of the projected 100m square.
            # A candidate intersecting only this bbox is NOT inside the study.
            # Clip against the exact study polygon before making height proxies.
            polygons=[g for g in rtree_candidates
                      if g.intersects(roi) and g.intersection(roi).area>0]
            if not polygons:
                raise BuildingProxyError("no positive-area building intersection in study")
            bbox_false_candidates=original_count-len(polygons)
            receipts={name:read_header_range(name) for name in ("MNT","MNS")}
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                CPL_VSIL_CURL_CHUNK_SIZE="65536",
                CPL_VSIL_CURL_CACHE_SIZE="1048576",
                GDAL_HTTP_MAX_RETRY="0", GDAL_HTTP_TIMEOUT="20",
                GDAL_CACHEMAX=8,VSI_CACHE="FALSE",
            ):
                sources={}
                for name in ("MNT","MNS"):
                    with rasterio.open("/vsicurl/"+OFFICIAL_BASE+FILES[name]) as src:
                        window=bounded_window_from_source(src,bbox)
                        grid=src.read(1,window=window,masked=True,boundless=False)
                        if grid.size>MAX_RASTER_PIXELS:
                            raise BuildingProxyError("original raster mask budget exceeded")
                        sources[name]=(grid,src.window_transform(window))
                dtm,ta=sources["MNT"]
                dsm,tb=sources["MNS"]
                if (dtm.shape!=dsm.shape or any(abs(a-b)>1e-6
                    for a,b in zip(ta,tb))):
                    raise BuildingProxyError("source grids not aligned")
                counts=aggregate(polygons,dtm,dsm,ta,roi)
    finally:
        db.close()
    return {
        "schema_version":"lu-geobase2026-lidar2024-bounded-object-proxy-v0",
        "study_window":"fixed public Luxembourg-city 100m x 100m equal-area",
        "geobase_original_gpkg_sha256":GEOBASE_SHA,
        "lidar_source_http_range_prefix_verified":True,
        "full_source_lidar_tiff_sha256_verified":False,
        "lidar_original_sizes_http":{
            name:receipts[name]["original_entire_file_bytes_declared_by_http"]
            for name in ("MNT","MNS")
        },
        "geobase_rtree_bbox_candidates":original_count,
        "geobase_bbox_candidates_outside_exact_roi":bbox_false_candidates,
        "geobase_upstream_family":"Luxembourg ACT 2026",
        "lidar_provider_same_family_as_geobase":True,
        "native_axis_ground_control_verified":False,
        "vertical_datum_independently_checked":False,
        "insured_exposure_or_tiv_inferred":False,
        **counts,
        "warning":(
            "Research-only object-clipped MNS-MNT median proxies. These can "
            "include vegetation and roof/surface artifacts, and 2024/2026 "
            "vintages differ. No per-building insured height or ground truth."
        ),
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--geobase-gpkg",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        report=run(args.geobase_gpkg)
    except (GeoPackageGateError,CogWindowError,BuildingProxyError,
            OSError,ValueError) as exc:
        p.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
