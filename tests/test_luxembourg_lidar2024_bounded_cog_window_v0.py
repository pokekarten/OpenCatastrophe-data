# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only 50cm local GeoTIFF test: NEVER fetch 40GB original COG."""
from __future__ import annotations

import importlib.util
import unittest

REQUIRED=all(importlib.util.find_spec(x) for x in ("rasterio","numpy","pyproj"))
from research_runners.luxembourg_lidar2024_bounded_cog_window_v0 import (
    CogWindowError,native_bbox,bounded_window_from_source,compute_proxy
)


@unittest.skipUnless(REQUIRED,"Optional pinned Rasterio/Numpy/PyProj research-only profile")
class LocalRasterWindowTests(unittest.TestCase):
    def synthetic(self, *,epsg=2169,res=0.5,width=800,height=800):
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        xlo,ylo,xhi,yhi=native_bbox()
        file=MemoryFile()
        source=file.open(
            driver="GTiff",width=width,height=height,count=1,
            dtype="float32",crs=f"EPSG:{epsg}",
            transform=from_origin(xlo-40,yhi+40,res,res),
            nodata=-9999,
        )
        source.write(np.full((height,width),211.0,dtype=np.float32),1)
        return file,source

    def test_original_city_window_stays_bounded(self):
        mem,src=self.synthetic()
        try:
            window=bounded_window_from_source(src,native_bbox())
            self.assertLessEqual(window.width,1024)
            self.assertLessEqual(window.height,1024)
            self.assertLessEqual(window.width*window.height,1000000)
            self.assertGreater(window.width,400)
            self.assertGreater(window.height,400)
            self.assertFalse(src.read(1,window=window,masked=True).mask.any())
        finally:
            src.close();mem.close()

    def test_malformed_epsg_rejected(self):
        mem,src=self.synthetic(epsg=3857)
        try:
            with self.assertRaisesRegex(CogWindowError,"CRS"):
                bounded_window_from_source(src,native_bbox())
        finally:
            src.close();mem.close()

    def test_unexpected_resolution_rejected(self):
        mem,src=self.synthetic(res=2.0)
        try:
            with self.assertRaisesRegex(CogWindowError,"resolution"):
                bounded_window_from_source(src,native_bbox())
        finally:
            src.close();mem.close()

    def test_outside_coverage_rejected(self):
        mem,src=self.synthetic(width=80,height=80)
        try:
            with self.assertRaisesRegex(CogWindowError,"outside"):
                bounded_window_from_source(src,native_bbox())
        finally:
            src.close();mem.close()

    def test_joint_masked_height_distribution_preserves_vegetation_limit(self):
        import numpy as np
        ground=np.ma.array([[200,200,200],[200,200,200]],mask=False,dtype=float)
        surface=np.ma.array([[203,209,200],[206,205,215]],mask=False,dtype=float)
        report=compute_proxy(ground,surface)
        self.assertEqual(report["valid_joint_pixels"],6)
        self.assertEqual(report["surface_minus_terrain_median_metres"],5.5)
        self.assertEqual(report["surface_minus_terrain_min_metres"],0)
        self.assertEqual(report["surface_minus_terrain_max_metres"],15)
        self.assertEqual(report["fraction_valid_pixels_above_3m_rounded_6dp"],round(4/6,6))

    def test_masked_nodata_not_subtracted_as_zero(self):
        import numpy as np
        ground=np.ma.array([[200,200],[200,200]],mask=[[1,0],[0,0]],dtype=float)
        surface=np.ma.array([[203,203],[203,203]],mask=False,dtype=float)
        report=compute_proxy(ground,surface)
        self.assertEqual(report["valid_joint_pixels"],3)
        self.assertEqual(report["surface_minus_terrain_median_metres"],3)

    def test_half_coverage_fails_closed(self):
        import numpy as np
        a=np.ma.array([[200,200],[200,200]],mask=[[1,1],[1,0]],dtype=float)
        b=np.ma.array([[201,201],[201,201]],mask=False,dtype=float)
        with self.assertRaisesRegex(CogWindowError,"coverage"):
            compute_proxy(a,b)

    def test_incompatible_dimensions_block(self):
        import numpy as np
        a=np.ma.array([[1,2],[3,4]])
        b=np.ma.array([[1,2]])
        with self.assertRaisesRegex(CogWindowError,"dimensions"):
            compute_proxy(a,b)

    def test_nonphysical_difference_blocks(self):
        import numpy as np
        a=np.ma.array([[200,200],[200,200]],dtype=float)
        b=np.ma.array([[1000,1000],[1000,1000]],dtype=float)
        with self.assertRaisesRegex(CogWindowError,"Nonphysical"):
            compute_proxy(a,b)


if __name__=="__main__":
    unittest.main()
