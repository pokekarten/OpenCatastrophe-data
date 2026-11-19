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
        self.assertGreater(a["footprint_symmetric_difference_km2"], 0)
        self.assertGreater(a["footprint_change_fraction_of_union"], 0)
        self.assertLessEqual(a["footprint_change_fraction_of_union"], 1)

    def test_equal_area_can_hide_material_spatial_disagreement(self):
        # Synthetic geometry-comparison receipt: identical alternative areas,
        # zero area difference, but ZERO spatial overlap. Never call this safe.
        first = s.examine_invalid(self.bowtie, Point(0.4, 1.4), self.geod)
        case = dict(first)
        case.update({
            "linework_area_km2": 10.0, "buffer_zero_area_km2": 10.0,
            "area_abs_delta_km2": 0.0, "overlap_km2": 0.0,
            "union_km2": 20.0, "footprint_symmetric_difference_km2": 20.0,
            "footprint_change_fraction_of_union": 1.0,
        })
        receipt = s.summarize([case], expected=1)
        self.assertEqual(receipt["material_area_difference_over_1pct_count"], 0)
        self.assertEqual(receipt["material_footprint_disagreement_over_1pct_count"], 1)
        self.assertEqual(receipt["equal_area_but_material_footprint_disagreement_count"], 1)
        self.assertEqual(receipt["area_weighted_jaccard_of_alternatives"], 0.0)
        self.assertEqual(receipt["footprint_symmetric_difference_km2_sum"], 20.0)
        self.assertFalse(receipt["CAT_model_input_approved"])

    def test_summary_rejects_corrupted_counterfactual_metrics(self):
        # Every case here is invented; no external source geometry is needed.
        original = s.examine_invalid(self.bowtie, Point(0.4, 1.4), self.geod)
        cases = (
            ("nan_area", "linework_area_km2", float("nan")),
            ("infinite_area", "buffer_zero_area_km2", float("inf")),
            ("negative_union", "union_km2", -1.0),
            ("incorrect_area_delta", "area_abs_delta_km2", 9999.0),
            ("overlap_exceeds_union", "overlap_km2", original["union_km2"] + 99.0),
            ("wrong_symmetric_difference", "footprint_symmetric_difference_km2", 0.0),
            ("wrong_fraction", "footprint_change_fraction_of_union", 1.5),
            ("fraction_is_bool", "footprint_change_fraction_of_union", True),
            ("noninteger_parts", "linework_parts", 2.5),
            ("nonboolean_coverage", "buffer_zero_barrier_covered", "yes"),
            ("missing_required_metric", "union_km2", None),
        )
        for label, field, replacement in cases:
            invalid = dict(original)
            invalid[field] = replacement
            with self.subTest(label=label), self.assertRaises(s.GDWSensitivityError):
                s.summarize([invalid], expected=1)
        with self.assertRaises(s.GDWSensitivityError):
            s.summarize([original], expected=0)
        with self.assertRaises(s.GDWSensitivityError):
            s.summarize([original], expected=True)

    def test_nonconservative_geodesic_overlay_fails_closed(self):
        from unittest.mock import patch
        # Previously accepted: union 7 km2 exceeds total alternative area 5.
        with patch.object(s, "_area_km2", side_effect=[3.0, 2.0, 1.0, 7.0]):
            with self.assertRaisesRegex(s.GDWSensitivityError,
                                        "nonconservative geodesic overlay"):
                s.examine_invalid(self.bowtie, Point(0.4, 1.4), self.geod)

    def test_unexpected_source_exception_never_leaks_coordinates(self):
        from contextlib import redirect_stderr
        from io import StringIO
        from unittest.mock import patch

        stderr = StringIO()
        with patch.object(s, "audit", side_effect=RuntimeError(
            "GEOS topology failed near original coordinates [12.345 67.890]")):
            with redirect_stderr(stderr):
                result = s.main(["--original-zip", "/nonexistent/source.zip"])
        self.assertEqual(result, 2)
        self.assertIn("BLOCKED: original GDW scientific sensitivity", stderr.getvalue())
        self.assertNotIn("12.345", stderr.getvalue())
        self.assertNotIn("67.890", stderr.getvalue())
        self.assertNotIn("GEOS topology", stderr.getvalue())

    def test_pinned_pyproj_synthetic_geodesic_when_available(self):
        # This optional dependency is installed in the reviewed original
        # main-only workflow, not in the repository-wide validation matrix.
        import importlib.util
        if importlib.util.find_spec("pyproj") is None:
            self.skipTest("pyproj is optional outside the GIS research runner")
        from pyproj import Geod
        result = s.examine_invalid(self.bowtie, Point(0.4, 1.4),
                                   Geod(ellps="WGS84"))
        self.assertAlmostEqual(result["linework_area_km2"], 24615.815, delta=1.0)
        self.assertAlmostEqual(result["buffer_zero_area_km2"], 12309.710, delta=1.0)
        self.assertGreater(result["footprint_change_fraction_of_union"], 0.4)
        self.assertLess(result["footprint_change_fraction_of_union"], 0.6)

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
        self.assertIn("material_footprint_disagreement_over_1pct_count", r)
        self.assertIn("equal_area_but_material_footprint_disagreement_count", r)
        self.assertFalse(r["CAT_model_input_approved"])
        self.assertNotIn("gdw_id", r)

    def test_wrong_or_absent_original_archive_is_rejected(self):
        with self.assertRaises((s.GDWSensitivityError, ValueError, OSError)):
            s.audit(Path("/this/path/must/not/exist/GDW_v1_0_shp.zip"))


if __name__ == "__main__":
    unittest.main()
