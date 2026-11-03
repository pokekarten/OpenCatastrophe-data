# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline integration and negative tests for normalized fictional OED mapping."""
import csv
import tempfile
import unittest
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from research_runners.export_relational_synthetic_oed_v1 import (
    SyntheticOedError, export_relational, project_relational,
)
from research_runners.export_synthetic_oed_v0 import export as export_baseline
from test_export_synthetic_oed_v0 import fixture as base_fixture


def fixture():
    obj = base_fixture()
    obj["account"] = {"account_key": "SYNTH-ACC-01", "currency": "EUR",
                      "synthetic": True, "source_key": None}
    obj["policy"] = {"policy_key": "SYNTH-POL-01",
                     "policy_perils_oed": "WW2;OO1",
                     "synthetic": True, "source_key": None}
    for unit in obj["units"]:
        unit["location_perils_oed"] = "WW2;OO1"
        unit["tiv_components"] = {
            "building": unit["insured_value"], "contents": "0",
            "bi": "0", "other": "0"
        }
    return obj


class RelationalSyntheticOedTests(unittest.TestCase):
    def test_identical_csvs_to_baseline_and_total(self):
        with tempfile.TemporaryDirectory() as root:
            snap = fixture()
            a = export_baseline(snap, Path(root) / "baseline")
            b = export_relational(snap, Path(root) / "relational")
            for x, y in zip(a, b):
                self.assertEqual(x.read_bytes(), y.read_bytes())
            with b[0].open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 12)
            self.assertEqual(sum(Decimal(row["BuildingTIV"]) for row in rows), 3150000)
            self.assertRaises(SyntheticOedError, export_relational, snap, Path(root) / "relational")

    def test_inadmissible_policy_value_and_crosswalk_rejected(self):
        modifications = [
            lambda obj: obj["account"].update(account_key="REAL-ACC"),
            lambda obj: obj["account"].update(synthetic=False),
            lambda obj: obj["account"].update(source_key="real-asset"),
            lambda obj: obj["policy"].update(policy_perils_oed="AA1"),
            lambda obj: obj["policy"].update(policy_key="REAL-POL"),
            lambda obj: obj["policy"].update(source_key="real-asset"),
            lambda obj: obj["units"][0].update(location_perils_oed="WW1"),
            lambda obj: obj["units"][0]["tiv_components"].update(building="125001"),
            lambda obj: obj["units"][0]["tiv_components"].update(contents="1"),
            lambda obj: obj["units"][0]["tiv_components"].update(contents=None),
            lambda obj: obj["units"][0]["tiv_components"].update(other="-1"),
            lambda obj: obj["units"][0]["tiv_components"].update(bi="NaN"),
            lambda obj: obj["units"][0]["tiv_components"].pop("bi"),
            lambda obj: obj["units"][0]["tiv_components"].update(extra="1"),
            lambda obj: obj["units"][1].update(external_unit_id="SYNTH-01"),
        ]
        for modify in modifications:
            with self.subTest(modify=repr(modify)), tempfile.TemporaryDirectory() as root:
                snapshot = deepcopy(fixture())
                modify(snapshot)
                out = Path(root) / "invalid"
                with self.assertRaises(SyntheticOedError):
                    export_relational(snapshot, out)
                self.assertFalse(out.exists())

    def test_does_not_export_reinsurance_from_illustrative_cat_xl(self):
        locations, accounts = project_relational(fixture())
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0]["PolPerilsCovered"], "WW2;OO1")
        self.assertTrue(all(row["AccNumber"] == "SYNTH-ACC-01" for row in locations))
        self.assertTrue(all("ReinsNumber" not in row for row in locations))


if __name__ == "__main__":
    unittest.main()
