# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic negative tests: no provider network calls or source bytes."""
from __future__ import annotations

import io
import json
import struct
import unittest
from unittest.mock import patch

from scripts import probe_esa_worldcover_tiff_header_v0 as wc


def tiff_bytes() -> bytes:
    raw = bytearray(wc.BYTES)
    raw[:4] = bytes((73, 73, 42, 0))  # Little-endian classic TIFF.
    struct.pack_into("<I", raw, 4, 8)
    struct.pack_into("<H", raw, 8, 1)
    struct.pack_into("<HHII", raw, 10, 256, 4, 1, 34560)  # image width tag only.
    struct.pack_into("<I", raw, 22, 0)
    return bytes(raw)


def big_tiff_bytes() -> bytes:
    raw = bytearray(wc.BYTES)
    raw[:4] = bytes((73, 73, 43, 0))
    struct.pack_into("<HHQ", raw, 4, 8, 0, 16)
    struct.pack_into("<Q", raw, 16, 0)
    return bytes(raw)


class Response(io.BytesIO):
    def __init__(self, data=None, *, status=206, url=wc.URL, headers=None):
        super().__init__(tiff_bytes() if data is None else data)
        self.status = status
        self.url = url
        self.headers = {
            "Content-Type": "binary/octet-stream",
            "Content-Length": "4096",
            "Content-Range": wc.CONTENT_RANGE,
        } if headers is None else headers
        self.bytes_requested = []

    def geturl(self):
        return self.url

    def read(self, n=-1):
        self.bytes_requested.append(n)
        return super().read(n)


class WorldCoverRangeTests(unittest.TestCase):
    def test_real_checked_in_reviewed_contract(self):
        timeout, digest = wc.reviewed_contract()
        self.assertEqual(timeout, 60)
        self.assertEqual(len(digest), 64)

    def test_valid_exact_range_and_sample_hash_without_byte_leakage(self):
        calls = []
        response = Response()
        def mock_open(req, timeout):
            calls.append((req.full_url, req.get_method(),
                          req.get_header("Range"),
                          req.get_header("Accept-encoding"), timeout))
            return response
        rec = wc.probe(open_request=mock_open)
        self.assertEqual(calls, [(wc.URL, "GET", "bytes=0-4095", "identity", 60)])
        self.assertEqual(response.bytes_requested, [wc.BYTES + 1])
        self.assertEqual(rec["sample_bytes"], wc.BYTES)
        self.assertEqual(rec["tiff_flavour"], "TIFF")
        self.assertTrue(rec["first_ifd_fully_within_sample"])
        self.assertEqual(rec["first_ifd_count_if_visible"], 1)
        self.assertFalse(rec["full_original_sha256_verified"])
        self.assertFalse(rec["cog_layout_verified"])
        self.assertFalse(rec["crs_verified"])
        self.assertFalse(rec["raster_values_inspected"])
        self.assertFalse(rec["external_bytes_persisted"])
        self.assertFalse(rec["model_input_approved"])
        self.assertNotIn("34560", json.dumps(rec))
        self.assertEqual(len(rec["sample_sha256"]), 64)

    def test_big_tiff_magic_and_ifd_range(self):
        sample = wc.inspect_tiff_header(big_tiff_bytes())
        self.assertEqual(sample["tiff_flavour"], "BigTIFF")
        self.assertTrue(sample["first_ifd_fully_within_sample"])
        self.assertEqual(sample["first_ifd_count_if_visible"], 0)

    def test_first_ifd_beyond_sample_remains_unknown(self):
        raw = bytearray(tiff_bytes())
        struct.pack_into("<I", raw, 4, wc.BYTES + 1024)
        sample = wc.inspect_tiff_header(bytes(raw))
        self.assertFalse(sample["first_ifd_fully_within_sample"])
        self.assertIsNone(sample["first_ifd_count_if_visible"])

    def test_reject_response_status_length_range_media_and_redirect(self):
        normal = {"Content-Type": "binary/octet-stream",
                  "Content-Length": "4096", "Content-Range": wc.CONTENT_RANGE}
        responses = [
            Response(status=200),  # Server ignored Range: never read full body.
            Response(status=403),
            Response(url="https://evil.invalid/other"),
            Response(headers={**normal, "Content-Length": "94851935"}),
            Response(headers={**normal, "Content-Range": "bytes 1-4096/94851935"}),
            Response(headers={**normal, "Content-Range": "bytes 0-4095/94851936"}),
            Response(headers={**normal, "Content-Type": "text/html"}),
            Response(headers={**normal, "Content-Encoding": "gzip"}),
            Response(data=b"wrong" * 100),
            Response(data=tiff_bytes() + b"x"),
        ]
        for response in responses:
            with self.subTest(status=response.status, headers=response.headers):
                with self.assertRaises(wc.HeaderBlocked):
                    wc.probe(open_request=lambda req, timeout: response)

    def test_wrong_tiff_magic_and_invalid_directory_blocked(self):
        invalid = [
            b"html" + bytes(wc.BYTES - 4),
            bytes(wc.BYTES),
            bytes((73, 73, 42, 0)) + bytes(wc.BYTES - 4),
        ]
        for data in invalid:
            with self.subTest(prefix=data[:8]), self.assertRaises(wc.HeaderBlocked):
                wc.inspect_tiff_header(data)

    def test_no_alternative_url_or_unreviewed_contract(self):
        with patch.object(wc, "URL", "https://different.invalid/other.tif"):
            with self.assertRaises(wc.HeaderBlocked):
                wc.reviewed_contract()

    def test_explicit_network_opt_in(self):
        with self.assertRaises(SystemExit) as e:
            wc.main([])
        self.assertNotEqual(e.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
