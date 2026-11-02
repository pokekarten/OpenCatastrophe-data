# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic Esri winding/containment and scientific non-admission tests."""
from __future__ import annotations

import json
import unittest

try:
    import shapely  # noqa: F401
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

from research_runners.luxembourg_age_hq2021_ring_hierarchy_challenge_v0 import (
    HierarchyChallengeError, SourceRingHierarchy,
)

# Shapefile Polygon exterior rings are conventionally clockwise.
SHELL = [(0., 0.), (0., 10.), (10., 10.), (10., 0.), (0., 0.)]
HOLE = [(2., 2.), (4., 2.), (4., 4.), (2., 4.), (2., 2.)]
ORPHAN = [(12., 2.), (14., 2.), (14., 4.), (12., 4.), (12., 2.)]
INNER_SHELL = [(1., 1.), (1., 8.), (8., 8.), (8., 1.), (1., 1.)]
INVALID_SHELL = [(0., 0.), (0., 5.), (5., 5.),
                 (5., 3.), (3., 3.), (5., 3.), (5., 0.), (0., 0.)]


@unittest.skipUnless(HAS_SHAPELY, "Shapely 2.x required for source ring topology")
class OriginalRingHierarchyTests(unittest.TestCase):
    def test_valid_hole_exactly_one_outer_shell(self):
        c = SourceRingHierarchy()
        c.observe(SHELL)
        c.observe(HOLE)
        result = c.summary(expected_rings=2)
        self.assertEqual(result["proposed_exterior_candidate_rings"], 1)
        self.assertEqual(result["proposed_hole_candidate_rings"], 1)
        self.assertEqual(result["valid_holes_with_exactly_one_valid_shell_cover"], 1)
        self.assertEqual(result["valid_holes_with_no_valid_shell_cover"], 0)
        self.assertEqual(result["valid_shell_hole_full_geos_covers_checks"], 1)
        self.assertFalse(result["full_original_multipart_polygon_topology_verified"])
        self.assertFalse(result["flood_building_intersection_authorized"])
        self.assertNotIn("POLYGON", json.dumps(result))

    def test_unassigned_hole_and_nested_duplicate_candidates_not_approved(self):
        c = SourceRingHierarchy()
        for ring in (SHELL, HOLE, ORPHAN):
            c.observe(ring)
        r = c.summary(expected_rings=3)
        self.assertEqual(r["valid_holes_with_exactly_one_valid_shell_cover"], 1)
        self.assertEqual(r["valid_holes_with_no_valid_shell_cover"], 1)
        b = SourceRingHierarchy()
        for ring in (SHELL, INNER_SHELL, HOLE):
            b.observe(ring)
        s = b.summary(expected_rings=3)
        self.assertEqual(s["valid_holes_with_multiple_valid_shell_covers"], 1)
        self.assertFalse(s["ring_hierarchy_fully_authorized"])

    def test_invalid_source_shell_is_quarantined_not_used_as_cover(self):
        c = SourceRingHierarchy()
        c.observe(INVALID_SHELL)
        c.observe(HOLE)
        r = c.summary(expected_rings=2)
        self.assertEqual(r["geos_invalid_proposed_exterior_candidates"], 1)
        self.assertEqual(r["valid_holes_with_exactly_one_valid_shell_cover"], 0)
        self.assertEqual(r["valid_holes_with_possible_invalid_shell_bbox_cover"], 1)
        self.assertFalse(r["cat_loss_model_input_admitted"])

    def test_reverse_winding_convention_is_independently_falsifiable(self):
        outer = list(reversed(SHELL))
        inner = list(reversed(HOLE))
        reversed_interpretation = SourceRingHierarchy(reverse_orientation=True)
        reversed_interpretation.observe(outer)
        reversed_interpretation.observe(inner)
        result = reversed_interpretation.summary(expected_rings=2)
        self.assertEqual(result["valid_holes_with_exactly_one_valid_shell_cover"], 1)
        self.assertEqual(result["proposed_exterior_candidate_rings"], 1)
        self.assertEqual(result["proposed_hole_candidate_rings"], 1)
        self.assertEqual(result["original_shapefile_polygon_winding_convention_hypothesis"],
                         "counterclockwise_exterior_clockwise_hole")
        traditional = SourceRingHierarchy()
        traditional.observe(outer)
        traditional.observe(inner)
        traditional_result = traditional.summary(expected_rings=2)
        self.assertEqual(traditional_result["valid_holes_with_exactly_one_valid_shell_cover"], 0)
        self.assertEqual(traditional_result["valid_holes_with_no_valid_shell_cover"], 1)
        with self.assertRaises(HierarchyChallengeError):
            SourceRingHierarchy(reverse_orientation=1)

    def test_bounded_exact_comparisons_and_population_fail_closed(self):
        c = SourceRingHierarchy(max_candidates=1)
        for ring in (SHELL, INNER_SHELL, HOLE):
            c.observe(ring)
        r = c.summary(expected_rings=3)
        self.assertEqual(r["valid_holes_quarantined_by_spatial_candidate_cap"], 1)
        with self.assertRaises(HierarchyChallengeError):
            c.summary(expected_rings=4)
        for bad in (0, 513, -1, True, None):
            with self.subTest(bad=bad), self.assertRaises(HierarchyChallengeError):
                SourceRingHierarchy(max_candidates=bad)


if __name__ == "__main__":
    unittest.main()
