# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Purely invented source-layer tests; no Oasis model, vendor data or live writes."""
from __future__ import annotations

from copy import deepcopy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.cede_oed_layer_identity_v0 import ReconcileError, reconcile_layers, run

ROOT = Path(__file__).resolve().parents[1]


def sample():
    exposure = {"source_format": "CEDE", "source_version": "10.0.0",
                "target_format": "OED", "target_version": "3.0.2", "synthetic_only": True,
                "rows": [
                    {"ExposureSetName": "IMAGINARY", "ContractID": "C1", "LocationID": "X1", "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "200.00", "ContentsValue": "30.00", "Latitude": "48.1", "Longitude": "11.5"},
                    {"ExposureSetName": "IMAGINARY", "ContractID": "C1", "LocationID": "X2", "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "70.00", "ContentsValue": "1.00", "Latitude": "", "Longitude": ""},
                ]}
    layers = {"source_version": "10.0.0", "target_version": "3.0.2", "synthetic_only": True,
              "layers": [
                  {"ExposureSetName": "IMAGINARY", "ContractID": "C1", "LayerID": "L1", "Currency": "EUR"},
                  {"ExposureSetName": "IMAGINARY", "ContractID": "C1", "LayerID": "L2", "Currency": "EUR"},
              ]}
    loc = [dict(PortNumber="IMAGINARY", AccNumber="C1", LocNumber=x["LocationID"],
                CountryCode=x["CountryISO"], LocCurrency=x["Currency"],
                BuildingTIV=x["BuildingValue"], ContentsTIV=x["ContentsValue"],
                Latitude=x["Latitude"], Longitude=x["Longitude"]) for x in exposure["rows"]]
    acc = [dict(PortNumber="IMAGINARY", AccNumber="C1", PolNumber=x["LayerID"],
                LayerNumber=x["LayerID"], AccCurrency="EUR") for x in layers["layers"]]
    return exposure, layers, loc, acc


class SyntheticLayerTests(unittest.TestCase):
    def test_two_layers_same_account_reconcile(self):
        result = reconcile_layers(*sample())
        self.assertEqual(result["source_account_count"], 1)
        self.assertEqual(result["source_layer_count"], 2)
        self.assertEqual(result["oed_layer_count"], 2)
        self.assertEqual(result["synthetic_totals_by_currency"]["EUR"]["BuildingTIV"], "270.00")
        self.assertFalse(result["executed_ods_tools"])
        self.assertFalse(result["peril_and_financial_terms_validated"])

    def test_row_reordering_does_not_change_result(self):
        exposure, layers, loc, acc = sample()
        self.assertEqual(reconcile_layers(exposure, layers, loc, acc), reconcile_layers(exposure, layers, loc[::-1], acc[::-1]))

    def test_duplicate_source_layer_rejected(self):
        exposure, layers, loc, acc = sample()
        layers["layers"][1] = deepcopy(layers["layers"][0])
        with self.assertRaisesRegex(ReconcileError, "duplicate source"):
            reconcile_layers(exposure, layers, loc, acc)

    def test_duplicate_and_unknown_output_layers_rejected(self):
        for value in ("L1", "OTHER"):
            exposure, layers, loc, acc = sample()
            acc[1]["PolNumber"] = value
            with self.assertRaises(ReconcileError):
                reconcile_layers(exposure, layers, loc, acc)

    def test_missing_layer_rejected(self):
        exposure, layers, loc, acc = sample()
        with self.assertRaisesRegex(ReconcileError, "cardinality"):
            reconcile_layers(exposure, layers, loc, acc[:-1])

    def test_layer_number_or_currency_change_rejected(self):
        for column, value in (("LayerNumber", "X"), ("AccCurrency", "USD")):
            exposure, layers, loc, acc = sample()
            acc[0][column] = value
            with self.assertRaises(ReconcileError):
                reconcile_layers(exposure, layers, loc, acc)

    def test_contract_without_layer_rejected(self):
        exposure, layers, loc, acc = sample()
        exposure["rows"].append(dict(exposure["rows"][0], ContractID="C2", LocationID="X3"))
        loc.append(dict(loc[0], AccNumber="C2", LocNumber="X3"))
        with self.assertRaisesRegex(ReconcileError, "missing any layer"):
            reconcile_layers(exposure, layers, loc, acc)

    def test_layer_without_location_account_rejected(self):
        exposure, layers, loc, acc = sample()
        layers["layers"][0]["ContractID"] = "C2"
        with self.assertRaisesRegex(ReconcileError, "unknown source account"):
            reconcile_layers(exposure, layers, loc, acc)

    def test_layer_vs_location_currency_rejected(self):
        exposure, layers, loc, acc = sample()
        layers["layers"][0]["Currency"] = "USD"
        with self.assertRaisesRegex(ReconcileError, "currency differs"):
            reconcile_layers(exposure, layers, loc, acc)

    def test_mixed_currencies_within_account_rejected(self):
        exposure, layers, loc, acc = sample()
        exposure["rows"][1]["Currency"] = "USD"
        with self.assertRaisesRegex(ReconcileError, "mixed location currencies"):
            reconcile_layers(exposure, layers, loc, acc)

    def test_cede13_and_unconfirmed_source_rejected(self):
        exposure, layers, loc, acc = sample()
        layers["source_version"] = "13.0.0"
        with self.assertRaisesRegex(ReconcileError, "unsupported"):
            reconcile_layers(exposure, layers, loc, acc)
        exposure, layers, loc, acc = sample()
        layers["synthetic_only"] = False
        with self.assertRaises(ReconcileError):
            reconcile_layers(exposure, layers, loc, acc)

    def test_cli_success_and_no_identifying_output(self):
        exposure, layers, loc, acc = sample()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            e, lay, l, a = (root / name for name in ("exposure.json", "layers.json", "loc.csv", "acc.csv"))
            e.write_text(json.dumps(exposure), encoding="utf-8")
            lay.write_text(json.dumps(layers), encoding="utf-8")
            for path, rows in ((l, loc), (a, acc)):
                with path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader(); writer.writerows(rows)
            self.assertTrue(run(e, lay, l, a)["layer_identity_consistent"])
            check = subprocess.run([sys.executable, str(ROOT / "scripts/cede_oed_layer_identity_v0.py"),
                                    "--synthetic-exposure", str(e), "--synthetic-layers", str(lay),
                                    "--oed-location", str(l), "--oed-account", str(a)],
                                   capture_output=True, text=True, check=False, cwd=ROOT)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertNotIn("IMAGINARY", check.stdout)
            self.assertTrue(json.loads(check.stdout)["layer_identity_consistent"])


if __name__ == "__main__":
    unittest.main()
