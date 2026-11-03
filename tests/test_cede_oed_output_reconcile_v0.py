# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only fictional test rows: synthetic CEDE/OED location and account reconciliation."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.cede_oed_output_reconcile_v0 import ReconcileError, reconcile, run

ROOT = Path(__file__).resolve().parents[1]
LOC_FIELDS = ["PortNumber", "AccNumber", "LocNumber", "CountryCode",
              "LocCurrency", "BuildingTIV", "ContentsTIV", "Latitude", "Longitude"]
ACC_FIELDS = ["PortNumber", "AccNumber"]


def sample():
    return {"source_format": "CEDE", "source_version": "10.0.0",
            "target_format": "OED", "target_version": "3.0.2",
            "synthetic_only": True, "rows": [
                {"ExposureSetName": "INVENTED-A", "ContractID": "A1", "LocationID": "L1",
                 "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "100.10",
                 "ContentsValue": "20.05", "Latitude": "48.10", "Longitude": "11.50"},
                {"ExposureSetName": "INVENTED-A", "ContractID": "A1", "LocationID": "L2",
                 "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "200.15",
                 "ContentsValue": "0", "Latitude": "", "Longitude": ""},
            ]}


def outputs():
    keys = {"PortNumber": "ExposureSetName", "AccNumber": "ContractID",
            "LocNumber": "LocationID", "CountryCode": "CountryISO",
            "LocCurrency": "Currency", "BuildingTIV": "BuildingValue",
            "ContentsTIV": "ContentsValue", "Latitude": "Latitude", "Longitude": "Longitude"}
    loc = [{target: row[source] for target, source in keys.items()} for row in sample()["rows"]]
    return loc, [{"PortNumber": "INVENTED-A", "AccNumber": "A1"}]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class SyntheticReconcileTests(unittest.TestCase):
    def test_direct_fields_and_totals_match(self):
        loc, acc = outputs()
        result = reconcile(sample(), loc, acc)
        self.assertEqual(result["synthetic_totals_by_currency"]["EUR"]["BuildingTIV"], "300.25")
        self.assertTrue(result["direct_mapping_consistent"])
        self.assertFalse(result["executed_ods_tools"])
        self.assertFalse(result["oed_schema_validated"])
        self.assertFalse(result["cede_13_compatible"])

    def test_different_row_order_is_valid(self):
        loc, acc = outputs()
        self.assertEqual(reconcile(sample(), list(reversed(loc)), acc)["oed_location_count"], 2)

    def test_changed_building_tiv_fails(self):
        loc, acc = outputs()
        loc[0]["BuildingTIV"] = "101.10"
        with self.assertRaisesRegex(ReconcileError, "changed BuildingTIV"):
            reconcile(sample(), loc, acc)

    def test_duplicate_and_unknown_location_fails(self):
        for key in ("L1", "UNKNOWN"):
            loc, acc = outputs()
            loc[1]["LocNumber"] = key
            with self.assertRaises(ReconcileError):
                reconcile(sample(), loc, acc)

    def test_location_missing_fails(self):
        loc, acc = outputs()
        with self.assertRaisesRegex(ReconcileError, "cardinality"):
            reconcile(sample(), loc[:-1], acc)

    def test_account_missing_or_spurious_fails(self):
        loc, acc = outputs()
        with self.assertRaises(ReconcileError):
            reconcile(sample(), loc, [])
        with self.assertRaises(ReconcileError):
            reconcile(sample(), loc, [{"PortNumber": "OTHER", "AccNumber": "A1"}])

    def test_wrong_country_currency_or_coordinate_fails(self):
        for field, value in (("CountryCode", "FR"), ("LocCurrency", "USD"), ("Latitude", "48.11")):
            loc, acc = outputs()
            loc[0][field] = value
            with self.assertRaises(ReconcileError):
                reconcile(sample(), loc, acc)

    def test_nonfinite_or_excess_money_scale_fails(self):
        for value in ("NaN", "Inf", "-1", "1.001"):
            loc, acc = outputs()
            loc[0]["BuildingTIV"] = value
            with self.assertRaises(ReconcileError):
                reconcile(sample(), loc, acc)

    def test_csv_duplicate_header_and_overwide_row_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, lf, af = (root / name for name in ("synthetic.json", "loc.csv", "acc.csv"))
            src.write_text(json.dumps(sample()), encoding="utf-8")
            loc, acc = outputs()
            write_csv(lf, LOC_FIELDS, loc)
            write_csv(af, ACC_FIELDS, acc)
            self.assertEqual(run(src, lf, af)["oed_location_count"], 2)
            lf.write_text(lf.read_text().replace("PortNumber,", "PortNumber,PortNumber,", 1), encoding="utf-8")
            with self.assertRaisesRegex(ReconcileError, "duplicate"):
                run(src, lf, af)
            write_csv(lf, LOC_FIELDS, loc)
            with lf.open("a", encoding="utf-8") as handle:
                handle.write("EXTRA,TOO,MANY,COLUMNS,AND,VALUES,AND,MORE,THAN,EXPECTED,YES\n")
            with self.assertRaises(ReconcileError):
                run(src, lf, af)

    def test_cli_report_does_not_echo_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, lf, af = (root / name for name in ("input.json", "loc.csv", "acc.csv"))
            src.write_text(json.dumps(sample()), encoding="utf-8")
            loc, acc = outputs()
            write_csv(lf, LOC_FIELDS, loc)
            write_csv(af, ACC_FIELDS, acc)
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/cede_oed_output_reconcile_v0.py"),
                 "--synthetic-input", str(src), "--oed-location", str(lf), "--oed-account", str(af)],
                cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("INVENTED-A", proc.stdout)
            self.assertFalse(json.loads(proc.stdout)["oed_schema_validated"])


if __name__ == "__main__":
    unittest.main()
