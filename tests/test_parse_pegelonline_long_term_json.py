# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.parse_pegelonline_long_term_json import (
    EXPECTED_HOLDOUT_GRID_SLOTS,
    PegelonlineLongTermJsonError,
    ParsedObservation,
    canonical_summary_bytes,
    dresden_holdout_observations,
    load_long_term_json_bytes,
    parse_long_term_json_bytes,
    validation_summary,
)

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def encoded(records: list[dict[str, object]]) -> bytes:
    return json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class StrictJsonTests(unittest.TestCase):
    def test_loader_rejects_duplicate_keys_nonfinite_invalid_utf8_and_non_array_root(self) -> None:
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "duplicate JSON key"):
            load_long_term_json_bytes(
                b'[{"timestamp":"2020-01-01T01:00:00+01:00","value":1,"value":2}]'
            )
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "non-finite JSON"):
            load_long_term_json_bytes(b'[{"timestamp":"2020-01-01T01:00:00+01:00","value":NaN}]')
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "valid UTF-8"):
            load_long_term_json_bytes(b"\xff")
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "root must be an array"):
            load_long_term_json_bytes(b'{}')


class LongTermParserTests(unittest.TestCase):
    def test_winter_and_summer_offsets_normalize_and_input_order_does_not_matter(self) -> None:
        observations = parse_long_term_json_bytes(
            encoded(
                [
                    {"timestamp": "2020-07-01T02:15:00+02:00", "value": 20.0},
                    {"timestamp": "2020-01-01T01:00:00+01:00", "value": 10.0},
                ]
            )
        )
        self.assertEqual(
            observations,
            (
                ParsedObservation(datetime(2020, 1, 1, 0, 0, tzinfo=UTC), 10.0),
                ParsedObservation(datetime(2020, 7, 1, 0, 15, tzinfo=UTC), 20.0),
            ),
        )

    def test_spring_forward_source_offsets_preserve_continuous_utc_grid(self) -> None:
        observations = parse_long_term_json_bytes(
            encoded(
                [
                    {"timestamp": "2020-03-29T01:45:00+01:00", "value": 1.0},
                    {"timestamp": "2020-03-29T03:00:00+02:00", "value": 2.0},
                ]
            )
        )
        self.assertEqual(observations[0].timestamp_utc, datetime(2020, 3, 29, 0, 45, tzinfo=UTC))
        self.assertEqual(observations[1].timestamp_utc, datetime(2020, 3, 29, 1, 0, tzinfo=UTC))

    def test_fall_back_repeated_local_hour_is_distinguished_by_offset(self) -> None:
        observations = parse_long_term_json_bytes(
            encoded(
                [
                    {"timestamp": "2020-10-25T02:00:00+01:00", "value": 2.0},
                    {"timestamp": "2020-10-25T02:45:00+02:00", "value": 1.0},
                ]
            )
        )
        self.assertEqual(observations[0].timestamp_utc, datetime(2020, 10, 25, 0, 45, tzinfo=UTC))
        self.assertEqual(observations[1].timestamp_utc, datetime(2020, 10, 25, 1, 0, tzinfo=UTC))

    def test_same_utc_instant_with_different_source_offsets_is_duplicate(self) -> None:
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "duplicate UTC"):
            parse_long_term_json_bytes(
                encoded(
                    [
                        {"timestamp": "2020-01-01T01:00:00+01:00", "value": 1.0},
                        {"timestamp": "2020-01-01T02:00:00+02:00", "value": 2.0},
                    ]
                )
            )

    def test_record_shape_numeric_type_and_grid_fail_closed(self) -> None:
        bad_records = (
            ([{"timestamp": "2020-01-01T01:00:00+01:00", "value": 1.0, "extra": 1}], "exactly"),
            ([{"timestamp": "2020-01-01T01:00:00+01:00"}], "exactly"),
            ([{"timestamp": "2020-01-01T01:00:00+01:00", "value": True}], "numeric"),
            ([{"timestamp": "2020-01-01T01:00:00+01:00", "value": "1"}], "numeric"),
            ([{"timestamp": "2020-01-01T01:07:00+01:00", "value": 1.0}], "15-minute"),
            ([{"timestamp": "2020-01-01T01:00:00", "value": 1.0}], "explicit UTC offset"),
        )
        for records, message in bad_records:
            with self.subTest(message=message), self.assertRaisesRegex(
                PegelonlineLongTermJsonError, message
            ):
                parse_long_term_json_bytes(encoded(records))


class HoldoutSelectionTests(unittest.TestCase):
    def test_holdout_selection_uses_immutable_utc_bounds(self) -> None:
        observations = parse_long_term_json_bytes(
            encoded(
                [
                    {"timestamp": "2019-12-31T23:45:00+01:00", "value": 1.0},
                    {"timestamp": "2020-01-01T01:00:00+01:00", "value": 2.0},
                    {"timestamp": "2024-01-01T00:45:00+01:00", "value": 3.0},
                    {"timestamp": "2024-01-01T01:00:00+01:00", "value": 4.0},
                ]
            )
        )
        selected = dresden_holdout_observations(observations)
        self.assertEqual(
            tuple(observation.timestamp_utc for observation in selected),
            (
                datetime(2020, 1, 1, 0, 0, tzinfo=UTC),
                datetime(2023, 12, 31, 23, 45, tzinfo=UTC),
            ),
        )

    def test_selection_requires_chronological_parsed_observations(self) -> None:
        observations = (
            ParsedObservation(datetime(2020, 1, 1, 0, 15, tzinfo=UTC), 1.0),
            ParsedObservation(datetime(2020, 1, 1, 0, 0, tzinfo=UTC), 2.0),
        )
        with self.assertRaisesRegex(PegelonlineLongTermJsonError, "strictly increasing"):
            dresden_holdout_observations(observations)


class SummaryAndCliTests(unittest.TestCase):
    def test_summary_is_value_free_and_reports_fixed_denominator(self) -> None:
        observations = parse_long_term_json_bytes(
            encoded(
                [
                    {"timestamp": "2020-01-01T01:00:00+01:00", "value": 987654.321},
                    {"timestamp": "2020-01-01T01:15:00+01:00", "value": 123456.789},
                ]
            )
        )
        summary = validation_summary(observations)
        self.assertEqual(summary["holdout_expected_grid_slots"], EXPECTED_HOLDOUT_GRID_SLOTS)
        self.assertEqual(summary["holdout_present_grid_slots"], 2)
        self.assertEqual(
            summary["holdout_missing_grid_slots"],
            EXPECTED_HOLDOUT_GRID_SLOTS - 2,
        )
        serialized = canonical_summary_bytes(summary).decode("utf-8")
        self.assertNotIn("987654.321", serialized)
        self.assertNotIn("123456.789", serialized)
        self.assertNotIn("discharge", serialized.lower())

    def test_cli_outputs_only_canonical_summary_metadata(self) -> None:
        raw = encoded(
            [{"timestamp": "2020-01-01T01:00:00+01:00", "value": 987654.321}]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dresden.json"
            path.write_bytes(raw)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "parse_pegelonline_long_term_json.py"), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("987654.321", result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["holdout_present_grid_slots"], 1)
        self.assertEqual(
            result.stdout.encode("utf-8"),
            canonical_summary_bytes(output) + b"\n",
        )


if __name__ == "__main__":
    unittest.main()
