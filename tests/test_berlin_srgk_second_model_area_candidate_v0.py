# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only second Berlin SRGK study pilot candidate negative QA."""
import json
import unittest
from datetime import datetime, timezone

from research_runners.berlin_srgk_second_model_area_candidate_v0 import (
    CONTROL_URL, CoverageBlocked, choose_candidate, probe,
)


def source_polygon(left=385000, bottom=5825000, right=387000, top=5827000,
                   crs="EPSG:25833"):
    return json.dumps({
        "type": "FeatureCollection",
        "numberReturned": 1, "numberMatched": 8,
        "crs": {"type": "name", "properties": {"name": crs}},
        "features": [{
            "type": "Feature",
            "id": "private-source-feature-id",
            "properties": {"address": "SHOULD NEVER BE LOGGED"},
            "geometry": {"type": "Polygon", "coordinates": [[
                [left,bottom],[right,bottom],[right,top],[left,top],[left,bottom]
            ]]},
        }],
    }, sort_keys=True).encode()


class FakeResponse:
    status = 200

    def __init__(self, url, raw, media="application/json"):
        self.url, self.body = url, raw
        self.headers = {"Content-Type": media}

    def geturl(self):
        return self.url

    def read(self, n):
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class SecondModelAreaCandidateTests(unittest.TestCase):
    def test_one_public_polygon_derives_nonoverlapping_research_box(self):
        out = choose_candidate(source_polygon())
        self.assertEqual(out["second_pilot_bbox_epsg25833"], [385900,5825900,386100,5826100])
        self.assertEqual(out["second_pilot_size_m"], [200,200])
        self.assertEqual(out["positive_original_source_polygon_overlap_area_m2"], 40000.0)
        self.assertTrue(out["original_bld4_pilot_is_separate"])
        for field in ("provider_fes_filter_for_second_pilot_verified",
                      "detailed_depth_tiff_pixels_or_units_verified",
                      "per_building_depth_or_insurer_loss_computed",
                      "cat_model_input_approved",
                      "original_source_features_ids_or_geometry_persisted"):
            self.assertFalse(out[field])
        self.assertNotIn("SHOULD NEVER BE LOGGED", str(out))
        self.assertNotIn("private-source-feature-id", str(out))

    def test_fixed_live_source_exactly_once_and_no_ids(self):
        seen = []
        def fake(req, timeout):
            seen.append((req.full_url, timeout))
            return FakeResponse(req.full_url, source_polygon())
        out = probe(opener=fake, clock=lambda: datetime(2026,11,2,tzinfo=timezone.utc))
        self.assertEqual(seen, [(CONTROL_URL,40)])
        self.assertEqual(out["one_exact_original_source_get"], True)
        self.assertEqual(len(out["original_source_response_sha256"]), 64)
        self.assertFalse(out["cat_model_input_approved"])
        self.assertNotIn("private-source-feature-id", str(out))
        self.assertNotIn("SHOULD NEVER BE LOGGED", str(out))

    def test_outside_berlin_untrustworthy_projection_rejected(self):
        for a,b,c,d in ((100000,5000000,102000,5002000),
                        (400000,5876000,401000,5877000)):
            with self.subTest(box=(a,b,c,d)), self.assertRaises(CoverageBlocked):
                choose_candidate(source_polygon(a,b,c,d))
        with self.assertRaisesRegex(CoverageBlocked, "EPSG:25833"):
            choose_candidate(source_polygon(crs="EPSG:4326"))

    def test_new_pilot_cannot_overlap_old_bld4(self):
        with self.assertRaisesRegex(CoverageBlocked, "old BLD4"):
            choose_candidate(source_polygon(391700,5819950,391900,5820150))

    def test_missing_or_duplicate_original_feature_rejected(self):
        one = json.loads(source_polygon())
        one["features"] = []
        one["numberReturned"] = 0
        with self.assertRaises(CoverageBlocked):
            choose_candidate(json.dumps(one).encode())
        one = json.loads(source_polygon())
        one["features"] *= 2
        one["numberReturned"] = 2
        with self.assertRaises(CoverageBlocked):
            choose_candidate(json.dumps(one).encode())
        raw = source_polygon().replace(b'"numberReturned": 1',
                                     b'"numberReturned": 1, "numberReturned": 0')
        with self.assertRaisesRegex(CoverageBlocked, "duplicate"):
            choose_candidate(raw)

    def test_wrong_media_and_oversized_body_rejected(self):
        def wrong(req, timeout):
            return FakeResponse(req.full_url, source_polygon(), "text/html")
        with self.assertRaisesRegex(CoverageBlocked, "GeoJSON"):
            probe(opener=wrong)
        def large(req, timeout):
            return FakeResponse(req.full_url, b"x"*786433)
        with self.assertRaises(CoverageBlocked):
            probe(opener=large)

    def test_too_small_or_nonpolygon_geometry_rejected(self):
        with self.assertRaises(CoverageBlocked):
            choose_candidate(source_polygon(385000,5825000,385001,5825001))
        one=json.loads(source_polygon())
        one["features"][0]["geometry"] = {"type":"Point","coordinates":[385000,5825000]}
        with self.assertRaises(CoverageBlocked):
            choose_candidate(json.dumps(one).encode())


if __name__ == "__main__":
    unittest.main()
