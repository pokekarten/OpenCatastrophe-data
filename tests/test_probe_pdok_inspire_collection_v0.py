# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-native PDOK INSPIRE Gewaspercelen Collection tests."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import probe_pdok_inspire_collection_v0 as pdok
from scripts.validate_source_access import validate_path
from scripts.structured_public_views import render_structured_markdown


def fixture():
    return {
        "id": "gewaspercelen", "title": "Gewaspercelen",
        "description": "De Gewaspercelen bevatten landbouwpercelen uit de RVO registraties.",
        "itemType": "feature", "storageCrs": pdok.EPSG4258,
        "crs": [pdok.CRS84, pdok.EPSG28992, pdok.EPSG4258],
        "extent": {"spatial": {"crs": pdok.CRS84,
                               "bbox": [[2.527125, 50.212863, 7.374026, 55.72116]]}},
        "links": [
            {"rel": "self", "type": "application/json", "href": pdok.URL},
            {"rel": "items", "type": "application/geo+json",
             "href": "https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen/items?f=json"}
        ],
        "updated": "2026-04-01T13:22:57Z",
    }


def enc(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


class FakeResponse:
    def __init__(self, raw=None, status=200, url=None, media="application/json", extra=None):
        self.raw = enc(fixture()) if raw is None else raw
        self.status = status
        self.url = url or pdok.URL
        self.headers = {"Content-Type": media, "Content-Encoding": "identity",
                        "Content-Length": str(len(self.raw))}
        self.headers.update(extra or {})

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.raw[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class INSPIRECollectionTests(unittest.TestCase):
    def test_rights_contract_and_canonical_public_view(self):
        pdok.verify_reviewed_contract()
        obj = validate_path(pdok.CONTRACT_PATH)
        self.assertEqual(obj["source_ids"], [pdok.SOURCE_ID])
        self.assertEqual(obj["access_scope"], ["metadata"])
        self.assertEqual(obj["rights_and_policy"]["redistribution_status"], "unknown")
        self.assertEqual(
            pdok.CONTRACT_PATH.with_suffix(".md").read_text(encoding="utf8"),
            render_structured_markdown(pdok.CONTRACT_PATH, obj, kind="access"),
        )

    def test_correct_source_metadata_no_parcels_or_year_approval(self):
        v = pdok.inspect_collection(enc(fixture()))
        self.assertTrue(v["inspire_ogc_storage_crs_epsg4258_verified"])
        self.assertTrue(v["bbox_overlaps_netherlands_verified"])
        self.assertEqual(v["feature_rows_requested"], 0)
        self.assertFalse(v["historical_2025_original_sha_verified"])
        self.assertFalse(v["independent_rvo_source_verified"])
        self.assertFalse(v["model_input_approved"])

    def test_strict_identity_crs_bbox_self_and_duplicate_fails(self):
        for key, bad in [
            ("id", "brpgewas"), ("title", "BRP Gewaspercelen"),
            ("itemType", "FeatureCollection"), ("storageCrs", pdok.EPSG28992),
            ("description", "empty soil"),
        ]:
            obj = fixture()
            obj[key] = bad
            with self.subTest(key=key), self.assertRaises(pdok.InspireBlocked):
                pdok.inspect_collection(enc(obj))
        variants = ["bbox", "bbox_bool", "crs", "self", "double_self", "spatial_crs"]
        for which in variants:
            obj = fixture()
            if which == "bbox":
                obj["extent"]["spatial"]["bbox"] = [[20.0, 30.0, 25.0, 45.0]]
            if which == "bbox_bool":
                obj["extent"]["spatial"]["bbox"][0][0] = True
            if which == "crs":
                obj["crs"] = [pdok.CRS84, pdok.EPSG28992]
            if which == "self":
                obj["links"][0]["href"] = "https://wrong.example/"
            if which == "double_self":
                obj["links"].append(deepcopy(obj["links"][0]))
            if which == "spatial_crs":
                obj["extent"]["spatial"]["crs"] = pdok.EPSG28992
            with self.subTest(which=which), self.assertRaises(pdok.InspireBlocked):
                pdok.inspect_collection(enc(obj))

    def test_invalid_json_and_byte_budget_fail(self):
        for raw in (b"", b"[]", b"oops", b'{"id":1,"id":2}', b'{"x":NaN}', b"\xff",
                    b"x" * (pdok.MAX_BYTES + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(pdok.InspireBlocked):
                pdok.inspect_collection(raw)

    def test_network_disabled_by_default(self):
        with patch.object(pdok, "probe") as p:
            with self.assertRaises(SystemExit) as cm:
                pdok.main([])
            self.assertEqual(cm.exception.code, 2)
            p.assert_not_called()

    def test_exact_bounded_one_get_and_metadata_only_sha(self):
        hits = []
        def fake_get(req, timeout):
            hits.append((req.full_url, req.get_method(), timeout))
            return FakeResponse()
        r = pdok.probe(open_request=fake_get,
                       clock=lambda: datetime(2026, 11, 13, tzinfo=timezone.utc))
        self.assertEqual(hits, [(pdok.URL, "GET", pdok.TIMEOUT)])
        self.assertEqual(r["response_sha256"], hashlib.sha256(enc(fixture())).hexdigest())
        self.assertEqual(r["feature_rows_requested"], 0)
        self.assertFalse(r["historical_2025_original_sha_verified"])
        self.assertFalse(r["original_response_body_persisted"])
        self.assertNotIn("links", r)
        self.assertNotIn("geometries", r)

    def test_wrong_http_redirect_compression_length_and_mime_rejected(self):
        bads = [FakeResponse(status=206), FakeResponse(url="https://api.other.invalid/"),
                FakeResponse(media="text/html"),
                FakeResponse(extra={"Content-Encoding": "gzip"}),
                FakeResponse(extra={"Content-Length": "NaN"}),
                FakeResponse(extra={"Content-Length": str(pdok.MAX_BYTES + 1)}),
                FakeResponse(extra={"Content-Length": "1"}),
                FakeResponse(raw=b"x" * (pdok.MAX_BYTES + 1))]
        for res in bads:
            with self.subTest(headers=res.headers), self.assertRaises(pdok.InspireBlocked):
                pdok.probe(open_request=lambda req, timeout: res)

    def test_revoked_rights_stop_before_network(self):
        real = validate_path(pdok.CONTRACT_PATH)
        for field, value in (("commercial_automation_status", "unknown"),
                             ("dataset_rights_status", "unknown"),
                             ("redistribution_status", "allowed")):
            obj = deepcopy(real)
            obj["rights_and_policy"][field] = value
            with (self.subTest(field=field),
                  patch.object(pdok, "validate_path", return_value=obj),
                  patch.object(pdok, "_open") as open_mock):
                with self.assertRaises(pdok.InspireBlocked):
                    pdok.verify_reviewed_contract()
                open_mock.assert_not_called()

    def test_redirect_never_followed(self):
        with self.assertRaises(pdok.InspireBlocked):
            pdok.NoRedirect().redirect_request(None, None, 302, "elsewhere", {}, "https://other.invalid")


if __name__ == "__main__":
    unittest.main()
