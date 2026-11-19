#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Forensic geometry-only QC of original JRC DE4 2023 area_ha == 0 rows.

Opt-in, FULL original-byte-pinned file only. Does not emit original rows,
IDs, geometry coordinates, area per parcel, TIV, damage, or insurer evidence.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from research_runners.eurocrops_jrc_original_run_v0 import (
    EXPECTED_FOOTER_ROWS, verified_original,
)
from research_runners.eurocrops_v202_preflight_v0 import Blocked, geo_metadata

PINNED_COMPLETE_JRC_SHA256 = (
    "4fc38f688a117db6cd0821c7aafc71fbbd2e7a493044c51266ae289929d7b2b6"
)
PREVIOUS_COMPLETE_ZERO_AREA_COUNT = 65


def audit_zero_area_geometry(parquet, *, expected_rows: int,
                             expected_zero: int) -> dict:
    """Scan bounded batches, only parse original WKB for exactly-zero areas."""
    from shapely import wkb
    from shapely.errors import GEOSException

    if (type(expected_rows) is not int or not 1 <= expected_rows <= 1000000
            or type(expected_zero) is not int or not 0 <= expected_zero <= expected_rows
            or parquet.metadata.num_rows != expected_rows):
        raise Blocked("unknown/oversized original row universe")
    geo = geo_metadata(parquet.schema_arrow.metadata, parquet.schema_arrow.names)
    if geo["primary_geometry_column"] != "geometry" or geo["crs"] != "EPSG:3035":
        raise Blocked("not the pinned original JRC geometry field and CRS")
    result = {
        "original_parquet_rows_inspected": 0,
        "original_reported_zero_area_ha_rows": 0,
        "zero_ha_wkb_invalid_or_missing": 0,
        "zero_ha_geometry_empty": 0,
        "zero_ha_geometry_invalid_topology": 0,
        "zero_ha_geometry_nonpolygon": 0,
        "zero_ha_polygon_computed_area_zero_m2": 0,
        "zero_ha_polygon_computed_area_positive_m2": 0,
        "zero_ha_polygon_positive_area_lt_1e_minus_6_m2": 0,
        "zero_ha_polygon_positive_area_1e_minus_6_to_lt_1_m2": 0,
        "zero_ha_polygon_positive_area_1_to_lt_100_m2": 0,
        "zero_ha_polygon_positive_area_gte_100_m2": 0,
    }
    min_area = None
    max_area = None
    for batch in parquet.iter_batches(batch_size=512, columns=["area_ha", "geometry"]):
        if not 0 < batch.num_rows <= 512:
            raise Blocked("zero-area original scan exceeded batch limit")
        rows = batch.to_pylist()
        if len(rows) != batch.num_rows:
            raise Blocked("original Parquet sample batch length drift")
        for row in rows:
            result["original_parquet_rows_inspected"] += 1
            if result["original_parquet_rows_inspected"] > expected_rows:
                raise Blocked("source rows exceeded pinned original footer")
            v = row["area_ha"]
            if (isinstance(v, bool) or not isinstance(v, (int, float))
                    or not math.isfinite(float(v)) or v < 0):
                raise Blocked("original area_ha outside prior full-column quality receipt")
            if v != 0:
                continue
            result["original_reported_zero_area_ha_rows"] += 1
            if result["original_reported_zero_area_ha_rows"] > expected_zero:
                raise Blocked("more zero-area records than prior original scan")
            try:
                raw = row["geometry"]
                if not isinstance(raw, (bytes, bytearray, memoryview)):
                    result["zero_ha_wkb_invalid_or_missing"] += 1
                    continue
                geometry = wkb.loads(bytes(raw))
            except (GEOSException, ValueError, TypeError, OverflowError):
                result["zero_ha_wkb_invalid_or_missing"] += 1
                continue
            if geometry.is_empty:
                result["zero_ha_geometry_empty"] += 1
                continue
            if not geometry.is_valid:
                result["zero_ha_geometry_invalid_topology"] += 1
                continue
            if geometry.geom_type not in ("Polygon", "MultiPolygon"):
                result["zero_ha_geometry_nonpolygon"] += 1
                continue
            area = float(geometry.area)
            if not math.isfinite(area) or area < 0:
                raise Blocked("unbounded original geometric polygon area")
            if area == 0:
                result["zero_ha_polygon_computed_area_zero_m2"] += 1
            else:
                result["zero_ha_polygon_computed_area_positive_m2"] += 1
                min_area = area if min_area is None else min(min_area, area)
                max_area = area if max_area is None else max(max_area, area)
                if area < 1e-6:
                    bucket = "zero_ha_polygon_positive_area_lt_1e_minus_6_m2"
                elif area < 1:
                    bucket = "zero_ha_polygon_positive_area_1e_minus_6_to_lt_1_m2"
                elif area < 100:
                    bucket = "zero_ha_polygon_positive_area_1_to_lt_100_m2"
                else:
                    bucket = "zero_ha_polygon_positive_area_gte_100_m2"
                result[bucket] += 1
    if (result["original_parquet_rows_inspected"] != expected_rows or
            result["original_reported_zero_area_ha_rows"] != expected_zero):
        raise Blocked("original zero-area count failed previous full-column parity")
    categories = (
        "zero_ha_wkb_invalid_or_missing", "zero_ha_geometry_empty",
        "zero_ha_geometry_invalid_topology", "zero_ha_geometry_nonpolygon",
        "zero_ha_polygon_computed_area_zero_m2",
        "zero_ha_polygon_computed_area_positive_m2",
    )
    if sum(result[k] for k in categories) != expected_zero:
        raise Blocked("zero-area classification did not conserve original records")
    result.update({
        "min_computed_positive_polygon_area_m2": min_area,
        "max_computed_positive_polygon_area_m2": max_area,
        "source_area_attribute_unit": "hectare",
        "computed_geometry_area_unit": "projected square metres EPSG:3035",
        "zero_area_source_rows_or_coordinates_output": False,
        "all_nonzero_original_field_polygons_individually_examined": False,
        "original_footprints_scientifically_admitted": False,
        "real_insurer_or_crop_value_estimate_created": False,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="operator explicitly approves exact original full-byte QA")
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    if not args.live:
        p.exit(2, "BLOCKED: explicit --live required\n")
    if args.expected_sha256 != PINNED_COMPLETE_JRC_SHA256:
        p.exit(2, "BLOCKED: original SHA does not match the independent first run\n")
    if args.output.exists() or args.output.is_symlink():
        p.exit(2, "BLOCKED: never overwrite original QA report\n")
    try:
        verified_original(args.original, args.expected_sha256)
        import pyarrow.parquet as pq
        parquet = pq.ParquetFile(args.original)
        result = audit_zero_area_geometry(
            parquet, expected_rows=EXPECTED_FOOTER_ROWS,
            expected_zero=PREVIOUS_COMPLETE_ZERO_AREA_COUNT,
        )
        result.update({
            "profile": "eurocrops-de4-2023-original-zero-area-geometry-QC-v0",
            "original_full_file_sha256_first_seen": PINNED_COMPLETE_JRC_SHA256,
            "source_rights_and_cat_model_admission": "NOT_ADMITTED",
            "original_rows_or_geometry_bytes_redistributed": False,
        })
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    except (Blocked, ValueError, RuntimeError, OSError) as exc:
        p.exit(2, "BLOCKED: " + str(exc) + "\n")
    print("PASS: Original zero-area geometry classification only, NOT_ADMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
