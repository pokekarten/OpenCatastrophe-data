# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import unittest
from urllib.parse import urlencode

from research_runners.ppri_polygon_geometry_preflight_v0 import audit

ROOT = "https://sig.seinegrandslacs.fr/arcgis/rest/services/Gestion_Eaux_Inondations_GP/MapServer/17/query"


def url(**extras):
    p = {"where": "objectid=574", "outFields": "objectid,code_zone",
         "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
    p.update(extras)
    return ROOT + "?" + urlencode(p)


def source(coords, kind="Polygon", objectid=574):
    return json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": objectid, "properties": {
            "objectid": objectid, "code_zone": "zone rouge"},
         "geometry": {"type": kind, "coordinates": coords}}
    ]}).encode()


class TopologyReceiptTests(unittest.TestCase):
    def test_valid_original_polygon_is_topologically_usable_but_never_admitted(self):
        raw = source([[[2.5, 48.5], [2.6, 48.5], [2.6, 48.6],
                       [2.5, 48.6], [2.5, 48.5]]])
        r = audit(raw, url(), 574)
        self.assertTrue(r["topology_valid"])
        self.assertTrue(r["safe_for_precise_spatial_overlay"])
        self.assertFalse(r["licence_reviewed"])
        self.assertFalse(r["cat_model_admitted"])

    def test_simplified_valid_polygon_cannot_be_used_for_precise_overlay(self):
        raw = source([[[2.5, 48.5], [2.6, 48.5], [2.6, 48.6],
                       [2.5, 48.6], [2.5, 48.5]]])
        r = audit(raw, url(maxAllowableOffset="0.00003", geometryPrecision="6"), 574)
        self.assertTrue(r["topology_valid"])
        self.assertFalse(r["safe_for_precise_spatial_overlay"])

    def test_bow_tie_is_invalid_and_blocked(self):
        raw = source([[[2.5, 48.5], [2.6, 48.6], [2.6, 48.5],
                       [2.5, 48.6], [2.5, 48.5]]])
        r = audit(raw, url(), 574)
        self.assertFalse(r["topology_valid"])
        self.assertFalse(r["safe_for_precise_spatial_overlay"])

    def test_wrong_wgs84_requested_is_blocked(self):
        raw = source([[[2.5, 48.5], [2.6, 48.5], [2.6, 48.6],
                       [2.5, 48.5]]])
        with self.assertRaisesRegex(ValueError, "WGS84"):
            audit(raw, url(outSR="2154"), 574)

    def test_wrong_objectid_is_blocked(self):
        raw = source([[[2.5, 48.5], [2.6, 48.5], [2.6, 48.6],
                       [2.5, 48.5]]], objectid=575)
        with self.assertRaisesRegex(ValueError, "identity"):
            audit(raw, url(), 574)

    def test_non_polygon_is_blocked(self):
        raw = source([2.5, 48.5], kind="Point")
        with self.assertRaisesRegex(ValueError, "polygon"):
            audit(raw, url(), 574)

    def test_truncated_source_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            audit(b'{"type":"FeatureCollection","features":[', url(), 574)


if __name__ == "__main__":
    unittest.main()
