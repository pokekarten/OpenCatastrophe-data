# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only MeteoSwiss Hail Climatology archive metadata tests."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import json
import unittest
from unittest.mock import patch

from scripts import probe_meteoswiss_hail_archive_item_v0 as p


def sample():
    return {
        "type": "Feature", "id": "archive-ch",
        "collection": p.COLLECTION_ID,
        "assets": {
            "synthetic-cog": {
                "href": "https://invalid.example/signed-source-token-private",
                "type": "image/tiff",
                "roles": ["data"],
            },
            "synthetic-netcdf": {
                "href": "https://invalid.example/synthetic-file.nc",
                "type": "application/x-netcdf",
                "roles": ["data"],
            },
        },
    }


def test_bytes(j):
    return json.dumps(j, sort_keys=True).encode("utf-8")


class MockResponse:
    status = 200

    def __init__(self, data=None, media="application/geo+json", declared=None):
        self.body = data if data is not None else test_bytes(sample())
        self.headers = {"Content-Type": media}
        if declared is not None:
            self.headers["Content-Length"] = declared

    def read(self, count):
        return self.body[:count]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class MockOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req, timeout))
        return self.response


class MeteoSwissArchiveTests(unittest.TestCase):
    def test_offline_valid_synthetic_archive_is_only_metadata(self):
        x = p.check_archive_metadata(test_bytes(sample()))
        self.assertEqual(x["archive_asset_metadata_count"], 2)
        self.assertEqual(x["archive_media_type_counts"]["image/tiff"], 1)
        self.assertEqual(x["archive_media_type_counts"]["application/x-netcdf"], 1)
        self.assertFalse(x["model_input_approved"])
        self.assertFalse(x["original_metadata_body_persisted"])
        self.assertEqual(x["asset_links_followed"], 0)
        self.assertNotIn("invalid.example", json.dumps(x))
        self.assertNotIn("source-token-private", json.dumps(x))

    def test_exact_single_request_and_timeout(self):
        opener = MockOpener(MockResponse())
        result = p.probe(opener)
        self.assertEqual(result["archive_asset_metadata_count"], 2)
        self.assertEqual(len(opener.requests), 1)
        req, timeout = opener.requests[0]
        self.assertEqual(req.full_url, p.URL)
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(timeout, p.TIMEOUT)

    def test_no_network_by_default(self):
        with patch.object(p, "probe") as probe, redirect_stderr(StringIO()):
            self.assertEqual(p.main([]), 2)
            probe.assert_not_called()

    def test_wrong_collection_or_item_rejected(self):
        for attr, val in (("type", "Collection"), ("id", "not-archive"), ("collection", "bad")):
            with self.subTest(attr=attr):
                data = sample()
                data[attr] = val
                with self.assertRaises(p.ArchiveBlocked):
                    p.check_archive_metadata(test_bytes(data))

    def test_empty_asset_index_is_blocked(self):
        data = sample()
        data["assets"] = {}
        with self.assertRaises(p.ArchiveBlocked):
            p.check_archive_metadata(test_bytes(data))

    def test_missing_pointer_and_bad_media_rejected(self):
        for changed in ({"type": "image/tiff"}, {"href": "https://invalid", "type": "not a mime"}):
            data = sample()
            data["assets"]["synthetic-cog"] = changed
            with self.assertRaises(p.ArchiveBlocked):
                p.check_archive_metadata(test_bytes(data))

    def test_reject_oversize_source_and_json_duplicate(self):
        with self.assertRaises(p.ArchiveBlocked):
            p.check_archive_metadata(b"z" * (p.MAX_BYTES + 1))
        with self.assertRaises(p.ArchiveBlocked):
            p.check_archive_metadata(b'{"type":"Feature","id":"a","id":"b"}')

    def test_reject_nonfinite_and_invalid_utf8(self):
        for raw in (b'{"bad":NaN}', b"\xff\xfe"):
            with self.subTest(raw=raw), self.assertRaises(p.ArchiveBlocked):
                p.check_archive_metadata(raw)

    def test_reject_media_and_declared_size(self):
        for media, size in (("text/html", None), ("application/json", "131073")):
            with self.subTest(media=media, size=size), self.assertRaises(p.ArchiveBlocked):
                p.probe(MockOpener(MockResponse(media=media, declared=size)))

    def test_redirect_not_allowed(self):
        with self.assertRaises(p.ArchiveBlocked):
            p.NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://invalid")

    def test_provider_error_text_never_echoed(self):
        with patch.object(p, "probe", side_effect=p.ArchiveBlocked("provider-secret-payload")):
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(p.main(["--live"]), 2)
            self.assertNotIn("provider-secret-payload", err.getvalue())


if __name__ == "__main__":
    unittest.main()
