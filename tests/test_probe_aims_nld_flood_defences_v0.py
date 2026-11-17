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
    fields = [{"name": target.oid, "type": "esriFieldTypeOID"}]
    attributes = {target.oid: 37}
    if target.identity_field:
        fields.append({"name": target.identity_field, "type": "esriFieldTypeDouble"})
        attributes[target.identity_field] = 129.0
    return {
        "objectIdFieldName": target.oid,
        "geometryType": "esriGeometryPolyline",
        "spatialReference": {"wkid": target.wkid},
        "fields": fields,
        "features": [{"attributes": attributes}],
        "exceededTransferLimit": True,
    }


def encoded(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class TestFloodDefenceProbe(unittest.TestCase):
    def test_all_sources_accept_one_bounded_no_geometry_id(self):
        for target in TARGETS:
            with self.subTest(target=target.source_id):
                result = validate_payload(encoded(fixture(target)), target)
                self.assertEqual(result["wkid"], target.wkid)
                self.assertEqual(result["shape"], "one_oid_one_join_id_no_geometry" if target.identity_field else "one_oid_no_geometry")
                self.assertNotIn("geometry", result)

    def test_query_is_fully_fixed_and_bounded(self):
        self.assertEqual(len(TARGETS), 3)
        for t in TARGETS:
            self.assertIn("resultRecordCount=1", t.url)
            self.assertIn("returnGeometry=false", t.url)
            self.assertIn("outFields=" + t.oid, t.url)
            self.assertIn("returnGeometry=false", t.url)
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

    def test_hidden_json_exponent_overflow_is_rejected(self):
        target = TARGETS[2]
        raw = encoded(fixture(target))[:-1] + b',"unrelated_provider_number":1e999}'
        with self.assertRaisesRegex(ProbeFailure, "non-finite JSON exponent"):
            validate_payload(raw, target)

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

    def test_embankment_source_uses_unique_field_and_no_geometry_or_raw_id_output(self):
        target = TARGETS[2]
        self.assertEqual(target.source_id, "us.usace.nld.public-embankments.2026")
        self.assertIn("/FeatureServer/11/query", target.url)
        self.assertIn("outFields=OBJECTID%2CEMBANK_ID", target.url)
        self.assertEqual(target.identity_field, "EMBANK_ID")
        valid = fixture(target)
        summary = validate_payload(encoded(valid), target)
        self.assertTrue(summary["join_id_present"])
        self.assertEqual(summary["shape"], "one_oid_one_join_id_no_geometry")
        self.assertNotIn("EMBANK_ID", json.dumps(summary))
        self.assertNotIn("129", json.dumps(summary))
        for key, bad in (
            ("fields", [{"name": target.oid, "type": "esriFieldTypeOID"}]),
            ("fields", [
                {"name": target.oid, "type": "esriFieldTypeOID"},
                {"name": "FLOODWALL_ID", "type": "esriFieldTypeDouble"},
            ]),
            ("features", [{"attributes": {target.oid: 37, "FLOODWALL_ID": 129}}]),
            ("features", [{"attributes": {target.oid: 37, "EMBANK_ID": True}}]),
            ("features", [{"attributes": {target.oid: 37, "EMBANK_ID": -1}}]),
            ("features", [{"attributes": {target.oid: 37, "EMBANK_ID": 129}, "geometry": {"paths": []}}]),
        ):
            data = fixture(target)
            data[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ProbeFailure):
                validate_payload(encoded(data), target)
        nullable = fixture(target)
        nullable["features"][0]["attributes"]["EMBANK_ID"] = None
        self.assertFalse(validate_payload(encoded(nullable), target)["join_id_present"])

    def test_join_identifier_is_lossless_integer_even_when_esri_double(self):
        target = TARGETS[2]
        for bad in (129.5, 2 ** 53, 10 ** 400, True, -1, "129",
                    float("inf"), float("nan")):
            row = fixture(target)
            row["features"][0]["attributes"]["EMBANK_ID"] = bad
            with self.subTest(bad=str(bad)[:25]), self.assertRaises(ProbeFailure):
                validate_payload(encoded(row), target)
        for good in (0, 129, 129.0, (2 ** 53) - 1):
            row = fixture(target)
            row["features"][0]["attributes"]["EMBANK_ID"] = good
            with self.subTest(good=good):
                self.assertTrue(validate_payload(encoded(row), target)["join_id_present"])
        row = fixture(target)
        row["features"][0]["attributes"]["OBJECTID"] = 10 ** 400
        with self.assertRaises(ProbeFailure):
            validate_payload(encoded(row), target)

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

        class CustomHeadersOpener(Opener):
            def __init__(self, headers):
                self.headers = headers
            def open(self, request, timeout):
                class CustomResponse(Response):
                    headers = self.headers
                return CustomResponse()

        for invalid in (
            {"Content-Type": "application/jsonp"},
            {"Content-Type": "text/plainness"},
            {"Content-Type": "application/json", "Content-Length": "-1"},
            {"Content-Type": "application/json", "Content-Length": "invalid"},
            {"Content-Type": "application/json", "Content-Length": str(MAX_BYTES + 1)},
            {"Content-Type": "application/json", "Content-Length": str(len(body) + 1)},
            {"Content-Type": "application/json", "Content-Length": str(len(body) - 1)},
        ):
            with self.subTest(headers=invalid), self.assertRaises(ProbeFailure):
                get_one(target, CustomHeadersOpener(invalid))

        valid_headers = {"Content-Type": "application/json; charset=utf-8",
                         "Content-Length": str(len(body))}
        self.assertEqual(len(get_one(target, CustomHeadersOpener(valid_headers))[
            "original_response_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
