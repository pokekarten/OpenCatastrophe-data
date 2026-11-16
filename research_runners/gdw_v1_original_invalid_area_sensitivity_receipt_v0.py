# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Observed *aggregate-only* GDW v1 invalid-polygon what-if sensitivity.

Original ZIP data were checked against one frozen publisher SHA256 and removed
on the reviewed main runner. This observation compares two repair
counterfactuals using one GEOS engine; it is neither an independent scientific
check nor a geometry correction or CAT-model data admission. Do NOT infer
polygon correctness from equality of these two alternative GEOS outputs.
No original polygons, GDW_IDs, coordinates or provider data are stored here.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_INVALID_AREA_SENSITIVITY_RECEIPT_V0 = {
    "schema_version": "gdw-v1-original-221-invalid-area-counterfactual-aggregate-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "original_source_file_id": 47913754,
    "original_file_sha256": "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "original_archive_bytes": 69745749,
    "trusted_main_source_run_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43975360416",
    "trusted_main_source_commit": "1192c2fe6779553e17371eaefc85d55611050c84",
    "observed_at_utc": "2026-11-16T23:02:08Z",
    "original_reservoir_polygons": 35295,
    "geos_valid_geometry_candidates": 35074,
    "geos_invalid_native_polygons": 221,
    "invalid_polygons_compared_geodesically": 221,
    "invalid_polygons_geodesic_exclusions": 0,
    "methods": ["GEOS make_valid(linework)", "GEOS buffer(0)"],
    "geodetic_area_method": "pyproj WGS84 Geod geodesic area of output polygonal parts; geodesic after planar GEOS overlay",
    "linework_area_km2_sum": 168149.31993856843,
    "buffer_zero_area_km2_sum": 168149.3199385684,
    "absolute_per_feature_area_difference_km2_sum": 3.878319887462567e-11,
    "footprint_symmetric_difference_km2_sum": 0.0,
    "area_weighted_jaccard_of_alternatives": 1.0,
    "material_footprint_disagreement_over_1pct_count": 0,
    "equal_area_but_material_footprint_disagreement_count": 0,
    "paired_barrier_coverage_disagreement": 0,
    "original_native_geometries_topologically_valid_for_all_reservoirs": False,
    "two_alternatives_share_one_geos_engine": True,
    "original_geom_correctness_independently_validated": False,
    "original_geometries_auto_repaired_or_overwritten": False,
    "source_ids_coordinates_raw_geometries_or_archive_published": False,
    "hydraulic_inundation_or_dam_failure_calibration_proven": False,
    "CAT_model_input_admitted": False,
}
