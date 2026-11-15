# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only scientific sensitivities; no provider coordinates or IDs."""
from __future__ import annotations

from pathlib import Path
import unittest
from shapely.geometry import Point, Polygon

from research_runners import gdw_v1_invalid_polygons_area_sensitivity_v0 as s


class SyntheticGeod:
    """Deterministic planar area proxy to test topology, not physical units."""
    def geometry_area_perimeter(self, poly):
        return poly.area * 1_000_000, 0


class GDWInvalidAreaSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.geod = SyntheticGeod()
        self.bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])

    def test_two_counterfactuals_are_not_equivalent(self):
        self.assertFalse(self.bowtie.is_valid)
        a = s.examine_invalid(self.bowtie, Point(0.3, 1.5), self.geod)
        self.assertIsNotNone(a)
        self.assertGreater(a["linework_area_km2"], 0)
        self.assertGreaterEqual(a["linework_parts"], 2)
        self.assertLess(a["buffer_zero_area_km2"], a["linework_area_km2"])
        self.assertGreater(a["area_abs_delta_km2"], 0)
        self.assertLess(a["overlap_km2"], a["union_km2"])

    def test_never_treat_valid_or_empty_as_original_invalid(self):
        with self.assertRaises(s.GDWSensitivityError):
            s.examine_invalid(Polygon([(0,0), (1,0), (1,1), (0,0)]),
                              Point(0,0), self.geod)
        with self.assertRaises(s.GDWSensitivityError):
            s.examine_invalid(Polygon(), Point(0,0), self.geod)

    def test_antimeridian_and_polar_are_explicit_exclusions(self):
        dateline = Polygon([(-179, 0), (179, 2), (-179, 2), (179, 0), (-179, 0)])
        self.assertFalse(dateline.is_valid)
        self.assertIsNone(s.examine_invalid(dateline, Point(0, 0), self.geod))
        polar = Polygon([(0, 86), (2, 88), (0, 88), (2, 86), (0, 86)])
        self.assertFalse(polar.is_valid)
        self.assertIsNone(s.examine_invalid(polar, Point(1,87), self.geod))

    def test_full_population_required_and_scope_never_promoted(self):
        c = s.examine_invalid(self.bowtie, Point(0.4, 1.4), self.geod)
        with self.assertRaises(s.GDWSensitivityError):
            s.summarize([c], expected=221)
        r = s.summarize([c, None], expected=2)
        self.assertEqual(r["geodesic_comparable_invalid_polygons"], 1)
        self.assertEqual(r["excluded_antimeridian_or_polar_cases"], 1)
        self.assertFalse(r["complete_geodesic_population_evaluated"])
        self.assertFalse(r["CAT_model_input_approved"])
        self.assertFalse(r["source_geometries_or_ids_exported"])
        self.assertFalse(r["independent_gis_engine_checked"])
        self.assertTrue(r["method_difference_is_not_a_ground_truth_error"])
        self.assertEqual(r["original_invalid_polygon_count"], 2)
        self.assertNotIn("gdw_id", r)

    def test_wrong_or_absent_original_archive_is_rejected(self):
        with self.assertRaises((s.GDWSensitivityError, ValueError, OSError)):
            s.audit(Path("/this/path/must/not/exist/GDW_v1_0_shp.zip"))


if __name__ == "__main__":
    unittest.main()
