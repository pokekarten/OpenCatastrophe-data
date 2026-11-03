# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Invented pixel arrays only; no NASA original/provider bytes or coordinates."""
from __future__ import annotations

import unittest

from research_runners.nasa_opera_dswx_s1_v1_class_preflight import (
    DswxV1PreflightBlocked, PRODUCT, PRODUCT_VERSION, summarize_wtr_bwtr_v1,
)


def run(wtr, bwtr, *, width=None, height=1, product=PRODUCT, version=PRODUCT_VERSION):
    return summarize_wtr_bwtr_v1(
        product=product, product_version=version,
        width=len(wtr) if width is None else width, height=height,
        wtr=wtr, bwtr=bwtr,
    )


class DswxS1V1PixelContractTests(unittest.TestCase):
    def test_all_original_v1_class_codes_and_conservation(self):
        r = run([0, 1, 3, 250, 251, 255], [0, 1, 1, 250, 251, 255])
        self.assertEqual(r["sample_pixel_count"], 6)
        self.assertEqual(r["water_classified_cells"], 2)
        self.assertEqual(r["not_water_classified_cells_not_dry_ground_proof"], 1)
        self.assertEqual(r["masked_or_nodata_cells_excluded"], 3)
        self.assertEqual(r["valid_classified_cells"], 3)
        self.assertEqual(sum(r["wtr_classes"].values()), 6)
        self.assertTrue(r["all_cell_counts_conserved"])

    def test_inundated_vegetation_is_water_not_a_depth(self):
        r = run([3], [1])
        self.assertEqual(r["water_classified_cells"], 1)
        self.assertFalse(r["water_depth_or_return_period_inferred"])
        self.assertFalse(r["baseline_water_change_or_flood_cause_inferred"])

    def test_masked_and_nodata_never_become_dry(self):
        r = run([250, 251, 255], [250, 251, 255])
        self.assertEqual(r["valid_classified_cells"], 0)
        self.assertEqual(r["not_water_classified_cells_not_dry_ground_proof"], 0)
        self.assertFalse(r["cat_model_input_admitted"])

    def test_not_water_does_not_claim_dry_or_no_insured_loss(self):
        r = run([0], [0])
        self.assertEqual(r["not_water_classified_cells_not_dry_ground_proof"], 1)
        self.assertFalse(r["insurer_loss_or_property_exposure_inferred"])

    def test_pre_release_class_codes_block(self):
        # Historical 2023 v0.2.1 has different values for masks/water.
        for code in (2, 4, 5, 6, 7, 120, 252, 253, 254):
            with self.subTest(code=code), self.assertRaises(DswxV1PreflightBlocked):
                run([code], [code])

    def test_wrong_product_and_version_block(self):
        for p, v in (
            ("OPERA_L3_DSWX-HLS_V1", "1.0"),
            ("OPERA_L3_DSWX-S1_V1", "0.2.1"),
            ("OPERA_L3_DSWX-S1_V1", "1.1"),
            ("OPERA_L3_DSWX-S1_V1", ""),
        ):
            with self.subTest(p=p, v=v), self.assertRaises(DswxV1PreflightBlocked):
                run([1], [1], product=p, version=v)

    def test_binary_water_agreement_required(self):
        for a, b in ((3, 3), (1, 0), (0, 1), (250, 0), (255, 250), (251, 255)):
            with self.subTest(a=a, b=b), self.assertRaises(DswxV1PreflightBlocked):
                run([a], [b])

    def test_bool_float_and_string_cells_block(self):
        for code in (True, 1.0, "1", None):
            with self.subTest(code=code), self.assertRaises(DswxV1PreflightBlocked):
                run([code], [1])

    def test_empty_and_mismatched_arrays_block(self):
        for a, b, w in (([], [], 0), ([1], [], 1), ([1, 1], [1, 1], 1)):
            with self.subTest(a=a, b=b), self.assertRaises(DswxV1PreflightBlocked):
                run(a, b, width=w)

    def test_pixel_geometry_budget_and_strict_type(self):
        for w, h in ((4097, 1), (129, 1), (1, 129), (0, 1), (True, 1)):
            with self.subTest(w=w, h=h), self.assertRaises(DswxV1PreflightBlocked):
                run([1], [1], width=w, height=h)

    def test_max_window_passes_with_all_observed_water(self):
        r = run([1] * 4096, [1] * 4096, width=64, height=64)
        self.assertEqual(r["water_classified_cells"], 4096)
        self.assertEqual(r["masked_or_nodata_cells_excluded"], 0)

    def test_no_provider_or_rights_promotion(self):
        r = run([1, 0, 255], [1, 0, 255])
        for key in (
            "source_granule_bytes_or_metadata_authenticated",
            "source_observation_time_verified",
            "source_geolocation_or_ancillary_masks_verified",
            "source_rights_or_commercial_use_approved",
            "cat_model_input_admitted",
        ):
            self.assertIs(r[key], False)


if __name__ == "__main__":
    unittest.main()
