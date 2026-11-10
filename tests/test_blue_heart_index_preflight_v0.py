# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Adversarial, synthetic-only source semantics tests; no Blue Heart data bytes."""

import csv
import tempfile
import unittest
from pathlib import Path

from research_runners.blue_heart_index_preflight_v0 import (
    BlueHeartPreflightError,
    explicit_utc_timestamp,
    inspect_index_csv,
    parse_quality_label,
)


class BlueHeartIndexPreflightTests(unittest.TestCase):
    FIELDS = [
        "locationLatitude", "locationLongitude", "gaugeType", "dataPath",
        "dataQualityFlagsPath", "gaugeParameters", "parameterUnits", "gaugeOwner",
    ]

    def sample(self, **overrides):
        row = {
            "locationLatitude": "50.0",
            "locationLongitude": "-0.2",
            "gaugeType": "Rain",
            "dataPath": "7_rain/SYNTHETIC.csv",
            "dataQualityFlagsPath": "7_rain/SYNTHETIC_quality_flags.csv",
            "gaugeParameters": "Precipitation;Air Temperature",
            "parameterUnits": "mm;°C",
            "gaugeOwner": "Blue Heart",
        }
        row.update(overrides)
        return row

    def make_index(self, rows, headers=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / "synthetic-index.csv"
        with p.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers or self.FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return p

    def test_valid_synthetic_index_returns_only_aggregates(self):
        rows = [
            self.sample(),
            self.sample(
                gaugeType="Highway gully", locationLatitude="51",
                dataPath="6_gully/SYNTHETIC.csv",
                dataQualityFlagsPath="6_gully/SYNTHETIC_quality_flags.csv",
                gaugeParameters="Water Level", parameterUnits="mm",
            ),
        ]
        result = inspect_index_csv(self.make_index(rows), expected_gauges=2)
        self.assertEqual(result["index_rows"], 2)
        self.assertEqual(result["gauge_type_counts"], {"Highway gully": 1, "Rain": 1})
        self.assertFalse(result["timestamp_alignment_approved"])
        self.assertNotIn("50.0", str(result))
        self.assertNotIn("SYNTHETIC.csv", str(result))

    def test_missing_qc_path_rejected(self):
        with self.assertRaisesRegex(BlueHeartPreflightError, "dataQualityFlagsPath"):
            inspect_index_csv(self.make_index([self.sample(dataQualityFlagsPath="")]))

    def test_path_traversal_rejected(self):
        with self.assertRaisesRegex(BlueHeartPreflightError, "relative CSV"):
            inspect_index_csv(self.make_index([self.sample(dataPath="../outside.csv")]))

    def test_parameter_unit_mismatch_rejected(self):
        with self.assertRaisesRegex(BlueHeartPreflightError, "one-to-one"):
            inspect_index_csv(self.make_index([self.sample(parameterUnits="mm")]))

    def test_duplicate_paths_rejected(self):
        with self.assertRaisesRegex(BlueHeartPreflightError, "repeated"):
            inspect_index_csv(self.make_index([self.sample(), self.sample()]))

    def test_missing_required_column_rejected(self):
        fields = [x for x in self.FIELDS if x != "dataQualityFlagsPath"]
        row = self.sample()
        with self.assertRaisesRegex(BlueHeartPreflightError, "required README"):
            inspect_index_csv(self.make_index([{k: row[k] for k in fields}], headers=fields))

    def test_gauge_count_mismatch_rejected(self):
        with self.assertRaisesRegex(BlueHeartPreflightError, "index size"):
            inspect_index_csv(self.make_index([self.sample()]), expected_gauges=497)

    def test_offset_utc_conversion_and_naive_rejection(self):
        self.assertEqual(
            explicit_utc_timestamp("2025-06-30 16:42:43+01:00"),
            "2025-06-30T15:42:43+00:00",
        )
        with self.assertRaisesRegex(BlueHeartPreflightError, "explicit UTC offset"):
            explicit_utc_timestamp("2025-06-30 16:42:43")

    def test_invalid_calendar_and_timezone_values_rejected(self):
        with self.assertRaises(BlueHeartPreflightError):
            explicit_utc_timestamp("2025-02-30 16:42:43+00:00")
        with self.assertRaises(BlueHeartPreflightError):
            explicit_utc_timestamp("2025-06-30 16:42:43+99:00")

    def test_quality_labels(self):
        self.assertEqual(parse_quality_label("1"), ("good", ()))
        self.assertEqual(parse_quality_label("2C"), ("suspect", ("C",)))
        self.assertEqual(parse_quality_label("3BE"), ("bad", ("B", "E")))
        for code in ("", "1A", "0", "4", "3BB", "3Z"):
            with self.subTest(code=code), self.assertRaises(BlueHeartPreflightError):
                parse_quality_label(code)


if __name__ == "__main__":
    unittest.main()
