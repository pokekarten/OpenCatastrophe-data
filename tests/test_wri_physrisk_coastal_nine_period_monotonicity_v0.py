# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests: nine RP order, masks, source identities."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import PixelGateError
from research_runners.wri_physrisk_coastal_nine_period_monotonicity_v0 import (
    BLOCK_SCALARS, BLOCKS, GLOBAL_COLS, GLOBAL_ROW,
    NAN_EXPECTED, ORIGINAL_HEADER_BYTES, ORIGINAL_HEADER_SHA256, PERIODS,
    POSITIVE_EXPECTED, SAMPLE_COUNT, ZARR_URL,
    decode_blosc_block, inspect_bounded_originals, read_pinned,
    require_exact_original_observations, sample_values, summarize_monotonicity,
    verify_blosc_header,
)

ROOT = Path(__file__).resolve().parents[1]


def invented_consistent_depths():
    """Never source data: monotone values with matching aggregate populations."""
    arrays = {}
    for i, rp in enumerate(PERIODS):
        n_positive = POSITIVE_EXPECTED[i]
        values = []
        for col in range(SAMPLE_COUNT):
            if col < NAN_EXPECTED:
                value = float("nan")
            elif col < SAMPLE_COUNT - n_positive:
                value = 0.0
            else:
                value = i + 1 + col / 1000.0
            values.append(value)
        arrays[rp] = values
    return arrays


class NineReturnPeriodTests(unittest.TestCase):
    def test_original_block_contracts_distinct_and_in_bounds(self):
        self.assertEqual(PERIODS, (2, 5, 10, 25, 50, 100, 250, 500, 1000))
        self.assertEqual(GLOBAL_ROW, 8100)
        self.assertEqual(GLOBAL_COLS, (32000, 32999))
        self.assertTrue(ZARR_URL.startswith("https://os-climate-physical-risk.s3.amazonaws.com/"))
        self.assertEqual(len(BLOCKS), 9)
        self.assertEqual(len({entry[0] for entry in BLOCKS.values()}), 9)
        self.assertEqual(ORIGINAL_HEADER_BYTES, 4096)
        self.assertTrue(re.fullmatch(r"[a-f0-9]{64}", ORIGINAL_HEADER_SHA256))
        for i, rp in enumerate(PERIODS):
            index, start, stop, digest = BLOCKS[rp]
            with self.subTest(rp=rp):
                self.assertTrue(0 <= start < stop <= 2375870)
                self.assertTrue(stop - start <= 200000)
                self.assertTrue(re.fullmatch(r"[a-f0-9]{64}", digest))
                first = i * 1000000 + 100000
                last = first + SAMPLE_COUNT - 1
                self.assertEqual(first // BLOCK_SCALARS, index)
                self.assertEqual(last // BLOCK_SCALARS, index)

    def test_all_nine_period_synthetic_curve_monotonic_and_missing_consistent(self):
        synthetic = invented_consistent_depths()
        report = summarize_monotonicity(synthetic)
        require_exact_original_observations(report)
        self.assertEqual(report["complete_nine_period_finite_columns"], 928)
        self.assertEqual(report["missing_in_all_nine_periods"], 72)
        self.assertEqual(report["unresolved_mixed_missing_columns"], 0)
        self.assertEqual(report["total_adjacent_finite_comparisons"], 7424)
        self.assertEqual(report["total_adjacent_both_nan"], 576)
        self.assertEqual(report["total_decreasing"], 0)
        self.assertEqual(report["total_nan_to_finite"], 0)
        self.assertEqual(report["total_finite_to_nan"], 0)
        self.assertEqual([x["finite_positive"] for x in report["per_period"]],
                         list(POSITIVE_EXPECTED))

    def test_a_genuine_decrease_blocks_even_with_same_class_count(self):
        synthetic = invented_consistent_depths()
        # The cell remains a positive and finite Float32, but lower than RP 50.
        synthetic[100][-1] = 0.01
        report = summarize_monotonicity(synthetic)
        self.assertEqual(report["total_decreasing"], 1)
        self.assertEqual(report["adjacent_transitions"][4]["decreasing"], 1)
        with self.assertRaisesRegex(PixelGateError, "drift"):
            require_exact_original_observations(report)

    def test_finite_to_missing_and_missing_to_finite_block(self):
        for from_rp, col, change in ((100, 100, float("nan")),
                                     (250, 0, 0.0)):
            with self.subTest(rp=from_rp, col=col):
                synthetic = invented_consistent_depths()
                synthetic[from_rp][col] = change
                report = summarize_monotonicity(synthetic)
                self.assertGreater(
                    report["total_nan_to_finite"] + report["total_finite_to_nan"], 0)
                with self.assertRaises(PixelGateError):
                    require_exact_original_observations(report)

    def test_negative_infinite_or_missing_period_blocks(self):
        for value in (-1, float("inf"), -float("inf")):
            with self.subTest(value=value):
                synthetic = invented_consistent_depths()
                synthetic[500][300] = value
                report = summarize_monotonicity(synthetic)
                with self.assertRaises(PixelGateError):
                    require_exact_original_observations(report)
        missing = invented_consistent_depths()
        del missing[10]
        with self.assertRaisesRegex(PixelGateError, "missing"):
            summarize_monotonicity(missing)
        wrong_size = invented_consistent_depths()
        wrong_size[2].pop()
        with self.assertRaisesRegex(PixelGateError, "pixel population"):
            summarize_monotonicity(wrong_size)

    def test_float32_block_channel_position_and_alignment(self):
        index, block_index = 5, BLOCKS[100][0]
        channels = [bytearray(BLOCK_SCALARS) for _ in range(4)]
        first = index * 1000000 + GLOBAL_ROW % 1000 * 1000 - block_index * BLOCK_SCALARS
        for col, depth in ((0, 0.0), (1, 0.5), (146, 5.9934983253479), (999, float("nan"))):
            encoded = struct.pack("<f", depth)
            for channel in range(4):
                channels[channel][first + col] = encoded[channel]
        values = sample_values(tuple(bytes(x) for x in channels), index, block_index)
        self.assertEqual(len(values), 1000)
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[1], 0.5)
        self.assertEqual(values[146], struct.unpack("<f", struct.pack("<f", 5.9934983253479))[0])
        self.assertTrue(math.isnan(values[999]))
        with self.assertRaises(PixelGateError):
            sample_values(tuple(bytes(x) for x in channels), index, 0)

    def test_bad_header_or_compressed_source_block_rejected(self):
        with self.assertRaises(PixelGateError):
            verify_blosc_header(b"")
        with self.assertRaisesRegex(PixelGateError, "SHA-256"):
            verify_blosc_header(b"\x00" * ORIGINAL_HEADER_BYTES)
        with self.assertRaises(PixelGateError):
            decode_blosc_block(b"\x00" * 32)
        with self.assertRaises(PixelGateError):
            inspect_bounded_originals(b"", {})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "range"
            for bad in (b"", b"ABCD", b"\x00" * 4097):
                path.write_bytes(bad)
                with self.subTest(length=len(bad)):
                    with self.assertRaises(PixelGateError):
                        read_pinned(path, 4096, ORIGINAL_HEADER_SHA256)

    def test_cli_refuses_overwriting_original_or_duplicate_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "external-original.bin"
            f.write_bytes(b"synthetic external input, not source")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_physrisk_coastal_nine_period_monotonicity_v0.py"),
                "--zarr-header", str(f),
            ]
            for rp in PERIODS:
                cmd.extend((f"--rp-{rp}", str(f)))
            cmd.extend(("--out", str(f)))
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(f.read_bytes(), b"synthetic external input, not source")


if __name__ == "__main__":
    unittest.main()
