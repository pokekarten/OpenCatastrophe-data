# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests for exact Ontario ArcGIS metadata identity and fail-closed gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research_runners.ontario_historical_events_metadata_receipt_v0 import (
    Blocked, EXPECTED_FIELDS, inspect, main, verify,
)


def fake_layer(**overrides):
    obj = {
        "id": 20,
        "name": "Emergency Management Historical Event",
        "type": "Feature Layer",
        "geometryType": "esriGeometryMultipoint",
        "sourceSpatialReference": {"wkid": 4269, "latestWkid": 4269},
        "displayField": "EVENT_TYPE",
        "fields": [{"name": k, "type": v} for k, v in EXPECTED_FIELDS.items()],
        "copyrightText": "https://www.ontario.ca/page/open-government-licence-ontario",
    }
    obj.update(overrides)
    return json.dumps(obj, sort_keys=True).encode("utf-8")


class OntarioMetadataTests(unittest.TestCase):
    def test_original_schema_metadata_only(self):
        x = inspect(fake_layer())
        self.assertEqual(x["candidate_id"], "ca.ontario.mnr.emergency-historical-events")
        self.assertEqual(x["source_wkid"], 4269)
        self.assertEqual(x["geometry_type"], "esriGeometryMultipoint")
        self.assertFalse(x["single_event_polygon_available"])
        self.assertFalse(x["loss_quantities_verified"])
        self.assertFalse(x["model_input_admitted"])
        self.assertFalse(x["individual_feature_rows_requested"])

    def test_reject_drifted_layer_identity_geometry_or_crs(self):
        for obj in (
            {"id": 21},
            {"id": "20"},
            {"name": "Flood Events"},
            {"type": "Raster Layer"},
            {"geometryType": "esriGeometryPolygon"},
            {"geometryType": "esriGeometryPoint"},
            {"sourceSpatialReference": {"wkid": 3857}},
            {"displayField": "EVENT_YEAR"},
            {"features": [{"attributes": {"EVENT_DESCR": "do-not-process"}}]},
            {"error": {"code": 403}},
            {"fields": [{"name": "OTHER", "type": "esriFieldTypeString"}]},
            {"fields": [{"name": "OGF_ID", "type": "esriFieldTypeDouble"}] * 2},
        ):
            with self.subTest(obj=obj), self.assertRaises(Blocked):
                inspect(fake_layer(**obj))

    def test_strict_json_and_size_boundaries(self):
        bad = [
            b"",
            b" " * 131073,
            b'{"id":20,"id":20}',
            b'{"id":NaN}',
            b'{"error":{"code":400}}',
            b"\xff\xfe",
        ]
        for original in bad:
            with self.subTest(body=original[:25]), self.assertRaises(Blocked):
                inspect(original)

    def test_pinned_original_byte_receipt_and_fail_closed_sha(self):
        data = fake_layer()
        digest = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "original.json"
            path.write_bytes(data)
            rec = verify(path, digest)
            self.assertEqual(rec["external_original_sha256"], digest)
            self.assertEqual(rec["external_original_bytes"], len(data))
            self.assertFalse(rec["source_raw_bytes_committed"])
            self.assertTrue(rec["offline_original_bytes_checked"])
            for bad_hash in ("bad", "A" * 64, "0" * 64):
                with self.subTest(hash=bad_hash), self.assertRaises(Blocked):
                    verify(path, bad_hash)

    def test_cli_is_offline_and_rejects_wrong_sha(self):
        data = fake_layer()
        digest = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "original.json"
            path.write_bytes(data)
            self.assertEqual(main(["--original-json", str(path), "--expected-sha256", digest]), 0)
            self.assertEqual(main(["--original-json", str(path), "--expected-sha256", "0"*64]), 2)


if __name__ == "__main__":
    unittest.main()
