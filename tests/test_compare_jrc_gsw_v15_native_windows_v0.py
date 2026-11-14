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
        for mask in (-1, 1.01, float("nan"), float("inf"), True, "1"):
            with self.subTest(mask=mask), self.assertRaises(jrc.JRCWindowComparisonBlocked):
                jrc.compare_native_occurrence_windows(b"\x01", [1], [mask])
        for value in (True, float("nan"), 1.5, 101, 255, "1"):
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


if __name__ == "__main__":
    unittest.main()
