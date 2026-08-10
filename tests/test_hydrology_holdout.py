# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from scripts.hydrology_holdout import (
    HoldoutPairError,
    build_dresden_holdout_pairs,
    required_pegelonline_utc_coverage,
)
from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE,
    DRESDEN_HOLDOUT_WINDOW_START_UTC,
    dresden_holdout_glofas_timestamps,
)

UTC = timezone.utc


def full_daily_source() -> list[tuple[datetime, float]]:
    return [
        (DRESDEN_HOLDOUT_WINDOW_START_UTC + timedelta(days=index), 100.0 + (index % 11))
        for index in range(DRESDEN_HOLDOUT_EXPECTED_DAYS)
    ]


def full_daily_model() -> list[tuple[datetime, float]]:
    return [
        (label, 101.0 + (index % 13))
        for index, label in enumerate(dresden_holdout_glofas_timestamps())
    ]


class AcquisitionBoundaryTests(unittest.TestCase):
    def test_required_source_coverage_is_the_exact_physical_utc_holdout(self) -> None:
        start, end = required_pegelonline_utc_coverage()
        self.assertEqual(start, datetime(2020, 1, 1, 0, 0, tzinfo=UTC))
        self.assertEqual(end, datetime(2024, 1, 1, 0, 0, tzinfo=UTC))
        self.assertEqual(end - start, timedelta(days=1461))


class HoldoutPairingTests(unittest.TestCase):
    def test_complete_synthetic_daily_series_builds_all_1461_pairs(self) -> None:
        result = build_dresden_holdout_pairs(
            pegelonline_observations_utc=full_daily_source(),
            glofas_dis24_values=full_daily_model(),
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(result.expected_days, 1461)
        self.assertEqual(result.valid_days, 1461)
        self.assertEqual(result.invalid_pair_days, 0)
        self.assertEqual(result.invalid_observed_days, 0)
        self.assertEqual(result.missing_glofas_days, 0)
        self.assertEqual(result.nonfinite_glofas_days, 0)
        self.assertEqual(result.valid_fraction, 1.0)
        self.assertEqual(len(result.pairs), 1461)
        self.assertEqual(result.pairs[0].glofas_timestamp_utc, datetime(2020, 1, 2, tzinfo=UTC))
        self.assertEqual(result.pairs[-1].glofas_timestamp_utc, datetime(2024, 1, 1, tzinfo=UTC))

    def test_output_is_independent_of_input_iteration_order(self) -> None:
        source = full_daily_source()
        model = full_daily_model()
        forward = build_dresden_holdout_pairs(
            pegelonline_observations_utc=source,
            glofas_dis24_values=model,
            sampling_interval_seconds=24 * 60 * 60,
        )
        reversed_inputs = build_dresden_holdout_pairs(
            pegelonline_observations_utc=reversed(source),
            glofas_dis24_values=reversed(model),
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(forward, reversed_inputs)

    def test_missing_model_day_keeps_fixed_denominator(self) -> None:
        model = full_daily_model()
        missing_label, _value = model.pop(100)
        result = build_dresden_holdout_pairs(
            pegelonline_observations_utc=full_daily_source(),
            glofas_dis24_values=model,
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(result.expected_days, 1461)
        self.assertEqual(result.valid_days, 1460)
        self.assertEqual(result.invalid_pair_days, 1)
        self.assertEqual(result.missing_glofas_days, 1)
        self.assertEqual(result.nonfinite_glofas_days, 0)
        self.assertAlmostEqual(result.valid_fraction, 1460 / 1461)
        self.assertNotIn(missing_label, {pair.glofas_timestamp_utc for pair in result.pairs})

    def test_nonfinite_model_day_is_invalid_not_missing(self) -> None:
        model = full_daily_model()
        label, _value = model[200]
        model[200] = (label, math.nan)
        result = build_dresden_holdout_pairs(
            pegelonline_observations_utc=full_daily_source(),
            glofas_dis24_values=model,
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(result.valid_days, 1460)
        self.assertEqual(result.missing_glofas_days, 0)
        self.assertEqual(result.nonfinite_glofas_days, 1)
        self.assertEqual(result.invalid_pair_days, 1)

    def test_missing_source_day_fails_daily_completeness_without_changing_denominator(self) -> None:
        source = full_daily_source()
        source.pop(300)
        result = build_dresden_holdout_pairs(
            pegelonline_observations_utc=source,
            glofas_dis24_values=full_daily_model(),
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(result.valid_days, 1460)
        self.assertEqual(result.invalid_observed_days, 1)
        self.assertEqual(result.invalid_pair_days, 1)
        self.assertEqual(result.missing_glofas_days, 0)

    def test_observed_and_model_invalidity_can_overlap_on_one_day(self) -> None:
        source = full_daily_source()
        source.pop(400)
        model = full_daily_model()
        label, _value = model[400]
        model[400] = (label, math.inf)
        result = build_dresden_holdout_pairs(
            pegelonline_observations_utc=source,
            glofas_dis24_values=model,
            sampling_interval_seconds=24 * 60 * 60,
        )
        self.assertEqual(result.invalid_observed_days, 1)
        self.assertEqual(result.nonfinite_glofas_days, 1)
        self.assertEqual(result.invalid_pair_days, 1)
        self.assertEqual(result.valid_days, 1460)

    def test_unexpected_or_duplicate_model_labels_fail_closed(self) -> None:
        model = full_daily_model()
        with self.assertRaisesRegex(HoldoutPairError, "unexpected GloFAS"):
            build_dresden_holdout_pairs(
                pegelonline_observations_utc=full_daily_source(),
                glofas_dis24_values=model + [(datetime(2020, 1, 1, tzinfo=UTC), 1.0)],
                sampling_interval_seconds=24 * 60 * 60,
            )

        duplicate = model + [model[0]]
        with self.assertRaisesRegex(HoldoutPairError, "duplicate GloFAS"):
            build_dresden_holdout_pairs(
                pegelonline_observations_utc=full_daily_source(),
                glofas_dis24_values=duplicate,
                sampling_interval_seconds=24 * 60 * 60,
            )

    def test_source_values_outside_physical_holdout_fail_closed(self) -> None:
        for timestamp in (
            DRESDEN_HOLDOUT_WINDOW_START_UTC - timedelta(seconds=1),
            DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE,
        ):
            with self.subTest(timestamp=timestamp), self.assertRaisesRegex(
                HoldoutPairError, "outside frozen physical holdout"
            ):
                build_dresden_holdout_pairs(
                    pegelonline_observations_utc=full_daily_source() + [(timestamp, 1.0)],
                    glofas_dis24_values=full_daily_model(),
                    sampling_interval_seconds=24 * 60 * 60,
                )

    def test_duplicate_source_timestamp_fails_closed(self) -> None:
        source = full_daily_source()
        source.append(source[0])
        with self.assertRaisesRegex(HoldoutPairError, "duplicate PEGELONLINE timestamp"):
            build_dresden_holdout_pairs(
                pegelonline_observations_utc=source,
                glofas_dis24_values=full_daily_model(),
                sampling_interval_seconds=24 * 60 * 60,
            )

    def test_off_grid_source_timestamp_is_rejected_by_window_contract(self) -> None:
        source = full_daily_source()
        source[10] = (source[10][0] + timedelta(seconds=1), source[10][1])
        with self.assertRaisesRegex(HoldoutPairError, "off the frozen sampling grid"):
            build_dresden_holdout_pairs(
                pegelonline_observations_utc=source,
                glofas_dis24_values=full_daily_model(),
                sampling_interval_seconds=24 * 60 * 60,
            )

    def test_model_type_confusion_and_integer_overflow_fail_closed(self) -> None:
        for bad_value in (True, 10**400):
            model = full_daily_model()
            label, _value = model[0]
            model[0] = (label, bad_value)  # type: ignore[list-item]
            with self.subTest(bad_value=type(bad_value).__name__), self.assertRaises(HoldoutPairError):
                build_dresden_holdout_pairs(
                    pegelonline_observations_utc=full_daily_source(),
                    glofas_dis24_values=model,
                    sampling_interval_seconds=24 * 60 * 60,
                )

    def test_model_timestamp_must_be_exact_expected_utc_label(self) -> None:
        model = full_daily_model()
        model[0] = (datetime(2020, 1, 2, 12, 0, tzinfo=UTC), model[0][1])
        with self.assertRaisesRegex(HoldoutPairError, "unexpected GloFAS"):
            build_dresden_holdout_pairs(
                pegelonline_observations_utc=full_daily_source(),
                glofas_dis24_values=model,
                sampling_interval_seconds=24 * 60 * 60,
            )


if __name__ == "__main__":
    unittest.main()
