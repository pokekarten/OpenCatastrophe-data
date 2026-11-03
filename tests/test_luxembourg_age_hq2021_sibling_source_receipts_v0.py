# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only AGE HQ10 / HQext source-label and structural admission tests."""
from __future__ import annotations

import unittest
from research_runners.luxembourg_age_hq2021_sibling_source_receipts_v0 import (
    summarize, SOURCES,
)
from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    HQ100OriginalError,
)


def receipt() -> dict:
    return {
        "original_zip_sha1_matches_publisher": True,
        "shp_records_match_dbf_records": True,
        "original_zip_sha256_observed": "a" * 64,
        "original_zip_bytes": 321,
        "archive_member_count": 2,
        "format_header_inventory_only": [
            {"format": ".dbf", "dbf_declared_records": 1,
             "dbf_field_schema": [{"name": "Shape_Area"}, {"name": "OBJECTID"}]},
            {"format": ".shp", "shp_polygon_record_count": 1,
             "shp_shape_type_code": 5, "shp_total_polygon_ring_parts": 3,
             "shp_total_coordinate_pairs_skipped_without_decoding": 14},
        ],
    }


class AGEHQ2021SiblingReceiptsTests(unittest.TestCase):
    def test_distinct_publisher_scenarios_and_nonadmission(self):
        self.assertNotEqual(SOURCES["hq10"]["sha1"], SOURCES["hqext"]["sha1"])
        self.assertNotEqual(SOURCES["hq10"]["url"], SOURCES["hqext"]["url"])
        for name in SOURCES:
            with self.subTest(scenario=name):
                result = summarize(name, receipt())
                self.assertEqual(result["scenario"], name)
                self.assertEqual(result["source_polygon_records"], 1)
                self.assertEqual(result["original_source_ring_parts"], 3)
                self.assertFalse(result["numeric_depth_semantics_verified"])
                self.assertFalse(result["shp_full_topology_or_axis_verified"])
                self.assertFalse(result["CAT_model_input_admitted"])
                self.assertNotIn("original_coordinates", result)

    def test_wrong_source_no_proof_bad_record_population_rejected(self):
        bad = receipt()
        for scenario in ("hq100", "", "x", None):
            with self.subTest(source=scenario), self.assertRaises(HQ100OriginalError):
                summarize(scenario, bad)
        other = receipt()
        other["original_zip_sha1_matches_publisher"] = False
        with self.assertRaises(HQ100OriginalError):
            summarize("hq10", other)
        other = receipt()
        other["format_header_inventory_only"][1]["shp_shape_type_code"] = 1
        with self.assertRaises(HQ100OriginalError):
            summarize("hqext", other)
        other = receipt()
        other["format_header_inventory_only"][1]["shp_polygon_record_count"] = 2
        with self.assertRaises(HQ100OriginalError):
            summarize("hq10", other)


if __name__ == "__main__":
    unittest.main()
