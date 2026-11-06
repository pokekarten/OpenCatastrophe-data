# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure offline tests: selected original event dates never become annual counts."""
from __future__ import annotations

import unittest
from research_runners import swiss_crop_hail_event_alignment_v0 as audit


class SwissHailEventJoinTests(unittest.TestCase):
    def test_accepted_true_subset_of_radar_dates(self):
        source = [100, 200, 300, 400]
        self.assertTrue(audit.verify_dates_subset(source, [100, 300]))
        self.assertTrue(audit.verify_dates_subset(source, source))

    def test_unknown_damage_event_rejected(self):
        self.assertFalse(audit.verify_dates_subset([100, 200], [100, 201]))

    def test_duplicate_events_rejected(self):
        self.assertFalse(audit.verify_dates_subset([100, 200, 300], [100, 100]))
        self.assertFalse(audit.verify_dates_subset([100, 100, 200], [100]))

    def test_empty_damage_event_set_rejected(self):
        self.assertFalse(audit.verify_dates_subset([100, 200], []))

    def test_damage_coordinate_subset_may_have_fewer_rows_than_exposure(self):
        summary = audit.coordinate_key_coverage(
            [(46.3, 8.2), (46.4, 8.3), (46.5, 8.4)],
            [(46.5, 8.4), (46.3, 8.2)],
        )
        self.assertTrue(summary["full_damage_coordinate_key_coverage"])
        self.assertEqual(summary["damage_positions_matching_exposure_key"], 2)
        self.assertEqual(summary["source_unique_key_count"], 3)

    def test_missing_damage_coordinate_is_not_silently_joined(self):
        summary = audit.coordinate_key_coverage(
            [(46.3, 8.2), (46.4, 8.3)], [(46.3, 8.2), (50, 10)],
        )
        self.assertEqual(summary["damage_positions_without_exposure_key"], 1)
        self.assertFalse(summary["full_damage_coordinate_key_coverage"])

    def test_duplicate_source_positions_invalidate_key_join(self):
        summary = audit.coordinate_key_coverage(
            [(46.3, 8.2), (46.3, 8.2)], [(46.3, 8.2)],
        )
        self.assertEqual(summary["source_duplicate_key_count"], 1)
        self.assertFalse(summary["full_damage_coordinate_key_coverage"])

    def test_duplicate_damage_keys_do_not_pass_full_one_to_one_coverage(self):
        # Every damage row can match an exposure key while two damage rows
        # still collide after rounding. Such a join is not one-to-one.
        summary = audit.coordinate_key_coverage(
            [(46.3, 8.2), (46.4, 8.3)],
            [(46.3, 8.2), (46.3, 8.2), (46.4, 8.3)],
        )
        self.assertEqual(summary["damage_positions_without_exposure_key"], 0)
        self.assertEqual(summary["damage_duplicate_key_count"], 1)
        self.assertEqual(summary["damage_unique_key_count"], 2)
        self.assertFalse(summary["full_damage_coordinate_key_coverage"])

    def test_rounding_collision_on_damage_side_is_not_full_coverage(self):
        summary = audit.coordinate_key_coverage(
            [(46.3, 8.2), (46.4, 8.3)],
            [(46.30000001, 8.2), (46.30000002, 8.2)],
        )
        self.assertEqual(summary["damage_duplicate_key_count"], 1)
        self.assertEqual(summary["damage_positions_without_exposure_key"], 0)
        self.assertFalse(summary["full_damage_coordinate_key_coverage"])

    def test_unmatched_grid_positions_with_actual_positive_impacts(self):
        result = audit.unmatched_positive_impact_summary(
            [(46.3, 8.2), (46.4, 8.3)],
            [(46.3, 8.2), (47.0, 9.0), (47.1, 9.1)],
            [0, 1, 1, 2, 2], [12, 0, 3, 1, 2],
        )
        self.assertEqual(result["unmatched_damage_grid_positions"], 2)
        self.assertEqual(result["unmatched_positions_with_positive_impact"], 2)
        self.assertEqual(result["positive_impact_matrix_cells_on_unmatched_positions"], 3)

    def test_extra_zero_damage_grid_positions_do_not_imply_actual_impacts(self):
        result = audit.unmatched_positive_impact_summary(
            [(46.3, 8.2)], [(46.3, 8.2), (47.0, 9.0)],
            [0, 1], [1, 0],
        )
        self.assertEqual(result["unmatched_damage_grid_positions"], 1)
        self.assertEqual(result["positive_impact_matrix_cells_on_unmatched_positions"], 0)

    def test_source_pair_summary_counts_actual_positive_cells_not_stored_zeros(self):
        # Sparse CSR matrices may contain explicit zero entries, not actual impacts.
        import numpy as np
        exposure = {"exposures": {
            "block0_items": np.asarray([b"latitude", b"longitude"]),
            "block0_values": np.asarray([[46.3, 8.2], [46.4, 8.3]]),
            "axis1": np.asarray([0, 1]),
        }}
        damage = {
            "coord_exp": np.asarray([[46.3, 8.2], [47.0, 9.0]]),
            "date": np.asarray([100, 200]),
            "imp_mat/indptr": np.asarray([0, 2, 3]),
            "imp_mat/indices": np.asarray([0, 1, 1]),
            "imp_mat/data": np.asarray([2.5, 0.0, 3.0]),
        }
        summary = audit.source_pair_summary(exposure, damage, [100, 200, 300])
        self.assertEqual(summary["stored_impact_matrix_cells"], 3)
        self.assertEqual(summary["nonzero_impact_cells"], 2)
        self.assertEqual(summary["unmatched_positions_with_positive_impact"], 1)
        self.assertEqual(summary["positive_impact_matrix_cells_on_unmatched_positions"], 1)
        self.assertEqual(
            [r["positive_impact_matrix_cells_on_unmatched_positions"]
             for r in summary["positive_impact_coverage_by_source_event"]],
            [0, 1]
        )
        self.assertFalse(summary["full_damage_coordinate_key_coverage"])

    def test_event_wise_positive_unmatched_cells_are_not_annual_claims(self):
        rows = audit.unmatched_positive_impacts_by_event(
            [(46.3, 8.2), (46.4, 8.3)],
            [(46.3, 8.2), (47.0, 9.0), (47.1, 9.1)],
            [100, 200, 300], [0, 3, 5, 7],
            [0, 1, 1, 2, 0, 1, 2], [10, 0, 3, 4, 1, 0, 5],
        )
        self.assertEqual([row["event_ordinal"] for row in rows], [100, 200, 300])
        self.assertEqual([row["positive_impact_matrix_cells"] for row in rows],
                         [2, 2, 1])
        self.assertEqual(
            [row["positive_impact_matrix_cells_on_unmatched_positions"]
             for row in rows], [1, 1, 1]
        )
        self.assertEqual(
            [row["unmatched_positions_with_positive_impact"] for row in rows],
            [1, 1, 1]
        )
        # The same missing position in multiple study events stays multiple
        # matrix cells, never an invented number of distinct insured claims.
        self.assertEqual(sum(
            row["positive_impact_matrix_cells_on_unmatched_positions"]
            for row in rows
        ), 3)

    def test_event_wise_empty_stored_rows_are_zero(self):
        rows = audit.unmatched_positive_impacts_by_event(
            [(46.3, 8.2)], [(47.0, 9.0)],
            [100, 200], [0, 0, 1], [0], [0],
        )
        self.assertEqual([r["positive_impact_matrix_cells"] for r in rows], [0, 0])
        self.assertEqual([r["unmatched_positions_with_positive_impact"] for r in rows],
                         [0, 0])

    def test_source_regression_12_radar_events_24_crop_grid_pairs(self):
        from research_runners.swiss_crop_hail_hdf5_metadata_profile_v0 import (
            CROPS, RESOLUTIONS_KM,
        )
        self.assertEqual(len(CROPS), 6)
        self.assertEqual(len(RESOLUTIONS_KM), 4)
        self.assertEqual(len(CROPS) * len(RESOLUTIONS_KM), 24)


if __name__ == "__main__":
    unittest.main()
