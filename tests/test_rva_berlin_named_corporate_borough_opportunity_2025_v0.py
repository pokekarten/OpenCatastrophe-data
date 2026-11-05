# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Separate insurer named customer vs same-year corporate borough DWELLING opportunity."""
from pathlib import Path
import copy,tomllib,unittest,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_berlin_named_corporate_borough_opportunity_sensitivity_v0 import validate,run,EXPECTED,OTHER,validate_pinned_original_pdf_receipt,ORIGINAL_PDFS  # noqa: E402
STOCK=ROOT/"research/observations/rva_berlin_senate_housing_borough_stock_2025_v0.toml"
INSURER=ROOT/"research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml"
def load():return tomllib.loads(STOCK.read_text()),tomllib.loads(INSURER.read_text())

class NamedRvaBerlinCorporateBoroughOpportunity(unittest.TestCase):
    def setUp(self):self.s,self.i=load()

    def test_both_exact_original_pdfs_are_a_required_scenario_prerequisite(self):
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
        proof=validate_pinned_original_pdf_receipt(receipt)
        self.assertTrue(proof["official_2025_senate_two_original_pdf_hashes_matched"])
        self.assertFalse(proof["current_run_fetched_original_pdf_bytes"])
        self.assertFalse(proof["specific_insured_rva_buildings_observed"])
        self.assertTrue(validate(self.s,self.i)["official_source_pdf_provenance"][
            "official_2025_senate_two_original_pdf_hashes_matched"
        ])

    def test_original_insurer_pdf_sha_mismatch_blocks(self):
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
        receipt["documents"][0]["original_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"source hash/bytes/scope drift"):
            validate_pinned_original_pdf_receipt(receipt)

    def test_original_dwelling_pdf_page_count_mismatch_blocks(self):
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
        receipt["documents"][1]["original_pages"]=4
        with self.assertRaisesRegex(ValueError,"source hash/bytes/scope drift"):
            validate_pinned_original_pdf_receipt(receipt)

    def test_false_insured_property_sites_from_govt_pdf_blocks(self):
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
        receipt["actual_RV_insured_berlin_building_sites_verified"]=True
        with self.assertRaisesRegex(ValueError,"non-insurer source scope changed"):
            validate_pinned_original_pdf_receipt(receipt)

    def test_missing_one_original_pdf_blocks_all_scenarios(self):
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
        receipt["documents"].pop()
        with self.assertRaisesRegex(ValueError,"PDF receipts missing"):
            validate_pinned_original_pdf_receipt(receipt)

    def test_exact_official_six_lwu_plus_berlinovo_reconciled(self):
        a=validate(self.s,self.i)
        self.assertEqual(len(a["boroughs"]),12)
        self.assertEqual(sum(EXPECTED[:6]),376278)
        self.assertEqual(a["published_company_totals"]["berlinovo"],18666)
        for j,k in enumerate(self.s["company_column_order"]):
            self.assertEqual(a["published_berlin_12_borough_totals"][k]+OTHER[j],EXPECTED[j])

    def test_actual_april_named_three_accounts_followed_by_june_corporate_dwelling_stock(self):
        a=validate(self.s,self.i)
        self.assertEqual(a["three_named_RV_linked_corporate_total_dwellings_including_other"],165731)
        self.assertEqual(a["three_named_RV_linked_corporate_12_borough_dwellings"],162883)
        self.assertFalse(self.s["june_2025_corporate_stock_same_as_april_2025_policy_schedule"])

    def test_publisher_representative_12_borough_values(self):
        m={r["borough_name"]:r for r in validate(self.s,self.i)["boroughs"]}
        self.assertEqual(m["Pankow"]["gesobau"],19578)
        self.assertEqual(m["Reinickendorf"]["gesobau"],18049)
        self.assertEqual(m["Friedrichshain-Kreuzberg"]["wbm"],16531)
        self.assertEqual(m["Mitte"]["wbm"],12455)
        self.assertEqual(m["Marzahn-Hellersdorf"]["degewo"],19566)
        self.assertEqual(m["Treptow-Koepenick"]["degewo"],16656)
        self.assertEqual(m["Lichtenberg"]["howoge"],62086)

    def test_three_hypotheses_not_tiv_or_actual_policy_counts(self):
        out=run(self.s,self.i)
        self.assertEqual(len(out["scenarios"]),3)
        self.assertTrue(all(x is False for x in out["insurer_exposure_admission"].values()))
        for case in out["scenarios"].values():
            self.assertEqual(len(case["boroughs"]),12)
            self.assertTrue(case["case_is_declared_hypothesis_not_observation"])
            self.assertFalse(case["count_of_real_RV_insured_buildings_estimated"])
            self.assertFalse(case["insurer_portfolio_actual_TIV_observed"])

    def test_known_corporate_dwellings_unknown_degewo_share_sensitivity(self):
        r=run(self.s,self.i)["scenarios"]
        self.assertEqual(r["degewo_0pct_hypothetical_share"]["hypothetical_total_account_dwelling_equivalents"],"82787")
        self.assertEqual(r["degewo_50pct_hypothetical_share"]["hypothetical_total_account_dwelling_equivalents"],"122835")
        self.assertEqual(r["degewo_100pct_hypothetical_share"]["hypothetical_total_account_dwelling_equivalents"],"162883")

    def test_borough_order_independent(self):
        original=run(self.s,self.i)
        self.s["boroughs"].reverse()
        inverted=run(self.s,self.i)
        # State receipt unchanged, rows repeat in source original order not normalized.
        for k in original["scenarios"]:
            self.assertEqual(
                {r["berlin_borough"]:r["hypothetical_RV_linked_account_dwelling_equivalent_twice"] for r in original["scenarios"][k]["boroughs"]},
                {r["berlin_borough"]:r["hypothetical_RV_linked_account_dwelling_equivalent_twice"] for r in inverted["scenarios"][k]["boroughs"]},
            )

    def test_wrong_senate_source_or_date_rejected(self):
        for k,v in [("source_answer_date","2026-11-05"),
                    ("source_stock_date_six_lwu","2025-12-31"),
                    ("source_official_url","https://example.com/other")]:
            c=copy.deepcopy(self.s);c[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):validate(c,self.i)

    def test_wrong_insurer_role_overclaim_rejected(self):
        c=copy.deepcopy(self.i)
        r=next(x for x in c["housing_companies"] if x["legal_name"]=="degewo AG")
        r["named_insurers"]=["R+V Allgemeine Versicherung AG"]
        with self.assertRaises(ValueError):validate(self.s,c)
        c=copy.deepcopy(self.i)
        r=next(x for x in c["housing_companies"] if x["legal_name"]=="GESOBAU AG")
        r["rva_allgemeine_explicitly_named"]=False
        with self.assertRaises(ValueError):validate(self.s,c)

    def test_other_stock_not_smeared_over_twelve_berlin_boroughs(self):
        a=validate(self.s,self.i)
        self.assertEqual(a["published_other_not_borough_assignable"]["degewo"],2541)
        self.assertEqual(a["published_other_not_borough_assignable"]["gesobau"],307)
        self.assertEqual(sum(r["degewo"] for r in a["boroughs"]),80096)

    def test_competitor_housing_stocks_not_rva(self):
        a=validate(self.s,self.i)
        self.assertEqual(a["published_company_totals"]["howoge"],82152)
        r=run(self.s,self.i)
        self.assertNotIn("howoge",r["scenarios"]["degewo_100pct_hypothetical_share"]["boroughs"][0])

    def test_no_dwellings_to_physical_buildings_promotion(self):
        c=copy.deepcopy(self.s)
        c["insured_buildings_count_observed"]=True
        with self.assertRaises(ValueError):validate(c,self.i)
        c=copy.deepcopy(self.s);c["insurance_contract_count_observed_from_this_matrix"]=True
        with self.assertRaises(ValueError):validate(c,self.i)
        c=copy.deepcopy(self.s);c["covered_tiv_or_rv_coinsurance_percent_observed"]=True
        with self.assertRaises(ValueError):validate(c,self.i)

    def test_fake_company_value_or_extra_borough_rejected(self):
        c=copy.deepcopy(self.s)
        c["boroughs"][0]["gesobau"]+=1
        with self.assertRaises(ValueError):validate(c,self.i)
        c=copy.deepcopy(self.s);c["boroughs"].pop()
        with self.assertRaises(ValueError):validate(c,self.i)

if __name__=="__main__":unittest.main()
