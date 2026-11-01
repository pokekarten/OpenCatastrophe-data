# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original TIFF class block decoding and HTTP safety tests."""
from __future__ import annotations

import io
import unittest
import zlib
from unittest.mock import patch

from scripts import probe_esa_worldcover_classified_block185_v0 as wc


class Reply(io.BytesIO):
    status = 206
    def __init__(self, raw, *, status=206, url=wc.URL, headers=None):
        super().__init__(raw)
        self.status = status
        self.url = url
        self.headers = {
            "Content-Type": "binary/octet-stream",
            "Content-Length": "4096",
            "Content-Range": f"bytes 0-4095/{wc.SOURCE_TOTAL}",
        } if headers is None else headers
        self.read_sizes = []
    def geturl(self):
        return self.url
    def read(self, n=-1):
        self.read_sizes.append(n)
        return super().read(n)


class OneWorldCoverOriginalBlockTests(unittest.TestCase):
    def test_real_frozen_one_block_source_access_contract(self):
        timeout, sha = wc.reviewed_contract()
        self.assertLessEqual(timeout, 60)
        self.assertEqual(len(sha), 64)

    def test_one_frozen_4096_byte_get_and_reject_arbitrary_ranges(self):
        response = Reply(bytes(4096))
        seen = []
        def open_request(req, timeout):
            seen.append((req.get_method(), req.full_url,
                         req.get_header("Range"),
                         req.get_header("Accept-encoding"), timeout))
            return response
        raw = wc._read_one(bounds=wc.HEADER_RANGE,
                           open_request=open_request, timeout=30)
        self.assertEqual(len(raw), 4096)
        self.assertEqual(seen, [("GET", wc.URL, "bytes=0-4095", "identity", 30)])
        self.assertEqual(response.read_sizes, [4097])
        with self.assertRaisesRegex(wc.PixelBlockBlocked, "unreviewed"):
            wc._read_one(bounds=(4096, 5000),
                         open_request=open_request, timeout=30)

    def test_http_bad_length_status_range_mime_redirect_and_short_body(self):
        good = {"Content-Type": "binary/octet-stream", "Content-Length": "4096",
                "Content-Range": f"bytes 0-4095/{wc.SOURCE_TOTAL}"}
        responses = [
            Reply(bytes(4096), status=200),
            Reply(bytes(4096), status=404),
            Reply(bytes(4096), url="https://evil.invalid/other"),
            Reply(bytes(4096), headers={**good, "Content-Type": "text/html"}),
            Reply(bytes(4096), headers={**good, "Content-Length": "94851935"}),
            Reply(bytes(4096), headers={**good, "Content-Range": "bytes 0-4095/1"}),
            Reply(bytes(4096), headers={**good, "Content-Encoding": "gzip"}),
            Reply(bytes(4095)),
            Reply(bytes(4097)),
        ]
        for response in responses:
            with self.subTest(status=response.status, header=response.headers):
                with self.assertRaises(wc.PixelBlockBlocked):
                    wc._read_one(bounds=wc.HEADER_RANGE,
                                 open_request=lambda req, timeout: response,
                                 timeout=30)

    def test_valid_original_class_bytes_with_predictor_one(self):
        plain = bytes([50]) * wc.UNCOMPRESSED_LIMIT
        blob = zlib.compress(plain)
        result = wc.decode_original_block(
            blob, predictor=1, expected_compressed_bytes=len(blob))
        self.assertEqual(result["class_code_counts"], {"50": 1024*1024})
        self.assertEqual(result["synthetic_test_location_class_code"], 50)
        self.assertTrue(result["class_code_whitelist_verified"])
        self.assertEqual(len(result["decoded_block_sha256"]), 64)

    def test_tiff_horizontal_prediction_two_is_reversed_per_row(self):
        # Every image row: one absolute 50 byte then 1023 deltas of 0.
        line = bytes([50]) + bytes(1023)
        blob = zlib.compress(line * 1024)
        result = wc.decode_original_block(
            blob, predictor=2, expected_compressed_bytes=len(blob))
        self.assertEqual(result["class_code_counts"], {"50": wc.UNCOMPRESSED_LIMIT})
        self.assertEqual(result["synthetic_test_location_class_code"], 50)

    def test_bad_zlib_unsupported_classes_and_bomb_bounds_block(self):
        valid = zlib.compress(bytes([10]) * wc.UNCOMPRESSED_LIMIT)
        invalid_class = zlib.compress(bytes([255]) * wc.UNCOMPRESSED_LIMIT)
        oversize = zlib.compress(bytes(wc.UNCOMPRESSED_LIMIT + 1))
        cases = [
            (valid, 3),
            (valid[:-1], 1),
            (b"not-zlib", 1),
            (invalid_class, 1),
            (oversize, 1),
        ]
        for payload, predictor in cases:
            with self.subTest(predictor=predictor, length=len(payload)):
                with self.assertRaises(wc.PixelBlockBlocked):
                    wc.decode_original_block(
                        payload, predictor=predictor,
                        expected_compressed_bytes=len(payload))
        with self.assertRaises(wc.PixelBlockBlocked):
            wc.decode_original_block(valid, predictor=1,
                                     expected_compressed_bytes=len(valid)+1)

    def test_live_opt_in_is_mandatory_and_host_cannot_change(self):
        with self.assertRaises(SystemExit) as ctx:
            wc.main([])
        self.assertNotEqual(ctx.exception.code, 0)
        with patch.object(wc, "URL", "https://evil.invalid/not-reviewed"):
            with self.assertRaises(wc.PixelBlockBlocked):
                wc.reviewed_contract()


if __name__ == "__main__":
    unittest.main()
