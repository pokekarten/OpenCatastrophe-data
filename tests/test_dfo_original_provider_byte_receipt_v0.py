# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for original DFO file identity and safe receipt output."""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER, DFOPreflightError
from research_runners.dfo_original_provider_byte_receipt_v0 import verify_source_bytes

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerow({
        "﹟": "5512", "Glide ﹟": "", "Start Date": "12/30/23", "End Date": "1/4/24",
        "Country": "Fictional Germany", "Area (km²)": "1,234", "Source": "Synthetic",
        "Main Cause": "Heavy rain", "Fatalities": "0", "Displaced": "",
        "Severity": "1.5", "Flood impact index ": "2.2",
    })
    return buffer.getvalue().encode("utf-8")


def md5(blob):
    return hashlib.md5(blob, usedforsecurity=False).hexdigest()


class DFOOriginalProviderReceiptTests(unittest.TestCase):
    def test_full_receipt_is_aggregate_not_rows_or_admission(self):
        raw = fixture()
        report = verify_source_bytes(
            raw, expected_size=len(raw), expected_publisher_md5=md5(raw),
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(report["reported_event_count"], 1)
        self.assertEqual(report["bytes"], len(raw))
        self.assertEqual(report["events_beyond_publisher_declared_end_year"], 1)
        self.assertTrue(report["publisher_md5_verified"])
        self.assertTrue(report["independently_pinned_sha256_verified"])
        self.assertFalse(report["release_date_consistent_with_original_csv"])
        self.assertFalse(report["original_rows_emitted"])
        self.assertFalse(report["source_admitted"])
        self.assertFalse(report["insured_losses_verified"])
        self.assertNotIn("events", report)
        self.assertNotIn("Fictional Germany", str(report))

    def test_publisher_md5_or_size_rejects_changed_bytes(self):
        raw = fixture()
        with self.assertRaisesRegex(DFOPreflightError, "length mismatch"):
            verify_source_bytes(raw, expected_size=len(raw) + 1, expected_publisher_md5=md5(raw))
        with self.assertRaisesRegex(DFOPreflightError, "MD5"):
            verify_source_bytes(raw, expected_size=len(raw), expected_publisher_md5="0" * 32)
        with self.assertRaisesRegex(DFOPreflightError, "SHA256"):
            verify_source_bytes(raw, expected_size=len(raw), expected_publisher_md5=md5(raw), expected_sha256="0" * 64)

    def test_invalid_csv_is_not_mistaken_for_valid_source(self):
        raw = b"header1,header2\n1,2\n"
        with self.assertRaisesRegex(DFOPreflightError, "headings"):
            verify_source_bytes(raw, expected_size=len(raw), expected_publisher_md5=md5(raw))

    def test_output_never_overwrites_offline_source(self):
        raw = fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "publisher.csv"
            path.write_bytes(raw)
            cmd = [
                sys.executable, str(ROOT / "research_runners/dfo_original_provider_byte_receipt_v0.py"),
                "--file", str(path), "--out", str(path),
            ]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
