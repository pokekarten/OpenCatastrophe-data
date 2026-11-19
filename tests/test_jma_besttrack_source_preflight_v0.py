# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests of original-source JMA best-track integrity gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.jma_besttrack_source_preflight_v0 import (
    JMABestTrackError, inspect_besttrack_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def header(sid="2601", n=2, revision="20261102"):
    h = list(" " * 72)
    h[0:5] = "66666"
    h[6:10] = sid
    h[12:15] = f"{n:03d}"
    h[16:20] = "0001"
    h[21:25] = sid
    h[26] = "0"
    h[28] = "6"
    h[30:50] = f"{'SYNTHETIC':^20}"
    h[64:72] = revision
    return "".join(h)


def point(when="26011318", *, grade="3", lat=77, lon=1327, pressure=1004, wind=35):
    h = list(" " * 62)
    h[0:8] = when
    h[9:12] = "002"
    h[13] = grade
    h[15:18] = f"{lat:03d}"
    h[19:23] = f"{lon:04d}"
    h[24:28] = f"{pressure:4d}"
    h[33:36] = f"{wind:03d}"
    return "".join(h)


def bytes_for(lines):
    return ("\n".join(lines) + "\n").encode("ascii")


def inspect(lines, *, expected=None):
    blob = bytes_for(lines)
    return inspect_besttrack_bytes(blob, expected or hashlib.sha256(blob).hexdigest())


class JMABestTrackTests(unittest.TestCase):
    def test_two_synthetic_tracks_no_provider_rows_exported(self):
        lines = [header(), point(), point("26011400", pressure=0, wind=0),
                 header("2602", 1), point("26020300", grade="2", wind=0)]
        report = inspect(lines)
        self.assertEqual(report["cyclone_header_count"], 2)
        self.assertEqual(report["analysis_record_count"], 3)
        self.assertEqual(report["records_with_positive_reported_max_wind"], 1)
        self.assertEqual(report["records_with_positive_reported_central_pressure"], 2)
        self.assertEqual(report["source_first_analysis_utc"], "2026-01-13T18:00:00+00:00")
        self.assertTrue(report["zero_wind_or_blank_is_unknown_not_no_wind"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["track_geometry_exported"])
        self.assertNotIn("SYNTHETIC", json.dumps(report))
        self.assertNotIn("2601", json.dumps(report))

    def test_fails_on_changed_sha_and_bad_encoding(self):
        lines = [header(n=1), point()]
        with self.assertRaisesRegex(JMABestTrackError, "mismatch"):
            inspect(lines, expected="0" * 64)
        blob = bytes_for(lines) + b"\xff"
        with self.assertRaisesRegex(JMABestTrackError, "ASCII"):
            inspect_besttrack_bytes(blob, hashlib.sha256(blob).hexdigest())
        for wrong in ("nan", "A" * 64):
            with self.assertRaises(JMABestTrackError):
                inspect(lines, expected=wrong)

    def test_fails_on_counts_duplicate_and_unordered_dates(self):
        cases = [
            [header(n=3), point(), point("26011400")],
            [header(n=1), point(), header(n=1), point()],
            [header(n=2), point("26011400"), point("26011318")],
            [header(n=1), point("26023100")],
            [header(n=1), point(grade="1")],
            [header(n=1), point(lat=901)],
            [header(n=1), point(wind=201)],
            [header(n=1), point(pressure=1200)],
        ]
        for lines in cases:
            with self.subTest(lines=len(lines)):
                with self.assertRaises(JMABestTrackError):
                    inspect(lines)

    def test_cli_produces_only_aggregate_evidence_and_does_not_overwrite_source(self):
        blob = bytes_for([header(n=1), point()])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "original_bst.txt"
            output = Path(folder) / "evidence.json"
            source.write_bytes(blob)
            sha = hashlib.sha256(blob).hexdigest()
            script = ROOT / "research_runners/jma_besttrack_source_preflight_v0.py"
            proc = subprocess.run(
                [sys.executable, str(script), str(source), "--expected-sha256", sha, "--out", str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["analysis_record_count"], 1)
            same = subprocess.run(
                [sys.executable, str(script), str(source), "--expected-sha256", sha, "--out", str(source)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(same.returncode, 0)
            self.assertEqual(source.read_bytes(), blob)


if __name__ == "__main__":
    unittest.main()
