# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original WRI vs derived Physrisk second-window regression checks."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import (
    PixelGateError, compare_pixels,
)
from research_runners.wri_physrisk_coastal_second_window_preflight_v0 import (
    COMPLETE_BLOCK_SHA256, DIGEST, FIRST_COL, HTTP_RANGES, NCOLS, PROFILE,
    RETURN_PERIOD, RETURN_PERIOD_INDEX, ROW, TIFF_STRIP_BYTES,
    ZARR_BLOCK_INDEX, ZARR_BLOCK_NEXT_OFFSET, ZARR_BLOCK_OFFSET,
    ZARR_UNCOMPRESSED_BLOCK_SIZE, inspect_real_paired_ranges,
    parse_blosc_block, read_exact_range,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_second_window():
    """Build 1,000 invented Float32 cells at the same spatial + Blosc indices."""
    row = bytearray(43200 * 4)
    streams = [bytearray(131072) for _ in range(4)]
    scalar_start = ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4)
    for i in range(NCOLS):
        if i < 72:
            source = -9999.0
            derived = float("nan")
        elif i < 72 + 594:
            source = derived = 0.0
        else:
            source = derived = 0.125 + (i - 72 - 594) / 1000.0
        struct.pack_into("<f", row, (FIRST_COL + i) * 4, source)
        encoded = struct.pack("<f", derived)
        position = (RETURN_PERIOD_INDEX * 1000 + ROW % 1000) * 1000 + i - scalar_start
        for channel in range(4):
            streams[channel][position] = encoded[channel]
    return bytes(row), tuple(bytes(channel) for channel in streams)


class SecondWindowTests(unittest.TestCase):
    def test_region_period_and_bounded_ranges_are_independent(self):
        self.assertEqual(RETURN_PERIOD, 100)
        self.assertEqual(ROW, 8100)
        self.assertEqual(FIRST_COL, 32000)
        self.assertEqual(NCOLS, 1000)
        self.assertNotEqual(PROFILE, "wri-physrisk-2yr-coastal-1000-pixel-paired-strip-v0")
        self.assertEqual(ZARR_BLOCK_NEXT_OFFSET - ZARR_BLOCK_OFFSET, 85755)
        self.assertEqual(sum(HTTP_RANGES[x][2] - HTTP_RANGES[x][1] + 1
                             for x in ("zarr_part0", "zarr_part1", "zarr_part2")), 85755)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", COMPLETE_BLOCK_SHA256))
        for key, digest in DIGEST.items():
            with self.subTest(key=key):
                self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", digest))
                self.assertTrue(HTTP_RANGES[key][2] >= HTTP_RANGES[key][1])
        self.assertEqual(TIFF_STRIP_BYTES, 4291)

    def test_second_window_float32_categories_pair_exactly(self):
        row, streams = synthetic_second_window()
        got = compare_pixels(row, streams, FIRST_COL, NCOLS,
                             RETURN_PERIOD_INDEX * 1000 + ROW % 1000,
                             1000, ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4))
        self.assertEqual(got["source_nodata_to_derived_nan"], 72)
        self.assertEqual(got["source_zero_exact"], 594)
        self.assertEqual(got["source_positive_exact"], 334)
        self.assertEqual(got["paired_cells"], 1000)
        self.assertEqual(got["mismatches"], 0)
        self.assertEqual(got["other_source_values"], 0)

    def test_second_window_nodata_to_zero_or_positive_drift_fails(self):
        row, original = synthetic_second_window()
        start = (RETURN_PERIOD_INDEX * 1000 + ROW % 1000) * 1000 - (
            ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4))
        mutated = [bytearray(channel) for channel in original]
        for k, value in enumerate(struct.pack("<f", 0.0)):
            mutated[k][start] = value
        wrong = compare_pixels(row, tuple(bytes(ch) for ch in mutated),
                               FIRST_COL, NCOLS, 5100, 1000,
                               ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4))
        self.assertEqual(wrong["mismatches"], 1)
        shifted = [bytearray(channel) for channel in original]
        for k, value in enumerate(struct.pack("<f", 123.0)):
            shifted[k][start + 72 + 594] = value
        wrong = compare_pixels(row, tuple(bytes(ch) for ch in shifted),
                               FIRST_COL, NCOLS, 5100, 1000,
                               ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4))
        self.assertEqual(wrong["mismatches"], 1)

    def test_out_of_range_or_wrong_geometry_fails(self):
        row, streams = synthetic_second_window()
        for scalar_row, ncols in ((5101, 1000), (0, 1000), (5100, 1001)):
            with self.subTest(scalar_row=scalar_row, ncols=ncols):
                with self.assertRaises(PixelGateError):
                    compare_pixels(row, streams, FIRST_COL, ncols, scalar_row,
                                   1000, ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4))
        # The original source must never be overwritten or confused with metadata.
        with self.assertRaises(PixelGateError):
            inspect_real_paired_ranges({})

    def test_bad_blosc_header_and_block_boundaries_block(self):
        with self.assertRaisesRegex(PixelGateError, "invalid Blosc metadata"):
            parse_blosc_block(b"", b"")
        bad_header = bytearray(4096)
        struct.pack_into("<BBBBIII", bad_header, 0, 2, 1, 33, 4,
                         36000000, 524288, 2375870)
        with self.assertRaises(PixelGateError):
            parse_blosc_block(bytes(bad_header), b"x" * 85755)
        with self.assertRaises(PixelGateError):
            parse_blosc_block(bytes(bad_header), b"x" * 85754)

    def test_exact_hash_enforcement_on_partial_response(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "source.bin"
            for payload in (b"", b"1234", b"invalid"):
                src.write_bytes(payload)
                with self.subTest(payload=payload):
                    with self.assertRaises(PixelGateError):
                        read_exact_range(src, "tiff_offset")
            with self.assertRaises(PixelGateError):
                read_exact_range(src, "unknown")

    def test_cli_cannot_overwrite_any_original_source(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            sources = {key: p / key for key in DIGEST}
            for path in sources.values():
                path.write_bytes(b"synthetic, not original")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_physrisk_coastal_second_window_preflight_v0.py"),
            ]
            for key, path in sources.items():
                cmd.extend(("--" + key.replace("_", "-"), str(path)))
            cmd.extend(("--out", str(sources["zarr_part1"])))
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sources["zarr_part1"].read_bytes(),
                             b"synthetic, not original")


if __name__ == "__main__":
    unittest.main()
