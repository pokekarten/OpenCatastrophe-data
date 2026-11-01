# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original-building LiDAR MNS-MNT masking and count QA."""
from __future__ import annotations

import importlib.util
import json
import unittest

HAS=all(importlib.util.find_spec(x) is not None
        for x in ("rasterio","numpy","shapely","pyproj"))
if HAS:
    import numpy as np
    from rasterio.transform import from_origin
    from shapely.geometry import box,Point
    from research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 import (
        BuildingProxyError,aggregate,
    )


@unittest.skipUnless(HAS,"pinned optional geospatial runtime needed")
class ObjectSurfaceTerrainTests(unittest.TestCase):
    def setUp(self):
        self.study=box(0,0,5,5)
        self.t=from_origin(0,5,1,1)
        self.ground=np.ma.array(np.full((5,5),200.0),mask=False)
        self.surface=np.ma.array(np.array([
            [205,205,212,212,212],
            [205,205,212,212,212],
            [205,205,212,212,212],
            [205,205,212,212,212],
            [205,205,212,212,212],
        ],dtype=float),mask=False)
        self.polys=[box(0,0,3,5),box(2,0,5,5)]

    def test_two_nonoverlap_pixel_medians_and_shared_pixel_exclusion(self):
        out=aggregate(self.polys,self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["raster_pixel_occupancy"],{
            "unassigned_raster_pixels":0,
            "uniquely_assigned_raster_pixels":20,
            "multiply_assigned_raster_pixels":5,
        })
        self.assertEqual(out["objects_with_bounded_raster_proxy"],2)
        self.assertEqual(out["proxy_median_bins_metres_not_surveyed_heights"]["3_to_6m"],1)
        self.assertEqual(out["proxy_median_bins_metres_not_surveyed_heights"]["10_to_15m"],1)
        self.assertFalse(out["overlap_pixels_double_counted"])
        self.assertFalse(out["building_heights_certified"])
        self.assertFalse(out["cat_model_input_admitted"])
        self.assertNotIn("200.0",json.dumps(out))

    def test_fully_overlapping_footprints_do_not_invent_heights(self):
        out=aggregate([self.polys[0],self.polys[0]],self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_no_unique_raster_pixel"],2)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],0)
        self.assertEqual(sum(out["proxy_median_bins_metres_not_surveyed_heights"].values()),0)

    def test_nodata_excluded_from_unique_pixel_medians(self):
        self.ground.mask=np.zeros((5,5),dtype=bool)
        self.ground.mask[:,0]=True
        out=aggregate(self.polys,self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],2)
        self.assertEqual(out["joint_source_valid_pixels"],20)

    def test_below_per_polygon_unique_pixel_quota_is_explicit(self):
        out=aggregate([box(0,0,2,2)],self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_insufficient_unique_valid_pixels"],1)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],0)

    def test_no_raster_pixel_center_in_narrow_polygon_flagged(self):
        out=aggregate([box(0.01,0.01,0.15,0.15)],self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_no_unique_raster_pixel"],1)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],0)

    def test_original_masked_source_coverage_gate(self):
        self.ground.mask=np.ones((5,5),dtype=bool)
        with self.assertRaisesRegex(BuildingProxyError,"coverage"):
            aggregate(self.polys,self.ground,self.surface,self.t,self.study)

    def test_nonlinear_or_nonphysical_lidar_height_difference_rejected(self):
        self.surface[:,:]=1000.0
        with self.assertRaisesRegex(BuildingProxyError,"outlier"):
            aggregate(self.polys,self.ground,self.surface,self.t,self.study)

    def test_outside_region_polygon_is_not_matched(self):
        with self.assertRaisesRegex(BuildingProxyError,"outside exact"):
            aggregate([box(100,100,105,105)],self.ground,self.surface,self.t,self.study)

    def test_wrong_geometry_or_missing_sample_fails(self):
        with self.assertRaisesRegex(BuildingProxyError,"invalid sample"):
            aggregate([],self.ground,self.surface,self.t,self.study)
        with self.assertRaisesRegex(BuildingProxyError,"invalid source building"):
            aggregate([Point(2,2)],self.ground,self.surface,self.t,self.study)

    def test_array_grid_size_and_shape_fails(self):
        with self.assertRaisesRegex(BuildingProxyError,"invalid sample"):
            aggregate(self.polys,self.ground[:2,:],self.surface,self.t,self.study)
        giant=np.ma.array(np.ones((500,500)))
        with self.assertRaisesRegex(BuildingProxyError,"invalid sample"):
            aggregate(self.polys,giant,giant,self.t,self.study)

    def test_clip_to_exact_study_prevents_spurious_outer_pixel_counts(self):
        source=box(-20,-20,2,5)
        out=aggregate([source],self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],1)
        self.assertEqual(out["raster_pixel_occupancy"]["uniquely_assigned_raster_pixels"],10)

    def test_negative_height_proxy_is_not_clamped_to_zero(self):
        self.surface[:,:]=195.0
        out=aggregate([box(0,0,5,5)],self.ground,self.surface,self.t,self.study)
        self.assertEqual(out["objects_with_bounded_raster_proxy"],0)
        self.assertEqual(out["objects_with_negative_median_excluded"],1)
        self.assertEqual(out["objects_with_insufficient_unique_valid_pixels"],1)


if __name__=="__main__":
    unittest.main()
