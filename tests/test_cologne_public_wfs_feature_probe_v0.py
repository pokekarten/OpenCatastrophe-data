# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic one-feature WFS GeoJSON validation and CRS-negative tests."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

MODULE = Path(__file__).resolve().parents[1] / "research_runners" / "cologne_public_wfs_feature_probe_v0.py"
spec = importlib.util.spec_from_file_location("cologne_public_wfs_feature_probe_v0", MODULE)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

TREE = {
    "type": "FeatureCollection",
    "features": [{"type": "Feature",
                  "geometry": {"type": "Point", "coordinates": [350000.5, 5648000.2]},
                  "properties": {"Baumnummer": "synthetic", "Höhe": 12}}],
}
KGG = {
    "type": "FeatureCollection",
    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    "features": [{"type": "Feature",
                  "geometry": {"type": "MultiPolygon",
                               "coordinates": [[[[6.9, 50.9], [7.0, 50.9],
                                                 [7.0, 51.0], [6.9, 50.9]]]]},
                  "properties": {"Name": "synthetic"}}],
}


def as_bytes(doc):
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


class CologneFeatureProbeTests(unittest.TestCase):
    def test_projected_tree_never_gets_geographic_approval(self):
        result = probe.inspect_geojson(as_bytes(TREE), "tree")
        self.assertEqual(result["source_crs_declaration"], "not_declared")
        self.assertIn("not_approved", result["coordinate_status"])
        self.assertFalse(result["model_admitted"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_declared_kgg_lonlat_is_only_schema_checked(self):
        result = probe.inspect_geojson(as_bytes(KGG), "kgg")
        self.assertEqual(result["source_crs_declaration"], "EPSG:4326")
        self.assertEqual(result["geometry_type"], "MultiPolygon")
        self.assertEqual(result["feature_count"], 1)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertFalse(result["model_admitted"])

    def test_mislabeled_kgg_crs_rejected(self):
        wrong = json.loads(json.dumps(KGG))
        wrong["crs"]["properties"]["name"] = "EPSG:25832"
        with self.assertRaises(probe.WfsSampleError):
            probe.inspect_geojson(as_bytes(wrong), "kgg")

    def test_geographic_coordinates_out_of_range_rejected(self):
        wrong = json.loads(json.dumps(KGG))
        wrong["features"][0]["geometry"]["coordinates"][0][0][0] = [350000, 5600000]
        with self.assertRaises(probe.WfsSampleError):
            probe.inspect_geojson(as_bytes(wrong), "kgg")

    def test_more_than_one_feature_rejected(self):
        wrong = json.loads(json.dumps(TREE))
        wrong["features"].append(wrong["features"][0])
        with self.assertRaises(probe.WfsSampleError):
            probe.inspect_geojson(as_bytes(wrong), "tree")

    def test_malformed_and_duplicate_keys_rejected(self):
        for raw in (b'', b'{"type":"x","type":"FeatureCollection"}', b'{"type":',
                    b'{"type":"FeatureCollection","x":NaN}', b'x' * (probe.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=len(raw)):
                with self.assertRaises(probe.WfsSampleError):
                    probe.inspect_geojson(raw, "tree")

    def test_unexpected_geometry_type_rejected(self):
        with self.assertRaises(probe.WfsSampleError):
            probe.inspect_geojson(as_bytes(TREE), "kgg")

    def test_mock_only_live_receipt_does_not_store_bytes(self):
        class Headers:
            def get_content_type(self):
                return "application/json"

            def get(self, _name):
                return None

        class Response:
            status = 200
            headers = Headers()

            def __init__(self, url):
                self.url = url

            def geturl(self):
                return self.url

            def read(self, n):
                assert n == probe.MAX_RESPONSE_BYTES + 1
                return as_bytes(KGG)

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class Opener:
            def open(self, req, timeout):
                assert timeout == 20
                return Response(req.full_url)

        with mock.patch.object(probe, "build_opener", return_value=Opener()):
            receipt = probe.probe_live("kgg")
        self.assertTrue(receipt["verified_live"])
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["model_admitted"])


if __name__ == "__main__":
    unittest.main()
