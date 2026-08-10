# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from scripts.hydrology_window import (
    HydrologyWindowError,
    aggregate_observed_discharge_for_glofas_dis24,
    assess_source_window,
    expected_observations_per_24h,
    glofas_dis24_window,
    pegelonline_long_term_json_time_to_utc,
)

UTC = timezone.utc


class PegelonlineLongTermJsonTimeTests(unittest.TestCase):
    def test_explicit_winter_and_summer_offsets_convert_to_utc(self) -> None:
        winter = pegelonline_long_term_json_time_to_utc("2026-01-15T12:00:00+01:00")
        summer = pegelonline_long_term_json_time_to_utc("2026-07-15T12:00:00+02:00")
        self.assertEqual(winter, datetime(2026, 1, 15, 11, 0, tzinfo=UTC))
        self.assertEqual(summer, datetime(2026, 7, 15, 10, 0, tzinfo=UTC))

    def test_timezone_naive_long_term_json_timestamp_fails_closed(self) -> None:
        with self.assertRaisesRegex(HydrologyWindowError, "explicit UTC offset"):
            pegelonline_long_term_json_time_to_utc("2026-07-15T12:00:00")

    def test_non_german_legal_offset_fails_closed(self) -> None:
        for value in (
            "2026-07-15T12:00:00+00:00",
            "2026-07-15T12:00:00+03:00",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                HydrologyWindowError, "offset must be \+01:00 or \+02:00"
            ):
                pegelonline_long_term_json_time_to_utc(value)

    def test_invalid_or_subsecond_long_term_json_timestamp_fails_closed(self) -> None:
        with self.assertRaisesRegex(HydrologyWindowError, "ISO-8601"):
            pegelonline_long_term_json_time_to_utc("not-a-timestamp")
        with self.assertRaisesRegex(HydrologyWindowError, "whole seconds"):
            pegelonline_long_term_json_time_to_utc("2026-07-15T12:00:00.001+02:00")


class GlofasWindowTests(unittest.TestCase):
    def test_dis24_timestamp_is_the_end_of_the_half_open_24h_window(self) -> None:
        end = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
        start, returned_end = glofas_dis24_window(end)
        self.assertEqual(start, datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
        self.assertEqual(returned_end, end)

    def test_dis24_window_requires_explicit_utc_and_whole_seconds(self) -> None:
        for value in (
            datetime(2026, 1, 2),
            datetime(2026, 1, 2, tzinfo=timezone(timedelta(hours=1))),
            datetime(2026, 1, 2, 0, 0, 0, 1, tzinfo=UTC),
        ):
            with self.subTest(value=value), self.assertRaises(HydrologyWindowError):
                glofas_dis24_window(value)


class ExpectedObservationTests(unittest.TestCase):
    def test_exact_daily_slot_counts(self) -> None:
        self.assertEqual(expected_observations_per_24h(60), 1440)
        self.assertEqual(expected_observations_per_24h(15 * 60), 96)
        self.assertEqual(expected_observations_per_24h(60 * 60), 24)

    def test_sampling_interval_must_be_positive_exact_divisor(self) -> None:
        for value in (0, -60, True, 1000):
            with self.subTest(value=value), self.assertRaises(HydrologyWindowError):
                expected_observations_per_24h(value)  # type: ignore[arg-type]


class WindowCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 1, 1, tzinfo=UTC)
        self.interval = 15 * 60

    def _observations(self, count: int, *, value: float = 1.0) -> list[tuple[datetime, float]]:
        return [
            (self.start + timedelta(seconds=index * self.interval), value)
            for index in range(count)
        ]

    def test_90_percent_threshold_uses_ceiling_of_expected_slots(self) -> None:
        passing = assess_source_window(
            self._observations(87),
            window_start_utc=self.start,
            sampling_interval_seconds=self.interval,
        )
        self.assertEqual(passing.expected_count, 96)
        self.assertEqual(passing.required_finite_count, 87)
        self.assertEqual(passing.finite_count, 87)
        self.assertAlmostEqual(passing.finite_fraction, 87 / 96)
        self.assertTrue(passing.valid)

        failing = assess_source_window(
            self._observations(86),
            window_start_utc=self.start,
            sampling_interval_seconds=self.interval,
        )
        self.assertEqual(failing.finite_count, 86)
        self.assertFalse(failing.valid)

    def test_present_non_finite_values_do_not_count_as_finite(self) -> None:
        observations = self._observations(96)
        for index in range(10):
            observations[index] = (observations[index][0], math.nan)
        result = assess_source_window(
            observations,
            window_start_utc=self.start,
            sampling_interval_seconds=self.interval,
        )
        self.assertEqual(result.present_count, 96)
        self.assertEqual(result.finite_count, 86)
        self.assertFalse(result.valid)

    def test_missing_slots_are_not_interpolated_or_inferred(self) -> None:
        observations = self._observations(96)
        del observations[20:30]
        result = assess_source_window(
            observations,
            window_start_utc=self.start,
            sampling_interval_seconds=self.interval,
        )
        self.assertEqual(result.present_count, 86)
        self.assertEqual(result.finite_count, 86)
        self.assertFalse(result.valid)

    def test_duplicate_timestamp_fails_closed(self) -> None:
        observations = self._observations(2)
        observations.append(observations[0])
        with self.assertRaisesRegex(HydrologyWindowError, "duplicate source timestamp"):
            assess_source_window(
                observations,
                window_start_utc=self.start,
                sampling_interval_seconds=self.interval,
            )

    def test_off_grid_timestamp_fails_closed(self) -> None:
        observations = [(self.start + timedelta(minutes=1), 1.0)]
        with self.assertRaisesRegex(HydrologyWindowError, "off the frozen sampling grid"):
            assess_source_window(
                observations,
                window_start_utc=self.start,
                sampling_interval_seconds=self.interval,
            )

    def test_end_boundary_belongs_to_next_window_and_is_rejected(self) -> None:
        observations = [(self.start + timedelta(days=1), 1.0)]
        with self.assertRaisesRegex(HydrologyWindowError, "outside the 24-hour window"):
            assess_source_window(
                observations,
                window_start_utc=self.start,
                sampling_interval_seconds=self.interval,
            )

    def test_utc_window_boundary_is_required_and_never_inferred(self) -> None:
        naive_start = datetime(2026, 1, 1)
        with self.assertRaisesRegex(HydrologyWindowError, "timezone-aware UTC"):
            assess_source_window([], window_start_utc=naive_start, sampling_interval_seconds=self.interval)

        cet_start = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1)))
        with self.assertRaisesRegex(HydrologyWindowError, "timezone-aware UTC"):
            assess_source_window([], window_start_utc=cet_start, sampling_interval_seconds=self.interval)

    def test_type_confusion_and_numeric_overflow_fail_closed(self) -> None:
        with self.assertRaisesRegex(HydrologyWindowError, "numeric and not boolean"):
            assess_source_window(
                [(self.start, True)],
                window_start_utc=self.start,
                sampling_interval_seconds=self.interval,
            )
        with self.assertRaisesRegex(HydrologyWindowError, "represented safely"):
            assess_source_window(
                [(self.start, 10**400)],
                window_start_utc=self.start,
                sampling_interval_seconds=self.interval,
            )


class ObservedDischargeAggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 1, 1, tzinfo=UTC)
        self.end = self.start + timedelta(days=1)
        self.interval = 15 * 60

    def _full_day(self) -> list[tuple[datetime, float]]:
        return [
            (self.start + timedelta(seconds=index * self.interval), float(index + 1))
            for index in range(96)
        ]

    def test_valid_window_uses_equal_weight_mean_of_finite_grid_samples(self) -> None:
        observations = self._full_day()
        for index in range(9):
            observations[index] = (observations[index][0], math.nan)
        result = aggregate_observed_discharge_for_glofas_dis24(
            observations,
            glofas_timestamp_utc=self.end,
            sampling_interval_seconds=self.interval,
        )
        self.assertTrue(result.completeness.valid)
        self.assertEqual(result.completeness.finite_count, 87)
        self.assertEqual(result.window_start_utc, self.start)
        self.assertEqual(result.window_end_utc, self.end)
        self.assertAlmostEqual(result.mean_discharge_m3s, sum(range(10, 97)) / 87)

    def test_invalid_completeness_returns_no_daily_observed_value(self) -> None:
        observations = self._full_day()[:86]
        result = aggregate_observed_discharge_for_glofas_dis24(
            observations,
            glofas_timestamp_utc=self.end,
            sampling_interval_seconds=self.interval,
        )
        self.assertFalse(result.completeness.valid)
        self.assertIsNone(result.mean_discharge_m3s)

    def test_end_timestamp_is_never_included_in_previous_daily_mean(self) -> None:
        observations = self._full_day()
        observations.append((self.end, 999.0))
        with self.assertRaisesRegex(HydrologyWindowError, "outside the 24-hour window"):
            aggregate_observed_discharge_for_glofas_dis24(
                observations,
                glofas_timestamp_utc=self.end,
                sampling_interval_seconds=self.interval,
            )

    def test_mean_accumulation_overflow_fails_closed(self) -> None:
        observations = [
            (self.start + timedelta(seconds=index * self.interval), 1e308)
            for index in range(96)
        ]
        with self.assertRaisesRegex(HydrologyWindowError, "sum must remain finite"):
            aggregate_observed_discharge_for_glofas_dis24(
                observations,
                glofas_timestamp_utc=self.end,
                sampling_interval_seconds=self.interval,
            )


if __name__ == "__main__":
    unittest.main()
