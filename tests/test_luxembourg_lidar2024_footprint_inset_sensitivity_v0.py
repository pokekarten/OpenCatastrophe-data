# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic square-footprint rasters; no original building source material."""
from __future__ import annotations

import importlib.util
import json
import unittest

REQUIRED=all(importlib.util.find_spec(z) for z in
             ("numpy","rasterio","shapely","pyproj"))
if REQUIRED:
    import numpy as np
    from shapely.geometry import box
    from rasterio.transform import from_origin
    from research_runners.luxembourg_lidar2024_footprint_inset_sensitivity_v0 import (
        sensitivity,BuildingProxyError,
    )


@unittest.skipUnless(REQUIRED,"requires pinned optional spatial research runtime")
class FootprintInsetResearchTests(unittest.TestCase):
    def setUp(self):
        self.study=box(0,0,9,7)
        self.affine=from_origin(0,7,1,1)
        self.polygons=[box(0,0,5,7),box(4,0,9,7)]
        self.dtm=np.ma.array(np.full((7,9),200.0),mask=False)
        self.dsm=np.ma.array(np.array([
            [205,205,205,205,222,212,212,212,212]
            for _ in range(7)],dtype=float),mask=False)

    def analyze(self,**kwargs):
        return sensitivity(self.polygons,self.dtm,self.dsm,
                           self.affine,self.study,**kwargs)

    def test_synthetic_roof_insets_do_not_reintroduce_overlaps(self):
        report=self.analyze()
        self.assertEqual(report["original_shared_raster_pixels_excluded_in_both"],7)
        self.assertEqual(report["baseline_eligible_objects"],2)
        self.assertEqual(report["inset_eligible_objects"],2)
        self.assertEqual(report["same_proxy_median_height_band_both_eligible"],2)
        self.assertEqual(report["proxy_median_band_changed_both_eligible"],0)
        self.assertEqual(report["absolute_inset_vs_baseline_proxy_median_drift_bands"]
                         ["within_0_5m"],2)
        self.assertEqual(report["inset_proxy_median_bins_not_building_heights"]["3_to_6m"],1)
        self.assertEqual(report["inset_proxy_median_bins_not_building_heights"]["10_to_15m"],1)
        self.assertFalse(report["production_exposure_or_cat_model_admitted"])
        self.assertFalse(report["individual_building_id_or_proxy_exported"])
        self.assertNotIn("original_id",json.dumps(report))

    def test_eroded_small_polygon_loses_provisional_cohort(self):
        self.polygons=[box(0,0,4,4)]
        out=self.analyze()
        self.assertEqual(out["baseline_eligible_objects"],1)
        self.assertEqual(out["inset_eligible_objects"],0)
        self.assertEqual(out["baseline_eligible_lost_after_inset"],1)
        self.assertEqual(out["previously_ineligible_becoming_eligible"],0)

    def test_complete_duplicate_polygons_create_no_false_eligible(self):
        self.polygons=[box(0,0,5,7)]*2
        out=self.analyze()
        self.assertEqual(out["baseline_eligible_objects"],0)
        self.assertEqual(out["inset_eligible_objects"],0)
        self.assertEqual(out["original_shared_raster_pixels_excluded_in_both"],35)

    def test_clear_negative_roof_proxy_not_relabelled_zero(self):
        self.dsm=np.ma.array(np.full((7,9),197.0),mask=False)
        out=self.analyze()
        self.assertEqual(out["baseline_eligible_objects"],0)
        self.assertEqual(out["inset_eligible_objects"],0)

    def test_all_nodata_original_data_rejected(self):
        self.dtm.mask=np.ones((7,9),dtype=bool)
        with self.assertRaisesRegex(BuildingProxyError,"coverage"):
            self.analyze()

    def test_nonphysical_source_difference_rejected(self):
        self.dsm[:,:]=1000
        with self.assertRaisesRegex(BuildingProxyError,"outlier"):
            self.analyze()

    def test_report_is_deterministic_and_no_measurement_list(self):
        a=self.analyze()
        b=self.analyze()
        self.assertEqual(a,b)
        self.assertNotIn("per_building",a)
        self.assertNotIn("raw",a)

    def test_invalid_shrink_parameters_fail_closed(self):
        for bad in (-1,0,0.2,10,float("nan"),float("inf")):
            with self.subTest(bad=bad),self.assertRaisesRegex(BuildingProxyError,"inputs"):
                self.analyze(inset=bad)

    def test_wrong_raster_shape_or_oversize_fails(self):
        with self.assertRaisesRegex(BuildingProxyError,"inputs"):
            sensitivity(self.polygons,self.dtm[:3,:],self.dsm,self.affine,self.study)
        massive=np.ma.array(np.ones((500,500)))
        with self.assertRaisesRegex(BuildingProxyError,"inputs"):
            sensitivity(self.polygons,massive,massive,self.affine,self.study)

    def test_roof_polygon_outside_study_is_rejected(self):
        self.polygons=[box(100,100,103,103)]
        with self.assertRaisesRegex(BuildingProxyError,"outside exact"):
            self.analyze()

    def test_no_buildings_and_nonpolygon_geometry_rejected(self):
        with self.assertRaisesRegex(BuildingProxyError,"inputs"):
            sensitivity([],self.dtm,self.dsm,self.affine,self.study)
        from shapely.geometry import Point
        self.polygons=[Point(1,1)]
        with self.assertRaisesRegex(BuildingProxyError,"invalid source"):
            self.analyze()

    def test_inset_erosion_stability_across_two_sizes(self):
        half=self.analyze(inset=0.5)
        one=self.analyze(inset=1.0)
        self.assertLessEqual(one["inset_eligible_objects"],
                             half["inset_eligible_objects"])
        self.assertEqual(one["previously_ineligible_becoming_eligible"],0)

    def test_original_shared_pixels_cannot_join_inset_even_if_middle_vegetated(self):
        self.dsm[:,4]=400.0
        out=self.analyze()
        self.assertEqual(out["baseline_eligible_objects"],2)
        self.assertEqual(out["inset_eligible_objects"],2)
        self.assertEqual(out["absolute_inset_vs_baseline_proxy_median_drift_bands"]
                         ["within_0_5m"],2)


if __name__=="__main__":
    unittest.main()
