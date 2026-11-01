# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only tests for two competing 2D topology repairs."""
import importlib.util
import unittest

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None
if HAS_SHAPELY:
    from shapely.geometry import Point, Polygon
    from research_runners.cems_emns028_topology_repair_challenge_v0 import (
        compare_repair_methods,
    )


@unittest.skipUnless(HAS_SHAPELY, "Shapely suite runs in pinned spatial CI")
class RepairChallengeTests(unittest.TestCase):
    def source(self):
        return Polygon([(2, 2), (4, 4), (2, 4), (4, 2), (2, 2)])

    def test_two_repair_methods_but_no_original_or_model_admission(self):
        result = compare_repair_methods(self.source())
        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual(result["source_coordinates"], 5)
        self.assertFalse(result["source_topology_valid"])
        self.assertFalse(result["invalid_original_algebraic_area_used_as_truth"])
        self.assertFalse(result["building_or_insurer_overlay_authorized"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["derived_repair_polygons_stored"])
        self.assertFalse(result["zero_buffer_challenge"]["candidate_is_model_admitted"])
        self.assertFalse(result["zero_buffer_challenge"]["candidate_is_stored"])
        for c in result["candidates"]:
            self.assertFalse(c["candidate_is_model_admitted"])
            self.assertFalse(c["candidate_is_stored"])

    def test_public_gauge_point_is_context_not_flood_or_claims(self):
        result = compare_repair_methods(self.source(), gauge_control=Point(3, 3.8))
        context = result["gauge_control_repaired_method_context"]
        self.assertEqual(len(context["comparisons"]), 3)
        self.assertFalse(context["point_overlay_is_historical_inundation_proof"])
        self.assertFalse(context["point_overlay_is_claims_or_insured_loss"])
        self.assertFalse(result["model_input_admitted"])

    def test_reject_nonpoint_context(self):
        with self.assertRaisesRegex(ValueError, "one nonempty point"):
            compare_repair_methods(self.source(), gauge_control=self.source())

    def test_reject_valid_polygon(self):
        with self.assertRaisesRegex(ValueError, "pinned invalid original"):
            compare_repair_methods(Polygon([
                (2, 2), (4, 2), (4, 4), (2, 4), (2, 2),
            ]))

    def test_reject_nonpolygon(self):
        with self.assertRaisesRegex(ValueError, "polygon"):
            compare_repair_methods(Point(2, 2))

    def test_reject_empty_polygon(self):
        with self.assertRaisesRegex(ValueError, "pinned invalid original"):
            compare_repair_methods(Polygon())

    def test_methods_never_claim_2016_flood_validation(self):
        result = compare_repair_methods(self.source())
        self.assertFalse(result["aoi04_specific_original_polygon_verified"])
        self.assertFalse(result["source_rights_approved"])
        self.assertFalse(result["methods_have_independent_physical_validation"])
        if result["both_repairs_polygonal_and_comparable"]:
            self.assertIsNotNone(result["candidate_area_absolute_delta_m2"])
            self.assertIsNotNone(result["candidate_symmetric_difference_area_m2"])


if __name__ == "__main__":
    unittest.main()
