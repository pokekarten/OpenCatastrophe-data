# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline cross-transport Occurrence/NoData/mask regression tests."""
import hashlib
import unittest
from scripts import compare_jrc_gsw_v15_native_windows_v0 as jrc


class JRCNativeWindowsComparisonTests(unittest.TestCase):
    def test_native_overlap_counts_and_fractional_mask_not_used_as_weight(self):
        raw = bytes([0, 1, 100, 255, 30])
        result = jrc.compare_native_occurrence_windows(
            raw, [0, 1.0, 100, None, 31], [1, 0.5, 1, 0, 1]
        )
        self.assertEqual(result["both_native_valid"], 4)
        self.assertEqual(result["equal_valid_occurrence_percent"], 3)
        self.assertEqual(result["different_valid_occurrence_percent"], 1)
        self.assertEqual(result["maximum_absolute_difference_on_valid_overlap"], 1)
        self.assertEqual(result["earth_engine_fractional_valid_mask"], 1)
        self.assertEqual(result["both_nodata"], 1)
        self.assertFalse(result["earth_engine_fractional_masks_used_as_weights"])
        self.assertFalse(result["supplied_window_positional_values_equal_if_overlap"])
        self.assertEqual(result["caller_supplied_decoded_geotiff_window_sha256"],hashlib.sha256(raw).hexdigest())
        for field in ("geospatial_grid_alignment_independently_verified", "original_geotiff_and_gee_source_identities_verified", "post_2026_11_10_correction_verified", "original_source_requests_executed", "model_input_approved"):
            self.assertFalse(result[field])

    def test_masked_earth_engine_zero_is_not_geotiff_valid_zero(self):
        result = jrc.compare_native_occurrence_windows(
            bytes([0, 255, 100]), [0, 0, 100], [0, 0, 0.25]
        )
        self.assertEqual(result["geotiff_valid_earth_engine_masked"], 1)
        self.assertEqual(result["both_nodata"], 1)
        self.assertEqual(result["both_native_valid"], 1)
        self.assertEqual(result["earth_engine_masked_numeric_placeholder"], 2)
        self.assertEqual(result["earth_engine_fractional_valid_mask"], 1)
        self.assertTrue(result["supplied_window_positional_values_equal_if_overlap"])
        self.assertFalse(result["model_input_approved"])

    def test_no_jointly_valid_pixels_do_not_prove_parity(self):
        rec = jrc.compare_native_occurrence_windows(bytes([0, 255]), [None, None], [0, 0])
        self.assertEqual(rec["both_native_valid"], 0)
        self.assertIsNone(rec["maximum_absolute_difference_on_valid_overlap"])
        self.assertIsNone(rec["supplied_window_positional_values_equal_if_overlap"])

    def test_disjoint_validity_counts_without_false_pixel_mismatch(self):
        rec = jrc.compare_native_occurrence_windows(bytes([255, 50]), [30, None], [1, 0])
        self.assertEqual(rec["earth_engine_valid_geotiff_nodata"], 1)
        self.assertEqual(rec["geotiff_valid_earth_engine_masked"], 1)
        self.assertEqual(rec["different_valid_occurrence_percent"], 0)
        self.assertIsNone(rec["supplied_window_positional_values_equal_if_overlap"])

    def test_untrusted_masks_and_values_fail_closed(self):
        for mask in (-1, 1.01, 10**1000, float("nan"), float("inf"), True, "1"):
            with self.subTest(mask=mask), self.assertRaises(jrc.JRCWindowComparisonBlocked):
                jrc.compare_native_occurrence_windows(b"\x01", [1], [mask])
        for value in (True, 10**1000, float("nan"), 1.5, 101, 255, "1"):
            with self.subTest(value=value), self.assertRaises(jrc.JRCWindowComparisonBlocked):
                jrc.compare_native_occurrence_windows(b"\x01", [value], [1])
        with self.assertRaises(jrc.JRCWindowComparisonBlocked):
            jrc.compare_native_occurrence_windows(b"\x00", [None], [1])

    def test_tiff_invalid_percent_or_ill_formed_arrays_fail_closed(self):
        for source in (None, b"", b"\x01" * 65537, bytes([101]), bytes([254])):
            with self.subTest(source=str(type(source))), self.assertRaises(jrc.JRCWindowComparisonBlocked):
                jrc.compare_native_occurrence_windows(source, [0], [1])
        for ee, mask in (([0,0], [1]), ([0], [1,1]), (b"\x00", [1]), ([0], b"\x01")):
            with self.subTest(ee=ee, mask=mask), self.assertRaises(jrc.JRCWindowComparisonBlocked):
                jrc.compare_native_occurrence_windows(b"\x00", ee, mask)

    def test_window_stats_exclude_source_values_and_no_network_dependencies(self):
        rec = jrc.compare_native_occurrence_windows(bytes([0,100]), [0, 99], [1, 1])
        self.assertEqual(rec["different_valid_occurrence_percent"], 1)
        self.assertNotIn("original_pixel_array", rec)
        self.assertNotIn("source_original_sha256", rec)
        self.assertTrue(all(not isinstance(val,(bytes,list)) for val in rec.values()))
        code=jrc.__file__
        with open(code,encoding="utf-8") as file:
            source=file.read()
        for banned in ("requests.", "urllib.", "ee.Initialize", "boto3", "open_url", "urlopen"):
            self.assertNotIn(banned,source)


    @staticmethod
    def native_grids():
        # Synthetic same-world 2x2 window from a 10-degree tile and a
        # separate global raster, without claiming source provenance.
        tiff = {
            "crs": "EPSG:4326",
            "transform": [0.00025, 0, 10, 0, -0.00025, 50],
            "raster_width": 40000, "raster_height": 40000,
            "left": 4, "top": 8, "width": 2, "height": 2,
        }
        gee = {
            "crs": "EPSG:4326",
            "transform": [0.00025, 0, -180, 0, -0.00025, 80],
            "raster_width": 1440000, "raster_height": 560000,
            "left": 760004, "top": 120008, "width": 2, "height": 2,
        }
        return tiff, gee

    def test_same_physical_window_different_parent_raster_origins(self):
        tiff, gee = self.native_grids()
        rec = jrc.inspect_supplied_native_window_grid_pair(tiff, gee)
        self.assertTrue(rec["caller_supplied_grid_metadata_compatible"])
        self.assertEqual(rec["caller_supplied_window_pixel_count"], 4)
        self.assertEqual(rec["native_grid_crs_expected"], "EPSG:4326")
        self.assertFalse(rec["grid_metadata_provider_authenticated"])
        self.assertFalse(rec["geospatial_grid_alignment_independently_verified"])
        result = jrc.compare_native_occurrence_windows_with_grid(
            bytes([0, 10, 100, 255]), [0, 10, 100, None], [1, 1, 0.5, 0],
            tiff, gee,
        )
        self.assertEqual(result["equal_valid_occurrence_percent"], 3)
        self.assertEqual(result["both_nodata"], 1)
        self.assertTrue(result["caller_supplied_grid_metadata_compatible"])
        self.assertFalse(result["native_unresampled_source_data_independently_verified"])
        self.assertFalse(result["model_input_approved"])

    def test_half_pixel_and_full_pixel_shift_refused(self):
        tiff, gee = self.native_grids()
        for perturbation in (0.000125, 0.00025, -0.000125):
            shifted = dict(gee)
            shifted["transform"] = list(gee["transform"])
            shifted["transform"][2] += perturbation
            with self.subTest(dx=perturbation), self.assertRaisesRegex(
                jrc.JRCWindowComparisonBlocked, "affine locations differ"
            ):
                jrc.inspect_supplied_native_window_grid_pair(tiff, shifted)
        moved = dict(gee)
        moved["left"] += 1
        with self.assertRaisesRegex(jrc.JRCWindowComparisonBlocked, "affine locations differ"):
            jrc.inspect_supplied_native_window_grid_pair(tiff, moved)

    def test_different_native_resolution_and_sheared_grid_refused(self):
        tiff, gee = self.native_grids()
        for index, value in ((0, 0.0005), (4, -0.0005), (1, 0.1), (3, 1e-8)):
            changed = dict(gee)
            changed["transform"] = list(gee["transform"])
            changed["transform"][index] = value
            with self.subTest(index=index), self.assertRaisesRegex(
                jrc.JRCWindowComparisonBlocked, "resolution, rotation or shear"
            ):
                jrc.inspect_supplied_native_window_grid_pair(tiff, changed)

    def test_crs_wrong_shapes_outside_source_bounds_refused(self):
        tiff, gee = self.native_grids()
        cases = (
            ("crs", "EPSG:3857"),
            ("width", 3),
            ("height", 0),
            ("left", 1440000),
            ("top", -1),
            ("raster_width", 10),
            ("raster_height", 100),
        )
        for key, value in cases:
            changed = dict(gee)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(
                jrc.JRCWindowComparisonBlocked
            ):
                jrc.inspect_supplied_native_window_grid_pair(tiff, changed)

    def test_reject_nonfinite_extreme_and_bool_affine_inputs(self):
        tiff, gee = self.native_grids()
        for invalid in (float("nan"), float("inf"), True, 10**1000, "0.00025"):
            modified = dict(tiff)
            modified["transform"] = list(tiff["transform"])
            modified["transform"][0] = invalid
            with self.subTest(invalid=str(invalid)[:20]), self.assertRaises(
                jrc.JRCWindowComparisonBlocked
            ):
                jrc.inspect_supplied_native_window_grid_pair(modified, gee)
        modified = dict(gee)
        modified["top"] = True
        with self.assertRaises(jrc.JRCWindowComparisonBlocked):
            jrc.inspect_supplied_native_window_grid_pair(tiff, modified)

    def test_window_pixel_count_must_equal_decoded_values(self):
        tiff, gee = self.native_grids()
        for raw in (None, [0, 0, 0, 0], b""):
            with self.subTest(input_type=str(type(raw))), self.assertRaises(
                jrc.JRCWindowComparisonBlocked
            ):
                jrc.compare_native_occurrence_windows_with_grid(
                    raw, [0, 0, 0, 0], [1, 1, 1, 1], tiff, gee
                )
        with self.assertRaisesRegex(
            jrc.JRCWindowComparisonBlocked, "do not fit supplied window"
        ):
            jrc.compare_native_occurrence_windows_with_grid(
                bytes([0, 100]), [0, 100], [1, 1], tiff, gee
            )
        # Native comparator must never grant source proof even if numeric
        # values happen to match at every provided position.
        rec = jrc.compare_native_occurrence_windows_with_grid(
            bytes([0, 0, 0, 0]), [0, 0, 0, 0], [1, 1, 1, 1],
            tiff, gee,
        )
        self.assertTrue(rec["supplied_window_positional_values_equal_if_overlap"])
        self.assertFalse(rec["geospatial_grid_alignment_independently_verified"])
        self.assertFalse(rec["original_geotiff_and_gee_source_identities_verified"])
        self.assertFalse(rec["model_input_approved"])


if __name__ == "__main__":
    unittest.main()
