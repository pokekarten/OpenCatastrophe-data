# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic offline tests for exact ISIMIP3a ER11 max-rain filelist."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.isimip3a_er11_maxrain_filelist_preflight_v0 import (
    EXPECTED_YEARS,
    FILELIST_URL,
    ISIMIPFilelistError,
    MAX_FILELIST_BYTES,
    inspect_filelist_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = (
    "https://files.isimip.org/ISIMIP3a/InputData/climate/tropical_cyclones/"
    "obsclim/global/storm/historical/ER11-wind/"
)


def fixture(years=EXPECTED_YEARS) -> bytes:
    return ("".join(
        BASE + f"er11-wind_obsclim_historical_maxrain_{year}.nc\n"
        for year in years
    )).encode("ascii")


def audit(raw: bytes) -> dict:
    return inspect_filelist_bytes(raw, hashlib.sha256(raw).hexdigest())


class TestISIMIPFilelistPreflight(unittest.TestCase):
    def test_valid_exact_annual_filelist_still_not_admitted(self) -> None:
        report = audit(fixture())
        self.assertEqual(report["annual_file_count"], 72)
        self.assertEqual((report["first_year"], report["last_year"]), (1950, 2021))
        self.assertEqual(report["provider_filelist_url"], FILELIST_URL)
        self.assertEqual(report["admission_status"], "not_admitted")
        self.assertTrue(report["derived_max_24h_rainfall_not_direct_observation"])
        self.assertFalse(report["netcdf_bytes_downloaded"])
        self.assertFalse(report["data_license_reviewed"])
        self.assertFalse(report["commercial_insurance_use_approved"])

    def test_pinned_sha_mismatch(self) -> None:
        with self.assertRaisesRegex(ISIMIPFilelistError, "SHA256 mismatch"):
            inspect_filelist_bytes(fixture(), "0" * 64)

    def test_invalid_sha(self) -> None:
        with self.assertRaisesRegex(ISIMIPFilelistError, "SHA256"):
            inspect_filelist_bytes(fixture(), "not-a-sha")

    def test_missing_year(self) -> None:
        with self.assertRaisesRegex(ISIMIPFilelistError, "72"):
            audit(fixture(EXPECTED_YEARS[:-1]))

    def test_years_out_of_order(self) -> None:
        years = list(EXPECTED_YEARS)
        years[2], years[3] = years[3], years[2]
        with self.assertRaisesRegex(ISIMIPFilelistError, "out-of-order"):
            audit(fixture(years))

    def test_duplicate_one_year(self) -> None:
        years = list(EXPECTED_YEARS)
        years[3] = years[2]
        with self.assertRaisesRegex(ISIMIPFilelistError, "duplicate"):
            audit(fixture(years))

    def test_wrong_forecast_or_other_product(self) -> None:
        raw = fixture().replace(b"/historical/", b"/future/")
        with self.assertRaisesRegex(ISIMIPFilelistError, "pathway"):
            audit(raw)

    def test_wrong_folder_model(self) -> None:
        raw = fixture().replace(b"/ER11-wind/", b"/H08/")
        with self.assertRaisesRegex(ISIMIPFilelistError, "pathway"):
            audit(raw)

    def test_other_variable_rejected(self) -> None:
        raw = fixture().replace(b"_maxrain_", b"_windlifetimemax_")
        with self.assertRaisesRegex(ISIMIPFilelistError, "filename"):
            audit(raw)

    def test_wrong_host_rejected(self) -> None:
        raw = fixture().replace(b"files.isimip.org", b"files.example.com")
        with self.assertRaisesRegex(ISIMIPFilelistError, "host"):
            audit(raw)

    def test_embedded_query_rejected(self) -> None:
        raw = fixture().replace(b"1950.nc", b"1950.nc?token=secret")
        with self.assertRaisesRegex(ISIMIPFilelistError, "query"):
            audit(raw)

    def test_http_rejected(self) -> None:
        raw = fixture().replace(b"https://", b"http://")
        with self.assertRaisesRegex(ISIMIPFilelistError, "host/scheme"):
            audit(raw)

    def test_crlf_rejected(self) -> None:
        raw = fixture().replace(b"\n", b"\r\n")
        with self.assertRaisesRegex(ISIMIPFilelistError, "CR"):
            audit(raw)

    def test_nonascii_rejected(self) -> None:
        raw = fixture() + b"\xff"
        with self.assertRaisesRegex(ISIMIPFilelistError, "ASCII"):
            audit(raw)

    def test_size_cap_rejected(self) -> None:
        raw = b"x" * (MAX_FILELIST_BYTES + 1)
        with self.assertRaisesRegex(ISIMIPFilelistError, "32 KiB"):
            audit(raw)

    def test_empty_rejected(self) -> None:
        with self.assertRaises(ISIMIPFilelistError):
            audit(b"")

    def test_cli_receipt_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test-filelist.txt"
            output = Path(d) / "report.json"
            blob = fixture()
            path.write_bytes(blob)
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/isimip3a_er11_maxrain_filelist_preflight_v0.py"),
                "--filelist", str(path),
                "--expected-sha256", hashlib.sha256(blob).hexdigest(),
                "--out", str(output),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["annual_file_count"], 72)
            self.assertEqual(path.read_bytes(), blob)
            blocked = subprocess.run(cmd[:-1] + [str(path)], capture_output=True, text=True, check=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(path.read_bytes(), blob)


if __name__ == "__main__":
    unittest.main()
