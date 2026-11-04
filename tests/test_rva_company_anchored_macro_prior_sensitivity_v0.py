# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent negative and positive controls for 2025 solo anchors and BVR scope."""

import copy
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_company_anchored_macro_prior_sensitivity_v0 import ( # noqa: E402
    compare_company_anchored_macro, verify_bvr)
from synthetic_regional_property_book_v0 import SyntheticBookError  # noqa: E402

H = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
B = ROOT / "research/observations/bvr_regional_association_counts_2024_2025_v0.toml"
S = ROOT / "research/scenarios/rva_solo_2025_company_anchored_macro_sensitivity_v0.toml"

def load():
    return [tomllib.loads(x.read_text(encoding="utf-8")) for x in (H,B,S)]

class CompanyAnchoredMacroPriorTests(unittest.TestCase):
    def setUp(self):
        self.h,self.b,self.s=load()

    def test_source_bvr_2024_25_exact_subtotals_and_identity(self):
        b=verify_bvr(self.b)
        self.assertEqual(b["banks_2025"],646)
        self.assertEqual(b["branch_offices_2025"],6167)
        self.assertEqual(b["members_2025"],17542193)
        self.assertEqual(b["branch_office_change_2025_minus_2024"],-144)
        self.assertFalse(b["bvr_association_to_state_weights_available"])
        self.assertFalse(b["branch_offices_equal_to_all_bank_sites"])

    def test_exact_solo_national_count_and_written_premium_conserved(self):
        r=compare_company_anchored_macro(self.h,self.b,self.s)
        self.assertEqual(r["observed_2025_national_connected_building_contract_count"],1060546)
        self.assertEqual(r["observed_2025_national_direct_booked_gwp_teuro"],997710)
        self.assertEqual(r["observed_2025_national_direct_booked_gwp_eur_cents"],99771000000)
        for name,case in r["regional_sensitivity_cases"].items():
            self.assertEqual(sum(x["synthetic_contracts_at_year_end"] for x in case["regions"]),1060546,name)
            self.assertEqual(sum(x["hypothetical_regional_annual_gwp_eur_cents"] for x in case["regions"]),99771000000,name)
            self.assertTrue(case["synthetic_total_annual_written_gwp_cents_conserved"])
            self.assertFalse(case["model_input_approved"])

    def test_three_alternative_priors_show_nonidentification(self):
        r=compare_company_anchored_macro(self.h,self.b,self.s)
        d=r["difference_from_uniform"]
        self.assertEqual(d["UNIFORM_HYPOTHESIS"]["hypothetical_contracts_shifted_from_uniform"],0)
        self.assertGreater(d["SOUTH_WEST_HYPOTHESIS"]["hypothetical_contracts_shifted_from_uniform"],0)
        self.assertGreater(d["NORTH_EAST_HYPOTHESIS"]["hypothetical_contracts_shifted_from_uniform"],0)
        self.assertNotEqual(d["NORTH_EAST_HYPOTHESIS"]["total_variation_fraction"],
                            d["SOUTH_WEST_HYPOTHESIS"]["total_variation_fraction"])

    def test_scenario_order_invariant(self):
        original=compare_company_anchored_macro(self.h,self.b,self.s)["regional_sensitivity_cases"]
        for row in self.s["hypotheses"]: row["regions"].reverse()
        self.s["hypotheses"].reverse()
        changed=compare_company_anchored_macro(self.h,self.b,self.s)["regional_sensitivity_cases"]
        # The source-order SHA-256 receipt changes by design; the projected\n        # regional allocation, exact national controls and flags must not.\n        for name in original:\n            self.assertEqual(original[name]["regions"], changed[name]["regions"])\n            self.assertEqual(original[name]["synthetic_total_contracts_conserved"],\n                             changed[name]["synthetic_total_contracts_conserved"])\n            self.assertEqual(original[name]["synthetic_total_annual_written_gwp_cents_conserved"],\n                             changed[name]["synthetic_total_annual_written_gwp_cents_conserved"])\n
    def test_change_fictional_geo_weights_but_preserve_real_national_constraints(self):
        original=compare_company_anchored_macro(self.h,self.b,self.s)
        rows=self.s["hypotheses"][1]["regions"]
        rows[0]["contract_prior_weight"]="0.75"
        changed=compare_company_anchored_macro(self.h,self.b,self.s)
        self.assertEqual(original["observed_2025_national_direct_booked_gwp_eur_cents"],
                         changed["observed_2025_national_direct_booked_gwp_eur_cents"])
        self.assertNotEqual(original["regional_sensitivity_cases"]["SOUTH_WEST_HYPOTHESIS"]["regions"],
                            changed["regional_sensitivity_cases"]["SOUTH_WEST_HYPOTHESIS"]["regions"])

    def test_false_insurer_geographies_blocked(self):
        for key in ("real_company_region_shares_observed",
                    "original_zensus_regional_building_counts_admitted",
                    "bvr_association_to_state_geography_verified",
                    "bvr_indicators_used_as_company_weights",
                    "issuer_peril_take_up_observed", "insurer_sites_and_tiv_observed",
                    "model_input_approved"):
            obj=copy.deepcopy(self.s);obj[key]=True
            with self.subTest(key=key),self.assertRaises(SyntheticBookError):
                compare_company_anchored_macro(self.h,self.b,obj)

    def test_wrong_company_identity_and_issuer_measures_blocked(self):
        for key,val in (("entity","R+V Gruppe"),("entity_kind","group"),
                        ("premium_unit","eur"),("accounting_basis","Solvency II")):
            h=copy.deepcopy(self.h);h[key]=val
            with self.subTest(key=key),self.assertRaises(SyntheticBookError):
                compare_company_anchored_macro(h,self.b,self.s)

    def test_mutated_original_national_controls_rejected(self):
        h=copy.deepcopy(self.h);h["years"][-1]["connected_buildings_self_written"]=1000000
        with self.assertRaises(SyntheticBookError): compare_company_anchored_macro(h,self.b,self.s)
        h=copy.deepcopy(self.h);h["building_contract_observations"]["years"][-1]["contracts"]=1060547
        with self.assertRaises(SyntheticBookError): compare_company_anchored_macro(h,self.b,self.s)

    def test_incomplete_or_duplicate_macro_regions_blocked(self):
        for mutation in ("duplicate","missing"):
            x=copy.deepcopy(self.s)
            if mutation=="duplicate":
                x["hypotheses"][1]["regions"][1]["region_code"]="DE_NORTH"
            else:
                x["hypotheses"][1]["regions"].pop(0)
            with self.subTest(mutation=mutation),self.assertRaises(SyntheticBookError):
                compare_company_anchored_macro(self.h,self.b,x)

    def test_hypothetical_flood_coverage_not_observed_or_set_without_source(self):
        for key in ("hypothetical_market_elemental_share", "assumed_carrier_uptake_multiplier"):
            x=copy.deepcopy(self.s);x["hypotheses"][0]["regions"][0][key]="0.75"
            with self.subTest(key=key),self.assertRaises(SyntheticBookError):
                compare_company_anchored_macro(self.h,self.b,x)

    def test_bvr_subtotal_or_category_source_tampering_detected(self):
        for k in ("members_2025","bank_offices_2024","cooperative_banks_2025"):
            b=copy.deepcopy(self.b);b["categories"][0][k]+=1
            with self.subTest(field=k),self.assertRaises(SyntheticBookError):
                verify_bvr(b)

    def test_bvr_bank_count_not_solo_insurance_shares(self):
        for key in ("associations_are_german_states","all_cooperative_banks_are_ruv_partners",
                    "membership_is_homeowner_population","banks_are_ruv_insured_property_locations",
                    "branch_counts_are_insured_locations","derived_carrier_state_weights_admitted"):
            b=copy.deepcopy(self.b);b[key]=True
            with self.subTest(key=key),self.assertRaises(SyntheticBookError):
                verify_bvr(b)

    def test_missing_bvr_category_blocked(self):
        b=copy.deepcopy(self.b);b["categories"].pop()
        with self.assertRaises(SyntheticBookError): verify_bvr(b)

    def test_no_oasis_output_or_actual_building_locations(self):
        r=compare_company_anchored_macro(self.h,self.b,self.s)
        self.assertFalse(any(r["limitations"].values()))
        for case in r["regional_sensitivity_cases"].values():
            self.assertFalse(case["has_true_risk_site_coordinates"])
            self.assertFalse(case["has_insured_tiv"])
            self.assertFalse(case["has_event_or_cat_losses"])

if __name__=="__main__":
    unittest.main()
