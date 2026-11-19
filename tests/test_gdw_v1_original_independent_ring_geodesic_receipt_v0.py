# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline aggregate-only checks of actual original GDW v1 source evidence."""
from __future__ import annotations

import math
import unittest

from research_runners.gdw_v1_original_independent_ring_geodesic_receipt_v0 import (
    GDW_V1_ORIGINAL_INDEPENDENT_RING_GEODESIC_RECEIPT_V0 as R,
)
from research_runners.gdw_v1_original_invalid_area_sensitivity_receipt_v0 import (
    GDW_V1_ORIGINAL_INVALID_AREA_SENSITIVITY_RECEIPT_V0 as PREVIOUS,
)
from research_runners.gdw_v1_original_spatial_source_receipt_v0 import (
    GDW_V1_ORIGINAL_SPATIAL_RECEIPT_V0 as SPATIAL,
)
from research_runners.gdw_v1_original_crossformat_id_receipt_v0 import (
    GDW_V1_ORIGINAL_CROSSFORMAT_ID_RECEIPT_V0 as CROSSFORMAT,
)
from research_runners import gdw_v1_independent_ring_geodesic_v0 as RUNNER


class GDWFullOriginalIndependentReceiptTests(unittest.TestCase):
    def test_frozen_source_hash_and_original_main_execution(self):
        self.assertEqual(R["source_id"], "globaldamwatch.gdw.v1.0")
        self.assertEqual(R["source_original_shp_zip_sha256"],
                         SPATIAL["original_file_sha256"])
        self.assertEqual(R["source_original_shp_zip_sha256"],
                         PREVIOUS["original_file_sha256"])
        self.assertEqual(R["source_original_shp_zip_sha256"],
                         CROSSFORMAT["original_shapefile_sha256"])
        self.assertEqual(R["source_original_shp_file_id"], 47913754)
        self.assertEqual(R["source_original_shp_zip_bytes"], 69745749)
        self.assertEqual(R["original_main_commit"],
                         "b8e93e8c319dd158b89795d26fdd578d34d82dbc")
        self.assertEqual(R["original_main_execution"],
                         "https://github.com/pokekarten/OpenCatastrophe-data/"
                         "actions/runs/43987585955")

    def test_original_population_and_full_numerical_completeness(self):
        self.assertEqual(R["total_original_reservoir_polygons"],
                         SPATIAL["reservoir_polygons"])
        self.assertEqual(R["native_geos_valid_polygons"],
                         SPATIAL["valid_reservoir_polygons"])
        self.assertEqual(R["native_geos_invalid_polygons"],
                         SPATIAL["invalid_reservoir_polygons"])
        self.assertEqual(R["native_geos_invalid_polygons"],
                         CROSSFORMAT["invalid_polygon_ids_in_both_formats"])
        self.assertEqual(R["invalid_polygons_with_exact_nonclosure_raw_ring_vertex_repeats"], 221)
        self.assertEqual(R["geographiclib_vs_proj_checked_polygons"], 221)
        self.assertEqual(R["native_original_invalid_source_vertices_total"],
                         R["geographiclib_vs_proj_original_vertices_checked"])
        self.assertEqual(R["max_single_invalid_original_polygon_source_vertices"], 171901)
        for key in ("geographiclib_vs_proj_domain_exclusions",
                    "geographiclib_vs_proj_per_feature_budget_exclusions",
                    "geographiclib_vs_proj_total_budget_exclusions"):
            self.assertEqual(R[key], 0)
        self.assertEqual(RUNNER.MAX_SOURCE_VERTICES_PER_FEATURE, 180000)
        self.assertEqual(RUNNER.MAX_TOTAL_GEODESIC_SOURCE_VERTICES, 3000000)

    def test_independent_numeric_result_is_bounded_and_finite(self):
        value = R["max_numeric_geodesic_area_abs_difference_km2"]
        self.assertTrue(math.isfinite(value))
        self.assertGreaterEqual(value, 0.0)
        self.assertAlmostEqual(value, 3.7471181713044643e-10, delta=1e-12)
        self.assertLess(value, 1e-6)
        self.assertEqual(len(R["original_num_area_implementations"]), 2)
        self.assertTrue(R["both_numeric_methods_share_geos_derived_polygon_geometry"])
        self.assertFalse(R["geographiclib_numeric_mismatch_above_preset_tolerance"])

    def test_geometric_and_scientific_nonadmission_remains_explicit(self):
        for key in ("exact_raw_vertex_repeat_is_complete_topology_validation",
                    "independent_full_topology_engine_verified",
                    "source_original_native_invalidities_resolved",
                    "original_geometries_changed_or_auto_repaired",
                    "per_id_source_identifiers_geometry_coordinates_or_raw_bytes_published",
                    "hydraulic_hazard_or_dam_failure_calibration_approved",
                    "CAT_model_input_admitted"):
            self.assertFalse(R[key])
        self.assertFalse(PREVIOUS["CAT_model_input_admitted"])
        self.assertNotIn("source_geometries", R)
        self.assertNotIn("original_gdw_ids", R)
        self.assertNotIn("coordinates", R)


if __name__ == "__main__":
    unittest.main()
