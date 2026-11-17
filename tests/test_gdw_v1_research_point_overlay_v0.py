# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic Shapely geometry; no source GDW or insurer data."""
from __future__ import annotations

import json
import unittest

from shapely.geometry import MultiPolygon, Point, Polygon

from research_runners.gdw_v1_research_point_overlay_v0 import (
    GDWResearchOverlayBlocked,
    screen_synthetic_reservoir_exposure_points as screen,
)


def square(west=0, south=0, east=2, north=2):
    return Polygon([(west, south), (east, south), (east, north),
                    (west, north), (west, south)])


class GDWSyntheticExposureOverlayTests(unittest.TestCase):
    def call(self, pairs, points):
        return screen(pairs, points, synthetic_research_only=True)

    def test_single_candidate_is_research_only_and_no_data_leak(self):
        receipt = self.call([(square(), Point(1, 1))], [Point(0.5, 1.5)])
        self.assertEqual(receipt["single_candidate_interior_points"], 1)
        self.assertEqual(receipt["native_geometry_candidate_pairs"], 1)
        self.assertEqual(receipt["native_geometry_excluded_pairs"], 0)
        self.assertEqual(receipt["synthetic_exposure_points"], 1)
        for key in ("source_original_archive_loaded", "CAT_model_input_approved",
                    "global_geospatial_join_uniqueness_proven",
                    "insured_exposure_or_value_verified",
                    "external_exposure_coordinates_or_ids_emitted"):
            self.assertFalse(receipt[key], key)
        self.assertNotIn("0.5", json.dumps(receipt))
        self.assertNotIn("1.5", json.dumps(receipt))

    def test_two_overlapping_reservoirs_are_ambiguous_not_two_exposures(self):
        pairs = [(square(), Point(1, 1)), (square(1, 1, 3, 3), Point(2.5, 2.5))]
        receipt = self.call(pairs, [Point(1.5, 1.5), Point(0.5, 0.5)])
        self.assertEqual(receipt["native_geometry_candidate_pairs"], 2)
        self.assertEqual(receipt["multiple_or_boundary_ambiguous_points"], 1)
        self.assertEqual(receipt["single_candidate_interior_points"], 1)
        self.assertEqual(receipt["synthetic_exposure_points"], 2)

    def test_one_interior_plus_other_polygon_border_is_ambiguous(self):
        a = square(0, 0, 3, 3)
        b = square(1, 1, 3, 4)
        receipt = self.call([(a, Point(0.5, 0.5)), (b, Point(2, 3))],
                            [Point(1, 1)])
        self.assertEqual(receipt["multiple_or_boundary_ambiguous_points"], 1)
        self.assertEqual(receipt["single_candidate_interior_points"], 0)

    def test_boundary_only_and_outside_do_not_count(self):
        r = self.call([(square(), Point(1, 1))], [Point(0, 1), Point(5, 5)])
        self.assertEqual(r["boundary_only_excluded_points"], 1)
        self.assertEqual(r["outside_all_screened_reservoirs_points"], 1)
        self.assertEqual(r["single_candidate_interior_points"], 0)

    def test_invalid_and_dateline_reservoirs_are_excluded(self):
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
        wrap = square(-179, 0, 179, 2)
        r = self.call([(bowtie, Point(0.5, 1)), (wrap, Point(0, 1))],
                      [Point(0.5, 1)])
        self.assertEqual(r["native_geometry_candidate_pairs"], 0)
        self.assertEqual(r["native_geometry_excluded_pairs"], 2)
        self.assertEqual(r["outside_all_screened_reservoirs_points"], 1)

    def test_empty_hole_multipolygon_and_barrier_outside(self):
        with_hole = Polygon([(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
                            holes=[[(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]])
        mp = MultiPolygon([with_hole, square(10, 10, 12, 12)])
        r = self.call([(mp, Point(0.5, 0.5)), (square(20, 20, 22, 22), Point(30, 30))],
                      [Point(1.5, 1.5), Point(11, 11), Point(0, 0)])
        self.assertEqual(r["native_geometry_candidate_pairs"], 1)
        self.assertEqual(r["native_geometry_excluded_pairs"], 1)
        self.assertEqual(r["outside_all_screened_reservoirs_points"], 1)
        self.assertEqual(r["single_candidate_interior_points"], 1)
        self.assertEqual(r["boundary_only_excluded_points"], 1)

    def test_rejects_unmarked_and_wrong_type_source(self):
        with self.assertRaises(GDWResearchOverlayBlocked):
            screen([], [], synthetic_research_only=False)
        with self.assertRaises(GDWResearchOverlayBlocked):
            screen([], [], synthetic_research_only=1)
        with self.assertRaises(GDWResearchOverlayBlocked):
            self.call(None, [])
        with self.assertRaises(GDWResearchOverlayBlocked):
            self.call(["not-a-pair"], [])

    def test_rejects_invalid_exposure_locations_and_3d_point(self):
        for value in ("not-a-point", None, Polygon(), Point(999, 1),
                      Point(1, -91), Point(0, 0, 11), Point()):
            with self.subTest(value=str(value)), self.assertRaises(GDWResearchOverlayBlocked):
                self.call([(square(), Point(1, 1))], [value])

    def test_rejects_unbounded_input_for_research_preview(self):
        with self.assertRaises(GDWResearchOverlayBlocked):
            self.call([(square(), Point(1, 1))] * 33, [])
        with self.assertRaises(GDWResearchOverlayBlocked):
            self.call([], [Point(1, 1)] * 129)

    def test_empty_inputs_stay_zero_and_not_model_ready(self):
        r = self.call([], [])
        self.assertEqual(r["native_geometry_candidate_pairs"], 0)
        self.assertEqual(r["synthetic_exposure_points"], 0)
        self.assertFalse(r["CAT_model_input_approved"])


if __name__ == "__main__":
    unittest.main()
