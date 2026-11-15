# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only Berlin ALKIS↔2022 height feature geometries and role guards."""
from __future__ import annotations

from datetime import datetime, timezone
import copy
import io
import importlib.util
import unittest

from research_runners.berlin_lod2_alkis_five_polygon_comparison_v0 import (
    HEIGHT_URL, ALKIS_URL, MIN_IOU, HeightPairError, _parse_height,
    compare_samples, probe,
)
from tests.test_berlin_alkis_gebaeude_five_feature_join_v0 import raw, fixture

HAS_SPATIAL=importlib.util.find_spec("shapely") is not None and importlib.util.find_spec("pyproj") is not None


def samples():
    a=fixture(n=2)
    h=copy.deepcopy(a)
    for i, f in enumerate(h["features"]):
        f["properties"]={"role_txt":"Gebäude","hoehe":15.0+i*4,
                         "dachart":"Fiktiver Dachcode","geschosse":2+i}
        f["id"]=f"fictitious-height-{i}"
    return a,h


class Reply(io.BytesIO):
    status=200
    headers={"Content-Type":"application/json"}
    def __init__(self,b,url):
        super().__init__(b);self.url=url
    def geturl(self):return self.url


class HeightPairSyntheticTests(unittest.TestCase):
    def test_official_layer_and_fixed_geometry_request(self):
        self.assertEqual(MIN_IOU,0.95)
        self.assertIn("ua_gebaeudehoehen%3Agebaeudehoehen",HEIGHT_URL)
        self.assertIn("count=5",HEIGHT_URL)
        self.assertIn("EPSG%3A25833",HEIGHT_URL)
        self.assertNotEqual(ALKIS_URL,HEIGHT_URL)

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_strict_two_independent_real_source_geometry_namespaces(self):
        a,h=samples()
        result=compare_samples(raw(a),raw(h))
        self.assertEqual(result["geometry_matches_iou_at_least_0_95"],2)
        self.assertEqual(result["sample_height_polygon_count"],2)
        self.assertEqual(result["height_numeric_positive_count"],2)
        self.assertEqual(result["height_non_null_field_counts"]["hoehe"],2)
        self.assertEqual(result["height_source_role_counts"]["building"],2)
        self.assertFalse(result["source_ids_or_feature_values_exported"])
        self.assertNotIn("Fiktiver Dachcode",str(result))
        self.assertNotIn("fictitious-height",str(result))

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_independent_source_does_not_infer_match_by_label(self):
        a,h=samples()
        # Just shift source polygons: same role & heights, no spatial truth.
        for f in h["features"]:
            for ring in f["geometry"]["coordinates"]:
                for xy in ring:xy[0]+=50
        result=compare_samples(raw(a),raw(h))
        self.assertEqual(result["geometry_matches_iou_at_least_0_95"],0)
        self.assertEqual(result["height_numeric_positive_count"],2)
        self.assertFalse(result["full_borough_count_or_completeness_inferred"])

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_3m_possible_imputation_not_measured(self):
        a,h=samples()
        h["features"][0]["properties"]["hoehe"]=3.0
        h["features"][1]["properties"]["role_txt"]="Bauteil"
        r=compare_samples(raw(a),raw(h))
        self.assertEqual(r["height_exact_3m_possible_placeholder_count"],1)
        self.assertEqual(r["height_source_role_counts"]["building_part"],1)
        self.assertTrue(r["three_metre_value_not_claimed_measured"])

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_duplicate_bad_crs_and_nonpolygon_rejected(self):
        a,h=samples()
        h["features"][1]["id"]=h["features"][0]["id"]
        with self.assertRaises(HeightPairError):compare_samples(raw(a),raw(h))
        a,h=samples()
        h["crs"]["properties"]["name"]="EPSG:4326"
        with self.assertRaises(HeightPairError):compare_samples(raw(a),raw(h))
        a,h=samples()
        h["features"][0]["geometry"]["type"]="Point"
        with self.assertRaises(HeightPairError):compare_samples(raw(a),raw(h))
        a,h=samples()
        h["features"][0]["properties"]["hoehe"]={"secret":"nested"}
        with self.assertRaises(HeightPairError):compare_samples(raw(a),raw(h))

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_missing_or_ambiguous_geojson_crs_never_matches_across_sources(self):
        a,h=samples()
        # GeoJSON without a CRS must not be silently reinterpreted as
        # projected EPSG:25833 from the WFS request's srsName parameter.
        h.pop("crs")
        with self.assertRaisesRegex(HeightPairError,"explicitly declare EPSG:25833"):
            compare_samples(raw(a),raw(h))
        a,h=samples()
        a.pop("crs")
        with self.assertRaisesRegex(HeightPairError,"explicitly declare EPSG:25833"):
            compare_samples(raw(a),raw(h))
        a,h=samples()
        h["crs"] = {"type":"name","properties":{"name":"EPSG:4326"}}
        with self.assertRaisesRegex(HeightPairError,"explicitly declare EPSG:25833"):
            compare_samples(raw(a),raw(h))
        a,h=samples()
        h["crs"] = {"type":"name","properties":{}}
        with self.assertRaisesRegex(HeightPairError,"explicitly declare EPSG:25833"):
            compare_samples(raw(a),raw(h))

    @unittest.skipUnless(HAS_SPATIAL,"Shapely and pyproj required")
    def test_exactly_two_fixed_requests_and_no_persistence(self):
        a,h=samples()
        calls=[]
        def opener(req,timeout):
            calls.append(req.full_url)
            if req.full_url==ALKIS_URL:return Reply(raw(a),ALKIS_URL)
            if req.full_url==HEIGHT_URL:return Reply(raw(h),HEIGHT_URL)
            raise AssertionError("unreviewed source")
        r=probe(opener=opener,clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(calls,[ALKIS_URL,HEIGHT_URL])
        self.assertEqual(r["geometry_matches_iou_at_least_0_95"],2)
        self.assertEqual(r["exact_original_source_requests"],2)
        self.assertFalse(r["CAT_or_insurer_database_modified"])
        self.assertFalse(r["raw_provider_features_persisted"])
        self.assertEqual(len(r["alkis_response_sha256"]),64)
        self.assertEqual(len(r["height_response_sha256"]),64)


if __name__=="__main__":
    unittest.main()
