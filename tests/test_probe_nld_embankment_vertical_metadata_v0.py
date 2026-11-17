# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative and provenance tests for USACE NLD layer 11 metadata."""
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from research_runners.probe_nld_embankment_vertical_metadata_v0 import (
    DICTIONARY_REFERENCE_UNIT,
    MAX_BYTES,
    METADATA_URL,
    NoRedirect,
    PreflightError,
    SOURCE_ID,
    get_original_metadata,
    main,
    validate_metadata,
)


def fixture():
    height = {
        "heightModel": "gravity_related_height",
        "vertCRS": "NAVD88_height_(ftUS)",
        "heightUnit": "us-foot",
    }
    return {
        "id": 11,
        "name": "Embankments",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPolyline",
        "hasZ": True,
        "hasM": False,
        "objectIdField": "OBJECTID",
        "isDataVersioned": True,
        "isDataArchived": False,
        "archivingInfo": {"supportsQueryWithHistoricMoment": False},
        "spatialReference": {
            "wkid": 4269, "vcsWkid": 105703, "latestVcsWkid": 6360,
            "zUnits": 3048.0060960121905,
        },
        "sourceSpatialReference": {
            "wkid": 4269, "vcsWkid": 105703, "latestVcsWkid": 6360,
            "zUnits": 3048.0060960121905,
        },
        "heightModelInfo": dict(height),
        "sourceHeightModelInfo": dict(height),
        "fields": [
            {"name": "OBJECTID", "type": "esriFieldTypeOID"},
            {"name": "EMBANK_ID", "type": "esriFieldTypeDouble"},
            {"name": "SEGMENT_ID", "type": "esriFieldTypeDouble"},
            {"name": "SYSTEM_ID", "type": "esriFieldTypeDouble"},
            {"name": "SURVEY_DATE", "type": "esriFieldTypeDate"},
        ],
    }


def encode(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class TestNldEmbankmentVerticalMetadata(unittest.TestCase):
    def test_fail_closed_positive_facts_never_approve_geometry_or_height(self):
        report = validate_metadata(encode(fixture()))
        self.assertEqual(report["source_id"], SOURCE_ID)
        self.assertEqual(report["shape"], "metadata_only_no_feature_or_geometry")
        self.assertEqual(report["horizontal_crs"], "EPSG:4269")
        self.assertEqual(report["vertical_crs"], "NAVD88_height_(ftUS)")
        self.assertEqual(report["service_height_unit"], "us-foot")
        self.assertEqual(report["service_vcs_wkid"], 105703)
        self.assertEqual(report["service_latest_vcs_wkid"], 6360)
        self.assertTrue(report["source_vertical_crs_views_consistent"])
        self.assertTrue(report["z_storage_resolution_verified_not_unit_conversion"])
        self.assertEqual(DICTIONARY_REFERENCE_UNIT, "international-foot")
        self.assertTrue(report["unit_conflict_unresolved"])
        self.assertTrue(report["service_is_data_versioned"])
        for name in ("historic_snapshot_supported", "elevation_values_examined", "data_persisted", "model_admitted"):
            self.assertFalse(report[name])
        self.assertNotIn("features", report)
        self.assertNotIn("geometry", report)

    def test_wrong_source_identity_and_version_flags_rejected(self):
        for key, bad in (
            ("id", 12), ("id", True), ("name", "Floodwalls"),
            ("type", "Map Layer"), ("geometryType", "esriGeometryPolygon"),
            ("hasZ", False), ("hasZ", 1), ("hasM", True),
            ("objectIdField", "EMBANK_ID"), ("isDataVersioned", False),
            ("isDataArchived", True),
        ):
            data = fixture()
            data[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(PreflightError):
                validate_metadata(encode(data))

    def test_historic_and_vertical_crs_unit_conflicts_fail_closed(self):
        edits = [
            ("archivingInfo", {"supportsQueryWithHistoricMoment": True}),
            ("archivingInfo", {}),
            ("sourceSpatialReference", {"wkid": 4326}),
            ("sourceSpatialReference", {"wkid": 4269.0}),
            ("heightModelInfo", None),
            ("heightModelInfo", {"heightUnit": "international-foot"}),
            ("sourceHeightModelInfo", {"heightUnit": "international-foot"}),
        ]
        for key, bad in edits:
            d = fixture()
            d[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(PreflightError):
                validate_metadata(encode(d))
        d = fixture()
        d["heightModelInfo"]["vertCRS"] = "unknown"
        with self.assertRaises(PreflightError):
            validate_metadata(encode(d))

    def test_independent_vertical_crs_views_reject_drift_and_bad_storage_units(self):
        for where in ("spatialReference", "sourceSpatialReference"):
            for key, bad in (
                ("wkid", 4326), ("wkid", True),
                ("vcsWkid", 6360), ("vcsWkid", True),
                ("latestVcsWkid", 105703), ("latestVcsWkid", 6360.0),
                ("zUnits", -1), ("zUnits", "3048.006"),
                ("zUnits", 10000), ("zUnits", True),
                ("zUnits", float("inf")), ("zUnits", 10 ** 400),
                ("zUnits", -(10 ** 400)),
            ):
                d = fixture()
                d[where][key] = bad
                with self.subTest(where=where, key=key, bad=bad), self.assertRaises(PreflightError):
                    validate_metadata(encode(d))
            for missing in ("vcsWkid", "latestVcsWkid", "zUnits"):
                d = fixture()
                d[where].pop(missing)
                with self.subTest(where=where, missing=missing), self.assertRaises(PreflightError):
                    validate_metadata(encode(d))

    def test_join_and_survey_schema_drift_fail_closed(self):
        for change in ("missing", "wrong_type", "duplicate", "invalid"):
            data = fixture()
            if change == "missing":
                data["fields"] = [f for f in data["fields"] if f["name"] != "EMBANK_ID"]
            elif change == "wrong_type":
                data["fields"][1]["type"] = "esriFieldTypeString"
            elif change == "duplicate":
                data["fields"].append({"name": "EMBANK_ID", "type": "esriFieldTypeDouble"})
            else:
                data["fields"].append({"name": None, "type": "esriFieldTypeDouble"})
            with self.subTest(change=change), self.assertRaises(PreflightError):
                validate_metadata(encode(data))

    def test_invalid_or_overlarge_bytes_rejected(self):
        for raw in (
            b"", b"<html>no</html>", b'{"error":{"code":403}}', b"{bad",
            b'{"id":11,"id":12}', b'{"id":NaN}', b"x" * (MAX_BYTES + 1),
            b"\xff",
        ):
            with self.subTest(body=raw[:20]), self.assertRaises(PreflightError):
                validate_metadata(raw)

    def test_finite_json_metadata_blocks_float_overflow(self):
        # RFC JSON exponent syntax is legal, but Python's default decoder
        # silently converts its overflow to float('inf'). Fail closed even
        # when the anomalous value is outside the required schema fields.
        raw = encode(fixture())[:-1] + b',"unexpected_value":1e999}'
        with self.assertRaisesRegex(PreflightError, "non-finite JSON number"):
            validate_metadata(raw)

    def test_huge_json_integer_is_controlled_source_failure(self):
        huge = encode(fixture())[:-1] + b',"unrelated":' + b"9" * 5000 + b"}"
        with self.assertRaisesRegex(PreflightError, "invalid JSON metadata"):
            validate_metadata(huge)

    def test_transport_fixed_origin_size_and_hash_without_raw_values(self):
        raw = encode(fixture())

        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}
            def geturl(self):
                return METADATA_URL
            def read(self, size):
                assert size == MAX_BYTES + 1
                return raw
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False

        class Opener:
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return Response()

        opener = Opener()
        report = get_original_metadata(opener)
        self.assertEqual(opener.request.full_url, METADATA_URL)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.timeout, 15)
        self.assertEqual(len(report["original_response_sha256"]), 64)
        self.assertNotIn("fields", json.dumps(report))
        self.assertFalse(report["model_admitted"])

        class WrongURLResponse(Response):
            def geturl(self):
                return "https://unrelated.example.com/"

        class WrongURLOpener(Opener):
            def open(self, request, timeout):
                return WrongURLResponse()

        with self.assertRaises(PreflightError):
            get_original_metadata(WrongURLOpener())

        class CustomHeadersOpener(Opener):
            def __init__(self, headers):
                self.headers = headers
            def open(self, request, timeout):
                class CustomResponse(Response):
                    headers = self.headers
                return CustomResponse()

        for invalid in (
            {"Content-Type": "application/jsonp"},
            {"Content-Type": "text/plain-vendor"},
            {"Content-Type": "application/json", "Content-Length": "-1"},
            {"Content-Type": "application/json", "Content-Length": "NaN"},
            {"Content-Type": "application/json", "Content-Length": str(MAX_BYTES + 1)},
            {"Content-Type": "application/json", "Content-Length": "9" * 5000},
            {"Content-Type": "application/json", "Content-Length": str(len(raw) - 1)},
            {"Content-Type": "application/json", "Content-Length": str(len(raw) + 1)},
        ):
            with self.subTest(headers=invalid), self.assertRaises(PreflightError):
                get_original_metadata(CustomHeadersOpener(invalid))
        good = {"Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(raw))}
        self.assertEqual(get_original_metadata(CustomHeadersOpener(good))[
            "original_response_sha256"], report["original_response_sha256"])

    def test_no_redirect_and_no_implicit_network_access(self):
        with self.assertRaises(PreflightError):
            NoRedirect().redirect_request(
                None, None, 302, "other", {}, "https://untrusted.example/"
            )
        with patch("research_runners.probe_nld_embankment_vertical_metadata_v0.get_original_metadata") as get:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([])
            get.assert_not_called()
            get.return_value = validate_metadata(encode(fixture()))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["--live"]), 0)
            self.assertIn(SOURCE_ID, out.getvalue())
            self.assertIn('"model_admitted": false', out.getvalue())
            self.assertNotIn("EMBANK_ID", out.getvalue())


if __name__ == "__main__":
    unittest.main()
