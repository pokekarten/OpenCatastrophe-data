# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only disjoint building-exterior raw-code support tests."""
from __future__ import annotations

import importlib.util
import unittest

from research_runners.berlin_bld4_bkg_exterior_ring_raw_support_v0 import (
    BANDS_METRES, RealSupportError, audit_disjoint_exterior_bands,
)

SPATIAL = all(importlib.util.find_spec(x) is not None for x in
              ("shapely","numpy","rasterio"))


@unittest.skipUnless(SPATIAL, "pinned spatial deps required in dedicated CI")
class BkgExteriorRingTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        from shapely.geometry import box
        from affine import Affine
        self.box = box
        self.np = np
        self.affine = Affine(1,0,0,0,-1,24)
        self.pilot = box(0,0,24,24)
        self.values = np.ones((24,24), dtype=np.int16)
        self.mask = np.zeros((24,24), dtype=bool)
        self.building = box(10,10,11,11)
        # Building interior is exclusively NoData, neighboring source values
        # are otherwise positive. Source building interior MUST NOT be counted.
        self.mask[13,10] = True

    def test_three_exact_distance_bands_disjoint_and_metric(self):
        out = audit_disjoint_exterior_bands(
            [self.building],self.pilot,self.values,self.mask,self.affine)
        self.assertEqual(out["exterior_rings_m"], [[0,1],[1,3],[3,5]])
        self.assertEqual(len(out["bands"]),3)
        # Axis-aligned square with 1m mitred buffer:
        # 3x3 - 1x1 = 8; 7x7 - 3x3 = 40; 11x11 - 7x7 = 72.
        self.assertEqual([x["unique_exterior_ring_area_m2"] for x in out["bands"]],
                         [8,40,72])
        self.assertEqual([x["positive_raw_integer_supported_area_m2"]
                          for x in out["bands"]],[8,40,72])
        self.assertEqual([x["valid_numeric_support_fraction"]
                          for x in out["bands"]],[1,1,1])
        self.assertFalse(out["cat_model_or_insurer_exposure_admitted"])
        self.assertFalse(out["original_per_building_ids_coords_or_pixel_values_exported"])
        self.assertTrue(out["exterior_rings_not_building_loss_depth"])

    def test_nodata_and_zero_not_promoted_to_positive_or_dry(self):
        v=self.values.copy()
        mask=self.mask.copy()
        # One adjacent ring cell has an authentic zero; another is masked.
        v[13,9]=0
        mask[13,11]=True
        out=audit_disjoint_exterior_bands(
            [self.building],self.pilot,v,mask,self.affine)
        near=out["bands"][0]
        self.assertEqual(near["unique_exterior_ring_area_m2"],8)
        self.assertEqual(near["positive_raw_integer_supported_area_m2"],6)
        self.assertEqual(near["valid_numeric_zero_supported_area_m2"],1)
        self.assertEqual(near["original_masked_nodata_area_m2"],1)
        self.assertEqual(near["valid_numeric_support_fraction"],.875)
        self.assertTrue(out["building_raster_nodata_never_interpreted_as_dry"])

    def test_neighbor_building_excluded_from_sample_rings(self):
        # Two different source polygons; ring union may overlap, but must
        # never count other original building footprints as exterior water.
        other=self.box(12,10,13,11)
        mask=self.mask.copy()
        mask[13,12]=True
        out=audit_disjoint_exterior_bands(
            [self.building,other],self.pilot,self.values,mask,self.affine)
        self.assertEqual(out["original_buildings_count"],2)
        self.assertLess(out["bands"][0]["unique_exterior_ring_area_m2"],16)
        for band in out["bands"]:
            a=band["positive_raw_integer_supported_area_m2"]
            z=band["valid_numeric_zero_supported_area_m2"]
            n=band["original_masked_nodata_area_m2"]
            o=band["outside_sample_window_area_m2"]
            self.assertAlmostEqual(band["unique_exterior_ring_area_m2"],a+z+n+o,5)

    def test_exact_pilot_clip_blocks_outer_unknown_inference(self):
        small_pilot=self.box(0,0,11,24)
        out=audit_disjoint_exterior_bands(
            [self.building],small_pilot,self.values,self.mask,self.affine)
        self.assertLess(out["bands"][0]["unique_exterior_ring_area_m2"],8)
        self.assertEqual(out["bands"][0]["outside_sample_window_area_m2"],0)
        self.assertEqual(out["bands"][0]["original_masked_nodata_area_m2"],0)

    def test_unmasked_negative_raw_code_is_blocker_in_outer_ring(self):
        arr=self.values.copy()
        arr[13,9]=-1
        with self.assertRaisesRegex(RealSupportError,"negative raw integer"):
            audit_disjoint_exterior_bands(
                [self.building],self.pilot,arr,self.mask,self.affine)

    def test_unclipped_building_and_invalid_pilot_are_blocked(self):
        for polys,pilot in (
            ([self.box(-1,10,11,11)],self.pilot),
            ([self.building],self.box(0,0,5,5)),
            ([],self.pilot),
            ([self.building]*6,self.pilot),
        ):
            with self.subTest(n=len(polys)),self.assertRaises(RealSupportError):
                audit_disjoint_exterior_bands(
                    polys,pilot,self.values,self.mask,self.affine)

    def test_ring_outside_sample_not_mislabelled_no_data_or_dry(self):
        # Small raster still valid 1m north-up. Pilot is a different,
        # larger source-original geometry than the sample window.
        small=self.np.ones((17,17),dtype=self.np.int16)
        mask=self.np.zeros_like(small,dtype=bool)
        out=audit_disjoint_exterior_bands(
            [self.building],self.pilot,small,mask,self.affine)
        self.assertGreater(sum(x["outside_sample_window_area_m2"]
                               for x in out["bands"]),0)


if __name__ == "__main__":
    unittest.main()
