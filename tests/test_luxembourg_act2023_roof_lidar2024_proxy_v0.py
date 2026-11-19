# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ACT2023 roof vs LiDAR2024 raster research validation."""
from __future__ import annotations

import importlib.util
import json
import unittest

HAS=all(importlib.util.find_spec(x) is not None for x in ("numpy","rasterio","shapely","pyproj"))
if HAS:
    import numpy as np
    from rasterio.transform import from_origin
    from shapely.geometry import box,Polygon
    from research_runners.luxembourg_act2023_roof_lidar2024_proxy_v0 import (
        RoofProxyError,roof_proxy_summary
    )


@unittest.skipUnless(HAS,"Requires pinned optional spatial research dependencies")
class RoofMaskedLidarScienceTests(unittest.TestCase):
    def setUp(self):
        self.roi=box(0,0,6,6)
        self.transform=from_origin(0,6,1,1)
        self.terrain=np.ma.array(np.full((6,6),200.0),mask=False)
        self.surface=np.ma.array(np.full((6,6),212.0),mask=False)

    def summary(self,roof_polygons):
        return roof_proxy_summary(roof_polygons,self.terrain,self.surface,self.transform,self.roi)

    def test_one_2023_roof_has_proxy_but_not_certified_building_height(self):
        report=self.summary([box(0,0,6,6)])
        self.assertEqual(report["act2023_true_intersecting_roof_polygons"],1)
        self.assertEqual(report["roof_proxy"]["objects_with_bounded_raster_proxy"],1)
        self.assertEqual(report["roof_proxy"]["proxy_median_bins_metres_not_surveyed_heights"]["10_to_15m"],1)
        self.assertFalse(report["individual_roof_match_to_geobase_verified"])
        self.assertFalse(report["act2023_original_roof_heights_measured_or_certified"])
        self.assertFalse(report["act2023_model_input_admitted"])
        self.assertNotIn("212.0",json.dumps(report))

    def test_real_polygon_intersection_filters_bbox_only_corner(self):
        triangular=Polygon([(0,0),(6,0),(0,6)])
        report=roof_proxy_summary(
            [box(0,0,3,3),box(5,5,6,6)],self.terrain,self.surface,self.transform,triangular)
        self.assertEqual(report["act2023_rtree_bbox_candidates"],2)
        self.assertEqual(report["act2023_candidates_outside_exact_100m_roi"],1)
        self.assertEqual(report["act2023_true_intersecting_roof_polygons"],1)

    def test_two_overlap_roofs_never_double_assign_shared_pixels(self):
        r=self.summary([box(0,0,4,6),box(2,0,6,6)])
        occ=r["roof_proxy"]["raster_pixel_occupancy"]
        self.assertEqual(occ["multiply_assigned_raster_pixels"],12)
        self.assertEqual(occ["uniquely_assigned_raster_pixels"],24)
        self.assertFalse(r["roof_proxy"]["overlap_pixels_double_counted"])

    def test_identical_roof_polygons_not_reported_as_verified_heights(self):
        r=self.summary([box(0,0,6,6),box(0,0,6,6)])
        self.assertEqual(r["roof_proxy"]["objects_with_bounded_raster_proxy"],0)
        self.assertEqual(r["roof_proxy"]["objects_with_no_unique_raster_pixel"],2)

    def test_no_intersecting_roof_blocks(self):
        with self.assertRaisesRegex(RoofProxyError,"rejected"):
            self.summary([box(100,100,101,101)])

    def test_empty_original_input_blocks(self):
        with self.assertRaisesRegex(RoofProxyError,"Invalid original"):
            self.summary([])

    def test_negative_source_surface_proxy_never_becomes_zero_height(self):
        self.surface[:,:]=194
        r=self.summary([box(0,0,6,6)])
        self.assertEqual(r["roof_proxy"]["objects_with_bounded_raster_proxy"],0)
        self.assertEqual(r["roof_proxy"]["objects_with_negative_median_excluded"],1)

    def test_nodata_coverage_blocks_roof_proxy_not_valid_height(self):
        self.terrain.mask=np.ones((6,6),dtype=bool)
        with self.assertRaisesRegex(RoofProxyError,"rejected"):
            self.summary([box(0,0,6,6)])


if __name__=="__main__":
    unittest.main()
