# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic negative tests of exact WorldCover 10368-byte table sample."""
from __future__ import annotations

import io
import struct
import unittest
from unittest.mock import patch

from scripts import probe_esa_worldcover_tile_tables_v0 as source


def fixture(*, mutate=None):
    offsets = [24_012 + i * 512 for i in range(source.ENTRIES)]
    counts = [256 for _ in range(source.ENTRIES)]
    if mutate is not None:
        mutate(offsets, counts)
    return struct.pack("<1296I", *offsets) + struct.pack("<1296I", *counts)


class Reply(io.BytesIO):
    def __init__(self, raw=None, *, status=206, url=source.URL, headers=None):
        super().__init__(fixture() if raw is None else raw)
        self.status = status
        self.url = url
        self.headers = {
            "Content-Type": "binary/octet-stream",
            "Content-Length": str(source.SAMPLE_BYTES),
            "Content-Range": source.EXPECTED_CONTENT_RANGE,
        } if headers is None else headers
        self.read_sizes = []

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class WorldCoverTileTableTests(unittest.TestCase):
    def test_canonical_source_contract_is_reviewed(self):
        timeout, sha = source.reviewed_contract()
        self.assertEqual(timeout, 60)
        self.assertEqual(len(sha), 64)

    def test_valid_1296_pair_arrays_with_selected_block_only_report_metadata(self):
        result = source.inspect_tables(fixture())
        self.assertEqual(result["declared_tiff_blocks"], 1296)
        self.assertEqual(result["nonempty_block_count"], 1296)
        self.assertEqual(result["zero_offset_zero_count_block_count"], 0)
        self.assertTrue(result["nonoverlapping_block_ranges"])
        self.assertEqual(result["selected_block_index"], 185)
        self.assertEqual(
            result["selected_block_source_byte_range_if_present"], [118_732, 118_987]
        )
        self.assertEqual(result["selected_block_compressed_bytes_if_present"], 256)

    def test_missing_compressed_block_is_not_hallucinated(self):
        def missing(offsets, counts):
            offsets[185] = counts[185] = 0
        result = source.inspect_tables(fixture(mutate=missing))
        self.assertEqual(result["zero_offset_zero_count_block_count"], 1)
        self.assertFalse(result["selected_block_present"])
        self.assertIsNone(result["selected_block_source_byte_range_if_present"])

    def test_malformed_source_arrays_reject(self):
        cases = [
            lambda o,c: o.__setitem__(1, 0),                 # mismatched sparse marker
            lambda o,c: c.__setitem__(2, 0),                 # invalid block bytecount
            lambda o,c: o.__setitem__(3, 24_000),            # intersects metadata
            lambda o,c: o.__setitem__(4, 94_851_930),       # past source end
            lambda o,c: c.__setitem__(5, 9_000_000),        # unreasonably large block
            lambda o,c: o.__setitem__(7, o[6] + 10),        # compressed overlap
            lambda o,c: o.__setitem__(8, o[7]),             # exact duplicate range
        ]
        for index, mutation in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(source.TableSampleBlocked):
                source.inspect_tables(fixture(mutate=mutation))
        with self.assertRaises(source.TableSampleBlocked):
            source.inspect_tables(b"garbage")
        with self.assertRaises(source.TableSampleBlocked):
            source.inspect_tables(fixture() + b"x")

    def test_single_exact_source_read_and_no_byte_persistence(self):
        response = Reply()
        calls = []
        def open_request(req, timeout):
            calls.append((req.get_method(), req.full_url,
                          req.get_header("Range"),
                          req.get_header("Accept-encoding"), timeout))
            return response
        result = source.probe(open_request=open_request)
        self.assertEqual(calls, [("GET", source.URL, "bytes=13644-24011", "identity", 60)])
        self.assertEqual(response.read_sizes, [source.SAMPLE_BYTES + 1])
        self.assertEqual(result["sample_bytes"], source.SAMPLE_BYTES)
        self.assertEqual(len(result["sample_sha256"]), 64)
        self.assertFalse(result["source_bytes_persisted"])
        self.assertFalse(result["raster_pixels_downloaded"])
        self.assertFalse(result["source_wide_sha256_verified"])
        self.assertFalse(result["model_input_approved"])

    def test_bad_http_status_mime_range_size_content_encoding_or_redirect(self):
        defaults = {"Content-Type": "binary/octet-stream",
                    "Content-Length": str(source.SAMPLE_BYTES),
                    "Content-Range": source.EXPECTED_CONTENT_RANGE}
        responses = [
            Reply(status=200),
            Reply(status=403),
            Reply(url="https://evil.invalid/other.tif"),
            Reply(headers={**defaults, "Content-Type": "text/html"}),
            Reply(headers={**defaults, "Content-Length": "94851935"}),
            Reply(headers={**defaults, "Content-Range": "bytes 0-10367/94851935"}),
            Reply(headers={**defaults, "Content-Range": "bytes 13644-24011/94851936"}),
            Reply(headers={**defaults, "Content-Encoding": "gzip"}),
            Reply(raw=fixture()[:-1]),
            Reply(raw=fixture() + b"extra"),
        ]
        for response in responses:
            with self.subTest(status=response.status, headers=response.headers):
                with self.assertRaises(source.TableSampleBlocked):
                    source.probe(open_request=lambda req, timeout: response)

    def test_unauthorized_path_or_opt_in_rejected(self):
        with patch.object(source, "URL", "https://evil.invalid/other"):
            with self.assertRaises(source.TableSampleBlocked):
                source.reviewed_contract()
        with self.assertRaises(SystemExit) as caught:
            source.main([])
        self.assertNotEqual(caught.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
