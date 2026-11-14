# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests of official *caption* meaning, never source features."""

from __future__ import annotations

import unittest

from scripts.ea_flood_published_depth_bands_v0 import (
    CAPTION_BOUNDS_MM, MISSING_CAPTION, DepthCaptionBlocked, inspect_published_caption,
)


class PublishedCaptionTests(unittest.TestCase):
    def test_official_seven_depth_captions(self):
        self.assertEqual(len(CAPTION_BOUNDS_MM), 7)
        for caption, (lower, upper) in CAPTION_BOUNDS_MM.items():
            with self.subTest(caption=caption):
                result = inspect_published_caption(caption)
                self.assertEqual(result["status"], "published_depth_interval_caption")
                self.assertEqual(result["nominal_lower_boundary_mm"], lower)
                self.assertEqual(result["nominal_upper_boundary_mm"], upper)
                self.assertIsNone(result["building_depth_mm"])
                self.assertIsNone(result["estimated_damage_ratio"])
                self.assertIsNone(result["representative_depth_mm"])
                self.assertFalse(result["model_data_admitted"])
                self.assertFalse(result["observed_actual_feature_label_verified"])
                self.assertFalse(result["safe_for_direct_feature_value_join"])

    def test_first_band_does_not_infer_zero_depth(self):
        out = inspect_published_caption("Up to 150mm")
        self.assertIsNone(out["nominal_lower_boundary_mm"])
        self.assertEqual(out["nominal_upper_boundary_mm"], 150)

    def test_last_band_has_no_fabricated_ceiling(self):
        out = inspect_published_caption("Over 2300mm")
        self.assertEqual(out["nominal_lower_boundary_mm"], 2300)
        self.assertIsNone(out["nominal_upper_boundary_mm"])

    def test_unavailable_is_missing_never_zero(self):
        out = inspect_published_caption(MISSING_CAPTION)
        self.assertEqual(out["status"], "published_unavailable_marker")
        self.assertTrue(out["unavailable_means_missing_not_zero"])
        self.assertIsNone(out["nominal_lower_boundary_mm"])
        self.assertIsNone(out["nominal_upper_boundary_mm"])

    def test_interval_edges_not_assumed_inclusive(self):
        for caption in CAPTION_BOUNDS_MM:
            self.assertFalse(inspect_published_caption(caption)["boundary_inclusivity_verified"])

    def test_unknown_actual_feature_label_rejected(self):
        for caption in ("0-150", "0 - 0.15", "0.15m", "150 - 300mm", "150–300mm", "150 - 300 mm", "No data", "None", "0", "150", ""):
            with self.subTest(caption=caption), self.assertRaises(DepthCaptionBlocked):
                inspect_published_caption(caption)

    def test_non_string_types_rejected(self):
        for value in (0, 150, 0.15, None, False, [], {}):
            with self.subTest(value=value), self.assertRaises(DepthCaptionBlocked):
                inspect_published_caption(value)

    def test_no_commercial_or_model_admission(self):
        for caption in (*CAPTION_BOUNDS_MM, MISSING_CAPTION):
            out = inspect_published_caption(caption)
            self.assertFalse(out["source_asset_rights_reviewed"])
            self.assertFalse(out["model_data_admitted"])
            self.assertFalse(out["safe_for_direct_feature_value_join"])
            self.assertIsNone(out["estimated_damage_ratio"])


if __name__ == "__main__":
    unittest.main()
