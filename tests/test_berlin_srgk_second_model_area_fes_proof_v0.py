# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic second Berlin detailed model-area FES proof safety gates."""
import io
import json
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timezone

from research_runners.berlin_srgk_second_model_area_fes_proof_v0 import (
    CONTROL_URL, FILTER_URL, FILTER, SECOND_BBOX,
    CoverageBlocked, evaluate, probe,
)


def polygon(a,b,c,d):
    return {"type":"Polygon","coordinates":[[
        [a,b],[c,b],[c,d],[a,d],[a,b]
    ]]}


def body(geom):
    features=[] if geom is None else [{
        "type":"Feature",
        "id":"SOURCE_ID_DO_NOT_PUBLISH",
        "properties":{"address":"PRIVATE ADDRESS"},
        "geometry":geom,
    }]
    return json.dumps({
        "type":"FeatureCollection", "numberReturned":len(features),
        "numberMatched":8 if geom is not None else 0,
        "crs":{"type":"name","properties":{"name":"EPSG:25833"}},
        "features":features,
    }).encode()


def control():
    return body(polygon(390000,5816000,393920,5817880))


def filtered():
    return body(polygon(391820,5816820,392080,5817080))


class Response:
    status=200
    def __init__(self,url,raw,media="application/json"):
        self.url=url
        self.raw=raw
        self.headers={"Content-Type":media}
    def geturl(self):
        return self.url
    def read(self,n):
        return self.raw[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class SourceFesProofTests(unittest.TestCase):
    def test_filter_exact_geometry_and_frozen_new_pilot(self):
        self.assertEqual(SECOND_BBOX,(391860,5816840,392060,5817040))
        self.assertIn("<fes:ValueReference>geom</fes:ValueReference>",FILTER)
        self.assertIn("391860 5816840",FILTER)
        self.assertIn("392060 5817040",FILTER)
        self.assertNotIn("filter=",CONTROL_URL)
        self.assertIn("filter=",FILTER_URL)

    def test_two_source_independent_intersections_not_raster_or_cat(self):
        out=evaluate(control(), filtered())
        self.assertEqual(out["provider_filter_acceptance_status"],
                         "TWO_INDEPENDENT_SOURCE_QUERIES_VERIFY_MODEL_AREA_OVERLAP")
        self.assertEqual(out["official_filtered_geometry_intersection_m2"],40000.0)
        self.assertTrue(out["provider_spatial_filter_independently_confirmed"])
        self.assertFalse(out["cat_model_input_approved"])
        self.assertFalse(out["water_depth_units_or_pixels_verified"])
        self.assertNotIn("PRIVATE ADDRESS",str(out))
        self.assertNotIn("SOURCE_ID_DO_NOT_PUBLISH",str(out))

    def test_empty_filter_stays_unresolved_without_dryness_claim(self):
        out=evaluate(control(),body(None))
        self.assertEqual(out["provider_filter_acceptance_status"],
                         "FES_EMPTY_SECOND_PILOT_COVERAGE_UNRESOLVED")
        self.assertIsNone(out["official_filtered_geometry_intersection_m2"])
        self.assertFalse(out["provider_spatial_filter_independently_confirmed"])
        self.assertFalse(out["cat_model_input_approved"])

    def test_filtered_unrelated_polygon_fails_closed(self):
        with self.assertRaisesRegex(CoverageBlocked,"positive intersection"):
            evaluate(control(),body(polygon(370000,5800000,371000,5801000)))

    def test_control_source_anchor_revision_must_be_rechecked(self):
        with self.assertRaisesRegex(CoverageBlocked,"no longer anchors"):
            evaluate(body(polygon(385000,5825000,387000,5827000)),filtered())

    def test_one_fixed_control_and_one_fixed_fes_provider_request(self):
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,timeout))
            return Response(req.full_url, control() if len(calls)==1 else filtered())
        out=probe(opener=fake,clock=lambda:datetime(2026,11,2,tzinfo=timezone.utc))
        self.assertEqual(calls,[(CONTROL_URL,40),(FILTER_URL,40)])
        self.assertTrue(out["provider_spatial_filter_independently_confirmed"])
        self.assertEqual(len(out["original_fes_response_sha256"]),64)
        self.assertFalse(out["cat_model_input_approved"])
        self.assertNotIn("PRIVATE ADDRESS",str(out))

    def test_source_mismatch_logs_hashes_not_features(self):
        def fake(req,timeout):
            return Response(req.full_url,body(polygon(370000,5800000,371000,5801000)))
        stream=io.StringIO()
        with redirect_stderr(stream), self.assertRaises(CoverageBlocked):
            probe(opener=fake)
        d=json.loads(stream.getvalue().strip())
        self.assertEqual(d["status"],"BLOCKED_UNVERIFIED_SECOND_PILOT_SOURCE_FILTER")
        self.assertFalse(d["cat_model_input_approved"])
        self.assertNotIn("PRIVATE ADDRESS",stream.getvalue())
        self.assertNotIn("SOURCE_ID_DO_NOT_PUBLISH",stream.getvalue())

    def test_bad_media_and_duplicate_key_rejected(self):
        def wrong(req,timeout):
            return Response(req.full_url,control(),"text/html")
        with self.assertRaisesRegex(CoverageBlocked,"GeoJSON"):
            probe(opener=wrong)
        corrupted=control().replace(b'"numberReturned": 1',
            b'"numberReturned": 1, "numberReturned": 2')
        with self.assertRaisesRegex(CoverageBlocked,"duplicate"):
            evaluate(corrupted,filtered())


if __name__=="__main__":
    unittest.main()
