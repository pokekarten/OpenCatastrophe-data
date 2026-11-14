# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GRIB2 regular lat/lon geometry and NCEI site-grid tests."""

from __future__ import annotations

import copy
import unittest

from research_runners.noaa_mrms_mesh_original_preflight_v0 import (
    MRMSPreflightError,
    SOURCE_OBJECTS,
    _grib_signed_magnitude_i32,
    nominal_grid_cell,
    template0_grid_geography,
)


def _encode_sign_magnitude(value: int) -> bytes:
    if value < 0:
        return ((-value) | 0x80000000).to_bytes(4, "big")
    return value.to_bytes(4, "big")


def grib3(nx: int = 7000, ny: int = 3500,
          first_lat: float = 20.0, first_lon: float = 230.0,
          di: float = 0.01, dj: float = 0.01, scanning: int = 0x40) -> bytes:
    """Synthetic Section 3 template 0: not actual NOAA original source bytes."""
    b = bytearray(72)
    b[:4] = (72).to_bytes(4, "big")
    b[4] = 3
    b[6:10] = (nx * ny).to_bytes(4, "big")
    b[12:14] = (0).to_bytes(2, "big")
    b[30:34] = nx.to_bytes(4, "big")
    b[34:38] = ny.to_bytes(4, "big")
    # zero basic-angle and subdivisions = WMO default microdegrees
    b[46:50] = _encode_sign_magnitude(round(first_lat * 1_000_000))
    b[50:54] = _encode_sign_magnitude(round(first_lon * 1_000_000))
    i_sign = -1 if scanning & 0x80 else 1
    j_sign = 1 if scanning & 0x40 else -1
    last_lat = first_lat + j_sign * (ny - 1) * dj
    last_lon = first_lon + i_sign * (nx - 1) * di
    b[55:59] = _encode_sign_magnitude(round(last_lat * 1_000_000))
    b[59:63] = _encode_sign_magnitude(round(last_lon * 1_000_000))
    b[63:67] = round(di * 1_000_000).to_bytes(4, "big")
    b[67:71] = round(dj * 1_000_000).to_bytes(4, "big")
    b[71] = scanning
    return bytes(b)


class NOAARealGridGeometryTests(unittest.TestCase):
    def test_2021_keller_source_byte_identity_pinned(self) -> None:
        source = SOURCE_OBJECTS["mesh_keller_2021"]
        self.assertEqual(source["compressed_size"], 54463)
        self.assertEqual(source["compressed_sha256"],
                         "7d1fc719f0791e25ddd2919cb5dcea1302caa4150712feebc42b6c0cbe84fdf6")
        self.assertTrue(source["key"].startswith("CONUS/MESH_00.50/20210429/"))
        self.assertEqual(source["mrms_grib_parameter_number"], 28)

    def test_known_conus_geometry_contains_ground_report(self) -> None:
        grid = template0_grid_geography(grib3(), 24500000)
        self.assertEqual(grid["nx"], 7000)
        self.assertEqual(grid["ny"], 3500)
        self.assertEqual(grid["longitude_last_east_0_360_deg"], 299.99)
        self.assertEqual(grid["latitude_last_deg"], 54.99)
        self.assertEqual(grid["longitude_increment_deg"], 0.01)
        cell = nominal_grid_cell(grid, 32.92, -97.29)
        self.assertTrue(cell["within_source_grid_bounds"])
        self.assertEqual(cell["nearest_grid_column"], 3271)
        self.assertEqual(cell["nearest_grid_row"], 1292)
        self.assertFalse(cell["raster_cell_value_read"])
        self.assertTrue(cell["same_location_as_actual_radar_maximum_not_established"])

    def test_reverse_scan_sign_magnitude_and_outside_report(self) -> None:
        grid = template0_grid_geography(
            grib3(first_lat=54.99, first_lon=299.99, scanning=0x80),
            24500000,
        )
        self.assertFalse(grid["i_eastward"])
        self.assertFalse(grid["j_northward"])
        self.assertEqual(grid["latitude_last_deg"], 20.0)
        self.assertEqual(grid["longitude_last_east_0_360_deg"], 230.0)
        self.assertTrue(nominal_grid_cell(grid, 32.92, -97.29)["within_source_grid_bounds"])
        self.assertFalse(nominal_grid_cell(grid, 10.0, -97.29)["within_source_grid_bounds"])
        self.assertEqual(_grib_signed_magnitude_i32(_encode_sign_magnitude(-12)), -12)

    def test_wmo_missing_angle_and_subdivisions_are_default_microdegrees(self) -> None:
        for first, second in (
            (0xffffffff, 0xffffffff),
            (0, 0xffffffff),
            (0xffffffff, 0),
            (1, 1000000),
            (2, 2000000),
            (0, 1000000),
            (1, 0),
        ):
            with self.subTest(first=first, second=second):
                source = bytearray(grib3())
                source[38:42] = first.to_bytes(4, "big")
                source[42:46] = second.to_bytes(4, "big")
                grid = template0_grid_geography(bytes(source), 24500000)
                self.assertEqual(grid["latitude_increment_deg"], 0.01)
                self.assertEqual(grid["longitude_increment_deg"], 0.01)
                self.assertTrue(grid["geometry_checked"])

    def test_reject_corrupt_count_scale_scan_endpoint_and_lat(self) -> None:
        good = grib3()
        for label, offset, replacement in (
            ("points", slice(6, 10), (10).to_bytes(4, "big")),
            ("nx", slice(30, 34), (0).to_bytes(4, "big")),
            ("angle", slice(38, 42), (7).to_bytes(4, "big")),
            ("scan", 71, 0x41),
            ("end", slice(55, 59), (15_000_000).to_bytes(4, "big")),
            ("latitude", slice(46, 50), (91_000_000).to_bytes(4, "big")),
            ("increment", slice(63, 67), (0).to_bytes(4, "big")),
        ):
            with self.subTest(label=label):
                broken = bytearray(good)
                broken[offset] = replacement
                with self.assertRaises(MRMSPreflightError):
                    template0_grid_geography(bytes(broken), 24500000)

    def test_reject_non_regular_template_missing_coord_and_bad_site(self) -> None:
        good = grib3()
        for label, offset, replacement in (
            ("template", slice(12, 14), (30).to_bytes(2, "big")),
            ("section", 4, 4),
            ("missing_lat", slice(46, 50), b"\xff\xff\xff\xff"),
        ):
            with self.subTest(label=label):
                broken = bytearray(good)
                broken[offset] = replacement
                with self.assertRaises(MRMSPreflightError):
                    template0_grid_geography(bytes(broken), 24500000)
        with self.assertRaises(MRMSPreflightError):
            template0_grid_geography(good[:60], 24500000)
        grid = template0_grid_geography(good, 24500000)
        with self.assertRaises(MRMSPreflightError):
            nominal_grid_cell(grid, 92, -97.29)
        with self.assertRaises(MRMSPreflightError):
            nominal_grid_cell({"geometry_checked": False}, 32.92, -97.29)


if __name__ == "__main__":
    unittest.main()
