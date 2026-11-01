# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only adversarial tests of the original two-source QA receipt."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from research_runners.validate_berlin_bkg_exterior_original_receipt_v0 import (
    SOURCE_SHA, ExteriorReceiptBlocked, main, validate,
)


def fixture():
    def band(distance, total, positive, zero, nodata, outside=0):
        return {
            "distance_from_source_building_union_m": distance,
            "unique_exterior_ring_area_m2": total,
            "positive_raw_integer_supported_area_m2": positive,
            "valid_numeric_zero_supported_area_m2": zero,
            "original_masked_nodata_area_m2": nodata,
            "outside_sample_window_area_m2": outside,
            "valid_numeric_support_fraction": round((positive + zero) / total, 6),
        }
    return {
        "profile": "berlin-bld4-bkg-real-kostra-raw-cell-support-v0",
        "source_bkg_original_tiff_sha256": SOURCE_SHA,
        "source_bkg_original_size_bytes": 47280200,
        "source_bld4_wfs_response_sha256": "a" * 64,
        "pilot_window_cells_examined": 47089,
        "pilot_clipped_buildings_checked": 5,
        "source_bld4_buildings_mutable_date_not_historic": True,
        "source_hazard_bkg_kostra_design_scenario": True,
        "original_bkg_bounded_real_pixel_window_used": True,
        "building_coverage_from_real_bkg_raw_codes_not_depth": True,
        "exact_polygon_cell_area_conservation_verified": True,
        "source_products_temporal_alignment_proven": False,
        "real_water_depth_units_verified": False,
        "cat_model_admitted": False,
        "any_property_ids_or_coordinates_written": False,
        "actual_insurance_exposure_or_loss_estimated": False,
        "individual_building_or_cell_values_exported": False,
        "clipped_building_area_in_raster_crs_m2": 100,
        "positive_raw_code_supported_area_m2": 5,
        "valid_zero_raw_code_supported_area_m2": 15,
        "original_nodata_supported_area_m2": 80,
        "outside_sample_window_area_m2": 0,
        "exterior_raw_code_support_research": {
            "original_buildings_count": 5,
            "exterior_rings_m": [[0, 1], [1, 3], [3, 5]],
            "raw_int16_values_not_physical_water_depths": True,
            "positive_raw_code_not_confirmed_as_centimetres_or_metres": True,
            "building_raster_nodata_never_interpreted_as_dry": True,
            "building_access_or_entrance_levels_not_verified": True,
            "exterior_rings_not_building_loss_depth": True,
            "original_per_building_ids_coords_or_pixel_values_exported": False,
            "cat_model_or_insurer_exposure_admitted": False,
            "bands": [
                band([0, 1], 20, 8, 6, 6),
                band([1, 3], 40, 20, 10, 10),
                band([3, 5], 60, 10, 10, 20, 20),
            ],
        },
    }


class OriginalExteriorReceiptGateTests(unittest.TestCase):
    def test_accepts_conserved_source_specific_aggregate_only(self):
        r = validate(fixture())
        self.assertEqual(len(r["exterior_bands"]), 3)
        self.assertEqual(r["exterior_bands"][0]["valid_numeric_fraction"], 0.7)
        self.assertEqual(r["exterior_bands"][2]["outside_window_m2"], 20)
        self.assertFalse(r["cat_model_input_approved"])
        self.assertFalse(r["independently_validated_physical_depth_units"])
        self.assertNotIn("polygons", str(r))
        self.assertNotIn("insurance_policy", str(r))

    def test_bad_original_tiff_identity_or_wfs_sha_blocks(self):
        for key, bad in (
            ("source_bkg_original_tiff_sha256", "b" * 64),
            ("source_bkg_original_size_bytes", 47280201),
            ("source_bld4_wfs_response_sha256", "not-sha"),
            ("pilot_window_cells_examined", 47088),
            ("pilot_clipped_buildings_checked", 4),
        ):
            r = fixture()
            r[key] = bad
            with self.subTest(key=key), self.assertRaises(ExteriorReceiptBlocked):
                validate(r)

    def test_never_promotes_scientific_admission_or_source_vintage(self):
        for key in (
            "real_water_depth_units_verified", "cat_model_admitted",
            "source_products_temporal_alignment_proven",
            "any_property_ids_or_coordinates_written",
            "actual_insurance_exposure_or_loss_estimated",
        ):
            r = fixture()
            r[key] = True
            with self.subTest(key=key), self.assertRaises(ExteriorReceiptBlocked):
                validate(r)

    def test_footprint_cannot_relabel_nodata_as_zero(self):
        r = fixture()
        r["original_nodata_supported_area_m2"] = 60
        r["valid_zero_raw_code_supported_area_m2"] = 35
        # Area still conserves, but this transformation cannot be proven from
        # aggregate metadata alone: gate only checks internal consistency.
        self.assertEqual(validate(r)["footprint_area_m2"], 100)
        r["original_nodata_supported_area_m2"] = 80
        with self.assertRaisesRegex(ExteriorReceiptBlocked, "footprint"):
            validate(r)

    def test_bad_band_order_conservation_and_zero_not_lost(self):
        r = fixture()
        bands = r["exterior_raw_code_support_research"]["bands"]
        bands[0], bands[1] = bands[1], bands[0]
        with self.assertRaisesRegex(ExteriorReceiptBlocked, "out-of-order"):
            validate(r)
        r = fixture()
        bands = r["exterior_raw_code_support_research"]["bands"]
        bands[0]["original_masked_nodata_area_m2"] = 0
        with self.assertRaisesRegex(ExteriorReceiptBlocked, "conserve"):
            validate(r)
        r = fixture()
        bands = r["exterior_raw_code_support_research"]["bands"]
        bands[0]["valid_numeric_support_fraction"] = 1
        with self.assertRaisesRegex(ExteriorReceiptBlocked, "fraction"):
            validate(r)

    def test_nonfinite_negative_and_boolean_numeric_block(self):
        for value in (float("nan"), float("inf"), -1, True, None, "5"):
            r = fixture()
            r["exterior_raw_code_support_research"]["bands"][0][
                "positive_raw_integer_supported_area_m2"
            ] = value
            with self.subTest(value=str(value)), self.assertRaises(ExteriorReceiptBlocked):
                validate(r)

    def test_privacy_and_nodata_flags_mandatory(self):
        for key in (
            "positive_raw_code_not_confirmed_as_centimetres_or_metres",
            "building_raster_nodata_never_interpreted_as_dry",
            "exterior_rings_not_building_loss_depth",
        ):
            r = fixture()
            r["exterior_raw_code_support_research"][key] = False
            with self.subTest(key=key), self.assertRaises(ExteriorReceiptBlocked):
                validate(r)
        r = fixture()
        r["exterior_raw_code_support_research"]["cat_model_or_insurer_exposure_admitted"] = True
        with self.assertRaises(ExteriorReceiptBlocked):
            validate(r)

    def test_cli_rejects_duplicate_json_keys_and_oversized_input(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "aggregate.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main([str(path)]), 0)
            raw = path.read_text(encoding="utf-8")
            path.write_text(raw.replace('"profile": ', '"profile": "forged", "profile": ', 1),
                            encoding="utf-8")
            self.assertEqual(main([str(path)]), 2)
            path.write_text(" " * 40001, encoding="utf-8")
            self.assertEqual(main([str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
