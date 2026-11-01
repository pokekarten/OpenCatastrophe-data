# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only adversarial WFS model area coverage tests, no provider requests."""
import json
import unittest
from datetime import datetime, timezone

from research_runners.berlin_srgk_model_area_pilot_coverage_v0 import (
    BBOX, CONTROL_URL, PILOT_URL, CoverageBlocked, classify, parse_features, probe,
)


def polygon(x1, y1, x2, y2):
    return {"type": "Polygon", "coordinates": [[
        [x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1],
    ]]}


def document(geometry=None, *, matched=1, crs="EPSG:25833"):
    features = ([] if geometry is None else [
        {"type": "Feature", "id": "private-source-123",
         "properties": {"address": "PRIVATE must not emit"},
         "geometry": geometry}
    ])
    return {
        "type": "FeatureCollection", "numberReturned": len(features),
        "numberMatched": matched,
        "crs": {"type": "name", "properties": {"name": crs}},
        "features": features,
    }


def encoded(value):
    return json.dumps(value).encode()


def control():
    return encoded(document(polygon(390000, 5818000, 395000, 5821000)))


def hit():
    return encoded(document(polygon(391725, 5819975, 391740, 5819990)))


class FakeResponse:
    status = 200

    def __init__(self, url, data):
        self.url = url
        self.data = data
        self.headers = {"Content-Type": "application/json"}

    def geturl(self):
        return self.url

    def read(self, n):
        return self.data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class PilotCoverageTests(unittest.TestCase):
    def test_exact_provider_url_only_and_crs(self):
        self.assertIn("typeNames=ua_srgk%3Aa_modellgebiete", PILOT_URL)
        self.assertIn("EPSG%3A25833", PILOT_URL)
        self.assertIn("391700", PILOT_URL)
        self.assertIn("5819950", PILOT_URL)
        self.assertNotIn("bbox", CONTROL_URL)

    def test_real_intersection_requires_exact_positive_geometry(self):
        output = classify(control(), hit())
        self.assertEqual(output["pilot_model_area_coverage_status"],
                         "PILOT_INTERSECTS_ONE_OFFICIAL_MODEL_AREA")
        self.assertEqual(output["pilot_positive_intersection_area_m2_rounded"], 225)
        self.assertFalse(output["real_cat_model_input_approved"])
        self.assertNotIn("private-source-123", str(output))
        self.assertNotIn("PRIVATE", str(output))
        self.assertFalse(output["original_water_depth_values_or_flood_losses_retrieved"])

    def test_empty_pilot_response_unresolved_not_proven_no_hazard(self):
        output = classify(control(), encoded(document(None, matched=0)))
        self.assertEqual(output["pilot_model_area_coverage_status"],
                         "PILOT_COVERAGE_UNRESOLVED_EMPTY_SOURCE_RESPONSE")
        self.assertIsNone(output["pilot_positive_intersection_area_m2_rounded"])
        self.assertTrue(output["no_pilot_features_not_interpreted_as_proven_dry"])
        with self.assertRaisesRegex(CoverageBlocked, "positive-control"):
            classify(encoded(document(None, matched=0)), hit())

    def test_unrelated_returned_bbox_feature_is_rejected(self):
        unrelated = encoded(document(polygon(370000, 5790000, 371000, 5791000)))
        with self.assertRaisesRegex(CoverageBlocked, "no positive pilot"):
            classify(control(), unrelated)

    def test_number_returned_and_matched_must_agree(self):
        for key, val in (("numberReturned", 0), ("numberReturned", True),
                         ("numberMatched", 0), ("numberMatched", -1)):
            d = document(polygon(391720, 5819960, 391750, 5819995))
            d[key] = val
            with self.subTest(key=key, val=val), self.assertRaises(CoverageBlocked):
                parse_features(encoded(d), require_one=True)

    def test_rejects_wrong_geometry_crs_duplicates_and_nonfinite(self):
        d = document(polygon(391720, 5819960, 391750, 5819995), crs="EPSG:4326")
        with self.assertRaisesRegex(CoverageBlocked, "EPSG:25833"):
            parse_features(encoded(d), require_one=True)
        d = document(polygon(391720, 5819960, 391750, 5819995))
        d["features"][0]["geometry"]["type"] = "Point"
        with self.assertRaisesRegex(CoverageBlocked, "polygonal"):
            parse_features(encoded(d), require_one=True)
        bad = control().replace(b'"type": "FeatureCollection"',
                                b'"type": "FeatureCollection", "type": "Forged"')
        with self.assertRaisesRegex(CoverageBlocked, "duplicate"):
            parse_features(bad, require_one=True)
        with self.assertRaisesRegex(CoverageBlocked, "nonfinite"):
            parse_features(control().replace(b"391700", b"NaN"), require_one=True)
        with self.assertRaises(CoverageBlocked):
            parse_features(b"x" * 786433, require_one=True)

    def test_no_geometry_leak_in_live_style_metadata_receipt(self):
        calls = []
        def fake_open(req, timeout):
            calls.append((req.full_url, timeout))
            return FakeResponse(req.full_url, control() if len(calls) == 1 else hit())

        output = probe(opener=fake_open,
                       clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(calls, [(CONTROL_URL, 40), (PILOT_URL, 40)])
        self.assertEqual(output["exact_fixed_source_requests"], 2)
        self.assertFalse(output["source_raw_xml_geojson_persisted"])
        self.assertFalse(output["real_cat_model_input_approved"])
        self.assertNotIn("private-source-123", str(output))
        self.assertNotIn("PRIVATE", str(output))


if __name__ == "__main__":
    unittest.main()
