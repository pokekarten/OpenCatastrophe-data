# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for EA 3.3% AEP original feature label semantics."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.ea_flood_original_feature_label_qa_v0 import (
    BANDS_MM, COLLECTION, MAX_BYTES, MISSING_BAND, SOURCES,
    FeatureLabelBlocked, inspect_original_label_response,
)


def fixture(band: str = "150-300mm", source: str = "sea") -> dict:
    return {
        "type": "FeatureCollection",
        "numberMatched": 1,
        "numberReturned": 1,
        "features": [{
            "type": "Feature",
            "id": COLLECTION + ".1",
            "properties": {
                "depth_band": band,
                "flood_source": source,
                "shape_length": None,
                "shape_area": None,
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[0.11, 50.22], [0.12, 50.23]]]],
            },
        }],
    }


def check(obj: dict) -> dict:
    return inspect_original_label_response(json.dumps(obj, sort_keys=True).encode("utf-8"))


class EAFloodOriginalFeatureLabelQATests(unittest.TestCase):
    def test_seven_original_label_classes_are_recognized_without_loss_admission(self):
        self.assertEqual(len(BANDS_MM), 7)
        for label, (lower, upper) in BANDS_MM.items():
            with self.subTest(label=label):
                out = check(fixture(label))
                self.assertEqual(out["depth_band"], label)
                self.assertEqual(out["nominal_lower_boundary_mm"], lower)
                self.assertEqual(out["nominal_upper_boundary_mm"], upper)
                self.assertFalse(out["depth_band_missing"])
                self.assertFalse(out["source_authenticity_proven_by_this_parser"])
                self.assertFalse(out["raw_feature_source_and_release_authenticity_verified"])
                self.assertFalse(out["geometry_crs_verified"])
                self.assertFalse(out["geometry_topology_verified"])
                self.assertFalse(out["model_data_admitted"])
                self.assertFalse(out["commercial_asset_rights_approved"])
                self.assertIsNone(out["representative_depth_mm"])
                self.assertIsNone(out["estimated_damage_ratio"])
                self.assertFalse(out["physical_depth_at_individual_building_verified"])

    def test_four_original_flood_source_labels_are_distinct(self):
        self.assertEqual(SOURCES, {"river", "sea", "rivers and sea", "unavailable"})
        for source in SOURCES:
            with self.subTest(source=source):
                out = check(fixture(source=source))
                self.assertEqual(out["flood_source"], source)
                self.assertEqual(out["flood_source_missing"], source == "unavailable")

    def test_unavailable_depth_is_missing_not_dry(self):
        out = check(fixture(MISSING_BAND, "unavailable"))
        self.assertTrue(out["depth_band_missing"])
        self.assertTrue(out["flood_source_missing"])
        self.assertIsNone(out["nominal_lower_boundary_mm"])
        self.assertIsNone(out["nominal_upper_boundary_mm"])
        self.assertTrue(out["unknown_or_missing_coverage_is_not_dry"])
        self.assertFalse(out["model_data_admitted"])

    def test_open_depth_intervals_not_imputed(self):
        low = check(fixture("<150mm"))
        high = check(fixture(">2300mm"))
        self.assertIsNone(low["nominal_lower_boundary_mm"])
        self.assertIsNone(high["nominal_upper_boundary_mm"])
        self.assertFalse(low["lower_boundary_inclusive_verified"])
        self.assertFalse(high["upper_boundary_inclusive_verified"])

    def test_original_values_differ_from_web_captions(self):
        with self.assertRaises(FeatureLabelBlocked):
            check(fixture("Over 2300mm"))
        with self.assertRaises(FeatureLabelBlocked):
            check(fixture("Unavailable"))
        with self.assertRaises(FeatureLabelBlocked):
            check(fixture("Up to 150mm"))

    def test_unknown_depth_band_fails_closed(self):
        for v in ("", "0-150mm", "no flood", "150 – 300mm", "200-400mm", None, 0):
            with self.subTest(v=v), self.assertRaises(FeatureLabelBlocked):
                check(fixture(v))

    def test_unknown_flood_source_fails_closed(self):
        for v in ("River", "river and sea", "surface water", "", None, 2):
            with self.subTest(v=v), self.assertRaises(FeatureLabelBlocked):
                check(fixture(source=v))

    def test_no_geometry_coordinates_identifiers_or_urls_emitted(self):
        doc = fixture()
        doc["features"][0]["geometry"]["coordinates"] = [[[[123.456, 54.321]]]]
        out = check(doc)
        serialized = json.dumps(out)
        self.assertNotIn("123.456", serialized)
        self.assertNotIn("54.321", serialized)
        self.assertNotIn(COLLECTION + ".1", serialized)
        self.assertFalse(out["geometry_coordinates_reported"])
        self.assertEqual(out["provider_requests_performed"], 0)

    def test_reject_non_feature_collection_and_zero_features(self):
        doc = fixture()
        doc["type"] = "Feature"
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)
        doc = fixture()
        doc["features"] = []
        doc["numberReturned"] = 0
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_reject_many_features(self):
        doc = fixture()
        doc["features"].append(copy.deepcopy(doc["features"][0]))
        doc["numberReturned"] = 2
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_reject_wrong_collection_identity(self):
        doc = fixture()
        doc["features"][0]["id"] = "other-layer.1"
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_reject_unexpected_property(self):
        doc = fixture()
        doc["features"][0]["properties"]["private_location"] = "do-not-return"
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_reject_wrong_geometry_shape(self):
        doc = fixture()
        doc["features"][0]["geometry"]["type"] = "Point"
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_reject_invalid_property_numeric_types(self):
        doc = fixture()
        doc["features"][0]["properties"]["shape_area"] = False
        with self.assertRaises(FeatureLabelBlocked):
            check(doc)

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(FeatureLabelBlocked):
            inspect_original_label_response(b'{"type":"FeatureCollection","type":"FeatureCollection"}')

    def test_nonfinite_json_values_rejected(self):
        for raw in (b'{"x":NaN}', b'{"x":1e999}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(FeatureLabelBlocked):
                inspect_original_label_response(raw)

    def test_bounded_response_and_wrong_python_type(self):
        for raw in (b"", b"x" * (MAX_BYTES + 1), "string-not-bytes"):
            with self.subTest(raw_type=type(raw)), self.assertRaises(FeatureLabelBlocked):
                inspect_original_label_response(raw)


if __name__ == "__main__":
    unittest.main()
