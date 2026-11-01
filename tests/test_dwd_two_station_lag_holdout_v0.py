# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only leak-proof historical DWD two-station lag holdout tests."""
from __future__ import annotations

from datetime import timedelta
import math
from pathlib import Path
import tempfile
import unittest

from scripts.dwd_two_station_lag_holdout_v0 import (
    DWDHoldoutBlocked, PERIODS, HOLDOUT_MONTHS, _slice_window,
    _fixed_lag_score, _evaluate_split, study, main,
)
from scripts.dwd_two_station_paired_gust_v0 import START, END, PairedWindBlocked


def value(i: int) -> float:
    return 1.0 + ((i * 2347 + (i * i) % 311) % 1031) / 100.0


def make_source_pair(*, validation_different_lag: bool = False):
    first, second = {}, {}
    i, t = 0, START
    start2011 = 52560
    while t <= END:
        first[t] = (value(i), 2 if i < 288 else 3)
        if validation_different_lag and i >= start2011:
            paired_index = i + 2  # Validation prefers -20m, not training +30m.
        else:
            paired_index = i - 3
        second[t] = (value(paired_index), 3)
        t += timedelta(minutes=10)
        i += 1
    return (
        {"shared_samples": first, "shared_missing": 0,
         "shared_qn_counts": {"2": 288, "3": i - 288}},
        {"shared_samples": second, "shared_missing": 0,
         "shared_qn_counts": {"3": i}},
    )


class DWDSeasonalHoldoutTests(unittest.TestCase):
    def test_fixed_study_periods_exact_and_disjoint(self):
        self.assertEqual(PERIODS["discovery_same_season_2010_q1"][2], 12960)
        self.assertEqual(PERIODS["discovery_all_2010"][2], 52560)
        self.assertEqual(PERIODS["holdout_2011_q1"][2], 12960)
        self.assertEqual(sum(month[3] for month in HOLDOUT_MONTHS), 12960)
        self.assertLess(PERIODS["discovery_all_2010"][1],
                        PERIODS["holdout_2011_q1"][0])

    def test_fixed_lag_sign_and_exact_paired_sample_counts(self):
        x = [value(i) for i in range(80)]
        y = [value(i - 3) for i in range(80)]
        result = _fixed_lag_score(x, y, 30)
        self.assertEqual(result["paired_samples"], 77)
        self.assertAlmostEqual(result["pearson_r_unadjusted"], 1.0, places=6)
        self.assertLess(_fixed_lag_score(x, y, 0)["pearson_r_unadjusted"], 0.999)

    def test_validation_lag_is_never_reoptimized_on_holdout(self):
        train_x = [value(i) for i in range(300)]
        train_y = [value(i - 3) for i in range(300)]
        holdout_x = [value(i) for i in range(12960)]
        holdout_y = [value(i + 2) for i in range(12960)]
        q = [3] * 12960
        result = _evaluate_split((train_x, train_y),
                                 (holdout_x, holdout_y, q, q),
                                 training_label="synthetic_discovery")
        self.assertEqual(result["discovery_selected_lag"]["lag_minutes_station00348_relative_to_00003"], 30)
        self.assertEqual(result["holdout_training_selected_lag"]["lag_minutes_station00348_relative_to_00003"], 30)
        self.assertFalse(result["lag_selected_using_holdout_values"])
        self.assertEqual(len(result["holdout_monthly_fixed_lag_checks"]), 3)

    def test_quality_subset_counts_do_not_fake_station_independence(self):
        train_x = [value(i) for i in range(320)]
        train_y = [value(i - 3) for i in range(320)]
        v_x = [value(i) for i in range(12960)]
        v_y = [value(i - 3) for i in range(12960)]
        q1 = [2] * 200 + [3] * (12960 - 200)
        q2 = [3] * 12960
        result = _evaluate_split((train_x, train_y),
                                 (v_x, v_y, q1, q2), training_label="quality_test")
        lag = result["holdout_training_selected_lag"]
        self.assertLess(lag["qn3_only"]["paired_samples"], lag["paired_samples"])
        self.assertFalse(result["physical_travel_time_confirmed"])

    def test_holdout_slices_reject_invalid_original_size(self):
        x = [value(i) for i in range(65520)]
        y = [value(i) for i in range(65520)]
        p = PERIODS["holdout_2011_q1"]
        with self.assertRaises(DWDHoldoutBlocked):
            _slice_window(x[:-1], y, *p)
        with self.assertRaises(DWDHoldoutBlocked):
            _slice_window(x, y, p[0] + timedelta(minutes=5), p[1], p[2])
        with self.assertRaises(DWDHoldoutBlocked):
            _slice_window(x, y, p[0], p[1], p[2] + 1)
        with self.assertRaises(DWDHoldoutBlocked):
            _slice_window(x, y, *p, qx=[3] * 2, qy=[3] * 2)

    def test_fixed_lag_rejects_out_of_scan_and_quality_shortfalls(self):
        x = [value(i) for i in range(40)]
        y = [value(i - 2) for i in range(40)]
        for lag in (125, -130, 200):
            with self.subTest(lag=lag), self.assertRaises(DWDHoldoutBlocked):
                _fixed_lag_score(x, y, lag)
        with self.assertRaises(DWDHoldoutBlocked):
            _fixed_lag_score(x, y, 0, [2] * 40, [3] * 40)

    def test_full_source_pair_seasonal_and_full_year_discovery(self):
        first, second = make_source_pair()
        receipt = study(first, second)
        primary = receipt["primary_same_season_chronological_holdout"]
        secondary = receipt["secondary_full_year_chronological_holdout"]
        self.assertEqual(receipt["full_original_paired_samples"], 65520)
        self.assertEqual(primary["training_original_pairs"], 12960)
        self.assertEqual(secondary["training_original_pairs"], 52560)
        self.assertEqual(primary["holdout_original_pairs"], 12960)
        self.assertEqual(secondary["holdout_original_pairs"], 12960)
        self.assertEqual(primary["discovery_selected_lag"]["lag_minutes_station00348_relative_to_00003"], 30)
        self.assertEqual(primary["holdout_training_selected_lag"]["lag_minutes_station00348_relative_to_00003"], 30)
        self.assertGreater(primary["holdout_delta_r_selected_minus_zero"], 0)
        self.assertEqual(primary["holdout_training_selected_lag"]["paired_samples"], 12957)
        self.assertTrue(receipt["calendar_2010_discovery_precedes_2011_holdout"])
        self.assertFalse(receipt["out_of_sample_physical_hazard_predictive_skill_proven"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertNotIn("shared_samples", str(receipt))

    def test_missing_original_timestamps_in_input_blocks_study(self):
        first, second = make_source_pair()
        del second["shared_samples"][START]
        with self.assertRaises(PairedWindBlocked):
            study(first, second)

    def test_synthetic_archive_cli_is_denied_by_sha(self):
        from tests.test_dwd_two_station_paired_gust_v0 import source
        from scripts.dwd_two_station_paired_gust_v0 import FIRST_FILE, SECOND_FILE
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            x, _ = source(root, FIRST_FILE, "00003")
            y, _ = source(root, SECOND_FILE, "00348")
            self.assertEqual(main(["--first-zip", str(x), "--second-zip", str(y)]), 1)


if __name__ == "__main__":
    unittest.main()
