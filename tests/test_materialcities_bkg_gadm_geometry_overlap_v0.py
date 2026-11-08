# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Dependency-free synthetic tests of source polygon overlap decision semantics."""
from __future__ import annotations

import math
import unittest

from research_runners.materialcities_bkg_gadm_geometry_overlap_v0 import (
    GeometryOverlapError,
    MANUAL_REVIEW_IOU_THRESHOLD,
    overlap_metrics,
    summarize_scores,
)


def example_scores():
    source = {
        "01001": overlap_metrics(100.0, 98.0, 97.0),
        "03159": overlap_metrics(100.0, 100.0, 99.9),
        "16063": overlap_metrics(100.0, 101.0, 99.0),
        "16054": overlap_metrics(100.0, 70.0, 69.8),
        "09162": overlap_metrics(100.0, 100.0, 99.7),
    }
    return source


class SourceGeometryResearchGateTests(unittest.TestCase):
    def test_same_polygon_is_100pct_iou(self):
        x = overlap_metrics(100.0, 100.0, 100.0)
        self.assertEqual(x["iou"], 1.0)
        self.assertEqual(x["official_bkg_covered_fraction"], 1.0)
        self.assertEqual(x["gadm_covered_fraction"], 1.0)
        self.assertEqual(x["area_difference_gadm_minus_bkg_km2"], 0.0)

    def test_disjoint_polygon_is_zero_overlap_not_fake_match(self):
        x = overlap_metrics(100.0, 100.0, 0.0)
        self.assertEqual(x["iou"], 0.0)
        self.assertEqual(x["official_bkg_covered_fraction"], 0.0)

    def test_coverage_directions_are_not_interchangeable(self):
        x = overlap_metrics(100.0, 75.0, 75.0)
        self.assertAlmostEqual(x["iou"], 0.75)
        self.assertAlmostEqual(x["official_bkg_covered_fraction"], 0.75)
        self.assertAlmostEqual(x["gadm_covered_fraction"], 1.0)

    def test_imbalanced_source_areas_are_flaggable(self):
        x = overlap_metrics(142.0, 103.0, 101.0)
        self.assertLess(x["iou"], MANUAL_REVIEW_IOU_THRESHOLD)
        self.assertLess(x["official_bkg_covered_fraction"], 0.75)

    def test_empty_or_negative_area_rejected(self):
        for values in ((0, 1, 0), (1, 0, 0), (-1, 1, 0), (1, -1, 0), (1, 1, -1)):
            with self.subTest(values=values), self.assertRaises(GeometryOverlapError):
                overlap_metrics(*values)

    def test_source_nan_or_infinity_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaisesRegex(GeometryOverlapError, "finite"):
                overlap_metrics(value, 1, 0)

    def test_fake_intersection_larger_than_source_rejected(self):
        with self.assertRaisesRegex(GeometryOverlapError, "larger"):
            overlap_metrics(100, 80, 90)

    def test_floating_inputs_only(self):
        with self.assertRaisesRegex(GeometryOverlapError, "finite"):
            overlap_metrics("100", 80, 50)
        with self.assertRaisesRegex(GeometryOverlapError, "finite"):
            overlap_metrics(True, 80, 50)

    def test_summary_retains_manual_review_and_research_no_go(self):
        r = summarize_scores(example_scores(), exact_original=False)
        self.assertEqual(r["unique_2022_ags_with_geometry_compared"], 5)
        self.assertEqual(r["count_manual_review_iou_below_0_95"], 1)
        self.assertEqual(r["count_iou_at_least_0_95"], 4)
        self.assertEqual(r["worst_ags"], "16054")
        self.assertIn("03159", r["source_identity_exceptions_focus"])
        self.assertIn("16063", r["source_identity_exceptions_focus"])
        self.assertTrue(r["research_only"])
        for key in ("full_per_region_geometry_exported",
                    "bkg_gadm_area_join_suitable_for_rva_exposure",
                    "gadm_redistribution_or_commercial_rights_granted",
                    "materialcities_gfa_reallocated",
                    "zensus_2022_2025_insurer_vintage_equivalence_proven",
                    "actual_insured_building_geocoding_proven",
                    "cat_model_input_admitted"):
            self.assertFalse(r[key])

    def test_missing_400_count_fails_original_gate(self):
        with self.assertRaisesRegex(GeometryOverlapError, "400-Kreis"):
            summarize_scores(example_scores())

    def test_original_400_count_still_requires_all_research_focus_regions(self):
        toy = {f"{i:05d}": overlap_metrics(100, 100, 100) for i in range(400)}
        with self.assertRaisesRegex(GeometryOverlapError, "original 400-Kreis"):
            summarize_scores(toy)

    def test_corrupt_iou_fraction_is_blocked(self):
        scores = example_scores()
        scores["16054"]["iou"] = float("nan")
        with self.assertRaisesRegex(GeometryOverlapError, "invalid geometry IoU"):
            summarize_scores(scores, exact_original=False)

    def test_empty_source_scores_blocked(self):
        with self.assertRaisesRegex(GeometryOverlapError, "complete AGS"):
            summarize_scores({}, exact_original=False)

    def test_geographic_area_units_are_explicit_m2_to_km2(self):
        x = overlap_metrics(2_000_000, 2_000_000, 1_500_000)
        self.assertEqual(x["bkg_area_km2"], 2.0)
        self.assertAlmostEqual(x["iou"], 0.6)

    def test_precision_tolerance_keeps_iou_in_unit_interval(self):
        x = overlap_metrics(100, 100, 100 + 1e-7)
        self.assertLessEqual(x["iou"], 1.0)


if __name__ == "__main__":
    unittest.main()
