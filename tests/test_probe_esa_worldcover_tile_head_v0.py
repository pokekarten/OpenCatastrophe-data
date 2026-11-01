# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, no-network regression for one reviewed WorldCover HEAD request."""
from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import probe_esa_worldcover_tile_head_v0 as wc


class Response:
    def __init__(self, headers=None, *, status=200, url=wc.URL):
        self.headers = headers or {
            "Content-Type": "image/tiff", "Content-Length": "25000000",
            "ETag": '"untrusted-transmission-etag"',
        }
        self.status = status
        self.url = url

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        raise AssertionError("HEAD probe must never read source raster bytes")


class WorldCoverHeadTests(unittest.TestCase):
    def test_reviewed_canonical_contract_is_head_only(self):
        timeout, sha = wc.validate_reviewed_contract()
        self.assertLessEqual(timeout, 60)
        self.assertEqual(len(sha), 64)

    def test_single_fixed_head_returns_transport_receipt_only(self):
        calls = []
        def open_request(req, timeout):
            calls.append((req.full_url, req.get_method(), timeout))
            return Response()
        receipt = wc.probe(open_request=open_request)
        self.assertEqual(calls, [(wc.URL, "HEAD", 60)])
        self.assertEqual(receipt["declared_object_bytes"], 25000000)
        self.assertEqual(receipt["source_raster_bytes_downloaded"], 0)
        self.assertFalse(receipt["cog_structure_validated"])
        self.assertFalse(receipt["original_object_sha256_verified"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertNotIn("untrusted-transmission-etag", str(receipt))
        self.assertEqual(len(receipt["request_sha256"]), 64)

    def test_rejects_wrong_media_size_redirect_status(self):
        bad = [
            Response({"Content-Type": "text/html", "Content-Length": "12"}),
            Response({"Content-Type": "image/tiff", "Content-Length": "nan"}),
            Response({"Content-Type": "image/tiff", "Content-Length": "0"}),
            Response({"Content-Type": "image/tiff", "Content-Length": str(5*1024**3)}),
            Response(status=403),
            Response(url="https://wrong.invalid/path"),
            Response({"Content-Type": "image/tiff", "Content-Length": "1",
                      "ETag": "x" * 300}),
        ]
        for response in bad:
            with self.subTest(status=response.status, headers=response.headers):
                with self.assertRaises(wc.WorldCoverProbeBlocked):
                    wc.probe(open_request=lambda req, timeout: response)

    def test_fixed_canonical_url_cannot_be_replaced(self):
        with patch.object(wc, "URL", "https://evil.invalid/object.tif"):
            with self.assertRaises(wc.WorldCoverProbeBlocked):
                wc.validate_reviewed_contract()

    def test_explicit_live_opt_in_is_mandatory(self):
        with self.assertRaises(SystemExit) as ctx:
            wc.main([])
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
