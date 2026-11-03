# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic native GTSM geographic QA tests: no downloaded coordinates."""
from __future__ import annotations

import unittest

from scripts.gtsm_era5_e_coordinate_audit_v0 import (
    CoordinateAuditBlocked, count_native_positions,
)


class GtsmCoordinateTests(unittest.TestCase):
    def count(self, lons, lats):
        return count_native_positions(lons, lats, expected=len(lons))

    def test_unique_valid_positions(self):
        report = self.count([1000, -180000, 180000], [2000, -90000, 90000])
        self.assertEqual(report["valid_range_position_records"], 3)
        self.assertEqual(report["distinct_valid_positions"], 3)
        self.assertFalse(report["exposure_linkage_authorized"])

    def test_missing_both_and_partial_missing(self):
        report = self.count([-999, -999, 1200], [-999, 1000, -999])
        self.assertEqual(report["missing_both_coordinates"], 1)
        self.assertEqual(report["missing_single_coordinate"], 2)
        self.assertEqual(report["valid_range_position_records"], 0)

    def test_rejects_geographically_invalid_bounds_without_claiming_valid_site(self):
        report = self.count([180001, -180001, 1000], [0, 0, 90001])
        self.assertEqual(report["out_of_geographic_bounds"], 3)

    def test_repeated_raw_pair_count(self):
        report = self.count([1000, 1000, 1000, 2000], [2000, 2000, 2000, 3000])
        self.assertEqual(report["repeated_position_records"], 2)
        self.assertEqual(report["distinct_valid_positions"], 2)

    def test_zero_zero_flag_is_only_qa_not_a_missing_marker(self):
        report = self.count([0, -999], [0, -999])
        self.assertEqual(report["records_at_zero_zero"], 1)
        self.assertEqual(report["missing_both_coordinates"], 1)

    def test_no_raw_point_data_emitted(self):
        report = self.count([123456], [-12345])
        self.assertNotIn("lon", report)
        self.assertNotIn("lat", report)
        self.assertFalse(report["raw_coordinate_values_redistributed"])
        self.assertFalse(report["near_coast_or_ocean_classification_done"])

    def test_length_drift_rejected(self):
        with self.assertRaises(CoordinateAuditBlocked):
            count_native_positions([0, 1], [0], expected=2)

    def test_non_integer_coordinate_rejected(self):
        for val in (1.0, True, None, "1000"):
            with self.subTest(val=val):
                with self.assertRaises(CoordinateAuditBlocked):
                    count_native_positions([val], [0], expected=1)

    def test_default_requires_entire_pinned_native_source_dimension(self):
        with self.assertRaises(CoordinateAuditBlocked):
            count_native_positions([0], [0])

    def test_invalid_expected_budget_rejected(self):
        with self.assertRaises(CoordinateAuditBlocked):
            count_native_positions([], [], expected=0)


if __name__ == "__main__":
    unittest.main()
