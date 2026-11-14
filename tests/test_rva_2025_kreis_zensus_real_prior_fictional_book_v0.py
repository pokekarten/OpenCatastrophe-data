# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Public 2022 400-Kreis census physical opportunity / 2025 RVA solo nonidentification tests."""
from pathlib import Path
import copy
import sys
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_2025_kreis_zensus_real_prior_fictional_book_v0 import (  # noqa: E402
    compare_real_census_fictional_rva,validate_kreis_original)
from synthetic_regional_property_book_v0 import SyntheticBookError  # noqa: E402

C=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
H=ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"

def input_data():
    return tomllib.loads(C.read_text(encoding="utf-8")),tomllib.loads(H.read_text(encoding="utf-8"))

class OriginalCensusCountyToRvaTests(unittest.TestCase):
    def setUp(self):
        self.c,self.h=input_data()

    def test_reconciles_real_original_400_counties_and_dates(self):
        r=validate_kreis_original(self.c)
        self.assertEqual(r["original_2022_kreis_count"],400)
        self.assertEqual(r["original_land_count"],16)
        self.assertEqual(r["original_2022_kreis_buildings_total"],19957288)
        self.assertEqual(r["original_2022_kreis_residential"],19488949)
        self.assertEqual(r["original_2022_kreis_mixeduse"],468301)
        self.assertEqual(r["published_kreis_sum_minus_separate_national_print"],20)
        self.assertEqual(r["original_2022_wohnheim_numeric_counties"],393)
        self.assertFalse(r["source_printed_CKM_region_sums_are_exact_underlying_counts"])

    def test_original_source_county_examples(self):
        rows={r["ags"]:r for r in self.c["kreise"]}
        self.assertEqual(rows["01001"]["geb_mit_wohnraum"],17984)
        self.assertEqual(rows["01002"]["geb_mit_wohnraum"],38247)
        self.assertEqual(rows["16077"]["geb_mit_wohnraum"],24356)
        self.assertEqual(rows["01001"]["wohngebaeude"],17706)
        self.assertEqual(len(rows),400)
        self.assertEqual(sum(r["wohnheime"]=="missing" for r in rows.values()),7)

    def test_all_three_county_scenarios_conserve_solo_2025_national_mass(self):
        r=compare_real_census_fictional_rva(self.c,self.h)
        self.assertEqual(r["observed_solo_2025_national_contract_count"],1060546)
        self.assertEqual(r["observed_solo_2025_national_written_premium_eur_cents"],99771000000)
        cases=r["hypothetical_geographical_cases"]
        self.assertEqual(len(cases),3)
        for name,case in cases.items():
            self.assertEqual(len(case["regions_400"]),400,name)
            self.assertEqual(len(case["hypothetical_2025_land_summaries"]),16,name)
            self.assertEqual(sum(s["hypothetical_contracts"] for s in case["hypothetical_2025_land_summaries"].values()),1060546,name)
            self.assertEqual(sum(s["hypothetical_written_gwp_eur_cents"] for s in case["hypothetical_2025_land_summaries"].values()),99771000000,name)
            self.assertTrue(case["issuer_count_and_premium_conserved"])
            self.assertFalse(case["regional_carrier_contracts_observed"])
            self.assertFalse(case["natural_peril_coverage_measured"])
            self.assertEqual(sum(x["hypothetical_elemental_cover_contract_equivalents"] for x in case["regions_400"]),0)

    def test_hypothetical_geo_allocation_is_not_uniquely_identified(self):
        cases=compare_real_census_fictional_rva(self.c,self.h)["hypothetical_geographical_cases"]
        self.assertEqual(cases["PHYSICAL_ALL_RESIDENTIAL_USE"]["shifted_hypothetical_policies_vs_physical_all"],0)
        self.assertGreater(cases["RESIDENTIAL_NON_DORMITORY"]["shifted_hypothetical_policies_vs_physical_all"],0)
        self.assertGreater(cases["MIXED_USE_OVERWEIGHT_5X"]["shifted_hypothetical_policies_vs_physical_all"],0)
        self.assertNotEqual(cases["RESIDENTIAL_NON_DORMITORY"]["county_total_variation_vs_physical_all"],
                            cases["MIXED_USE_OVERWEIGHT_5X"]["county_total_variation_vs_physical_all"])

    def test_county_ordinal_order_does_not_change_assigned_book(self):
        r=compare_real_census_fictional_rva(self.c,self.h)
        self.c["kreise"].reverse()
        self.assertEqual(r,compare_real_census_fictional_rva(self.c,self.h))

    def test_false_insurer_observation_flags_rejected(self):
        for k in ("physical_building_count_2022_is_insurer_contract_count_2025",
                  "observed_rva_kreis_policies","observed_rva_site_coordinates","observed_rva_tiv",
                  "observed_rva_flood_coverage","real_insurer_model_admitted"):
            c=copy.deepcopy(self.c)
            c[k]=True
            with self.subTest(k=k),self.assertRaises(SyntheticBookError):
                validate_kreis_original(c)

    def test_mutated_original_file_sha_or_2022_date_rejected(self):
        for k,v in (("original_full_file_sha256","x"*64),
                    ("source_values_canonical_sha256","0"*64),
                    ("source_event_date","2025-12-31"),
                    ("source_geo_key","ZIP")):
            c=copy.deepcopy(self.c);c[k]=v
            with self.subTest(k=k),self.assertRaises(SyntheticBookError):
                validate_kreis_original(c)

    def test_different_insurer_or_gwp_not_silently_accepted(self):
        h=copy.deepcopy(self.h);h["entity"]="R+V group"
        with self.assertRaises(SyntheticBookError): compare_real_census_fictional_rva(self.c,h)
        h=copy.deepcopy(self.h);h["years"][-1]["connected_buildings_self_written"]+=1
        with self.assertRaises(SyntheticBookError): compare_real_census_fictional_rva(self.c,h)

    def test_wrong_actual_2025_policy_count_blocked(self):
        self.h["building_contract_observations"]["years"][-1]["contracts"]=1060547
        with self.assertRaises(SyntheticBookError):
            compare_real_census_fictional_rva(self.c,self.h)

    def test_duplicate_and_missing_county_fail(self):
        c=copy.deepcopy(self.c)
        c["kreise"][1]["ags"]=c["kreise"][0]["ags"]
        with self.assertRaises(SyntheticBookError): validate_kreis_original(c)
        c=copy.deepcopy(self.c)
        c["kreise"].pop()
        with self.assertRaises(SyntheticBookError): validate_kreis_original(c)

    def test_suppressed_subcategory_never_filled_as_zero(self):
        c=copy.deepcopy(self.c)
        idx=next(i for i,r in enumerate(c["kreise"]) if r["wohnheime"]=="missing")
        c["kreise"][idx]["wohnheime"]=0
        with self.assertRaises(SyntheticBookError): validate_kreis_original(c)

    def test_primary_numeric_cannot_be_suppressed(self):
        c=copy.deepcopy(self.c);c["kreise"][0]["geb_mit_wohnraum"]="missing"
        with self.assertRaises(SyntheticBookError): validate_kreis_original(c)

    def test_source_count_not_become_2025_eur_tiv(self):
        r=compare_real_census_fictional_rva(self.c,self.h)
        self.assertTrue(all(v is False for v in r["admission"].values()))
        self.assertFalse(r["original_census_2022_source"]["source_printed_CKM_region_sums_are_exact_underlying_counts"])

    def test_region_keys_and_scope(self):
        rows=self.c["kreise"]
        self.assertEqual(rows[0]["ags"],"01001")
        self.assertEqual(rows[-1]["ags"],"16077")
        self.assertEqual(len({x["ags"][:2] for x in rows}),16)

if __name__=="__main__":
    unittest.main()
