# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic fixture polygons and injected WFS response objects."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import unittest

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import (
    BBOX, LAYER, MAX_BYTES, MAX_COUNT, TIMEOUT, URL,
    BerlinBuildingSampleError, inspect_building_geojson, probe,
)

HAS_SPATIAL = (
    importlib.util.find_spec("shapely") is not None
    and importlib.util.find_spec("pyproj") is not None
)


def feature(*, x=391780, y=5820060, geometry_type="Polygon"):
    ring = [[x,y],[x+20,y],[x+20,y+20],[x,y+20],[x,y]]
    return {"type":"Feature","id":f"fictional-{x}-{y}",
            "properties":{"fixture":"not a real building"},
            "geometry":{"type":geometry_type,"coordinates":[ring]}}


def raw(doc: dict) -> bytes:
    return json.dumps(doc,sort_keys=True,separators=(",",":")).encode()


def fixture(*, n=1):
    return {"type":"FeatureCollection",
            "crs":{"type":"name","properties":{"name":"EPSG:25833"}},
            "numberReturned":n, "features":[feature(x=391780+22*i) for i in range(n)]}


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type":"application/json; charset=utf-8"}
    def geturl(self):
        return URL


class StrictWfsConfigurationTests(unittest.TestCase):
    def test_fixed_request_area_count_and_feature_type(self):
        self.assertEqual(LAYER, "alkis_gebaeude:gebaeude")
        self.assertEqual(BBOX, (391700,5819950,391900,5820150))
        self.assertEqual(MAX_COUNT, 5)
        self.assertIn("typeNames=alkis_gebaeude%3Agebaeude", URL)
        self.assertIn("outputFormat=application%2Fjson", URL)

    def test_bad_json_and_oversize_refused(self):
        for value in (b"", b"x"*(MAX_BYTES+1), b'{"foo":NaN}',
                      b'{"features":[],"features":[]}'):
            with self.subTest(value=value[:20]), self.assertRaises(BerlinBuildingSampleError):
                inspect_building_geojson(value)

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_exact_synthetic_building_polygon_and_injected_source(self):
        row, points = inspect_building_geojson(raw(fixture(n=2)))
        self.assertEqual(row["sampled_feature_count"], 2)
        self.assertEqual(row["sampled_distinct_polygon_count"], 2)
        self.assertTrue(row["sampled_duplicate_ids_or_geometries_rejected"])
        self.assertEqual(len(points), 2)
        self.assertGreater(points[0][0], 13.0)
        self.assertLess(points[0][0], 13.8)
        self.assertFalse(row["source_original_bytes_saved"] if "source_original_bytes_saved" in row else row["provider_feature_bytes_persisted"])
        def opener(req, timeout):
            self.assertEqual(req.full_url, URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, TIMEOUT)
            return Response(raw(fixture(n=2)))
        report=probe(opener=opener,clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(report["sampled_feature_count"],2)
        self.assertFalse(report["source_original_bytes_saved"])
        self.assertFalse(report["building_assets_or_insured_values_inferred"])
        self.assertIsNone(report["nuts2021_10m_join_region_counts"])
        self.assertEqual(len(report["response_sha256"]),64)

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_rejects_invalid_bounded_feature_count_geometry_and_wrong_crs(self):
        for count in (0,6):
            with self.subTest(n=count), self.assertRaises(BerlinBuildingSampleError):
                inspect_building_geojson(raw(fixture(n=count)))
        bad=fixture()
        bad["features"][0]["geometry"]["type"]="Point"
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))
        bad=fixture()
        bad["crs"]["properties"]["name"]="EPSG:4326"
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))
        bad=fixture()
        bad["features"][0]=feature(x=800000,y=4500000)
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))
        bad=fixture()
        bad["numberReturned"]=4
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_rejects_duplicate_ids_even_when_polygons_differ(self):
        doc = fixture(n=2)
        doc["features"][1]["id"] = doc["features"][0]["id"]
        with self.assertRaisesRegex(BerlinBuildingSampleError, "duplicate WFS building feature ID"):
            inspect_building_geojson(raw(doc))

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_rejects_geometrically_equal_polygons_even_with_distinct_ids(self):
        doc = fixture(n=2)
        doc["features"][1]["geometry"] = doc["features"][0]["geometry"]
        with self.assertRaisesRegex(BerlinBuildingSampleError, "duplicate physical building footprint"):
            inspect_building_geojson(raw(doc))

        # Reordering ring vertices is also an identical footprint; byte-
        # comparison cannot detect it but topological equality must.
        doc = fixture(n=2)
        coords = doc["features"][0]["geometry"]["coordinates"][0]
        doc["features"][1]["geometry"]["coordinates"][0] = coords[2:-1] + coords[:3]
        with self.assertRaisesRegex(BerlinBuildingSampleError, "duplicate physical building footprint"):
            inspect_building_geojson(raw(doc))

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_rejects_malformed_optional_feature_id_without_guessing(self):
        for bad_id in ("", "  ", True, [], {}):
            with self.subTest(id=bad_id):
                doc = fixture()
                doc["features"][0]["id"] = bad_id
                with self.assertRaisesRegex(BerlinBuildingSampleError, "invalid WFS building feature ID"):
                    inspect_building_geojson(raw(doc))
        # GeoJSON Feature.id is optional. Source-provided unique geometry
        # remains the fallback; no ID or guessed building identity is output.
        doc = fixture()
        doc["features"][0].pop("id")
        stats, points = inspect_building_geojson(raw(doc))
        self.assertEqual(stats["sampled_distinct_polygon_count"], 1)
        self.assertTrue(stats["sampled_duplicate_ids_or_geometries_rejected"])
        self.assertEqual(len(points), 1)

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_malformed_polygon_and_unrelated_bbox_fail(self):
        bad=fixture()
        bad["features"][0]["geometry"]["coordinates"]=[[
            [391780,5820060],[391800,5820080],[391800,5820060],
            [391780,5820080],[391780,5820060],
        ]]
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))
        bad=fixture()
        bad["features"][0]=feature(x=393000)
        with self.assertRaises(BerlinBuildingSampleError):
            inspect_building_geojson(raw(bad))

    @unittest.skipUnless(HAS_SPATIAL,"Pinned Shapely/Pyproj needed")
    def test_live_receipt_does_not_accept_redirect_or_html(self):
        class Bad(Response):
            def geturl(self): return "https://example.invalid/other"
        with self.assertRaises(BerlinBuildingSampleError):
            probe(opener=lambda req,t:Bad(raw(fixture())))
        class Html(Response):
            headers={"Content-Type":"text/html"}
        with self.assertRaises(BerlinBuildingSampleError):
            probe(opener=lambda req,t:Html(b"hello"))


if __name__=="__main__":
    unittest.main()
