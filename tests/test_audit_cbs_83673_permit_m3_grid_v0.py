# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic CBS OData response structure and non-admission tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cbs_83673_permit_m3_grid_v0 import (
    CbsPermitCostError, REGIONS, TENURES, audit, main, read,
)

# These 10 values reproduce PUBLIC CBS 2026VJ06 aggregate cells only.
# They are not insurer prices, individual buildings, licensed insurer rates,
# replacement costs or hypothetical dwelling policy locations.
RATES = {
    "A028867": {"NL01": 488, "LD01": 400, "LD02": 446, "LD03": 552, "LD04": 417},
    "A028868": {"NL01": 438, "LD01": 442, "LD02": 417, "LD03": 481, "LD04": 394},
}


def sources():
    props = {
        "Identifier": "83673NED",
        "Version": "202608200000",
        "Modified": "2026-08-20T00:00:00+02:00",
        "License": "https://creativecommons.org/licenses/by/4.0/",
    }
    rows = [
        {
            "Id": i,
            "Measure": "M002974",
            "ValueAttribute": "None",
            "Value": value,
            "StringValue": None,
            "Eigendom": t,
            "RegioS": r,
            "Perioden": "2026VJ06",
        }
        for i, (t, r, value) in enumerate(
            (t, r, RATES[t][r]) for t in TENURES for r in REGIONS
        )
    ]
    return props, {"value": rows}


class CbsM3GridTests(unittest.TestCase):
    def test_tenure_region_prices_are_observed_permit_not_reconstruction(self):
        p, o = sources()
        res = audit(p, o)
        self.assertTrue(res["observation_grid_complete"])
        self.assertEqual(res["number_of_aggregate_observations"], 10)
        self.assertEqual(res["prices_eur_per_m3"]["netherlands"]["rental_new_housing"], "488")
        self.assertEqual(res["prices_eur_per_m3"]["west"]["owner_occupied_new_housing"], "481")
        self.assertEqual(res["prices_eur_per_m3"]["south"]["rental_new_housing"], "417")
        self.assertEqual(res["original_version"], "202608200000")
        self.assertEqual(res["measure_code"], "M002974")
        self.assertTrue(res["data_provisional"])
        for k in ("valid_for_existing_building_rebuild_cost_directly",
                  "valid_for_mixed_use_or_historic_reinstatement_directly",
                  "real_insured_tiv_calculated", "source_admitted",
                  "scientific_review_approved", "model_input_approved"):
            self.assertFalse(res[k])
        self.assertTrue(res["unapproved_lod_volume_multiplication_blocked"])

    def test_missing_duplicate_and_extra_cells_fail(self):
        p, o = sources()
        o["value"].pop()
        with self.assertRaises(CbsPermitCostError):
            audit(p, o)
        p, o = sources()
        o["value"][1]["RegioS"] = o["value"][0]["RegioS"]
        with self.assertRaises(CbsPermitCostError):
            audit(p, o)
        p, o = sources()
        o["@odata.nextLink"] = "https://another-page.example"
        with self.assertRaisesRegex(CbsPermitCostError, "truncated"):
            audit(p, o)

    def test_wrong_metadata_revision_licence_and_period(self):
        for field, val in (
            ("Version", "202611010000"), ("Identifier", "85728NED"),
            ("License", "https://other.example/rights"),
            ("Modified", "2026-11-05T10:00:00+01:00"),
        ):
            with self.subTest(field=field), self.assertRaises(CbsPermitCostError):
                p, o = sources()
                p[field] = val
                audit(p, o)
        p, o = sources()
        o["value"][0]["Perioden"] = "2026VJ03"
        with self.assertRaises(CbsPermitCostError):
            audit(p, o)
        p, o = sources()
        o["value"][0]["Measure"] = "M002973"  # EUR/m², NOT EUR/m³
        with self.assertRaises(CbsPermitCostError):
            audit(p, o)

    def test_suppressed_or_nonnumeric_rate_never_used(self):
        for rate in (-1, 0, True, None, float("nan"), "not available", 10001):
            with self.subTest(rate=rate):
                p, o = sources()
                o["value"][0]["Value"] = rate
                with self.assertRaises(CbsPermitCostError):
                    audit(p, o)
        p, o = sources()
        o["value"][1]["ValueAttribute"] = "Missing"
        with self.assertRaises(CbsPermitCostError):
            audit(p, o)

    def test_observation_order_is_not_assumed(self):
        p, o = sources()
        o["value"].reverse()
        r = audit(p, o)
        self.assertEqual(r["prices_eur_per_m3"]["east"]["rental_new_housing"], "446")

    def test_cli_reads_original_schema_shape_only_and_blocks_duplicate_json(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "props.json"
            g = Path(temp) / "observations.json"
            p, o = sources()
            f.write_text(json.dumps(p), encoding="utf-8")
            g.write_text(json.dumps(o), encoding="utf-8")
            self.assertEqual(main(["--properties", str(f), "--observations", str(g)]), 0)
            self.assertEqual(len(read(f)[1]), 64)
            g.write_text('{"value":[],"value":[]}', encoding="utf-8")
            with self.assertRaises(CbsPermitCostError):
                read(g)
            self.assertEqual(main(["--properties", str(f), "--observations", str(g)]), 2)


if __name__ == "__main__":
    unittest.main()
