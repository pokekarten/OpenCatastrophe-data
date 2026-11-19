# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""2022 official state aggregates + exact 2025 company controls; no regional R+V facts."""
from pathlib import Path
import copy
import sys
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_census_16state_company_prior_v0 import compare_state_priors, validate_state_census  # noqa: E402
from synthetic_regional_property_book_v0 import SyntheticBookError  # noqa: E402

CENSUS=ROOT/"research/observations/zensus2022_16_state_residential_use_buildings_v0.toml"
HGB=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"

def load():
    return (tomllib.loads(HGB.read_text(encoding="utf-8")),
            tomllib.loads(CENSUS.read_text(encoding="utf-8")))

class OfficialCensusCompanyNonIdentifiability(unittest.TestCase):
    def setUp(self):
        self.h,self.c=load()

    def test_16_real_state_counts_and_nonadditivity_explicit(self):
        receipt=validate_state_census(self.c)
        self.assertEqual(receipt["observed_publisher_national_2022_buildings_with_residential_use"],19957268)
        self.assertEqual(receipt["summed_16_state_2022_buildings_with_residential_use"],19957266)
        self.assertEqual(receipt["printed_state_sum_minus_publisher_national"],-2)
        self.assertFalse(receipt["source_national_vs_state_additivity_exact"])
        self.assertEqual(len(self.c["states"]),16)

    def test_primary_source_state_counts_sample(self):
        d={r["state_ags"]:r for r in self.c["states"]}
        self.assertEqual(d["05"]["buildings_with_residential_use_2022"],4042229)
        self.assertEqual(d["09"]["buildings_with_residential_use_2022"],3227324)
        self.assertEqual(d["08"]["buildings_with_residential_use_2022"],2566980)
        self.assertEqual(d["11"]["buildings_with_residential_use_2022"],338663)
        self.assertEqual(d["16"]["owned_by_private_persons"],474845)

    def test_three_2022_opportunity_based_alternatives_exact_national_2025_controls(self):
        r=compare_state_priors(self.h,self.c)
        self.assertEqual(r["observed_national_2025_connected_building_contracts"],1060546)
        self.assertEqual(r["observed_national_2025_direct_booked_gwp_teuro"],997710)
        self.assertEqual(len(r["three_source_based_opportunity_alternatives"]),3)
        for name,case in r["three_source_based_opportunity_alternatives"].items():
            self.assertEqual(len(case["regional_2025_book"]),16)
            self.assertEqual(sum(x["hypothetical_2025_rva_policy_contracts"] for x in case["regional_2025_book"]),1060546)
            self.assertEqual(sum(x["hypothetical_2025_direct_written_gwp_eur_cents"] for x in case["regional_2025_book"]),99771000000)
            self.assertFalse(case["simulated_rva_2025_contracts_are_observed"])
            self.assertFalse(case["source_vintage_alignment_achieved"])

    def test_actual_population_counts_change_scenario_distribution(self):
        r=compare_state_priors(self.h,self.c)
        cases=r["three_source_based_opportunity_alternatives"]
        self.assertEqual(cases["PHYSICAL_BUILDING_OPPORTUNITY"]["shifted_hypothetical_contracts_vs_building_opportunity"],0)
        self.assertGreater(cases["PRIVATE_OWNER_OPPORTUNITY"]["shifted_hypothetical_contracts_vs_building_opportunity"],0)
        self.assertGreater(cases["CO_OWNED_AND_HOUSING_COMPANY_OPPORTUNITY"]["shifted_hypothetical_contracts_vs_building_opportunity"],0)
        private={r["state_ags"]:r["hypothetical_2025_rva_policy_contracts"]
                 for r in cases["PRIVATE_OWNER_OPPORTUNITY"]["regional_2025_book"]}
        multi={r["state_ags"]:r["hypothetical_2025_rva_policy_contracts"]
               for r in cases["CO_OWNED_AND_HOUSING_COMPANY_OPPORTUNITY"]["regional_2025_book"]}
        self.assertGreater(multi["11"],private["11"])

    def test_order_independent_state_source(self):
        result=compare_state_priors(self.h,self.c)
        self.c["states"].reverse()
        self.assertEqual(result,compare_state_priors(self.h,self.c))

    def test_false_insurer_state_counts_blocked(self):
        for k in ("company_insured_buildings_observed","company_policyholder_by_ownership_observed",
                  "company_state_market_shares_observed","geocoded_risk_sites_observed",
                  "year_2025_building_stock_observed",
                  "insurer_tiv_or_natural_perils_coverage_observed"):
            c=copy.deepcopy(self.c)
            c[k]=True
            with self.subTest(k=k),self.assertRaises(SyntheticBookError):
                compare_state_priors(self.h,c)

    def test_census_broad_buildings_with_residential_use_not_narrowed_to_residential_only(self):
        self.c["statistical_universe"]="fully_residential_buildings_exclusively"
        with self.assertRaises(SyntheticBookError): compare_state_priors(self.h,self.c)

    def test_census_2022_date_not_changed_to_2025(self):
        self.c["census_date"]="2025-12-31"
        with self.assertRaises(SyntheticBookError): compare_state_priors(self.h,self.c)

    def test_census_national_print_difference_not_silently_corrected(self):
        self.c["national_publisher_printed"]["buildings_with_residential_use_2022"]=19957266
        with self.assertRaises(SyntheticBookError): validate_state_census(self.c)

    def test_census_bad_suppressed_or_mutated_count_blocked(self):
        for n in (0,-1,"/","...",None):
            c=copy.deepcopy(self.c)
            c["states"][0]["buildings_with_residential_use_2022"]=n
            with self.subTest(n=n),self.assertRaises(SyntheticBookError):
                validate_state_census(c)

    def test_missing_duplicate_state_ags_blocked(self):
        for x in ("01","99"):
            c=copy.deepcopy(self.c)
            c["states"][1]["state_ags"]=x
            with self.subTest(x=x),self.assertRaises(SyntheticBookError):
                validate_state_census(c)

    def test_unexplained_ownership_subtotal_exceeding_print_variance_blocked(self):
        self.c["states"][0]["owned_by_housing_companies"]+=100
        with self.assertRaises(SyntheticBookError): validate_state_census(self.c)

    def test_wrong_2025_solo_insurer_or_premium_blocked(self):
        h=copy.deepcopy(self.h);h["entity_kind"]="group"
        with self.assertRaises(SyntheticBookError):compare_state_priors(h,self.c)
        h=copy.deepcopy(self.h);h["years"][-1]["connected_buildings_self_written"]=997711
        with self.assertRaises(SyntheticBookError):compare_state_priors(h,self.c)
        h=copy.deepcopy(self.h);h["building_contract_observations"]["years"][-1]["contracts"]=1050000
        with self.assertRaises(SyntheticBookError):compare_state_priors(h,self.c)

    def test_no_real_sites_tiv_native_oasis_or_contract_uptake(self):
        r=compare_state_priors(self.h,self.c)
        self.assertFalse(any(r["limitations"].values()))
        self.assertEqual(r["census_2022_source_audit"]["printed_state_sum_minus_publisher_national"],-2)
        for name,case in r["three_source_based_opportunity_alternatives"].items():
            self.assertTrue(all(x["not_company_observed_risk_locations"] for x in case["regional_2025_book"]))

if __name__=="__main__":
    unittest.main()
