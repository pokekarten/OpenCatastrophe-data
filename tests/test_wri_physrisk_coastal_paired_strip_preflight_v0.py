# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only TIFF-LZW, Blosc-LZ4 and paired-pixel no-data regressions."""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import (
    PixelGateError, SHA, compare_pixels, inspect_original_ranges,
    lz4_raw_decode, read_pinned, tiff_lzw_decode,
)

ROOT = Path(__file__).resolve().parents[1]


def _nine_bit_lzw_codes(*codes):
    stream = "".join(f"{code:09b}" for code in codes)
    stream += "0" * (-len(stream) % 8)
    return bytes(int(stream[i:i+8], 2) for i in range(0, len(stream), 8))


def _lz4_literals(values):
    """One legal LZ4 literal-only block, no match or external compression."""
    n = len(values)
    if n < 15:
        return bytes((n << 4,)) + values
    extra = n - 15
    sizes = bytearray()
    while extra >= 255:
        sizes.append(255)
        extra -= 255
    sizes.append(extra)
    return bytes((0xF0,)) + bytes(sizes) + values


def _split_float_streams(values):
    packed = [struct.pack("<f", v) for v in values]
    return tuple(bytes(x[j] for x in packed) for j in range(4))


class WriPhysriskPairedStripTests(unittest.TestCase):
    def test_lzw_minimal_literal_stream_with_clear_and_eoi(self):
        data = _nine_bit_lzw_codes(256, 65, 66, 67, 257)
        self.assertEqual(tiff_lzw_decode(data, 3), b"ABC")
        with self.assertRaises(PixelGateError):
            tiff_lzw_decode(data[:-1], 3)
        with self.assertRaises(PixelGateError):
            tiff_lzw_decode(data, 2)

    def test_lzw_code_dictionary_backreference(self):
        # CLEAR, A, B, 258 (= AB), EOI -> ABAB.
        data = _nine_bit_lzw_codes(256, 65, 66, 258, 257)
        self.assertEqual(tiff_lzw_decode(data, 4), b"ABAB")
        with self.assertRaises(PixelGateError):
            tiff_lzw_decode(_nine_bit_lzw_codes(256, 400, 257), 2)

    def test_lz4_literal_only_and_bounded_invalid_match(self):
        for text in (b"hello", bytes(range(100)), bytes(range(255)) * 2):
            with self.subTest(length=len(text)):
                self.assertEqual(lz4_raw_decode(_lz4_literals(text), len(text)), text)
        with self.assertRaises(PixelGateError):
            lz4_raw_decode(_lz4_literals(b"xyz"), 4)
        with self.assertRaises(PixelGateError):
            lz4_raw_decode(b"\x10X\x00\x00", 5)  # illegal zero backref
        with self.assertRaises(PixelGateError):
            lz4_raw_decode(b"\xf0\xff", 131072)  # truncated length

    def test_pixel_crosswalk_exact_zero_positive_and_nodata(self):
        source = b"".join(struct.pack("<f", z) for z in (-9999., 0., 0.5, 1.25))
        derived = _split_float_streams((float("nan"), 0., 0.5, 1.25))
        result = compare_pixels(source, derived, 0, 4, 0, 4, 0)
        self.assertEqual(result["source_nodata_to_derived_nan"], 1)
        self.assertEqual(result["source_zero_exact"], 1)
        self.assertEqual(result["source_positive_exact"], 2)
        self.assertEqual(result["paired_cells"], 4)
        self.assertEqual(result["mismatches"], 0)

    def test_misinterpreted_nodata_or_misaligned_pixel_fails(self):
        source = b"".join(struct.pack("<f", z) for z in (-9999., 0., 0.5, 1.25))
        wrong_nodata = _split_float_streams((0., 0., 0.5, 1.25))
        wrong_intensity = _split_float_streams((float("nan"), 0., 0.8, 1.25))
        self.assertEqual(compare_pixels(source, wrong_nodata, 0, 4, 0, 4, 0)["mismatches"], 1)
        self.assertEqual(compare_pixels(source, wrong_intensity, 0, 4, 0, 4, 0)["mismatches"], 1)
        for bad_first_col, bad_count, bad_row in ((-1, 4, 0), (0, 5, 0), (0, 4, 1)):
            with self.assertRaises(PixelGateError):
                compare_pixels(source, wrong_nodata, bad_first_col, bad_count,
                               bad_row, 4, 0)

    def test_exact_pin_rejects_empty_wrong_and_oversized_source_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "provider.bin"
            for blob in (b"", b"0000", b"x" * 5):
                p.write_bytes(blob)
                with self.subTest(blob=blob):
                    with self.assertRaises(PixelGateError):
                        read_pinned(p, "tiff_offset")
        with self.assertRaises(PixelGateError):
            inspect_original_ranges({})

    def test_cli_never_overwrites_original_source_files(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            originals = {key: p / key for key in SHA}
            for file in originals.values():
                file.write_bytes(b"source-not-the-required-original")
            out = originals["tiff_strip"]
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_physrisk_coastal_paired_strip_preflight_v0.py"),
            ]
            for key, file in originals.items():
                cmd.extend(["--" + key.replace("_", "-"), str(file)])
            cmd.extend(["--out", str(out)])
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_bytes(), b"source-not-the-required-original")


if __name__ == "__main__":
    unittest.main()
