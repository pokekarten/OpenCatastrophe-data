# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All tests synthetic; no producer station IDs, positions, or raw data."""
from __future__ import annotations

import unittest

from scripts.gtsm_era5_e_station_id_qa_v0 import (
    PAPER_GTSM_OUTPUT_LOCATIONS,
    StationIdAuditBlocked,
    summarize_native_station_ids,
)


class GtsmStationIdTests(unittest.TestCase):
    def summary(self, ids, **kwargs):
        return summarize_native_station_ids(ids, expected_rows=len(ids), **kwargs)

    def test_unique_contiguous_zero_based_ids(self):
        value = self.summary([0, 1, 2, 3])
        self.assertEqual(value["native_id_span_width"], 4)
        self.assertEqual(value["unrepresented_ids_inside_native_span"], 0)
        self.assertEqual(value["distinct_native_ids"], 4)
        self.assertEqual(value["duplicate_native_id_records"], 0)
        self.assertEqual(value["number_of_internal_gap_runs"], 0)
        self.assertEqual(value["largest_internal_gap_run"], 0)
        self.assertEqual(
            value["zero_based_hypothetical_parent_omissions"]["after_native_id_span"],
            PAPER_GTSM_OUTPUT_LOCATIONS - 4,
        )
        self.assertTrue(value["zero_based_catalogue_index_range_compatible"])
        self.assertFalse(value["one_based_catalogue_index_range_compatible"])
        self.assertFalse(value["parent_catalogue_index_identity_proven"])

    def test_gap_and_order_are_distinct_from_duplicates(self):
        value = self.summary([1, 4, 2, 4, 7])
        self.assertEqual(value["native_id_span_width"], 7)
        self.assertEqual(value["unrepresented_ids_inside_native_span"], 3)
        self.assertEqual(value["duplicate_native_id_records"], 1)
        self.assertEqual(value["nonincreasing_adjacent_id_pairs"], 1)
        self.assertEqual(value["distinct_native_ids"], 4)
        self.assertEqual(value["number_of_internal_gap_runs"], 2)
        self.assertEqual(value["largest_internal_gap_run"], 2)
        self.assertEqual(
            value["zero_based_hypothetical_parent_omissions"]["before_native_id_span"], 1
        )
        self.assertEqual(
            value["zero_based_hypothetical_parent_omissions"]["inside_native_id_span"], 3
        )

    def test_hypothetical_parent_range_is_not_verified_identity(self):
        value = self.summary([PAPER_GTSM_OUTPUT_LOCATIONS - 1,
                              PAPER_GTSM_OUTPUT_LOCATIONS])
        self.assertEqual(value["ids_outside_zero_based_paper_catalogue_range"], 1)
        self.assertEqual(value["ids_outside_one_based_paper_catalogue_range"], 0)
        self.assertFalse(value["zero_based_catalogue_index_range_compatible"])
        self.assertIsNone(value["zero_based_hypothetical_parent_omissions"])
        self.assertTrue(value["one_based_catalogue_index_range_compatible"])
        self.assertFalse(value["paper_output_location_count_same_release_proven"])

    def test_parent_index_gap_partition_sums_only_under_zero_based_hypothesis(self):
        value = self.summary([0, 5, 9])
        parts = value["zero_based_hypothetical_parent_omissions"]
        self.assertEqual(parts["before_native_id_span"], 0)
        self.assertEqual(parts["inside_native_id_span"], 7)
        self.assertEqual(parts["after_native_id_span"], PAPER_GTSM_OUTPUT_LOCATIONS - 10)
        self.assertEqual(sum(parts[k] for k in (
            "before_native_id_span", "inside_native_id_span", "after_native_id_span"
        )), PAPER_GTSM_OUTPUT_LOCATIONS - 3)
        self.assertFalse(value["parent_catalogue_index_identity_proven"])

    def test_thousand_length_internal_gap_reported_without_positions(self):
        value = self.summary([0, 1001])
        self.assertEqual(value["number_of_internal_gap_runs"], 1)
        self.assertEqual(value["largest_internal_gap_run"], 1000)
        self.assertEqual(value["internal_gap_runs_of_at_least_1000_ids"], 1)

    def test_native_fill_does_not_appear_as_valid_station(self):
        value = self.summary([1, 65535, 3], source_fill_value=65535)
        self.assertEqual(value["native_station_id_fill_records"], 1)
        self.assertEqual(value["native_station_id_records"], 2)
        self.assertEqual(value["native_id_span_width"], 3)
        self.assertEqual(value["unrepresented_ids_inside_native_span"], 1)

    def test_all_fill_no_minmax_ids_leaked(self):
        value = self.summary([65535], source_fill_value=65535)
        self.assertEqual(value["distinct_native_ids"], 0)
        self.assertEqual(value["native_id_span_width"], 0)
        self.assertFalse(value["zero_based_catalogue_index_range_compatible"])
        self.assertNotIn("id_min", value)
        self.assertNotIn("id_max", value)
        self.assertFalse(value["individual_station_ids_or_positions_emitted"])

    def test_duplicate_ids_are_counted_without_any_per_id_values(self):
        result = self.summary([5, 5, 5, 5])
        self.assertEqual(result["duplicate_native_id_records"], 3)
        self.assertEqual(result["nonincreasing_adjacent_id_pairs"], 3)
        self.assertNotIn("station_ids", result)
        self.assertNotIn("individual_ids", result)

    def test_fixed_source_dimension_must_match_in_production(self):
        with self.assertRaises(StationIdAuditBlocked):
            summarize_native_station_ids([0])

    def test_non_uint16_ids_rejected(self):
        for bad in (-1, 65536, 1.0, True, None, "1"):
            with self.subTest(v=str(bad)), self.assertRaises(StationIdAuditBlocked):
                self.summary([bad])

    def test_illegal_fill_markers_rejected(self):
        for bad in (-1, 65536, True, 1.0):
            with self.subTest(v=str(bad)), self.assertRaises(StationIdAuditBlocked):
                self.summary([2], source_fill_value=bad)

    def test_invalid_source_budget_rejected(self):
        for limit in (-1, 0, 38_958):
            with self.subTest(limit=limit), self.assertRaises(StationIdAuditBlocked):
                summarize_native_station_ids([], expected_rows=limit)

    def test_no_source_bytes_or_categorical_coastal_claims(self):
        value = self.summary([1, 2])
        self.assertFalse(value["coastal_vs_ocean_station_membership_proven"])
        self.assertFalse(value["geolocation_or_site_join_authorized"])
        self.assertFalse(value["commercial_rights_approved"])
        self.assertFalse(value["cat_model_admitted"])


if __name__ == "__main__":
    unittest.main()
