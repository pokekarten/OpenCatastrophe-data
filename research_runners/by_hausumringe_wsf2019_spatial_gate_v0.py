#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed Bavaria Hausumringe vs WSF2019 source-footprint research.

Consumes one original research-only Neon mask sample (#28 or #29) and a
separately prepared local excerpt from the PUBLIC BVV Hausumringe Shapefile.
No network requests, provider-byte persistence, original polygons/masks in
logs, private ALKIS WFS access, residential counts, TIV or CAT admission.

The internal FeatureCollection intentionally carries original EPSG:25832 UTM
coordinates. It is NOT RFC7946 longitude/latitude GeoJSON. GEOS/pyproj
projects its valid Polygon/MultiPolygon geometry into the fixed WSF grid.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE = "de.bayern.hausumringe"
WSF = "dlr.wsf.2019"
ORIGINAL_COMPRESSED_TILE_SHA = "8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503"
SAMPLES = {
    28: ("ff08ea1f4b89475bb4bcf8d4a453e55058f21eba2de2daa1fb5943d1706293df", 0),
    29: ("85aaf92c2b87fc7ea80359498680bca371aaa0e974d65476328bb70e314b3fce", 482),
}
MAX_SOURCE_BYTES = 4_000_000
SHA = re.compile(r"^[a-f0-9]{64}$")


class AlignmentBlocked(ValueError):
    """Exact original, rights, CRS or topology evidence failed closed."""


def _sha(v):
    if type(v) is not str or not SHA.fullmatch(v):
        raise AlignmentBlocked("64-character lowercase SHA-256 required")
    return v


def _date(v):
    if type(v) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        raise AlignmentBlocked("source snapshot ISO date required")
    try:
        return date.fromisoformat(v)
    except ValueError as exc:
        raise AlignmentBlocked("invalid source date") from exc


def verify_neon_mask(row):
    if type(row) is not dict or type(row.get("sample_id")) is not int:
        raise AlignmentBlocked("integer Neon sample ID required")
    sid = row["sample_id"]
    if sid not in SAMPLES or row.get("source_id") != WSF:
        raise AlignmentBlocked("only reviewed Neon masks 28 and 29 accepted")
    if row.get("sample_kind") != "geospatial_preview" or row.get("model_input_approved") is not False:
        raise AlignmentBlocked("not a research-only native sample")
    if _sha(row.get("provider_response_sha256")) != ORIGINAL_COMPRESSED_TILE_SHA:
        raise AlignmentBlocked("original source compressed block SHA mismatch")
    j = row.get("sample_json")
    if type(j) is not dict or j.get("source_id") != WSF or j.get("epsg") != 4326:
        raise AlignmentBlocked("source profile / original EPSG mismatch")
    if j.get("model_input_approved") is not False or j.get("original_compressed_tile_sha256") != ORIGINAL_COMPRESSED_TILE_SHA:
        raise AlignmentBlocked("source not independently pinned or not research-only")
    if j.get("sample_subtype") not in ("native_geotiff_lzw_window", "native_geotiff_lzw_window_mixed"):
        raise AlignmentBlocked("not a native DLR original class mask")
    if j.get("window_width") != 32 or j.get("window_height") != 32:
        raise AlignmentBlocked("only the two fixed 32x32 pixel windows allowed")
    rows = j.get("window_raster_rows_binary_1_is_255")
    if type(rows) is not list or len(rows) != 32 or any(type(r) is not str or len(r) != 32 or set(r) - {"0", "1"} for r in rows):
        raise AlignmentBlocked("invalid original 32x32 binary rows")
    digest = hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()
    if digest != SAMPLES[sid][0]:
        raise AlignmentBlocked("original Neon/GDAL mask digest mismatch")
    pos = sum(x.count("1") for x in rows)
    counts = j.get("window_counts") or j.get("window_class_counts")
    if type(counts) is not dict or counts.get("255") != pos or counts.get("0") != 1024-pos or pos != SAMPLES[sid][1]:
        raise AlignmentBlocked("original raster class count mismatch")
    bbox = j.get("window_bbox_lonlat")
    if type(bbox) is not list or len(bbox) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in bbox):
        raise AlignmentBlocked("invalid original raster bbox")
    w,s,e,n = bbox
    if not (11.53 < w < e < 11.57 and 48.11 < s < n < 48.15):
        raise AlignmentBlocked("unexpected original DLR sample extent")
    dx,dy=(e-w)/32,(n-s)/32
    if not (8.983e-5 < dx < 8.984e-5 and abs(dx-dy) < 1e-11):
        raise AlignmentBlocked("native pixel scale mismatch")
    return rows, tuple(bbox)


def verify_local_reference(ref):
    if type(ref) is not dict or ref.get("source_id") != SOURCE:
        raise AlignmentBlocked("BVV Hausumringe candidate required")
    if ref.get("original_format") != "Shapefile" or ref.get("source_crs") != "EPSG:25832":
        raise AlignmentBlocked("original Shape / ETRS89 UTM32 CRS required")
    if ref.get("license") != "CC-BY-4.0" or ref.get("source_is_official_open_data") is not True:
        raise AlignmentBlocked("exact open-download licence assertion required")
    # No caller can promote an unverified local subset via this interface.
    if ref.get("independently_verified_source_asset") is not False or ref.get("roi_complete_for_frozen_bbox") is not False:
        raise AlignmentBlocked("provider integrity and full-ROI completeness remain unverified")
    _sha(ref.get("original_archive_sha256"))
    vintage = _date(ref.get("source_snapshot_date"))
    if not date(2020,1,1) <= vintage <= date.today():
        raise AlignmentBlocked("unreviewed BVV snapshot date")
    features=ref.get("features")
    if ref.get("type") != "FeatureCollection" or type(features) is not list or not 1 <= len(features) <= 256:
        raise AlignmentBlocked("1 to 256 bounded BVV features required")
    try:
        from shapely.geometry import shape
    except ImportError as exc:
        raise AlignmentBlocked("GEOS Shapely required") from exc
    geometries=[]
    vertices=0
    for feature in features:
        if type(feature) is not dict or feature.get("type") != "Feature":
            raise AlignmentBlocked("invalid official Feature")
        geometry=feature.get("geometry")
        if type(geometry) is not dict or geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise AlignmentBlocked("official geometry must be polygonal")
        try:
            g=shape(geometry)
        except Exception as exc:
            raise AlignmentBlocked("original polygon could not be parsed") from exc
        if g.is_empty or not g.is_valid or g.area <= 0 or not all(math.isfinite(v) for v in g.bounds):
            raise AlignmentBlocked("invalid official footprint topology")
        if not (600000 < g.bounds[0] < g.bounds[2] < 800000 and 5200000 < g.bounds[1] < g.bounds[3] < 5500000):
            raise AlignmentBlocked("unexpected ETRS89 UTM32 building coordinates")
        parts=list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        vertices+=sum(len(p.exterior.coords)+sum(len(r.coords) for r in p.interiors) for p in parts)
        if vertices > 15000:
            raise AlignmentBlocked("unbounded original geometry vertices")
        geometries.append(g)
    return geometries,vintage


def compare_area_weighted(rows, bbox, geometries):
    """Fractional pixel-square intersections, unioned features; no centroid test."""
    try:
        from pyproj import Transformer
        from shapely.geometry import box
        from shapely.ops import transform, unary_union
    except ImportError as exc:
        raise AlignmentBlocked("GEOS and PROJ required for pixel-overlay QA") from exc
    to_wgs=Transformer.from_crs("EPSG:25832","EPSG:4326",always_xy=True)
    w,s,e,n=bbox
    dx=(e-w)/32
    dy=(n-s)/32
    pixel=lambda x,y,z=None: ((x-w)/dx,(n-y)/dy)
    try:
        footprint=unary_union([
            transform(pixel,transform(to_wgs.transform,g)) for g in geometries
        ])
        if footprint.is_empty or not footprint.is_valid:
            raise AlignmentBlocked("invalid transformed footprint union")
        footprint=footprint.intersection(box(0,0,32,32))
    except AlignmentBlocked:
        raise
    except Exception as exc:
        raise AlignmentBlocked("reviewed original CRS transform failed") from exc
    if footprint.is_empty or footprint.area <= 0:
        raise AlignmentBlocked("no common footprint / original WSF cell support")
    settlement=unary_union([
        box(x,y,x+1,y+1)
        for y,line in enumerate(rows) for x,bit in enumerate(line) if bit=="1"
    ])
    intersection=footprint.intersection(settlement).area if not settlement.is_empty else 0.0
    actual=footprint.area
    predicted=settlement.area
    union=actual+predicted-intersection
    if not (0 <= intersection <= min(actual,predicted)+1e-6 and 0<actual<=1024+1e-6 and 0<=predicted<=1024):
        raise AlignmentBlocked("native pixel / polygon area conservation failed")
    return {
        "reference_area_in_native_cell_equivalents":round(actual,6),
        "wsf_settled_area_in_native_cell_equivalents":round(predicted,6),
        "intersection_area_in_native_cell_equivalents":round(intersection,6),
        "area_weighted_iou_on_partial_reference":round(intersection/union,6) if union else None,
        "area_weighted_reference_recall_partial_only":round(intersection/actual,6),
        "area_weighted_predicted_precision_partial_only":round(intersection/predicted,6) if predicted else None,
        "area_weighted_false_positive_cells_relative_to_excerpt":round(predicted-intersection,6),
        "area_weighted_false_negative_cells_relative_to_excerpt":round(actual-intersection,6),
    }


def inspect(sample_record, official_excerpt):
    rows,bbox=verify_neon_mask(sample_record)
    geometries,snapshot=verify_local_reference(official_excerpt)
    result=compare_area_weighted(rows,bbox,geometries)
    return {
        "profile":"oc-by-hausumringe-wsf2019-native-32px-partial-footprint-qc-v0",
        "source_id":SOURCE,"raster_source_id":WSF,
        "neon_sample_id":sample_record["sample_id"],
        "original_wsf_mask_sha256":SAMPLES[sample_record["sample_id"]][0],
        "original_bvv_archive_sha256_reported_only":_sha(official_excerpt["original_archive_sha256"]),
        "reported_official_snapshot_date":snapshot.isoformat(),
        "year_gap_from_2019":snapshot.year-2019,
        "local_reference_polygons_read":len(geometries),
        "bounded_offline_research_comparison_executed":True,
        "roi_complete_independently_verified":False,
        "original_reference_sha_independently_verified":False,
        "provider_geometry_or_pixel_data_emitted":False,
        "individual_cadastral_building_count_validated":False,
        "insurer_exposure_or_tiv_inferred":False,
        "model_input_approved":False,
        **result,
    }


def _local_json(path):
    p=Path(path)
    if p.stat().st_size>MAX_SOURCE_BYTES:
        raise AlignmentBlocked("offline input exceeds 4 MB")
    with p.open("r",encoding="utf-8") as stream:
        return json.load(stream)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neon-sample",required=True,help="private local Neon row export, not in Git")
    parser.add_argument("--bvv-geojson",required=True,help="private local original-UTM32 building subset")
    args=parser.parse_args(argv)
    try:
        receipt=inspect(_local_json(args.neon_sample),_local_json(args.bvv_geojson))
    except (AlignmentBlocked,OSError,ValueError,OverflowError):
        print("BLOCKED: local raster/building comparison failed closed",file=sys.stderr)
        return 2
    print(json.dumps(receipt,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
