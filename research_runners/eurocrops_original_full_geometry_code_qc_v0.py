#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""FULL original JRC DE4 2023 crop geometry/taxonomy quality census.

Only a first-seen SHA-pinned 2023 original may be read. Transient WKB and
cropfield IDs stay in memory; stdout/JSON contain ONLY aggregate QA counts.
Original source rights, perils, individual exposure, valuations and losses
remain unadmitted. This is NOT a scientific representativeness proof.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from research_runners.eurocrops_jrc_original_run_v0 import (
    BOOKS, EXPECTED_FOOTER_ROWS, download_pinned_codebook, verified_original,
)
from research_runners.eurocrops_original_zero_area_geometry_v0 import (
    PINNED_COMPLETE_JRC_SHA256, PREVIOUS_COMPLETE_ZERO_AREA_COUNT,
)
from research_runners.eurocrops_codebook_qc_v0 import (
    MAP_HEADER, HCAT_HEADER, _read_rows, audit,
)
from research_runners.eurocrops_v202_preflight_v0 import Blocked, geo_metadata

MAX_ROWS = 1_000_000
BATCH_SIZE = 512
REGION = "de4"


def complete_original_geometry_and_code_qc(
    parquet, mappings: list[dict], taxonomy: list[dict],
    *, expected_rows: int = EXPECTED_FOOTER_ROWS,
) -> dict:
    """A whole-file aggregate (not a licensed original parcel catalogue)."""
    from shapely import wkb
    from shapely.errors import GEOSException

    if (type(expected_rows) is not int or not 1 <= expected_rows <= MAX_ROWS or
            parquet.metadata.num_rows != expected_rows):
        raise Blocked("original Parquet footer row count differs from pinned asset")
    geo = geo_metadata(parquet.schema_arrow.metadata, parquet.schema_arrow.names)
    if geo["primary_geometry_column"] != "geometry" or geo["crs"] != "EPSG:3035":
        raise Blocked("unexpected original JRC geometry schema")

    regional = {}
    for row in mappings:
        if row["nuts"] != REGION or not row["original_code"]:
            continue
        code = row["original_code"]
        if code in regional:
            raise Blocked("duplicated regional crop dictionary join key")
        regional[code] = row["hcat4_code"]
    if not regional:
        raise Blocked("source codebook has no region-specific crop map")
    known_hcat = {r["hcat4_code"] for r in taxonomy}
    if not known_hcat:
        raise Blocked("original HCAT4 hierarchy empty")

    stats = {
        "source_rows": 0,
        "source_area_ha_zero_rows": 0,
        "source_area_ha_positive_rows": 0,
        "source_cropfield_noninteger_rows": 0,
        "source_cropfield_duplicate_subsequent_rows": 0,
        "source_crop_code_blank_or_nonstring_rows": 0,
        "source_crop_code_absent_from_regional_mapping_rows": 0,
        "source_code_mapping_to_absent_hcat4_rows": 0,
        "source_code_mapping_resolved_to_hcat4_rows": 0,
        "wkb_missing_or_unreadable_rows": 0,
        "geometry_empty_rows": 0,
        "geometry_nonpolygon_rows": 0,
        "geometry_invalid_topology_rows": 0,
        "geometry_nonfinite_or_nonpositive_area_rows": 0,
        "geometry_valid_positive_polygon_rows": 0,
        "valid_positive_polygon_area_delta_gt_1pct_rows": 0,
        "valid_positive_polygon_area_delta_gt_5pct_rows": 0,
        "valid_positive_polygon_area_delta_gt_50pct_rows": 0,
        "valid_polygons_with_source_area_ha_zero_rows": 0,
    }
    source_area_hectares: list[float] = []
    polygon_area_hectares: list[float] = []
    ids: set[int] = set()
    for batch in parquet.iter_batches(
        batch_size=BATCH_SIZE,
        columns=["cropfield", "original_code", "area_ha", "geometry"],
    ):
        if not 0 < batch.num_rows <= BATCH_SIZE:
            raise Blocked("invalid/oversized full original QA batch")
        rows = batch.to_pylist()
        if len(rows) != batch.num_rows:
            raise Blocked("source Arrow batch length drift")
        for row in rows:
            stats["source_rows"] += 1
            if stats["source_rows"] > expected_rows:
                raise Blocked("source exceeded verified original footer rows")
            original_id = row["cropfield"]
            if type(original_id) is not int:
                stats["source_cropfield_noninteger_rows"] += 1
            elif original_id in ids:
                stats["source_cropfield_duplicate_subsequent_rows"] += 1
            else:
                ids.add(original_id)
            area = row["area_ha"]
            if (isinstance(area, bool) or not isinstance(area, (int, float))
                    or not math.isfinite(float(area)) or area < 0):
                raise Blocked("source area changed from verified clean full area column")
            if area == 0:
                stats["source_area_ha_zero_rows"] += 1
            else:
                stats["source_area_ha_positive_rows"] += 1
            source_area_hectares.append(float(area))
            code = row["original_code"]
            if not isinstance(code, str) or not code or code.strip() != code:
                stats["source_crop_code_blank_or_nonstring_rows"] += 1
            else:
                mapped = regional.get(code)
                if mapped is None:
                    stats["source_crop_code_absent_from_regional_mapping_rows"] += 1
                elif mapped not in known_hcat:
                    stats["source_code_mapping_to_absent_hcat4_rows"] += 1
                else:
                    stats["source_code_mapping_resolved_to_hcat4_rows"] += 1
            try:
                raw = row["geometry"]
                if not isinstance(raw, (bytes, bytearray, memoryview)):
                    stats["wkb_missing_or_unreadable_rows"] += 1
                    continue
                geom = wkb.loads(bytes(raw))
            except (GEOSException, ValueError, TypeError, OverflowError):
                stats["wkb_missing_or_unreadable_rows"] += 1
                continue
            if geom.is_empty:
                stats["geometry_empty_rows"] += 1
                continue
            if geom.geom_type not in ("Polygon", "MultiPolygon"):
                stats["geometry_nonpolygon_rows"] += 1
                continue
            if not geom.is_valid:
                stats["geometry_invalid_topology_rows"] += 1
                continue
            geometric_m2 = float(geom.area)
            if not math.isfinite(geometric_m2) or geometric_m2 <= 0:
                stats["geometry_nonfinite_or_nonpositive_area_rows"] += 1
                continue
            stats["geometry_valid_positive_polygon_rows"] += 1
            geometric_ha = geometric_m2 / 10000
            polygon_area_hectares.append(geometric_ha)
            if area == 0:
                stats["valid_polygons_with_source_area_ha_zero_rows"] += 1
            else:
                ratio = abs(geometric_ha - float(area)) / float(area)
                if not math.isfinite(ratio):
                    raise Blocked("geometry/source area relative difference not finite")
                stats["valid_positive_polygon_area_delta_gt_1pct_rows"] += ratio > .01
                stats["valid_positive_polygon_area_delta_gt_5pct_rows"] += ratio > .05
                stats["valid_positive_polygon_area_delta_gt_50pct_rows"] += ratio > .50
    if stats["source_rows"] != expected_rows:
        raise Blocked("complete geometry scan shorter than original footer")
    if stats["source_area_ha_zero_rows"] != PREVIOUS_COMPLETE_ZERO_AREA_COUNT:
        raise Blocked("full original source area zero count differs from prior run")
    if (stats["source_area_ha_positive_rows"]
            + stats["source_area_ha_zero_rows"] != expected_rows):
        raise Blocked("original source area classifications do not conserve count")
    crop_kinds = (
        "source_crop_code_blank_or_nonstring_rows",
        "source_crop_code_absent_from_regional_mapping_rows",
        "source_code_mapping_to_absent_hcat4_rows",
        "source_code_mapping_resolved_to_hcat4_rows",
    )
    if sum(stats[k] for k in crop_kinds) != expected_rows:
        raise Blocked("complete codebook crosswalk counts do not conserve rows")
    kinds = (
        "wkb_missing_or_unreadable_rows", "geometry_empty_rows",
        "geometry_nonpolygon_rows", "geometry_invalid_topology_rows",
        "geometry_nonfinite_or_nonpositive_area_rows",
        "geometry_valid_positive_polygon_rows",
    )
    if sum(stats[k] for k in kinds) != expected_rows:
        raise Blocked("complete geometry classifications do not conserve rows")
    return {
        "profile": "eurocrops-de4-2023-original-full-wkb-and-hcat4-qc-v0",
        "original_file_rows": expected_rows,
        "full_original_geometry_and_code_quality": stats,
        "raw_source_area_ha_sum_not_unique_land_area":
            round(math.fsum(source_area_hectares), 4),
        "raw_valid_polygon_area_ha_sum_not_union_area":
            round(math.fsum(polygon_area_hectares), 4),
        "distinct_original_crop_codes_in_regional_codebook": len(regional),
        "original_region": REGION,
        "original_crs": "EPSG:3035",
        "actual_original_file_sha256_first_seen": PINNED_COMPLETE_JRC_SHA256,
        "original_raw_rows_or_geometries_output": False,
        "agricultural_parcel_overlaps_or_complete_coverage_verified": False,
        "model_input_rights_scientific_and_insurer_admission": "NOT_ADMITTED",
        "actual_insurer_agriculture_tiv_or_loss_derived": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.live:
        parser.exit(2, "BLOCKED: explicit --live required\n")
    if args.expected_sha256 != PINNED_COMPLETE_JRC_SHA256:
        parser.exit(2, "BLOCKED: original full-file SHA changed\n")
    if args.output.exists() or args.output.is_symlink():
        parser.exit(2, "BLOCKED: output receipt already exists\n")
    try:
        verified_original(args.original, args.expected_sha256)
        mapping_bytes = download_pinned_codebook("eurocrops.csv")
        hierarchy_bytes = download_pinned_codebook("hcat4.csv")
        audit(mapping_bytes, BOOKS["eurocrops.csv"],
              hierarchy_bytes, BOOKS["hcat4.csv"])
        mappings = _read_rows(mapping_bytes, BOOKS["eurocrops.csv"], MAP_HEADER)
        taxonomy = _read_rows(hierarchy_bytes, BOOKS["hcat4.csv"], HCAT_HEADER)
        import pyarrow.parquet as pq
        source = pq.ParquetFile(args.original)
        result = complete_original_geometry_and_code_qc(source, mappings, taxonomy)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    except (Blocked, OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print("PASS: full original WKB + crop code census completed, NOT_ADMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
