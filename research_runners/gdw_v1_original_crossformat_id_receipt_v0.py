# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Real original GDW v1 two-format source-ID and invalid-polygon concordance.

These aggregate-only findings were observed on the reviewed main runner.
No original provider bytes, record GDW_ID values or coordinates are stored.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_CROSSFORMAT_ID_RECEIPT_V0 = {
    "schema_version": "gdw-v1-exact-original-shp-filegdb-invalid-id-concordance-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "original_shapefile_sha256": "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "original_filegdb_sha256": "5ebb1092e355f1833132be8a16340da7de979314d06aba00e57eb7412884f09f",
    "original_source_execution": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41893588594",
    "source_main_commit": "e86349f0699e1165a6466d3412b66b5a5cb5806b",
    "source_date_utc": "2026-11-04",
    "shapefile_barrier_count": 41145,
    "filegdb_barrier_count": 41145,
    "barrier_ids_present_in_both_formats": 41145,
    "barrier_ids_shp_only": 0,
    "barrier_ids_gdb_only": 0,
    "shapefile_reservoir_count": 35295,
    "filegdb_reservoir_count": 35295,
    "reservoir_ids_present_in_both_formats": 35295,
    "reservoir_ids_shp_only": 0,
    "reservoir_ids_gdb_only": 0,
    "invalid_ring_self_intersections_per_format": 221,
    "invalid_polygon_ids_in_both_formats": 221,
    "invalid_polygon_ids_shp_only": 0,
    "invalid_polygon_ids_gdb_only": 0,
    "all_barrier_ids_match": True,
    "all_reservoir_ids_match": True,
    "all_geos_invalid_ids_match": True,
    "geometries_topologically_valid_for_all_reservoirs": False,
    "automatic_source_repair_performed": False,
    "source_feature_ids_coordinates_or_raw_bytes_exported": False,
    "flood_inundation_or_dam_failure_calibration_proven": False,
    "model_source_admitted": False,
}
