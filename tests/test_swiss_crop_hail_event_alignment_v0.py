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

    def test_source_regression_12_radar_events_24_crop_grid_pairs(self):
        from research_runners.swiss_crop_hail_hdf5_metadata_profile_v0 import (
            CROPS, RESOLUTIONS_KM,
        )
        self.assertEqual(len(CROPS), 6)
        self.assertEqual(len(RESOLUTIONS_KM), 4)
        self.assertEqual(len(CROPS) * len(RESOLUTIONS_KM), 24)


if __name__ == "__main__":
    unittest.main()
