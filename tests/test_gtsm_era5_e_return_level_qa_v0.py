# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GTSM return-level statistical quality regressions."""
from __future__ import annotations

import unittest

from scripts.gtsm_era5_e_return_level_qa_v0 import (
    ReturnLevelAuditBlocked, audit_return_levels, should_compare_source_fill_value,
)


class GtsmReturnLevelAuditTests(unittest.TestCase):
    def profile(self, best, low, upper):
        return audit_return_levels(best, low, upper, expected_stations=len(best),
                                   expected_periods=len(best[0]))

    def test_normal_ascending_levels_with_bounds(self):
        result = self.profile([[1., 2., 3.]], [[0.5, 1.5, 2.5]], [[1.5, 2.5, 3.5]])
        self.assertEqual(result["numeric_finite_triplets"], 3)
        self.assertEqual(result["stations_without_any_these_quality_flags"], 1)
        self.assertEqual(result["descending_bestfit_adjacent_period_pairs"], 0)
        self.assertFalse(result["cat_model_admitted"])

    def test_missing_and_nonfinite_triplets_counted_without_raw_leak(self):
        report = self.profile([[1., float("nan"), 3.]], [[0.5, 1., 2.5]],
                              [[1.5, 3., float("inf")]])
        self.assertEqual(report["missing_or_nonfinite_triplets"], 2)
        self.assertEqual(report["numeric_finite_triplets"], 1)
        self.assertEqual(report["stations_with_missing_or_nonfinite_triplet"], 1)
        self.assertNotIn("values", report)
        self.assertFalse(report["provider_sea_level_values_redistributed"])

    def test_inverted_bounds_and_best_fit_outside_range(self):
        report = self.profile([[3., 1., 9.]], [[4., 2., 6.]], [[2., 5., 7.]])
        self.assertEqual(report["inverted_uncertainty_interval_cells"], 1)
        self.assertEqual(report["bestfit_below_five_percent_bound_cells"], 2)
        self.assertEqual(report["bestfit_above_ninetyfive_percent_bound_cells"], 2)
        self.assertEqual(report["stations_with_uncertainty_interval_conflict"], 1)

    def test_descending_return_level_bestfit_detected(self):
        report = self.profile([[1., 4., 3.]], [[0., 3., 2.]], [[2., 5., 4.]])
        self.assertEqual(report["descending_bestfit_adjacent_period_pairs"], 1)
        self.assertEqual(report["stations_with_descending_bestfit_periods"], 1)

    def test_nan_breaks_comparison_without_fabricating_zero(self):
        report = self.profile([[1., float("nan"), 0.]], [[0., 1., -1.]], [[2., 3., 1.]])
        self.assertEqual(report["descending_bestfit_adjacent_period_pairs"], 0)
        self.assertEqual(report["missing_or_nonfinite_triplets"], 1)

    def test_exact_epsilon_roundoff_is_not_flagged_as_material_regression(self):
        report = self.profile([[1., 1. - 1e-11]], [[1., 1.]], [[1., 1.]])
        self.assertEqual(report["descending_bestfit_adjacent_period_pairs"], 0)

    def test_station_length_mismatch_blocked(self):
        with self.assertRaises(ReturnLevelAuditBlocked):
            audit_return_levels([[1., 2.]], [[0., 1.]], [], expected_stations=1,
                                expected_periods=2)

    def test_period_length_mismatch_blocked(self):
        with self.assertRaises(ReturnLevelAuditBlocked):
            self.profile([[1., 2.]], [[0.]], [[2., 3.]])

    def test_type_rejection_blocks_boolean_and_str(self):
        for value in (True, "1", None):
            with self.subTest(value=value), self.assertRaises(ReturnLevelAuditBlocked):
                self.profile([[value]], [[0.]], [[2.]])

    def test_bounded_budget_rejects_zero_and_oversized(self):
        for stations, periods in ((0, 1), (1, 9), (38958, 8)):
            with self.subTest(stations=stations, periods=periods):
                with self.assertRaises(ReturnLevelAuditBlocked):
                    audit_return_levels([], [], [], expected_stations=stations,
                                        expected_periods=periods)

    def test_native_nan_missing_marker_allowed_without_false_equality(self):
        self.assertFalse(should_compare_source_fill_value(float("nan")))
        self.assertTrue(should_compare_source_fill_value(-9999.))

    def test_infinite_missing_marker_remains_blocked(self):
        for value in (float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ReturnLevelAuditBlocked):
                should_compare_source_fill_value(value)

    def test_non_float_missing_marker_rejected(self):
        for value in (True, "nan", None):
            with self.subTest(value=value), self.assertRaises(ReturnLevelAuditBlocked):
                should_compare_source_fill_value(value)

    def test_no_loss_or_exposure_claim_from_statistics(self):
        report = self.profile([[1.]], [[0.]], [[2.]])
        self.assertFalse(report["sea_level_to_inundation_transform_performed"])
        self.assertFalse(report["vertical_datum_validated"])
        self.assertFalse(report["commercial_rights_approved"])
        self.assertFalse(report["statistical_fit_validated"])


if __name__ == "__main__":
    unittest.main()
