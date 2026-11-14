# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic, offline negative controls for original ComCat receipt semantics."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners import usgs_comcat_original_response_gate_v0 as gate


def invented_feature_collection():
    return {
        "type": "FeatureCollection",
        "metadata": {"count": 1},
        "features": [{
            "type": "Feature",
            "id": "invented000001",
            "properties": {
                "type": "earthquake", "time": 1700000000000,
                "updated": 1700000001000,
            },
            "geometry": {"type": "Point", "coordinates": [10.25, 45.75, 12.0]},
        }],
    }


def original_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


class OriginalComCatGateTests(unittest.TestCase):
    def verify(self, body=None, **updates):
        kwargs = {
            "exact_query": gate.EXACT_QUERY,
            "received_at_utc": "2026-11-13T15:20:00Z",
            "media_type": "application/json",
        }
        kwargs.update(updates)
        return gate.verify_original_response(
            original_bytes(invented_feature_collection()) if body is None else body,
            **kwargs,
        )

    def test_real_bytes_digest_not_hash_of_exported_row(self):
        body = original_bytes(invented_feature_collection())
        receipt = self.verify(body)
        self.assertEqual(receipt["original_body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(receipt["original_body_bytes"], len(body))
        self.assertEqual(receipt["event_count"], 1)
        for key in ("rights_approved", "source_model_admitted",
                    "historical_availability_proven", "live_provider_request_executed",
                    "event_id_published"):
            self.assertFalse(receipt[key])

    def test_request_media_and_timestamp_fail_closed(self):
        for changes in (
            {"exact_query": gate.EXACT_QUERY + "&eventid=invented"},
            {"media_type": "text/html"},
            {"received_at_utc": "2026-11-13"},
            {"received_at_utc": "2026-11-31T15:20:00Z"},
        ):
            with self.subTest(changes=changes), self.assertRaises(gate.ComCatOriginalBlocked):
                self.verify(**changes)

    def test_duplicate_keys_nonfinite_and_truncated_original_fail_closed(self):
        for body in (
            b'{"type":"FeatureCollection","type":"FeatureCollection"}',
            b'{"metadata":{"count":NaN},"features":[],"type":"FeatureCollection"}',
            b"<html>error</html>",
            b"",
            b"x" * (gate.MAX_ORIGINAL_BYTES + 1),
        ):
            with self.subTest(body=body[:40]), self.assertRaises(gate.ComCatOriginalBlocked):
                self.verify(body)

    def test_feature_cardinality_and_identity(self):
        for bad in ("count", "empty", "not_earthquake", "bad_id"):
            payload = invented_feature_collection()
            if bad == "count":
                payload["metadata"]["count"] = 2
            elif bad == "empty":
                payload["features"] = []
                payload["metadata"]["count"] = 0
            elif bad == "not_earthquake":
                payload["features"][0]["properties"]["type"] = "quarry blast"
            else:
                payload["features"][0]["id"] = "../../other"
            with self.subTest(bad=bad), self.assertRaises(gate.ComCatOriginalBlocked):
                self.verify(original_bytes(payload))

    def test_malformed_point_and_nonfinite_coordinates(self):
        for bad in ("lat", "depth", "nan", "length"):
            payload = invented_feature_collection()
            point = payload["features"][0]["geometry"]["coordinates"]
            if bad == "lat":
                point[1] = 91
            elif bad == "depth":
                point[2] = -999
            elif bad == "nan":
                point[0] = float("nan")
            else:
                point.pop()
            with self.subTest(bad=bad), self.assertRaises(gate.ComCatOriginalBlocked):
                self.verify(original_bytes(payload))

    def test_extremely_large_integer_is_blocked_without_overflow(self):
        payload = invented_feature_collection()
        payload["features"][0]["properties"]["time"] = 10 ** 400
        with self.assertRaises(gate.ComCatOriginalBlocked):
            self.verify(original_bytes(payload))

    def test_missing_origin_time_and_update(self):
        for field in ("time", "updated"):
            payload = invented_feature_collection()
            payload["features"][0]["properties"].pop(field)
            with self.subTest(field=field), self.assertRaises(gate.ComCatOriginalBlocked):
                self.verify(original_bytes(payload))

    def test_bytes_not_transformed_or_retained_by_receipt(self):
        body = original_bytes(invented_feature_collection())
        result = self.verify(body)
        self.assertNotIn("features", result)
        self.assertNotIn("invented000001", json.dumps(result))
        self.assertNotIn("geometry", result)
        self.assertEqual(self.verify(body), result)


if __name__ == "__main__":
    unittest.main()
