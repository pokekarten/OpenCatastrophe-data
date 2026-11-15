# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ETOPO bedrock/geoid vertical-datum safety tests."""
from __future__ import annotations

import math
import unittest
from scripts.etopo2022_bedrock_vertical_conversion_v0 import (
    convert_bedrock_egm2008_to_wgs84 as run, ETOPOVerticalBlocked,
)


def kwargs():
    return dict(
        bedrock_filename="ETOPO_2022_v1_15s_N60W045_bed.nc",
        geoid_filename="ETOPO_2022_v1_15s_N60W045_geoid.nc",
        bedrock_sha256="a"*64, geoid_sha256="b"*64,
        bedrock_elevation_m=[[10.,-5.],[0.,100.]],
        geoid_height_m=[[2.,3.],[-1.,-2.]],
    )


class PairedScientificDatumTests(unittest.TestCase):
    def test_correct_sign_and_grid_conservation(self):
        out = run(**kwargs())
        self.assertEqual(out["converted_values_m"],[[12.,-2.],[-1.,98.]])
        self.assertEqual((out["source_vertical_epsg"],out["output_ellipsoidal_epsg"]),(3855,4979))
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["sample_spatial_grid_coregistration_independently_verified"])
        self.assertEqual(len(out["converted_sample_sha256"]),64)

    def test_wrong_product_version_format_res_and_path_rejected(self):
        for replacement in ("ETOPO_2022_v2_15s_N60W045_bed.nc",
            "ETOPO_2022_v1_30s_N60W045_bed.nc",
            "ETOPO_2022_v1_15s_N60W045_surface.nc",
            "ETOPO_2022_v1_15s_N60W045_bed.tif",
            "../ETOPO_2022_v1_15s_N60W045_bed.nc",
            "ETOPO_2022_v1_15s_N99W045_bed.nc"):
            d=kwargs();d["bedrock_filename"]=replacement
            with self.subTest(filename=replacement), self.assertRaises(ETOPOVerticalBlocked): run(**d)

    def test_other_geographic_tile_rejected(self):
        d=kwargs();d["geoid_filename"]="ETOPO_2022_v1_15s_N45W045_geoid.nc"
        with self.assertRaises(ETOPOVerticalBlocked): run(**d)

    def test_same_source_hash_missing_and_bad_hashes_rejected(self):
        for a,b in [("a"*64,"a"*64),("a"*64,"garbage"),("A"*64,"b"*64)]:
            d=kwargs();d.update(bedrock_sha256=a,geoid_sha256=b)
            with self.subTest(a=a[:4],b=b[:4]), self.assertRaises(ETOPOVerticalBlocked): run(**d)

    def test_ragged_and_mismatched_grid_rejected(self):
        for bed,geo in [([[1.,2.],[3.]], [[1.,2.],[3.,4.]]),
                        ([[1.,2.]],[[1.]]),
                        ([[]],[[1.]]), ([], [[1.]]),
                        ([[1.]],[[1.],[2.]])]:
            d=kwargs();d.update(bedrock_elevation_m=bed,geoid_height_m=geo)
            with self.subTest(bed=bed,geoid=geo),self.assertRaises(ETOPOVerticalBlocked): run(**d)

    def test_nan_inf_bool_and_overflow_rejected(self):
        for v in [float("nan"),float("inf"),True,10**2000]:
            d=kwargs();d["geoid_height_m"]=[[v,3.],[-1.,-2.]]
            with self.subTest(kind=type(v).__name__),self.assertRaises(ETOPOVerticalBlocked): run(**d)

    def test_at_most_ten_thousand_cells(self):
        d=kwargs();d["bedrock_elevation_m"]=[[0.]*101]*100
        d["geoid_height_m"]=[[0.]*101]*100
        with self.assertRaises(ETOPOVerticalBlocked): run(**d)


if __name__ == "__main__": unittest.main()
