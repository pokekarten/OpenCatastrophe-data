# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative and reconciliation checks for bounded CEDE/OED preflight."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.cede_oed_synthetic_preflight_v0 import PreflightError, inspect, run

ROOT = Path(__file__).resolve().parents[1]


def sample():
    return {"source_format": "CEDE", "source_version": "10.0.0", "target_format": "OED",
            "target_version": "3.0.2", "synthetic_only": True, "rows": [
                {"ExposureSetName": "INVENTED-A", "ContractID": "A1", "LocationID": "L1",
                 "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "100.10",
                 "ContentsValue": "20.05", "Latitude": "48.10", "Longitude": "11.50"},
                {"ExposureSetName": "INVENTED-A", "ContractID": "A1", "LocationID": "L2",
                 "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "200.15",
                 "ContentsValue": "0", "Latitude": "", "Longitude": ""},
            ]}


class SyntheticCedeOedPreflightTests(unittest.TestCase):
    def test_valid_synthetic_rows_report_counts_and_currency_exactly(self):
        outcome = inspect(sample())
        self.assertEqual(outcome["row_count"], 2)
        self.assertEqual(outcome["account_count"], 1)
        self.assertEqual(outcome["rows_without_coordinates"], 1)
        self.assertEqual(outcome["synthetic_totals_by_currency"]["EUR"],
                         {"BuildingTIV": "300.25", "ContentsTIV": "20.05"})
        self.assertFalse(outcome["executed_ods_tools"])
        self.assertFalse(outcome["model_input_admitted"])
        self.assertFalse(outcome["cede_13_compatible"])

    def test_mixed_currency_not_summed_together(self):
        data = sample()
        data["rows"][1]["Currency"] = "USD"
        self.assertEqual(set(inspect(data)["synthetic_totals_by_currency"]), {"EUR", "USD"})

    def test_duplicate_identity_rejected(self):
        data = sample()
        data["rows"].append(deepcopy(data["rows"][0]))
        with self.assertRaisesRegex(PreflightError, "duplicate"):
            inspect(data)

    def test_reject_cede_13_version(self):
        data = sample()
        data["source_version"] = "13.0.0"
        with self.assertRaisesRegex(PreflightError, "NOT validated"):
            inspect(data)

    def test_reject_target_oed_version_drift(self):
        data = sample()
        data["target_version"] = "4.0.0"
        with self.assertRaisesRegex(PreflightError, "unsupported"):
            inspect(data)

    def test_reject_real_or_unconfirmed_data(self):
        for truth in (False, None, 1, "true"):
            data = sample()
            data["synthetic_only"] = truth
            with self.assertRaises(PreflightError):
                inspect(data)

    def test_reject_unreviewed_cede13_columns(self):
        data = sample()
        data["rows"][0]["AverageHazardLevel"] = "1"
        with self.assertRaisesRegex(PreflightError, "unreviewed"):
            inspect(data)

    def test_reject_float_money_and_negative_money(self):
        for amount in (100.0, "-1", "1e4", "NaN", "0.001", True):
            data = sample()
            data["rows"][0]["BuildingValue"] = amount
            with self.assertRaises(PreflightError):
                inspect(data)

    def test_reject_partial_and_invalid_coordinates(self):
        for lat, lon in (("", "10"), ("90.1", "1"), ("0", "-180.1"), ("NaN", "1")):
            data = sample()
            data["rows"][0]["Latitude"] = lat
            data["rows"][0]["Longitude"] = lon
            with self.assertRaises(PreflightError):
                inspect(data)

    def test_reject_invalid_country_currency_and_blank_id(self):
        for col, value in (("CountryISO", "DEU"), ("Currency", "€"), ("LocationID", " ")):
            data = sample()
            data["rows"][0][col] = value
            with self.assertRaises(PreflightError):
                inspect(data)

    def test_reject_missing_or_extra_fields(self):
        data = sample()
        data["rows"][0].pop("ContentsValue")
        with self.assertRaises(PreflightError):
            inspect(data)
        data = sample()
        data["source_new"] = "bad"
        with self.assertRaises(PreflightError):
            inspect(data)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "input.json"
            p.write_text('{"synthetic_only":true,"synthetic_only":true}', encoding="utf-8")
            with self.assertRaisesRegex(PreflightError, "duplicate JSON"):
                run(p)
            p.write_text('{"synthetic_only":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(PreflightError, "non-finite"):
                run(p)

    def test_cli_uses_synthetic_only_input_and_no_raw_rows_in_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "synthetic.json"
            p.write_text(json.dumps(sample()), encoding="utf-8")
            output = subprocess.run([sys.executable, str(ROOT / "scripts/cede_oed_synthetic_preflight_v0.py"),
                                     "--synthetic-input", str(p)], cwd=ROOT,
                                    capture_output=True, text=True, check=False)
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertNotIn("INVENTED-A", output.stdout)
            self.assertIn('"cede_13_compatible": false', output.stdout)


if __name__ == "__main__":
    unittest.main()
