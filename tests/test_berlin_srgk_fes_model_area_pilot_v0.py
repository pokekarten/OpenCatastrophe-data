# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic exact FES2 geometry source acceptance and negative gates."""
import io
import json
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timezone

from research_runners.berlin_srgk_fes_model_area_pilot_v0 import (
    CONTROL_URL, FILTER, FILTER_URL, CoverageBlocked, probe,
)


def document(x1, y1, x2, y2):
    return json.dumps({
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:25833"}},
        "numberReturned": 1,
        "numberMatched": 1,
        "features": [{
            "type": "Feature", "id": "private-source-id",
            "properties": {"address": "NEVER PUBLISH"},
            "geometry": {"type": "Polygon", "coordinates": [[
                [x1, y1], [x2, y1], [x2, y2],
                [x1, y2], [x1, y1],
            ]]},
        }],
    }).encode()


class Response:
    status = 200

    def __init__(self, url, body, media="application/json"):
        self.url, self.body, self.headers = url, body, {"Content-Type": media}

    def geturl(self):
        return self.url

    def read(self, n):
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class FesSourceTests(unittest.TestCase):
    def test_exact_reviewed_geometry_field_and_box(self):
        self.assertIn("<fes:ValueReference>geom</fes:ValueReference>", FILTER)
        self.assertIn("391700 5819950", FILTER)
        self.assertIn("391900 5820150", FILTER)
        self.assertIn("http://www.opengis.net/fes/2.0", FILTER)
        self.assertIn("filter=", FILTER_URL)
        self.assertNotIn("filter=", CONTROL_URL)

    def test_positive_result_is_only_model_area_coverage_not_insurer_loss(self):
        responses = [
            document(390000, 5818000, 390500, 5818500),
            document(391720, 5819970, 391740, 5819990),
        ]
        calls = []
        def fake(req, timeout):
            calls.append(req.full_url)
            return Response(req.full_url, responses[len(calls)-1])
        result = probe(opener=fake, clock=lambda: datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(calls, [CONTROL_URL, FILTER_URL])
        self.assertEqual(result["pilot_model_area_coverage_status"],
                         "PILOT_INTERSECTS_ONE_OFFICIAL_MODEL_AREA")
        self.assertFalse(result["insured_cat_model_admitted"])
        self.assertFalse(result["real_cat_model_input_approved"])
        self.assertFalse(result["physical_water_depth_units_verified"])
        self.assertNotIn("private-source-id", str(result))
        self.assertNotIn("NEVER PUBLISH", str(result))

    def test_unrelated_fes_feature_blocks_and_hashes_only(self):
        unrelated = document(390000, 5818000, 390500, 5818500)
        calls = []
        def fake(req, timeout):
            calls.append(req.full_url)
            return Response(req.full_url, unrelated)
        log = io.StringIO()
        with redirect_stderr(log), self.assertRaises(CoverageBlocked):
            probe(opener=fake)
        self.assertEqual(calls, [CONTROL_URL, FILTER_URL])
        metadata = json.loads(log.getvalue())
        self.assertEqual(metadata["fes_source_coverage_status"],
                         "BLOCKED_UNVERIFIED_FILTER_RESULT")
        self.assertTrue(metadata["original_control_and_fes_bodies_identical"])
        self.assertFalse(metadata["insured_cat_model_admitted"])
        self.assertNotIn("private-source-id", log.getvalue())

    def test_wrong_source_media_blocks_even_if_body_is_json(self):
        def fake(req, timeout):
            return Response(req.full_url,
                            document(391720, 5819970, 391740, 5819990),
                            "text/plain")
        with self.assertRaisesRegex(CoverageBlocked, "GeoJSON"):
            probe(opener=fake)

    def test_empty_filtered_response_remains_unresolved(self):
        first = document(390000,5818000,390500,5818500)
        empty = json.dumps({
            "type":"FeatureCollection", "features":[],
            "numberReturned":0, "numberMatched":0
        }).encode()
        calls = []
        def fake(req, timeout):
            calls.append(req.full_url)
            return Response(req.full_url, first if len(calls)==1 else empty)
        result = probe(opener=fake)
        self.assertEqual(result["pilot_model_area_coverage_status"],
                         "PILOT_COVERAGE_UNRESOLVED_EMPTY_SOURCE_RESPONSE")
        self.assertFalse(result["pilot_model_area_feature_returned"])
        self.assertFalse(result["real_cat_model_input_approved"])

    def test_oversized_or_invalid_source_response_stays_blocked(self):
        def fake(req, timeout):
            return Response(req.full_url, b"z"*786433)
        with self.assertRaisesRegex(CoverageBlocked, "oversized"):
            probe(opener=fake)


if __name__ == "__main__":
    unittest.main()
