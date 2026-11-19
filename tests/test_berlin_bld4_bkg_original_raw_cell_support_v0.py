# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic tests; no original building, TIFF or WFS/HTTP requests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

HAVE_SPATIAL = all(importlib.util.find_spec(x) is not None
                   for x in ("numpy", "shapely", "rasterio", "pyproj"))

from research_runners.berlin_bld4_bkg_original_raw_cell_support_v0 import (
    RealSupportError, audit_cells, audit,
)


@unittest.skipUnless(HAVE_SPATIAL, "Required pinned spatial dependencies tested in dedicated CI")
class RealRawSupportTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        from shapely.geometry import box
        from affine import Affine
        self.box = box
        self.arr = np.array([[5,0],[0,-9999]], dtype=np.int16)
        self.missing = np.array([[False,False],[False,True]])
        self.a = Affine(1,0,100,0,-1,202)

    def test_exact_partial_cells_and_nodata_never_zero(self):
        # One 2x2 m original geometry, exactly covers all four cells.
        r = audit_cells([self.box(100,200,102,202)],self.arr,self.missing,self.a)
        self.assertEqual(r["pilot_clipped_buildings_checked"],1)
        self.assertEqual(r["clipped_building_area_in_raster_crs_m2"],4)
        self.assertEqual(r["positive_raw_code_supported_area_m2"],1)
        self.assertEqual(r["valid_zero_raw_code_supported_area_m2"],2)
        self.assertEqual(r["original_nodata_supported_area_m2"],1)
        self.assertEqual(r["outside_sample_window_area_m2"],0)
        self.assertEqual(r["buildings_with_any_positive_raw_code"],1)
        self.assertEqual(r["buildings_with_all_area_valid_numeric_codes"],0)
        self.assertTrue(r["positive_raw_code_not_confirmed_as_metres_of_depth"])
        self.assertFalse(r["actual_insurance_exposure_or_loss_estimated"])
        self.assertNotIn("100",str(r))

    def test_polygon_fraction_area_not_centroid_classifier(self):
        poly = self.box(100.5,201.0,101.5,202)
        r = audit_cells([poly],self.arr,self.missing,self.a)
        self.assertAlmostEqual(r["positive_raw_code_supported_area_m2"],.5)
        self.assertAlmostEqual(r["valid_zero_raw_code_supported_area_m2"],.5)
        self.assertAlmostEqual(r["clipped_building_area_in_raster_crs_m2"],1)
        self.assertEqual(r["buildings_with_all_area_valid_numeric_codes"],1)

    def test_boundary_outside_window_accounted_not_assumed_dry(self):
        poly = self.box(99,201,101,202)
        r = audit_cells([poly],self.arr,self.missing,self.a)
        self.assertEqual(r["outside_sample_window_area_m2"],1)
        self.assertEqual(r["positive_raw_code_supported_area_m2"],1)
        self.assertEqual(r["buildings_with_all_area_valid_numeric_codes"],0)

    def test_all_missing_refuses_to_claim_dry_or_positive(self):
        import numpy as np
        mask=np.ones((2,2),dtype=bool)
        r = audit_cells([self.box(100,200,102,202)],self.arr,mask,self.a)
        self.assertEqual(r["original_nodata_supported_area_m2"],4)
        self.assertEqual(r["valid_zero_raw_code_supported_area_m2"],0)
        self.assertEqual(r["positive_raw_code_supported_area_m2"],0)
        self.assertEqual(r["buildings_without_valid_numeric_codes"],1)

    def test_negative_unmasked_code_is_scientific_blocker(self):
        import numpy as np
        m = np.zeros((2,2),dtype=bool)
        with self.assertRaisesRegex(RealSupportError,"negative raw integer"):
            audit_cells([self.box(101,200,102,201)],self.arr,m,self.a)

    def test_bad_mask_type_or_nonmeter_grid_refused(self):
        import numpy as np
        from affine import Affine
        for raw,mask,a in (
            (self.arr,self.arr,self.a),
            (self.arr.astype(float),self.missing,self.a),
            (self.arr,self.missing,Affine(2,0,100,0,-2,202)),
            (self.arr,self.missing,Affine(1,0.2,100,0,-1,202)),
        ):
            with self.subTest(dtype=str(raw.dtype),a=a),self.assertRaises(RealSupportError):
                audit_cells([self.box(100,200,102,202)],raw,mask,a)

    def test_overlapping_buildings_not_an_individual_export(self):
        # Original BLD4 reader guards overlap; support helper separately
        # returns only aggregates, never polygons, building IDs or positions.
        r=audit_cells([self.box(100,201,101,202),self.box(101,201,102,202)],
                      self.arr,self.missing,self.a)
        self.assertEqual(r["pilot_clipped_buildings_checked"],2)
        self.assertEqual(r["buildings_with_any_positive_raw_code"],1)
        self.assertFalse(r["individual_building_or_cell_values_exported"])
        self.assertFalse(r["actual_insurance_exposure_or_loss_estimated"])

    def test_original_source_exact_size_required_before_raster_open(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fake.tif"
            path.write_bytes(b"II*\0" + b"\0"*200)
            with self.assertRaisesRegex(RealSupportError,"size changed"):
                audit(Path(td)/"fake.cat.sqlite",path)


if __name__=="__main__":
    unittest.main()
