# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for real n_fields source support; no original downloads."""
from __future__ import annotations

import unittest

from research_runners import swiss_crop_hail_nonzero_exposure_support_v0 as source
from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked


class SwissHailTrueSupportTests(unittest.TestCase):
    def test_three_disjoint_positive_damage_supports(self):
        result = source.classify_original_support(
            [(46.1, 7.1), (46.2, 7.2), (46.3, 7.3)],
            [3.0, 0.0, 1.0],
            [(46.1, 7.1), (46.2, 7.2), (47.0, 8.0)],
            [1, 2], [0, 3, 5], [0, 1, 2, 0, 1],
            [1, 1, 1, 0, 2],
        )
        self.assertEqual(result["source_positions_with_zero_fields"], 1)
        self.assertEqual(result["damage_grid_positions_missing_from_source_coordinates"], 1)
        self.assertEqual(result["damage_grid_positions_with_source_n_fields_zero"], 1)
        self.assertEqual(result["positive_event_grid_damage_cells_total"], 4)
        self.assertEqual(result["positive_event_grid_cells_with_source_n_fields_at_least_one"], 1)
        self.assertEqual(result["positive_event_grid_cells_with_source_n_fields_zero"], 2)
        self.assertEqual(result["positive_event_grid_cells_with_source_coordinate_absent"], 1)
        self.assertEqual(result["positive_event_grid_cells_outside_true_source_exposure"], 3)
        self.assertEqual(result["excluded_observed_positive_fraction"], 0.75)
        self.assertFalse(result["actual_insurer_claims_read"])

    def test_equal_geometry_does_not_imply_crop_exposure(self):
        value = source.classify_original_support(
            [(46, 8), (47, 9)], [0, 1],
            [(46, 8), (47, 9)], [123], [0, 2], [0, 1], [1, 1],
        )
        self.assertEqual(value["damage_grid_positions_missing_from_source_coordinates"], 0)
        self.assertEqual(value["positive_event_grid_cells_outside_true_source_exposure"], 1)

    def test_rounded_key_match_allows_tiny_coordinate_repr_error(self):
        value = source.classify_original_support(
            [(46.000000001, 8.000000001)], [1],
            [(46.000000003, 8.000000003)], [1], [0, 1], [0], [2],
        )
        self.assertEqual(value["positive_event_grid_cells_with_source_n_fields_at_least_one"], 1)

    def test_outside_rows_with_explicit_zero_do_not_inflate_damage(self):
        value = source.classify_original_support(
            [(46, 8)], [0], [(46, 8)], [1], [0, 2], [0, 0], [2, 0],
        )
        self.assertEqual(value["positive_event_grid_damage_cells_total"], 1)
        self.assertEqual(value["positive_event_grid_cells_with_source_n_fields_zero"], 1)

    def test_bad_exposure_counts_rejected(self):
        for bad in (-1, 2.5, float("nan"), float("inf"), 1_000_001):
            with self.subTest(bad=bad):
                with self.assertRaises(Blocked):
                    source.classify_original_support(
                        [(46, 8)], [bad], [(46, 8)], [1], [0, 1], [0], [1]
                    )

    def test_duplicate_exposure_key_and_unreal_coordinates_block(self):
        with self.assertRaisesRegex(Blocked, "non-unique"):
            source.classify_original_support(
                [(46, 8), (46, 8)], [1, 1], [(46, 8)],
                [1], [0, 1], [0], [1],
            )
        with self.assertRaises(Blocked):
            source.key((float("nan"), 8))
        with self.assertRaises(Blocked):
            source.key((91, 8))

    def test_bad_CSR_event_bounds_or_indices_block(self):
        for dates, ptrs, indexes in [
            ([1], [0, 2], [0]),
            ([1], [1, 2], [0]),
            ([1, 2], [0, 2], [0]),
            ([1], [0, 1], [2]),
            (list(range(13)), list(range(14)), list(range(13))),
        ]:
            with self.subTest(dates=dates, ptrs=ptrs, indexes=indexes):
                with self.assertRaises(Blocked):
                    source.classify_original_support(
                        [(46, 8)], [1], [(46, 8)], dates,
                        ptrs, indexes, [1] * len(indexes),
                    )

    def test_empty_or_negative_impact_not_valid(self):
        with self.assertRaises(Blocked):
            source.classify_original_support(
                [(46, 8)], [1], [(46, 8)], [1], [0, 1], [0], [0]
            )
        with self.assertRaises(Blocked):
            source.classify_original_support(
                [(46, 8)], [1], [(46, 8)], [1], [0, 1], [0], [-1]
            )


if __name__ == "__main__":
    unittest.main()
