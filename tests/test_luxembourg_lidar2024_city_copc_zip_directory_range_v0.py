# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP central-directory + HTTP Range fail-closed tests, no network."""
from __future__ import annotations

from io import BytesIO
import struct
import unittest
from urllib.request import Request
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.luxembourg_lidar2024_city_copc_zip_directory_range_v0 import (
    ZIP_TAIL_BYTES,CITY_ORIGINAL_BYTES,ZipRangeError,
    parse_eocd,parse_directory,read_http,_request,
)


class FakeResponse:
    def __init__(self,status,body,headers):
        self.status=status;self.body=body;self.headers=headers;self.read_count=0
    def getcode(self):return self.status
    def read(self,n):
        self.read_count+=1
        return self.body[:n]
    def info(self):return self.headers
    def __enter__(self):return self
    def __exit__(self,*args):return False


class FakeOpener:
    def __init__(self,response):self.response=response
    def open(self,req,timeout):return self.response


def small_original():
    buf=BytesIO()
    with ZipFile(buf,"w",compression=ZIP_DEFLATED) as zip:
        zip.writestr("77000_75500.copc.laz",b"NOT_TRUE_COPC_POINTS")
        zip.writestr("77500_75500.copc.laz",b"NO_REAL_POINTS")
        zip.writestr("README.txt",b"SYMBOLIC_ONLY")
    small=buf.getvalue()
    padded=b"\x00"*(ZIP_TAIL_BYTES-len(small))+small
    return small,padded


class ZIPCentralDirectoryTests(unittest.TestCase):
    def test_true_synthetic_zip_directory_and_study_tile_evidence(self):
        original,tail=small_original()
        receipt=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
        self.assertEqual(receipt["members"],3)
        directory=original[receipt["directory_start"]:receipt["directory_end"]+1]
        report=parse_directory(directory,count=receipt["members"])
        self.assertEqual(report["declared_original_zip_member_count"],3)
        self.assertEqual(report["declared_laz_members"],2)
        self.assertEqual(report["declared_copc_laz_named_members"],2)
        self.assertEqual(report["city_study_tile_named_member_count"],1)
        self.assertNotIn("77000_75500",str(report))
        self.assertNotIn("NOT_TRUE_COPC_POINTS",str(report))

    def test_wrong_eocd_signature_rejected(self):
        with self.assertRaisesRegex(ZipRangeError,"not present"):
            parse_eocd(bytes(ZIP_TAIL_BYTES),full_size=CITY_ORIGINAL_BYTES)

    def test_trailing_comment_bytes_mismatch_rejected(self):
        _,tail=small_original()
        with self.assertRaisesRegex(ZipRangeError,"trailing"):
            parse_eocd(tail[:-1]+b"X",full_size=CITY_ORIGINAL_BYTES)

    def test_encrypted_or_zip64_central_member_rejected(self):
        original,tail=small_original()
        r=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
        directory=bytearray(original[r["directory_start"]:r["directory_end"]+1])
        # Strictly force encrypted bit in central directory general-purpose flags.
        flags=struct.unpack_from("<H",directory,8)[0]
        struct.pack_into("<H",directory,8,flags|1)
        with self.assertRaisesRegex(ZipRangeError,"unsafe"):
            parse_directory(bytes(directory),count=r["members"])
        directory=bytearray(original[r["directory_start"]:r["directory_end"]+1])
        struct.pack_into("<I",directory,20,0xFFFFFFFF)
        with self.assertRaisesRegex(ZipRangeError,"ZIP64"):
            parse_directory(bytes(directory),count=r["members"])

    def test_unexpected_extra_directory_bytes_rejected(self):
        original,tail=small_original()
        r=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
        directory=original[r["directory_start"]:r["directory_end"]+1]
        with self.assertRaisesRegex(ZipRangeError,"unparsed"):
            parse_directory(directory+b"EXTRA",count=r["members"])

    def test_range_status200_rejected_before_reading_any_body(self):
        req=_request("https://download.data.public.lu/fixed.zip",start=1,end=200)
        fake=FakeResponse(200,b"BAD_UNBOUNDED_PAYLOAD"*100,{"Content-Length":"1700086212"})
        with self.assertRaisesRegex(ZipRangeError,"did not honour"):
            read_http(FakeOpener(fake),req,status=206,limit=200,range_expected=(1,200,1000))
        self.assertEqual(fake.read_count,0)

    def test_wrong_http206_content_range_rejected_without_body(self):
        fake=FakeResponse(206,b"0"*100,{"Content-Range":"bytes 2-101/1000"})
        with self.assertRaisesRegex(ZipRangeError,"Content-Range"):
            read_http(FakeOpener(fake),_request("https://download.data.public.lu/fixed.zip",start=1,end=100),
                      status=206,limit=100,range_expected=(1,100,1000))
        self.assertEqual(fake.read_count,0)

    def test_valid_exact_range_read_and_no_more(self):
        body=b"A"*100
        fake=FakeResponse(206,body,{"Content-Range":"bytes 10-109/1000","Content-Length":"100"})
        got=read_http(FakeOpener(fake),_request("https://download.data.public.lu/fixed.zip",start=10,end=109),
                      status=206,limit=100,range_expected=(10,109,1000))
        self.assertEqual(got,body)
        self.assertEqual(fake.read_count,1)

    def test_truncated_range_fails(self):
        fake=FakeResponse(206,b"A"*99,{"Content-Range":"bytes 10-109/1000"})
        with self.assertRaisesRegex(ZipRangeError,"truncated"):
            read_http(FakeOpener(fake),_request("https://download.data.public.lu/fixed.zip",start=10,end=109),
                      status=206,limit=100,range_expected=(10,109,1000))

    def test_bounded_metadata_get_not_required_to_fill_limit(self):
        fake=FakeResponse(200,b'{"id":"synthetic"}',{})
        got=read_http(FakeOpener(fake),_request("https://data.public.lu/api/1/fixed.json"),
                      status=200,limit=262144)
        self.assertEqual(got,b'{"id":"synthetic"}')

    def test_path_traversal_original_zip_member_blocks(self):
        buf=BytesIO()
        with ZipFile(buf,"w",compression=ZIP_DEFLATED) as z:
            z.writestr("../SECRET.copc.laz",b"NOT_A_POINT")
        original=buf.getvalue()
        tail=bytes(ZIP_TAIL_BYTES-len(original))+original
        eo=parse_eocd(tail,full_size=CITY_ORIGINAL_BYTES)
        with self.assertRaisesRegex(ZipRangeError,"Unsafe"):
            parse_directory(original[eo["directory_start"]:eo["directory_end"]+1],count=1)


if __name__=="__main__":
    unittest.main()
