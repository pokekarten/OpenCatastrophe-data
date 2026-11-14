# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Independent synthetic-only tests; no Blue Heart telemetry, events or claims."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from unittest.mock import patch

from research_runners.blue_heart_synthetic_rain_sewer_lag_v0 import (
    SyntheticRainSewerError, SyntheticSample, SyntheticStorm,
    challenge, demo, main, synthetic_storm, validate_storm,
)


def storm(name="SYNTHETIC_TRAIN", start="2026-04-12T00:00:00+00:00", *,
          lag=2, gain=3.5):
    rainfall = [0.] * 5 + [1., 3., 7., 2., 0.5] + [0.] * 25
    return synthetic_storm(name, start, rainfall, lag_steps=lag, gain=gain)


def mutate_sample(event, i, **kw):
    rows = list(event.samples)
    rows[i] = replace(rows[i], **kw)
    return replace(event, samples=tuple(rows))


class SyntheticRainSewerLagTests(unittest.TestCase):
    def test_two_distinct_synthetic_events_recover_preset_lag(self):
        result = demo()
        self.assertEqual(result["selected_lag_minutes"], 10)
        self.assertEqual(result["calibrated_synthetic_gain_mm_level_per_mm_rain"], 3.5)
        self.assertLess(result["independent_holdout_rmse_mm"], 1e-7)
        self.assertLess(result["training_response_rmse_mm"], 1e-7)
        self.assertFalse(result["original_blue_heart_telemetry_used"])
        self.assertFalse(result["device_timezone_verified"])
        self.assertFalse(result["real_hydraulic_calibration_completed"])
        self.assertFalse(result["cat_event_set_or_insurer_loss_admitted"])
        self.assertEqual(result["candidate_lags_minutes"], [0, 5, 10, 15, 20])

    def test_validation_uses_untouched_holdout_not_refit(self):
        train = storm()
        holdout = storm(name="SYNTHETIC_HOLDOUT", start="2026-04-16T00:00:00Z", gain=4.5)
        result = challenge(train, holdout)
        self.assertEqual(result["calibrated_synthetic_gain_mm_level_per_mm_rain"], 3.5)
        self.assertGreater(result["independent_holdout_rmse_mm"], 0.2)

    def test_training_and_validation_events_must_not_overlap(self):
        sample = storm()
        with self.assertRaisesRegex(SyntheticRainSewerError, "separate"):
            challenge(sample, replace(sample, name="SYNTHETIC_OTHER"))

    def test_unknown_source_material_rejected(self):
        event = replace(storm(), source_class="original_blue_heart")
        with self.assertRaisesRegex(SyntheticRainSewerError, "real or unknown"):
            validate_storm(event)

    def test_ambiguous_local_timestamp_rejected(self):
        event = mutate_sample(storm(), 6, timestamp="2026-04-12 00:30:00")
        with self.assertRaisesRegex(SyntheticRainSewerError, "UTC timestamp"):
            validate_storm(event)

    def test_time_gap_in_five_minute_series_rejected(self):
        event = mutate_sample(storm(), 6, timestamp="2026-04-12T00:40:00+00:00")
        with self.assertRaisesRegex(SyntheticRainSewerError, "time gap"):
            validate_storm(event)

    def test_observation_quality_suspect_rejected(self):
        event = mutate_sample(storm(), 6, rain_qc="2C")
        with self.assertRaisesRegex(SyntheticRainSewerError, "suspect/bad"):
            validate_storm(event)

    def test_observation_quality_bad_rejected(self):
        event = mutate_sample(storm(), 6, sewer_qc="3BE")
        with self.assertRaisesRegex(SyntheticRainSewerError, "suspect/bad"):
            validate_storm(event)

    def test_incorrect_rain_depth_unit_rejected(self):
        event = replace(storm(), rainfall_unit="mm_per_hour")
        with self.assertRaisesRegex(SyntheticRainSewerError, "units"):
            validate_storm(event)

    def test_incorrect_sewer_level_unit_rejected(self):
        event = replace(storm(), sewer_level_unit="mAOD")
        with self.assertRaisesRegex(SyntheticRainSewerError, "units"):
            validate_storm(event)

    def test_nonfinite_and_negative_rainfall_rejected(self):
        for value in (float("nan"), float("inf"), -0.1):
            with self.subTest(value=value), self.assertRaises(SyntheticRainSewerError):
                validate_storm(mutate_sample(storm(), 5, rainfall_depth_mm_per_step=value))

    def test_dry_training_period_cannot_fit_gain(self):
        dry = storm()
        dry = replace(dry, samples=tuple(
            replace(s, rainfall_depth_mm_per_step=0., sewer_level_mm=100.)
            for s in dry.samples
        ))
        with self.assertRaisesRegex(SyntheticRainSewerError, "dry window"):
            validate_storm(dry)

    def test_unstable_baseline_rejected(self):
        event = mutate_sample(storm(), 1, sewer_level_mm=105.)
        with self.assertRaisesRegex(SyntheticRainSewerError, "baseline"):
            validate_storm(event)

    def test_unbounded_fixture_size_rejected(self):
        event = replace(storm(), samples=storm().samples[:5])
        with self.assertRaisesRegex(SyntheticRainSewerError, "unbounded"):
            validate_storm(event)

    def test_fixture_rejects_boolean_and_float_lag_steps(self):
        # bool is a subclass of int and 2.0 compares equal to 2, but
        # neither is a valid discrete five-minute lag index.
        for invalid in (True, False, 2.0, 2.5, "2", -1, 5):
            with self.subTest(lag=invalid):
                with self.assertRaisesRegex(SyntheticRainSewerError, "unsupported synthetic lag"):
                    synthetic_storm(
                        "SYNTHETIC_BAD_LAG", "2026-04-12T00:00:00Z",
                        [0.] * 5 + [1., 2., 3.] + [0.] * 22,
                        lag_steps=invalid,
                    )

    def test_timestamps_with_explicit_offsets_can_normalise(self):
        event = storm(start="2026-04-12T01:00:00+01:00")
        instants, *_ = validate_storm(event)
        self.assertEqual(instants[0].isoformat(), "2026-04-12T00:00:00+00:00")

    def test_cli_is_synthetic_only(self):
        capture = io.StringIO()
        with patch.object(sys, "argv", ["challenge", "--synthetic-demo"]):
            with redirect_stdout(capture):
                self.assertEqual(main(), 0)
        result = json.loads(capture.getvalue())
        self.assertEqual(result["selected_lag_minutes"], 10)
        self.assertFalse(result["original_blue_heart_telemetry_used"])


if __name__ == "__main__":
    unittest.main()
