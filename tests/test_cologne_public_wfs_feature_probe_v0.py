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
        self.assertIn("not_model_approved", result["coordinate_status"])
        self.assertEqual(result["source_order"], "Baumnummer_ascending")
        self.assertEqual(len(result["tree_identifier_sha256"]), 64)
        self.assertFalse(result["model_admitted"])
        self.assertFalse(result["external_bytes_persisted"])


    def test_tree_source_request_pins_tree_identifier_order(self):
        self.assertIn("SORTBY=Baumnummer", probe.SOURCES["tree"]["url"])

    def test_tree_coordinate_range_outlier_rejected(self):
        for coord in ([6.91, 50.94], [950000, 100000], [float("inf"), 5648000]):
            wrong = json.loads(json.dumps(TREE))
            wrong["features"][0]["geometry"]["coordinates"] = coord
            with self.subTest(coord=coord), self.assertRaises(probe.WfsSampleError):
                probe.inspect_geojson(as_bytes(wrong), "tree")

    def test_missing_stable_tree_key_rejected(self):
        for value in ("", None, 123, " "):
            wrong = json.loads(json.dumps(TREE))
            wrong["features"][0]["properties"]["Baumnummer"] = value
            with self.subTest(value=value), self.assertRaises(probe.WfsSampleError):
                probe.inspect_geojson(as_bytes(wrong), "tree")

    def test_tree_declared_geographic_crs_with_projected_values_rejected(self):
        wrong = json.loads(json.dumps(TREE))
        wrong["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}
        with self.assertRaises(probe.WfsSampleError):
            probe.inspect_geojson(as_bytes(wrong), "tree")

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

    def test_multipolygon_rejects_corrupted_member_among_valid_coordinates(self):
        # The earlier recursive pair collector silently skipped a malformed
        # vertex and counted all the remaining positions as a valid polygon.
        wrong = json.loads(json.dumps(KGG))
        wrong["features"][0]["geometry"]["coordinates"][0][0].insert(
            1, ["not-a-longitude", 50.91]
        )
        with self.assertRaisesRegex(probe.WfsSampleError, "position"):
            probe.inspect_geojson(as_bytes(wrong), "kgg")

    def test_multipolygon_rejects_wrong_nesting_and_unclosed_ring(self):
        for defect in ("polygon_instead_of_multipolygon", "unclosed_ring",
                       "empty_inner_polygon", "missing_coordinate"):
            wrong = json.loads(json.dumps(KGG))
            geom = wrong["features"][0]["geometry"]
            if defect == "polygon_instead_of_multipolygon":
                geom["coordinates"] = geom["coordinates"][0]
            elif defect == "unclosed_ring":
                geom["coordinates"][0][0][-1] = [6.9, 51.0]
            elif defect == "empty_inner_polygon":
                geom["coordinates"].append([])
            else:
                geom["coordinates"][0][0][1] = [7.0]
            with self.subTest(defect=defect), self.assertRaises(probe.WfsSampleError):
                probe.inspect_geojson(as_bytes(wrong), "kgg")

    def test_projected_tree_rejects_hidden_extra_or_nonfinite_ordinate(self):
        for coords in (
            [350000.5, 5648000.2, {"ignored": "invalid"}],
            [350000.5, 5648000.2, False],
            [350000.5, 5648000.2, float("inf")],
            [350000.5, 5648000.2, 7, 8],
        ):
            wrong = json.loads(json.dumps(TREE))
            wrong["features"][0]["geometry"]["coordinates"] = coords
            with self.subTest(coords=coords), self.assertRaises(probe.WfsSampleError):
                probe.inspect_geojson(as_bytes(wrong), "tree")

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
