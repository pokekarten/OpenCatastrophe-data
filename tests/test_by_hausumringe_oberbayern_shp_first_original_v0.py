# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only official Bavarian first-SHP Polygon source format tests."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import unittest
import zlib

from research_runners import by_hausumringe_oberbayern_shp_first_original_v0 as shp


def fake_first_shp() -> bytes:
    """Synthetic geometry only; not a real cadastral or insured location."""
    nbytes=100+8+128
    raw=bytearray(nbytes)
    struct.pack_into(">I",raw,0,9994)
    struct.pack_into(">I",raw,24,shp.UNCOMPRESSED_SHP_BYTES//2)
    struct.pack_into("<II",raw,28,1000,5)
    struct.pack_into("<dddd",raw,36,500000.,5200000.,800000.,5500000.)
    struct.pack_into(">II",raw,100,1,64)
    struct.pack_into("<I",raw,108,5)
    # Fixed synthetic 20-by-10 metre closed Polygon, no real building.
    struct.pack_into("<dddd",raw,112,650000.,5350000.,650020.,5350010.)
    struct.pack_into("<II",raw,144,1,5)
    struct.pack_into("<I",raw,152,0)
    vertices=((650000.,5350000.),(650020.,5350000.),
              (650020.,5350010.),(650000.,5350010.),(650000.,5350000.))
    for i,(x,y) in enumerate(vertices):
        struct.pack_into("<dd",raw,156+i*16,x,y)
    return bytes(raw)


def fake_source_original_range() -> bytes:
    """One fully synthetic, incomplete raw-DEFLATE ZIP member prefix."""
    preview=fake_first_shp()
    # Deterministic incompressible filler ensures member stream is not EOF
    # in its first 49,152 compressed bytes. Never touches real buildings.
    filler=random.Random(20261112).randbytes(100000)
    compressor=zlib.compressobj(level=1,wbits=-15)
    zipped=compressor.compress(preview+filler)+compressor.flush()
    assert len(zipped)>shp.PREVIEW_COMPRESSED_BYTES
    h=bytearray(shp.ZIP_HEADER_BYTES)
    struct.pack_into("<4sHHHHHIIIHH",h,0,b"PK\x03\x04",20,0,8,0,0,
                     shp.ORIGINAL_DIRECTORY_CRC32_CLAIM,
                     shp.COMPRESSED_MEMBER_BYTES,shp.UNCOMPRESSED_SHP_BYTES,
                     len(shp.NAME),0)
    h[30:45]=shp.NAME
    return bytes(h)+zipped[:shp.PREVIEW_COMPRESSED_BYTES]


def transport_headers():
    return {
        "Content-Range":f"bytes {shp.START}-{shp.END}/{shp.TOTAL}",
        "Content-Length":str(shp.READ_BYTES),
        "Content-Encoding":"identity",
        "Content-Type":"application/zip",
    }


class OriginalBVVShapefilePreviewTests(unittest.TestCase):
    def test_valid_synthetic_polygon_structural_qa_without_coords_export(self):
        result=shp.inspect_bounded_shp_preview(fake_first_shp())
        self.assertTrue(result["first_original_shape_record_complete"])
        self.assertEqual(result["original_first_record_parts"],1)
        self.assertEqual(result["original_first_record_points"],5)
        self.assertTrue(result["original_first_record_rings_closed"])
        self.assertTrue(result["original_first_record_bbox_matches_all_vertices"])
        self.assertFalse(result["original_first_record_geometry_or_coordinates_persisted"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("650000",json.dumps(result))
        self.assertNotIn("5350000",json.dumps(result))

    def test_original_transport_and_incomplete_deflate_record_handling(self):
        source=fake_source_original_range()
        data=shp.inspect_original_shp_prefix(
            source,status=206,response_url=shp.URL,headers=transport_headers())
        self.assertEqual(data["original_source_response_bytes"],shp.READ_BYTES)
        self.assertTrue(data["first_original_shape_record_complete"])
        self.assertFalse(data["full_original_zip_or_shp_sha256_verified"])
        self.assertFalse(data["original_shp_member_bytes_or_geometries_persisted"])
        self.assertEqual(data["original_http_response_sha256"],
                         hashlib.sha256(source).hexdigest())

    def test_wrong_range_mime_status_zip_crc_name_or_full_size_block(self):
        src=fake_source_original_range()
        with self.assertRaises(shp.BVVShpPreviewBlocked):
            shp.inspect_original_shp_prefix(src,status=200,
                response_url=shp.URL,headers=transport_headers())
        with self.assertRaises(shp.BVVShpPreviewBlocked):
            shp.inspect_original_shp_prefix(src,status=206,
                response_url="https://evil.invalid/",headers=transport_headers())
        for field,value in (
            ("Content-Range","bytes 0-49196/174299765"),
            ("Content-Type","text/html"),("Content-Encoding","gzip"),
            ("Content-Length","1")):
            with self.subTest(field=field):
                headers=transport_headers()
                headers[field]=value
                with self.assertRaises(shp.BVVShpPreviewBlocked):
                    shp.inspect_original_shp_prefix(src,status=206,
                        response_url=shp.URL,headers=headers)
        for pos,value in ((0,b"XX"),(14,b"abcd"),(30,b"X"),(22,b"\x00\x00\x00\x00")):
            with self.subTest(pos=pos):
                corrupted=bytearray(src)
                corrupted[pos:pos+len(value)]=value
                with self.assertRaises(shp.BVVShpPreviewBlocked):
                    shp.inspect_original_shp_prefix(bytes(corrupted),status=206,
                        response_url=shp.URL,headers=transport_headers())

    def test_bad_shp_header_record_shape_bbox_and_open_ring_fail_closed(self):
        src=fake_first_shp()
        mutations=[
            (0,">I",0),
            (24,">I",5),
            (32,"<I",3),
            (100,">I",2),
            (104,">I",900_000),
            (108,"<I",0),
            (144,"<I",0),
            (148,"<I",100_000),
            (156,"<d",float("nan")),
            (156+4*16,"<d",650001.),
        ]
        for offset,format,value in mutations:
            with self.subTest(offset=offset,value=value):
                b=bytearray(src)
                struct.pack_into(format,b,offset,value)
                with self.assertRaises(shp.BVVShpPreviewBlocked):
                    shp.inspect_bounded_shp_preview(bytes(b))

    def test_bounded_source_request_cap_and_live_gate(self):
        with self.assertRaises(shp.BVVShpPreviewBlocked):
            shp.inspect_original_shp_prefix(b"PK\x03\x04",status=206,
                response_url=shp.URL,headers=transport_headers())
        with self.assertRaises(SystemExit) as ctx:
            shp.main([])
        self.assertNotEqual(ctx.exception.code,0)


if __name__ == "__main__":
    unittest.main()
