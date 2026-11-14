# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No real insurer, GDV or Zensus data. Entirely fictional geographic cases."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research_runners"))
from synthetic_regional_property_book_v0 import (
    SyntheticBookError, allocate_synthetic_regional_book
)


def fixture():
    return {
        "schema_version":"0.1.0", "scenario_kind":"fully_synthetic_test_only",
        "reporting_scope":"fictional_solo_direct_residential_building",
        "year_end":"2025-12-31",
        "contract_population":"at_least_one_year_contracts_at_year_end_not_buildings",
        "premium_population":"annual_direct_gross_written_eur_cents_not_tariff",
        "geography_status":"hypothetical_not_insurer_observed",
        "take_up_status":"hypothetical_market_reference_not_carrier_observed",
        "synthetic_total_year_end_contracts":"100",
        "synthetic_total_written_gwp_eur_cents":"1234567",
        "regions":[
            {"region_code":"FICT_A","hypothetical_contract_capacity":"80",
             "contract_prior_weight":"2","premium_relativity":"1.2",
             "hypothetical_market_elemental_share":"0.5","assumed_carrier_uptake_multiplier":"1"},
            {"region_code":"FICT_B","hypothetical_contract_capacity":"80",
             "contract_prior_weight":"1","premium_relativity":"0.7",
             "hypothetical_market_elemental_share":"0.8","assumed_carrier_uptake_multiplier":"0.5"}
        ]
    }


class SyntheticRegionalPropertyBookTests(unittest.TestCase):
    def test_conserve_integer_contracts_and_euro_cents(self):
        out=allocate_synthetic_regional_book(fixture())
        self.assertEqual(sum(x["synthetic_contracts_at_year_end"] for x in out["regions"]),100)
        self.assertEqual(sum(x["hypothetical_regional_annual_gwp_eur_cents"] for x in out["regions"]),1234567)
        self.assertEqual({x["region_code"]:x["synthetic_contracts_at_year_end"] for x in out["regions"]},
                         {"FICT_A":67,"FICT_B":33})
        self.assertTrue(out["synthetic_total_contracts_conserved"])
        self.assertTrue(out["synthetic_total_annual_written_gwp_cents_conserved"])

    def test_deterministic_and_input_order_independent_rows(self):
        raw=fixture()
        first=allocate_synthetic_regional_book(raw)
        raw["regions"].reverse()
        second=allocate_synthetic_regional_book(raw)
        self.assertEqual(first["regions"],second["regions"])
        # SHA fingerprints input byte semantics, not guaranteed scenario equivalence.
        self.assertNotEqual(first["scenario_sha256"],second["scenario_sha256"])

    def test_same_country_margins_do_not_identify_county_distribution(self):
        raw=fixture()
        one=allocate_synthetic_regional_book(raw)
        raw["regions"][0]["contract_prior_weight"]="1"
        raw["regions"][1]["contract_prior_weight"]="2"
        two=allocate_synthetic_regional_book(raw)
        self.assertNotEqual(one["regions"][0]["synthetic_contracts_at_year_end"],
                            two["regions"][0]["synthetic_contracts_at_year_end"])
        self.assertEqual(sum(x["synthetic_contracts_at_year_end"] for x in one["regions"]),
                         sum(x["synthetic_contracts_at_year_end"] for x in two["regions"]))

    def test_capacity_waterfill(self):
        raw=fixture()
        raw["regions"][0]["hypothetical_contract_capacity"]="20"
        out=allocate_synthetic_regional_book(raw)
        self.assertEqual([x["synthetic_contracts_at_year_end"] for x in out["regions"]],[20,80])
        self.assertEqual(sum(x["hypothetical_regional_annual_gwp_eur_cents"] for x in out["regions"]),1234567)

    def test_infeasible_market_equivalents_fail_closed(self):
        raw=fixture()
        raw["regions"][0]["hypothetical_contract_capacity"]="1"
        with self.assertRaisesRegex(SyntheticBookError,"exceeds all regional capacities"):
            allocate_synthetic_regional_book(raw)

    def test_zero_capacities_not_silently_promoted(self):
        raw=fixture()
        for x in raw["regions"]:x["hypothetical_contract_capacity"]="0"
        with self.assertRaises(SyntheticBookError):
            allocate_synthetic_regional_book(raw)

    def test_region_without_capacity_has_zero_allocations(self):
        raw=fixture()
        raw["regions"][0]["hypothetical_contract_capacity"]="0"
        raw["regions"][1]["hypothetical_contract_capacity"]="100"
        out=allocate_synthetic_regional_book(raw)
        self.assertEqual(out["regions"][0]["synthetic_contracts_at_year_end"],0)
        self.assertEqual(out["regions"][0]["hypothetical_regional_annual_gwp_eur_cents"],0)
        self.assertEqual(out["regions"][0]["hypothetical_elemental_cover_contract_equivalents"],0)

    def test_industry_elemental_market_share_is_not_carrier_share(self):
        raw=fixture()
        first=allocate_synthetic_regional_book(raw)
        raw["regions"][0]["assumed_carrier_uptake_multiplier"]="0.25"
        next_one=allocate_synthetic_regional_book(raw)
        self.assertNotEqual(first["regions"][0]["hypothetical_elemental_cover_contract_equivalents"],
                            next_one["regions"][0]["hypothetical_elemental_cover_contract_equivalents"])
        self.assertEqual(first["regions"][0]["synthetic_contracts_at_year_end"],
                         next_one["regions"][0]["synthetic_contracts_at_year_end"])
        self.assertFalse(next_one["market_elemental_take_up_is_insurer_take_up"])

    def test_elemental_coverage_capped_at_contract_count(self):
        raw=fixture()
        raw["regions"][0]["hypothetical_market_elemental_share"]="1"
        raw["regions"][0]["assumed_carrier_uptake_multiplier"]="8"
        out=allocate_synthetic_regional_book(raw)
        self.assertEqual(out["regions"][0]["hypothetical_elemental_cover_contract_equivalents"],
                         out["regions"][0]["synthetic_contracts_at_year_end"])

    def test_invalid_integer_types_and_literals(self):
        for bad in (1,False,None,"-10","NaN","1e2","1.2"):
            raw=fixture();raw["synthetic_total_year_end_contracts"]=bad
            with self.subTest(bad=bad),self.assertRaises(SyntheticBookError):
                allocate_synthetic_regional_book(raw)

    def test_source_geography_population_and_net_premium_promotion_blocked(self):
        mutations=[
            ("scenario_kind","real_insurer_portfolio"),
            ("geography_status","insurer_actual_risk_sites"),
            ("take_up_status","company_elemental_coverage_observed"),
            ("premium_population","net_earned_premium"),
            ("contract_population","unique_physical_buildings"),
            ("reporting_scope","group")]
        for key,value in mutations:
            raw=fixture();raw[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(SyntheticBookError,"unsupported source"):
                allocate_synthetic_regional_book(raw)

    def test_date_and_undeclared_authority_fields_blocked(self):
        raw=fixture();raw["year_end"]="2025-02-31"
        with self.assertRaises(SyntheticBookError):allocate_synthetic_regional_book(raw)
        raw=fixture();raw["actual_insurer_risk_sites_verified"]=True
        with self.assertRaises(SyntheticBookError):allocate_synthetic_regional_book(raw)

    def test_duplicate_and_unstructured_region_ids_blocked(self):
        raw=fixture();raw["regions"][1]["region_code"]="FICT_A"
        with self.assertRaisesRegex(SyntheticBookError,"duplicate"):allocate_synthetic_regional_book(raw)
        raw=fixture();raw["regions"][0]["region_code"]="invalid-district"
        with self.assertRaisesRegex(SyntheticBookError,"region code"):allocate_synthetic_regional_book(raw)

    def test_invalid_fraction_and_weight_blocks(self):
        for name,value in [("hypothetical_market_elemental_share","1.01"),
                           ("assumed_carrier_uptake_multiplier","10.1"),
                           ("contract_prior_weight","0"),("premium_relativity","0")]:
            raw=fixture();raw["regions"][0][name]=value
            with self.subTest(field=name),self.assertRaises(SyntheticBookError):
                allocate_synthetic_regional_book(raw)

    def test_zero_carrier_take_up_sensitivity(self):
        raw=fixture();raw["regions"][0]["assumed_carrier_uptake_multiplier"]="0"
        out=allocate_synthetic_regional_book(raw)
        self.assertEqual(out["regions"][0]["hypothetical_elemental_cover_contract_equivalents"],0)

    def test_never_observed_policy_building_tariff_tiv_or_cat_model(self):
        result=allocate_synthetic_regional_book(fixture())
        for key in ("contract_count_is_insured_building_count",
                    "market_elemental_take_up_is_insurer_take_up",
                    "regional_contract_counts_are_observed","regional_premiums_are_observed",
                    "annual_written_premium_per_year_end_contract_is_tariff",
                    "has_true_risk_site_coordinates","has_insured_tiv",
                    "has_event_or_cat_losses","has_reinsurance_treaties",
                    "model_input_approved"):
            self.assertFalse(result[key],key)

    def test_positive_universe_and_bounded_size(self):
        raw=fixture();raw["synthetic_total_written_gwp_eur_cents"]="0"
        with self.assertRaisesRegex(SyntheticBookError,"positive fictional"):
            allocate_synthetic_regional_book(raw)
        raw=fixture();raw["synthetic_total_year_end_contracts"]="1000000001"
        with self.assertRaisesRegex(SyntheticBookError,"bounded synthetic limit"):
            allocate_synthetic_regional_book(raw)


if __name__ == "__main__":
    unittest.main()
