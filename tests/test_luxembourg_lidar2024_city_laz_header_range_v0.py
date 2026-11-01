# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: fixed city LAZ ZIP-range/public LAS-header contracts."""
from __future__ import annotations

import json
import struct
import unittest

from research_runners.luxembourg_lidar2024_city_laz_header_range_v0 import (
    city_member, local_file_data_offset, las_prefix_info,
    complete_las_header, LAZHeaderError,
)


def zip_dir(name="77000_75500.laz", method=0, flags=0,
            comp_size=1048576, uncomp_size=1048576, offset=17):
    raw=name.encode("ascii")
    record=struct.pack(
        "<IHHHHHHIIIHHHHHII",
        0x02014B50,20,20,flags,method,0,0,0,
        comp_size,uncomp_size,len(raw),0,0,0,0,0,offset
    )
    return record+raw


def zip_local(name="77000_75500.laz", method=0, flags=0, extra=b""):
    raw=name.encode("ascii")
    return struct.pack(
        "<IHHHHHIIIHH",
        0x04034B50,20,flags,method,0,0,0,1048576,1048576,
        len(raw),len(extra)
    )


def las_header(minor=4, points=234567, point_format=0x86):
    size={2:227,3:235,4:375}[minor]
    out=bytearray(size)
    out[:4]=b"LASF"
    out[24]=1
    out[25]=minor
    struct.pack_into("<H",out,94,size)
    struct.pack_into("<I",out,96,2092)
    struct.pack_into("<I",out,100,2)
    out[104]=point_format
    struct.pack_into("<H",out,105,30)
    struct.pack_into("<I",out,107,points if minor<4 else 0)
    if minor==4:
        struct.pack_into("<Q",out,247,points)
    return bytes(out)


class LAZHeaderRangeTests(unittest.TestCase):
    def test_original_selected_city_filename_recognised(self):
        m=city_member(zip_dir(),expected_members=1)
        self.assertEqual(m["method"],0)
        self.assertEqual(m["offset"],17)
        self.assertEqual(m["name_raw"],b"77000_75500.laz")

    def test_deflate_explicit_not_silently_treated_as_stored(self):
        m=city_member(zip_dir(method=8,comp_size=600000),expected_members=1)
        self.assertEqual(m["method"],8)
        self.assertLess(m["compressed"],m["uncompressed"])

    def test_no_city_member_fails(self):
        with self.assertRaisesRegex(LAZHeaderError,"single selected"):
            city_member(zip_dir(name="77000_76000.laz"),expected_members=1)

    def test_duplicate_tile_members_fail(self):
        data=zip_dir(offset=10)+zip_dir(offset=100)
        with self.assertRaisesRegex(LAZHeaderError,"single selected"):
            city_member(data,expected_members=2)

    def test_encrypted_zip_member_rejected(self):
        with self.assertRaisesRegex(LAZHeaderError,"encrypted"):
            city_member(zip_dir(flags=1),expected_members=1)

    def test_zip64_sentinel_rejected(self):
        with self.assertRaisesRegex(LAZHeaderError,"ZIP64"):
            city_member(zip_dir(comp_size=0xffffffff),expected_members=1)

    def test_local_header_must_agree_with_directory(self):
        m=city_member(zip_dir(),expected_members=1)
        offset, length=local_file_data_offset(zip_local(),m)
        self.assertEqual(offset,17+30+len(m["name_raw"]))
        self.assertEqual(length,len(m["name_raw"]))
        with self.assertRaisesRegex(LAZHeaderError,"compression or flag drift"):
            local_file_data_offset(zip_local(method=8),m)

    def test_las14_header_public_metadata_only(self):
        b=las_header()
        pre=las_prefix_info(b[:110],member_size=1000000)
        out=complete_las_header(b[:110],b[110:],pre)
        self.assertEqual(out["original_tile_points_declared_by_las_header"],234567)
        self.assertEqual(out["point_record_format"],6)
        self.assertTrue(out["laz_compressed_bit_declared"])
        self.assertFalse(out["building_class_6_points_counted"])
        self.assertFalse(out["high_vegetation_class_5_points_counted"])
        self.assertFalse(out["original_crs_from_vlr_verified"])
        self.assertNotIn("x_coordinate",json.dumps(out))

    def test_legacy_las12_header_with_point_count(self):
        b=las_header(minor=2,points=32000,point_format=1)
        pre=las_prefix_info(b[:110],member_size=1000000)
        out=complete_las_header(b[:110],b[110:],pre)
        self.assertEqual(out["las_version"],"1.2")
        self.assertEqual(out["original_tile_points_declared_by_las_header"],32000)

    def test_wrong_las_signature_fails_closed(self):
        b=b"ABCD"+las_header()[4:]
        with self.assertRaisesRegex(LAZHeaderError,"LASF"):
            las_prefix_info(b[:110],member_size=1000000)

    def test_bad_las_header_size_fails_closed(self):
        b=bytearray(las_header())
        struct.pack_into("<H",b,94,227)
        with self.assertRaisesRegex(LAZHeaderError,"Invalid LAS"):
            las_prefix_info(bytes(b[:110]),member_size=1000000)

    def test_impossible_point_offset_fails_closed(self):
        b=bytearray(las_header())
        struct.pack_into("<I",b,96,100)
        with self.assertRaisesRegex(LAZHeaderError,"Invalid LAS"):
            las_prefix_info(bytes(b[:110]),member_size=1000000)

    def test_mismatched_full_header_fails_closed(self):
        b=las_header()
        pre=las_prefix_info(b[:110],member_size=1000000)
        with self.assertRaisesRegex(LAZHeaderError,"size changed"):
            complete_las_header(b[:110],b[110:-1],pre)

    def test_zero_original_point_population_fails_closed(self):
        b=las_header(points=0)
        pre=las_prefix_info(b[:110],member_size=1000000)
        with self.assertRaisesRegex(LAZHeaderError,"Unbounded"):
            complete_las_header(b[:110],b[110:],pre)

    def test_no_source_point_positions_or_classes_in_results(self):
        b=las_header()
        out=complete_las_header(b[:110],b[110:],las_prefix_info(b[:110],member_size=1000000))
        self.assertFalse(out["actual_point_records_read"])
        self.assertFalse(out["copc_vlr_verified"])


if __name__=="__main__":
    unittest.main()
