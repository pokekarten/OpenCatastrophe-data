# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline pinned original Berlin building-exterior source receipt (no network)."""
from __future__ import annotations

import math
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (ROOT / "docs/research" /
           "berlin-bld4-bkg-original-exterior-ring-receipt-20261101.toml")
BKG_SHA = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"
WFS_SHA = "c4342109c0c13b31996d7cb9a5a16db56af3e536dc4910938a9fc72bab049bba"
EXPECTED = [
    ((0, 1), 296.465049, 28.156356, 94.312623, 173.996069, 0.413098),
    ((1, 3), 613.724262, 170.126378, 141.690844, 301.907040, 0.508074),
    ((3, 5), 634.364187, 236.862675, 121.530717, 275.970795, 0.564965),
]


class OriginalBerlinBkgExteriorRingReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_original_provider_run_and_two_independent_source_identities(self):
        d = self.d
        self.assertEqual(d["original_github_actions_run_id"], 41350285830)
        self.assertEqual(d["original_github_actions_run_url"],
                         "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41350285830")
        self.assertEqual(d["original_main_commit"],
                         "63a13bd477067527dc9e67e6e6d4ba817189178f")
        self.assertEqual(d["original_bkg_full_file_sha256_locally_verified"], BKG_SHA)
        self.assertEqual(d["original_bkg_tiff_bytes"], 47280200)
        self.assertEqual(d["original_alkis_wfs_response_sha256"], WFS_SHA)
        self.assertTrue(d["original_source_wfs_response_mutable"])
        self.assertIn("maxdepth_kostra/s32790/", d["original_bkg_source_url"])
        self.assertEqual(d["original_alkis_clipped_building_count"], 5)

    def test_mutually_exclusive_disjoint_bands_and_fractional_area_conservation(self):
        d = self.d
        self.assertTrue(d["all_exterior_bands_unique_and_disjoint"])
        bands = d["exterior_bands"]
        self.assertEqual(len(bands), len(EXPECTED))
        for band, (distance, area, positive, zero, missing, valid) in zip(bands, EXPECTED):
            with self.subTest(distance=distance):
                self.assertEqual(
                    (band["distance_min_m"], band["distance_max_m"]), distance
                )
                for key, exp in (
                    ("sample_area_m2", area),
                    ("positive_raw_area_m2", positive),
                    ("valid_zero_area_m2", zero),
                    ("source_nodata_area_m2", missing),
                    ("valid_numeric_support_fraction", valid),
                ):
                    self.assertAlmostEqual(band[key], exp, places=6)
                self.assertEqual(band["outside_window_area_m2"], 0)
                self.assertTrue(math.isclose(
                    band["sample_area_m2"],
                    sum(band[x] for x in (
                        "positive_raw_area_m2", "valid_zero_area_m2",
                        "source_nodata_area_m2", "outside_window_area_m2")),
                    rel_tol=0.0, abs_tol=0.000003))
                self.assertAlmostEqual(
                    (band["positive_raw_area_m2"] + band["valid_zero_area_m2"])
                    / band["sample_area_m2"],
                    valid, delta=0.000001)

    def test_original_building_interior_nodata_stays_missing(self):
        d = self.d
        self.assertEqual(d["fixed_pilot_crs"], "EPSG:25833")
        self.assertEqual(d["raster_crs"], "EPSG:25832")
        self.assertEqual(d["original_raster_resolution_metres"], 1)
        self.assertEqual(d["original_raster_window_cells"], 47089)
        self.assertEqual(d["original_building_area_total_m2"], 683.311267)
        self.assertAlmostEqual(
            d["original_building_positive_raw_area_m2"]
            + d["original_building_valid_zero_area_m2"]
            + d["original_building_nodata_area_m2"]
            + d["original_building_outside_window_area_m2"],
            d["original_building_area_total_m2"], delta=0.000002)
        self.assertGreater(d["original_building_nodata_area_m2"]
                           / d["original_building_area_total_m2"], .97)
        self.assertEqual(d["original_buildings_any_positive_code"], 3)
        self.assertEqual(d["original_buildings_all_area_valid"], 0)
        self.assertEqual(d["original_buildings_without_valid_codes"], 2)

    def test_no_source_units_entry_elevation_damage_or_insurer_admission(self):
        d = self.d
        self.assertTrue(d["research_only"])
        self.assertTrue(d["distance_is_projected_planar_not_building_entry_distance"])
        for key in (
            "original_numeric_raw_code_physical_depth_unit_verified",
            "original_raster_zero_indicates_observed_dryness",
            "original_raster_nodata_indicates_observed_dryness",
            "actual_building_entrance_and_basement_elevation_verified",
            "model_product_building_vintage_consistent",
            "annual_loss_probability_or_recurrence_estimated",
            "individual_building_ids_or_geometry_exported",
            "original_source_data_persisted",
            "insured_building_exposure_or_cat_loss_admitted",
        ):
            self.assertIs(d[key], False)
        self.assertIn("DL-DE/BY-2.0", d["bkg_data_reuse_licence_label"])

    def test_duplicates_and_infinite_float_cannot_be_reinterpreted(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("sample_area_m2=1\nsample_area_m2=2")
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("[[exterior_bands]]\ndistance_min_m=0\ndistance_min_m=1")


if __name__ == "__main__":
    unittest.main()
