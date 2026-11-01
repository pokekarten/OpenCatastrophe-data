# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original BKG single-tile source receipt guard; no source downloads."""
from __future__ import annotations

import math
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/research/bkg-berlin-kostra-original-window-receipt-20261101.toml"
ORIGINAL_URL = (
    "https://daten.gdz.bkg.bund.de/produkte/sonstige/starkregen/aktuell/"
    "be/maxdepth_kostra/s32790/"
    "starkregen_maxdepth_kostra_32790_5820_10_be.tif"
)
SHA = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"


class OriginalBkgSourceWindowReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_pinned_original_source_identity_full_sha_and_workflow(self):
        x = self.receipt
        self.assertEqual(x["source_url"], ORIGINAL_URL)
        self.assertEqual(x["source_full_tiff_sha256"], SHA)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", x["source_full_tiff_sha256"]))
        self.assertEqual(x["original_github_run_id"], 41348217549)
        self.assertEqual(
            x["original_github_run_url"],
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348217549",
        )
        self.assertEqual(x["original_execution_main_commit"],
                         "4ce081f8a6427d7ff674c9c8d3e1b6676f61b55d")
        self.assertEqual(x["source_bytes"], 47280200)
        self.assertTrue(x["source_http_content_length_verified"])
        self.assertFalse(x["original_source_bytes_persisted"])

    def test_pixel_grid_actual_nonfictional_raw_counts_are_conserved(self):
        x = self.receipt
        self.assertEqual(x["source_crs"], "EPSG:25832")
        self.assertEqual(x["source_raw_dtype"], "int16")
        self.assertEqual(x["source_raster_dimensions_pixels"], [10000, 10000])
        self.assertEqual(x["source_band_count"], 1)
        self.assertEqual(x["source_declared_nodata"], -9999.0)
        h, w = x["source_window_shape_pixels"]
        self.assertEqual([h, w], [217, 217])
        self.assertEqual(x["original_raw_cells_examined"], h*w)
        self.assertEqual(x["original_raw_cells_examined"],
                         x["original_source_masked_nodata_cells"] +
                         x["original_finite_unmasked_cells"])
        self.assertEqual(
            x["original_finite_unmasked_cells"],
            x["original_finite_unmasked_zeros"] +
            x["original_finite_unmasked_positives"] +
            x["original_finite_unmasked_negatives"],
        )
        self.assertEqual(
            [x["original_source_masked_nodata_cells"],
             x["original_finite_unmasked_zeros"],
             x["original_finite_unmasked_positives"],
             x["original_finite_unmasked_negatives"]],
            [4746, 4503, 37840, 0],
        )
        self.assertEqual(x["original_raw_min_if_valid"], 0.0)
        self.assertEqual(x["original_raw_max_if_valid"], 108.0)
        self.assertTrue(x["actual_pixel_mask_sample_verified"])

    def test_source_crs_and_physical_units_never_silently_admitted(self):
        x = self.receipt
        self.assertEqual(x["frozen_berlin_pilot_bbox_epsg25833_m"],
                         [391700, 5819950, 391900, 5820150])
        a, b, c, d = x["source_pilot_bbox_epsg25832_m"]
        self.assertTrue(all(math.isfinite(v) for v in (a, b, c, d)))
        self.assertTrue(790000 < a < c < 800000)
        self.assertTrue(5820000 < b < d < 5830000)
        self.assertTrue(x["research_only"])
        self.assertTrue(x["source_is_different_from_berlin_2022_named_zip"])
        for name in (
            "raw_pixel_physical_depth_units_verified",
            "raw_pixel_depth_scale_or_offset_verified",
            "scenario_equivalence_to_berlin_2022_zip_verified",
            "individual_building_hazard_join_verified",
            "insurer_exposure_or_cat_model_admitted",
        ):
            self.assertIs(x[name], False)
        self.assertTrue(x["source_licence_attribution"].startswith("BKG"))

    def test_duplicate_toml_field_is_never_silently_accepted(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads('source_bytes = 1\nsource_bytes = 2')


if __name__ == "__main__":
    unittest.main()
