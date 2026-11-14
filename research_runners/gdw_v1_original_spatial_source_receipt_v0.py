# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen aggregate-only GEOS result from the real GDW v1.0 original shapefile.

This is a *diagnostic* source receipt, not a GIS repair or CAT admission.
No original coordinates, feature IDs or source bytes appear in this module.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_SPATIAL_RECEIPT_V0 = {
    "schema_version": "gdw-v1-original-geos-paired-geometry-receipt-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "original_file_sha256": "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "source_run_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41886824276",
    "source_run_commit": "800806bb028ac698c67a98747747f7a8058422b8",
    "source_run_date_utc": "2026-11-04",
    "reader": "pyshp 2.3.1 + Shapely 2.1.2 / GEOS",
    "barrier_points": 41145,
    "reservoir_polygons": 35295,
    "point_only_barriers": 5850,
    "valid_reservoir_polygons": 35074,
    "invalid_reservoir_polygons": 221,
    "unparseable_reservoir_polygons": 0,
    "valid_polygon_matched_point_strict_interior": 35074,
    "valid_polygon_matched_point_boundary": 0,
    "valid_polygon_matched_point_outside": 0,
    "unassessable_matched_pairs_due_to_invalid_polygon": 221,
    "all_valid_native_polygons_contain_paired_dam_point": True,
    "all_original_polygons_geos_valid": False,
    "invalidity_reason_families_quantified": False,
    "source_geometries_repaired": False,
    "source_ids_or_coordinates_exported": False,
    "dam_failure_probabilities_or_flood_extent_proven": False,
    "model_input_admitted": False,
}
