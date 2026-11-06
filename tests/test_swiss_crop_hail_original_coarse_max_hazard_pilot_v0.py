# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network Swiss LV95 grid/max-hail study support tests."""
from __future__ import annotations

import importlib.util
import unittest

from research_runners import swiss_crop_hail_original_coarse_max_hazard_pilot_v0 as pilot
from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked


class SwissCoarseHailAggregationTests(unittest.TestCase):
    def test_fixed_2056_grid_indices_bin_edges_and_out_of_bounds(self):
        import numpy as np
        ids, ix, iy, n = pilot.grid_bins_projected(
            np.asarray([pilot.MIN_X_M + 1, pilot.MIN_X_M + 2001]),
            np.asarray([pilot.MIN_Y_M + 1, pilot.MIN_Y_M + 1]),
            2,
        )
        self.assertEqual(list(ix), [0, 1])
        self.assertEqual(list(iy), [0, 0])
        self.assertEqual(list(ids), [0, n // (int((pilot.MAX_X_M-pilot.MIN_X_M+1999)//2000)+1)])
        self.assertGreater(n, 10)

    def test_unsupported_grid_resolution_blocks(self):
        import numpy as np
        for size in (0, 1, 3, 16, 2.0):
            with self.subTest(km=size):
                with self.assertRaises(Blocked):
                    pilot.grid_bins_projected(np.asarray([2600000]), np.asarray([1200000]), size)

    def test_coordinates_outside_study_LV95_grid_block(self):
        import numpy as np
        with self.assertRaises(Blocked):
            pilot.grid_bins_projected(np.asarray([pilot.MIN_X_M-1]),
                                      np.asarray([pilot.MIN_Y_M+1]), 8)

    @unittest.skipUnless(importlib.util.find_spec("scipy") and importlib.util.find_spec("pyproj"),
                         "Requires pinned Swiss grid geometry packages in dedicated original source workflow")
    def test_max_radar_in_same_2km_swiss_cell_and_is_event_specific(self):
        import numpy as np
        from scipy.sparse import csr_matrix
        from pyproj import Transformer
        x = [2600500, 2601400]
        y = [1200500, 1200500]
        to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
        lon, lat = to_wgs.transform(x, y)
        src = np.zeros((12,2),dtype="float32")
        src[0] = [20,40]
        src[1] = [10,0]
        radar={"variable":"MESHS", "dates":tuple(range(100,112)),
               "lat":np.asarray(lat), "lon":np.asarray(lon),
               "csr":csr_matrix(src), "published_nonzero_hazard_values":3}
        aggregated=pilot.aggregate_hazard_fixed_swiss_grid(radar,2)
        ids, *_ = pilot.grid_bins_projected(np.asarray(x), np.asarray(y),2)
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(float(aggregated["csr"][0,ids[0]]), 40.)
        self.assertEqual(float(aggregated["csr"][1,ids[0]]), 10.)
        self.assertEqual(float(aggregated["csr"][2,ids[0]]), 0.)
        self.assertEqual(aggregated["aggregate_operation"],"max")

    @unittest.skipUnless(importlib.util.find_spec("pyproj"),
                         "Requires Swiss projection package in dedicated original source workflow")
    def test_true_bin_centroids_and_misaligned_coords(self):
        import numpy as np
        from pyproj import Transformer
        to_wgs = Transformer.from_crs("EPSG:2056","EPSG:4326",always_xy=True)
        x,y=pilot.MIN_X_M+4000,pilot.MIN_Y_M+4000
        lon,lat=to_wgs.transform([x], [y])
        coords=np.asarray([[lat[0],lon[0]]])
        ids, n, offset=pilot.map_aggregated_crop_coords(coords,8)
        self.assertEqual(int(ids[0]),0)
        self.assertLess(offset,0.05)
        shifted_lon,shifted_lat=to_wgs.transform([x+1000],[y])
        with self.assertRaisesRegex(Blocked,"do not map one-to-one"):
            pilot.map_aggregated_crop_coords(
                np.asarray([[shifted_lat[0],shifted_lon[0]]]),8)


if __name__=="__main__":
    unittest.main()
