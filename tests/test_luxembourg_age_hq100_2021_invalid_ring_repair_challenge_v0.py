# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic invalid-source HQ100 ring repair: no automatic flood model admission."""
from __future__ import annotations

import json
import unittest
from shapely.geometry import Polygon
from research_runners.luxembourg_age_hq100_2021_invalid_ring_repair_challenge_v0 import (
    InvalidRingRepairChallenger,
)
from research_runners.luxembourg_age_hq100_2021_ring_topology_v0 import RingTopologyCounter


class HQ100InvalidRingRepairTests(unittest.TestCase):
    def test_bowtie_is_comparable_but_never_admitted(self):
        bowtie = [(0., 0.), (3., 3.), (0., 3.), (3., 0.), (0., 0.)]
        ring = Polygon(bowtie)
        self.assertFalse(ring.is_valid)
        challenge = InvalidRingRepairChallenger()
        challenge.observe(ring, len(bowtie))
        result = challenge.summary(expected_invalid=1)
        self.assertEqual(result["bounded_repair_comparisons_usable"], 1)
        self.assertEqual(result["quarantined_above_vertex_cap"], 0)
        self.assertFalse(result["CAT_model_input_admitted"])
        self.assertTrue(result["repair_cannot_be_used_as_flood_extent_without_full_source_topology_review"])
        self.assertNotIn("POLYGON", json.dumps(result))

    def test_retraced_spike_preserves_nominal_area_but_reports_boundary_debris(self):
        spike = [(0., 0.), (4., 0.), (4., 4.), (2., 4.),
                 (2., 2.), (2., 4.), (0., 4.), (0., 0.)]
        ring = Polygon(spike)
        self.assertFalse(ring.is_valid)
        challenge = InvalidRingRepairChallenger()
        challenge.observe(ring, len(spike))
        result = challenge.summary(expected_invalid=1)
        self.assertEqual(result["bounded_repair_comparisons_usable"], 1)
        self.assertEqual(result["linework_repairs_without_nonpolygon_debris"], 0)
        self.assertEqual(result["original_boundary_lineal_set_changed"], 1)
        self.assertEqual(result["nominal_source_area_vs_repaired_change_over_1pct"], 0)
        self.assertFalse(result["numeric_hazard_depth_observed"])

    def test_explicit_cap_quarantine_and_no_anomalous_count_suppression(self):
        ring = Polygon([(0., 0.), (3., 3.), (0., 3.), (3., 0.), (0., 0.)])
        challenge = InvalidRingRepairChallenger(limit=4)
        challenge.observe(ring, 5)
        record = challenge.summary(expected_invalid=1)
        self.assertEqual(record["quarantined_above_vertex_cap"], 1)
        self.assertEqual(record["bounded_repair_comparisons_usable"], 0)
        with self.assertRaises(ValueError):
            challenge.summary(expected_invalid=2)
        for limit in (3, 50001, True, -1):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                InvalidRingRepairChallenger(limit=limit)

    def test_ring_counter_only_forwards_invalid_source_shapes(self):
        challenger = InvalidRingRepairChallenger()
        counter = RingTopologyCounter(repair_challenger=challenger)
        counter.observe([(0., 0.), (4., 0.), (4., 4.), (0., 4.), (0., 0.)])
        counter.observe([(0., 0.), (3., 3.), (0., 3.), (3., 0.), (0., 0.)])
        self.assertEqual(counter.summary(2)["individually_invalid_rings"], 1)
        self.assertEqual(challenger.summary(expected_invalid=1)["original_invalid_ring_count"], 1)


if __name__ == "__main__":
    unittest.main()
