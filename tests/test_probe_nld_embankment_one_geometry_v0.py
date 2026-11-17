# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic negative tests: no copied public provider geometry or live GET."""
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from research_runners.probe_nld_embankment_one_geometry_v0 import (
    GeometryCanaryError, MAX_BYTES, MAX_VERTICES, NoRedirect, QUERY_URL,
    SOURCE_ID, get_one_original_geometry, main, validate_geometry_response,
)


def make_fixture():
    return {
        "objectIdFieldName": "OBJECTID",
        "geometryType": "esriGeometryPolyline",
        "spatialReference": {"wkid": 4269, "latestWkid": 4269},
        "fields": [
            {"name": "OBJECTID", "type": "esriFieldTypeOID"},
            {"name": "EMBANK_ID", "type": "esriFieldTypeDouble"},
        ],
        "features": [
            {
                "attributes": {"OBJECTID": 43, "EMBANK_ID": 71.0},
                "geometry": {
                    "hasZ": True,
                    "paths": [[[-81.25, 37.5, 1.5], [-81.26, 37.49, None]]],
                },
            }
        ],
        "exceededTransferLimit": True,
    }


def encode(data):
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


class TestNldOneOriginalGeometry(unittest.TestCase):
    def test_fixed_single_original_geometry_not_download(self):
        self.assertTrue(QUERY_URL.startswith(
            "https://geospatial.sec.usace.army.mil/dls/rest/services/"
            "NLD/Public/FeatureServer/11/query?"
        ))
        for piece in (
            "where=1%3D1", "outFields=OBJECTID%2CEMBANK_ID",
            "returnGeometry=true", "returnZ=true", "returnM=false",
            "resultRecordCount=1", "orderByFields=OBJECTID",
            "outSR=4269", "f=json",
        ):
            self.assertIn(piece, QUERY_URL)
        self.assertNotIn("token=", QUERY_URL)
        self.assertNotIn("resultOffset=", QUERY_URL)
        self.assertNotIn("outFields=*", QUERY_URL)

    def test_one_3d_original_shape_reports_coverage_not_crest_height(self):
        outcome = validate_geometry_response(encode(make_fixture()))
        self.assertEqual(outcome["source_id"], SOURCE_ID)
        self.assertEqual(outcome["path_count"], 1)
        self.assertEqual(outcome["vertex_count"], 2)
        self.assertEqual(outcome["finite_z_count"], 1)
        self.assertEqual(outcome["null_z_count"], 1)
        self.assertTrue(outcome["z_observed_not_crest_certified"])
        for key in ("vertical_units_resolved", "historical_snapshot_supported",
                    "hydraulic_protection_validated", "source_bytes_persisted",
                    "model_admitted"):
            self.assertFalse(outcome[key])
        rendered = json.dumps(outcome)
        for value in ("-81.25", "37.49", "OBJECTID", "EMBANK_ID", "71.0", "1.5"):
            self.assertNotIn(value, rendered)

    def test_all_missing_z_reports_missingness_without_approving(self):
        data = make_fixture()
        data["features"][0]["geometry"]["paths"][0][0][2] = None
        report = validate_geometry_response(encode(data))
        self.assertFalse(report["z_observed_not_crest_certified"])
        self.assertEqual(report["finite_z_count"], 0)
        self.assertEqual(report["null_z_count"], 2)
        self.assertFalse(report["model_admitted"])

    def test_wrong_identity_crs_and_schema_rejected(self):
        tests = [
            ("objectIdFieldName", "FLOODWALL_ID"),
            ("geometryType", "esriGeometryPolygon"),
            ("spatialReference", {"wkid": 4326}),
            ("fields", [{"name": "OBJECTID", "type": "esriFieldTypeOID"}]),
            ("fields", [
                {"name": "OBJECTID", "type": "esriFieldTypeOID"},
                {"name": "SYSTEM_ID", "type": "esriFieldTypeDouble"},
            ]),
            ("features", []),
            ("features", [{"attributes": {}, "geometry": {"hasZ": True, "paths": []}}]),
            ("exceededTransferLimit", "true"),
        ]
        for field, bad in tests:
            data = make_fixture()
            data[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(encode(data))

    def test_extra_features_attributes_geometry_and_bad_id_rejected(self):
        cases = [
            ("attributes", {"OBJECTID": 43, "EMBANK_ID": 71, "SYSTEM_ID": 33}),
            ("attributes", {"OBJECTID": 43, "EMBANK_ID": True}),
            ("attributes", {"OBJECTID": -1, "EMBANK_ID": 71}),
            ("attributes", {"OBJECTID": 43, "EMBANK_ID": -3.2}),
            ("geometry", {"hasZ": False, "paths": [[[0, 0, 1], [1, 1, 2]]]}),
            ("geometry", {"hasZ": True, "hasM": True, "paths": [[[0, 0, 1], [1, 1, 2]]]}),
            ("geometry", {"hasZ": True, "paths": [[[0, 0, 1], [1, 1, 2]]], "extent": "untrusted"}),
        ]
        for field, value in cases:
            data = make_fixture()
            data["features"][0][field] = value
            with self.subTest(field=field, value=str(value)[:40]), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(encode(data))
        data = make_fixture()
        data["features"].append(data["features"][0])
        with self.assertRaises(GeometryCanaryError):
            validate_geometry_response(encode(data))

    def test_embankment_ids_must_be_lossless_integer_join_keys(self):
        for bad in (1.5, -1, True, "71", 2 ** 53, 10 ** 400,
                    float("nan"), float("inf")):
            row = make_fixture()
            row["features"][0]["attributes"]["EMBANK_ID"] = bad
            with self.subTest(value=str(bad)[:32]), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(encode(row))
        for good in (0, 71, 71.0, (2 ** 53) - 1):
            row = make_fixture()
            row["features"][0]["attributes"]["EMBANK_ID"] = good
            with self.subTest(good=good):
                self.assertTrue(validate_geometry_response(encode(row))["one_feature"])

    def test_oversized_json_integers_rejected_without_python_overflow(self):
        for mutation in ("oid", "z"):
            row = make_fixture()
            if mutation == "oid":
                row["features"][0]["attributes"]["OBJECTID"] = 10 ** 400
            else:
                row["features"][0]["geometry"]["paths"][0][0][2] = 10 ** 400
            with self.subTest(mutation=mutation), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(encode(row))

    def test_bad_vertices_and_malformed_paths_fail_closed(self):
        bad_paths = [
            [], [[]], [[[0, 0, 1]]],
            [[[0, 0, 1], [1, 1, 2, 3]]],
            [[[0, 0, 1], [1, 1, True]]],
            [[[0, 0, 1], [1, 1, "unknown"]]],
            [[[181, 0, 1], [1, 1, 2]]],
            [[[0, 91, 1], [1, 1, 2]]],
            [[[0, 0, 1], [1, 1, 2]]] * 65,
            [[[0, 0, 1], [1, 1, 2]] * (MAX_VERTICES + 1)],
        ]
        for paths in bad_paths:
            data = make_fixture()
            data["features"][0]["geometry"]["paths"] = paths
            with self.subTest(count=len(paths)), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(encode(data))

    def test_reject_html_duplicate_members_infinite_and_oversize(self):
        cases = [
            b"", b"<html>error</html>", b"{bad",
            b'{"error":{"code":403}}',
            b'{"x":1,"x":2}', b'{"foo":NaN}',
            b'{"foo":Infinity}', b"x" * (MAX_BYTES + 1),
        ]
        for value in cases:
            with self.subTest(raw=value[:20]), self.assertRaises(GeometryCanaryError):
                validate_geometry_response(value)

    def test_original_transport_fixed_endpoint_status_size_and_hash(self):
        body = encode(make_fixture())

        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}
            def geturl(self):
                return QUERY_URL
            def read(self, limit):
                assert limit == MAX_BYTES + 1
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
        result = get_one_original_geometry(opener)
        self.assertEqual(opener.request.full_url, QUERY_URL)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.timeout, 15)
        self.assertEqual(len(result["original_response_sha256"]), 64)
        self.assertNotIn("-81.25", json.dumps(result))
        self.assertFalse(result["model_admitted"])

        class RedirectOpener(Opener):
            def open(self, request, timeout):
                class Redirect(Response):
                    def geturl(self):
                        return "https://untrusted.example"
                return Redirect()

        with self.assertRaises(GeometryCanaryError):
            get_one_original_geometry(RedirectOpener())
        with self.assertRaises(GeometryCanaryError):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://host.invalid")

    def test_cli_never_reads_network_without_opt_in(self):
        with patch(
            "research_runners.probe_nld_embankment_one_geometry_v0.get_one_original_geometry"
        ) as get:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([])
            get.assert_not_called()
            get.return_value = validate_geometry_response(encode(make_fixture()))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--live"]), 0)
            self.assertIn(SOURCE_ID, output.getvalue())
            self.assertNotIn("EMBANK_ID", output.getvalue())
            self.assertNotIn("-81.25", output.getvalue())
            self.assertIn('"model_admitted": false', output.getvalue())


if __name__ == "__main__":
    unittest.main()
