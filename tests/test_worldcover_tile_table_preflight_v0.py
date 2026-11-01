# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic TIFF 1296-block table pointer preflight: absolutely no network."""
from __future__ import annotations

import io
import struct
import unittest

from scripts.inspect_worldcover_tile_table_preflight_v0 import (
    TileTableBlocked, EXPECTED_BLOCKS, TABLE_BYTES, inspect_tile_table_locations,
)
from scripts.probe_esa_worldcover_tiff_header_v0 import inspect_tiff_header, probe
from scripts.probe_esa_worldcover_tiff_header_v0 import URL, CONTENT_RANGE


def fake_first_ifd(*, offsets=10000, bytecounts=17000) -> bytes:
    raw = bytearray(4096)
    raw[:4] = bytes((73, 73, 42, 0))
    struct.pack_into("<I", raw, 4, 192)
    tags = [
        (256, 4, 1, 36000),
        (257, 4, 1, 36000),
        (259, 3, 1, 8),
        (277, 3, 1, 1),
        (322, 4, 1, 1024),
        (323, 4, 1, 1024),
        (324, 4, EXPECTED_BLOCKS, offsets),
        (325, 4, EXPECTED_BLOCKS, bytecounts),
    ]
    tags.extend((400 + i, 3, 1, 1) for i in range(13))
    struct.pack_into("<H", raw, 192, len(tags))
    for i, entry in enumerate(tags):
        struct.pack_into("<HHII", raw, 194 + 12 * i, *entry)
    return bytes(raw)


class FakePartialResponse(io.BytesIO):
    status = 206
    def __init__(self, raw):
        super().__init__(raw)
        self.headers = {
            "Content-Type": "binary/octet-stream",
            "Content-Length": "4096",
            "Content-Range": CONTENT_RANGE,
        }
    def geturl(self):
        return URL


class TileTablePreflightTests(unittest.TestCase):
    def test_exact_original_header_semantics_yield_bounded_table_requests_not_data(self):
        raw = fake_first_ifd()
        header = inspect_tiff_header(raw)
        result = inspect_tile_table_locations(raw, header=header)
        self.assertEqual(result["expected_tiff_blocks"], 1296)
        self.assertEqual(result["blocks_per_axis"], 36)
        self.assertEqual(result["table_bytes_each"], 5184)
        self.assertEqual(result["tile_offsets_table_original_byte_range"], [10000, 15183])
        self.assertEqual(result["tile_bytecounts_table_original_byte_range"], [17000, 22183])
        self.assertFalse(result["tile_offsets_validated"])
        self.assertFalse(result["individual_block_bytecounts_validated"])
        self.assertFalse(result["tile_pixels_downloaded"])
        self.assertEqual(result["table_original_bytes_downloaded"], 0)
        self.assertTrue(result["next_probe_requires_separate_review"])

    def test_one_original_header_probing_request_with_opt_in_table_preflight(self):
        calls = []
        def open_request(req, timeout):
            calls.append((req.full_url, req.get_method(), req.get_header("Range")))
            return FakePartialResponse(fake_first_ifd())
        evidence = probe(open_request=open_request, tile_table_preflight=True)
        self.assertEqual(calls, [(URL, "GET", "bytes=0-4095")])
        self.assertEqual(evidence["tile_table_entries_per_array"], 1296)
        self.assertFalse(evidence["raster_values_inspected"])
        self.assertFalse(evidence["model_input_approved"])
        self.assertEqual(evidence["table_original_bytes_downloaded"], 0)
        self.assertEqual(evidence["sample_bytes"], 4096)

    def test_missing_duplicate_wrong_types_counts_and_bad_pointers_reject(self):
        def alter(raw, tag, dtype=None, count=None, ptr=None, replace_tag=None):
            b = bytearray(raw)
            for i in range(21):
                start = 194 + i*12
                actual_tag, old_dtype, old_count, old_ptr = struct.unpack_from("<HHII", b, start)
                if actual_tag == tag:
                    struct.pack_into("<HHII", b, start,
                        actual_tag if replace_tag is None else replace_tag,
                        old_dtype if dtype is None else dtype,
                        old_count if count is None else count,
                        old_ptr if ptr is None else ptr)
                    return bytes(b)
            raise AssertionError("missing original tag")
        normal = fake_first_ifd()
        cases = [
            alter(normal, 325, replace_tag=326),
            alter(normal, 325, replace_tag=324),
            alter(normal, 324, dtype=3),
            alter(normal, 325, count=1295),
            alter(normal, 324, ptr=200),
            alter(normal, 325, ptr=10000),
            alter(normal, 325, ptr=11000),
            alter(normal, 324, ptr=94_851_934),
            alter(normal, 325, ptr=17001),
        ]
        reviewed_header = inspect_tiff_header(normal)
        for i, raw in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(TileTableBlocked):
                inspect_tile_table_locations(raw, header=reviewed_header)

    def test_header_mismatch_and_bad_size_fail_closed(self):
        normal = fake_first_ifd()
        with self.assertRaises(TileTableBlocked):
            inspect_tile_table_locations(normal, header={})
        bad = bytearray(normal)
        bad[0] = 77
        with self.assertRaises(TileTableBlocked):
            inspect_tile_table_locations(bytes(bad), header={})
        with self.assertRaises(TileTableBlocked):
            inspect_tile_table_locations(normal[:-1], header={})
        hdr = inspect_tiff_header(normal)
        hdr["tile_width_if_inline"] = 512
        with self.assertRaises(TileTableBlocked):
            inspect_tile_table_locations(normal, header=hdr)


if __name__ == "__main__":
    unittest.main()
