# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original BKG GDAL scalar receipt; independent from TIFF and WFS IO."""
from __future__ import annotations

import copy
import math
import tomllib
import unittest

from research_runners.bkg_berlin_source_readiness_gate_v0 import (
    BKG_TIFF_SHA,
    EvidenceBlocked,
    NATIVE_UNIT_RECEIPT,
    NATIVE_UNIT_RUN_ID,
    RECEIPT,
    assess_both_receipts,
    assess_native_unit_claims,
)


class OriginalBkgNativeBandUnitReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spatial = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.native = tomllib.loads(NATIVE_UNIT_RECEIPT.read_text(encoding="utf-8"))

    def fresh(self):
        return copy.deepcopy(self.native)

    def test_exact_original_native_band_unit_evidence_is_explicitly_uncalibrated(self):
        result = assess_native_unit_claims(self.fresh())
        self.assertEqual(result["original_native_tiff_band_metadata_run_id"],
                         NATIVE_UNIT_RUN_ID)
        self.assertTrue(result["source_sha_crosschecked_between_independent_runs"])
        self.assertFalse(result["explicit_unit_metadata_found"])
        self.assertFalse(result["explicit_source_scale_offset_tag_found"])
        self.assertTrue(result["gdal_scalar_values_are_possible_implicit_defaults"])
        self.assertFalse(result["raw_int16_to_physical_water_depth_calibration_authorized"])
        self.assertEqual(self.native["original_bkg_tiff_sha256"], BKG_TIFF_SHA)
        self.assertEqual(self.native["runtime_gdal_band_scale"], 1.0)
        self.assertEqual(self.native["runtime_gdal_band_offset"], 0.0)

    def test_integration_retains_original_geometry_and_both_evidence_runs(self):
        result = assess_both_receipts(copy.deepcopy(self.spatial), self.fresh())
        self.assertEqual(result["original_source_workflow_run_ids"],
                         [41350285830, 41353177132])
        self.assertEqual(len(result["original_exterior_support"]), 3)
        self.assertFalse(result["building_depth_calculation_authorized"])
        self.assertFalse(result["insured_loss_or_tiv_calculation_authorized"])
        self.assertFalse(result["cat_model_input_admitted"])
        native = result["native_tiff_unit_evidence"]
        self.assertFalse(native["raw_int16_to_physical_water_depth_calibration_authorized"])
        self.assertNotIn("water_depth_cm", result)
        self.assertNotIn("annual_insured_loss", result)

    def test_forged_unit_claim_cannot_override_missing_source_label(self):
        for field, value in (
            ("unit_metadata_present", True),
            ("recognized_unit_candidate_present", True),
            ("unit_source_fields_with_claims", ["rasterio_band_unit"]),
            ("explicit_scale_or_offset_tag_keys_present", True),
            ("source_units_and_scale_physically_calibrated", True),
            ("model_input_approved", True),
            ("gdal_scale_and_offset_may_be_implicit_defaults", False),
        ):
            with self.subTest(field=field):
                receipt = self.fresh()
                receipt[field] = value
                with self.assertRaisesRegex(EvidenceBlocked, "native BKG scalar"):
                    assess_native_unit_claims(receipt)

    def test_nondefault_gdal_scalars_and_nonfinite_values_block(self):
        for field, value in (
            ("runtime_gdal_band_scale", 0.01),
            ("runtime_gdal_band_scale", 1),
            ("runtime_gdal_band_scale", float("nan")),
            ("runtime_gdal_band_scale", float("inf")),
            ("runtime_gdal_band_offset", 1.0),
            ("runtime_gdal_band_offset", -1.0),
            ("original_int16_nodata", 0),
        ):
            with self.subTest(field=field, value=value):
                receipt = self.fresh()
                receipt[field] = value
                with self.assertRaises(EvidenceBlocked):
                    assess_native_unit_claims(receipt)

    def test_forged_source_hash_commit_or_run_id_blocks_even_if_spatial_valid(self):
        for field, value in (
            ("original_bkg_tiff_sha256", "0"*64),
            ("original_main_commit", "1"*40),
            ("original_github_actions_run_id", 1),
            ("original_github_actions_run_url", "https://example.org/forged"),
            ("original_bkg_tiff_bytes", 47280201),
            ("original_raster_crs", "EPSG:25833"),
        ):
            with self.subTest(field=field):
                receipt = self.fresh()
                receipt[field] = value
                with self.assertRaises(EvidenceBlocked):
                    assess_both_receipts(copy.deepcopy(self.spatial), receipt)

    def test_missing_or_wrong_raster_band_attributes_cannot_admit(self):
        for field in (
            "original_raster_dtype", "original_raster_dimensions_pixels",
            "unit_metadata_present", "raw_int16_values_not_imputed_as_m_or_cm",
        ):
            with self.subTest(field=field):
                receipt = self.fresh()
                del receipt[field]
                with self.assertRaises(EvidenceBlocked):
                    assess_native_unit_claims(receipt)

    def test_two_source_receipts_still_block_fake_depth_and_cat_claim(self):
        altered = copy.deepcopy(self.spatial)
        altered["original_numeric_raw_code_physical_depth_unit_verified"] = True
        with self.assertRaises(EvidenceBlocked):
            assess_both_receipts(altered, self.fresh())
        altered = copy.deepcopy(self.spatial)
        altered["insured_building_exposure_or_cat_loss_admitted"] = True
        with self.assertRaises(EvidenceBlocked):
            assess_both_receipts(altered, self.fresh())

    def test_toml_duplicate_units_cannot_be_silently_accepted(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("unit_metadata_present=false\nunit_metadata_present=true")


if __name__ == "__main__":
    unittest.main()
