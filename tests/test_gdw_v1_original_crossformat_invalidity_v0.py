# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic original-format invalid-ID overlap tests; no external records."""
from __future__ import annotations

import unittest

from research_runners import gdw_v1_original_crossformat_invalidity_v0 as s
from research_runners.gdw_v1_original_crossformat_id_receipt_v0 import (
    GDW_V1_ORIGINAL_CROSSFORMAT_ID_RECEIPT_V0 as EXACT_SOURCE,
)
from research_runners.gdw_v1_original_filegdb_receipt_v0 import (
    GDW_V1_ORIGINAL_FILEGDB_RECEIPT_V0 as GDB,
)
from research_runners.gdw_v1_original_invalidity_family_receipt_v0 import (
    GDW_V1_ORIGINAL_INVALIDITY_REASON_RECEIPT_V0 as SHP,
)

class CrossFormatOriginalIDTests(unittest.TestCase):
    def test_frozen_real_original_crossformat_concordance(self):
        r = EXACT_SOURCE
        self.assertEqual(r["original_shapefile_sha256"], SHP["original_file_sha256"])
        self.assertEqual(r["original_filegdb_sha256"], GDB["original_sha256_observed"])
        self.assertEqual(r["barrier_ids_present_in_both_formats"], 41145)
        self.assertEqual(r["reservoir_ids_present_in_both_formats"], 35295)
        self.assertEqual(r["invalid_polygon_ids_in_both_formats"], 221)
        for name in ("barrier_ids_shp_only", "barrier_ids_gdb_only",
                     "reservoir_ids_shp_only", "reservoir_ids_gdb_only",
                     "invalid_polygon_ids_shp_only", "invalid_polygon_ids_gdb_only"):
            self.assertEqual(r[name], 0)
        self.assertTrue(r["all_barrier_ids_match"])
        self.assertTrue(r["all_reservoir_ids_match"])
        self.assertTrue(r["all_geos_invalid_ids_match"])
        for name in ("geometries_topologically_valid_for_all_reservoirs",
                     "automatic_source_repair_performed",
                     "source_feature_ids_coordinates_or_raw_bytes_exported",
                     "flood_inundation_or_dam_failure_calibration_proven",
                     "model_source_admitted"):
            self.assertFalse(r[name])

    def test_matching_original_bad_ids_not_exported(self):
        r=s.aggregate_concordance(
            {1,2,3,4}, {1,2,3}, {2,3},
            {1,2,3,4}, {1,2,3}, {2,3}
        )
        self.assertEqual(r["same_invalid_gdw_id_in_both_formats"],2)
        self.assertEqual(r["invalid_gdw_id_only_in_shp"],0)
        self.assertEqual(r["invalid_gdw_id_only_in_gdb"],0)
        self.assertTrue(r["entire_invalid_gdw_id_sets_match"])
        self.assertTrue(r["entire_barrier_id_universes_match"])
        self.assertTrue(r["entire_polygon_id_universes_match"])
        self.assertFalse(r["source_ids_coordinates_geometries_emitted"])
        self.assertNotIn("[",str(r))

    def test_equal_invalid_counts_do_not_prove_same_ids(self):
        r=s.aggregate_concordance(
            {1,2,3,4}, {1,2,3}, {2},
            {1,2,3,4}, {1,2,3}, {3}
        )
        self.assertEqual(r["shp_invalid_geos_count"],1)
        self.assertEqual(r["gdb_invalid_geos_count"],1)
        self.assertEqual(r["same_invalid_gdw_id_in_both_formats"],0)
        self.assertEqual(r["invalid_gdw_id_only_in_shp"],1)
        self.assertEqual(r["invalid_gdw_id_only_in_gdb"],1)
        self.assertFalse(r["entire_invalid_gdw_id_sets_match"])
        self.assertTrue(r["entire_polygon_id_universes_match"])

    def test_different_polygon_and_barrier_id_universes_diagnosed(self):
        r=s.aggregate_concordance(
            {1,2,3,4}, {1,2}, {2},
            {2,3,4,5}, {2,3}, {2}
        )
        self.assertFalse(r["entire_barrier_id_universes_match"])
        self.assertFalse(r["entire_polygon_id_universes_match"])
        self.assertEqual(r["barrier_id_in_both"],3)
        self.assertEqual(r["polygon_id_in_both"],1)
        self.assertEqual(r["same_invalid_gdw_id_in_both_formats"],1)

    def test_invalid_id_not_in_original_layer_blocks(self):
        with self.assertRaises(s.GDWConcordanceError):
            s.aggregate_concordance({1,2},{1},{999},{1,2},{1},set())
        with self.assertRaises(s.GDWConcordanceError):
            s.aggregate_concordance({1,2},{1},set(),{1,2},{1},{999})
        with self.assertRaises(s.GDWConcordanceError):
            s.aggregate_concordance({1},{2},set(),{1,2},{2},set())

    def test_original_gdb_receipt_matches_other_source_counts_only(self):
        self.assertEqual(GDB["original_file_bytes"],57476758)
        self.assertEqual(GDB["original_sha256_observed"],
                         "5ebb1092e355f1833132be8a16340da7de979314d06aba00e57eb7412884f09f")
        self.assertEqual(GDB["valid_reservoir_polygons"],
                         SHP["geos_valid_original_reservoir_polygons"])
        self.assertEqual(GDB["invalid_reservoir_polygons"],
                         SHP["geos_invalid_original_reservoir_polygons"])
        self.assertEqual(GDB["invalid_geos_reason_families"],
                         SHP["invalid_geos_reason_families"])
        self.assertFalse(GDB["cross_format_per_id_compared"])
        self.assertFalse(GDB["model_input_admitted"])


if __name__ == "__main__":
    unittest.main()
