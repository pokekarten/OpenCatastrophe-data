# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic scalar TIFF metadata only: no source network or source pixels."""
import math
import unittest

from research_runners.probe_bkg_original_depth_unit_claims_v0 import (
    SourceBandSemanticsBlocked, inspect_unit_claims,
)


def claim(*, global_tags=None, band_tags=None, scale=1.0, offset=0.0,
          unit=None, description=None):
    return inspect_unit_claims(
        global_tags={} if global_tags is None else global_tags,
        band_tags={} if band_tags is None else band_tags,
        gdal_scale=scale, gdal_offset=offset,
        gdal_unit=unit, band_description=description,
    )


class OriginalBkgUnitClaimsTests(unittest.TestCase):
    def test_gdal_default_scalars_are_not_depth_units(self):
        out = claim()
        self.assertIsNone(out["declared_or_runtime_recognized_unit_candidate"])
        self.assertEqual(out["runtime_gdal_band_scale"], 1.0)
        self.assertFalse(out["unit_metadata_present"])
        self.assertTrue(out["gdal_scale_and_offset_may_be_implicit_defaults"])
        self.assertFalse(out["source_units_and_scale_physically_calibrated"])
        self.assertFalse(out["model_input_approved"])

    def test_known_band_unit_is_only_candidate_without_calibration(self):
        for name, expected in (("m", "metres"), ("meters", "metres"),
                               ("centimetre", "centimetres"), ("mm", "millimetres")):
            with self.subTest(name=name):
                out = claim(band_tags={"UNITTYPE": name}, scale=0.01)
                self.assertEqual(out["declared_or_runtime_recognized_unit_candidate"], expected)
                self.assertFalse(out["source_units_and_scale_physically_calibrated"])
                self.assertTrue(out["raw_int16_values_not_imputed_as_m_or_cm"])

    def test_recognized_metre_in_two_carriers_is_not_conflict(self):
        out = claim(global_tags={"UNITTYPE": "m"}, unit="metres",
                    band_tags={"description": "one public TIFF band"})
        self.assertEqual(out["declared_or_runtime_recognized_unit_candidate"], "metres")
        self.assertEqual(out["unit_source_fields_with_claims"],
                         ["dataset_unit_tag", "rasterio_band_unit"])

    def test_conflicting_candidate_units_fail_closed(self):
        with self.assertRaisesRegex(SourceBandSemanticsBlocked, "conflicting"):
            claim(global_tags={"UNITTYPE": "m"}, band_tags={"UNITTYPE": "cm"})
        with self.assertRaisesRegex(SourceBandSemanticsBlocked, "multiple"):
            claim(band_tags={"UNITTYPE": "m", "UNITS": "m"})

    def test_unknown_units_not_upgraded_to_physical_depth(self):
        out = claim(unit="furlongs", global_tags={"SCALE": "3.0"})
        self.assertIsNone(out["declared_or_runtime_recognized_unit_candidate"])
        self.assertTrue(out["unit_metadata_unrecognized_or_ambiguous"])
        self.assertTrue(out["explicit_scale_or_offset_tag_keys_present"])
        self.assertFalse(out["model_input_approved"])

    def test_nonfinite_or_invalid_scale_fails_closed(self):
        for value in (math.nan, math.inf, -math.inf, True, "0.01", None):
            with self.subTest(value=str(value)), self.assertRaises(SourceBandSemanticsBlocked):
                claim(scale=value)
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(offset=float("nan"))

    def test_overlong_or_wrong_metadata_rejected(self):
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(global_tags={str(i): "x" for i in range(130)})
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(unit="m" * 65)
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(description="x" * 257)
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(global_tags={"long" * 35: "x"})
        with self.assertRaises(SourceBandSemanticsBlocked):
            claim(band_tags=[("UNITTYPE", "m")])


if __name__ == "__main__":
    unittest.main()
