# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only DFO provider-byte preflight regression tests."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.dfo_floodrecords_csv_preflight_v0 import (
    DFOPreflightError,
    HEADER,
    parse_dfo_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def example_row(**overrides):
    row = {
        "﹟": "9001", "Glide ﹟": "", "Start Date": "12/30/23",
        "End Date": "1/4/24", "Country": "Syntheticland, Testisland",
        "Area (km²)": "1,234", "Source": "Synthetic",
        "Main Cause": "Heavy rain", "Fatalities": "0", "Displaced": "",
        "Severity": "1.5", "Flood impact index ": "5.2",
    }
    row.update(overrides)
    return row


def csv_bytes(rows, columns=HEADER, *, bom=False):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return (b"\xef\xbb\xbf" if bom else b"") + stream.getvalue().encode("utf-8")


class DFOPreflightTests(unittest.TestCase):
    def test_original_header_contract_and_source_version_anomaly(self):
        blob = csv_bytes([example_row()], bom=True)
        result = parse_dfo_csv(blob)
        self.assertEqual(result["reported_event_count"], 1)
        self.assertEqual(result["event_rows_reaching_beyond_declared_end_year"], 1)
        self.assertFalse(result["published_release_end_year_consistent_with_csv"])
        self.assertEqual(result["source_csv_sha256"], hashlib.sha256(blob).hexdigest())
        e = result["events"][0]
        self.assertEqual(e["start_date"], "2023-12-30")
        self.assertEqual(e["end_date"], "2024-01-04")
        self.assertEqual(e["country_text_unparsed"], "Syntheticland, Testisland")
        self.assertEqual(e["reported_area_affected_km2_not_inundation"], "1234")
        self.assertIsNone(e["reported_displaced"])
        self.assertEqual(e["reported_fatalities"], 0)
        self.assertFalse(result["insured_losses_observed"])
        self.assertFalse(result["model_source_admission_approved"])

    def test_strict_original_date_pivot_and_calendar_validation(self):
        blob = csv_bytes([example_row(**{"Start Date": "1/1/85", "End Date": "1/2/85"})])
        self.assertEqual(parse_dfo_csv(blob)["observed_first_start_date"], "1985-01-01")
        for broken in ("2024-01-01", "1/1/2024", "2/30/24", "1/1/70", "٠١/١/٢٤"):
            with self.subTest(broken=broken):
                blob = csv_bytes([example_row(**{"Start Date": broken})])
                with self.assertRaises(DFOPreflightError):
                    parse_dfo_csv(blob)
        with self.assertRaisesRegex(DFOPreflightError, "end date precedes"):
            parse_dfo_csv(csv_bytes([example_row(**{"Start Date": "1/4/24", "End Date": "1/3/24"})]))

    def test_invalid_schema_duplicate_ids_and_numeric_values(self):
        with self.assertRaisesRegex(DFOPreflightError, "headings"):
            parse_dfo_csv(csv_bytes([example_row()], columns=HEADER[:-1]))
        for broken in ("٩٠٠١", "-1", "", "9.01"):
            with self.subTest(event_id=broken):
                with self.assertRaises(DFOPreflightError):
                    parse_dfo_csv(csv_bytes([example_row(**{"﹟": broken})]))
        with self.assertRaisesRegex(DFOPreflightError, "duplicate"):
            parse_dfo_csv(csv_bytes([example_row(), example_row()]))
        for bad in ("-1", "1,00", "NaN", "1e309"):
            with self.subTest(area=bad):
                with self.assertRaises(DFOPreflightError):
                    parse_dfo_csv(csv_bytes([example_row(**{"Area (km²)": bad})]))
        with self.assertRaisesRegex(DFOPreflightError, "must be a count"):
            parse_dfo_csv(csv_bytes([example_row(**{"Fatalities": "1.5"})]))
        with self.assertRaisesRegex(DFOPreflightError, "empty country"):
            parse_dfo_csv(csv_bytes([example_row(**{"Country": " "})]))

    def test_real_file_not_committed_and_sha_required_for_cli(self):
        blob = csv_bytes([example_row()])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "original.csv"
            out = Path(folder) / "normalized.json"
            source.write_bytes(blob)
            script = ROOT / "research_runners/dfo_floodrecords_csv_preflight_v0.py"
            base_cmd = [sys.executable, str(script), str(source), "--out", str(out)]
            wrong = subprocess.run(base_cmd + ["--expected-source-sha256", "0" * 64], capture_output=True, text=True)
            self.assertNotEqual(wrong.returncode, 0)
            self.assertFalse(out.exists())
            good = subprocess.run(base_cmd + ["--expected-source-sha256", hashlib.sha256(blob).hexdigest()], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["reported_event_count"], 1)
            same = subprocess.run([sys.executable, str(script), str(source), "--out", str(source),
                "--expected-source-sha256", hashlib.sha256(blob).hexdigest()], capture_output=True)
            self.assertNotEqual(same.returncode, 0)
            self.assertEqual(source.read_bytes(), blob)

    def test_empty_or_non_utf8_bytes_fail(self):
        for bad in (b"", b"\xff", "not a CSV".encode()):
            with self.subTest(blob=bad[:5]):
                with self.assertRaises(DFOPreflightError):
                    parse_dfo_csv(bad)


if __name__ == "__main__":
    unittest.main()
