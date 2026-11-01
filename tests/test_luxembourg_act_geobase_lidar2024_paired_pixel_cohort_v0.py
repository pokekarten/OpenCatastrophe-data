# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only strict paired spatial-source / shared LiDAR pixel checks."""
from __future__ import annotations

import importlib.util
import json
import unittest

HAS_SPATIAL=all(importlib.util.find_spec(x) is not None
                for x in ("numpy","rasterio","pyproj","shapely"))
if HAS_SPATIAL:
    import numpy as np
    from rasterio.transform import from_origin
    from shapely.geometry import box
    from research_runners.luxembourg_act_geobase_lidar2024_paired_pixel_cohort_v0 import (
        PairedSourceError, paired_pixel_diagnostic, strict_spatial_pairs,
    )


@unittest.skipUnless(HAS_SPATIAL,"Pinned optional spatial research runtime required")
class PairedSourcePixelTests(unittest.TestCase):
    def setUp(self):
        self.region=box(0,0,10,10)
        self.affine=from_origin(0,10,1,1)
        self.dtm=np.ma.array(np.full((10,10),200.0),mask=False)
        self.dsm=np.ma.array(np.full((10,10),210.0),mask=False)

    def probe(self,a,b):
        return paired_pixel_diagnostic(a,b,self.dtm,self.dsm,self.affine,self.region)

    def test_identical_cohort_zero_median_delta_not_physical_identity(self):
        a=[box(0,0,5,10),box(5,0,10,10)]
        b=[box(0,0,5,10),box(5,0,10,10)]
        report=self.probe(a,b)
        self.assertEqual(report["geometry_unique_uncontested_candidate_pairs"],2)
        self.assertEqual(report["paired_source_geometry_height_proxy_pairs_eligible"],2)
        self.assertEqual(report["paired_unique_shared_raster_pixels_aggregate"],100)
        self.assertEqual(report["absolute_paired_median_surface_minus_terrain_difference_bins"]["below_0_5m"],2)
        self.assertFalse(report["independently_verified_same_physical_building"])
        self.assertFalse(report["source_rights_or_cat_model_admitted"])
        self.assertFalse(report["original_pixel_grids_exported"])
        self.assertNotIn("210.0",json.dumps(report))

    def test_source_mask_shift_changes_medians_without_source_height_change(self):
        self.dsm[:,:]=210.0
        self.dsm[:,5:]=230.0
        a=[box(1,0,6,10)]
        b=[box(2,0,7,10)]
        report=self.probe(a,b)
        self.assertEqual(report["paired_source_geometry_height_proxy_pairs_eligible"],1)
        self.assertEqual(sum(report["absolute_paired_median_surface_minus_terrain_difference_bins"].values()),1)

    def test_cropped_small_window_cannot_manufacture_full_polygon_identity(self):
        # In this 10m ROI both clips would appear exactly equal (IoU=1),
        # but the full source shapes mostly extend in opposite directions.
        huge_left=box(-100,0,10,10)
        huge_right=box(0,0,110,10)
        self.assertAlmostEqual(
            huge_left.intersection(self.region).intersection(
                huge_right.intersection(self.region)).area
            / huge_left.intersection(self.region).union(
                huge_right.intersection(self.region)).area, 1.0
        )
        with self.assertRaisesRegex(PairedSourceError,"No uncontested"):
            self.probe([huge_left],[huge_right])

    def test_small_roof_part_inside_larger_building_counts_as_split_competitor(self):
        large=box(0,0,10,10)
        small=box(0,0,2,2)
        self.assertLess(small.area/large.area,0.2)
        result=strict_spatial_pairs([large,small],[large])
        self.assertEqual(result["high_iou_candidate_pairs"],1)
        self.assertEqual(result["unique_uncontested_spatial_pairs"],0)
        self.assertEqual(result["high_iou_pairs_rejected_as_ambiguous"],1)
        with self.assertRaisesRegex(PairedSourceError,"No uncontested"):
            self.probe([large,small],[large])

    def test_high_iou_but_split_merge_competitor_must_be_rejected(self):
        a=[box(0,0,6,10),box(3,0,9,10)]
        b=[box(0,0,6,10)]
        r=strict_spatial_pairs(a,b)
        self.assertEqual(r["high_iou_candidate_pairs"],1)
        self.assertEqual(r["unique_uncontested_spatial_pairs"],0)
        self.assertEqual(r["high_iou_pairs_rejected_as_ambiguous"],1)
        with self.assertRaisesRegex(PairedSourceError,"No uncontested"):
            self.probe(a,b)

    def test_no_proximate_geometry_pairs_fails(self):
        with self.assertRaisesRegex(PairedSourceError,"No uncontested"):
            self.probe([box(0,0,3,10)],[box(7,0,10,10)])

    def test_nodata_does_not_become_fake_height(self):
        self.dtm.mask=np.ones((10,10),dtype=bool)
        with self.assertRaisesRegex(PairedSourceError,"Insufficient"):
            self.probe([box(0,0,10,10)],[box(0,0,10,10)])

    def test_too_few_unique_shared_pixels_fail_closed(self):
        with self.assertRaisesRegex(PairedSourceError,"No shared-pixel"):
            self.probe([box(0,0,1,1)],[box(0,0,1,1)])

    def test_nonphysical_height_difference_blocks(self):
        self.dsm[:,:]=1000.0
        with self.assertRaisesRegex(PairedSourceError,"Implausible"):
            self.probe([box(0,0,10,10)],[box(0,0,10,10)])

    def test_negative_original_proxy_not_a_zero_metre_roof(self):
        self.dsm[:,:]=195.0
        with self.assertRaisesRegex(PairedSourceError,"No shared-pixel"):
            self.probe([box(0,0,10,10)],[box(0,0,10,10)])

    def test_duplicate_sources_not_uncontested(self):
        r=strict_spatial_pairs([box(0,0,10,10),box(0,0,10,10)],
                               [box(0,0,10,10)])
        self.assertEqual(r["unique_uncontested_spatial_pairs"],0)

    def test_wrong_or_outside_polygon_fails(self):
        from shapely.geometry import Point
        with self.assertRaisesRegex(PairedSourceError,"Invalid polygon"):
            strict_spatial_pairs([Point(0,0)],[box(0,0,10,10)])
        with self.assertRaisesRegex(PairedSourceError,"Invalid bounded"):
            strict_spatial_pairs([],[])

    def test_quality_count_conservation_mixed_cohort(self):
        a=[box(0,0,5,10),box(5,0,10,10)]
        b=[box(0,0,5,10),box(5,0,10,10)]
        self.dsm.mask=np.zeros((10,10),dtype=bool)
        self.dsm.mask[:,0:5]=True
        result=self.probe(a,b)
        self.assertEqual(result["paired_source_geometry_height_proxy_pairs_eligible"],1)
        self.assertEqual(result["paired_source_insufficient_joint_unique_pixel_pairs"],1)
        self.assertEqual(result["geometry_unique_uncontested_candidate_pairs"],2)


if __name__=="__main__":
    unittest.main()
