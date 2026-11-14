# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Ephemeral original Overture Luxembourg-city source-family aggregate.

Reads only public bbox and sources columns from frozen original Parquet
part 00226 row-group 182. No IDs, record_ids, WKB, coordinates,
addresses, provider bytes, insurer exposures or CAT input persisted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys

from research_runners.overture_lu_rowgroup_metadata_v0 import probe as source_preflight
from research_runners.overture_lu_one_rowgroup_geometry_observation_v0 import (
    _coordinates_in_city_box, S3_PATH, REGION, EXPECTED_BYTES, EXPECTED_ROWS,
    EXPECTED_ROW_GROUPS_STAC, TARGET_ROW_GROUP, TARGET_ROW_COUNT,
    ProbeError,
)

SCHEMA = "opencatastrophe-lu-original-overture-source-family-counts-v0"
EXPECTED_CITY_BBOX_ROWS = 69
MAX_SELECTED_COMPRESSED_BYTES = 8 * 1024 * 1024


def _safe_label(value):
    if type(value) is str and re.fullmatch(r"[A-Za-z0-9 ._:/()+-]{1,80}", value):
        return value
    return "unclassified"


def summarize_sources(bboxes, sources):
    if len(bboxes) != TARGET_ROW_COUNT or len(sources) != TARGET_ROW_COUNT:
        raise ProbeError("source lineage row-group population changed")
    datasets = Counter()
    licenses = Counter()
    selected = 0
    missing_source_rows = 0
    rows_with_multiple_source_datasets = 0
    rejected_source_entries = 0
    for bounds, raw_entries in zip(bboxes, sources):
        if not _coordinates_in_city_box(bounds):
            continue
        selected += 1
        if raw_entries is None:
            missing_source_rows += 1
            continue
        if type(raw_entries) is not list or len(raw_entries) > 128:
            rejected_source_entries += 1
            continue
        row_datasets = set()
        row_licenses = set()
        for entry in raw_entries:
            if type(entry) is not dict:
                rejected_source_entries += 1
                continue
            row_datasets.add(_safe_label(entry.get("dataset")))
            if entry.get("license") is not None:
                row_licenses.add(_safe_label(entry.get("license")))
            # Never emit per-record record_id, property, provider object IDs
            # or any user-derived, geospatial or source coordinate fields.
        datasets.update(row_datasets)
        licenses.update(row_licenses)
        if len(row_datasets) > 1:
            rows_with_multiple_source_datasets += 1
    if selected != EXPECTED_CITY_BBOX_ROWS:
        raise ProbeError("source candidate geographic bbox count differs from verified original")
    return {
        "original_file_row_group_rows_scanned": TARGET_ROW_COUNT,
        "original_source_rows_intersecting_bbox": selected,
        "city_bbox_rows_without_source_entries": missing_source_rows,
        "city_bbox_rows_with_multiple_upstream_datasets": rows_with_multiple_source_datasets,
        "invalid_source_entries_quarantined": rejected_source_entries,
        "upstream_dataset_row_presence_counts": dict(sorted(datasets.items())),
        "upstream_license_tag_row_presence_counts": dict(sorted(licenses.items())),
        "labels_are_unverified_original_provenance_claims": True,
        "independent_data_lineage_proven": False,
        "per_building_source_ids_or_geometry_exported": False,
        "source_data_retained": False,
        "model_input_approved": False,
        "neon_modified": False,
    }


def live():
    provider = source_preflight()
    if provider["original_zero_based_rowgroup_indices_for_followup"] != [TARGET_ROW_GROUP]:
        raise ProbeError("pinned Overture geographic rowgroup changed")
    try:
        import pyarrow.fs as fs
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ProbeError("Arrow runtime missing") from exc
    storage = fs.S3FileSystem(anonymous=True, region=REGION,
                              connect_timeout=15, request_timeout=15)
    if storage.get_file_info(S3_PATH).size != EXPECTED_BYTES:
        raise ProbeError("source file byte length differs from STAC receipt")
    pf = pq.ParquetFile(S3_PATH, filesystem=storage, pre_buffer=False)
    if (pf.metadata.num_rows != EXPECTED_ROWS
            or pf.metadata.num_row_groups != EXPECTED_ROW_GROUPS_STAC
            or pf.metadata.row_group(TARGET_ROW_GROUP).num_rows != TARGET_ROW_COUNT):
        raise ProbeError("original source metadata mismatch")
    group = pf.metadata.row_group(TARGET_ROW_GROUP)
    compressed = 0
    has_sources = False
    has_bbox = set()
    for j in range(group.num_columns):
        m = group.column(j)
        path = m.path_in_schema
        if path.startswith("sources."):
            has_sources = True
            compressed += m.total_compressed_size
        elif path in ("bbox.xmin","bbox.ymin","bbox.xmax","bbox.ymax"):
            has_bbox.add(path)
            compressed += m.total_compressed_size
    if (not has_sources or len(has_bbox) != 4
            or compressed <= 0 or compressed > MAX_SELECTED_COMPRESSED_BYTES):
        raise ProbeError("source lineage columns unavailable or oversized")
    table = pf.read_row_group(TARGET_ROW_GROUP, columns=["bbox", "sources"],
                              use_threads=False)
    if table.num_rows != TARGET_ROW_COUNT:
        raise ProbeError("Arrow returned partial or excess source records")
    summary = summarize_sources(table["bbox"].to_pylist(),
                                table["sources"].to_pylist())
    return {
        "schema": SCHEMA,
        "release": "2026-10-21.0",
        "original_rowgroup_index": TARGET_ROW_GROUP,
        "original_selected_column_compressed_bytes": compressed,
        "network_bytes_strictly_capped": False,
        "source_licensing_reviewed_for_CAT_reuse": False,
        **summary,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true", help="Explicit source metadata-only review")
    args = p.parse_args(argv)
    if not args.live:
        print("BLOCKED: explicit --live required", file=sys.stderr)
        return 2
    try:
        result = live()
    except (ProbeError, OSError, ValueError, TypeError, ImportError):
        print("BLOCKED: original source lineage preflight failure", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
