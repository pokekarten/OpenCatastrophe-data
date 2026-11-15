# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GHS-AGE coarse original-byte *readiness* checks."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from research_runners.ghsl_age_r2025a_coarse_pixel_window_preflight_v0 import (
    GHSAGEBlocked, PRODUCT, TIFF_MEMBER, inspect_window, main,
)


def fake_metadata(**overrides):
    value = {
        "product_id": PRODUCT,
        "raster_member": TIFF_MEMBER,
        "crs_identifier": "ESRI:54009",
        "data_type": "UInt8", "band_count": 1,
        "window_width": 4, "window_height": 2,
        "pixel_width_m": 1000, "pixel_height_m": -1000,
        "rotation_x": 0, "rotation_y": 0,
        "declared_nodata": 255,
    }
    value.update(overrides)
    return value


def digest(value):
    return hashlib.sha256(value).hexdigest()


class GHSLAGEWindowTest(unittest.TestCase):
    def setUp(self):
        self.pixels = bytes((0, 1, 2, 3, 4, 5, 255, 0))

    def test_source_exact_synthetic_uint8_window_and_semantics(self):
        result = inspect_window(self.pixels, fake_metadata(), digest(self.pixels))
        self.assertEqual(result["class_counts"], {
            "0": 2, "1": 1, "2": 1, "3": 1, "4": 1, "5": 1})
        self.assertEqual(result["not_built_up_cells_class_zero"], 2)
        self.assertEqual(result["built_stock_age_class_cells_1_to_5"], 5)
        self.assertEqual(result["declared_nodata_cells"], 1)
        self.assertEqual(result["window_cell_count"], 8)
        self.assertTrue(result["window_sha256_matches_caller_provided_digest"])
        self.assertTrue(result["declared_nodata_from_external_metadata_not_independently_verified"])
        for key in (
            "raster_pixels_proven_original_jrc",
            "original_zip_sha256_independently_verified",
            "original_tiff_sha256_independently_verified",
            "raster_georeferencing_independently_verified",
            "full_global_raster_coverage_verified",
            "individual_building_construction_year_verified",
            "window_is_statistically_representative", "CAT_model_input_approved",
            "source_cells_coordinates_or_policy_values_exported",
        ):
            self.assertFalse(result[key])
        self.assertNotIn("coordinates", json.dumps(result["class_counts"]))

    def test_code_zero_remains_nonbuilt_not_nodata(self):
        pixels = bytes((0,)) * 8
        result = inspect_window(pixels, fake_metadata(declared_nodata=None), digest(pixels))
        self.assertEqual(result["not_built_up_cells_class_zero"], 8)
        self.assertEqual(result["declared_nodata_cells"], 0)
        self.assertEqual(result["built_stock_age_class_cells_1_to_5"], 0)

    def test_rejects_fine_resolution_codes_and_unreviewed_missing_code(self):
        for value in (6, 10, 254, 255):
            pixels = bytes((0, 1, 2, 3, 4, 5, value, 0))
            kwargs = {"declared_nodata": None} if value == 255 else {}
            with self.subTest(value=value), self.assertRaises(GHSAGEBlocked):
                inspect_window(pixels, fake_metadata(**kwargs), digest(pixels))

    def test_wrong_vintage_resolution_projection_and_band_fail(self):
        changes = (
            {"product_id": "GHS_AGE_1975052020_GLOBE_R2025A_54009_1000_V1_0"},
            {"product_id": PRODUCT.replace("_R2025A_", "_R2023A_")},
            {"raster_member": TIFF_MEMBER.replace("_1000_", "_100_")},
            {"crs_identifier": "EPSG:4326"},
            {"data_type": "UInt16"}, {"band_count": True}, {"band_count": 3},
            {"pixel_width_m": 100}, {"pixel_height_m": 1000},
            {"rotation_x": 1}, {"rotation_y": -0.5},
        )
        for mutate in changes:
            with self.subTest(mutate=mutate), self.assertRaises(GHSAGEBlocked):
                inspect_window(self.pixels, fake_metadata(**mutate), digest(self.pixels))

    def test_duplicate_or_fractional_window_shape_and_checksum_fail(self):
        for mutate in (
            {"window_width": 32}, {"window_height": 33},
            {"window_width": 4.0}, {"window_width": True},
            {"window_width": 0}, {"window_height": -1},
        ):
            with self.subTest(mutate=mutate), self.assertRaises(GHSAGEBlocked):
                inspect_window(self.pixels, fake_metadata(**mutate), digest(self.pixels))
        for bad in ("0" * 64, "G" * 64, "", None):
            with self.subTest(hash=bad), self.assertRaises(GHSAGEBlocked):
                inspect_window(self.pixels, fake_metadata(), bad)

    def test_nodata_must_not_be_a_real_class_or_unverified_sentinel(self):
        for bad in (0, 1, 5, 6, 254, "255", True):
            with self.subTest(bad=bad), self.assertRaises(GHSAGEBlocked):
                inspect_window(self.pixels, fake_metadata(declared_nodata=bad),
                               digest(self.pixels))

    def test_unknown_metadata_fields_or_wrong_data_type_rejected(self):
        data = fake_metadata()
        data["original_verified"] = True
        with self.assertRaises(GHSAGEBlocked):
            inspect_window(self.pixels, data, digest(self.pixels))
        with self.assertRaises(GHSAGEBlocked):
            inspect_window(self.pixels, [], digest(self.pixels))
        with self.assertRaises(GHSAGEBlocked):
            inspect_window([0, 1], fake_metadata(), digest(self.pixels))

    def test_cli_never_discloses_local_paths_or_pixel_values_on_errors(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "private-source-window.bin"
            m = Path(td) / "private-metadata.json"
            p.write_bytes(self.pixels)
            m.write_text(json.dumps(fake_metadata()), encoding="utf-8")
            ok, err = io.StringIO(), io.StringIO()
            with redirect_stdout(ok), redirect_stderr(err):
                status = main(["--window-bytes", str(p), "--metadata-json", str(m),
                               "--window-sha256", digest(self.pixels)])
            self.assertEqual(status, 0)
            self.assertFalse(json.loads(ok.getvalue())["CAT_model_input_approved"])
            m.write_text('{"product_id":"bad","product_id":"also bad"}', encoding="utf-8")
            ok, err = io.StringIO(), io.StringIO()
            with redirect_stdout(ok), redirect_stderr(err):
                status = main(["--window-bytes", str(p), "--metadata-json", str(m),
                               "--window-sha256", digest(self.pixels)])
            self.assertEqual(status, 2)
            self.assertEqual(ok.getvalue(), "")
            self.assertNotIn(str(p), err.getvalue())
            self.assertNotIn(str(m), err.getvalue())


if __name__ == "__main__":
    unittest.main()
