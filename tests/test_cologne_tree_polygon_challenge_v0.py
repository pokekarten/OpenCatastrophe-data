# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic, offline independent Cologne tree-to-KGG polygon negative tests."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

RUNNERS = Path(__file__).resolve().parents[1] / "research_runners"
sys.path.insert(0, str(RUNNERS))
MODULE = RUNNERS / "cologne_tree_polygon_challenge_v0.py"
spec = importlib.util.spec_from_file_location("cologne_tree_polygon_challenge_v0", MODULE)
assert spec and spec.loader
challenge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(challenge)

POINTS = (
    (350000.0, 5620000.0),
    (353000.0, 5635000.0),
    (360000.0, 5640000.0),
    (370000.0, 5660000.0),
    (365000.0, 5630000.0),
)
OFFICIAL = ("Synthetic A", "Synthetic B", "Synthetic C", "Synthetic D", "Synthetic E")


def sample_cases():
    return [
        {
            "coords_internal": xy,
            "tree_id_sha256": ("%064x" % (i + 1)),
            "source_crs_declaration": "not_declared",
            "response_sha256": ("%064x" % (i + 11)),
            "source_stadtteil_internal": "" if i == 0 else OFFICIAL[i],
        }
        for i, xy in enumerate(POINTS)
    ]


def fake_transform(x, y):
    """Artificial mock only, never a real EPSG projection."""
    return 6.9 + (x - 350000.0) / 150000.0, 50.86 + (y - 5600000.0) / 300000.0


def official_lookup(lon, lat):
    if (lon, lat) == challenge.NEGATIVE_POINT:
        return None
    for i, (x, y) in enumerate(POINTS):
        p = fake_transform(x, y)
        if abs(lon - p[0]) < 0.000001 and abs(lat - p[1]) < 0.000001:
            return OFFICIAL[i]
    return None


def make_reply(names):
    return json.dumps({
        "features": [
            {"attributes": {"name": name, "nummer": "%03d" % (i + 1)}}
            for i, name in enumerate(names)
        ],
        "fields": [],
    }).encode("utf-8")


class CologneTreePolygonTests(unittest.TestCase):
    def test_source_bound_point_query_no_raw_polygon(self):
        url = challenge.query_url(6.96, 50.95)
        self.assertIn("/basiskarten/kgg/MapServer/3/query?", url)
        self.assertIn("geometry=6.96000000,50.95000000", url)
        self.assertIn("inSR=4326", url)
        self.assertIn("esriSpatialRelIntersects", url)
        self.assertIn("returnGeometry=false", url)
        self.assertIn("outFields=name,nummer", url)

    def test_only_city_points_and_fixed_negative_control(self):
        self.assertIn("13.40500000,52.52000000", challenge.query_url(*challenge.NEGATIVE_POINT))
        for coords in ((13.3, 52.0), (7.0, float("nan")), (300000.0, 5640000.0)):
            with self.subTest(coords=coords), self.assertRaises(challenge.PolygonChallengeError):
                challenge.query_url(*coords)

    def test_original_response_contract_without_geometry(self):
        self.assertEqual(challenge.parse_point_reply(make_reply(["Suelz"])), "Suelz")
        self.assertIsNone(challenge.parse_point_reply(make_reply([])))
        self.assertEqual(challenge.parse_point_reply(make_reply(["Merheim"])), "Merheim")

    def test_wrong_response_shapes_fail_closed(self):
        cases = [
            b'',
            b'<xml/>',
            json.dumps({"error": {"code": 404}}).encode("utf-8"),
            make_reply(["A", "B"]),
            json.dumps({"features": [{"geometry": {"x": 7}, "attributes":
                         {"name": "A", "nummer": "123"}}]}).encode("utf-8"),
            json.dumps({"features": [{"attributes": {"name": "", "nummer": "123"}}]}).encode("utf-8"),
            json.dumps({"features": [{"attributes": {"name": "A", "nummer": 123}}]}).encode("utf-8"),
        ]
        for data in cases:
            with self.subTest(length=len(data)), self.assertRaises(challenge.PolygonChallengeError):
                challenge.parse_point_reply(data)

    def test_all_five_inside_and_four_stadtteil_labels_match(self):
        receipt = challenge.review_samples(sample_cases(), fake_transform, official_lookup)
        self.assertEqual(receipt["independent_polygon_hits"], 5)
        self.assertEqual(receipt["source_stadtteil_labels_corroborated"], 4)
        self.assertEqual(receipt["source_stadtteil_labels_missing"], 1)
        self.assertEqual(receipt["independent_distinct_stadtteil_count"], 5)
        self.assertTrue(receipt["outside_city_negative_control_returns_zero"])
        self.assertFalse(receipt["model_admitted"])
        self.assertFalse(receipt["scientific_validation_complete"])
        self.assertFalse(receipt["external_data_bytes_persisted"])
        self.assertNotIn("Synthetic", str(receipt))
        self.assertNotIn("coords_internal", str(receipt))

    def test_mismatching_source_area_is_blocked(self):
        arr = sample_cases()
        arr[1]["source_stadtteil_internal"] = "different name"
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(arr, fake_transform, official_lookup)

    def test_point_outside_official_polygon_is_blocked(self):
        def none_for_all(lon, lat):
            return None
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(sample_cases(), fake_transform, none_for_all)

    def test_city_negative_control_must_remain_negative(self):
        def false_positive(lon, lat):
            if (lon, lat) == challenge.NEGATIVE_POINT:
                return "Berlin"
            return official_lookup(lon, lat)
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(sample_cases(), fake_transform, false_positive)

    def test_three_or_more_independent_areas_required(self):
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(sample_cases(), fake_transform, lambda x, y: "one district")

    def test_missing_source_area_not_auto_imputed(self):
        arr = sample_cases()
        for x in arr:
            x["source_stadtteil_internal"] = ""
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(arr, fake_transform, official_lookup)

    def test_wrong_transform_or_original_snapshot_rejected(self):
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(sample_cases(), lambda x, y: (9.0, 52.0), official_lookup)
        with self.assertRaises(challenge.PolygonChallengeError):
            challenge.review_samples(sample_cases()[:3], fake_transform, official_lookup)

    def test_replay_source_stadtteil_only_in_private_memory(self):
        data = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature",
                          "geometry": {"type": "Point", "coordinates": [355000, 5640000]},
                          "properties": {"Baumnummer": "synthetic-only",
                                         "Stadtteil": "TestDistrict"}}],
        }
        info = challenge.tree.parse_source_sample(json.dumps(data).encode("utf-8"))
        self.assertEqual(info["source_stadtteil_internal"], "TestDistrict")
        self.assertNotIn("synthetic-only", str(info))


if __name__ == "__main__":
    unittest.main()
