# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GeoPackageBinary and non-admission metric regressions."""
from __future__ import annotations

import math
import struct
import unittest

from shapely.geometry import MultiPoint
from shapely import wkb
from research_runners.lu_caclr_singleton_position_parity_v0 import (
    ParityError,geopackage_single_point,metric_summary,percentile,
)


def gpkgbinary(xys, *, srs=2169, envelope=0, little=True, flags_add=0):
    flags=(1 if little else 0) | (envelope<<1) | flags_add
    endian="<" if little else ">"
    header=b"GP"+bytes([0,flags])+struct.pack(endian+"i",srs)
    if envelope:
        sizes={1:32,2:48,3:48,4:64}
        header+=bytes(sizes[envelope])
    return header+wkb.dumps(MultiPoint(xys))


class ParitySyntheticTests(unittest.TestCase):
    def test_little_endian_no_envelope(self):
        self.assertEqual(geopackage_single_point(gpkgbinary([(62000,87000)])),
                         (62000,87000))

    def test_big_endian_header_with_xy_envelope(self):
        self.assertEqual(geopackage_single_point(
            gpkgbinary([(62000,87000)],envelope=1,little=False)),(62000,87000))

    def test_xyzm_envelope_offset(self):
        self.assertEqual(geopackage_single_point(
            gpkgbinary([(62000,87000)],envelope=4)),(62000,87000))

    def test_multiple_geopackage_points_are_not_forced_into_one_address(self):
        self.assertIsNone(geopackage_single_point(
            gpkgbinary([(62000,87000),(62100,87000)])))

    def test_wrong_crs_invalid_flags_and_bad_magic_block(self):
        for blob in [gpkgbinary([(62000,87000)],srs=4326),
                     gpkgbinary([(62000,87000)],flags_add=0x20),
                     b"XX"+gpkgbinary([(62000,87000)])[2:],
                     b"GP\x00\x01\x00\x00\x00\x00"]:
            with self.subTest(blob=blob[:4]),self.assertRaises(ParityError):
                geopackage_single_point(blob)

    def test_bad_original_geometry_type_blocked(self):
        from shapely.geometry import Point
        blob=b"GP"+bytes([0,1])+struct.pack("<i",2169)+wkb.dumps(Point(62000,87000))
        with self.assertRaises(ParityError):
            geopackage_single_point(blob)

    def test_outside_national_luref_extent_blocks(self):
        with self.assertRaises(ParityError):
            geopackage_single_point(gpkgbinary([(1,2)]))

    def test_exact_metric_residual_quantiles(self):
        x=metric_summary([0.0,0.1,2.0,12.0,55.0],0)
        self.assertEqual(x["residual_at_most_0_01m"],1)
        self.assertEqual(x["residual_at_most_1m"],2)
        self.assertEqual(x["residual_at_most_10m"],3)
        self.assertEqual(x["residual_at_most_50m"],4)
        self.assertEqual(x["residual_over_50m"],1)
        self.assertEqual(x["median_residual_m"],2)
        self.assertFalse(x["same_physical_address_or_building_proven"])
        self.assertFalse(x["cat_model_input_admitted"])

    def test_not_singlepoint_stays_out_of_denominator(self):
        out=metric_summary([],2)
        self.assertEqual(out["metric_residual_observations"],0)
        self.assertEqual(out["matched_singleton_caclr_key_candidates"],2)
        self.assertIsNone(out["max_residual_m"])

    def test_nonfinite_negative_and_boolean_metric_reject(self):
        for value in (float("nan"),float("inf"),-1.0,True):
            with self.assertRaises(ParityError):
                metric_summary([value],0)

    def test_percentile_interpolation(self):
        self.assertEqual(percentile([0,10,20,30,40],.95),38.0)


if __name__=="__main__":
    unittest.main()
