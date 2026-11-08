# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed Gewobag/WBM public procurement segment and issuer IFRS checks."""
from __future__ import annotations

import copy
import hashlib
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))

from berlin_lwu_procurement_property_segment_crosscheck_v0 import (  # noqa: E402
    SEGMENTS, STOCK, INSURER, run, checked,
)


def load():
    return (tomllib.loads(SEGMENTS.read_text(encoding="utf-8")),
            tomllib.loads(STOCK.read_text(encoding="utf-8")),
            tomllib.loads(INSURER.read_text(encoding="utf-8")))


class BerlinPropertyProcurementSegments(unittest.TestCase):
    def setUp(self):
        self.source, self.stock, self.insurer = load()

    def check(self, source=None, stock=None, insurer=None):
        return checked(self.source if source is None else source,
                       self.stock if stock is None else stock,
                       self.insurer if insurer is None else insurer,
                       hashes={"segments": "a" * 64, "stock": "b" * 64, "insurer": "c" * 64})

    def test_valid_real_source_inputs_and_hashes(self):
        output = run()
        self.assertEqual(output["typed_source_sha256"]["segments"],
                         hashlib.sha256(SEGMENTS.read_bytes()).hexdigest())
        self.assertEqual(output["typed_source_sha256"]["stock"],
                         hashlib.sha256(STOCK.read_bytes()).hexdigest())
        self.assertTrue(output["independent_official_senate_original_pdf_receipt_checked"])
        self.assertFalse(output["original_ted_or_ifrs_external_source_bytes_verified_this_run"])

    def test_ado_issuer_2024_report_exact_numbers(self):
        row = self.check()["segments"]["gewobag_2019_ado_2024_ifrs"]
        self.assertEqual((row["property_objects"], row["dwellings"],
                          row["commercial_units"], row["parking_spaces"], row["other_units"]),
                         (21, 5894, 65, 1433, 139))
        self.assertEqual(row["year_end_2024_market_fair_value_eur_thousand"], 821190)
        self.assertEqual(row["potential_development_component_in_market_value_eur_thousand"], 15010)
        self.assertEqual(row["independently_observed_2025_gewobag_corporate_dwelling_total"], 75091)

    def test_wbm_nine_commercial_three_awardees_not_27_insured_assets(self):
        row = self.check()["segments"]["wbm_september_2026_pure_commercial"]
        self.assertEqual(row["pure_commercial_objects_described"], 9)
        self.assertEqual(len(row["named_awardees"]), 3)
        self.assertIn("R+V Allgemeine Versicherung AG", row["named_awardees"])
        self.assertEqual(row["independently_observed_2025_wbm_corporate_residential_dwelling_total"], 34040)
        self.assertFalse(row["three_awardees_means_twenty_seven_distinct_insured_objects"])
        self.assertFalse(row["exact_carrier_allocation_of_nine_objects_observed"])

    def test_global_no_admitted_or_spatial_or_real_tiv(self):
        r = self.check()
        self.assertTrue(r["research_only_not_admitted"])
        for k in ("market_fair_value_equals_cat_reinstatement_tiv",
                  "awarded_named_insurers_equal_coverage_per_object",
                  "individual_insured_buildings_observed", "model_cat_exposure_admitted"):
            self.assertFalse(self.source[k])
        self.assertFalse(r["segments"]["gewobag_2019_ado_2024_ifrs"][
            "market_fair_value_means_insured_reinstatement_tiv"])

    def test_source_2024_and_2026_clocks_kept_distinct(self):
        self.check()
        self.assertEqual(self.source["gewobag_2024_tender"]["notice_published"], "2024-09-13")
        self.assertEqual(self.source["gewobag_2024_ado_issuer_ifrs"]["valuation_date"], "2024-12-31")
        self.assertEqual(self.source["wbm_2026_commercial_award"]["award_date"], "2026-09-21")

    def test_ado_rounded_6000_never_added_to_5894(self):
        row = self.check()["segments"]["gewobag_2019_ado_2024_ifrs"]
        self.assertFalse(row["tender_rounded_six_thousand_dwellings_is_separate_added_stock"])
        self.assertFalse(row["ado_2024_subset_membership_in_2025_total_individually_crosswalk_verified"])

    def test_tender_not_same_as_award(self):
        self.check()
        self.assertFalse(self.source["gewobag_2024_tender"][
            "actual_awarded_carrier_legal_names_verified_from_this_notice"])
        self.assertFalse(self.source["wbm_2026_commercial_award"][
            "official_ted_eforms_original_http_bytes_verified"])

    def test_ifrs_market_value_cannot_be_reported_as_tiv(self):
        x = copy.deepcopy(self.source)
        x["gewobag_2024_ado_issuer_ifrs"]["reported_market_value_is_insured_tiv"] = True
        with self.assertRaises(ValueError):
            self.check(source=x)
        x = copy.deepcopy(self.source)
        x["market_fair_value_equals_cat_reinstatement_tiv"] = True
        with self.assertRaises(ValueError):
            self.check(source=x)

    def test_ifrs_numeric_or_valued_date_tampering_blocks(self):
        for name, changed in (
            ("reported_property_objects", 22),
            ("reported_residential_dwellings", 6000),
            ("reported_market_fair_value_eur_thousand", 821190000),
            ("valuation_date", "2025-12-31"),
        ):
            x = copy.deepcopy(self.source)
            x["gewobag_2024_ado_issuer_ifrs"][name] = changed
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check(source=x)

    def test_tender_10_percent_not_carrier_insured_growth(self):
        x = copy.deepcopy(self.source)
        x["gewobag_2024_tender"]["tender_option_is_realised_growth_or_2025_insured_risk"] = True
        with self.assertRaises(ValueError):
            self.check(source=x)
        x = copy.deepcopy(self.source)
        x["gewobag_2024_tender"]["tender_option_increase_usable_floor_area_pct_max"] = 20
        with self.assertRaises(ValueError):
            self.check(source=x)

    def test_secondary_ted_hash_claims_rejected(self):
        for grp, key in (("gewobag_2024_tender", "original_ted_notice_download_sha256_verified"),
                         ("gewobag_2024_ado_issuer_ifrs", "source_original_pdf_sha256_verified"),
                         ("wbm_2026_commercial_award", "official_ted_eforms_original_http_bytes_verified")):
            x = copy.deepcopy(self.source)
            x[grp][key] = True
            with self.subTest(group=grp), self.assertRaises(ValueError):
                self.check(source=x)

    def test_wbm_awardee_addition_or_implied_all_9_covered_rejected(self):
        x = copy.deepcopy(self.source)
        x["wbm_2026_commercial_award"]["reported_winners"].append("An invented insurer")
        with self.assertRaises(ValueError):
            self.check(source=x)
        x = copy.deepcopy(self.source)
        x["wbm_2026_commercial_award"]["each_winner_covers_all_nine_objects_proven"] = True
        with self.assertRaises(ValueError):
            self.check(source=x)

    def test_wbm_award_fraud_or_2025_residential_conflation_blocked(self):
        for key in ("commercial_objects_are_2025_wbm_residential_dwellings",
                    "award_date_proves_2025_residential_carrier_contract",
                    "carrier_share_and_policy_limits_disclosed"):
            x = copy.deepcopy(self.source)
            x["wbm_2026_commercial_award"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(source=x)

    def test_no_double_count_2025_total_after_ado_acquisition(self):
        x = copy.deepcopy(self.stock)
        x["national_published_row_totals"]["gewobag"] += 5894
        with self.assertRaises(ValueError):
            self.check(stock=x)

    def test_irrelevant_senate_corporate_role_forgery_rejected(self):
        x = copy.deepcopy(self.insurer)
        x["housing_companies"][3]["rva_allgemeine_explicitly_named"] = True
        with self.assertRaises(ValueError):
            self.check(insurer=x)

    def test_sorted_awardees_output_stable_to_input_order(self):
        a = self.check()
        x = copy.deepcopy(self.source)
        x["wbm_2026_commercial_award"]["reported_winners"].reverse()
        self.assertEqual(self.check(source=x), a)

    def test_missing_source_sections_rejected(self):
        for name in ("gewobag_2024_tender", "gewobag_2024_ado_issuer_ifrs",
                     "wbm_2026_commercial_award"):
            x = copy.deepcopy(self.source)
            x.pop(name)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check(source=x)


if __name__ == "__main__":
    unittest.main()
