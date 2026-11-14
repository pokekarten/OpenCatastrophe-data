# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only, independently synthetic DART observations; zero provider requests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from research_runners.ndbc_dart_original_preflight_v0 import (
    DARTPreflightError, MAX_BYTES, preflight,
)

ROOT = Path(__file__).resolve().parents[1]
GOOD = ("station 46401\nstart 2004-01-18\nend 2004-01-22\n\n"
        "YYYY MM DD hh mm ss T HEIGHT (meters)\n"
        "2004 01 22 15 00 00 1 5526.870\n"
        "2004 01 22 14 45 00 1 5526.883\n"
        "2004 01 22 14 44 45 3 5526.884\n")


class DARTScreenTests(unittest.TestCase):
    def setUp(self):
        t = TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.dir = Path(t.name)
        self.path = self.dir / "synthetic.txt"
        self.path.write_text(GOOD, encoding="ascii")

    def run_screen(self, body: str | None = None, **kwargs):
        if body is not None:
            self.path.write_text(body, encoding="ascii")
        return preflight(self.path, station=kwargs.get("station", "46401"),
                         start=kwargs.get("start", "2004-01-18"),
                         end=kwargs.get("end", "2004-01-22"))

    def test_receipt_is_deterministic_and_aggregate_only(self):
        report = self.run_screen()
        self.assertEqual(report, self.run_screen())
        self.assertEqual(report["input_sha256"], hashlib.sha256(GOOD.encode()).hexdigest())
        self.assertEqual(report["observations"], 3)
        self.assertEqual(report["count_by_type"], {"1": 2, "2": 0, "3": 1})
        self.assertEqual(report["largest_observed_gap_seconds"], 900)
        self.assertEqual(report["minimum_water_column_m"], 5526.870)
        self.assertFalse(report["original_provider_provenance_verified"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("2004 01 22", str(report))

    def test_request_identity_must_match_body(self):
        for args in ({"station": "43412"}, {"start": "2004-01-19"},
                     {"end": "2004-01-21"}):
            with self.subTest(args=args), self.assertRaisesRegex(DARTPreflightError, "mismatch"):
                self.run_screen(**args)

    def test_invalid_request_parameters(self):
        for args in ({"station": "abc/../"}, {"start": "2004-02-31"},
                     {"start": "2004-01-23"}, {"end": "2004-01-30"}):
            with self.subTest(args=args), self.assertRaises(DARTPreflightError):
                self.run_screen(**args)

    def test_reject_html_and_provider_error_text(self):
        for body in ("<html>error</html>", "No station ID specified.",
                     GOOD + "<script>alert(1)</script>"):
            with self.subTest(body=body[:16]), self.assertRaises(DARTPreflightError):
                self.run_screen(body)

    def test_reject_invalid_timestamp_type_and_height(self):
        for old, new in (("2004 01 22 14 44 45", "2004 02 30 14 44 45"),
                         ("2004 01 22 14 44 45", "2004 01 23 14 44 45"),
                         (" 3 5526.884", " 4 5526.884"),
                         (" 3 5526.884", " 3 NaN"),
                         (" 3 5526.884", " 3 -4"),
                         (" 3 5526.884", " 3 12000.01")):
            with self.subTest(new=new), self.assertRaises(DARTPreflightError):
                self.run_screen(GOOD.replace(old, new))

    def test_reject_out_of_order_duplicate_and_missing_rows(self):
        rows = GOOD.splitlines()
        for body in (GOOD + rows[-1] + "\n",
                     GOOD.replace(rows[-1], "2004 01 22 15 01 00 3 5526.884"),
                     "\n".join(rows[:5]) + "\n"):
            with self.subTest(body=body[-50:]), self.assertRaises(DARTPreflightError):
                self.run_screen(body)

    def test_reject_non_ascii_and_large_file(self):
        self.path.write_bytes(GOOD.encode() + "ö".encode("utf-8"))
        with self.assertRaisesRegex(DARTPreflightError, "non-ASCII"):
            self.run_screen()
        self.path.write_bytes(b"x" * (MAX_BYTES + 1))
        with self.assertRaisesRegex(DARTPreflightError, "byte limit"):
            self.run_screen()

    def test_reject_symlink(self):
        alias = self.dir / "alias.txt"
        try:
            alias.symlink_to(self.path)
        except OSError:
            self.skipTest("symlink not available")
        with self.assertRaisesRegex(DARTPreflightError, "non-symlink"):
            preflight(alias, station="46401", start="2004-01-18", end="2004-01-22")

    def test_cli_does_not_export_source_rows(self):
        args = [sys.executable, "research_runners/ndbc_dart_original_preflight_v0.py",
                "--file", str(self.path), "--station", "46401",
                "--start", "2004-01-18", "--end", "2004-01-22"]
        cmd = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(cmd.returncode, 0, cmd.stderr)
        self.assertNotIn("2004 01 22 15 00 00", cmd.stdout)
        self.assertIn('"model_input_admitted": false', cmd.stdout)
        bad = subprocess.run(args[:-1] + ["2004-01-21"], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("BLOCKED:", bad.stderr)


if __name__ == "__main__":
    unittest.main()
