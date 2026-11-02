# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GEOS source ring topology and source privacy tests."""
from __future__ import annotations

from io import BytesIO
import json
import unittest

from research_runners.luxembourg_age_hq100_2021_ring_topology_v0 import (
    RingTopologyCounter,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    check_shp, HQ100GeometryError,
)
from tests.test_luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import build_shape


class HQ100OriginalRingTopologyTests(unittest.TestCase):
    def test_valid_closed_ring_and_invalid_bowtie_are_both_counted(self):
        square = [(0., 0.), (4., 0.), (4., 4.), (0., 4.), (0., 0.)]
        bowtie = [(1., 1.), (3., 3.), (1., 3.), (3., 1.), (1., 1.)]
        counter = RingTopologyCounter()
        meta = check_shp(BytesIO(build_shape([square, bowtie])),
                         ring_diagnostic=counter.observe)
        report = counter.summary(meta["source_polygon_ring_parts"])
        self.assertEqual(report["source_rings_examined_total"], 2)
        self.assertEqual(report["individually_valid_nonzero_area_rings"], 1)
        self.assertEqual(report["individually_invalid_rings"], 1)
        self.assertEqual(report["complex_ring_geometry_test_skipped"], 0)
        self.assertFalse(report["full_multipart_polygon_ogc_validity_verified"])
        self.assertFalse(report["flood_depth_available_or_inferred"])
        self.assertFalse(report["building_to_hazard_overlap_authorized"])
        self.assertNotIn("1.0", json.dumps(report))
        self.assertNotIn("POLYGON", json.dumps(report))

    def test_count_conservation_fail_closed(self):
        collector = RingTopologyCounter()
        collector.observe([(0., 0.), (3., 0.), (3., 3.), (0., 3.), (0., 0.)])
        with self.assertRaises(HQ100GeometryError):
            collector.summary(2)
        self.assertEqual(collector.summary(1)["individually_valid_nonzero_area_rings"], 1)

    def test_complex_rings_quarantined_without_geos_attempt(self):
        collector = RingTopologyCounter()
        collector.observe([(0., 0.)] * 250_001)
        report = collector.summary(1)
        self.assertEqual(report["complex_ring_geometry_test_skipped"], 1)
        self.assertEqual(report["individually_valid_nonzero_area_rings"], 0)
        self.assertFalse(report["model_input_admitted"])


if __name__ == "__main__":
    unittest.main()
