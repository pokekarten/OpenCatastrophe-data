#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded ACT2023v2 roof polygons vs original LiDAR2024 surface/terrain proxy.

This is a *roof-polygon* cohort contrast for the exact public 100m Luxembourg
city window, NOT actual per-building height nor independent ground truth.
Never emit original roof IDs, geometry, MNT/MNS arrays, per-roof medians or
any CAT model input. ACT2023 and LiDAR2024 share ACT source lineage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from research_runners.luxembourg_act2023_geobase2026_geometry_v0 import (
    ACT_GPKG_SHA, ACT_COUNT, ACT_LAYER,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, sample as sample_gpkg,
)
from research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 import (
    BuildingProxyError, aggregate, exact_area_candidates, original_window,
    MAX_POLYGONS, MAX_RASTER_PIXELS,
)
from research_runners.luxembourg_lidar2024_bounded_cog_window_v0 import (
    CogWindowError, bounded_window_from_source,
)
from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    FILES, OFFICIAL_BASE, read_header_range,
)


class RoofProxyError(ValueError):
    """Blocked input vintage, native geometry or projected raster research."""


def roof_proxy_summary(rtree_geometries, dtm, dsm, affine, roi):
    """Compute only source-cohort counts; avoid roof-vs-ground identity claims."""
    if not isinstance(rtree_geometries,list) or not 1 <= len(rtree_geometries) <= MAX_POLYGONS:
        raise RoofProxyError("Invalid original bounded roof source population")
    try:
        exact=exact_area_candidates(rtree_geometries,roi)
        result=aggregate(exact,dtm,dsm,affine,roi)
    except BuildingProxyError as exc:
        raise RoofProxyError("Original-source roof polygon/raster mask rejected") from exc
    false_hits=len(rtree_geometries)-len(exact)
    if (false_hits < 0 or result["original_building_polygons_in_study"] != len(exact)
        or result["objects_with_bounded_raster_proxy"]+
           result["objects_with_insufficient_unique_valid_pixels"]+
           result["objects_with_no_unique_raster_pixel"] != len(exact)):
        raise RoofProxyError("Original ACT roof count conservation failure")
    return {
        "act2023_rtree_bbox_candidates":len(rtree_geometries),
        "act2023_candidates_outside_exact_100m_roi":false_hits,
        "act2023_true_intersecting_roof_polygons":len(exact),
        "roof_proxy":result,
        "provider_source_role":"ACT2023v2 roof extents, not 2026 GeoBase buildings",
        "individual_roof_match_to_geobase_verified":False,
        "act2023_original_roof_heights_measured_or_certified":False,
        "act2023_to_lidar2024_independent_observation_proven":False,
        "act2023_model_input_admitted":False,
    }


def run_roof(original_gpkg:Path) -> dict:
    try:
        import rasterio
        from shapely.geometry import shape
    except ImportError as exc:
        raise RoofProxyError("Missing pinned spatial research-only runtime") from exc
    roi=original_window()
    receipt,db=inspect_gpkg(original_gpkg,expected_sha256=ACT_GPKG_SHA)
    try:
        layers=[layer for layer in receipt["layers"] if layer["table"]==ACT_LAYER]
        if (len(layers)!=1 or layers[0]["feature_count"]!=ACT_COUNT
            or layers[0]["srs_id"]!=2169 or not layers[0]["has_rtree"]
            or layers[0]["geometry_type"].upper() not in ("POLYGON","MULTIPOLYGON")):
            raise RoofProxyError("Unrecognized ACT2023v2 original roof schema or source population")
        with tempfile.TemporaryDirectory(prefix="oc-lu-act2023-roof-lidar-proxy-") as temp:
            sample_path=Path(temp)/"private-research-roofs.geojson"
            n=sample_gpkg(db,layers[0],id_field="buildingid",bbox=roi.bounds,
                          limit=MAX_POLYGONS,output=sample_path)
            sample=json.loads(sample_path.read_text(encoding="utf-8"))
            features=sample["features"]
            if len(features)!=n:
                raise RoofProxyError("Original sampled ACT roof count drift")
            roofs=[shape(feature["geometry"]) for feature in features]
            # These source 40GB COG assets support exact HTTP206 byte range reads
            # and known BigTIFF headers, but not full-file SHA-256 provenance.
            prefixes={key:read_header_range(key) for key in ("MNT","MNS")}
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                CPL_VSIL_CURL_CHUNK_SIZE="65536",
                CPL_VSIL_CURL_CACHE_SIZE="1048576",
                GDAL_HTTP_MAX_RETRY="0",GDAL_HTTP_TIMEOUT="20",
                GDAL_CACHEMAX=8,VSI_CACHE="FALSE",
            ):
                sampled={}
                for name in ("MNT","MNS"):
                    with rasterio.open("/vsicurl/"+OFFICIAL_BASE+FILES[name]) as source:
                        win=bounded_window_from_source(source,roi.bounds)
                        if win.width*win.height>MAX_RASTER_PIXELS:
                            raise RoofProxyError("Original LiDAR2024 study raster exceeds verified sample budget")
                        raster=source.read(1,window=win,masked=True,boundless=False)
                        if raster.size>MAX_RASTER_PIXELS:
                            raise RoofProxyError("Oversized original LiDAR2024 raster array")
                        sampled[name]=(raster,source.window_transform(win))
                ground,affine=sampled["MNT"]
                surface,affine2=sampled["MNS"]
                if (ground.shape!=surface.shape or
                    any(abs(x-y)>1e-6 for x,y in zip(affine,affine2))):
                    raise RoofProxyError("Original source terrain and surface grids do not align")
                counts=roof_proxy_summary(roofs,ground,surface,affine,roi)
    finally:
        db.close()
    return {
        "schema_version":"lu-act2023-roof-lidar2024-100m-bounded-mns-mnt-proxy-v0",
        "original_act2023_gpkg_sha256":ACT_GPKG_SHA,
        "original_act2023_full_count":ACT_COUNT,
        "native_source_crs":2169,
        "original_cog_http_fragment_receipts":{
            name:{"range_verified":True,
                  "declared_full_asset_bytes":prefixes[name]["original_entire_file_bytes_declared_by_http"],
                  "full_asset_sha256_verified":False}
            for name in ("MNT","MNS")
        },
        "study_window":"identical public 100m x 100m Luxembourg city window from #948/#957",
        "same_provider_ACT_lineage_is_independent":False,
        **counts,
        "original_roof_ids_geometries_per_roof_values_or_pixels_exported":False,
        "model_input_admitted":False,
        "note":"Median DSM-MNT inside 2023 rooftop polygons is vegetation/roof-object and 2023/2024 vintage sensitive; not certified building height. Bins not directly comparable to 2026 GeoBase object-bin numbers without polygon crosswalk.",
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--act2023-gpkg",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        data=run_roof(args.act2023_gpkg)
    except (GeoPackageGateError,CogWindowError,RoofProxyError,
            OSError,ValueError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
