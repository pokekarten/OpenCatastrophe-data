# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original WRI riverine RP100 554-cell Bavaria row tests."""
from __future__ import annotations

import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import PixelGateError
from research_runners import wri_riverine_bavaria_original_row5000_v0 as m

ROOT = Path(__file__).resolve().parents[1]


def invented_32bit_raster_row(*, nodata_col=None, bad_col=None):
    row = bytearray(43200*4)
    for col in range(22788, 22813):
        struct.pack_into("<f", row, col*4, 0.11534500122070312 + (col-22788)*.04)
    struct.pack_into("<f", row, 22812*4, 1.1153450012207031)
    if nodata_col is not None:
        struct.pack_into("<f", row, nodata_col*4, -9999.)
    if bad_col is not None:
        struct.pack_into("<f", row, bad_col*4, float("nan"))
    return bytes(row)


class WriOriginalRiverineBavariaRowTests(unittest.TestCase):
    def test_original_source_contracts_are_bounded_and_riverine(self):
        self.assertEqual(m.ROW, 5000)
        self.assertEqual(m.COLUMNS, (22684, 23237))
        self.assertEqual(m.SOURCE_STRIP_OFFSET, 28730421)
        self.assertEqual(m.SOURCE_COMPRESSED_BYTES, 6541)
        self.assertIn("inunriver_", m.RIVERINE_ORIGINAL)
        self.assertNotIn("inuncoast_", m.RIVERINE_ORIGINAL)
        self.assertEqual(m.PROFILE, "wri-riverine-bavaria-real-100yr-554-cell-one-row-v0")
        for k, (start, end, digest) in m.RANGES.items():
            with self.subTest(part=k):
                self.assertGreaterEqual(end, start)
                self.assertTrue(re.fullmatch("[0-9a-f]{64}", digest))

    def test_invented_float32_raster_categories_and_source_location(self):
        stats = m.summarize_row_5000(invented_32bit_raster_row())
        self.assertEqual(stats["sampled_raster_pixels"], 554)
        self.assertEqual(stats["finite_zero_depths"], 529)
        self.assertEqual(stats["finite_positive_depths"], 25)
        self.assertEqual(stats["nodata"], 0)
        self.assertEqual(stats["other_invalid_values"], 0)
        self.assertTrue(math.isclose(stats["raster_row_centre_latitude_degrees"],
                                     48.329166666666666, abs_tol=1e-12))
        self.assertEqual(len(stats["longitude_range_of_pixel_centres_degrees"]), 2)

    def test_nodata_negative_and_nan_are_counted_as_distinct_fail_categories(self):
        for kw, expected_field in (({"nodata_col": 22788}, "nodata"),
                                   ({"bad_col": 22788}, "other_invalid_values")):
            with self.subTest(kw=kw):
                stats = m.summarize_row_5000(invented_32bit_raster_row(**kw))
                self.assertEqual(stats[expected_field], 1)
                self.assertEqual(stats["finite_positive_depths"], 24)
        with self.assertRaises(PixelGateError):
            m.summarize_row_5000(b"corrupted original row")

    def test_original_row_requires_pinned_bytes_not_synthetic_fixture(self):
        with self.assertRaises(PixelGateError):
            m.inspect_original_source_ranges({})
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "original-suspect"
            for content in (b"", b"1234", b"bad-data"):
                f.write_bytes(content)
                with self.subTest(content=content):
                    with self.assertRaises(PixelGateError):
                        m.read_pinned(f, "offset")
        with self.assertRaises(PixelGateError):
            m.read_pinned(Path("not-used"), "unknown")

    def test_no_overwrite_of_original_provider_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "original-provider-response.bin"
            f.write_bytes(b"synthetic-only")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_riverine_bavaria_original_row5000_v0.py"),
                "--offset", str(f), "--bytecount", str(f),
                "--strip", str(f), "--out", str(f),
            ]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(f.read_bytes(), b"synthetic-only")


if __name__ == "__main__":
    unittest.main()
