# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic MeteoSwiss STAC Collection fixtures; no original data/assets."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.probe_meteoswiss_hail_stac_collection_v0 import (
    ACCESS_ID, COLLECTION_ID, HailCollectionBlocked, MAX_BYTES,
    NoRedirect, PROVIDER, TIMEOUT, URL,
    inspect_collection, main, probe, verify_reviewed_contract,
)


def fixture() -> dict:
    return {
        "type": "Collection",
        "stac_version": "1.0.0",
        "id": COLLECTION_ID,
        "title": "Spatial climate analyses - Hail",
        "description": "Swiss radar-based hail climatology, April–September season",
        "license": "CC-BY",
        "providers": [{"name": PROVIDER, "roles": ["producer", "licensor"]}],
        "extent": {"spatial": {"bbox": [[5.96, 45.82, 10.49, 47.81]]},
                   "temporal": {"interval": [[None, None]]}},
        "links": [{"rel": "self", "href": URL},
                  {"rel": "items", "href": "https://data.geo.admin.ch/never-follow"}],
        "assets": {},
    }


def encoded(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


class FakeResponse:
    def __init__(self, raw=None, status=200, url=URL, media="application/json",
                 other=None):
        self.raw = encoded(fixture()) if raw is None else raw
        self.status = status
        self.url = url
        self.headers = {
            "Content-Type": media, "Content-Encoding": "identity",
            "Content-Length": str(len(self.raw)),
        }
        self.headers.update(other or {})

    def geturl(self):
        return self.url

    def read(self, maximum):
        return self.raw[:maximum]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class MeteoSwissHailCollectionTests(unittest.TestCase):
    def test_contract_is_reviewed_for_one_stac_collection_get_only(self):
        verify_reviewed_contract()
        self.assertEqual(ACCESS_ID, "meteoswiss.national-hail-climatology")
        self.assertEqual(COLLECTION_ID, "ch.meteoschweiz.ogd-radar-derived-grid")
        self.assertEqual(URL, "https://data.geo.admin.ch/api/stac/v1/collections/" + COLLECTION_ID)
        self.assertEqual(MAX_BYTES, 262144)
        self.assertEqual(TIMEOUT, 30)

    def test_valid_synthetic_collection_without_assets(self):
        result = inspect_collection(encoded(fixture()))
        self.assertEqual(result["collection_id_verified"], COLLECTION_ID)
        self.assertEqual(result["collection_license_label"], "CC-BY")
        self.assertTrue(result["swiss_spatial_scope_verified"])
        self.assertEqual(result["stac_item_gets_executed"], 0)
        self.assertEqual(result["linked_asset_requests_executed"], 0)
        self.assertEqual(result["netcdf_files_downloaded"], 0)

    def test_provider_and_license_drift_fail_closed(self):
        for path, replacement in (
            ("id", "some-other-collection"),
            ("title", "Weather forecast"),
            ("type", "FeatureCollection"),
            ("stac_version", "0.9.0"),
            ("license", "proprietary"),
        ):
            with self.subTest(path=path):
                x = fixture()
                x[path] = replacement
                with self.assertRaises(HailCollectionBlocked):
                    inspect_collection(encoded(x))
        for change in ("provider", "roles", "self"):
            x = fixture()
            if change == "provider":
                x["providers"][0]["name"] = "not MeteoSwiss"
            elif change == "roles":
                x["providers"][0]["roles"] = ["producer"]
            else:
                x["links"][0]["href"] = "https://elsewhere.invalid"
            with self.subTest(change=change), self.assertRaises(HailCollectionBlocked):
                inspect_collection(encoded(x))

    def test_bbox_description_and_json_malformations_fail(self):
        for data in (
            b"", b"[]", b"{bad}", b'{"id":"x","id":"y"}',
            b'{"x":NaN}', b'\xff', b"x" * (MAX_BYTES + 1),
        ):
            with self.subTest(data=data[:30]), self.assertRaises(HailCollectionBlocked):
                inspect_collection(data)
        for value in (
            [[4.0, 45.0, 12.0, 50.0]],
            [[5.0, 47.0, 10.0, 46.0]],
            [[5.0, 45.0, float("nan"), 48.0]],
            [5.0, 45.0, 10.0, 48.0],
        ):
            x = fixture()
            x["extent"]["spatial"]["bbox"] = value
            with self.subTest(bbox=value), self.assertRaises(HailCollectionBlocked):
                inspect_collection(encoded(x))
        x = fixture()
        x["description"] = "radar-only dataset"
        with self.assertRaises(HailCollectionBlocked):
            inspect_collection(encoded(x))

    def test_one_fixed_http_get_receipt_no_asset_download(self):
        requests = []

        def fake_open(req, timeout):
            requests.append((req.full_url, req.get_method(), timeout))
            return FakeResponse()

        report = probe(open_request=fake_open, clock=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(requests, [(URL, "GET", TIMEOUT)])
        self.assertEqual(report["response_sha256"], hashlib.sha256(encoded(fixture())).hexdigest())
        self.assertEqual(report["response_bytes"], len(encoded(fixture())))
        self.assertEqual(report["netcdf_files_downloaded"], 0)
        self.assertFalse(report["original_provider_body_persisted"])
        self.assertFalse(report["derived_model_input_approved"])
        self.assertFalse(report["commercial_bulk_hail_data_authorized"])
        self.assertNotIn("assets", report)

    def test_http_status_redirect_mime_compression_length_fail(self):
        too_many = encoded(fixture()) + b" " * MAX_BYTES
        for bad in (
            FakeResponse(status=206),
            FakeResponse(url="https://unknown.invalid/stac"),
            FakeResponse(media="text/html"),
            FakeResponse(other={"Content-Encoding": "gzip"}),
            FakeResponse(other={"Content-Length": "NaN"}),
            FakeResponse(other={"Content-Length": str(MAX_BYTES + 1)}),
            FakeResponse(other={"Content-Length": str(len(encoded(fixture())) + 1)}),
            FakeResponse(raw=too_many),
        ):
            with self.subTest(status=bad.status, url=bad.url, headers=bad.headers):
                with self.assertRaises(HailCollectionBlocked):
                    probe(open_request=lambda req, timeout: bad)

    def test_no_auto_network_without_explicit_live(self):
        with patch("scripts.probe_meteoswiss_hail_stac_collection_v0.probe") as runner:
            with self.assertRaises(SystemExit) as e:
                main([])
        self.assertEqual(e.exception.code, 2)
        runner.assert_not_called()

    def test_unsafe_redirect_disallowed(self):
        with self.assertRaises(HailCollectionBlocked):
            NoRedirect().redirect_request(None, None, 302, "moved", {},
                                          "https://other.invalid/")

    def test_rights_revocation_fails_preflight(self):
        from scripts.probe_meteoswiss_hail_stac_collection_v0 import validate_path
        x = copy.deepcopy(validate_path(
            __import__("scripts.probe_meteoswiss_hail_stac_collection_v0",
                       fromlist=["CONTRACT_PATH"]).CONTRACT_PATH
        ))
        x["rights_and_policy"]["commercial_automation_status"] = "unknown"
        with patch("scripts.probe_meteoswiss_hail_stac_collection_v0.validate_path",
                   return_value=x):
            with self.assertRaises(HailCollectionBlocked):
                verify_reviewed_contract()


if __name__ == "__main__":
    unittest.main()
