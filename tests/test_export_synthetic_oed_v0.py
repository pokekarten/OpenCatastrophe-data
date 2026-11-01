# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline negative and round-trip tests for independent synthetic OED projection."""
import csv
import json
import tempfile
import unittest
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from research_runners.export_synthetic_oed_v0 import (
    ACCOUNT_FIELDS, LOCATION_FIELDS, SyntheticOedError, export, project,
)


def fixture():
    return {
        "portfolio_key": "oc-synthetic-exposure-smoke-v0",
        "portfolio_type": "synthetic", "organization_id": None,
        "version_label": "v0", "generation_method": "deterministic_independent_synthetic_sql_v0",
        "assumptions": {"synthetic": True, "real_insurer": False, "real_buildings": False,
                        "model_input_approved": False, "external_source_rows_used": 0},
        "units": [{
            "external_unit_id": f"SYNTH-{n:02d}", "source_key": None,
            "assumption_status": "synthetic", "unit_type": "asset", "country_code": "DE",
            "insured_value_currency": "EUR", "value_basis": "invented_smoke_test_value_not_insured_observation",
            "building_count": "1", "insured_value": str(100000 + 25000*n),
            "latitude": str(Decimal("50.0") + ((n-1)//4) * Decimal("0.1")),
            "longitude": str(Decimal("9.9") + (n%4) * Decimal("0.1")),
        } for n in range(1, 13)]
    }


class ExportSyntheticOedTests(unittest.TestCase):
    def test_deterministic_csv_and_round_trip(self):
        with tempfile.TemporaryDirectory() as root:
            inp = fixture()
            locpath, accpath = export(inp, Path(root)/"oed")
            with locpath.open(newline="", encoding="utf-8") as f:
                loc = list(csv.DictReader(f))
            with accpath.open(newline="", encoding="utf-8") as f:
                acc = list(csv.DictReader(f))
            self.assertEqual(len(loc), 12)
            self.assertEqual(len(acc), 1)
            self.assertEqual(tuple(loc[0]), LOCATION_FIELDS)
            self.assertEqual(tuple(acc[0]), ACCOUNT_FIELDS)
            self.assertEqual(sum(Decimal(r["BuildingTIV"]) for r in loc), Decimal("3150000"))
            self.assertTrue(all(r["OtherTIV"] == r["BITIV"] == r["ContentsTIV"] == "0" for r in loc))
            self.assertEqual({r["LocNumber"] for r in loc}, {f"SYNTH-{n:02}" for n in range(1,13)})
            self.assertTrue(all(r["AccNumber"] == acc[0]["AccNumber"] for r in loc))
            self.assertEqual({r["OEDVersion"] for r in loc}, {"5.0.0"})
            self.assertEqual({r["LocPerilsCovered"] for r in loc}, {"WW2;OO1"})
            self.assertEqual(project(inp)[0], loc)
            self.assertRaises(SyntheticOedError, export, inp, Path(root)/"oed")

    def test_reject_real_or_invalid_snapshot_before_writing(self):
        mutations = [
            lambda s: s.update(organization_id="real-company-id"),
            lambda s: s.update(portfolio_type="real_restricted"),
            lambda s: s["assumptions"].update(model_input_approved=True),
            lambda s: s["assumptions"].update(real_buildings=True),
            lambda s: s["assumptions"].update(external_source_rows_used=1),
            lambda s: s["units"][0].update(source_key="some-source"),
            lambda s: s["units"][0].update(assumption_status="modelled"),
            lambda s: s["units"][0].update(insured_value="999999"),
            lambda s: s["units"][0].update(insured_value="NaN"),
            lambda s: s["units"][0].update(insured_value=None),
            lambda s: s["units"][0].update(building_count="2"),
            lambda s: s["units"][0].update(latitude="91"),
            lambda s: s["units"][0].update(country_code="GB"),
            lambda s: s["units"][1].update(external_unit_id="SYNTH-01"),
            lambda s: s["units"].pop(),
        ]
        for modify in mutations:
            with self.subTest(modify=repr(modify)), tempfile.TemporaryDirectory() as root:
                s = deepcopy(fixture())
                modify(s)
                out = Path(root)/"not_created"
                with self.assertRaises(SyntheticOedError):
                    export(s, out)
                self.assertFalse(out.exists())

    def test_no_valid_insurer_or_real_coverage_claim(self):
        rows, account = project(fixture())
        self.assertTrue(all("SYNTH" in r["LocNumber"] for r in rows))
        self.assertEqual(account[0]["PolNumber"], "SYNTH-POL-01")
        self.assertNotIn("ReinsType", account[0])
        self.assertNotIn("OccupancyCode", rows[0])  # unknown OED taxonomy, not invented code
        self.assertNotIn("ConstructionCode", rows[0])


if __name__ == "__main__":
    unittest.main()
