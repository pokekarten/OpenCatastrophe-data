# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No real homes, no geographic inference: all test squares invented."""
from __future__ import annotations

import importlib.util
import unittest

from research_runners.us_census_2026_parish_point_crosswalk_v0 import (
    CrosswalkError, SyntheticPoint, match_synthetic_points,
)

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None


@unittest.skipUnless(HAS_SHAPELY, "Dedicated geographic workflow pins Shapely")
class ParishCrosswalkTests(unittest.TestCase):
    def fake_shapes(self):
        from shapely.geometry import Polygon
        # Side-by-side fictional polygon boxes, not Louisiana actual boundaries.
        return {
            "22071":Polygon([(-90.2,29.9),(-90.1,29.9),
                             (-90.1,30.0),(-90.2,30.0)]),
            "22051":Polygon([(-90.1,29.9),(-90.0,29.9),
                             (-90.0,30.0),(-90.1,30.0)]),
        }

    def test_two_synthetic_inside_sites_have_exact_nested_regions(self):
        shapes=self.fake_shapes()
        points=(
            SyntheticPoint("test_orleans",-90.15,29.95),
            SyntheticPoint("test_jefferson",-90.05,29.95),
        )
        matched=match_synthetic_points(shapes,points)
        self.assertEqual(matched,[
            {"asset_id":"test_jefferson","country_code":"US",
             "subdivisions":["US-LA","US-LA-22051"]},
            {"asset_id":"test_orleans","country_code":"US",
             "subdivisions":["US-LA","US-LA-22071"]},
        ])
        for row in matched:
            self.assertNotIn("longitude",row)
            self.assertNotIn("latitude",row)
            self.assertNotIn("value",row)

    def test_permutation_preserves_exact_output(self):
        shapes=self.fake_shapes()
        p=(SyntheticPoint("b",-90.15,29.95),
           SyntheticPoint("a",-90.05,29.95))
        self.assertEqual(match_synthetic_points(shapes,p),
                         match_synthetic_points(shapes,p[::-1]))

    def test_exact_shared_border_refuses_any_arbitrary_join(self):
        with self.assertRaisesRegex(CrosswalkError, "boundary"):
            match_synthetic_points(
                self.fake_shapes(),(SyntheticPoint("border",-90.1,29.95),))

    def test_polygon_outer_boundary_is_also_ambiguous(self):
        with self.assertRaisesRegex(CrosswalkError, "boundary"):
            match_synthetic_points(
                self.fake_shapes(),(SyntheticPoint("edge",-90.2,29.95),))

    def test_unmatched_point_fails_instead_of_nearest_region(self):
        with self.assertRaisesRegex(CrosswalkError, "no unique"):
            match_synthetic_points(
                self.fake_shapes(),(SyntheticPoint("gap",-90.5,30.2),))

    def test_overlapping_shapes_are_not_resolved_by_order(self):
        from shapely.geometry import Polygon
        shapes=self.fake_shapes()
        shapes["22051"]=Polygon([(-90.18,29.9),(-90.08,29.9),
                                 (-90.08,30.0),(-90.18,30.0)])
        with self.assertRaisesRegex(CrosswalkError, "no unique"):
            match_synthetic_points(
                shapes,(SyntheticPoint("ambiguous",-90.15,29.95),))

    def test_duplicate_asset_identifier_is_blocked(self):
        with self.assertRaisesRegex(CrosswalkError, "duplicate"):
            match_synthetic_points(
                self.fake_shapes(),
                (SyntheticPoint("same",-90.15,29.95),
                 SyntheticPoint("same",-90.05,29.95)))

    def test_unlabelled_or_real_asset_source_is_blocked(self):
        with self.assertRaisesRegex(CrosswalkError, "synthetic"):
            match_synthetic_points(
                self.fake_shapes(),
                (SyntheticPoint("secret",-90.15,29.95,origin="real_insurer"),))

    def test_nonfinite_or_invented_faraway_coordinates_are_blocked(self):
        for x,y in ((float("nan"),29.95),(float("inf"),29.95),
                    (-90.15,200),(True,29.95),(-1000,29.95)):
            with self.subTest(x=x,y=y),self.assertRaises(CrosswalkError):
                match_synthetic_points(
                    self.fake_shapes(),(SyntheticPoint("bad",x,y),))

    def test_fake_country_or_ambiguous_geoid_rejected(self):
        cases=({"01001":self.fake_shapes()["22071"]},
               {"22-071":self.fake_shapes()["22071"]},
               {})
        for case in cases:
            with self.subTest(case=case),self.assertRaises(CrosswalkError):
                match_synthetic_points(
                    case,(SyntheticPoint("x",-90.15,29.95),))

    def test_duplicate_or_missing_input_points_do_not_pass(self):
        with self.assertRaises(CrosswalkError):
            match_synthetic_points(self.fake_shapes(),())
        with self.assertRaises(CrosswalkError):
            match_synthetic_points(self.fake_shapes(),
                                   [SyntheticPoint("x",-90.15,29.95)])

    def test_input_with_unrecognized_value_fields_is_not_accepted(self):
        with self.assertRaises(CrosswalkError):
            match_synthetic_points(
                self.fake_shapes(),
                ({"asset_id":"x","longitude":-90.15,
                  "latitude":29.95,"tiv":1000000},))


if __name__=="__main__":
    unittest.main()
