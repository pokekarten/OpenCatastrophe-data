# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only tests; no network or copied provider responses."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from research_runners.probe_aims_nld_flood_defences_v0 import (
    MAX_BYTES, NoRedirect, ProbeFailure, TARGETS, get_one, main, validate_payload,
)


def fixture(target):
    return {
        "objectIdFieldName": target.oid,
        "geometryType": "esriGeometryPolyline",
        "spatialReference": {"wkid": target.wkid},
        "fields": [{"name": target.oid, "type": "esriFieldTypeOID"}],
        "features": [{"attributes": {target.oid: 37}}],
        "exceededTransferLimit": True,
    }


def encoded(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class TestFloodDefenceProbe(unittest.TestCase):
    def test_both_sources_accept_one_bounded_no_geometry_oid(self):
        for target in TARGETS:
            with self.subTest(target=target.source_id):
                result = validate_payload(encoded(fixture(target)), target)
                self.assertEqual(result["wkid"], target.wkid)
                self.assertEqual(result["shape"], "one_oid_no_geometry")
                self.assertNotIn("geometry", result)

    def test_query_is_fully_fixed_and_bounded(self):
        self.assertEqual(len(TARGETS), 2)
        for t in TARGETS:
            self.assertIn("resultRecordCount=1", t.url)
            self.assertIn("returnGeometry=false", t.url)
            self.assertIn("outFields=" + t.oid, t.url)
            self.assertIn("f=json", t.url)
            self.assertTrue(t.url.startswith("https://"))

    def test_rejects_bad_json_empty_html_and_oversize(self):
        target = TARGETS[0]
        for raw in (b"", b"<html>blocked</html>", b"{bad", b"x" * (MAX_BYTES + 1), b'{"error":{"code":403}}'):
            with self.subTest(raw=raw[:15]), self.assertRaises(ProbeFailure):
                validate_payload(raw, target)

    def test_rejects_duplicate_keys_and_nan(self):
        for raw in (b'{"x":1,"x":2}', b'{"value":NaN}'):
            with self.assertRaises(ProbeFailure):
                validate_payload(raw, TARGETS[0])

    def test_rejects_schema_drift(self):
        target = TARGETS[0]
        for key, bad in (
            ("objectIdFieldName", "WRONG"),
            ("geometryType", "esriGeometryPolygon"),
            ("spatialReference", {"wkid": 4326}),
            ("fields", [{"name": "something", "type": "esriFieldTypeOID"}]),
            ("features", []),
            ("features", [{"attributes": {target.oid: 3}, "geometry": {"x": 3}}]),
            ("features", [{"attributes": {"secret": "nonpublic"}}]),
            ("features", [{"attributes": {target.oid: True}}]),
            ("exceededTransferLimit", "true"),
        ):
            data = fixture(target)
            data[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ProbeFailure):
                validate_payload(encoded(data), target)

    def test_rejects_two_returned_features(self):
        payload = fixture(TARGETS[1])
        payload["features"].append({"attributes": {"OBJECTID": 38}})
        with self.assertRaises(ProbeFailure):
            validate_payload(encoded(payload), TARGETS[1])

    def test_cli_selects_exactly_one_trusted_fixed_provider(self):
        calls = []

        def fake_get_one(target):
            calls.append(target.source_id)
            return {
                "source_id": target.source_id,
                "shape": "one_oid_no_geometry",
                "wkid": target.wkid,
                "original_response_sha256": "0" * 64,
            }

        with patch(
            "research_runners.probe_aims_nld_flood_defences_v0.get_one",
            side_effect=fake_get_one,
        ), redirect_stdout(io.StringIO()) as capture:
            self.assertEqual(main(["--live", "--source", TARGETS[1].source_id]), 0)
        self.assertEqual(calls, [TARGETS[1].source_id])
        receipt = json.loads(capture.getvalue())
        self.assertFalse(receipt["data_persisted"])
        self.assertFalse(receipt["model_admitted"])
        self.assertNotIn("url", receipt)

    def test_cli_disallows_network_by_default_and_untrusted_source(self):
        with patch(
            "research_runners.probe_aims_nld_flood_defences_v0.get_one"
        ) as call:
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                main(["--source", TARGETS[0].source_id])
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                main(["--live", "--source", "not-an-allowed-provider"])
            call.assert_not_called()

    def test_no_redirect_handler(self):
        with self.assertRaisesRegex(ProbeFailure, "redirect forbidden"):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.example/")

    def test_get_one_offline_fake_success_and_identity_check(self):
        target = TARGETS[0]
        body = encoded(fixture(target))

        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}
            def geturl(self):
                return target.url
            def read(self, size):
                assert size == MAX_BYTES + 1
                return body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        class Opener:
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return Response()

        opener = Opener()
        receipt = get_one(target, opener)
        self.assertEqual(len(receipt["original_response_sha256"]), 64)
        self.assertEqual(opener.timeout, 15)

        class WrongURLResponse(Response):
            def geturl(self):
                return "https://other.example"

        class WrongURLOpener(Opener):
            def open(self, request, timeout):
                return WrongURLResponse()

        with self.assertRaises(ProbeFailure):
            get_one(target, WrongURLOpener())


if __name__ == "__main__":
    unittest.main()
