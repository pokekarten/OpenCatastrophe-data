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

    def test_official_15s_paired_cell_centres_optional_science_gate(self):
        d = kwargs()
        # N60 is the *north* border, W045 the *west* border;
        # 15 arcseconds = 1/240 degree, first cell is half step in.
        d.update(
            bedrock_lat_deg=[59.9979166667, 59.99375],
            bedrock_lon_deg=[-44.9979166667, -44.99375],
            geoid_lat_deg=[59.9979166667, 59.99375],
            geoid_lon_deg=[-44.9979166667, -44.99375],
        )
        output = run(**d)
        self.assertEqual(output["converted_values_m"], [[12., -2.], [-1., 98.]])
        self.assertTrue(output["supplied_coordinate_arrays_15s_cell_parity_checked"])
        self.assertFalse(output["coordinates_verified_from_original_file_bytes"])
        self.assertFalse(output["sample_spatial_grid_coregistration_independently_verified"])

    def test_reject_shifted_geoid_pixels_missing_axes_and_non_cell_centres(self):
        coords = dict(
            bedrock_lat_deg=[59.9979166667, 59.99375],
            bedrock_lon_deg=[-44.9979166667, -44.99375],
            geoid_lat_deg=[59.9979166667, 59.99375],
            geoid_lon_deg=[-44.9979166667, -44.99375],
        )
        cases = [
            {"geoid_lon_deg": [-44.99375, -44.9895833333]},
            {"geoid_lat_deg": [59.99375, 59.9895833333]},
            {"bedrock_lat_deg": [60., 59.9958333333]},
            {"bedrock_lon_deg": [-45., -44.9958333333]},
            {"bedrock_lon_deg": [-44.9979166667, -44.9979166667]},
            {"geoid_lon_deg": [-44.9979166667, -44.9895833333]},
            {"geoid_lon_deg": [0., 0.00416666667]},
            {"bedrock_lat_deg": [float("nan"), 59.99375]},
            {"geoid_lat_deg": [float("inf"), 59.99375]},
            {"geoid_lat_deg": [True, 59.99375]},
            {"geoid_lon_deg": [-44.9979166667]},
            {"bedrock_lon_deg": None},
            {"geoid_lat_deg": None},
        ]
        for changes in cases:
            d = kwargs()
            d.update(coords)
            d.update(changes)
            with self.subTest(changes=str(changes)), self.assertRaises(ETOPOVerticalBlocked):
                run(**d)

    def test_off_grid_tile_id_rejected_even_when_sample_axes_omitted(self):
        for tile in ["N61W045", "N60W044", "N90E180", "S90W045", "N45E170"]:
            d = kwargs()
            d["bedrock_filename"] = f"ETOPO_2022_v1_15s_{tile}_bed.nc"
            d["geoid_filename"] = f"ETOPO_2022_v1_15s_{tile}_geoid.nc"
            with self.subTest(tile=tile), self.assertRaises(ETOPOVerticalBlocked):
                run(**d)

    def test_reverse_order_supported_only_when_both_products_agree(self):
        d = kwargs()
        d.update(
            bedrock_lat_deg=[59.99375, 59.9979166667],
            bedrock_lon_deg=[-44.99375, -44.9979166667],
            geoid_lat_deg=[59.99375, 59.9979166667],
            geoid_lon_deg=[-44.99375, -44.9979166667],
        )
        self.assertTrue(run(**d)["supplied_coordinate_arrays_15s_cell_parity_checked"])
        d["geoid_lon_deg"] = [-44.9979166667, -44.99375]
        with self.assertRaises(ETOPOVerticalBlocked):
            run(**d)

    def test_three_cell_axis_must_be_monotone_not_zigzag(self):
        # Both products may agree on a malformed [0, 1, 0] axis. Matching
        # two repeated pixel identities is still scientifically invalid.
        lat = [59.9979166667, 59.99375, 59.9895833333]
        lon = [-44.9979166667, -44.99375, -44.9895833333]
        for dimension in ("longitude", "latitude"):
            d = kwargs()
            if dimension == "longitude":
                d["bedrock_elevation_m"] = [[1., 2., 3.]]
                d["geoid_height_m"] = [[1., 1., 1.]]
                d.update(
                    bedrock_lat_deg=lat[:1], geoid_lat_deg=lat[:1],
                    bedrock_lon_deg=lon, geoid_lon_deg=lon,
                )
                zigzag = [lon[0], lon[1], lon[0]]
                d["bedrock_lon_deg"] = zigzag
                d["geoid_lon_deg"] = zigzag
            else:
                d["bedrock_elevation_m"] = [[1.], [2.], [3.]]
                d["geoid_height_m"] = [[1.], [1.], [1.]]
                d.update(
                    bedrock_lat_deg=lat, geoid_lat_deg=lat,
                    bedrock_lon_deg=lon[:1], geoid_lon_deg=lon[:1],
                )
                zigzag = [lat[0], lat[1], lat[0]]
                d["bedrock_lat_deg"] = zigzag
                d["geoid_lat_deg"] = zigzag
            with self.subTest(axis=dimension), self.assertRaisesRegex(
                ETOPOVerticalBlocked, "reverses direction"
            ):
                run(**d)

    def test_three_cell_reverse_order_remains_valid(self):
        d = kwargs()
        d["bedrock_elevation_m"] = [[1., 2., 3.]]
        d["geoid_height_m"] = [[1., 1., 1.]]
        d.update(
            bedrock_lat_deg=[59.9979166667], geoid_lat_deg=[59.9979166667],
            bedrock_lon_deg=[-44.9895833333, -44.99375, -44.9979166667],
            geoid_lon_deg=[-44.9895833333, -44.99375, -44.9979166667],
        )
        out = run(**d)
        self.assertEqual(out["converted_values_m"], [[2., 3., 4.]])
        self.assertTrue(out["supplied_coordinate_arrays_15s_cell_parity_checked"])
        self.assertFalse(out["coordinates_verified_from_original_file_bytes"])

    def test_at_most_ten_thousand_cells(self):
        d=kwargs();d["bedrock_elevation_m"]=[[0.]*101]*100
        d["geoid_height_m"]=[[0.]*101]*100
        with self.assertRaises(ETOPOVerticalBlocked): run(**d)


if __name__ == "__main__": unittest.main()
