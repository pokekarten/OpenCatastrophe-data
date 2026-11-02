# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic source grouped polygon OGC validity, complexity quarantine and privacy."""
from __future__ import annotations

import json
import unittest

try:
    import shapely  # noqa: F401
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

from research_runners.luxembourg_age_hq2021_geojson_group_ogc_v0 import (
    GroupTopologyError, challenge_publisher_groups,
)


def source(polygons):
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": "do-not-output-source-id",
         "properties": {"OBJECTID": 456},
         "geometry": {"type": "MultiPolygon", "coordinates": polygons}},
    ]}


@unittest.skipUnless(HAS_SHAPELY, "Requires pinned Shapely 2.1.2")
class PublisherGeoJSONGroupOGCTests(unittest.TestCase):
    def test_valid_shell_hole_and_independent_invalid_bowtie(self):
        square = [[0., 0.], [0., 10.], [10., 10.], [10., 0.], [0., 0.]]
        hole = [[2., 2.], [4., 2.], [4., 4.], [2., 4.], [2., 2.]]
        bowtie = [[20., 0.], [24., 4.], [20., 4.], [24., 0.], [20., 0.]]
        r = challenge_publisher_groups(source([[square, hole], [bowtie]]))
        self.assertEqual(r["original_publisher_groups_examined"], 2)
        self.assertEqual(r["publisher_groups_with_assigned_holes"], 1)
        self.assertEqual(r["individually_geos_valid_publisher_polygon_groups"], 1)
        self.assertEqual(r["individually_geos_invalid_publisher_polygon_groups"], 1)
        self.assertEqual(r["publisher_groups_over_vertex_complexity_budget"], 0)
        self.assertFalse(r["whole_original_publisher_multipolygon_OGC_validity_verified"])
        self.assertFalse(r["CAT_loss_input_admitted"])
        self.assertNotIn("do-not-output-source-id", json.dumps(r))
        self.assertNotIn("456", json.dumps(r))

    def test_hole_outside_shell_is_invalid_and_not_repaired(self):
        square = [[0., 0.], [0., 10.], [10., 10.], [10., 0.], [0., 0.]]
        hole = [[11., 2.], [13., 2.], [13., 4.], [11., 4.], [11., 2.]]
        r = challenge_publisher_groups(source([[square, hole]]))
        self.assertEqual(r["individually_geos_invalid_publisher_polygon_groups"], 1)
        self.assertEqual(r["invalid_group_ogc_reason_categories_only"].get("Hole lies outside shell"), 1)
        self.assertFalse(r["source_polygons_repaired_or_admitted"])

    def test_overbudget_groups_quarantined_and_counts_conserved(self):
        ring = [[0.,0.],[0.,10.],[10.,10.],[10.,0.],[0.,0.]]
        small = [[20.,0.],[20.,10.],[30.,10.],[30.,0.],[20.,0.]]
        r = challenge_publisher_groups(source([[ring], [small]]), max_group_vertices=4)
        self.assertEqual(r["publisher_groups_over_vertex_complexity_budget"], 2)
        self.assertFalse(r["every_original_publisher_group_tested"])
        for invalid in (0,120001,None,True,-1):
            with self.subTest(invalid=invalid), self.assertRaises(GroupTopologyError):
                challenge_publisher_groups(source([[ring]]),max_group_vertices=invalid)

    def test_reject_nonpolygon_sources(self):
        with self.assertRaises(GroupTopologyError):
            challenge_publisher_groups({"type":"Point","coordinates":[0,0]})
        with self.assertRaises(GroupTopologyError):
            challenge_publisher_groups({"type":"FeatureCollection","features":[]})


if __name__ == "__main__":
    unittest.main()
