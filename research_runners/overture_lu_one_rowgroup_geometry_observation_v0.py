# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Ephemeral, exact-one-row-group Overture Luxembourg-city geometry observation.

Explicit opt-in only. Reads bbox and geometry columns from original S3
Parquet part 00226, row group 182, never persists provider rows, IDs or WKB,
logs only aggregate counts, does not write to Git/Neon/Oasis or infer TIV.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys

from research_runners.overture_luxembourg_stac_receipt_v0 import (
    EXPECTED_BYTES, EXPECTED_ROWS, EXPECTED_ROW_GROUPS_STAC, S3_OBJECT_KEY,
    ProbeError,
)
from research_runners.overture_lu_rowgroup_metadata_v0 import (
    EXPECTED_FOOTER_BYTES, probe as metadata_probe,
)

SCHEMA = "opencatastrophe-overture-lu-one-rowgroup-original-geometry-observation-v0"
BUCKET = "overturemaps-us-west-2"
REGION = "us-west-2"
S3_PATH = BUCKET + "/" + S3_OBJECT_KEY
TARGET_ROW_GROUP = 182
TARGET_ROW_COUNT = 19095
CITY_BOX = (6.129, 49.609, 6.131, 49.611)
MAX_SELECTED_COLUMN_COMPRESSED_BYTES = 12 * 1024 * 1024
MAX_FEATURES_PROFILED = 64


def _coordinates_in_city_box(bbox):
    """Candidate-only rectangle check, never proof of polygon intersection."""
    if type(bbox) is not dict or set(bbox) != {"xmin", "ymin", "xmax", "ymax"}:
        return False
    vals = [bbox.get(k) for k in ("xmin", "ymin", "xmax", "ymax")]
    if any(type(v) not in (float, int) or not math.isfinite(v) for v in vals):
        return False
    xmin, ymin, xmax, ymax = vals
    if xmin > xmax or ymin > ymax:
        return False
    return (xmin < CITY_BOX[2] and xmax > CITY_BOX[0]
            and ymin < CITY_BOX[3] and ymax > CITY_BOX[1])


def screen_original_rows(bboxes, geometry_wkb):
    """Aggregate actual WKB checks; no source geometry or IDs in return value."""
    if (len(bboxes) != TARGET_ROW_COUNT or len(geometry_wkb) != TARGET_ROW_COUNT):
        raise ProbeError("unexpected original row-group batch size")
    from shapely import wkb
    from shapely.geometry import box
    from shapely.errors import GEOSException
    from pyproj import Geod

    query = box(*CITY_BOX)
    geod = Geod(ellps="WGS84")
    bbox_candidates = 0
    positive_overlap = 0
    malformed_wkb = 0
    invalid_topology = 0
    profiled_geodesic_area = []
    for bbox, raw in zip(bboxes, geometry_wkb):
        if not _coordinates_in_city_box(bbox):
            continue
        bbox_candidates += 1
        if not isinstance(raw, bytes) or not 0 < len(raw) <= 500_000:
            malformed_wkb += 1
            continue
        try:
            geom = wkb.loads(raw)
        except (GEOSException, ValueError, TypeError):
            malformed_wkb += 1
            continue
        if (geom.geom_type not in ("Polygon", "MultiPolygon")
                or geom.is_empty or not geom.is_valid):
            invalid_topology += 1
            continue
        try:
            if not geom.intersects(query) or geom.intersection(query).area <= 0:
                continue
        except GEOSException:
            invalid_topology += 1
            continue
        positive_overlap += 1
        if len(profiled_geodesic_area) < MAX_FEATURES_PROFILED:
            try:
                a = abs(geod.geometry_area_perimeter(geom)[0])
            except (ValueError, TypeError):
                a = float("nan")
            if math.isfinite(a) and a > 0:
                profiled_geodesic_area.append(a)
    return {
        "actual_original_rows_scanned_in_one_group": len(bboxes),
        "source_bbox_candidates_in_research_window": bbox_candidates,
        "original_valid_polygons_with_positive_window_overlap": positive_overlap,
        "source_invalid_polygon_candidates": invalid_topology,
        "malformed_geometry_candidates": malformed_wkb,
        "profiled_valid_geodesic_footprint_count": len(profiled_geodesic_area),
        "profiled_geodesic_footprint_m2_median": (
            round(statistics.median(profiled_geodesic_area), 2)
            if profiled_geodesic_area else None),
        "individual_original_ids_or_polygons_emitted": False,
        "actual_city_building_count_certified": False,
        "source_lineage_and_GERS_membership_proven": False,
        "insurer_valuation_inferred": False,
        "insurance_CAT_model_input_approved": False,
        "neon_production_modified": False,
    }


def _expected_column_bytes(meta):
    desired = {"geometry", "bbox.xmin", "bbox.ymin", "bbox.xmax", "bbox.ymax"}
    found = set()
    bytes_total = 0
    for i in range(meta.num_columns):
        col = meta.column(i)
        if col.path_in_schema not in desired:
            continue
        if col.path_in_schema in found:
            raise ProbeError("duplicate source Parquet column")
        found.add(col.path_in_schema)
        if type(col.total_compressed_size) is not int or col.total_compressed_size < 1:
            raise ProbeError("source Parquet column lacks compressed byte budget")
        bytes_total += col.total_compressed_size
    if found != desired or bytes_total > MAX_SELECTED_COLUMN_COMPRESSED_BYTES:
        raise ProbeError("source column missing or too large for bounded research")
    return bytes_total


def live_observation():
    # Separate bounded original STAC + footer proof, including exactly one
    # potentially intersecting original row group (index 182).
    proof = metadata_probe()
    if proof["original_zero_based_rowgroup_indices_for_followup"] != [TARGET_ROW_GROUP]:
        raise ProbeError("original row-group geography changed")
    try:
        import pyarrow.fs as fs
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ProbeError("pinned Arrow runtime not installed") from exc
    filesystem = fs.S3FileSystem(anonymous=True, region=REGION,
                               connect_timeout=15, request_timeout=15)
    info = filesystem.get_file_info(S3_PATH)
    if info.size != EXPECTED_BYTES:
        raise ProbeError("original S3 object size changed")
    parquet = pq.ParquetFile(S3_PATH, filesystem=filesystem,
                             pre_buffer=False)
    if (parquet.metadata.num_rows != EXPECTED_ROWS or
            parquet.metadata.num_row_groups != EXPECTED_ROW_GROUPS_STAC):
        raise ProbeError("original Parquet footer differs from source receipt")
    rowgroup = parquet.metadata.row_group(TARGET_ROW_GROUP)
    if rowgroup.num_rows != TARGET_ROW_COUNT:
        raise ProbeError("candidate source row-group population changed")
    expected_compressed_bytes = _expected_column_bytes(rowgroup)
    # Arrow's S3 filesystem range-reads selected columns; this is a compressed
    # column-size preflight, NOT a strict cap on HTTP header/index overhead.
    table = parquet.read_row_group(TARGET_ROW_GROUP,
                                   columns=["bbox", "geometry"],
                                   use_threads=False)
    if table.num_rows != TARGET_ROW_COUNT:
        raise ProbeError("returned source row-group population differs")
    result = screen_original_rows(table["bbox"].to_pylist(),
                                  table["geometry"].to_pylist())
    return {
        "schema": SCHEMA,
        "original_s3_source_key": S3_OBJECT_KEY,
        "source_release": "2026-10-21.0",
        "selected_zero_based_original_row_group": TARGET_ROW_GROUP,
        "declared_selected_columns_compressed_bytes": expected_compressed_bytes,
        "original_source_file_full_sha256_verified": False,
        "source_CRS_epoch_independently_proven": False,
        "source_ODbL_attribution_needs_review": True,
        "source_rows_retained_or_exported": False,
        "HTTP_network_transfer_strict_byte_cap_proven": False,
        **result,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Read one source row-group of public Overture geometry ephemerally")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: explicit --live required", file=sys.stderr)
        return 2
    try:
        result = live_observation()
    except (ProbeError, OSError, ValueError, TypeError, ImportError) as exc:
        print("BLOCKED: " + type(exc).__name__ + " in original-only research", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
