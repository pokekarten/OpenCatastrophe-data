# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic/geodetic only: named rural study envelope vs frozen city pilot."""
from __future__ import annotations

import importlib.util
import unittest

HAS=all(importlib.util.find_spec(x) is not None for x in ("shapely","pyproj"))
if HAS:
    from pyproj import Transformer
    from research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 import (
        BuildingProxyError, LON, LAT, HALF_WIDTH_METRES, STUDY_SITES,
        original_window,
    )


@unittest.skipUnless(HAS, "requires pinned PyProj/Shapely profile")
class RuralWindowTests(unittest.TestCase):
    def test_city_stays_the_frozen_baseline(self):
        self.assertEqual(STUDY_SITES["luxembourg-city"], (LON,LAT))
        self.assertEqual(original_window().wkb,original_window(site="luxembourg-city").wkb)
        self.assertEqual(HALF_WIDTH_METRES,50.0)

    def test_berdorf_is_second_fixed_public_village_study(self):
        self.assertEqual(STUDY_SITES["berdorf-village"],(6.348821,49.820946))
        self.assertEqual(len(STUDY_SITES),2)
        rural=original_window(site="berdorf-village")
        city=original_window()
        self.assertTrue(rural.is_valid)
        self.assertGreater(rural.area,9700)
        self.assertLess(rural.area,10300)
        self.assertFalse(rural.intersects(city))
        native_to_wgs84=Transformer.from_crs(2169,4326,always_xy=True)
        x,y=native_to_wgs84.transform(rural.centroid.x,rural.centroid.y)
        self.assertAlmostEqual(x,6.348821,places=3)
        self.assertAlmostEqual(y,49.820946,places=3)

    def test_arbitrary_residential_coordinates_are_forbidden(self):
        for selector in ("", "home", "49.820946,6.348821", "../../etc/passwd", "BERDORF"):
            with self.subTest(selector=selector):
                with self.assertRaisesRegex(BuildingProxyError,"unknown or unapproved"):
                    original_window(site=selector)

    def test_source_study_window_is_square_near_100m(self):
        for site in STUDY_SITES:
            with self.subTest(site=site):
                geom=original_window(site=site)
                self.assertEqual(len(list(geom.exterior.coords)),5)
                self.assertGreater(geom.minimum_rotated_rectangle.area,9700)
                self.assertLess(geom.minimum_rotated_rectangle.area,10300)


if __name__ == "__main__":
    unittest.main()
