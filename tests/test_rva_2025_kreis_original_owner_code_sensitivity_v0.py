# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-gated owner code/issuer solo identity and exact-conservation tests."""
from pathlib import Path
import sys,tomllib,copy,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_2025_kreis_original_owner_code_sensitivity_v0 import ( # noqa: E402
    validate_owner_source,simulate_owner_code_scenarios,SyntheticBookError)

P=[ROOT/"research/observations/zensus2022_400_kreis_original_owner_code_aggregates_v0.toml",
   ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml",
   ROOT/"research/observations/rva_solo_hgb_property_2019_2025_v0.toml"]

def load():return [tomllib.loads(p.read_text(encoding="utf-8")) for p in P]

class CountyOwnershipSourceAndInsurerTests(unittest.TestCase):
    def setUp(self):self.o,self.b,self.h=load()
    def test_400_original_owner_source_and_missing_counts(self):
        m,v=validate_owner_source(self.o,self.b)
        self.assertEqual(m["original_2022_kreis_count"],400)
        self.assertEqual(len(v),400)
        self.assertEqual(self.o["original_all_eight_numeric_kreise"],385)
        self.assertEqual(self.o["source_column_numeric_kreise"],[400,400,390,400,400,400,394,400])
        self.assertEqual(self.o["source_column_numeric_totals_available_only"][:2],[1771256,16944010])
        self.assertFalse(self.o["individual_owner_code_name_mapping_confirmed"])

    def test_exact_national_contract_and_cent_mass_three_scenarios(self):
        r=simulate_owner_code_scenarios(self.o,self.b,self.h)
        self.assertEqual(r["observed_solo_national_2025_contracts"],1060546)
        self.assertEqual(r["observed_solo_national_2025_booked_gwp_eur_cents"],99771000000)
        self.assertEqual(len(r["scenarios"]),3)
        self.assertTrue(all(v is False for v in r["admission"].values()))
        for name,c in r["scenarios"].items():
            self.assertEqual(len(c["county_allocations"]),400,name)
            self.assertEqual(len(c["state_rollups"]),16,name)
            self.assertEqual(sum(x["hypothetical_contracts"] for x in c["state_rollups"].values()),1060546,name)
            self.assertEqual(sum(x["hypothetical_gwp_eur_cents"] for x in c["state_rollups"].values()),99771000000,name)
            self.assertFalse(c["actual_rva_2025_geo_exposure_observed"])

    def test_owner_code_affinity_does_change_fictional_region(self):
        c=simulate_owner_code_scenarios(self.o,self.b,self.h)["scenarios"]
        self.assertEqual(c["ALL_PUBLISHED_BUILDINGS"]["hypothetical_relocated_contracts_vs_baseline"],0)
        self.assertGreater(c["SOURCE_CODE1_EXTRA_50PCT"]["hypothetical_relocated_contracts_vs_baseline"],0)
        self.assertGreater(c["SOURCE_CODE2_EXTRA_50PCT"]["hypothetical_relocated_contracts_vs_baseline"],0)

    def test_source_order_does_not_change_allocations(self):
        r=simulate_owner_code_scenarios(self.o,self.b,self.h)
        self.o["kreise"].reverse()
        self.b["kreise"].reverse()
        self.assertEqual(r,simulate_owner_code_scenarios(self.o,self.b,self.h))

    def test_change_raw_owner_value_rejected_by_original_canonical_sha(self):
        self.o["kreise"][0]["original_owner_codes"][0]+=1
        with self.assertRaisesRegex(SyntheticBookError,"SHA mismatch"):
            validate_owner_source(self.o,self.b)

    def test_hidden_owner_category_not_filled_with_zero(self):
        row=next(x for x in self.o["kreise"] if "missing" in x["original_owner_codes"])
        i=row["original_owner_codes"].index("missing")
        row["original_owner_codes"][i]=0
        with self.assertRaises(SyntheticBookError):
            validate_owner_source(self.o,self.b)

    def test_owner_labels_not_assumed(self):
        self.o["individual_owner_code_name_mapping_confirmed"]=True
        with self.assertRaises(SyntheticBookError):
            validate_owner_source(self.o,self.b)

    def test_wrong_company_or_claim_of_geo_observation_rejected(self):
        h=copy.deepcopy(self.h)
        h["entity"]="R+V group"
        with self.assertRaises(SyntheticBookError):simulate_owner_code_scenarios(self.o,self.b,h)
        h=copy.deepcopy(self.h)
        h["company_geo_exposure_observed"]=True
        with self.assertRaises(SyntheticBookError):simulate_owner_code_scenarios(self.o,self.b,h)

    def test_wrong_national_premium_or_policy_blocked(self):
        h=copy.deepcopy(self.h);h["years"][-1]["connected_buildings_self_written"]+=1
        with self.assertRaises(SyntheticBookError):simulate_owner_code_scenarios(self.o,self.b,h)
        h=copy.deepcopy(self.h);h["building_contract_observations"]["years"][-1]["contracts"]+=1
        with self.assertRaises(SyntheticBookError):simulate_owner_code_scenarios(self.o,self.b,h)

    def test_missing_county_source_rejected(self):
        self.o["kreise"].pop()
        with self.assertRaises(SyntheticBookError):validate_owner_source(self.o,self.b)

    def test_wrong_source_original_sha_rejected(self):
        self.o["source_original_sha256"]="0"*64
        with self.assertRaises(SyntheticBookError):validate_owner_source(self.o,self.b)

if __name__=="__main__":
    unittest.main()
