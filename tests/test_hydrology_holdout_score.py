# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from scripts.hydrology_holdout import build_dresden_holdout_pairs
from scripts.hydrology_holdout_score import HoldoutScoreError, score_dresden_holdout
from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    DRESDEN_HOLDOUT_WINDOW_START_UTC,
    dresden_holdout_glofas_timestamps,
)

UTC = timezone.utc
DAY_SECONDS = 24 * 60 * 60


def complete_perfect_pairing():
    labels = tuple(dresden_holdout_glofas_timestamps())
    source = [
        (
            DRESDEN_HOLDOUT_WINDOW_START_UTC + timedelta(days=index),
            float(1 + (index % 37)),
        )
        for index in range(DRESDEN_HOLDOUT_EXPECTED_DAYS)
    ]
    model = [(label, source[index][1]) for index, label in enumerate(labels)]
    return build_dresden_holdout_pairs(
        pegelonline_observations_utc=source,
        glofas_dis24_values=model,
        sampling_interval_seconds=DAY_SECONDS,
    )


def sparse_pairing(observed_values: list[float], model_values: list[float]):
    if len(observed_values) != len(model_values):
        raise AssertionError("synthetic vectors must have equal length")
    labels = tuple(dresden_holdout_glofas_timestamps())[: len(observed_values)]
    source = [
        (DRESDEN_HOLDOUT_WINDOW_START_UTC + timedelta(days=index), value)
        for index, value in enumerate(observed_values)
    ]
    model = list(zip(labels, model_values))
    return build_dresden_holdout_pairs(
        pegelonline_observations_utc=source,
        glofas_dis24_values=model,
        sampling_interval_seconds=DAY_SECONDS,
    )


class HoldoutScoreTests(unittest.TestCase):
    def test_perfect_nonconstant_holdout_scores_exactly(self) -> None:
        result = score_dresden_holdout(complete_perfect_pairing())
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.expected_days, 1461)
        self.assertEqual(result.valid_days, 1461)
        self.assertEqual(result.valid_fraction, 1.0)
        self.assertEqual(result.modified_kge_prime.status, "pass")
        self.assertAlmostEqual(result.modified_kge_prime.value, 1.0)
        self.assertEqual(result.pearson_correlation.status, "pass")
        self.assertAlmostEqual(result.pearson_correlation.value, 1.0)
        self.assertEqual(result.relative_mean_bias.status, "pass")
        self.assertAlmostEqual(result.relative_mean_bias.value, 0.0)
        self.assertIsNone(result.modified_kge_prime.reason)
        self.assertIsNone(result.pearson_correlation.reason)
        self.assertIsNone(result.relative_mean_bias.reason)

    def test_zero_observed_mean_keeps_defined_pearson_but_blocks_mean_based_metrics(self) -> None:
        pairing = sparse_pairing([-1.0, 1.0], [-1.0, 1.0])
        result = score_dresden_holdout(pairing)
        self.assertEqual(result.status, "not_comparable")
        self.assertEqual(result.valid_days, 2)
        self.assertEqual(result.pearson_correlation.status, "pass")
        self.assertAlmostEqual(result.pearson_correlation.value, 1.0)
        self.assertEqual(result.modified_kge_prime.status, "not_comparable")
        self.assertIsNone(result.modified_kge_prime.value)
        self.assertTrue(result.modified_kge_prime.reason)
        self.assertEqual(result.relative_mean_bias.status, "not_comparable")
        self.assertIsNone(result.relative_mean_bias.value)
        self.assertTrue(result.relative_mean_bias.reason)

    def test_constant_series_preserves_bias_when_correlation_metrics_are_undefined(self) -> None:
        pairing = sparse_pairing([5.0, 5.0], [5.0, 5.0])
        result = score_dresden_holdout(pairing)
        self.assertEqual(result.status, "not_comparable")
        self.assertEqual(result.modified_kge_prime.status, "not_comparable")
        self.assertEqual(result.pearson_correlation.status, "not_comparable")
        self.assertEqual(result.relative_mean_bias.status, "pass")
        self.assertAlmostEqual(result.relative_mean_bias.value, 0.0)

    def test_single_valid_pair_reports_metric_specific_comparability(self) -> None:
        pairing = sparse_pairing([2.0], [3.0])
        result = score_dresden_holdout(pairing)
        self.assertEqual(result.status, "not_comparable")
        self.assertEqual(result.valid_days, 1)
        self.assertEqual(result.modified_kge_prime.status, "not_comparable")
        self.assertEqual(result.pearson_correlation.status, "not_comparable")
        self.assertEqual(result.relative_mean_bias.status, "pass")
        self.assertAlmostEqual(result.relative_mean_bias.value, 0.5)

    def test_pairing_counts_and_fraction_are_revalidated_before_scoring(self) -> None:
        pairing = sparse_pairing([1.0, 2.0], [1.0, 2.0])
        corruptions = (
            pairing._replace(expected_days=1460),
            pairing._replace(valid_days=3),
            pairing._replace(invalid_pair_days=0),
            pairing._replace(valid_fraction=0.5),
            pairing._replace(invalid_observed_days=-1),
        )
        for corrupted in corruptions:
            with self.subTest(corrupted=corrupted), self.assertRaises(HoldoutScoreError):
                score_dresden_holdout(corrupted)

    def test_pairs_must_remain_unique_chronological_and_inside_holdout(self) -> None:
        pairing = sparse_pairing([1.0, 2.0], [1.0, 2.0])
        reversed_pairs = pairing._replace(pairs=tuple(reversed(pairing.pairs)))
        with self.assertRaisesRegex(HoldoutScoreError, "strictly chronological"):
            score_dresden_holdout(reversed_pairs)

        duplicate_pairs = pairing._replace(pairs=(pairing.pairs[0], pairing.pairs[0]))
        with self.assertRaises(HoldoutScoreError):
            score_dresden_holdout(duplicate_pairs)

        outside = pairing.pairs[0]._replace(glofas_timestamp_utc=datetime(2020, 1, 1, tzinfo=UTC))
        outside_pairing = pairing._replace(pairs=(outside, pairing.pairs[1]))
        with self.assertRaisesRegex(HoldoutScoreError, "outside the frozen holdout"):
            score_dresden_holdout(outside_pairing)

    def test_nonfinite_or_type_confused_pair_values_fail_as_contract_errors(self) -> None:
        pairing = sparse_pairing([1.0, 2.0], [1.0, 2.0])
        bad_pairs = (
            pairing.pairs[0]._replace(observed_mean_discharge_m3s=math.nan),
            pairing.pairs[0]._replace(glofas_mean_discharge_m3s=math.inf),
            pairing.pairs[0]._replace(observed_mean_discharge_m3s=True),
        )
        for bad_pair in bad_pairs:
            corrupted = pairing._replace(pairs=(bad_pair, pairing.pairs[1]))
            with self.subTest(bad_pair=bad_pair), self.assertRaises(HoldoutScoreError):
                score_dresden_holdout(corrupted)


if __name__ == "__main__":
    unittest.main()
