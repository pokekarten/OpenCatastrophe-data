# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial offline tests for actual BKG source evidence CAT admission gate."""
from __future__ import annotations

import copy
import math
from pathlib import Path
import tomllib
import unittest

from research_runners.bkg_berlin_source_readiness_gate_v0 import (
    EvidenceBlocked, RECEIPT, BKG_TIFF_SHA, WFS_RESPONSE_SHA,
    assess_receipt,
)


class BerlinBkgReadinessGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))

    def fresh(self):
        return copy.deepcopy(self.original)

    def test_actual_2026_source_receipt_is_screening_only(self):
        result = assess_receipt(self.fresh())
        self.assertEqual(result["source_evidence_run_id"], 41350285830)
        self.assertTrue(result["raw_geometric_support_screening_available"])
        self.assertEqual(len(result["original_exterior_support"]), 3)
        self.assertAlmostEqual(result["building_nodata_fraction"], 0.974849, places=4)
        self.assertFalse(result["cat_model_input_admitted"])
        self.assertFalse(result["building_depth_calculation_authorized"])
        self.assertFalse(result["insured_loss_or_tiv_calculation_authorized"])
        self.assertFalse(result["physical_depth_unit_or_scale_verified"])
        self.assertEqual(len(result["blockers"]), 6)
        forbidden_output_keys = ("estimated_depth_m", "flooded_building_count",
                                 "annual_probability", "insured_loss_eur", "tiv_eur")
        for key in forbidden_output_keys:
            self.assertNotIn(key, result)

    def test_ring_area_conservation_and_support_not_raw_flood_probability(self):
        result = assess_receipt(self.fresh())
        actual = result["original_exterior_support"]
        self.assertEqual([x["distance_band_m"] for x in actual],
                         [[0, 1], [1, 3], [3, 5]])
        self.assertEqual([x["valid_numeric_support_fraction"] for x in actual],
                         [0.413098, 0.508074, 0.564965])
        for x in actual:
            self.assertTrue(x["positive_raw_code_is_not_calibrated_depth"])
            self.assertGreater(x["nodata_or_outside_fraction"], 0)
            self.assertGreaterEqual(x["positive_raw_code_area_fraction_of_total"], 0)
            self.assertLessEqual(x["positive_raw_code_area_fraction_of_total"], 1)
            self.assertAlmostEqual(
                x["valid_numeric_support_fraction"] +
                x["nodata_or_outside_fraction"], 1, delta=2e-6)

    def test_changed_source_sha_wfs_snapshot_and_source_url_block(self):
        for key, fake in [
            ("original_bkg_full_file_sha256_locally_verified", "0"*64),
            ("original_alkis_wfs_response_sha256", "a"*64),
            ("original_main_commit", "a"*40),
            ("original_bkg_tiff_bytes", 47280201),
            ("original_bkg_source_url", "https://another.example/changed.tif"),
            ("original_alkis_clipped_building_count", 6),
            ("raster_crs", "EPSG:25833"),
            ("original_github_actions_run_id", 2),
        ]:
            with self.subTest(key=key):
                document = self.fresh()
                document[key] = fake
                with self.assertRaises(EvidenceBlocked):
                    assess_receipt(document)

    def test_ambiguous_or_forged_unit_claim_is_rejected(self):
        for key in [
            "original_numeric_raw_code_physical_depth_unit_verified",
            "actual_building_entrance_and_basement_elevation_verified",
            "model_product_building_vintage_consistent",
            "annual_loss_probability_or_recurrence_estimated",
            "insured_building_exposure_or_cat_loss_admitted",
        ]:
            with self.subTest(key=key):
                d = self.fresh()
                d[key] = True
                with self.assertRaisesRegex(EvidenceBlocked, "unauthorized promotion"):
                    assess_receipt(d)
        d = self.fresh()
        del d["original_numeric_raw_code_physical_depth_unit_verified"]
        with self.assertRaises(EvidenceBlocked):
            assess_receipt(d)

    def test_corrupt_exterior_row_and_fabricated_area_sum_rejected(self):
        changes = [
            ("sample_area_m2", 1000),
            ("positive_raw_area_m2", 9999),
            ("valid_zero_area_m2", 0),
            ("source_nodata_area_m2", -1),
            ("valid_numeric_support_fraction", 2.0),
            ("distance_min_m", 2),
            ("outside_window_area_m2", float("nan")),
        ]
        for key, fake in changes:
            with self.subTest(key=key):
                d = self.fresh()
                d["exterior_bands"][0][key] = fake
                with self.assertRaises(EvidenceBlocked):
                    assess_receipt(d)
        d = self.fresh()
        d["original_building_nodata_area_m2"] = 0.0
        with self.assertRaises(EvidenceBlocked):
            assess_receipt(d)

    def test_relabelled_zero_as_nodata_even_with_conserved_sum_rejected(self):
        d = self.fresh()
        row = d["exterior_bands"][0]
        row["source_nodata_area_m2"] += 1
        row["valid_zero_area_m2"] -= 1
        row["valid_numeric_support_fraction"] = (
            row["valid_zero_area_m2"] + row["positive_raw_area_m2"]
        ) / row["sample_area_m2"]
        with self.assertRaisesRegex(EvidenceBlocked, "original pinned"):
            assess_receipt(d)

    def test_duplicate_or_nonfinite_toml_cannot_sneak_into_canonical_receipt(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("original_bkg_tiff_bytes=1\noriginal_bkg_tiff_bytes=2")
        d = self.fresh()
        d["exterior_bands"][2]["source_nodata_area_m2"] = float("inf")
        with self.assertRaises(EvidenceBlocked):
            assess_receipt(d)

    def test_pinned_original_hash_values_not_a_source_download(self):
        self.assertEqual(
            self.original["original_bkg_full_file_sha256_locally_verified"],
            BKG_TIFF_SHA)
        self.assertEqual(self.original["original_alkis_wfs_response_sha256"],
                         WFS_RESPONSE_SHA)
        self.assertFalse(self.original["original_source_data_persisted"])
        self.assertFalse(self.original["individual_building_ids_or_geometry_exported"])


if __name__ == "__main__":
    unittest.main()
