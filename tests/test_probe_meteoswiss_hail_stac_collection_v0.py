# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, no-network tests for the reviewed Swiss hail STAC canary."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.probe_meteoswiss_hail_stac_collection_v0 import (
    ACCESS_ID, COLLECTION_ID, ITEMS_URL, URL, HailSTACBlocked,
    MAX_BYTES, TIMEOUT, NoRedirect, inspect_collection, probe,
    verify_contract,
)


def fixture() -> dict:
    return {
        "type": "Collection",
        "stac_version": "1.0.0",
        "id": COLLECTION_ID,
        "title": "Spatial climate analyses - Hail",
        "license": "CC-BY",
        "providers": [{
            "name": "Federal Office of Meteorology and Climatology MeteoSwiss",
            "roles": ["producer", "licensor"],
        }],
        "links": [
            {"rel": "self", "href": URL},
            {"rel": "items", "href": ITEMS_URL},
        ],
        "extent": {
            "spatial": {"bbox": [[5.96, 45.82, 10.49, 47.81]]},
            "temporal": {"interval": [["2026-10-31T04:00:18Z", "2026-11-12T04:00:18Z"]]},
        },
        "assets": {},
    }


def encoded(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")


class Response:
    def __init__(self, raw=None, status=200, url=URL, media="application/json", headers=None):
        self.body = raw if raw is not None else encoded(fixture())
        self.status, self.url = status, url
        self.headers = {
            "Content-Type": media,
            "Content-Encoding": "identity",
            "Content-Length": str(len(self.body)),
        }
        self.headers.update(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, max_bytes):
        return self.body[:max_bytes]


class MeteoSwissHailSTACTests(unittest.TestCase):
    def test_contract_stays_one_public_metadata_get_only(self):
        verify_contract()
        self.assertEqual(ACCESS_ID, "meteoswiss.national-hail-climatology")
        self.assertEqual(
            URL,
            "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid",
        )
        self.assertEqual(MAX_BYTES, 262144)
        self.assertEqual(TIMEOUT, 30)

    def test_valid_original_shape_yields_no_asset_download(self):
        r = inspect_collection(encoded(fixture()))
        self.assertEqual(r["stac_version_verified"], "1.0.0")
        self.assertEqual(r["collection_licence_verified"], "CC-BY")
        self.assertTrue(r["provider_identity_verified"])
        self.assertEqual(r["stac_item_requests"], 0)
        self.assertEqual(r["netcdf_assets_downloaded"], 0)

    def test_strict_original_identity_licence_and_links(self):
        mutations = (
            ("id", "unknown"),
            ("type", "FeatureCollection"),
            ("stac_version", "1.1.0"),
            ("license", "proprietary"),
            ("title", "Other climate"),
            ("providers", []),
            ("links", []),
            ("assets", {"hail.nc": {"href": "https://example.com/hail.nc"}}),
            ("extent", {}),
        )
        for key, value in mutations:
            with self.subTest(field=key):
                f = fixture()
                f[key] = value
                with self.assertRaises(HailSTACBlocked):
                    inspect_collection(encoded(f))
        f = fixture()
        f["links"][1]["href"] = "https://evil.example/items"
        with self.assertRaises(HailSTACBlocked):
            inspect_collection(encoded(f))
        f = fixture()
        f["providers"][0]["roles"] = ["producer"]
        with self.assertRaises(HailSTACBlocked):
            inspect_collection(encoded(f))

    def test_reject_duplicate_keys_nonfinite_and_bad_utf8(self):
        samples = (
            b'{"id":"good","id":"evil"}',
            encoded(fixture())[:-1] + b',"infinite":NaN}',
            b"\xff\x80",
            b'{"type":"Collection"',
            b"",
            b"a" * (MAX_BYTES + 1),
        )
        for raw in samples:
            with self.subTest(raw=raw[:22]):
                with self.assertRaises(HailSTACBlocked):
                    inspect_collection(raw)

    def test_reject_invalid_extent(self):
        f = fixture()
        f["extent"]["spatial"]["bbox"] = [[-100.0, 45.82, 10.49, 47.81]]
        with self.assertRaises(HailSTACBlocked):
            inspect_collection(encoded(f))

    def test_receipt_hashes_original_bytes_without_logging_provider_payload(self):
        requests = []
        original = encoded(fixture())

        def fake_open(req, timeout):
            requests.append((req.full_url, req.get_method(), timeout))
            return Response(raw=original)

        result = probe(
            open_request=fake_open,
            clock=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc),
        )
        self.assertEqual(requests, [(URL, "GET", TIMEOUT)])
        self.assertEqual(result["response_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(result["original_response_bytes"], len(original))
        self.assertFalse(result["original_provider_bytes_persisted"])
        self.assertFalse(result["cat_model_input_approved"])
        self.assertNotIn("links", result)
        self.assertNotIn("assets", result)

    def test_http_status_redirect_mime_gzip_length_oversize_rejected(self):
        samples = (
            Response(status=204),
            Response(url="https://other.example/stac"),
            Response(media="text/html"),
            Response(headers={"Content-Encoding": "gzip"}),
            Response(headers={"Content-Length": "not-an-integer"}),
            Response(headers={"Content-Length": "262145"}),
            Response(headers={"Content-Length": "1"}),
            Response(raw=b"X" * (MAX_BYTES + 1)),
        )
        for resp in samples:
            with self.subTest(status=resp.status, url=resp.url, media=resp.headers["Content-Type"]):
                with self.assertRaises(HailSTACBlocked):
                    probe(open_request=lambda req, timeout: resp)

    def test_cli_never_probes_by_default(self):
        from scripts.probe_meteoswiss_hail_stac_collection_v0 import main
        with patch("scripts.probe_meteoswiss_hail_stac_collection_v0.probe") as action:
            with self.assertRaises(SystemExit) as caught:
                main([])
        self.assertEqual(caught.exception.code, 2)
        action.assert_not_called()

    def test_redirect_handler_rejects_provider_movement(self):
        with self.assertRaises(HailSTACBlocked):
            NoRedirect().redirect_request(None, None, 302, "move", {}, "https://example.com/")


if __name__ == "__main__":
    unittest.main()
