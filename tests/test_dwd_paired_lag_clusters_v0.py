# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, purely synthetic controls for gust lags and algorithmic event clusters."""
from __future__ import annotations

from datetime import timedelta
import math
import unittest

from scripts.dwd_paired_lag_clusters_v0 import (
    MAX_LAG_STEPS, WindEpisodesBlocked,
    _episodes, _lag_pair, _lag_profile, _pearson, _study,
)
from scripts.dwd_two_station_paired_gust_v0 import START, END


class OriginalTwoStationLagResearchTests(unittest.TestCase):
    def test_correct_positive_lag_sign_direction(self):
        x = [float((i * i + 7 * i) % 43 + 1) for i in range(220)]
        y = [2.0, 4.0] + x[:-2]
        result = _lag_profile(x, y, max_lag_steps=12)
        self.assertEqual(result["maximum_observed_r_unadjusted"], 1.0)
        self.assertEqual(result["maximizing_lags_minutes_ties_preserved"], [20])
        self.assertEqual(len(result["lags_minutes"]), 25)
        self.assertFalse(result["lag_based_physical_propagation_claim"])
        self.assertEqual(
            _lag_pair(x, y, 2),
            (x[:-2], y[2:]),
        )

    def test_zero_lag_matches_pearson_with_identical_observations(self):
        x = [1.0, 3.0, 5.0, 8.0, 13.0]
        self.assertEqual(_pearson(x, x), 1.0)
        self.assertEqual(_lag_profile(x, x, max_lag_steps=0)
                         ["lags_minutes"][0]["pearson_r_unadjusted"], 1.0)

    def test_negative_lag_direction_is_inverse_of_positive_input(self):
        x = [float((i * i + 7 * i) % 43 + 1) for i in range(220)]
        y = [2.0, 4.0] + x[:-2]
        profile = _lag_profile(y, x, max_lag_steps=12)
        self.assertEqual(profile["maximizing_lags_minutes_ties_preserved"], [-20])

    def test_lag_bounds_and_bad_source_lengths_block(self):
        x = [float(i) for i in range(50)]
        with self.assertRaises(WindEpisodesBlocked):
            _lag_profile(x, x, max_lag_steps=MAX_LAG_STEPS + 1)
        with self.assertRaises(WindEpisodesBlocked):
            _lag_profile(x, x[:-1])
        with self.assertRaises(WindEpisodesBlocked):
            _lag_profile([1.0, 2.0], [1.0, 2.0])
        with self.assertRaises(WindEpisodesBlocked):
            _lag_profile(x, x, max_lag_steps=-1)

    def test_pearson_nonfinite_or_zero_variance_blocked(self):
        with self.assertRaises(WindEpisodesBlocked):
            _pearson([1.0] * 5, [1.0, 2.0, 3.0, 4.0, 5.0])
        for value in (float("nan"), float("inf")):
            with self.assertRaises(WindEpisodesBlocked):
                _pearson([1.0, 2.0, value, 4.0], [2.0, 3.0, 4.0, 5.0])

    def test_exceedance_clusters_do_not_conflate_per_timestamp_hit_with_event(self):
        x, y = [0.0] * 30, [0.0] * 30
        x[2] = 16
        x[7] = 16
        x[15] = 16
        y[7] = 18
        y[25] = 17
        report = _episodes(x, y, 15.0, max_gap_slots=6)
        self.assertEqual(report["algorithmic_exceedance_cluster_count"], 3)
        self.assertEqual(report["both_station_hits_in_cluster"], 1)
        self.assertEqual(report["station00003_only_cluster"], 1)
        self.assertEqual(report["station00348_only_cluster"], 1)
        self.assertEqual(report["original_10min_samples_with_either_station_exceedance"], 4)
        self.assertEqual(report["longest_cluster_span_minutes"], 60)
        self.assertFalse(report["physically_independent_storm_events_proven"])

    def test_gap_boundary_and_no_exceedances(self):
        x, y = [0.0] * 20, [0.0] * 20
        x[0] = 16
        x[6] = 16
        x[13] = 16
        self.assertEqual(_episodes(x, y, 15.0)["algorithmic_exceedance_cluster_count"], 2)
        empty = _episodes(x, y, 25.0)
        self.assertEqual(empty["algorithmic_exceedance_cluster_count"], 0)
        self.assertEqual(empty["longest_cluster_span_minutes"], 0)

    def test_bad_cluster_rules_and_negative_source_values_block(self):
        with self.assertRaises(WindEpisodesBlocked):
            _episodes([2.0, 3.0], [1.0], 15)
        with self.assertRaises(WindEpisodesBlocked):
            _episodes([2.0, -999.0], [1.0, 1.0], 15)
        with self.assertRaises(WindEpisodesBlocked):
            _episodes([2.0], [1.0], 15, max_gap_slots=30)
        with self.assertRaises(WindEpisodesBlocked):
            _episodes([2.0], [1.0], float("nan"))

    def test_full_65520_synthetic_integration_qn3_sensitivity(self):
        a, b = {}, {}
        current = START
        i = 0
        while current <= END:
            a[current] = (float((i % 31) + 2), 2 if i < 288 else 3)
            b[current] = (float((i % 29) + 2), 3)
            current += timedelta(minutes=10)
            i += 1
        left = {"shared_samples": a, "shared_missing": 0,
                "shared_qn_counts": {"2": 288, "3": i - 288}}
        right = {"shared_samples": b, "shared_missing": 0,
                 "shared_qn_counts": {"3": i}}
        result = _study(left, right)
        self.assertEqual(result["paired_10min_original_observations"], 65520)
        self.assertEqual(result["qn3_only_zero_lag"]["paired_original_observations_both_qn3"], 65232)
        self.assertEqual(len(result["lag_research"]["lags_minutes"]), 25)
        self.assertEqual(len(result["threshold_hit_clusters"]), 3)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["statistical_significance_inferred"]
                         if "statistical_significance_inferred" in result else
                         result["effective_independent_storm_sample_size_estimated"])
        self.assertNotIn("shared_samples", str(result))


if __name__ == "__main__":
    unittest.main()
