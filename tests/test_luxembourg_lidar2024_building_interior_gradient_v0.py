# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only central-difference MNS gradients, no rooftop pitch claims."""
from __future__ import annotations

import importlib.util
import json
import math
import unittest

HAS_SPATIAL = all(importlib.util.find_spec(m) for m in ("numpy", "shapely", "rasterio"))
if HAS_SPATIAL:
    import numpy as np
    from rasterio.transform import from_origin
    from shapely.geometry import box
    from research_runners.luxembourg_lidar2024_building_interior_gradient_v0 import (
        InteriorGradientError, local_gradients,
    )


@unittest.skipUnless(HAS_SPATIAL, "Requires pinned optional raster/geometry dependencies")
class InteriorGradientTests(unittest.TestCase):
    def setUp(self):
        self.study = box(0, 0, 10, 10)
        self.affine = from_origin(0, 10, 1, 1)
        x = np.arange(10, dtype=float)[None, :]
        self.terrain = np.ma.array(np.full((10, 10), 100.0), mask=False)
        # Exactly 10 degree continuous synthetic surface (no voxel 'roof' claim).
        self.surface = np.ma.array(
            np.broadcast_to(110.0 + math.tan(math.radians(10)) * x, (10, 10)).copy(),
            mask=False,
        )

    def run_proxy(self, polygons=None):
        return local_gradients(
            polygons or [self.study],
            self.terrain, self.surface, self.affine, self.study
        )

    def test_flat_surface_has_no_inferred_roof_pitch(self):
        self.surface[:,:] = 110.0
        result = self.run_proxy()
        self.assertEqual(result["footprints_with_surface_gradient_proxy"], 1)
        self.assertEqual(result["median_mns_surface_gradient_bins_not_roof_pitch"]["0_to_5_degrees"], 1)
        self.assertFalse(result["true_roof_pitch_validated"])
        self.assertFalse(result["model_input_admitted"])

    def test_continuous_10_degree_source_gradient_is_not_roof_slope(self):
        result = self.run_proxy()
        self.assertEqual(result["median_mns_surface_gradient_bins_not_roof_pitch"]["5_to_15_degrees"], 1)
        self.assertEqual(result["interior_stencil_centres_before_steepness_screen"], 64)
        self.assertFalse(result["solar_facet_tilt_or_aspect_observed"])

    def test_shared_footprint_pixels_not_double_assigned(self):
        polygons = [box(0, 0, 6, 10), box(4, 0, 10, 10)]
        r = self.run_proxy(polygons)
        self.assertEqual(r["footprints_with_surface_gradient_proxy"], 2)
        self.assertEqual(r["multiply_assigned_source_pixels"], 20)
        self.assertEqual(sum(r["median_mns_surface_gradient_bins_not_roof_pitch"].values()), 2)
        self.assertNotIn("100.0", json.dumps(r))

    def test_tiny_footprint_reports_insufficient_not_zero_slope(self):
        r = self.run_proxy([box(0,0,2,2)])
        self.assertEqual(r["footprints_without_enough_clean_interior_stencils"], 1)
        self.assertEqual(sum(r["median_mns_surface_gradient_bins_not_roof_pitch"].values()), 0)

    def test_full_mask_and_low_coverage_are_blocked(self):
        self.terrain.mask = np.ones((10,10), dtype=bool)
        with self.assertRaisesRegex(InteriorGradientError, "Insufficient joint finite"):
            self.run_proxy()

    def test_source_grid_shape_difference_is_blocked(self):
        with self.assertRaisesRegex(InteriorGradientError, "bounded raster"):
            local_gradients([self.study], self.terrain[:5], self.surface,
                            self.affine, self.study)

    def test_vertical_walls_70_degree_screen_excludes_unphysical_stencils(self):
        # Large constant X derivative implies steep (not trusted) surface.
        x = np.arange(10, dtype=float)[None, :]
        self.surface[:,:] = 110.0 + 10 * x
        r = self.run_proxy()
        self.assertEqual(r["footprints_with_surface_gradient_proxy"], 0)
        self.assertEqual(r["footprints_without_enough_clean_interior_stencils"], 1)
        self.assertGreater(r["stencil_centres_ge_70_degrees_excluded"], 0)

    def test_nonphysical_surface_terrain_outliers_block(self):
        self.surface[3,3] = 350
        with self.assertRaisesRegex(InteriorGradientError, "MNS-minus-MNT"):
            self.run_proxy()

    def test_negative_surface_terrain_cells_dont_count_as_roofs(self):
        self.surface[:,:] = 99.0
        r = self.run_proxy()
        self.assertEqual(r["footprints_with_surface_gradient_proxy"], 0)
        self.assertEqual(r["footprints_without_enough_clean_interior_stencils"], 1)

    def test_polygon_outside_study_blocks(self):
        with self.assertRaisesRegex(InteriorGradientError, "misses exact"):
            self.run_proxy([box(20,20,25,25)])

    def test_source_noise_and_nodata_reduce_valid_stencils(self):
        self.terrain.mask = np.zeros((10,10), dtype=bool)
        self.terrain.mask[2:9, 4:7] = True
        result = self.run_proxy()
        self.assertLess(result["interior_stencil_centres_before_steepness_screen"], 64)
        self.assertFalse(result["source_building_ids_or_raw_values_exported"])


if __name__ == "__main__":
    unittest.main()
