# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only, offline negative tests for Blue Heart temporal alignment."""

import csv
import tempfile
import unittest
from pathlib import Path

from research_runners.blue_heart_index_preflight_v0 import BlueHeartPreflightError
from research_runners.blue_heart_timestamp_pair_preflight_v0 import inspect_timestamp_pair


class BlueHeartTemporalPairTests(unittest.TestCase):
    def csv_file(self, name, stamps):
        folder = getattr(self, "_tmp", None)
        if folder is None:
            folder = tempfile.TemporaryDirectory()
            self._tmp = folder
            self.addCleanup(folder.cleanup)
        path = Path(folder.name) / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["timestamp", "synthetic"])
            writer.writeheader()
            for stamp in stamps:
                writer.writerow({"timestamp": stamp, "synthetic": "0"})
        return path

    def test_matching_offsets_are_one_instant(self):
        raw = self.csv_file("raw.csv", [
            "2025-06-30 16:42:43+01:00", "2025-06-30 16:43:43+01:00"
        ])
        qc = self.csv_file("quality.csv", [
            "2025-06-30 15:42:43+00:00", "2025-06-30 15:43:43Z"
        ])
        report = inspect_timestamp_pair(raw, qc)
        self.assertEqual(report["matched_timestamp_count"], 2)
        self.assertTrue(report["timestamp_sets_identical"])
        self.assertFalse(report["physical_clock_provenance_verified"])
        self.assertFalse(report["source_bytes_admitted"])
        self.assertNotIn("2025", str(report))

    def test_raw_gully_time_without_offset_rejected(self):
        raw = self.csv_file("raw.csv", ["2025-06-30 16:42:43"])
        qc = self.csv_file("quality.csv", ["2025-06-30 16:42:43+00:00"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "explicit UTC offset"):
            inspect_timestamp_pair(raw, qc)

    def test_qc_time_without_offset_rejected(self):
        raw = self.csv_file("raw.csv", ["2025-06-30 16:42:43+00:00"])
        qc = self.csv_file("quality.csv", ["2025-06-30 16:42:43"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "explicit UTC offset"):
            inspect_timestamp_pair(raw, qc)

    def test_partial_overlap_not_approved_or_imputed(self):
        raw = self.csv_file("raw.csv", ["2025-06-30 16:00:00+00:00",
                                        "2025-06-30 17:00:00+00:00"])
        qc = self.csv_file("quality.csv", ["2025-06-30 17:00:00+00:00",
                                           "2025-06-30 18:00:00+00:00"])
        report = inspect_timestamp_pair(raw, qc)
        self.assertEqual(report["matched_timestamp_count"], 1)
        self.assertEqual(report["raw_without_quality_count"], 1)
        self.assertEqual(report["quality_without_raw_count"], 1)
        self.assertFalse(report["timestamp_alignment_approved"])

    def test_duplicate_utc_instant_even_with_different_offsets_rejected(self):
        raw = self.csv_file("raw.csv", ["2025-06-30 15:00:00+00:00",
                                        "2025-06-30 16:00:00+01:00"])
        qc = self.csv_file("quality.csv", ["2025-06-30 15:00:00+00:00"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "repeated UTC instant"):
            inspect_timestamp_pair(raw, qc)

    def test_unbounded_request_rejected(self):
        raw = self.csv_file("raw.csv", ["2025-06-30 15:00:00+00:00",
                                        "2025-06-30 15:01:00+00:00"])
        qc = self.csv_file("quality.csv", ["2025-06-30 15:00:00+00:00"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "row limit"):
            inspect_timestamp_pair(raw, qc, max_rows=1)

    def test_empty_file_rejected(self):
        raw = self.csv_file("raw.csv", [])
        qc = self.csv_file("quality.csv", ["2025-06-30 15:00:00+00:00"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "no records"):
            inspect_timestamp_pair(raw, qc)

    def test_invalid_calendar_rejected(self):
        raw = self.csv_file("raw.csv", ["2025-02-30 16:42:43+00:00"])
        qc = self.csv_file("quality.csv", ["2025-06-30 16:42:43+00:00"])
        with self.assertRaisesRegex(BlueHeartPreflightError, "invalid offset-bearing timestamp"):
            inspect_timestamp_pair(raw, qc)


if __name__ == "__main__":
    unittest.main()
