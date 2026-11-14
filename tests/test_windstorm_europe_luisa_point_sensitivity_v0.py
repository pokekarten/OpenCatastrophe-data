# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from unittest.mock import patch

from research_runners import windstorm_europe_luisa_point_sensitivity_v0 as model


class LuisaPointSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.headers = ["wind speed", "outbuilding", "strong brick structure"]
        self.rows = [
            {"wind speed": 0.0, "outbuilding": 0.0, "strong brick structure": 0.0},
            {"wind speed": 40.0, "outbuilding": 0.8, "strong brick structure": 0.0},
            {"wind speed": 80.0, "outbuilding": 72.0, "strong brick structure": 10.8},
        ]

    def test_named_curve_interpolates_damage_percent(self):
        self.assertAlmostEqual(model.interpolate_percent(20.0, "outbuilding", self.headers, self.rows), 0.4)
        self.assertAlmostEqual(model.interpolate_percent(60.0, "strong brick structure", self.headers, self.rows), 5.4)

    def test_named_curve_blocks_implicit_alias_and_extrapolation(self):
        with self.assertRaisesRegex(ValueError, "exact source column name"):
            model.interpolate_percent(20.0, "strong outbuilding", self.headers, self.rows)
        with self.assertRaisesRegex(ValueError, "extrapolation is blocked"):
            model.interpolate_percent(81.0, "outbuilding", self.headers, self.rows)

    def test_one_pixel_loss_is_bounded_by_its_structural_maximum(self):
        maximum = 180.0 * 2500
        ratio = model.interpolate_percent(40.0, "outbuilding", self.headers, self.rows) / 100
        loss = maximum * ratio
        self.assertEqual(loss, 3600.0)
        self.assertGreaterEqual(loss, 0)
        self.assertLessEqual(loss, maximum)

    def test_run_evaluates_each_named_curve_without_mixture(self):
        sites = [{"site_id": "sample-a", "longitude": 1.0, "latitude": 2.0}]
        with patch.object(model, "sha256_file", return_value=model.HAZARD_SHA256), \
             patch("pathlib.Path.read_bytes", return_value=b"hazard"), \
             patch.object(model, "read_luisa_values", return_value={1111: {
                 "description": "fixture class", "structural_2010_eur_per_m2": 180.0,
                 "content_2010_eur_per_m2": 25.0}}), \
             patch.object(model, "read_named_curves", return_value=(self.headers, self.rows)), \
             patch.object(model, "read_landuse_points", return_value=[{
                 "row": 1, "column": 1, "landuse_code": 1111, "pixel_area_m2": 2500}]), \
             patch.object(model, "export", return_value={"features": [], "metadata": {}}), \
             patch.object(model, "join_points", return_value=[{"status": "matched", "gust_mps": 40.0}]):
            result = model.run("raster", "workbook", "curves", "hazard", sites)
        point = result["points"][0]
        self.assertFalse(result["vulnerability_mixture_admitted"])
        self.assertFalse(result["building_or_insured_loss"])
        self.assertEqual(point["single_curve_sensitivity"]["outbuilding"]["structural_loss_2010_eur"], 3600.0)
        self.assertNotIn("strong outbuilding", point["single_curve_sensitivity"])
        self.assertEqual(result["sum_of_sampled_pixels_structural_loss_2010_eur_by_single_curve"]["outbuilding"], 3600.0)

    def test_run_rejects_duplicate_pixel_identity_from_source_lookup(self):
        sites = [
            {"site_id": "sample-a", "longitude": 1.0, "latitude": 2.0},
            {"site_id": "sample-b", "longitude": 1.1, "latitude": 2.1},
        ]
        with patch.object(model, "sha256_file", return_value=model.HAZARD_SHA256), \
             patch.object(model, "read_luisa_values", return_value={1111: {
                 "description": "fixture class", "structural_2010_eur_per_m2": 180.0,
                 "content_2010_eur_per_m2": 25.0}}), \
             patch.object(model, "read_named_curves", return_value=(self.headers, self.rows)), \
             patch.object(model, "read_landuse_points", return_value=[
                 {"row": 1, "column": 1, "landuse_code": 1111, "pixel_area_m2": 2500},
                 {"row": 1, "column": 1, "landuse_code": 1111, "pixel_area_m2": 2500}]), \
             patch.object(model, "export", return_value={"features": [], "metadata": {}}), \
             patch.object(model, "join_points", return_value=[]):
            with self.assertRaisesRegex(ValueError, "duplicate point pixels"):
                model.run("raster", "workbook", "curves", "hazard", sites)


if __name__ == "__main__":
    unittest.main()
