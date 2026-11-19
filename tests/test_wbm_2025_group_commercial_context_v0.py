# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-year & non-allocation safeguards for official WBM group-level stats."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from research_runners import wbm_like_nine_fictional_oed_v0 as gen

DATA = (
    Path(__file__).resolve().parents[1] / "research" / "observations" /
    "wbm_2025_group_commercial_metrics_separate_from_nine_award_v0.toml"
)


class WBM2025GroupSourceMetricsTests(unittest.TestCase):
    def setUp(self):
        self.r = tomllib.loads(DATA.read_text(encoding="utf-8"))

    def test_original_wbm_publisher_and_year(self):
        self.assertEqual(self.r["source_publication_date"], "2026-06-03")
        self.assertEqual(self.r["source_reporting_period"], "2025")
        self.assertEqual(self.r["source_level"], "entire_WBM_group")
        self.assertEqual(
            self.r["source_original_url"],
            "https://www.wbm.de/presse/pressemitteilung/detail/"
            "wbm-setzt-strategischen-wachstumskurs-erfolgreich-fort/")
        self.assertFalse(self.r["raw_publisher_source_bytes_sha256_pinned"])

    def test_commercial_area_rent_and_vacancy_are_aggregate(self):
        c = self.r["commercial_group"]
        self.assertEqual(c["managed_rental_commercial_floor_area_sqm_approx"], 314000)
        self.assertEqual(c["average_net_cold_rent_eur_per_sqm"], "15.62")
        self.assertEqual(c["vacancy_percent"], "1.4")
        self.assertEqual(c["tenant_turnover_percent"], "4.6")
        self.assertFalse(c["actual_insured_site_coordinates_available"])

    def test_portfolio_59bn_is_group_market_value_not_tiv(self):
        g = self.r["all_asset_classes_group"]
        self.assertEqual(g["market_portfolio_value_eur_approx"], 5900000000)
        self.assertTrue(g["this_is_not_replacement_cost_or_insurance_TIV"])
        self.assertEqual(g["number_of_apartments_approx"], 35000)

    def test_no_source_to_insured_nine_building_allocation(self):
        self.assertFalse(self.r["is_the_nine_pure_commercial_2026_policy_object_list"])
        self.assertFalse(self.r["can_allocate_numbers_to_the_nine_TED_objects"])
        self.assertFalse(
            self.r["award_2026_separate_source"]["approved_group_to_award_value_allocation"])

    def test_no_real_carrier_ceded_or_CAT_admission(self):
        for k in (
            "source_values_are_building_replacement_TIV",
            "source_values_are_actual_2027_insurance_policy_values",
            "actual_RV_HDI_Helvetia_exposure_or_contract_coverage_established",
            "real_insurer_CAT_exposure_admitted",
        ):
            with self.subTest(k=k):
                self.assertFalse(self.r[k])

    def test_independent_oed_demo_not_scaled_to_wbm_metrics(self):
        demo = self.r["completely_fictional_oed_5_demo"]
        self.assertEqual(demo["location_count"], gen.COUNT)
        self.assertEqual(demo["invented_building_tiv_total_eur"],
                         gen.TOTAL_FAKE_BUILDING_EUR)
        self.assertTrue(demo["invented_amount_does_not_derive_from_2025_group_market_value"])
        self.assertTrue(demo["invented_amount_does_not_derive_from_314000_sqm"])
        self.assertTrue(demo["invented_amount_does_not_derive_from_15_62_eur_rent"])

    def test_real_Sep_notice_count_only_synthetic_grid_dimension(self):
        self.assertEqual(
            self.r["award_2026_separate_source"]["ted_publication_number"],
            "668506-2026")
        self.assertEqual(
            self.r["award_2026_separate_source"]
            ["published_described_pure_commercial_object_count"], 9)
        self.assertNotEqual(
            self.r["commercial_group"]["managed_rental_commercial_floor_area_sqm_approx"],
            gen.TOTAL_FAKE_BUILDING_EUR)


if __name__ == "__main__":
    unittest.main()
