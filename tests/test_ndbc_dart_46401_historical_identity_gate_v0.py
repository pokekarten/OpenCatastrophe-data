# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic-only checks for NDBC 46401 historic source identity."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from research_runners.ndbc_dart_original_preflight_v0 import DARTPreflightError
from research_runners.ndbc_dart_46401_historical_identity_gate_v0 import (
    END,
    ORIGINAL_DOCUMENTED_URL,
    START,
    STATION,
    inspect_local_canary,
)

ROOT = Path(__file__).resolve().parents[1]
# Not provider bytes; format/layout alone mirrors NDBC's published example.
FAKE_BODY = (
    b"station 46401\n"
    b"start 2004-01-18\n"
    b"end 2004-01-22\n"
    b"\n"
    b"YYYY MM DD hh mm ss T   HEIGHT (meters)\n"
    b"2004 01 22 15 00 00 1 5526.870\n"
    b"2004 01 22 14 45 00 1 5526.883\n"
)


class HistoricalDARTIdentityTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.source = Path(tmp.name) / "synthetic-dart.txt"
        self.source.write_bytes(FAKE_BODY)

    def test_exact_offline_source_identity_and_historical_not_current_station(self):
        report = inspect_local_canary(self.source)
        self.assertEqual((STATION, START, END), ("46401", "2004-01-18", "2004-01-22"))
        self.assertEqual(report["observations"], 2)
        self.assertEqual(report["count_by_type"], {"1": 2, "2": 0, "3": 0})
        self.assertEqual(report["input_sha256"], hashlib.sha256(FAKE_BODY).hexdigest())
        self.assertEqual(report["fixed_documented_request_url"], ORIGINAL_DOCUMENTED_URL)
        self.assertTrue(report["historical_station_record_includes_2004"])
        self.assertTrue(report["station_disestablished_in_2006"])
        self.assertFalse(report["station_operational_in_2026"])
        self.assertFalse(report["original_http_response_retrieved_in_this_run"])
        self.assertFalse(report["service_automation_rights_verified"])
        self.assertFalse(report["commercial_cat_use_rights_verified"])
        self.assertFalse(report["original_provider_provenance_verified"])
        self.assertFalse(report["source_admitted"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("2004 01 22 15 00 00 1", str(report))

    def test_supplied_matching_hash_does_not_upgrade_original_provenance(self):
        receipt = inspect_local_canary(
            self.source,
            supplied_original_sha256=hashlib.sha256(FAKE_BODY).hexdigest(),
        )
        self.assertTrue(receipt["external_digest_supplied_and_matched"])
        self.assertFalse(receipt["external_digest_proves_provider_origin"])
        self.assertFalse(receipt["original_provider_provenance_verified"])
        self.assertFalse(receipt["model_input_admitted"])

    def test_wrong_or_noncanonical_caller_hash_blocks(self):
        for supplied in (
            "0" * 64,
            hashlib.sha256(FAKE_BODY).hexdigest().upper(),
            "NaN",
            "f" * 65,
            "",
        ):
            with self.subTest(supplied=supplied[:12]), self.assertRaises(DARTPreflightError):
                inspect_local_canary(self.source, supplied_original_sha256=supplied)

    def test_source_identity_cannot_be_substituted_by_body_claim(self):
        for body in (
            FAKE_BODY.replace(b"station 46401", b"station 32066"),
            FAKE_BODY.replace(b"start 2004-01-18", b"start 2004-01-19"),
            FAKE_BODY.replace(b"end 2004-01-22", b"end 2004-01-23"),
            FAKE_BODY.replace(b"2004 01 22 14 45 00", b"2004 01 23 14 45 00"),
            FAKE_BODY.replace(b"HEIGHT (meters)", b"HEIGHT (feet)"),
        ):
            with self.subTest(body=body[:40]):
                self.source.write_bytes(body)
                with self.assertRaises(DARTPreflightError):
                    inspect_local_canary(self.source)
        self.source.write_bytes(FAKE_BODY)

    def test_symlink_and_html_error_body_blocked(self):
        self.source.write_bytes(b"<html>No data available</html>")
        with self.assertRaises(DARTPreflightError):
            inspect_local_canary(self.source)
        self.source.write_bytes(FAKE_BODY)
        alias = self.source.parent / "symlink.txt"
        try:
            alias.symlink_to(self.source)
        except OSError:
            self.skipTest("symlink not available")
        with self.assertRaises(DARTPreflightError):
            inspect_local_canary(alias)

    def test_command_line_emits_aggregates_not_rows_and_blocks_bad_hash(self):
        cmd = [
            sys.executable, "-m",
            "research_runners.ndbc_dart_46401_historical_identity_gate_v0",
            "--file", str(self.source),
        ]
        good = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn('"observations": 2', good.stdout)
        self.assertIn('"model_input_admitted": false', good.stdout)
        self.assertNotIn("2004 01 22 15 00 00 1 5526.870", good.stdout)
        bad = subprocess.run(
            cmd + ["--expected-original-sha256", "f" * 64],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(bad.returncode, 2)
        self.assertIn("BLOCKED", bad.stderr)


if __name__ == "__main__":
    unittest.main()
