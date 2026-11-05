# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic no-network source acquisition tests; no original dataset bytes."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_runners import swiss_crop_hail_zenodo_original_acquire_v0 as subject
from research_runners import swiss_crop_hail_asset_preflight_v0 as existing


class Response:
    status = 200

    def __init__(self, body, url, headers=None):
        self.buffer = io.BytesIO(body)
        self.url = url
        self.headers = headers if headers is not None else {"Content-Length": str(len(body))}

    def __enter__(self): return self
    def __exit__(self, *_): self.buffer.close()
    def read(self, amount): return self.buffer.read(amount)
    def geturl(self): return self.url


class Opener:
    def __init__(self, response): self.response = response
    def open(self, request, timeout):
        assert timeout == 30
        assert request.full_url.startswith("https://zenodo.org/records/")
        return self.response


class OriginalAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name) / "original.bin"
        self.url = subject.source_url("radar_metadata")

    def test_fixed_original_urls(self):
        self.assertEqual(len(subject.SOURCE_FILES), 7)
        for asset in subject.SOURCE_FILES:
            self.assertTrue(subject.source_url(asset).startswith(
                "https://zenodo.org/records/" + str(existing.ASSETS[asset][0]) + "/files/"))

    def test_no_arbitrary_host_or_asset(self):
        with self.assertRaises(subject.Blocked): subject.source_url("random")
        for url in ["http://zenodo.org/foo", "https://zenodo.org.evil.test/foo",
                    "https://foo.zenodo.org/foo", "https://zenodo.org:444/foo"]:
            with self.subTest(url=url):
                with self.assertRaises(subject.Blocked):
                    subject.require_original_host(url)

    def test_good_synthetic_replay_and_negative_model_flags(self):
        content = b"test,value\nA,1\n"
        published = hashlib.md5(content, usedforsecurity=False).hexdigest()
        with patch.dict(existing.ASSETS, {"radar_metadata": (11064781, published, "csv", 100)}):
            result = subject.verify(("radar_metadata",),
                     opener=Opener(Response(content, self.url)))
        self.assertEqual(result["receipts"][0]["sha256"], hashlib.sha256(content).hexdigest())
        self.assertFalse(result["scientific_admission"])
        self.assertFalse(result["source_bytes_retained"])

    def test_publisher_hash_mismatch_blocks(self):
        with self.assertRaisesRegex(subject.Blocked, "MD5"):
            subject.verify(("radar_metadata",),
                opener=Opener(Response(b"csv,wrong\n", self.url)))

    def test_cross_host_final_redirect_blocks(self):
        with self.assertRaisesRegex(subject.Blocked, "original"):
            subject.acquire_one("radar_metadata", self.target,
                Opener(Response(b"csv,ok\n", "https://another.example/files")))

    def test_declared_and_stream_overflow_block(self):
        for headers, data in [
            ({"Content-Length": "9999999"}, b"csv,ok\n"),
            ({"Content-Length": "nonnumeric"}, b"csv,ok\n"),
            ({}, b"x" * (existing.ASSETS["radar_metadata"][3] + 1)),
        ]:
            with self.subTest(headers=headers):
                with self.assertRaises(subject.Blocked):
                    subject.acquire_one("radar_metadata", self.target, Opener(Response(data, self.url, headers)))
                self.target.unlink(missing_ok=True)

    def test_truncation_and_empty_blocks(self):
        for headers, data in [({"Content-Length": "99"}, b"csv,ok\n"), ({}, b"")]:
            with self.subTest(headers=headers):
                with self.assertRaisesRegex(subject.Blocked, "empty or truncated"):
                    subject.acquire_one("radar_metadata", self.target,
                        Opener(Response(data, self.url, headers)))
                self.target.unlink(missing_ok=True)

    def test_selection_and_aggregate_guards(self):
        for assets in [(), ("radar_metadata", "radar_metadata"), ("wrong",)]:
            with self.assertRaises(subject.Blocked):
                subject.verify(assets, opener=None)
        with patch.object(subject, "MAX_TOTAL", 1):
            with self.assertRaisesRegex(subject.Blocked, "aggregate"):
                subject.verify(("radar_metadata",), opener=None)


if __name__ == "__main__":
    unittest.main()
