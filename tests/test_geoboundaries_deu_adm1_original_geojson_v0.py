# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic 16-state geoBoundaries original-geometry fail-closed regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import unittest

from research_runners.geoboundaries_deu_adm1_original_geojson_v0 import (
    BoundaryGeometryError, EXPECTED_FEATURES, MAX_SOURCE_BYTES,
    SOURCE_GIT_COMMIT, SOURCE_LFS_SIZE, SOURCE_LFS_OID_SHA256,
    inspect_geojson_bytes,
)

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None


def valid_collection() -> dict:
    features = []
    for index in range(EXPECTED_FEATURES):
        col, row = index % 4, index // 4
        x, y = 6.0 + col * 1.1, 48.0 + row * 1.1
        ring = [[x, y], [x + 0.7, y], [x + 0.7, y + 0.7],
                [x, y + 0.7], [x, y]]
        features.append({
            "type": "Feature",
            "properties": {
                "shapeID": f"synthetic-test-{index:02d}",
                "shapeName": f"STATE-{index:02d}",
                "shapeGroup": "DEU",
                "shapeType": "ADM1",
            },
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })
    return {"type": "FeatureCollection", "features": features}


def raw(doc: dict) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def run_fixture(doc: dict):
    data = raw(doc)
    return inspect_geojson_bytes(data, expected_sha256=hashlib.sha256(data).hexdigest(),
                                 expected_size=len(data))


class OriginalGeoBoundariesStructureTests(unittest.TestCase):
    def test_frozen_git_lfs_original_byte_identity(self):
        self.assertEqual(SOURCE_GIT_COMMIT, "9469f09")
        self.assertEqual(SOURCE_LFS_SIZE, 6254151)
        self.assertEqual(len(SOURCE_LFS_OID_SHA256), 64)

    def test_pointer_file_cannot_masquerade_as_geometry(self):
        pointer = (b"version https://git-lfs.github.com/spec/v1\n"
                   b"oid sha256:0123456789012345678901234567890123456789012345678901234567890123\n"
                   b"size 6254151\n")
        with self.assertRaisesRegex(BoundaryGeometryError, "pointer"):
            inspect_geojson_bytes(pointer, expected_sha256=hashlib.sha256(pointer).hexdigest(),
                                  expected_size=len(pointer))

    def test_mismatched_size_and_digest_and_oversized_payload_are_blocked(self):
        b = raw(valid_collection())
        for size, digest in ((len(b) - 1, hashlib.sha256(b).hexdigest()),
                             (len(b), "0" * 64)):
            with self.assertRaises(BoundaryGeometryError):
                inspect_geojson_bytes(b, expected_sha256=digest, expected_size=size)
        with self.assertRaises(BoundaryGeometryError):
            inspect_geojson_bytes(b"x" * (MAX_SOURCE_BYTES + 1),
                                  expected_sha256="0" * 64,
                                  expected_size=MAX_SOURCE_BYTES + 1)

    def test_duplicate_json_keys_and_nan_are_rejected(self):
        for payload in (b'{"type":"FeatureCollection","type":"FeatureCollection"}',
                        b'{"type":"FeatureCollection","features":NaN}'):
            with self.assertRaises(BoundaryGeometryError):
                inspect_geojson_bytes(payload, expected_sha256=hashlib.sha256(payload).hexdigest(),
                                      expected_size=len(payload))


@unittest.skipUnless(HAS_SHAPELY, "Spatial regression job installs reviewed Shapely")
class GeoBoundariesPolygonTests(unittest.TestCase):
    def test_synthetic_deu16_aggregate_only(self):
        report = run_fixture(valid_collection())
        self.assertEqual(report["features"], 16)
        self.assertEqual(report["unique_feature_ids"], 16)
        self.assertEqual(report["unique_names"], 16)
        self.assertEqual(report["total_polygon_coordinates"], 80)
        self.assertEqual(report["max_polygon_intersection_square_degrees"], 0.0)
        self.assertFalse(report["source_geometry_admitted_to_model"])
        self.assertFalse(report["provider_bytes_persisted"])
        self.assertNotIn("shapes", report)
        self.assertNotIn("features_data", report)
        self.assertNotIn("source_feature_names", report)

    def test_wrong_feature_count_fails(self):
        obj = valid_collection()
        obj["features"].pop()
        with self.assertRaisesRegex(BoundaryGeometryError, "16"):
            run_fixture(obj)

    def test_original_id_name_type_country_crs_drift(self):
        changes = (
            ("shapeGroup", "FRA"),
            ("shapeType", "ADM2"),
            ("shapeID", ""),
            ("shapeName", ""),
        )
        for field, changed in changes:
            obj = valid_collection()
            obj["features"][0]["properties"][field] = changed
            with self.subTest(field=field), self.assertRaises(BoundaryGeometryError):
                run_fixture(obj)
        obj = valid_collection()
        obj["features"][0]["properties"]["shapeID"] = obj["features"][1]["properties"]["shapeID"]
        with self.assertRaisesRegex(BoundaryGeometryError, "duplicate"):
            run_fixture(obj)
        obj = valid_collection()
        obj["crs"] = {"type": "name", "properties": {"name": "EPSG:3857"}}
        with self.assertRaisesRegex(BoundaryGeometryError, "CRS"):
            run_fixture(obj)

    def test_polygon_self_intersection_and_coordinates_outside_country_fail(self):
        obj = valid_collection()
        obj["features"][0]["geometry"]["coordinates"] = [[
            [6.0, 48.0], [6.7, 48.7], [6.7, 48.0], [6.0, 48.7], [6.0, 48.0]
        ]]
        with self.assertRaisesRegex(BoundaryGeometryError, "invalid"):
            run_fixture(obj)
        obj = valid_collection()
        obj["features"][0]["geometry"]["coordinates"] = [[
            [26.0, 48.0], [26.7, 48.0], [26.7, 48.7], [26.0, 48.7], [26.0, 48.0]
        ]]
        with self.assertRaisesRegex(BoundaryGeometryError, "outside Germany"):
            run_fixture(obj)

    def test_material_interstate_overlap_fails(self):
        obj = valid_collection()
        obj["features"][1]["geometry"] = copy.deepcopy(obj["features"][0]["geometry"])
        with self.assertRaisesRegex(BoundaryGeometryError, "overlapping"):
            run_fixture(obj)


if __name__ == "__main__":
    unittest.main()
