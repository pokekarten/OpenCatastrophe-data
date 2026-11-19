# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WRI riverine native-grid and Bavaria defence candidate tests.

No real coordinates or protected properties are imported into the test suite.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners import wri_bavaria_riverine_defence_spatial_candidate_v0 as m
from research_runners.bavaria_hwsa_full_shapefile_integrity_v0 import EXPECTED_COUNTS

ROOT = Path(__file__).resolve().parents[1]


def lon_from_pixel(x):
    return -180 + x / 120


def lat_from_pixel(y):
    return 90 - y / 120


def synthetic_one_line_shp(count: int, a=(11.60, 48.40), b=(11.72, 48.25)):
    """Invented Bavarian-looking polylines; not any source provider geometry."""
    data = bytearray(100)
    for i in range(count):
        record = bytearray(80)
        struct.pack_into("<I", record, 0, 3)
        struct.pack_into("<4d", record, 4,
                         min(a[0], b[0]), min(a[1], b[1]),
                         max(a[0], b[0]), max(a[1], b[1]))
        struct.pack_into("<II", record, 36, 1, 2)
        struct.pack_into("<I", record, 44, 0)
        struct.pack_into("<4d", record, 48, a[0], a[1], b[0], b[1])
        data.extend(struct.pack(">II", i+1, 40))
        data.extend(record)
    return bytes(data)


class RiverineBavariaSpatialCandidateTests(unittest.TestCase):
    def test_source_is_riverine_not_earlier_coastal_asset(self):
        self.assertIn("inunriver_historical_000000000WATCH_1980_rp00100.tif",
                      m.RIVERINE_ORIGINAL)
        self.assertNotIn("inuncoast_", m.RIVERINE_ORIGINAL)
        self.assertEqual((m.WIDTH, m.HEIGHT), (43200, 21600))
        self.assertEqual(m.CELLS_PER_DEGREE, 120)
        self.assertEqual(m.CHUNK_WIDTH, 1000)
        self.assertEqual(set(m.TIFF_SOURCE_RANGES),
                         {"header", "ifd", "scale", "tie", "geokeys", "nodata"})
        for name, (start, end, digest) in m.TIFF_SOURCE_RANGES.items():
            with self.subTest(name=name):
                self.assertGreaterEqual(end, start)
                self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", digest))

    def test_riverine_source_range_guard_needs_actual_original_bytes(self):
        with self.assertRaisesRegex(m.SpatialCandidateError, "incomplete"):
            m.verify_original_wri_riverine_tiff({})
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "not-the-original-header.bin"
            for payload in (b"", b"II\x2a\x00" + b"\0"*4092, b"A"*4097):
                bad.write_bytes(payload)
                with self.subTest(length=len(payload)):
                    with self.assertRaises(m.SpatialCandidateError):
                        m.original_range_bytes(bad, "header")
        with self.assertRaises(m.SpatialCandidateError):
            m.original_range_bytes(Path("unused"), "unknown")

    def test_exact_riverine_global_pixel_axes(self):
        self.assertEqual(m.global_wri_cell(11.0, 48.0), (5040, 22920))
        self.assertEqual(m.global_wri_cell(11.5, 48.5), (4980, 22980))
        self.assertEqual(m.global_wri_cell(-179.5, 89.5), (60, 60))
        for coord in ((float("nan"), 48), (11, float("inf")),
                      (180, 48), (11, -90)):
            with self.subTest(coord=coord):
                with self.assertRaises(m.SpatialCandidateError):
                    m.global_wri_cell(*coord)

    def test_line_through_three_interior_cells_is_not_vertex_only(self):
        a = (lon_from_pixel(23000.2), lat_from_pixel(5000.3))
        b = (lon_from_pixel(23002.7), lat_from_pixel(5000.3))
        cells = m.segment_candidate_cells(a, b)
        self.assertTrue({(5000, 23000), (5000, 23001), (5000, 23002)}
                        .issubset(cells))
        self.assertEqual(len(cells), 3)

    def test_boundary_and_corner_touching_are_not_silently_dropped(self):
        a = (lon_from_pixel(23000.25), lat_from_pixel(5000.0))
        b = (lon_from_pixel(23002.75), lat_from_pixel(5000.0))
        rows = {row for row, _ in m.segment_candidate_cells(a, b)}
        self.assertEqual(rows, {4999, 5000})
        a = (lon_from_pixel(23000.2), lat_from_pixel(5000.2))
        b = (lon_from_pixel(23002.8), lat_from_pixel(5002.8))
        cells = m.segment_candidate_cells(a, b)
        self.assertIn((5000, 23001), cells)
        self.assertIn((5001, 23000), cells)
        self.assertIn((5002, 23002), cells)

    def test_crs_accuracy_near_border_adds_candidates_not_fake_protection(self):
        # Synthetic straight segment 0.001 source cells from an exact WRI border.
        # With a ~1 m-class datum operation and a conservative 0.0025-cell
        # margin, both adjacent rows must remain *candidates*, not protected.
        a = (lon_from_pixel(23000.2), lat_from_pixel(5000.001))
        b = (lon_from_pixel(23000.8), lat_from_pixel(5000.001))
        strict = m.segment_candidate_cells(a, b)
        conservative = m.segment_candidate_cells(
            a, b, boundary_tolerance_cells=0.0025)
        self.assertIn((5000, 23000), strict)
        self.assertNotIn((4999, 23000), strict)
        self.assertIn((4999, 23000), conservative)
        self.assertIn((5000, 23000), conservative)
        self.assertGreater(len(conservative), len(strict))

        # Beyond the declared uncertainty we do not add entire nearby rows.
        farther = (
            (lon_from_pixel(23000.2), lat_from_pixel(5000.01)),
            (lon_from_pixel(23000.8), lat_from_pixel(5000.01)),
        )
        unchanged = m.segment_candidate_cells(
            *farther, boundary_tolerance_cells=0.0025)
        self.assertNotIn((4999, 23000), unchanged)
        for bad in (-0.1, 0.0, 0.1, float("nan"), float("inf")):
            with self.subTest(tolerance=bad):
                with self.assertRaises(m.SpatialCandidateError):
                    m.segment_candidate_cells(
                        a, b, boundary_tolerance_cells=bad)

    def test_realistic_bavaria_tile_boundaries_are_candidates_only(self):
        synthetic = {k: synthetic_one_line_shp(n)
                     for k, n in EXPECTED_COUNTS.items()}
        # An identity operation is ONLY an invented fixture here.
        # Production code requires explicit pyproj ETRS89->WGS84.
        summary = m.aggregate_original_defence_candidate_cells(
            synthetic, lambda x, y: (x, y))
        self.assertEqual(set(summary), set(EXPECTED_COUNTS))
        for kind, count in EXPECTED_COUNTS.items():
            with self.subTest(kind=kind):
                item = summary[kind]
                self.assertEqual(item["original_source_records"], count)
                self.assertGreater(item["distinct_wri_riverine_candidate_cells"], 2)
                self.assertGreater(item["source_record_candidate_cell_relations"], count)
                tiles = {x["tile_key_y_x"] for x in item["candidate_tiles"]}
                self.assertIn("4.22", tiles)
                self.assertIn("5.23", tiles)
                self.assertTrue(item["no_hazard_depth_or_protection_inferred"])

    def test_wrong_crs_or_source_geometry_is_rejected_not_assumed(self):
        synthetic = {k: synthetic_one_line_shp(n)
                     for k, n in EXPECTED_COUNTS.items()}
        with self.assertRaises(m.SpatialCandidateError):
            m.aggregate_original_defence_candidate_cells(
                synthetic, lambda x, y: (x*100000, y*100000))
        altered = dict(synthetic)
        altered["deich"] = altered["deich"][:-5]
        with self.assertRaises(m.SpatialCandidateError):
            m.aggregate_original_defence_candidate_cells(
                altered, lambda x, y: (x, y))
        with self.assertRaises(m.SpatialCandidateError):
            m.aggregate_original_defence_candidate_cells(
                {}, lambda x, y: (x, y))

    def test_too_large_source_segment_does_not_explode_runtime(self):
        with self.assertRaisesRegex(m.SpatialCandidateError, "excessive"):
            m.segment_candidate_cells((-179, 48), (179, 48))
        with self.assertRaises(m.SpatialCandidateError):
            m.segment_candidate_cells((11, float("nan")), (11.1, 48.1))

    def test_cli_never_overwrites_original_provider_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "original-only.zip"
            p.write_bytes(b"synthetic-only, not external archive")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_bavaria_riverine_defence_spatial_candidate_v0.py"),
                "--lfu-epsg4258-original-zip", str(p),
            ]
            for key in m.TIFF_SOURCE_RANGES:
                cmd += ["--wri-"+key, str(p)]
            cmd += ["--out", str(p)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(p.read_bytes(),
                             b"synthetic-only, not external archive")


if __name__ == "__main__":
    unittest.main()
