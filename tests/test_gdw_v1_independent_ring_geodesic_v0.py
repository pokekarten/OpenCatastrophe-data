# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GDW independent diagnostics use synthetic geometry only, no source bytes."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import importlib.util
import unittest
from unittest.mock import patch

from research_runners import gdw_v1_independent_ring_geodesic_v0 as source


class SyntheticShape:
    def __init__(self, points, parts=(0,)):
        self.points = points
        self.parts = parts


class GDWIndependentDiagnosticTests(unittest.TestCase):
    def test_closure_is_not_self_touch_and_pure_vertex_witness(self):
        square = SyntheticShape([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        self.assertFalse(source.has_nonclosure_ring_vertex_repeat(square))
        touch = SyntheticShape([(0, 0), (2, 0), (2, 2), (1, 1),
                                (0, 2), (1, 1), (0, 0)])
        self.assertTrue(source.has_nonclosure_ring_vertex_repeat(touch))
        # Proper-crossing bowties may not duplicate a vertex: this is NOT
        # an independent complete GEOS topology validity engine.
        crossing = SyntheticShape([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        self.assertFalse(source.has_nonclosure_ring_vertex_repeat(crossing))

    def test_separate_ring_vertices_not_mislabeled_as_same_ring_repeat(self):
        outer = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]
        hole = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        self.assertFalse(source.has_nonclosure_ring_vertex_repeat(
            SyntheticShape(outer + hole, (0, len(outer)))))
        self.assertTrue(source.has_nonclosure_ring_vertex_repeat(
            SyntheticShape(outer + hole[:-1] + [hole[1], hole[-1]],
                           (0, len(outer)))))

    def test_invalid_native_ring_offsets_block(self):
        sample = [(0, 0), (1, 0), (1, 1), (0, 0)]
        for offsets in ((), (1,), (0, 0), (0, 5), (-1,), (0, 3, 2)):
            with self.subTest(offsets=offsets), self.assertRaises(
                    source.IndependentDiagnosticError):
                source.has_nonclosure_ring_vertex_repeat(
                    SyntheticShape(sample, offsets))

    @unittest.skipUnless(importlib.util.find_spec("geographiclib") and
                         importlib.util.find_spec("pyproj"),
                         "independent optional GIS libraries not installed")
    def test_geographiclib_matches_proj_on_synthetic_polygon_and_hole(self):
        from pyproj import Geod
        from shapely.geometry import Polygon
        from research_runners import (
            gdw_v1_invalid_polygons_area_sensitivity_v0 as s)
        square = Polygon([(0, 0), (2, 0), (2, 1), (0, 1), (0, 0)])
        self.assertAlmostEqual(source.geographiclib_area_km2(square),
                               s._area_km2(square, Geod(ellps="WGS84")),
                               delta=1e-8)
        hole = Polygon([(0, 0), (3, 0), (3, 3), (0, 3), (0, 0)],
                       holes=[[(1, 1), (1, 2), (2, 2),
                               (2, 1), (1, 1)]])
        self.assertAlmostEqual(source.geographiclib_area_km2(hole),
                               s._area_km2(hole, Geod(ellps="WGS84")),
                               delta=1e-8)
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        mismatch = source.compare_geodesic_counterfactuals(
            bowtie, Geod(ellps="WGS84"))
        self.assertLess(mismatch, 1e-8)

    @unittest.skipUnless(importlib.util.find_spec("geographiclib") and
                         importlib.util.find_spec("pyproj"),
                         "independent optional GIS libraries not installed")
    def test_wrong_independent_geodesic_is_rejected(self):
        from pyproj import Geod
        from shapely.geometry import Polygon
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        with patch.object(source, "geographiclib_area_km2",
                          return_value=987654):
            with self.assertRaisesRegex(source.IndependentDiagnosticError,
                                        "independent WGS84 area mismatch"):
                source.compare_geodesic_counterfactuals(
                    bowtie, Geod(ellps="WGS84"))

    def test_cli_fail_closed_without_original_coordinate_leak(self):
        stderr = StringIO()
        with patch.object(source, "audit", side_effect=RuntimeError(
                "source lon=12.345 lat=67.890")):
            with redirect_stderr(stderr):
                status = source.main(
                    ["--original-zip", "/absent/original.zip"])
        self.assertEqual(status, 2)
        self.assertIn("BLOCKED: GDW independent diagnostics failed",
                      stderr.getvalue())
        self.assertNotIn("12.345", stderr.getvalue())
        self.assertNotIn("67.890", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
