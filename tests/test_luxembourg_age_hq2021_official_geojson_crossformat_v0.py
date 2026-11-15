# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original publisher GeoJSON cross-format audit regressions."""
from __future__ import annotations

import json
import unittest

from research_runners.luxembourg_age_hq2021_official_geojson_crossformat_v0 import (
    SOURCES, OriginalGeoJSONError, profile_original_geojson, _reject_nonfinite_constant,
)


def fixture():
    outer = [[5.9, 49.7], [5.9, 49.8], [6.0, 49.8],
             [6.0, 49.7], [5.9, 49.7]]
    inner = [[5.94, 49.74], [5.96, 49.74], [5.96, 49.76],
             [5.94, 49.76], [5.94, 49.74]]
    return {"type":"FeatureCollection",
            "features":[{"type":"Feature", "id": "private-do-not-export",
                         "properties": {"OBJECTID": 99, "Shape_Area": 1},
                         "geometry":{"type":"Polygon", "coordinates":[outer,inner]}}]}


class PublisherGeoJSONFormatTests(unittest.TestCase):
    def test_publisher_geometry_groups_and_no_identifying_values(self):
        f=fixture()
        for scenario in SOURCES:
            with self.subTest(scenario=scenario):
                r=profile_original_geojson(f,scenario=scenario)
                self.assertEqual(r["source_feature_count"],1)
                self.assertEqual(r["original_publisher_polygon_group_count"],1)
                self.assertEqual(r["original_publisher_hole_ring_count_from_grouping"],1)
                self.assertEqual(r["original_publisher_ring_parts"],2)
                self.assertEqual(r["original_publisher_point_pairs"],10)
                self.assertEqual(r["closed_publisher_rings"],2)
                self.assertEqual(r["source_coordinate_domain_hypothesis"],
                                 "looks_luxembourg_longitude_latitude")
                self.assertFalse(r["ring_count_matches_original_publisher_shapefile"])
                self.assertFalse(r["insurer_CAT_model_input_admitted"])
                self.assertFalse(r["GeoJSON_and_SHP_topological_sets_proven_equal"])
                self.assertTrue(r["RFC7946_WGS84_longitude_latitude_domain_plausible"])
                self.assertFalse(r["requires_explicit_projected_CRS_interpretation_before_spatial_use"])
                self.assertNotIn("private-do-not-export",json.dumps(r))
                self.assertNotIn("99",json.dumps(r))

    def test_source_projected_coordinates_warn_against_implicit_wgs84(self):
        f = fixture()
        f["features"][0]["geometry"]["coordinates"] = [
            [[50000., 80000.], [50000., 81000.], [51000., 81000.],
             [51000., 80000.], [50000., 80000.]]
        ]
        r = profile_original_geojson(f, scenario="hq100")
        self.assertFalse(r["RFC7946_WGS84_longitude_latitude_domain_plausible"])
        self.assertTrue(r["requires_explicit_projected_CRS_interpretation_before_spatial_use"])
        self.assertFalse(r["WGS84_to_LUREF_transform_ground_verified"])

    def test_multiple_polygons_counted_without_exterior_hole_invention(self):
        f=fixture()
        coords=f["features"][0]["geometry"]["coordinates"]
        f["features"][0]["geometry"]={"type":"MultiPolygon","coordinates":[coords,[coords[0]]]}
        r=profile_original_geojson(f,scenario="hq100")
        self.assertEqual(r["original_publisher_polygon_group_count"],2)
        self.assertEqual(r["original_publisher_ring_parts"],3)
        self.assertEqual(r["original_publisher_hole_ring_count_from_grouping"],1)
        self.assertEqual(r["original_publisher_point_pairs"],15)
        self.assertEqual(r["geometry_type_counts"]["MultiPolygon"],1)

    def test_open_rings_are_not_silently_closed(self):
        f=fixture()
        f["features"][0]["geometry"]["coordinates"][0][-1]=[6.1,49.7]
        r=profile_original_geojson(f,scenario="hq100")
        self.assertEqual(r["open_publisher_rings"],1)
        self.assertFalse(r["GeoJSON_and_SHP_topological_sets_proven_equal"])

    def test_reject_unknown_geometry_infinite_and_malformed_root(self):
        f=fixture()
        for variant in ("LineString","Point","GeometryCollection"):
            f=fixture()
            f["features"][0]["geometry"]["type"]=variant
            with self.subTest(variant=variant),self.assertRaises(OriginalGeoJSONError):
                profile_original_geojson(f,scenario="hq10")
        f=fixture()
        f["features"][0]["geometry"]["coordinates"][0][2]=[float("nan"),49.8]
        with self.assertRaises(OriginalGeoJSONError):
            profile_original_geojson(f,scenario="hqext")
        for scen in ("hq7","",None):
            with self.assertRaises(OriginalGeoJSONError):
                profile_original_geojson(fixture(),scenario=scen)
        with self.assertRaises(OriginalGeoJSONError):
            profile_original_geojson({"type":"FeatureCollection","features":[]},scenario="hq100")
        with self.assertRaises(OriginalGeoJSONError):
            json.loads('{"x":NaN}',parse_constant=_reject_nonfinite_constant)


if __name__ == "__main__":
    unittest.main()
