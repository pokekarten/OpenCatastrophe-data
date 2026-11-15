# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only invented building polygons and synthetic raster classes; no network."""
from __future__ import annotations

import unittest
import zlib

from scripts.worldcover_synthetic_grid_shift_sensitivity_v0 import (
    OFFSETS, SensitivityBlocked, synthetic_grid_shift_sensitivity,
)
from scripts.worldcover_synthetic_polygon_overlap_v0 import SIDE
from scripts.probe_esa_worldcover_classified_block185_v0 import decode_original_block


class SyntheticGridSensitivityTests(unittest.TestCase):
    def test_fixed_bounded_scenarios_and_no_coordinates_exported(self):
        self.assertEqual(len(OFFSETS), 17)
        self.assertEqual(OFFSETS[0], (0.0, 0.0))
        self.assertEqual(len(set(OFFSETS)), 17)
        self.assertEqual(max(abs(dx) for dx, dy in OFFSETS), 1.0)
        self.assertEqual(max(abs(dy) for dx, dy in OFFSETS), 1.0)
        record = synthetic_grid_shift_sensitivity(bytes([10]) * (SIDE * SIDE))
        self.assertEqual(record["fixed_scenario_count"], 17)
        self.assertEqual(record["maximum_total_variation_from_baseline"], 0)
        self.assertEqual(record["shifted_class_fraction_ranges"], {
            "10": {"minimum_fraction": 1.0, "maximum_fraction": 1.0}
        })
        self.assertFalse(record["real_building_geometry_used"])
        self.assertFalse(record["actual_transform_accuracy_in_metres_inferred"])
        self.assertFalse(record["actual_building_worldcover_overlap_verified"])
        self.assertFalse(record["model_input_approved"])
        self.assertNotIn("coordinates", str(record))

    def test_synthetic_class_boundary_proves_centroid_and_polygon_shift_instability(self):
        # Real original provider pixels are NOT used here. A made-up vertical
        # split at column 880 runs through the invented polygon's center.
        raw = bytearray([10]) * (SIDE * SIDE)
        for row in range(875, 887):
            for col in range(880, 888):
                raw[row * SIDE + col] = 50
        record = synthetic_grid_shift_sensitivity(bytes(raw))
        base = record["baseline_area_weighted_class_fractions"]
        self.assertAlmostEqual(base["10"], 0.5, places=5)
        self.assertAlmostEqual(base["50"], 0.5, places=5)
        self.assertGreater(record["maximum_total_variation_from_baseline"], 0.2)
        self.assertTrue(record["any_shift_changes_majority_class"])
        for class_record in record["shifted_class_fraction_ranges"].values():
            self.assertLess(class_record["minimum_fraction"],
                            class_record["maximum_fraction"])
        self.assertFalse(record["provider_wfs_count_discrepancy_resolved"])
        self.assertFalse(record["model_input_approved"])

    def test_synthetic_decoder_reuses_real_production_pixel_path_without_extra_get(self):
        pixels = bytes([30]) * (SIDE * SIDE)
        payload = zlib.compress(pixels)
        result = decode_original_block(
            payload, predictor=1, expected_compressed_bytes=len(payload),
            synthetic_shift_sensitivity=True,
        )
        self.assertEqual(result["decompressed_uint8_pixel_count"], SIDE * SIDE)
        self.assertEqual(result["class_code_counts"], {"30": SIDE * SIDE})
        sensitivity = result["synthetic_grid_shift_sensitivity"]
        self.assertEqual(sensitivity["baseline_area_weighted_class_fractions"],
                         {"30": 1.0})
        self.assertEqual(sensitivity["maximum_total_variation_from_baseline"], 0)
        self.assertFalse(sensitivity["real_building_geometry_used"])

    def test_wrong_size_class_or_byte_type_rejects(self):
        with self.assertRaises(SensitivityBlocked):
            synthetic_grid_shift_sensitivity(b"not-a-tiff")
        with self.assertRaises(SensitivityBlocked):
            synthetic_grid_shift_sensitivity(bytearray([10]) * (SIDE * SIDE))
        invalid = bytearray([10]) * (SIDE * SIDE)
        invalid[880 * SIDE + 880] = 255
        with self.assertRaises(SensitivityBlocked):
            synthetic_grid_shift_sensitivity(bytes(invalid))

    def test_all_shift_labels_remain_pixels_not_metres(self):
        result = synthetic_grid_shift_sensitivity(bytes([50]) * (SIDE * SIDE))
        self.assertEqual(result["shift_units"],
                         "worldcover_source_grid_pixels_not_metres")
        self.assertEqual(result["perturbation_steps_pixels"], [0.25, 1.0])
        self.assertEqual(result["baseline_majority_class_if_unique"], 50)
        self.assertFalse(result["any_shift_changes_majority_class"])
        self.assertFalse(result["source_building_survey_vintage_verified"])
        self.assertFalse(result["original_source_pixel_values_exported"])


if __name__ == "__main__":
    unittest.main()
