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
from urllib.request import build_opener

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

    def test_default_live_acquisition_blocked_before_network(self):
        with self.assertRaisesRegex(subject.Blocked, "documented_only"):
            subject.verify(("radar_metadata",))
        with self.assertRaisesRegex(subject.Blocked, "documented_only"):
            subject.build_reviewed_opener()

    def test_standard_library_opener_blocked_before_request(self):
        opener = build_opener()
        with patch.object(opener, "open") as open_request:
            with self.assertRaisesRegex(subject.Blocked, "documented_only"):
                subject.acquire_one("radar_metadata", self.target, opener)
            open_request.assert_not_called()
        self.assertFalse(self.target.exists())

    def test_local_batch_receipt_is_not_live_and_does_not_copy_files(self):
        first = b"field,value\nA,1\n"
        second = b"field,value\nB,2\n"
        other = self.target.with_name("second.csv")
        self.target.write_bytes(first)
        other.write_bytes(second)
        pins = {
            "radar_metadata": (11064781, hashlib.md5(first, usedforsecurity=False).hexdigest(), "csv", 100),
            "damage_metadata": (11064767, hashlib.md5(second, usedforsecurity=False).hexdigest(), "csv", 100),
        }
        with patch.dict(existing.ASSETS, pins), patch.object(subject, "build_reviewed_opener") as live:
            out = subject.verify_local((("radar_metadata", self.target), ("damage_metadata", other)))
        live.assert_not_called()
        self.assertEqual(out["provider_requests_performed"], 0)
        self.assertEqual([x["sha256"] for x in out["receipts"]],
                         [hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest()])
        self.assertFalse(out["scientific_admission"])
        self.assertFalse(out["source_files_copied_by_verifier"])
        self.assertEqual(self.target.read_bytes(), first)
        self.assertEqual(other.read_bytes(), second)

    def test_local_selection_and_parser_fail_closed(self):
        for bad in ((), (("wrong", self.target),),
                    (("radar_metadata", self.target), ("radar_metadata", self.target))):
            with self.assertRaises(subject.Blocked):
                subject.verify_local(bad)
        for value in ("radar_metadata", "radar_metadata=", "wrong=somewhere"):
            with self.assertRaises(subject.Blocked):
                subject.parse_local_files([value])
        self.assertEqual(subject.parse_local_files(["radar_metadata=a=b.csv"]),
                         (("radar_metadata", Path("a=b.csv")),))

    def test_fixed_original_urls(self):
        self.assertEqual(len(subject.SOURCE_FILES), 8)
        for asset in subject.SOURCE_FILES:
            if asset == "code_zip":
                self.assertEqual(subject.source_url(asset),
                    "https://zenodo.org/api/records/12784190/files/raphael-portmann/202403_crop_hail_damage_footprint-1.0.zip/content")
            else:
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
