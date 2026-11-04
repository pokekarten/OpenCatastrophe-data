# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Wholly fictional EPSG2169-like geometry: no original address/source records."""
from __future__ import annotations

import unittest

from shapely.geometry import Point, Polygon, box

from research_runners.lu_act_address_geobase_original_window_v0 import (
    AddressFootprintError, classify, run,
)


class SourceCandidateTests(unittest.TestCase):
    def test_one_interior_candidate_is_not_building_identity(self):
        result = classify([Point(5,5)], [box(0,0,10,10)])
        self.assertEqual(result["status_counts"], {"one_containing_polygon_candidate":1})
        self.assertFalse(result["one_to_one_physical_building_identity_proven"])
        self.assertFalse(result["cat_model_exposure_admitted"])

    def test_point_outside_all_polygons_reports_metric_distance_only(self):
        result = classify([Point(15,5)], [box(0,0,10,10)])
        self.assertEqual(result["status_counts"], {"no_intersecting_polygon":1})
        self.assertEqual(result["outside_distance_mean_m"], 5.0)

    def test_boundary_point_is_ambiguous(self):
        result = classify([Point(0,5)], [box(0,0,10,10)])
        self.assertEqual(result["status_counts"], {"boundary_only_ambiguous":1})

    def test_two_overlapping_polygons_are_ambiguous(self):
        result = classify([Point(5,5)], [box(0,0,10,10),box(4,4,12,12)])
        self.assertEqual(result["status_counts"], {"multiple_containing_polygons":1})

    def test_interior_plus_other_boundary_is_ambiguous(self):
        result = classify([Point(5,5)], [box(0,0,10,10), box(5,5,8,8)])
        self.assertEqual(result["status_counts"], {"interior_plus_boundary_ambiguity":1})

    def test_multiple_addresses_share_one_polygon_not_unique_building(self):
        result = classify([Point(2,2),Point(8,8)], [box(0,0,10,10)])
        self.assertEqual(result["polygons_with_multiple_uniquely_contained_addresses"],1)
        self.assertEqual(result["addresses_in_such_polygons"],2)
        self.assertFalse(result["one_to_one_physical_building_identity_proven"])

    def test_non_building_area_hole_does_not_count_as_containment(self):
        poly = Polygon([(0,0),(10,0),(10,10),(0,10)], holes=[[(4,4),(6,4),(6,6),(4,6)]])
        result = classify([Point(5,5)], [poly])
        self.assertEqual(result["status_counts"],{"no_intersecting_polygon":1})

    def test_invalid_self_intersection_blocks(self):
        bad = Polygon([(0,0),(10,10),(0,10),(10,0)])
        with self.assertRaises(AddressFootprintError):
            classify([Point(1,1)], [bad])

    def test_empty_sample_blocks(self):
        with self.assertRaises(AddressFootprintError):
            classify([], [box(0,0,10,10)])
        with self.assertRaises(AddressFootprintError):
            classify([Point(1,1)], [])

    def test_nonpoint_geometry_blocks(self):
        with self.assertRaises(AddressFootprintError):
            classify([box(0,0,1,1)], [box(0,0,10,10)])

    def test_only_aggregate_data_emitted(self):
        result = classify([Point(5,5),Point(20,20)], [box(0,0,10,10)])
        self.assertEqual(sum(result["status_counts"].values()),2)
        self.assertNotIn("coordinates",str(result))
        self.assertEqual(result["geobase_polygons_sampled"],1)

    def test_missing_actual_files_fail_closed(self):
        from pathlib import Path
        with self.assertRaises(AddressFootprintError):
            run(Path("synthetic-absent-address.csv"), Path("synthetic-absent-building.zip"))


if __name__ == "__main__":
    unittest.main()
