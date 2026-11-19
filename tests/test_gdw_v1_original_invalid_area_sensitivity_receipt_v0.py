# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen independent original runner evidence; synthetic/offline checks only."""
from __future__ import annotations
import math
import unittest

from research_runners.gdw_v1_original_invalid_area_sensitivity_receipt_v0 import (
    GDW_V1_ORIGINAL_INVALID_AREA_SENSITIVITY_RECEIPT_V0 as SOURCE,
)
from research_runners.gdw_v1_original_spatial_source_receipt_v0 import (
    GDW_V1_ORIGINAL_SPATIAL_RECEIPT_V0 as SPATIAL,
)
from research_runners.gdw_v1_original_crossformat_id_receipt_v0 import (
    GDW_V1_ORIGINAL_CROSSFORMAT_ID_RECEIPT_V0 as CROSSFORMAT,
)
from research_runners.gdw_v1_original_spatial_quality_v0 import PINNED_SHA256


class ObservedOriginalGDWInvalidAreaReceiptTests(unittest.TestCase):
    def test_exact_source_lineage_and_all_221_observed(self):
        self.assertEqual(SOURCE["source_id"], "globaldamwatch.gdw.v1.0")
        self.assertEqual(SOURCE["original_file_sha256"], PINNED_SHA256)
        self.assertEqual(SOURCE["original_file_sha256"], SPATIAL["original_file_sha256"])
        self.assertEqual(SOURCE["original_file_sha256"], CROSSFORMAT["original_shapefile_sha256"])
        self.assertEqual(SOURCE["original_source_file_id"], 47913754)
        self.assertEqual(SOURCE["original_archive_bytes"], 69745749)
        self.assertEqual(SOURCE["trusted_main_source_commit"],
                         "1192c2fe6779553e17371eaefc85d55611050c84")
        self.assertEqual(SOURCE["trusted_main_source_run_url"],
                         "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43975360416")
        self.assertEqual(SOURCE["original_reservoir_polygons"], SPATIAL["reservoir_polygons"])
        self.assertEqual(SOURCE["geos_invalid_native_polygons"], SPATIAL["invalid_reservoir_polygons"])
        self.assertEqual(SOURCE["geos_invalid_native_polygons"],
                         CROSSFORMAT["invalid_polygon_ids_in_both_formats"])
        self.assertEqual(SOURCE["geos_valid_geometry_candidates"], SPATIAL["valid_reservoir_polygons"])
        self.assertEqual(SOURCE["invalid_polygons_compared_geodesically"] +
                         SOURCE["invalid_polygons_geodesic_exclusions"], 221)
        self.assertEqual(SOURCE["invalid_polygons_geodesic_exclusions"], 0)
        self.assertEqual(SOURCE["geos_valid_geometry_candidates"] +
                         SOURCE["geos_invalid_native_polygons"], 35295)

    def test_logged_aggregate_is_finite_consistent_and_nearly_equal(self):
        self.assertEqual(SOURCE["methods"], ["GEOS make_valid(linework)", "GEOS buffer(0)"])
        for field in ("linework_area_km2_sum","buffer_zero_area_km2_sum",
                      "absolute_per_feature_area_difference_km2_sum",
                      "footprint_symmetric_difference_km2_sum",
                      "area_weighted_jaccard_of_alternatives"):
            self.assertTrue(math.isfinite(SOURCE[field]))
        self.assertAlmostEqual(SOURCE["linework_area_km2_sum"], 168149.31993856843, places=7)
        self.assertAlmostEqual(SOURCE["buffer_zero_area_km2_sum"], 168149.3199385684, places=7)
        self.assertLess(SOURCE["absolute_per_feature_area_difference_km2_sum"], 1e-8)
        self.assertLessEqual(abs(SOURCE["linework_area_km2_sum"] -
                                 SOURCE["buffer_zero_area_km2_sum"]),
                             SOURCE["absolute_per_feature_area_difference_km2_sum"] + 1e-8)
        self.assertEqual(SOURCE["footprint_symmetric_difference_km2_sum"], 0)
        self.assertEqual(SOURCE["area_weighted_jaccard_of_alternatives"], 1.0)
        for k in ("material_footprint_disagreement_over_1pct_count",
                  "equal_area_but_material_footprint_disagreement_count",
                  "paired_barrier_coverage_disagreement"):
            self.assertEqual(SOURCE[k], 0)

    def test_agreement_does_not_promote_invalid_source_or_models(self):
        self.assertTrue(SOURCE["two_alternatives_share_one_geos_engine"])
        for flag in ("original_native_geometries_topologically_valid_for_all_reservoirs",
                     "original_geom_correctness_independently_validated",
                     "original_geometries_auto_repaired_or_overwritten",
                     "source_ids_coordinates_raw_geometries_or_archive_published",
                     "hydraulic_inundation_or_dam_failure_calibration_proven",
                     "CAT_model_input_admitted"):
            self.assertFalse(SOURCE[flag])
        self.assertNotIn("original_ids", SOURCE)
        self.assertNotIn("geometries", SOURCE)
        self.assertNotIn("coordinates", SOURCE)


if __name__ == "__main__":
    unittest.main()
