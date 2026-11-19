# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: coast-prefix versus other producer family return-level QA."""
from __future__ import annotations

import math
import unittest

from scripts.gtsm_era5_e_author_family_return_qa_v0 import (
    GtsmFamilyReturnAuditBlocked,
    audit_return_levels_by_author_name_family,
    FAMILIES, COUNTER_FIELDS, require_verified_author_station_join,
)


def consistent_matrices(size: int):
    best = [[float(k + i) for i in range(8)] for k in range(size)]
    lower = [[v - 0.5 for v in row] for row in best]
    upper = [[v + 0.5 for v in row] for row in best]
    return best, lower, upper


def authors(ids, families):
    return {
        key: (0, 0, group) for key, group in zip(ids, families)
    }


class GtsmCoastalReturnQualityTests(unittest.TestCase):
    def test_coast_upper_crossing_grid_lower_crossing_and_observation_nonfinite(self):
        ids = [5, 6, 9, 10, 12, 15]
        matrix = consistent_matrices(6)
        best, low, high = matrix
        high[1][1] = best[1][1] - 0.1
        low[2][0] = best[2][0] + 0.1
        best[3][0] = math.nan
        catalogue = authors(ids, [
            "coast_name_prefix",
            "coast_name_prefix",
            "regular_grid_name_prefix",
            "observation_name_prefix",
            "other_name_prefix",
            "other_name_prefix",
        ])
        result = audit_return_levels_by_author_name_family(
            ids, matrix, catalogue, expected_rows=6
        )
        stats = result["station_family_quality_counts"]
        self.assertEqual(stats["coast_name_prefix"]["original_station_rows"], 2)
        self.assertEqual(stats["coast_name_prefix"]["bestfit_above_ninetyfive_percent_bound_cells"], 1)
        self.assertEqual(stats["coast_name_prefix"]["stations_with_uncertainty_interval_conflict"], 1)
        self.assertEqual(stats["regular_grid_name_prefix"]["bestfit_below_five_percent_bound_cells"], 1)
        self.assertEqual(stats["observation_name_prefix"]["missing_or_nonfinite_triplets"], 1)
        self.assertEqual(stats["other_name_prefix"]["stations_without_any_these_quality_flags"], 2)
        self.assertEqual(result["source_global_quality_counts"]["numeric_finite_triplets"], 47)
        for field in COUNTER_FIELDS:
            self.assertEqual(
                sum(group[field] for group in stats.values()),
                result["source_global_quality_counts"][field],
            )
        self.assertFalse(result["full_source_levels_station_ids_and_coordinates_emitted"])
        self.assertFalse(result["cat_model_admitted"])
        self.assertFalse(result["physical_coastal_cat_model_validated"])

    def test_empty_families_have_bounded_zero_counts(self):
        result = audit_return_levels_by_author_name_family(
            [5], consistent_matrices(1),
            authors([5], ["coast_name_prefix"]), expected_rows=1
        )
        for category in FAMILIES[1:]:
            self.assertEqual(result["station_family_quality_counts"][category], {
                counter: 0 for counter in COUNTER_FIELDS
            })
        self.assertTrue(result["native_2p5_97p5_versus_named_5_95_confidence_semantics_unresolved"])

    def test_unrecognized_family_fails_closed(self):
        with self.assertRaises(GtsmFamilyReturnAuditBlocked):
            audit_return_levels_by_author_name_family(
                [3], consistent_matrices(1),
                {3: (0, 0, "not_a_gtsm_family")}, expected_rows=1
            )

    def test_missing_author_match_and_duplicate_ids_fail_closed(self):
        for ids, catalogue in (
            ([1], authors([2], ["coast_name_prefix"])),
            ([1, 1], authors([1], ["coast_name_prefix"])),
        ):
            with self.subTest(ids=ids), self.assertRaises(GtsmFamilyReturnAuditBlocked):
                audit_return_levels_by_author_name_family(
                    ids, consistent_matrices(len(ids)), catalogue, expected_rows=len(ids)
                )

    def test_bounded_numeric_matrix_and_dimension_guard(self):
        for ids, matrix, limit in (
            ([1], ([], [], []), 1),
            ([1], ([["oops"] * 8], [[0.0] * 8], [[0.0] * 8]), 1),
            ([1], consistent_matrices(1), 38958),
            ([1], consistent_matrices(1), 0),
            ([True], consistent_matrices(1), 1),
        ):
            with self.subTest(limit=limit, ids=ids), self.assertRaises(GtsmFamilyReturnAuditBlocked):
                audit_return_levels_by_author_name_family(
                    ids, matrix, authors([1], ["coast_name_prefix"]), expected_rows=limit
                )

    def test_source_name_prefix_not_independent_coast_hazard_proof(self):
        result = audit_return_levels_by_author_name_family(
            [0], consistent_matrices(1),
            authors([0], ["coast_name_prefix"]), expected_rows=1
        )
        self.assertTrue(
            result["producer_station_prefix_is_not_geographic_coast_or_flood_footprint_proof"]
        )
        self.assertTrue(
            result["bestfit_outside_reported_interval_not_necessarily_source_error"]
        )
        self.assertFalse(result["source_commercial_rights_approved"])


class OriginalStationCoordinateGateTests(unittest.TestCase):
    """All values are invented aggregate receipts, not publisher station data."""

    @staticmethod
    def receipt(rows=2):
        return {
            "matching_native_station_ids": rows,
            "original_native_station_ids_absent_in_author_catalogue": 0,
            "matching_ids_with_exact_quantized_coordinates": rows - 1,
            "matching_ids_within_one_0p001_degree_packed_unit": 1,
            "matching_ids_with_coordinate_conflict_larger_than_0p001_degree": 0,
            "source_source_parent_catalogue_join_for_all_rows_proven": True,
        }

    def test_exact_and_one_rounding_unit_match_are_accepted(self):
        self.assertIsNone(require_verified_author_station_join(self.receipt(), expected_rows=2))

    def test_coordinate_conflict_blocks_even_with_complete_ids(self):
        rec = self.receipt()
        rec["matching_ids_with_coordinate_conflict_larger_than_0p001_degree"] = 1
        with self.assertRaises(GtsmFamilyReturnAuditBlocked):
            require_verified_author_station_join(rec, expected_rows=2)

    def test_false_or_missing_identity_attestation_blocks(self):
        for value in (False, None, "true", 1):
            with self.subTest(value=value):
                rec = self.receipt()
                rec["source_source_parent_catalogue_join_for_all_rows_proven"] = value
                with self.assertRaises(GtsmFamilyReturnAuditBlocked):
                    require_verified_author_station_join(rec, expected_rows=2)

    def test_missing_source_id_blocks(self):
        rec = self.receipt()
        rec["original_native_station_ids_absent_in_author_catalogue"] = 1
        with self.assertRaises(GtsmFamilyReturnAuditBlocked):
            require_verified_author_station_join(rec, expected_rows=2)

    def test_tally_mismatch_blocks_even_when_attestation_true(self):
        rec = self.receipt()
        rec["matching_ids_with_exact_quantized_coordinates"] = 0
        with self.assertRaises(GtsmFamilyReturnAuditBlocked):
            require_verified_author_station_join(rec, expected_rows=2)

    def test_boolean_integer_and_missing_counts_block(self):
        for value in (True, "2", None):
            with self.subTest(value=value):
                rec = self.receipt()
                rec["matching_native_station_ids"] = value
                with self.assertRaises(GtsmFamilyReturnAuditBlocked):
                    require_verified_author_station_join(rec, expected_rows=2)
        rec = self.receipt()
        del rec["matching_native_station_ids"]
        with self.assertRaises(GtsmFamilyReturnAuditBlocked):
            require_verified_author_station_join(rec, expected_rows=2)

    def test_unbounded_or_malformed_receipt_blocks(self):
        for expected in (0, 38958, True):
            with self.subTest(expected=expected):
                with self.assertRaises(GtsmFamilyReturnAuditBlocked):
                    require_verified_author_station_join(self.receipt(), expected_rows=expected)
        for receipt in (None, [], "joined"):
            with self.subTest(receipt=receipt):
                with self.assertRaises(GtsmFamilyReturnAuditBlocked):
                    require_verified_author_station_join(receipt, expected_rows=2)



if __name__ == "__main__":
    unittest.main()
