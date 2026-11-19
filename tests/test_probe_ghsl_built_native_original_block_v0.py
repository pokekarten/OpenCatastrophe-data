# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only. No external original-data reads in PR CI."""
from __future__ import annotations

import io
import struct
import unittest
from unittest.mock import patch
import zlib

from scripts import probe_ghsl_built_native_original_block_v0 as p


class Reply(io.BytesIO):
    def __init__(self, raw: bytes, *, url: str, headers: dict,
                 status: int = 206):
        super().__init__(raw)
        self.url = url
        self.status = status
        self.headers = headers
        self.read_lengths = []

    def geturl(self):
        return self.url

    def read(self, length=-1):
        self.read_lengths.append(length)
        return super().read(length)


def response(product="surface", start=0, length=p.PREFIX_BYTES,
             *, size=None, status=206, bad_url=None, headers=None):
    cfg = p.PRODUCTS[product]
    exact = {
        "Content-Range": f"bytes {start}-{start+length-1}/{cfg['object_bytes']}",
        "Content-Length": str(length),
        "Content-Type": "binary/octet-stream",
        "Content-Encoding": "identity",
    }
    if headers:
        exact.update(headers)
    data = b"X" * length if size is None else b"X" * size
    return Reply(data, url=bad_url or p.ROOT+p.FILES[product],
                 headers=exact, status=status)


class GHSLNativeOriginalTests(unittest.TestCase):
    def test_exact_original_header_range_and_no_redirect_or_bulk_get(self):
        for product in p.PRODUCTS:
            with self.subTest(product=product):
                reply = response(product=product)
                seen = []
                def opener(req, timeout):
                    seen.append((req.get_method(), req.full_url,
                                 req.get_header("Range"), timeout))
                    return reply
                data = p._fetch_range(product, 0, p.PREFIX_BYTES, opener=opener)
                self.assertEqual(len(data), p.PREFIX_BYTES)
                self.assertEqual(seen, [(
                    "GET", p.ROOT+p.FILES[product], "bytes=0-32767", 45,
                )])
                self.assertEqual(reply.read_lengths, [p.PREFIX_BYTES+1])
                for start, n in ((0, 4096), (0, 1_000_000), (5, 1000),
                                 (p.PRODUCTS[product]["native_block_offset"], 600_001)):
                    with self.assertRaises(p.GHSLNativeBlocked):
                        p._fetch_range(product, start, n, opener=opener)
        with self.assertRaises(p.GHSLNativeBlocked):
            p._fetch_range("other", 0, p.PREFIX_BYTES)

    def test_source_http_semantics_fail_closed(self):
        cfg = p.PRODUCTS["surface"]
        responses = [
            response(status=200),
            response(bad_url="https://evil.invalid/payload"),
            response(headers={"Content-Type": "text/html"}),
            response(headers={"Content-Encoding": "gzip"}),
            response(headers={"Content-Range": "bytes 0-32767/1"}),
            response(headers={"Content-Length": "100000000"}),
            response(size=p.PREFIX_BYTES-1),
            response(size=p.PREFIX_BYTES+1),
        ]
        for reply in responses:
            with self.subTest(status=reply.status, headers=reply.headers):
                with self.assertRaises(p.GHSLNativeBlocked):
                    p._fetch_range("surface", 0, p.PREFIX_BYTES,
                                   opener=lambda req, timeout: reply)

    def test_exact_native_block_request_range(self):
        cfg = p.PRODUCTS["volume"]
        start, n = cfg["native_block_offset"], cfg["native_block_bytes"]
        reply = response(product="volume", start=start, length=n)
        data = p._fetch_range("volume", start, n,
                              opener=lambda req, timeout: reply)
        self.assertEqual(len(data), n)
        self.assertEqual(reply.read_lengths, [n+1])

    def test_bounded_original_uint32_32x32_source_aggregate(self):
        image = bytearray(p.NATIVE_BYTES)
        expected_positive = 0
        for y in range(p.WINDOW_LOCAL_Y, p.WINDOW_LOCAL_Y+p.WINDOW_SIDE):
            for x in range(p.WINDOW_LOCAL_X, p.WINDOW_LOCAL_X+p.WINDOW_SIDE):
                col = x-p.WINDOW_LOCAL_X
                value = 0 if col < 8 else (0xffffffff if col == 8 else 120)
                struct.pack_into("<I", image, (y*p.TILE_SIDE+x)*4, value)
                if col > 8:
                    expected_positive += 1
        compressed = zlib.compress(image, level=1)
        result = p.aggregate_native_block(
            compressed, expected_bytes=len(compressed))
        self.assertEqual(result["fixed_window_zero_cells"], 256)
        self.assertEqual(result["fixed_window_potential_uint32_max_sentinel_cells"], 32)
        self.assertEqual(result["fixed_window_positive_non_sentinel_cells"],
                         expected_positive)
        self.assertEqual(result["fixed_window_positive_sum_raw_source_units"],
                         expected_positive*120)
        self.assertEqual(result["fixed_window_min_positive_value"], 120)
        self.assertEqual(result["fixed_window_max_positive_value"], 120)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["uint32_max_nodata_semantics_approved"])
        self.assertNotIn("raw_pixels", result)

    def test_corrupt_truncated_trailing_and_inflation_bombs_rejected(self):
        good = zlib.compress(bytes(p.NATIVE_BYTES))
        cases = [
            b"plain-text",
            good[:-1],
            good+b"EXTRA",
            zlib.compress(bytes(p.NATIVE_BYTES+4)),
            zlib.compress(bytes(4)),
        ]
        for blob in cases:
            with self.subTest(size=len(blob)):
                with self.assertRaises(p.GHSLNativeBlocked):
                    p.aggregate_native_block(blob, expected_bytes=len(blob))
        with self.assertRaises(p.GHSLNativeBlocked):
            p.aggregate_native_block(good, expected_bytes=len(good)+1)

    def test_live_requires_independent_pinned_header_before_block_fetch(self):
        with patch.object(p, "_fetch_range", return_value=b"X"*p.PREFIX_BYTES) as fetch:
            with self.assertRaises(p.GHSLNativeBlocked):
                p.run_probe("surface")
            fetch.assert_called_once_with("surface", 0, p.PREFIX_BYTES)

    def test_no_automatic_network_without_explicit_live(self):
        with self.assertRaises(SystemExit) as ctx:
            p.main(["--product", "surface"])
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
