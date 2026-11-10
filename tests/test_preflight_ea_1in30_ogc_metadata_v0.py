# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic synthetic-only tests for published EA OGC service metadata."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.preflight_ea_1in30_ogc_metadata_v0 import (
    BBOX, BBOX_CRS, COLLECTION, DATASET_UUID, EXPECTED_FIELDS,
    MAX_BYTES, RECEIPTS, STORAGE_CRS, EAOgcMetadataError, inspect_metadata,
)

COLLECTIONS_URL = (
    "https://environment.data.gov.uk/geoservices/datasets/"
    + DATASET_UUID + "/ogc/features/v1/collections?f=application%2Fjson"
)


def fixture(document: str) -> dict:
    link = [{"rel": "self", "type": "application/json", "href": "https://example.invalid/do-not-follow"}]
    extent = {"spatial": {"bbox": [BBOX.copy()], "crs": BBOX_CRS}}
    if document == "landing":
        return {
            "title": "WFS",
            "description": "Defra Network WFS server provided by the Environment Agency",
            "links": [{"rel": "data", "type": "application/json", "href": COLLECTIONS_URL}],
        }
    if document == "conformance":
        return {
            "conformsTo": [
                "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
                "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
            ],
            "links": link,
        }
    if document == "collections":
        return {"collections": [{"id": COLLECTION, "extent": extent}], "links": link}
    if document == "collection":
        return {
            "id": COLLECTION, "storageCrs": STORAGE_CRS,
            "crs": [BBOX_CRS, STORAGE_CRS],
            "extent": extent, "links": link,
        }
    if document == "queryables":
        return {
            "title": "Rivers 1In30 Sea 1In30 Defended Depths",
            "type": "object",
            "properties": copy.deepcopy(EXPECTED_FIELDS),
            "links": link,
        }
    raise AssertionError("invalid fixture selector")


def check(doc: dict, document: str) -> dict:
    return inspect_metadata(json.dumps(doc, sort_keys=True).encode("utf-8"), document)


class EA3p3OgcMetadataTests(unittest.TestCase):
    def test_five_synthetic_metadata_types_are_valid_without_admission(self):
        for name in RECEIPTS:
            with self.subTest(name=name):
                result = check(fixture(name), name)
                self.assertFalse(result["matches_original_observed_bytes"])
                self.assertFalse(result["provider_authenticity_proven_by_this_parser"])
                self.assertFalse(result["source_rights_approved"])
                self.assertFalse(result["model_data_admitted"])
                self.assertFalse(result["verified_property_flood_depth"])
                self.assertFalse(result["has_verified_unavailable_class_values"])
                self.assertTrue(result["depth_band_is_string_not_metres"])
                self.assertEqual(result["native_collection_crs"], STORAGE_CRS)
                self.assertEqual(result["extent_crs"], BBOX_CRS)
                self.assertEqual(result["actual_provider_features_read"], 0)
                self.assertEqual(result["provider_requests_performed"], 0)
                self.assertEqual(result["external_resource_links_followed"], 0)
                self.assertNotIn("example.invalid", json.dumps(result))

    def test_pinned_five_original_metadata_hashes_are_well_formed(self):
        self.assertEqual(len(RECEIPTS), 5)
        for size, digest in RECEIPTS.values():
            self.assertGreater(size, 0)
            self.assertEqual(len(digest), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_unknown_document(self):
        with self.assertRaises(EAOgcMetadataError):
            check(fixture("landing"), "items")

    def test_forged_features_payload(self):
        data = fixture("collection")
        data["features"] = [{"id": "synthetic"}]
        with self.assertRaises(EAOgcMetadataError):
            check(data, "collection")

    def test_empty_or_oversized_input(self):
        for value in (b"", b"x" * (MAX_BYTES + 1)):
            with self.assertRaises(EAOgcMetadataError):
                inspect_metadata(value, "landing")

    def test_duplicate_json_key(self):
        with self.assertRaises(EAOgcMetadataError):
            inspect_metadata(b'{"title":"WFS","title":"WFS"}', "landing")

    def test_nan_and_infinite_float(self):
        for payload in (b'{"x":NaN}', b'{"x":1e999}'):
            with self.assertRaises(EAOgcMetadataError):
                inspect_metadata(payload, "landing")

    def test_wrong_landing_collection_link(self):
        data = fixture("landing")
        data["links"][0]["href"] = "https://untrusted.example.invalid/collections"
        with self.assertRaises(EAOgcMetadataError):
            check(data, "landing")

    def test_missing_ogc_core_standard(self):
        data = fixture("conformance")
        data["conformsTo"].pop(0)
        with self.assertRaises(EAOgcMetadataError):
            check(data, "conformance")

    def test_extra_or_wrong_collection(self):
        data = fixture("collections")
        data["collections"].append({"id": "unexpected"})
        with self.assertRaises(EAOgcMetadataError):
            check(data, "collections")
        data = fixture("collections")
        data["collections"][0]["id"] = "other"
        with self.assertRaises(EAOgcMetadataError):
            check(data, "collections")

    def test_reject_bbox_assigned_native_crs_instead_of_crs84(self):
        for name in ("collections", "collection"):
            data = fixture(name)
            item = data["collections"][0] if name == "collections" else data
            item["extent"]["spatial"]["crs"] = STORAGE_CRS
            with self.assertRaises(EAOgcMetadataError):
                check(data, name)

    def test_wrong_coverage_bbox(self):
        data = fixture("collection")
        data["extent"]["spatial"]["bbox"][0][0] = -1.0
        with self.assertRaises(EAOgcMetadataError):
            check(data, "collection")

    def test_no_native_epsg27700(self):
        data = fixture("collection")
        data["storageCrs"] = BBOX_CRS
        with self.assertRaises(EAOgcMetadataError):
            check(data, "collection")

    def test_depth_band_is_string_not_numeric_metres(self):
        data = fixture("queryables")
        data["properties"]["depth_band"]["type"] = "number"
        with self.assertRaises(EAOgcMetadataError):
            check(data, "queryables")

    def test_missing_flood_source(self):
        data = fixture("queryables")
        data["properties"].pop("flood_source")
        with self.assertRaises(EAOgcMetadataError):
            check(data, "queryables")

    def test_unexpected_geometry_reference(self):
        data = fixture("queryables")
        data["properties"]["shape"]["$ref"] = "https://bad.invalid/schema"
        with self.assertRaises(EAOgcMetadataError):
            check(data, "queryables")


if __name__ == "__main__":
    unittest.main()
