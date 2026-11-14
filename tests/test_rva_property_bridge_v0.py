# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely offline synthetic negative/positive cases for R+V solo receipt bridge."""
import tomllib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from rva_property_bridge_v0 import bridge, RvaBridgeError  # noqa: E402


def public_source():
    return tomllib.loads((ROOT / "research/observations/rva_solo_2025_public_sfcr_v0.toml").read_text(encoding="utf-8"))


def scenario():
    return tomllib.loads((ROOT / "research/scenarios/rva_property_geography_hypotheses_v0.toml").read_text(encoding="utf-8"))

class RvaBridgeTests(unittest.TestCase):
    def test_conserving_research_scenario(self):
        r = bridge(public_source(), scenario())
        self.assertEqual(r["reported_fire_other_property_gwp_eur"], "2223182000.000")
        self.assertEqual(sum(x["assumed_site_count"] for x in r["fictional_region_rows"]), 100000)
        self.assertEqual(sum(x["assumed_tiv_eur"] for x in r["fictional_region_rows"]), 500000000000)
        self.assertFalse(r["oasis_production_run_allowed"])
        self.assertFalse(r["company_site_geography_observed"])
        self.assertFalse(r["gwp_to_tiv_conversion_used"])

    def test_scenario_region_order_is_invariant(self):
        s = scenario(); r = bridge(public_source(), s)
        s["regions"].reverse()
        self.assertEqual(r["fictional_region_rows"], bridge(public_source(), s)["fictional_region_rows"])

    def test_distribution_changes_without_changing_accounting_premium(self):
        s = scenario(); original = bridge(public_source(), s)
        s["regions"][0]["tiv_weight"] = "0.20"
        s["regions"][1]["tiv_weight"] = "0.30"
        changed = bridge(public_source(), s)
        self.assertEqual(original["reported_fire_other_property_gwp_eur"], changed["reported_fire_other_property_gwp_eur"])
        self.assertNotEqual(original["fictional_region_rows"], changed["fictional_region_rows"])

    def test_blocks_renamed_parent_and_wrong_scope(self):
        for field, value in (("entity", "R+V Gruppe"), ("entity_kind", "group"),
                             ("lob_measure", "net_earned_premium_eur_million"), ("report_year", 2024)):
            d = public_source(); d["profiles"][0][field] = value
            with self.subTest(field=field), self.assertRaises(RvaBridgeError):
                bridge(d, scenario())

    def test_blocks_mutated_source_amounts_and_mixed_source_rows(self):
        for property_amt, other_amt in (("2223.181", "3769.124"), ("2223.182", "3769.126")):
            d = public_source(); d["profiles"][0]["lob_rows"][0]["value"] = property_amt
            d["profiles"][0]["lob_rows"][1]["value"] = other_amt
            with self.assertRaises(RvaBridgeError):
                bridge(d, scenario())

    def test_blocks_false_authority_and_extra_claims(self):
        for key, value in (("scenario_status", "real_rva_exposure"),
                           ("target_profile_id", "GROUP"), ("as_of", "2024-12-31")):
            s = scenario(); s[key] = value
            with self.subTest(key=key), self.assertRaises(RvaBridgeError):
                bridge(public_source(), s)
        s = scenario(); s["model_input_approved"] = True
        with self.assertRaises(RvaBridgeError):
            bridge(public_source(), s)

    def test_blocks_nonconserving_or_duplicate_regions(self):
        for change in ("wrong_sum", "duplicate", "non_de"):
            s = scenario()
            if change == "wrong_sum": s["regions"][0]["site_weight"] = "0.26"
            elif change == "duplicate": s["regions"][1]["region_id"] = "DE_NORTH"
            else: s["regions"][1]["region_id"] = "FR_EAST"
            with self.subTest(change=change), self.assertRaises(RvaBridgeError):
                bridge(public_source(), s)

    def test_blocks_bad_tiv_peril_and_sites(self):
        for key, value in (("assumed_tiv_eur", "0"), ("assumed_site_count", "500.2"),
                           ("model_perils", ["windstorm", "windstorm"])):
            s = scenario(); s[key] = value
            with self.subTest(key=key), self.assertRaises(RvaBridgeError):
                bridge(public_source(), s)


if __name__ == "__main__":
    unittest.main()
