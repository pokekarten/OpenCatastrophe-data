# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-source and 10k research gust source receipt conservation."""
from pathlib import Path
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"research/observations/xws_kyrill_2007_original_netcdf_receipts_v0.toml"
SPATIAL=ROOT/"research/observations/xws_kyrill_2007_nrw_10k_fictional_hazard_join_receipt_v0.toml"


class OriginalKyrillNRWSiteResearchReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=tomllib.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.sites=tomllib.loads(SPATIAL.read_text(encoding="utf-8"))

    def test_four_source_bytes_one_actual_historical_storm(self):
        s=self.source
        self.assertEqual(s["canonical_existing_candidate_id"],"xws.european-extreme-windstorms")
        self.assertEqual(s["original_file_count"],4)
        self.assertEqual(s["physical_storm_count"],1)
        self.assertFalse(s["annual_event_probability_established"])
        self.assertFalse(s["original_latitude_longitude_are_WGS84"])
        self.assertFalse(s["independent_second_environment_original_sha_reproduction_verified"])
        self.assertEqual((s["grid_nlat"],s["grid_nlon"]),(158,178))
        self.assertEqual(s["publisher_data_rights"],
                         "Creative Commons Attribution 4.0 International (CC BY 4.0)")
        products={x["key"]:x for x in s["product"]}
        self.assertEqual(len(products),4)
        for item in products.values():
            self.assertEqual(item["original_bytes"],122304)
            self.assertRegex(item["original_sha256"],r"^[0-9a-f]{64}$")
            self.assertTrue(item["original_publisher_url"].startswith(
                "https://www.europeanwindstorms.org/repository/Kyrill/"))

    def test_full_10k_historical_hazard_conserves_fictional_source_only(self):
        s=self.sites
        self.assertEqual(s["fictional_source_building_location_count"],10000)
        self.assertEqual(s["fictional_insurance_policy_count"],10000)
        self.assertEqual(s["fictional_Kreis_count"],53)
        self.assertEqual(s["distinct_original_rotated_XWS_grid_cells_used"],79)
        self.assertEqual(s["fictional_building_TIV_eur_reconciled"],4826029500)
        self.assertEqual(s["historical_gust_missing_site_count"],0)
        self.assertTrue(s["recalibrated_95_bounds_bracket_mean_at_all_10000_sites"])
        self.assertAlmostEqual(s["mean_Kyrill_recalibrated_gust_m_per_s"],29.02092687625885)
        self.assertAlmostEqual(s["median_Kyrill_recalibrated_gust_m_per_s"],29.009979248046875)
        self.assertLess(s["min_Kyrill_recalibrated_gust_m_per_s"],
                        s["max_Kyrill_recalibrated_gust_m_per_s"])
        self.assertRegex(s["derived_site_hazard_csv_sha256"],r"^[0-9a-f]{64}$")
        self.assertEqual(s["github_derived_research_artifact_id"],13452772144)

    def test_source_and_real_insurer_loss_frequency_are_different(self):
        s=self.sites
        self.assertTrue(s["original_source_is_historical_not_synthetic_storm"])
        self.assertFalse(s["actual_RV_insured_risks_or_addresses_observed"])
        self.assertFalse(s["german_wind_construction_fragility_verified"])
        self.assertFalse(s["real_insurance_policy_terms_verified"])
        self.assertFalse(s["oasis_native_Kyrill_GUL_IL_RI_executed"])
        self.assertFalse(s["annual_event_occurrence_rate_or_frequency_verified"])
        self.assertFalse(s["gross_net_OEP_AEP_authorized"])
        self.assertFalse(s["XWS_four_footprint_products_are_four_independent_events"])
        self.assertFalse(s["source_files_republished_to_GitHub"])
        self.assertFalse(s["raw_third_party_NetCDF_stored_in_Neon"])


if __name__=="__main__":
    unittest.main()
