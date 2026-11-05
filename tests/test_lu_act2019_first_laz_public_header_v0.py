# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fictional LAZ/LASF public-header and ZIP/Deflate byte-budget regressions."""
from __future__ import annotations

import io
import re
import struct
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from research_runners.lu_act2019_three_zip_directory_range_v0 import (
    MAX_TAIL, locate_eocd, summarize_central,
)
from research_runners.lu_act2019_first_laz_public_header_v0 import (
    MAX_LAZ_ZIP_PREFIX_COMPRESSED_BYTES, PUBLIC_LAS_HEADER_PREFIX_BYTES,
    PublicHeaderError, classify_public_las_prefix,
    first_central_laz_member, zip_deflated_member_first_public_bytes, main,
)

SYNTHETIC_URL=("https://download.data.public.lu/resources/"
               "lidar-2019-releve-3d-du-territoire-luxembourgeois/"
               "20200101-000000/fictional-not-source.zip")


def fake_las(*, major=1,minor=2,signature=b"LASF",format_code=0x83,
             point_offset=227):
    data=bytearray(227)
    data[:4]=signature
    data[24]=major
    data[25]=minor
    struct.pack_into("<H",data,94,227)
    struct.pack_into("<I",data,96,point_offset)
    struct.pack_into("<I",data,100,0)
    data[104]=format_code
    struct.pack_into("<H",data,105,34)
    struct.pack_into("<I",data,107,70)
    return bytes(data)+b"synthetic following bytes are not real LiDAR points"


def fake_zip(*,member_name="invented-first.laz",compression=ZIP_DEFLATED,
             first_body=None):
    buf=io.BytesIO()
    with ZipFile(buf,"w",compression=compression) as z:
        z.writestr(member_name,fake_las() if first_body is None else first_body)
        for i in range(8):
            z.writestr("dummy-%02d.laz"%i,b"fictional ZIP members only")
    return buf.getvalue()


def parse_fictional_zip(raw):
    tail=raw[-min(len(raw),MAX_TAIL):]
    start=len(raw)-len(tail)
    eocd=locate_eocd(tail,tail_start=start,total=len(raw))
    body=raw[eocd["offset"]:eocd["offset"]+eocd["size"]]
    return eocd,body


class FakeResponse:
    def __init__(self,payload,headers):
        self.status=206
        self.payload=payload
        self.headers=headers
        self.reads=[]
    def geturl(self):
        return SYNTHETIC_URL
    def read(self,n):
        self.reads.append(n)
        if not 0<n<=262145:
            raise AssertionError("Unbounded original byte request")
        return self.payload[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class FakeOpener:
    def __init__(self,original):
        self.original=original
        self.calls=[]
        self.responses=[]
    def open(self,request,timeout):
        self.calls.append((request.get_method(),request.headers))
        text=request.headers.get("Range")
        m=re.fullmatch(r"bytes=(\d+)-(\d+)",text or "")
        if not m or request.get_method()!="GET":
            raise AssertionError("Fictional test observed unbounded read")
        start,end=map(int,m.groups())
        self.responses.append(FakeResponse(
            self.original[start:end+1],
            {"Content-Range":f"bytes {start}-{end}/{len(self.original)}",
             "Content-Length":str(end-start+1)}))
        return self.responses[-1]


class PublicHeaderTests(unittest.TestCase):
    def test_actual_public_prefix_is_limited_to_111_bytes(self):
        raw=fake_zip()
        eocd,directory=parse_fictional_zip(raw)
        meta=summarize_central(directory,entries=eocd["entries"],
                               archive_size=len(raw),directory_offset=eocd["offset"])
        self.assertEqual(meta["member_extension_counts"]["laz"],9)
        first=first_central_laz_member(directory,original_cd_offset=eocd["offset"])
        opener=FakeOpener(raw)
        prefix,io_report=zip_deflated_member_first_public_bytes(
            SYNTHETIC_URL,archive_size=len(raw),cd_offset=eocd["offset"],
            first=first,opener=opener)
        self.assertEqual(len(prefix),111)
        info=classify_public_las_prefix(
            prefix,member_uncompressed_bytes=first["declared_uncompressed_bytes"])
        self.assertTrue(info["original_decompressed_member_begins_LASF"])
        self.assertEqual((info["las_major"],info["las_minor"]),(1,2))
        self.assertEqual(info["las_point_format_code_declared"],3)
        self.assertEqual(info["las_header_bytes_declared"],227)
        self.assertTrue(info["laszip_compressed_header_flag_declared"])
        self.assertFalse(info["point_records_or_las_vlrs_read"])
        self.assertFalse(info["actual_building_class6_points_verified"])
        self.assertLessEqual(io_report["compressed_member_prefix_bytes_fetched"],
                             MAX_LAZ_ZIP_PREFIX_COMPRESSED_BYTES)
        self.assertEqual(io_report["max_public_uncompressed_las_header_bytes"],111)
        self.assertEqual(len(opener.calls),3)
        self.assertNotIn("invented-first.laz",str(io_report)+str(info))

    def test_public_header_fails_without_lasf(self):
        with self.assertRaisesRegex(PublicHeaderError,"LASF"):
            classify_public_las_prefix(b"x"*111,member_uncompressed_bytes=300)

    def test_las_prefix_size_always_exact(self):
        for n in (0,110,112):
            with self.subTest(n=n):
                with self.assertRaises(PublicHeaderError):
                    classify_public_las_prefix(b"LASF"+b"\0"*(n-4 if n>=4 else 0),
                                               member_uncompressed_bytes=300)

    def test_unsupported_las_version_rejected(self):
        for major,minor in ((2,2),(1,1),(1,5)):
            with self.subTest(version=(major,minor)):
                prefix=fake_las(major=major,minor=minor)[:111]
                with self.assertRaisesRegex(PublicHeaderError,"version"):
                    classify_public_las_prefix(prefix,member_uncompressed_bytes=300)

    def test_point_offset_must_be_before_end_of_member(self):
        prefix=fake_las(point_offset=5000)[:111]
        with self.assertRaisesRegex(PublicHeaderError,"point-format"):
            classify_public_las_prefix(prefix,member_uncompressed_bytes=300)

    def test_point_format_reserved_flag_rejected(self):
        prefix=fake_las(format_code=0x40|3)[:111]
        with self.assertRaisesRegex(PublicHeaderError,"point-format"):
            classify_public_las_prefix(prefix,member_uncompressed_bytes=300)

    def test_nondeflate_zip_first_member_blocks(self):
        raw=fake_zip(compression=ZIP_STORED)
        eocd,directory=parse_fictional_zip(raw)
        with self.assertRaisesRegex(PublicHeaderError,"deflated"):
            first_central_laz_member(directory,original_cd_offset=eocd["offset"])

    def test_wrong_first_extension_blocks(self):
        raw=fake_zip(member_name="invented-first.txt")
        eocd,directory=parse_fictional_zip(raw)
        with self.assertRaisesRegex(PublicHeaderError,"extension"):
            first_central_laz_member(directory,original_cd_offset=eocd["offset"])

    def test_deflate_stream_prefix_not_las(self):
        raw=fake_zip(first_body=b"not-a-lidar-prefix"*12)
        eocd,directory=parse_fictional_zip(raw)
        first=first_central_laz_member(directory,original_cd_offset=eocd["offset"])
        opener=FakeOpener(raw)
        prefix,report=zip_deflated_member_first_public_bytes(
            SYNTHETIC_URL,archive_size=len(raw),cd_offset=eocd["offset"],
            first=first,opener=opener)
        with self.assertRaisesRegex(PublicHeaderError,"LASF"):
            classify_public_las_prefix(prefix,member_uncompressed_bytes=first["declared_uncompressed_bytes"])

    def test_local_header_name_disagreement_blocks(self):
        raw=bytearray(fake_zip())
        # Change local name only. Central source name and location still original.
        original=bytes(raw)
        eocd,directory=parse_fictional_zip(original)
        first=first_central_laz_member(directory,original_cd_offset=eocd["offset"])
        name_start=first["original_local_header_offset"]+30
        raw[name_start]=ord("z")
        with self.assertRaisesRegex(PublicHeaderError,"local ZIP name"):
            zip_deflated_member_first_public_bytes(
                SYNTHETIC_URL,archive_size=len(raw),cd_offset=eocd["offset"],
                first=first,opener=FakeOpener(bytes(raw)))

    def test_invalid_las_member_does_not_prove_building_classes(self):
        prefix=fake_las()[:111]
        info=classify_public_las_prefix(prefix,member_uncompressed_bytes=300)
        self.assertFalse(info["actual_building_class6_points_verified"])
        self.assertFalse(info["geodetic_crs_or_vdatum_verified"])
        self.assertFalse(info["source_epoch_independent_of_vdl3d_verified"])

    def test_missing_source_index_blocks_without_network(self):
        self.assertEqual(main(["--original-index","synthetic-nonexistent-act-original.geojson"]),2)


if __name__=="__main__":
    unittest.main()
