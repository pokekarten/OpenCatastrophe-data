# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hermetic negative and source-receipt checks for 2022 Kreis ages vs 2025 solo HGB."""
from pathlib import Path
import copy
import sys
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_2025_kreis_age_source_sensitivity_v0 import (  # noqa: E402
    validate_original_building_age,simulate_age_prior,_hamilton,
    SyntheticBookError,
)

BUILDING=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
AGE=ROOT/"research/observations/zensus2022_400_kreis_original_building_age_cohorts_v0.toml"
ISSUER=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"

def sources():
    return [tomllib.loads(p.read_text(encoding="utf-8")) for p in (BUILDING,AGE,ISSUER)]

class RealCountyBuildingAgeVersusCompanyTest(unittest.TestCase):
    def setUp(self):
        self.b,self.a,self.h=sources()

    def test_original_400_county_age_sha_and_source_benchmarks(self):
        receipt,by=validate_original_building_age(self.b,self.a)
        self.assertEqual(receipt["original_2022_kreis_count"],400)
        self.assertEqual(len(by),400)
        self.assertEqual(self.a["original_age_rows_canonical_sha256"],
                         "2cb3d015c9a55ac90c3e738f4f8feac0adb095ad661a76b2231e56a7867fffc3")
        self.assertEqual(self.a["source_national_age_band_available_numeric_sums"][0],2606819)
        self.assertEqual(self.a["source_national_age_band_available_numeric_sums"][1],2345872)
        self.assertEqual(self.a["source_national_age_band_available_numeric_sums"][-1],764071)
        self.assertEqual(sum(self.a["source_national_age_band_available_numeric_sums"]),19957171)
        self.assertEqual(self.a["source_age_band_county_sum_minus_building_count"],-117)
        self.assertEqual(self.a["source_max_absolute_county_delta"],20)

    def test_original_age_record_matches_400_building_keys(self):
        by={r["ags"]:r for r in self.a["kreise"]}
        self.assertEqual(by["01001"]["age_bands_source_order"][:3],[2400,2140,2195])
        self.assertEqual(by["16077"]["age_bands_source_order"][:3],[9245,4779,1035])
        self.assertEqual(by["01001"]["buildings_mit_wohnraum_2022"],17984)
        self.assertEqual(len({x["ags"][:2] for x in self.a["kreise"]}),16)

    def test_three_genuine_2022_age_opportunity_priors_conserve_all_2025_controls(self):
        result=simulate_age_prior(self.b,self.a,self.h)
        self.assertEqual(result["observed_national_2025_contracts"],1060546)
        self.assertEqual(result["observed_national_2025_annual_gwp_eur_cents"],99771000000)
        self.assertEqual(len(result["cases"]),3)
        for name,c in result["cases"].items():
            self.assertEqual(sum(c["national_hypothetical_insurer_contracts_by_source_age_cohort"]),1060546,name)
            self.assertEqual(len(c["hypothetical_county_rows"]),400,name)
            self.assertEqual(len(c["hypothetical_state_rollup"]),16,name)
            self.assertEqual(sum(r["contract_count"] for r in c["hypothetical_state_rollup"].values()),1060546,name)
            self.assertEqual(sum(r["gwp_eur_cents"] for r in c["hypothetical_state_rollup"].values()),99771000000,name)
            self.assertTrue(all(sum(r["hypothetical_age_contracts_2025"])==r["hypothetical_contracts_2025"] for r in c["hypothetical_county_rows"]))
            self.assertFalse(c["company_2025_kreis_age_distribution_observed"])
            self.assertFalse(c["2022_2025_population_equivalence_verified"])

    def test_pre1950_bias_hypothesis_yields_more_old_contracts(self):
        cases=simulate_age_prior(self.b,self.a,self.h)["cases"]
        self.assertGreater(cases["HISTORIC_PRE1950_AFFINITY_1_5X"]["national_hypothetical_pre1950_contracts"],
                           cases["PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY"]["national_hypothetical_pre1950_contracts"])

    def test_post2000_bias_hypothesis_yields_more_modern_contracts(self):
        cases=simulate_age_prior(self.b,self.a,self.h)["cases"]
        self.assertGreater(cases["MODERN_POST2000_AFFINITY_1_5X"]["national_hypothetical_post2000_contracts"],
                           cases["PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY"]["national_hypothetical_post2000_contracts"])

    def test_different_age_affinities_relocate_county_book_without_real_geo_evidence(self):
        r=simulate_age_prior(self.b,self.a,self.h)
        cases=r["cases"]
        self.assertEqual(cases["PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY"]["hypothetical_policies_relocated_vs_baseline"],0)
        self.assertGreater(cases["HISTORIC_PRE1950_AFFINITY_1_5X"]["hypothetical_policies_relocated_vs_baseline"],0)
        self.assertGreater(cases["MODERN_POST2000_AFFINITY_1_5X"]["hypothetical_policies_relocated_vs_baseline"],0)
        self.assertFalse(any(r["admission"].values()))

    def test_order_invariant_for_original_public_age_rows(self):
        orig=simulate_age_prior(self.b,self.a,self.h)
        self.a["kreise"].reverse()
        self.b["kreise"].reverse()
        self.assertEqual(orig,simulate_age_prior(self.b,self.a,self.h))

    def test_tampered_age_count_fails_canonical_original_source_hash(self):
        self.a["kreise"][0]["age_bands_source_order"][0]+=1
        with self.assertRaisesRegex(SyntheticBookError,"SHA-256"):
            validate_original_building_age(self.b,self.a)

    def test_unreported_age_cohort_must_not_be_imputed_as_zero(self):
        self.a["kreise"][0]["age_bands_source_order"][0]="missing"
        with self.assertRaises(SyntheticBookError):
            validate_original_building_age(self.b,self.a)

    def test_missing_or_duplicate_ags_fails(self):
        self.a["kreise"][0]["ags"]=self.a["kreise"][1]["ags"]
        with self.assertRaises(SyntheticBookError):
            validate_original_building_age(self.b,self.a)

    def test_missing_2022_county_building_population_fails(self):
        self.b["kreise"][0]["geb_mit_wohnraum"]+=1
        with self.assertRaises(SyntheticBookError):
            validate_original_building_age(self.b,self.a)

    def test_wrong_year_source_or_insurer_data_admission_rejected(self):
        for field,value in (("source_date","2025-12-31"),
                            ("source_sheet","CSV-Wohnungen"),
                            ("actual_rva_contracts_by_building_year_observed",True),
                            ("roof_vulnerability_or_wind_loss_observed",True)):
            x=copy.deepcopy(self.a)
            x[field]=value
            with self.subTest(field=field),self.assertRaises(SyntheticBookError):
                validate_original_building_age(self.b,x)

    def test_wrong_solo_company_or_contract_total_blocked(self):
        self.h["entity"]="R+V Gruppe"
        with self.assertRaises(SyntheticBookError):simulate_age_prior(self.b,self.a,self.h)
        self.h,self.a=sources()[2],sources()[1] if False else (self.h,self.a)  # overwritten below in test
        _,_,h=sources()
        h["building_contract_observations"]["years"][-1]["contracts"]+=1
        with self.assertRaises(SyntheticBookError):simulate_age_prior(self.b,self.a,h)

    def test_hamilton_zero_weights_fail_and_conservation(self):
        self.assertEqual(sum(_hamilton(100,[9,3,2,1,1,1,1,1,1,1])),100)
        with self.assertRaises(SyntheticBookError):_hamilton(50,[0]*10)

if __name__=="__main__":
    unittest.main()
