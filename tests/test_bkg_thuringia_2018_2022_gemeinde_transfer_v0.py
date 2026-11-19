# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic/offline negative tests: never admit a historic municipal shape as insured assets."""
from __future__ import annotations

import math
import unittest

from research_runners.bkg_thuringia_2018_2022_gemeinde_transfer_v0 import (
    BKGTransferError,
    BKG_2018_SHA256,
    BKG_2022_SHA256,
    CASES,
    _source_zip,
    polygon_transfer_summary,
)


def sample():
    # Entirely synthetic square-meter source polygon area counters.
    return polygon_transfer_summary(
        former_area_m2=40_000_000.0,
        recipient_new_area_m2=41_000_000.0,
        former_intersection_recipient_new_m2=39_000_000.0,
        donor_lost_area_m2=40_500_000.0,
        former_intersection_donor_lost_m2=39_000_000.0,
        former_intersection_recipient_2022_m2=39_800_000.0,
    )


class OfficialBKG2018MunicipalTransferTests(unittest.TestCase):
    def test_exact_2018_four_municipality_keys_pinned(self):
        self.assertEqual(CASES["Suhl"]["recipient_ags"], "16054")
        self.assertEqual(CASES["Suhl"]["donor_ags"], "16070")
        self.assertEqual(CASES["Suhl"]["former_municipalities"], {
            "16070017": "Gehlberg",
            "16070046": "Schmiedefeld am Rennsteig",
        })
        self.assertEqual(CASES["Sonneberg"]["recipient_ags"], "16072")
        self.assertEqual(CASES["Sonneberg"]["donor_ags"], "16073")
        self.assertEqual(CASES["Sonneberg"]["former_municipalities"], {
            "16073049": "Lichte",
            "16073066": "Piesau",
        })

    def test_pinned_2018_2022_source_digests_are_distinct(self):
        self.assertEqual(len(BKG_2018_SHA256), 64)
        self.assertEqual(len(BKG_2022_SHA256), 64)
        self.assertNotEqual(BKG_2018_SHA256, BKG_2022_SHA256)

    def test_numeric_transfer_measures_both_source_area_directions(self):
        report = sample()
        self.assertEqual(report["bkg_2018_former_municipality_union_km2"], 40)
        self.assertEqual(report["bkg_2018_to_2022_recipient_new_area_km2"], 41)
        self.assertEqual(report["bkg_2018_to_2022_donor_lost_area_km2"], 40.5)
        self.assertEqual(report["former_municipality_intersection_recipient_new_km2"], 39)
        self.assertEqual(report["former_municipality_intersection_donor_lost_km2"], 39)
        self.assertEqual(report["former_municipality_intersection_recipient_2022_km2"], 39.8)
        self.assertAlmostEqual(report["portion_of_recipient_gain_covered_by_old_municipalities"], 39 / 41)
        self.assertAlmostEqual(report["portion_of_old_municipalities_in_new_recipient_gain"], 39 / 40)
        self.assertAlmostEqual(report["portion_of_old_municipalities_in_recipient_2022"], 39.8 / 40)
        self.assertAlmostEqual(report["former_municipality_vs_recipient_gain_iou"], 39 / 42)

    def test_source_overlap_is_not_commercial_or_insurer_admission(self):
        report = sample()
        self.assertTrue(report["official_2018_and_2022_source_geometry_overlaps_measured"])
        self.assertTrue(report["research_only"])
        for key in ("exact_equality_of_2018_and_2022_polygons_proven",
                    "gadm4_1_or_materialcities_join_approved",
                    "real_insurer_exposure_locations_proven",
                    "transfer_of_region_level_building_gfa_authorized",
                    "carrier_tiv_or_insured_replacement_value_inferred",
                    "cat_model_input_admitted"):
            self.assertFalse(report[key])

    def test_no_intersection_is_mathematically_reported_not_faked(self):
        report = polygon_transfer_summary(100, 100, 0, 100, 0, 0)
        self.assertEqual(report["former_municipality_vs_recipient_gain_iou"], 0)
        self.assertFalse(report["transfer_of_region_level_building_gfa_authorized"])

    def test_all_source_values_must_be_numeric_finite(self):
        vals = (100.0, 120.0, 90.0, 110.0, 91.0, 95.0)
        for i in range(6):
            for invalid in (math.nan, math.inf, -math.inf, "90", True, None):
                example = list(vals)
                example[i] = invalid
                with self.subTest(index=i, invalid=str(invalid)):
                    with self.assertRaisesRegex(BKGTransferError, "nonnumeric"):
                        polygon_transfer_summary(*example)

    def test_all_three_denominator_areas_must_be_positive(self):
        for i in (0, 1, 3):
            for invalid in (0, -1):
                ex = [100.0, 100.0, 50.0, 100.0, 50.0, 90.0]
                ex[i] = invalid
                with self.subTest(index=i, invalid=invalid):
                    with self.assertRaisesRegex(BKGTransferError, "empty original"):
                        polygon_transfer_summary(*ex)

    def test_negative_overlap_blocked_in_all_three_directions(self):
        for i in (2, 4, 5):
            ex = [100.0, 100.0, 50.0, 100.0, 50.0, 90.0]
            ex[i] = -1.0
            with self.subTest(index=i):
                with self.assertRaisesRegex(BKGTransferError, "negative original"):
                    polygon_transfer_summary(*ex)

    def test_municipality_intersection_cannot_exceed_2018_area(self):
        for i in (2, 4, 5):
            ex = [100.0, 100.0, 50.0, 100.0, 50.0, 90.0]
            ex[i] = 101.0
            with self.subTest(index=i):
                with self.assertRaisesRegex(BKGTransferError, "cannot exceed"):
                    polygon_transfer_summary(*ex)

    def test_intersection_cannot_exceed_target_gain_area(self):
        with self.assertRaisesRegex(BKGTransferError, "cannot exceed"):
            polygon_transfer_summary(200, 100, 110, 200, 50, 90)

    def test_intersection_cannot_exceed_donor_loss_area(self):
        with self.assertRaisesRegex(BKGTransferError, "cannot exceed"):
            polygon_transfer_summary(200, 200, 100, 50, 70, 90)

    def test_no_implicit_unbounded_fake_zip_archive(self):
        for fake in (b"", b"PK" * 100, b"dummy" * 1000):
            with self.subTest(length=len(fake)):
                with self.assertRaisesRegex(BKGTransferError, "archive bounds"):
                    _source_zip(fake, BKG_2018_SHA256, "2018")

    def test_newer_geometry_does_not_prove_exact_administrative_effective_date(self):
        report = sample()
        # Legal effective dates are from the Landesamt, not source geometries.
        self.assertNotIn("legal_effective_date_from_polygon", report)
        self.assertFalse(report["gadm4_1_or_materialcities_join_approved"])


if __name__ == "__main__":
    unittest.main()
