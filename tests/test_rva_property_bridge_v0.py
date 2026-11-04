# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely offline synthetic negative/positive cases for R+V solo receipt bridge."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from rva_property_bridge_v0 import bridge, RvaBridgeError  # noqa: E402


def ffbk_source():
    return {"schema_version":"FFBK_SFCR_SOLO_CEDANT_REINSURER_PUBLIC_PROFILES_V0",
            "calibration_status":"NOT_CALIBRATED", "profiles":[{
            "profile_id":"RVA_DE_2025", "entity":"R+V Allgemeine Versicherung AG",
            "entity_kind":"solo_direct_insurer", "report_year":2025, "currency":"EUR",
            "source":{"url":"https://www.ruv.de/example/SFCR-2025.pdf"},
            "basis":{"denominator_measure":"gross_written_premium","denominator_eur_million":"5992.306"},
            "lob_measure":"gross_written_premium_eur_million", "lob_rows":[
                {"code":"fire_and_other_property", "value":"2223.182"},
                {"code":"other_test_lines_combined", "value":"3769.124"}]}]}


def scenario():
    return json.loads((ROOT / "research/scenarios/rva_property_geography_hypotheses_v0.json").read_text())


class RvaBridgeTests(unittest.TestCase):
    def test_conserving_research_scenario(self):
        r = bridge(ffbk_source(), scenario())
        self.assertEqual(r["reported_fire_other_property_gwp_eur"], "2223182000.000")
        self.assertEqual(sum(x["assumed_site_count"] for x in r["fictional_region_rows"]), 100000)
        self.assertEqual(sum(x["assumed_tiv_eur"] for x in r["fictional_region_rows"]), 500000000000)
        self.assertFalse(r["oasis_production_run_allowed"])
        self.assertFalse(r["company_site_geography_observed"])
        self.assertFalse(r["gwp_to_tiv_conversion_used"])

    def test_scenario_region_order_is_invariant(self):
        s = scenario(); r = bridge(ffbk_source(), s)
        s["regions"].reverse()
        self.assertEqual(r["fictional_region_rows"], bridge(ffbk_source(), s)["fictional_region_rows"])

    def test_distribution_changes_without_changing_accounting_premium(self):
        s = scenario(); original = bridge(ffbk_source(), s)
        s["regions"][0]["tiv_weight"] = "0.20"
        s["regions"][1]["tiv_weight"] = "0.30"
        changed = bridge(ffbk_source(), s)
        self.assertEqual(original["reported_fire_other_property_gwp_eur"], changed["reported_fire_other_property_gwp_eur"])
        self.assertNotEqual(original["fictional_region_rows"], changed["fictional_region_rows"])

    def test_blocks_renamed_parent_and_wrong_scope(self):
        for field, value in (("entity", "R+V Gruppe"), ("entity_kind", "group"),
                             ("lob_measure", "net_earned_premium_eur_million"), ("report_year", 2024)):
            d = ffbk_source(); d["profiles"][0][field] = value
            with self.subTest(field=field), self.assertRaises(RvaBridgeError):
                bridge(d, scenario())

    def test_blocks_mutated_source_amounts_and_mixed_source_rows(self):
        for property_amt, other_amt in (("2223.181", "3769.124"), ("2223.182", "3769.126")):
            d = ffbk_source(); d["profiles"][0]["lob_rows"][0]["value"] = property_amt
            d["profiles"][0]["lob_rows"][1]["value"] = other_amt
            with self.assertRaises(RvaBridgeError):
                bridge(d, scenario())

    def test_blocks_false_authority_and_extra_claims(self):
        for key, value in (("scenario_status", "real_rva_exposure"),
                           ("target_profile_id", "GROUP"), ("as_of", "2024-12-31")):
            s = scenario(); s[key] = value
            with self.subTest(key=key), self.assertRaises(RvaBridgeError):
                bridge(ffbk_source(), s)
        s = scenario(); s["model_input_approved"] = True
        with self.assertRaises(RvaBridgeError):
            bridge(ffbk_source(), s)

    def test_blocks_nonconserving_or_duplicate_regions(self):
        for change in ("wrong_sum", "duplicate", "non_de"):
            s = scenario()
            if change == "wrong_sum": s["regions"][0]["site_weight"] = "0.26"
            elif change == "duplicate": s["regions"][1]["region_id"] = "DE_NORTH"
            else: s["regions"][1]["region_id"] = "FR_EAST"
            with self.subTest(change=change), self.assertRaises(RvaBridgeError):
                bridge(ffbk_source(), s)

    def test_blocks_bad_tiv_peril_and_sites(self):
        for key, value in (("assumed_tiv_eur", "0"), ("assumed_site_count", "500.2"),
                           ("model_perils", ["windstorm", "windstorm"])):
            s = scenario(); s[key] = value
            with self.subTest(key=key), self.assertRaises(RvaBridgeError):
                bridge(ffbk_source(), s)


if __name__ == "__main__":
    unittest.main()
