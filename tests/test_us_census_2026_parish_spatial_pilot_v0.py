# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only polygon pilot challenges, never original Census data."""
from __future__ import annotations

import hashlib
import struct
import unittest

from tests.test_us_census_2026_county_zip_audit_v0 import fake_members, zipped
from research_runners.us_census_2026_county_zip_audit_v0 import STEM
from research_runners.us_census_2026_parish_spatial_pilot_v0 import (
    PilotGeometryError, inspect_pilot_bytes,
)


def invented_zip(*, closed=True, ccw=False, xshift=0.0, geoid=None):
    m=fake_members()
    shp=bytearray(m[f"{STEM}.shp"])
    start=100+8+44+4
    points=[struct.unpack_from("<dd",shp,start+i*16) for i in range(5)]
    # The fixture is CCW, unlike correct clockwise Shapefile shells.
    if not ccw:
        points.reverse()
    if not closed:
        points[-1] = (-90.12, 29.9)
    if xshift:
        points[1] = (points[1][0]+xshift,points[1][1])
    for i,pair in enumerate(points):
        struct.pack_into("<dd",shp,start+i*16,*pair)
    m[f"{STEM}.shp"]=bytes(shp)
    if geoid is not None:
        dbf=bytearray(m[f"{STEM}.dbf"])
        hlen=struct.unpack_from("<H",dbf,8)[0]
        dbf[hlen+1+2+3:hlen+1+2+3+5]=geoid
        m[f"{STEM}.dbf"]=bytes(dbf)
    return zipped(m)


class CensusParishPilotTopologyTests(unittest.TestCase):
    def test_synthetic_single_clockwise_source_shape_valid_but_not_admitted(self):
        raw=invented_zip()
        out=inspect_pilot_bytes(
            raw, expected_sha256=hashlib.sha256(raw).hexdigest(),
            geoids=("22071",))
        self.assertTrue(out["selected_original_geometry_valid"])
        self.assertEqual(out["selected_parish_geoids"],["22071"])
        self.assertEqual(out["selected_polygon_qc"][0]["ring_count"],1)
        self.assertEqual(out["selected_polygon_qc"][0]["outer_shells"],1)
        self.assertEqual(out["max_selected_interparish_overlap_square_degrees"],0)
        self.assertFalse(out["native_model_region_assignment_admitted"])
        self.assertFalse(out["any_cat_model_input_admitted"])

    def test_invalid_external_source_hash_blocked(self):
        with self.assertRaises(ValueError):
            inspect_pilot_bytes(invented_zip(),expected_sha256="a"*64,
                                geoids=("22071",))

    def test_reverse_wrong_source_winding_blocked(self):
        with self.assertRaises(PilotGeometryError):
            inspect_pilot_bytes(invented_zip(ccw=True),geoids=("22071",))

    def test_unclosed_original_polygon_ring_blocked(self):
        with self.assertRaises(PilotGeometryError):
            inspect_pilot_bytes(invented_zip(closed=False),geoids=("22071",))

    def test_nonfinite_selected_polygon_coordinates_blocked(self):
        raw=invented_zip(xshift=float("inf"))
        with self.assertRaises(PilotGeometryError):
            inspect_pilot_bytes(raw,geoids=("22071",))

    def test_outside_fixed_louisiana_bbox_blocked(self):
        raw=invented_zip(xshift=90.0)
        with self.assertRaises(PilotGeometryError):
            inspect_pilot_bytes(raw,geoids=("22071",))

    def test_missing_exact_original_parish_id_blocked(self):
        with self.assertRaises(PilotGeometryError):
            inspect_pilot_bytes(invented_zip(),geoids=("22051",))

    def test_duplicate_or_cross_country_parish_requested_blocked(self):
        raw=invented_zip()
        for request in (("22071","22071"),("01001",),("22071","22051","22087","22101")):
            with self.subTest(request=request),self.assertRaises(PilotGeometryError):
                inspect_pilot_bytes(raw,geoids=request)

    def test_tampered_county_geoid_source_archive_is_blocked(self):
        with self.assertRaises(ValueError):
            inspect_pilot_bytes(invented_zip(geoid=b"22070"),geoids=("22071",))

    def test_empty_random_source_bytes_blocked(self):
        with self.assertRaises(ValueError):
            inspect_pilot_bytes(b"not-an-original-zip",geoids=("22071",))


if __name__=="__main__":
    unittest.main()
