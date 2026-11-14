# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline tests: no provider GET or Neon write."""
from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from research_runners import ghsl_bvv_cross_epoch_area_gate_v0 as gate


def ghsl(ident):
    r=gate.SAMPLES[ident]
    return {
        "sample_id":ident,"source_id":r["id"],"sample_kind":"observed_values",
        "sample_sha256":r["sha"],"provider_response_sha256":r["block"],
        "research_only":True,"model_input_approved":False,
        "sample_json":{
            "source_id":r["id"],"profile":"oc-ghsl-e2020-original-native-32x32-values-aggregate-research-v0",
            "product_epoch":2020,"source_license":"CC BY 4.0",
            "model_input_approved":False,
            "fixed_original_window_shape":[32,32],
            "fixed_original_window_global_col_row":[22973,4899],
            "original_source_compressed_block_sha256":r["block"],
            "fixed_window_uint32_le_sha256":r["window"],
            "original_data_unit_from_publisher":r["units"],
            "fixed_window_positive_sum_raw_source_units":r["raw_sum"],
            "fixed_window_positive_non_sentinel_cells":937,
            "fixed_window_zero_cells":87,
            "fixed_window_potential_uint32_max_sentinel_cells":0,
            "source_pixel_window_values_observed_for_research_only":True,
            "individual_source_raster_pixels_persisted":False,
            "insurer_exposure_or_tiv_inferred":False,
            "native_window_scientifically_calibrated":False,
        }
    }


def bvv():
    return {
        "source_id":"de.bayern.hausumringe",
        "profile":"oc-bvv-original-oberbayern-complete-shp-ghsl-roi-v0",
        "official_source_url":gate.BVV_SOURCE,
        "original_member":"hausumringe.shp",
        "exact_source_range":gate.RANGE,
        "original_partial_first_49197_sha256":gate.SOURCE_PREFIX_SHA256,
        "original_full_decoded_shape_bytes":gate.UNCOMPRESSED_SHP_BYTES,
        "original_full_decoded_shape_crc32":f"{gate.ORIGINAL_DIRECTORY_CRC32_CLAIM:08x}",
        "original_full_native_records_checked":gate.EXPECTED_SHX_ENTRIES,
        "original_shape_polygons_checked":gate.EXPECTED_SHX_ENTRIES,
        "full_original_member_compressed_bytes":gate.READ_BYTES-45,
        "provider_original_206_segments_verified":gate.EXPECTED_SEGMENTS,
        "provider_source_range_mode":"contiguous_exact_206_bounded_segments",
        "original_source_epoch_is_2020":False,"ghsl_source_epoch":2020,
        "roi_complete_for_this_verified_SHAPE_archive_only":True,
        "original_cadastre_survey_vintage_verified":False,
        "historical_2020_ground_truth_verified":False,
        "ghsl_actual_accuracy_or_tiv_validated":False,
        "source_coordinates_geometries_or_bytes_persisted":False,
        "source_bytes_committed_or_persisted":False,
        "model_input_approved":False,
        "complete_original_zip_hash_verified":False,
        "official_BVV_HU_BY_CC_BY_4_license_only":True,
        "original_full_decoded_shape_sha256":"c"*64,
        "full_original_compressed_member_sha256":"e"*64,
        "roi_original_polygon_records_intersecting":250000,
        "roi_bbox_candidates":350000,
        "roi_invalid_geos_rings":0,
        "roi_invalid_geos_polygons":0,
        "projected_utm32_study_roi_area_m2":600_000_000,
        "roi_original_polygon_areas_union_m2":50_000_000,
        "roi_original_polygon_areas_sum_pre_union_m2":55_000_000,
        "roi_original_polygon_overlap_area_m2":5_000_000,
        "roi_geos_union_batches_completed":123,
    }


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.patcher=patch.object(gate,"frozen_roi_geometries",
            return_value=(SimpleNamespace(area=600_000_000),None))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_only_complete_source_allows_descriptive_cross_epoch_area(self):
        out=gate.compare(ghsl(49),ghsl(50),bvv())
        self.assertEqual(out["original_bvv_current_cadastre_roi_polygon_union_m2"],50_000_000)
        self.assertEqual(out["original_ghsl_built_surface_e2020_sum_m2"],74_802_406)
        self.assertEqual(out["original_ghsl_built_volume_e2020_sum_m3_context_only"],520_775_503)
        self.assertAlmostEqual(out["current_bvv_union_over_ghsl_e2020_modelled_surface_ratio"],50_000_000/74_802_406,places=6)
        self.assertFalse(out["model_input_approved"])
        self.assertFalse(out["ratio_is_accuracy_or_model_calibration_metric"])
        self.assertTrue(out["bvv_nonrandom_2026_source_not_historical_2020_ground_truth"])

    def test_incomplete_1m_original_run_cannot_count_as_complete(self):
        for field,value in (
            ("original_full_native_records_checked",1_000_000),
            ("roi_complete_for_this_verified_SHAPE_archive_only",False),
            ("original_full_decoded_shape_crc32","00000000"),
            ("provider_original_206_segments_verified",19),
            ("provider_source_range_mode","single_full_206"),
            ("original_cadastre_survey_vintage_verified",True),
            ("model_input_approved",True),
            ("source_coordinates_geometries_or_bytes_persisted",True),
            ("original_partial_first_49197_sha256","0"*64),
        ):
            with self.subTest(field=field):
                row=bvv()
                row[field]=value
                with self.assertRaises(gate.ComparisonBlocked):
                    gate.compare(ghsl(49),ghsl(50),row)

    def test_noon_original_ghsl_s_v_pinning_and_unit_conversion(self):
        for ident in (49,50):
            for field,value in (
                ("fixed_window_positive_sum_raw_source_units",1),
                ("fixed_original_window_global_col_row",[22974,4899]),
                ("source_license","not-reviewed"),
                ("native_window_scientifically_calibrated",True),
                ("model_input_approved",True),
            ):
                with self.subTest(sample=ident,field=field):
                    source=ghsl(ident)
                    source["sample_json"][field]=value
                    with self.assertRaises(gate.ComparisonBlocked):
                        gate.verify_ghsl_neon_row(source,ident)
            altered=ghsl(ident)
            altered["sample_sha256"]="f"*64
            with self.assertRaises(gate.ComparisonBlocked):
                gate.verify_ghsl_neon_row(altered,ident)

    def test_rollback_on_invalid_union_or_bbox(self):
        for field,value in (
            ("roi_original_polygon_areas_sum_pre_union_m2",40_000_000),
            ("roi_original_polygon_areas_union_m2",700_000_000),
            ("roi_original_polygon_overlap_area_m2",-2),
            ("projected_utm32_study_roi_area_m2",600_000_001),
            ("roi_invalid_geos_rings",1),
            ("roi_original_polygon_records_intersecting",360000),
            ("roi_geos_union_batches_completed",0),
            ("original_full_decoded_shape_sha256","not-sha"),
        ):
            with self.subTest(field=field):
                row=bvv()
                row[field]=value
                with self.assertRaises(gate.ComparisonBlocked):
                    gate.verify_full_bvv_receipt(row)

    def test_raw_source_not_needed_for_offline_comparison(self):
        result=gate.compare(ghsl(49),ghsl(50),bvv())
        self.assertNotIn("geometry",result)
        self.assertNotIn("source_pixels",result)
        self.assertFalse(result["individual_original_data_coordinates_or_pixels_emitted"])

    def test_original_comparison_requires_three_local_paths(self):
        with self.assertRaises(SystemExit) as e:
            gate.main([])
        self.assertNotEqual(e.exception.code,0)


if __name__=="__main__":
    unittest.main()
