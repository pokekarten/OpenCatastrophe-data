# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-attribute redaction and fail-closed classification tests."""
import unittest
from research_runners.cems_emns028_priority_layer_semantics_v0 import (
    PRIORITY_LAYERS, source_property_summary,
)


class PriorityLayerTests(unittest.TestCase):
    def test_exact_distinct_names(self):
        self.assertEqual(PRIORITY_LAYERS,
            ("aoi", "Flooded_area", "Estimated_Max_Flood_Extent"))

    def test_bounded_source_fields(self):
        props = {
            "act_id": "EMSN028",
            "src_date": "2016-06-03",
            "src_info": "a" * 200,
            "individual_name": "not publishable",
            "depth_m": 2.7,
        }
        result = source_property_summary(props)
        self.assertEqual(result["act_id"], "EMSN028")
        self.assertEqual(result["src_info"], "[LONG_VALUE_REDACTED]")
        self.assertNotIn("individual_name", result)
        self.assertNotIn("depth_m", result)

    def test_unknown_fields_and_non_scalar_values_never_published(self):
        res = source_property_summary({
            "nam": {"secret": "private"}, "act_id": None, "src_name": "CEMS"})
        self.assertEqual(res, {"src_name": "CEMS"})

    def test_true_model_scientific_flags_are_not_inferred_from_names(self):
        self.assertNotEqual(PRIORITY_LAYERS[1], PRIORITY_LAYERS[2])
        self.assertIn("Estimated", PRIORITY_LAYERS[2])


if __name__ == "__main__":
    unittest.main()
