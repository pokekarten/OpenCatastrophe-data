# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Observed GDW v1.0 native-ring and independent geodesic *numeric* receipt.

Pinned exact original SHP ZIP; aggregate counts only, no coordinates,
GDW_IDs or source assets. Two separate numerical geodesic implementations
were checked on the SAME GEOS-derived repair counterfactual surfaces.
Independent numerical agreement and repeated raw-ring vertices do NOT make
the original source polygons topologically valid or CAT-model-admitted.

Provider: Global Dam Watch v1.0, DOI 10.6084/m9.figshare.25988293.v1,
CC BY 4.0; original full ZIP was held transiently by trusted main CI.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_INDEPENDENT_RING_GEODESIC_RECEIPT_V0 = {
    "schema_version": "gdw-v1-221-original-raw-ring-geographiclib-proj-aggregate-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "source_product_version": "Global Dam Watch v1.0, Figshare 25988293.v1",
    "source_doi": "10.6084/m9.figshare.25988293.v1",
    "source_original_shp_file_id": 47913754,
    "source_original_shp_zip_bytes": 69745749,
    "source_original_shp_zip_sha256":
        "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "original_main_execution":
        "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43987585955",
    "original_main_commit": "b8e93e8c319dd158b89795d26fdd578d34d82dbc",
    "source_observed_utc": "2026-11-17T00:29:49Z",
    "total_original_reservoir_polygons": 35295,
    "native_geos_valid_polygons": 35074,
    "native_geos_invalid_polygons": 221,
    "invalid_polygons_with_exact_nonclosure_raw_ring_vertex_repeats": 221,
    "exact_raw_vertex_repeat_is_complete_topology_validation": False,
    "native_original_invalid_source_vertices_total": 1190727,
    "max_single_invalid_original_polygon_source_vertices": 171901,
    "geographiclib_vs_proj_checked_polygons": 221,
    "geographiclib_vs_proj_domain_exclusions": 0,
    "geographiclib_vs_proj_per_feature_budget_exclusions": 0,
    "geographiclib_vs_proj_total_budget_exclusions": 0,
    "geographiclib_vs_proj_original_vertices_checked": 1190727,
    "original_num_area_implementations": [
        "GeographicLib 2.1 Python PolygonArea WGS84",
        "PROJ/pyproj 3.7.2 Geod WGS84",
    ],
    "both_numeric_methods_share_geos_derived_polygon_geometry": True,
    "max_numeric_geodesic_area_abs_difference_km2": 3.7471181713044643e-10,
    "geographiclib_numeric_mismatch_above_preset_tolerance": False,
    "independent_full_topology_engine_verified": False,
    "source_original_native_invalidities_resolved": False,
    "original_geometries_changed_or_auto_repaired": False,
    "per_id_source_identifiers_geometry_coordinates_or_raw_bytes_published": False,
    "hydraulic_hazard_or_dam_failure_calibration_approved": False,
    "CAT_model_input_admitted": False,
}
