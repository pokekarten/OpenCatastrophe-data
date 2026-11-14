# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for European North Sea original WRI/Physrisk pair."""
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
from research_runners.wri_physrisk_coastal_europe_100yr_pair_v0 import (
    BLOSC_BLOCK_BEGIN, BLOSC_BLOCK_END, BLOSC_BLOCK_INDEX, CHUNK_LOCAL_ROW,
    COLS, FIRST_COL, GLOBAL_ROW, HEADER_LENGTH, PERIOD_INDEX,
    PERIOD_YEARS, SOURCE_TIFF_STRIP_BEGIN, SOURCE_TIFF_STRIP_LENGTH, SOURCES,
    WRI_URL, PHYSRISK_URL, inspect_range_pair, read_original,
    split_original_blosc,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_north_sea_pair():
    """Purely invented values with the observed real-source sample category sizes."""
    row = bytearray(43200*4)
    streams = [bytearray(131072) for _ in range(4)]
    blosc_scalar_start = BLOSC_BLOCK_INDEX * 131072
    starting_cell = PERIOD_INDEX * 1000000 + CHUNK_LOCAL_ROW * 1000
    for col in range(COLS):
        if col < 93:
            source, target = -9999.0, float("nan")
        elif col < 93 + 819:
            source = target = 0.0
        else:
            source = target = 0.01 + col / 1000.0
        struct.pack_into("<f", row, (FIRST_COL+col)*4, source)
        bits = struct.pack("<f", target)
        for channel in range(4):
            streams[channel][starting_cell+col-blosc_scalar_start] = bits[channel]
    return bytes(row), tuple(bytes(x) for x in streams)


class EuropeanNorthSeaHundredYearTests(unittest.TestCase):
    def test_original_independent_region_and_source_contracts(self):
        self.assertEqual(GLOBAL_ROW, 4560)
        self.assertEqual(FIRST_COL, 22000)
        self.assertEqual(PERIOD_YEARS, 100)
        self.assertEqual(PERIOD_INDEX, 5)
        self.assertEqual(CHUNK_LOCAL_ROW, 560)
        self.assertEqual(BLOSC_BLOCK_INDEX, 42)
        self.assertEqual(BLOSC_BLOCK_END - BLOSC_BLOCK_BEGIN, 51008)
        self.assertEqual(SOURCE_TIFF_STRIP_BEGIN, 9532356)
        self.assertEqual(SOURCE_TIFF_STRIP_LENGTH, 2717)
        self.assertEqual(len(SOURCES), 6)
        self.assertEqual(HEADER_LENGTH, 4096)
        self.assertTrue(WRI_URL.startswith("https://aqueduct.wridata.org/"))
        self.assertTrue(PHYSRISK_URL.endswith("/0.4.22"))
        for key, (_url, start, end, sha) in SOURCES.items():
            with self.subTest(key=key):
                self.assertTrue(0 <= start <= end)
                self.assertLessEqual(end-start+1, 40000)
                self.assertTrue(re.fullmatch("[0-9a-f]{64}", sha))

    def test_exact_synthetic_finite_values_and_nodata_categories(self):
        row, streams = synthetic_north_sea_pair()
        result = compare_pixels(
            row, streams, FIRST_COL, COLS,
            PERIOD_INDEX*1000+CHUNK_LOCAL_ROW, 1000, BLOSC_BLOCK_INDEX*131072,
        )
        self.assertEqual(result["source_zero_exact"], 819)
        self.assertEqual(result["source_positive_exact"], 88)
        self.assertEqual(result["source_nodata_to_derived_nan"], 93)
        self.assertEqual(result["mismatches"], 0)
        self.assertEqual(result["paired_cells"], 1000)

    def test_missing_to_zero_wrong_depth_or_alignment_will_fail(self):
        row, streams = synthetic_north_sea_pair()
        first = PERIOD_INDEX*1000000 + CHUNK_LOCAL_ROW*1000 - BLOSC_BLOCK_INDEX*131072
        variants = []
        x = [bytearray(y) for y in streams]
        for k, b in enumerate(struct.pack("<f", 0.0)):
            x[k][first] = b
        variants.append(tuple(bytes(v) for v in x))
        x = [bytearray(y) for y in streams]
        for k, b in enumerate(struct.pack("<f", 9.0)):
            x[k][first+999] = b
        variants.append(tuple(bytes(v) for v in x))
        for invalid in variants:
            res = compare_pixels(
                row, invalid, FIRST_COL, COLS, 5560, 1000, 42*131072,
            )
            self.assertEqual(res["mismatches"], 1)
        with self.assertRaises(PixelGateError):
            compare_pixels(row, streams, FIRST_COL, COLS, 0, 1000, 42*131072)

    def test_original_hash_is_required_and_truncation_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.bin"
            for payload in (b"", b"ABCD", b"x" * 6):
                path.write_bytes(payload)
                with self.subTest(payload=payload):
                    with self.assertRaises(PixelGateError):
                        read_original(path, "wri_row_offset")
            with self.assertRaises(PixelGateError):
                read_original(path, "made-up")
        with self.assertRaises(PixelGateError):
            inspect_range_pair({})

    def test_blosc_rejects_changed_headers_or_chunk_length(self):
        with self.assertRaises(PixelGateError):
            split_original_blosc(b"", b"")
        wrong = bytearray(4096)
        struct.pack_into("<BBBBIII", wrong, 0, 2, 1, 33, 4, 36000000,
                         524288, 1751433)
        with self.assertRaises(PixelGateError):
            split_original_blosc(bytes(wrong), b"\x00" * 51008)
        with self.assertRaises(PixelGateError):
            split_original_blosc(bytes(wrong), b"\x00" * 51007)

    def test_cli_forbids_source_overwrite_and_duplicate_source_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source"
            source.write_bytes(b"synthetic-only")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_physrisk_coastal_europe_100yr_pair_v0.py"),
            ]
            for key in SOURCES:
                cmd += ["--"+key.replace("_", "-"), str(source)]
            cmd += ["--out", str(source)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_bytes(), b"synthetic-only")


if __name__ == "__main__":
    unittest.main()
