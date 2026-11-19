# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Small synthetic-only SHX/ZIP fixture; never original Bavarian feature positions."""
from __future__ import annotations

import struct
import unittest
from unittest.mock import patch
import zlib

from research_runners import by_hausumringe_oberbayern_shx_v0 as shx


def source_index(*,wrong=None):
    b=bytearray(124)
    struct.pack_into(">I",b,0,9994)
    struct.pack_into(">I",b,24,62)
    struct.pack_into("<II",b,28,1000,5)
    struct.pack_into("<4d",b,36,600000.,5300000.,610000.,5310000.)
    for i in range(3):
        struct.pack_into(">II",b,100+i*8,50+i*26,22)
    if wrong=="header_code":
        struct.pack_into(">I",b,0,1000)
    elif wrong=="shape":
        struct.pack_into("<I",b,32,15)
    elif wrong=="offset":
        struct.pack_into(">I",b,108,78)
    elif wrong=="end":
        struct.pack_into(">I",b,116,101)
    elif wrong=="file_size":
        struct.pack_into(">I",b,24,63)
    elif wrong=="extent":
        struct.pack_into("<d",b,36,float("inf"))
    return bytes(b)


def zip_member(contents):
    compressor=zlib.compressobj(level=6,wbits=-15)
    zipped=compressor.compress(contents)+compressor.flush()
    crc=zlib.crc32(contents)
    packet=bytearray(45+len(zipped))
    struct.pack_into(
        "<4sHHHHHIIIHH",packet,0,b"PK\x03\x04",20,0,8,0,0,
        crc,len(zipped),len(contents),len(shx.NAME),0,
    )
    packet[30:45]=shx.NAME
    packet[45:]=zipped
    return bytes(packet),zipped,crc


def fixture(*,wrong=None):
    original=source_index(wrong=wrong)
    packet,compressed,crc=zip_member(original)
    m={
        "READ_BYTES":len(packet),
        "END":shx.START+len(packet)-1,
        "COMPRESSED":len(compressed),
        "UNCOMPRESSED":len(original),
        "ORIGINAL_CRC32":crc,
        "EXPECTED_SHX_ENTRIES":3,
        "EXPECTED_DBF_RECORDS":3,
        "EXPECTED_SHP_LENGTH_CLAIM_ONLY":256,
        "CENTRAL_START":shx.START+len(packet),
        "FROZEN":{
            "hausumringe.shx":(shx.START,len(compressed),len(original)),
            "hausumringe.shp":(0,0,256),
        },
    }
    return packet,m


def headers(length):
    return {
        "Content-Range":f"bytes {shx.START}-{shx.START+length-1}/{shx.TOTAL}",
        "Content-Type":"application/zip",
        "Content-Length":str(length),
        "Content-Encoding":"identity",
    }


class OriginalIndexSyntheticTests(unittest.TestCase):
    def test_synthetic_contiguous_three_index_records(self):
        packet,changes=fixture()
        with patch.multiple(shx,**changes):
            result=shx.inspect_original_shx(
                packet,status=206,response_url=shx.URL,headers=headers(len(packet))
            )
        self.assertEqual(result["original_index_entries_verified"],3)
        self.assertEqual(result["last_index_record_ends_at_shp_byte_claim"],256)
        self.assertEqual(result["min_index_record_content_bytes"],44)
        self.assertTrue(result["index_records_contiguous_no_gaps"])
        self.assertFalse(result["source_shp_polygon_bytes_fetched"])
        self.assertFalse(result["source_feature_positions_persisted"])
        self.assertFalse(result["model_input_approved"])

    def test_bad_source_http_range_encoding_and_media_block(self):
        packet,changes=fixture()
        with patch.multiple(shx,**changes):
            cases=[
                (200,shx.URL,headers(len(packet))),
                (206,"https://other.example/",headers(len(packet))),
                (206,shx.URL,{**headers(len(packet)),"Content-Length":"500000000"}),
                (206,shx.URL,{**headers(len(packet)),"Content-Range":"bytes 0-100/174299765"}),
                (206,shx.URL,{**headers(len(packet)),"Content-Encoding":"gzip"}),
                (206,shx.URL,{**headers(len(packet)),"Content-Type":"text/html"}),
            ]
            for status,url,h in cases:
                with self.subTest(status=status,url=url,h=h),self.assertRaises(shx.SHXBlocked):
                    shx.inspect_original_shx(packet,status=status,response_url=url,headers=h)

    def test_wrong_shx_semantics_even_with_self_consistent_crc_block(self):
        for wrong in ("header_code","shape","offset","end","file_size","extent"):
            packet,changes=fixture(wrong=wrong)
            with self.subTest(wrong=wrong),patch.multiple(shx,**changes),self.assertRaises(shx.SHXBlocked):
                shx.inspect_original_shx(
                    packet,status=206,response_url=shx.URL,headers=headers(len(packet))
                )

    def test_bad_zip_header_or_content_checksum_block(self):
        packet,changes=fixture()
        with patch.multiple(shx,**changes):
            for pos in (0,8,14,len(packet)-1):
                changed=bytearray(packet);changed[pos]^=1
                with self.subTest(offset=pos),self.assertRaises(shx.SHXBlocked):
                    shx.inspect_original_shx(
                        bytes(changed),status=206,response_url=shx.URL,headers=headers(len(packet))
                    )

    def test_truncated_overlong_untrusted_member_block(self):
        packet,changes=fixture()
        with patch.multiple(shx,**changes):
            for bad in (packet[:-1],packet+b"\0",b""):
                with self.assertRaises(shx.SHXBlocked):
                    shx.inspect_original_shx(
                        bad,status=206,response_url=shx.URL,headers=headers(len(packet))
                    )

    def test_shx_real_source_limits_only_7_85mb_not_full_polygon(self):
        self.assertEqual(shx.RANGE,"bytes=166448184-174299354")
        self.assertEqual(shx.READ_BYTES,7851171)
        self.assertEqual(shx.EXPECTED_SHX_ENTRIES,2703736)
        self.assertEqual(shx.UNCOMPRESSED,21629988)
        self.assertEqual(shx.EXPECTED_SHP_LENGTH_CLAIM_ONLY,501212696)


if __name__=="__main__":
    unittest.main()
