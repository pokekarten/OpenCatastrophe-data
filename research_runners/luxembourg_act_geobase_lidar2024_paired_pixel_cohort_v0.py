#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Paired original ACT2023 roof vs GeoBase2026 footprint LiDAR2024 pixel study.

Original provider sources are SHA256-pinned, and the fixed 100m Luxembourg
study uses ephemeral polygon/raster sampling. Output aggregate statistics only.
No joined building identities, per-building median, pixels, actual source
geometry or source IDs leave the temporary research environment. A high IoU
pair is NOT independently verified to be the same physical building.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import tempfile

from research_runners.luxembourg_act2023_geobase2026_geometry_v0 import (
    ACT_COUNT, ACT_GPKG_SHA, ACT_LAYER, GEOBASE_COUNT, GEOBASE_GPKG_SHA,
    GEOBASE_LAYER,
)
from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_gpkg, sample as sample_gpkg,
)
from research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 import (
    BuildingProxyError, MAX_POLYGONS, MAX_RASTER_PIXELS, original_window,
    exact_area_candidates,
)
from research_runners.luxembourg_lidar2024_bounded_cog_window_v0 import (
    CogWindowError, bounded_window_from_source,
)
from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    FILES, OFFICIAL_BASE, read_header_range,
)

MIN_IOU=0.60
CONFLICT_IOU=0.20
MIN_PIXELS=8

class PairedSourceError(ValueError):
    """Source identity, geometry pair or measurement fails a reviewed bound."""


def strict_spatial_pairs(left, right, *, min_iou=MIN_IOU,
                         conflict_iou=CONFLICT_IOU):
    """Find unique high-IoU pairs with no other >=0.20 alternative on either side.

    The result is indices private to this process; callers must never export
    these indices or imply that high IoU establishes physical identity.
    """
    from shapely.geometry import Polygon, MultiPolygon
    if not (isinstance(left,list) and isinstance(right,list)
            and 1<=len(left)<=MAX_POLYGONS and 1<=len(right)<=MAX_POLYGONS
            and 0<conflict_iou<min_iou<=1):
        raise PairedSourceError("Invalid bounded source polygons or IoU gates")
    if any(g.is_empty or not g.is_valid or g.area<=0
           or g.geom_type not in ("Polygon","MultiPolygon")
           for g in left+right):
        raise PairedSourceError("Invalid polygon source geometry")
    candidates=[]
    left_conflicts=Counter()
    right_conflicts=Counter()
    for i,a in enumerate(left):
        for j,b in enumerate(right):
            if not a.intersects(b):
                continue
            overlap=a.intersection(b).area
            if overlap<=0:
                continue
            union=a.area+b.area-overlap
            if union<=0:
                raise PairedSourceError("Invalid geometry union")
            iou=overlap/union
            if iou>=conflict_iou:
                left_conflicts[i]+=1
                right_conflicts[j]+=1
            if iou>=min_iou:
                candidates.append((i,j,iou))
    accepted=[(i,j) for i,j,_ in candidates
              if left_conflicts[i]==1 and right_conflicts[j]==1]
    if len({x[0] for x in accepted})!=len(accepted) or len({x[1] for x in accepted})!=len(accepted):
        raise PairedSourceError("Ambiguous spatial pair escaped uniqueness guard")
    return {
        "private_pairs":accepted,
        "high_iou_candidate_pairs":len(candidates),
        "unique_uncontested_spatial_pairs":len(accepted),
        "high_iou_pairs_rejected_as_ambiguous":len(candidates)-len(accepted),
        "geometry_iou_threshold":min_iou,
        "competing_geometry_iou_threshold":conflict_iou,
    }


def paired_pixel_diagnostic(roof_polygons, building_polygons, terrain, surface,
                            affine, study):
    """Aggregate source-mask-dependent medians for identical source pixel grids.

    Pairs must be disjoint candidates in BOTH source geometries. In addition,
    every retained pixel must belong to only ONE polygon *within each source*.
    Mask/median arrays and source indices remain transient and unpublished.
    """
    import numpy as np
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping
    if (not 1<=len(roof_polygons)<=MAX_POLYGONS
            or not 1<=len(building_polygons)<=MAX_POLYGONS
            or terrain.shape!=surface.shape or terrain.ndim!=2
            or not 1<=terrain.size<=MAX_RASTER_PIXELS):
        raise PairedSourceError("Invalid bounded pair / raster cohort dimensions")
    if not study.is_valid or study.is_empty or study.area<=0:
        raise PairedSourceError("Invalid equal-area study region")
    # CRITICAL: source polygons must be matched in their full native shape.
    # Clipping to 100m can artificially inflate IoU for nearby large,
    # differently segmented objects and create false 1:1 candidates.
    pairs=strict_spatial_pairs(roof_polygons,building_polygons)
    roofs=[g.intersection(study) for g in roof_polygons]
    buildings=[g.intersection(study) for g in building_polygons]
    if pairs["unique_uncontested_spatial_pairs"]<1:
        raise PairedSourceError("No uncontested high-IoU original source candidates")

    def masks(geoms):
        result=[]
        owners=np.zeros(terrain.shape,dtype=np.uint16)
        for geom in geoms:
            mask=geometry_mask([mapping(geom)],out_shape=terrain.shape,
                               transform=affine,invert=True,all_touched=False)
            owners+=mask.astype(np.uint16)
            result.append(mask)
        if int(np.max(owners))>len(geoms):
            raise PairedSourceError("Invalid raster polygon ownership counter")
        return result, owners

    roof_masks, roof_owners=masks(roofs)
    building_masks, building_owners=masks(buildings)
    a=np.asarray(terrain.data,dtype=np.float64)
    b=np.asarray(surface.data,dtype=np.float64)
    valid=(~np.ma.getmaskarray(terrain) & ~np.ma.getmaskarray(surface)
           & np.isfinite(a) & np.isfinite(b)
           & (a>=-1000) & (a<=4000) & (b>=-1000) & (b<=4000))
    diff=b-a
    if np.any(np.abs(diff[valid])>200):
        raise PairedSourceError("Implausible original raster height difference")
    if int(np.count_nonzero(valid))*2<terrain.size:
        raise PairedSourceError("Insufficient original source joint pixel coverage")

    bins={"below_0_5m":0,"0_5_to_below_2m":0,"2_to_below_5m":0,"5m_or_more":0}
    accepted=0
    insufficient=0
    negative_excluded=0
    n_shared=0
    total_roof_unique_pixels=0
    total_building_unique_pixels=0
    for i,j in pairs["private_pairs"]:
        am=roof_masks[i] & (roof_owners==1) & valid
        bm=building_masks[j] & (building_owners==1) & valid
        common=am & bm
        count_a=int(np.count_nonzero(am))
        count_b=int(np.count_nonzero(bm))
        count_common=int(np.count_nonzero(common))
        if min(count_a,count_b,count_common)<MIN_PIXELS:
            insufficient+=1
            continue
        med_a=float(np.median(diff[am]))
        med_b=float(np.median(diff[bm]))
        if not (math.isfinite(med_a) and math.isfinite(med_b)):
            raise PairedSourceError("Invalid source pair medians")
        if med_a<0 or med_b<0:
            negative_excluded+=1
            continue
        delta=abs(med_a-med_b)
        if delta<0.5:
            bins["below_0_5m"]+=1
        elif delta<2:
            bins["0_5_to_below_2m"]+=1
        elif delta<5:
            bins["2_to_below_5m"]+=1
        else:
            bins["5m_or_more"]+=1
        accepted+=1
        n_shared+=count_common
        total_roof_unique_pixels+=count_a
        total_building_unique_pixels+=count_b
    if accepted+insufficient+negative_excluded!=len(pairs["private_pairs"]) or sum(bins.values())!=accepted:
        raise PairedSourceError("Paired cohort conservation failed")
    if accepted==0:
        raise PairedSourceError("No shared-pixel source geometry pairs passed quality gates")
    return {
        "source_roof_positive_area_polygons":len(roof_polygons),
        "source_geobase_positive_area_polygons":len(building_polygons),
        "source_joint_valid_raster_pixels":int(np.count_nonzero(valid)),
        "geometry_high_iou_candidates":pairs["high_iou_candidate_pairs"],
        "geometry_unique_uncontested_candidate_pairs":pairs["unique_uncontested_spatial_pairs"],
        "geometry_ambiguous_high_iou_pairs_rejected":pairs["high_iou_pairs_rejected_as_ambiguous"],
        "paired_source_geometry_height_proxy_pairs_eligible":accepted,
        "paired_source_insufficient_joint_unique_pixel_pairs":insufficient,
        "paired_source_negative_median_excluded":negative_excluded,
        "paired_unique_shared_raster_pixels_aggregate":n_shared,
        "paired_total_roof_owned_raster_pixels_aggregate":total_roof_unique_pixels,
        "paired_total_geobase_owned_raster_pixels_aggregate":total_building_unique_pixels,
        "absolute_paired_median_surface_minus_terrain_difference_bins":bins,
        "geometry_min_iou":MIN_IOU,
        "competing_candidate_iou_threshold":CONFLICT_IOU,
        "per_source_object_indices_or_identifiers_exported":False,
        "independently_verified_same_physical_building":False,
        "independent_vertical_ground_truth_proven":False,
        "building_heights_certified":False,
        "original_pixel_grids_exported":False,
        "source_rights_or_cat_model_admitted":False,
    }


def _read_source_geometries(original:Path,*,sha256:str,layer_name:str,
                           id_field:str, expected_rows:int,roi):
    from shapely.geometry import shape
    receipt,db=inspect_gpkg(original,expected_sha256=sha256)
    try:
        matches=[layer for layer in receipt["layers"] if layer["table"]==layer_name]
        if (len(matches)!=1 or matches[0]["feature_count"]!=expected_rows
                or matches[0]["srs_id"]!=2169
                or matches[0]["geometry_type"].upper() not in ("POLYGON","MULTIPOLYGON")
                or not matches[0]["has_rtree"]):
            raise PairedSourceError("Original source schema/vintage changed")
        with tempfile.TemporaryDirectory(prefix="lu-paired-source-") as d:
            destination=Path(d)/"private-source.geojson"
            n=sample_gpkg(db,matches[0],id_field=id_field,bbox=roi.bounds,
                          limit=MAX_POLYGONS,output=destination)
            objects=json.loads(destination.read_text(encoding="utf-8"))["features"]
            if len(objects)!=n:
                raise PairedSourceError("Sampled original source population drift")
            geometries=[shape(x["geometry"]) for x in objects]
        exact=exact_area_candidates(geometries,roi)
        return exact,{"bbox_candidates":n,"exact_roi_geometries":len(exact),
                      "bbox_false_positives":n-len(exact)}
    except BuildingProxyError as exc:
        raise PairedSourceError("Unsafe/empty source geometry selection") from exc
    finally:
        db.close()


def run(act2023:Path,geobase2026:Path)->dict:
    import rasterio
    roi=original_window()
    roofs,acount=_read_source_geometries(
        act2023,sha256=ACT_GPKG_SHA,layer_name=ACT_LAYER,
        id_field="buildingid",expected_rows=ACT_COUNT,roi=roi)
    buildings,gcount=_read_source_geometries(
        geobase2026,sha256=GEOBASE_GPKG_SHA,layer_name=GEOBASE_LAYER,
        id_field="BU_BuildingID",expected_rows=GEOBASE_COUNT,roi=roi)
    receipts={name:read_header_range(name) for name in ("MNT","MNS")}
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        CPL_VSIL_CURL_CHUNK_SIZE="65536",
        CPL_VSIL_CURL_CACHE_SIZE="1048576",
        GDAL_HTTP_MAX_RETRY="0",
        GDAL_HTTP_TIMEOUT="20",
        GDAL_CACHEMAX=8,VSI_CACHE="FALSE",
    ):
        sampled={}
        for name in ("MNT","MNS"):
            with rasterio.open("/vsicurl/"+OFFICIAL_BASE+FILES[name]) as src:
                win=bounded_window_from_source(src,roi.bounds)
                if win.width*win.height>MAX_RASTER_PIXELS:
                    raise PairedSourceError("Source raster window budget exceeded")
                a=src.read(1,window=win,masked=True,boundless=False)
                if a.size>MAX_RASTER_PIXELS:
                    raise PairedSourceError("Source raster array budget exceeded")
                sampled[name]=(a,src.window_transform(win))
        terrain,transform=sampled["MNT"]
        surface,other_transform=sampled["MNS"]
        if terrain.shape!=surface.shape or any(abs(x-y)>1e-6
               for x,y in zip(transform,other_transform)):
            raise PairedSourceError("Original MNT/MNS grids not aligned")
        result=paired_pixel_diagnostic(roofs,buildings,terrain,surface,transform,roi)
    return {
        "schema_version":"lu-act2023-geobase2026-lidar2024-shared-pixel-geometry-cohort-v0",
        "study_area":"same fixed Luxembourg city 100mx100m EPSG3035 square; native 2169 research hypothesis",
        "act2023_original_gpkg_sha256":ACT_GPKG_SHA,
        "geobase2026_original_gpkg_sha256":GEOBASE_GPKG_SHA,
        "source_original_counts":{"act2023":ACT_COUNT,"geobase2026":GEOBASE_COUNT},
        "source_window_counts":{"act2023":acount,"geobase2026":gcount},
        "lidar_http206_prefix_pass":all(x["range_verified"] for x in receipts.values()),
        "full_original_40gb_cog_file_sha256_verified":False,
        "source_geodetic_axis_ground_control_verified":False,
        "source_lidar_vertical_datum_independently_verified":False,
        "sources_share_act_provider_lineage":True,
        **result,
        "warning":"Aggregate paired spatial candidates, not confirmed physical building identity or independent building-height ground truth. Geometry segmentation/vintage, trees and roof artifacts remain unresolved.",
        "model_input_admitted":False,
    }


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--act2023-gpkg",type=Path,required=True)
    parser.add_argument("--geobase2026-gpkg",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        report=run(args.act2023_gpkg,args.geobase2026_gpkg)
    except (GeoPackageGateError,CogWindowError,PairedSourceError,
            BuildingProxyError,OSError,ValueError) as exc:
        parser.exit(2,"BLOCKED: "+str(exc)+"\n")
        return 2
    print(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
