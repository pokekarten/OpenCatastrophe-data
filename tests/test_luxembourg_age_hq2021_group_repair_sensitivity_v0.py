# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic invalid group repair comparison and rejection regression."""
from __future__ import annotations

import json
import unittest

try:
    import shapely  # noqa: F401
    from shapely.geometry import Polygon
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

from research_runners.luxembourg_age_hq2021_group_repair_sensitivity_v0 import (
    GroupRepairChallengeError, InvalidPublisherGroupRepairChallenge,
)


@unittest.skipUnless(HAS_SHAPELY, "Pinned shapely required for bounded challenge")
class PublisherRepairComparisonTests(unittest.TestCase):
    def test_bowtie_zero_nominal_area_and_no_cat_admission(self):
        bowtie = Polygon([(0, 0), (3, 3), (0, 3), (3, 0), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        c = InvalidPublisherGroupRepairChallenge()
        c.observe(bowtie, point_count=5)
        r = c.summary(expected_invalid=1)
        self.assertEqual(r["linework_usable_publisher_groups"], 1)
        self.assertEqual(r["invalid_original_zero_nominal_area_groups"], 1)
        self.assertEqual(r["linework_structure_equal_polygonal_sets"], 1)
        self.assertEqual(r["linework_candidate_split_multipolygon_groups"], 1)
        self.assertEqual(r["sum_linework_repair_candidate_group_area_m2_not_union"], 4.5)
        self.assertFalse(r["building_overlay_or_cat_model_input_authorized"])
        self.assertFalse(r["complete_original_source_multipolygon_validity_proven"])
        self.assertNotIn("POLYGON", json.dumps(r))

    def test_spike_original_boundary_debris_not_hidden(self):
        spike = Polygon([(0, 0), (4, 0), (4, 4), (2, 4), (2, 2),
                         (2, 4), (0, 4), (0, 0)])
        self.assertFalse(spike.is_valid)
        c = InvalidPublisherGroupRepairChallenge()
        c.observe(spike, point_count=8)
        r = c.summary(expected_invalid=1)
        self.assertEqual(r["linework_usable_publisher_groups"], 1)
        self.assertEqual(r["linework_repairs_with_nonpolygon_debris"], 1)
        self.assertEqual(r["original_nominal_vs_linework_area_change_above_1pct"], 0)

    def test_complexity_quarantined_and_population_conserved(self):
        bowtie = Polygon([(0, 0), (3, 3), (0, 3), (3, 0), (0, 0)])
        c = InvalidPublisherGroupRepairChallenge(max_vertices=4)
        c.observe(bowtie, point_count=5)
        self.assertEqual(c.summary(expected_invalid=1)["original_invalid_groups_above_repair_vertex_cap"], 1)
        with self.assertRaises(GroupRepairChallengeError):
            c.summary(expected_invalid=2)
        for x in (0, -1, 50001, None, True):
            with self.subTest(x=x), self.assertRaises(GroupRepairChallengeError):
                InvalidPublisherGroupRepairChallenge(max_vertices=x)

    def test_two_invalid_group_population_and_no_coordinates(self):
        bowtie = Polygon([(0, 0), (3, 3), (0, 3), (3, 0), (0, 0)])
        c = InvalidPublisherGroupRepairChallenge()
        c.observe(bowtie, point_count=5)
        c.observe(bowtie, point_count=5)
        report = c.summary(expected_invalid=2)
        self.assertEqual(report["original_invalid_publisher_group_population"], 2)
        self.assertEqual(report["linework_usable_publisher_groups"], 2)
        self.assertEqual(report["linework_structure_equal_polygonal_sets"], 2)
        self.assertFalse(report["repair_candidates_or_geometry_written"])


if __name__ == "__main__":
    unittest.main()
