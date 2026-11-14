# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Tiny synthetic original-ZIP Shape source, never actual Bavarian polygons/masks."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import struct
import unittest
from unittest.mock import patch
import zlib

from research_runners import by_hausumringe_oberbayern_shp_windows_v0 as shp

HAS_GEOS=bool(importlib.util.find_spec("shapely") and importlib.util.find_spec("pyproj") and importlib.util.find_spec("numpy"))


def square_near(sid):
    from pyproj import Transformer
    w,so,e,n=shp.WINDOWS[sid]
    center_x=(w+e)/2
    center_y=(so+n)/2
    width=(e-w)/32
    height=(n-so)/32
    # Exterior clockwise in (x East, y North).
    original=[(center_x-2*width,center_y-2*height),
              (center_x-2*width,center_y+2*height),
              (center_x+2*width,center_y+2*height),
              (center_x+2*width,center_y-2*height)]
    utm=Transformer.from_crs(4326,25832,always_xy=True)
    ring=[utm.transform(lon,lat) for lon,lat in original]
    ring.append(ring[0])
    return ring


def polygon_record(seq,ring):
    bb=[min(x for x,y in ring),min(y for x,y in ring),max(x for x,y in ring),max(y for x,y in ring)]
    content=(struct.pack("<I4dII",5,*bb,1,len(ring))
             +struct.pack("<I",0)+b"".join(struct.pack("<dd",x,y) for x,y in ring))
    assert len(content)%2==0
    return struct.pack(">II",seq,len(content)//2)+content


def synthetic_source(*,bad_shape=False,bad_offset=False):
    rings=[square_near(28),square_near(29)]
    records=[polygon_record(i+1,r) for i,r in enumerate(rings)]
    head=bytearray(100)
    struct.pack_into(">I",head,0,9994)
    struct.pack_into(">I",head,24,(100+sum(map(len,records)))//2)
    struct.pack_into("<II",head,28,1000,5)
    allpts=[p for ring in rings for p in ring]
    struct.pack_into("<4d",head,36,min(p[0] for p in allpts),min(p[1] for p in allpts),
                     max(p[0] for p in allpts),max(p[1] for p in allpts))
    if bad_shape:
        records[1]=bytearray(records[1])
        struct.pack_into("<I",records[1],8,15)
        records[1]=bytes(records[1])
    if bad_offset:
        records[1]=bytearray(records[1])
        struct.pack_into(">I",records[1],0,3)
        records[1]=bytes(records[1])
    binary=bytes(head)+b"".join(records)
    deflater=zlib.compressobj(level=6,wbits=-15)
    compressed=deflater.compress(binary)+deflater.flush()
    crc=zlib.crc32(binary)
    wrapped=(struct.pack("<4sHHHHHIIIHH",b"PK\x03\x04",20,0,8,0,0,
             crc,len(compressed),len(binary),len(shp.NAME),0)
             +shp.NAME+compressed)
    return wrapped,binary,compressed,crc


def local_patches(original,raw,compressed,crc):
    return {
        "COMPRESSED_BYTES":len(compressed),
        "UNCOMPRESSED_BYTES":len(raw),
        "READ_BYTES":len(original),
        "END":shp.START+len(original)-1,
        "EXPECTED_CRC32":crc,
        "EXPECTED_SHX_ENTRIES":2,
        "FROZEN":{
            "hausumringe.shp":(shp.START,len(compressed),len(raw)),
            "hausumringe.shx":(shp.START+len(original),1,2),
        },
    }


class FakeSource:
    status=206
    def __init__(self,original,*,status=206,url=None,headers=None):
        self.status=status
        self.data=io.BytesIO(original)
        self.url=url or shp.URL
        self.headers=headers or {
            "Content-Range":f"bytes {shp.START}-{shp.START+len(original)-1}/{shp.TOTAL}",
            "Content-Length":str(len(original)),
            "Content-Type":"application/zip",
            "Content-Encoding":"identity",
        }
    def geturl(self):
        return self.url
    def read(self,n):
        return self.data.read(n)


@unittest.skipUnless(HAS_GEOS,"dedicated pinned GEOS + PROJ CI validates geometry")
class OfflineSourceGeometryTests(unittest.TestCase):
    def test_full_synthetic_shape_and_both_native_windows(self):
        original,raw,compressed,crc=synthetic_source()
        with patch.multiple(shp,**local_patches(original,raw,compressed,crc)):
            receipt=shp.verify_live(FakeSource(original))
        self.assertEqual(receipt["original_shp_polygon_record_count_verified"],2)
        self.assertEqual(receipt["original_shp_zip_crc32_verified"],f"{crc:08x}")
        self.assertTrue(receipt["full_official_shp_member_verified"])
        self.assertEqual(len(receipt["native_window_source_derived_grids"]),2)
        for res in receipt["native_window_source_derived_grids"]:
            self.assertEqual(res["official_polygon_candidates_in_broad_utm_bbox"],1)
            self.assertGreater(res["positive_footprint_pixels"],0)
            self.assertLessEqual(res["positive_footprint_pixels"],64)
            self.assertEqual(len(base64.b64decode(res["derived_fraction_uint16_le_32x32_base64"])),2048)
            self.assertFalse(res["original_geometry_coordinates_emitted"])
        self.assertFalse(receipt["wsf2019_raster_mask_compared"])
        self.assertFalse(receipt["model_input_approved"])

    def test_streaming_parser_recovers_arbitrary_chunk_boundaries(self):
        original,uncompressed,compressed,crc=synthetic_source()
        with patch.multiple(shp,**local_patches(original,uncompressed,compressed,crc)):
            reader=shp.OriginalShpReader()
            for i in range(0,len(uncompressed),3):
                reader.feed(uncompressed[i:i+3])
            results=reader.finish()
        self.assertEqual(reader.records,2)
        self.assertEqual(len(results),2)

    def test_truncated_encrypted_or_oversized_source_is_blocked(self):
        original,raw,comp,crc=synthetic_source()
        with patch.multiple(shp,**local_patches(original,raw,comp,crc)):
            for data in (original[:-1],original+b"\x00"):
                with self.assertRaises(shp.SHPBlocked):
                    shp.verify_live(FakeSource(data,headers=FakeSource(original).headers))
            encrypted=bytearray(original);encrypted[6]=1
            with self.assertRaises(shp.SHPBlocked):
                shp.verify_live(FakeSource(bytes(encrypted)))

    def test_malformed_record_shape_and_record_number_rejected(self):
        for bad in ("shape","record"):
            original,raw,compressed,crc=synthetic_source(
                bad_shape=bad=="shape",bad_offset=bad=="record",
            )
            with self.subTest(bad=bad),patch.multiple(shp,**local_patches(original,raw,compressed,crc)):
                with self.assertRaises(shp.SHPBlocked):
                    shp.verify_live(FakeSource(original))

    def test_transport_source_not_allow_redirect_or_full_zip(self):
        original,raw,compressed,crc=synthetic_source()
        with patch.multiple(shp,**local_patches(original,raw,compressed,crc)):
            for status,url,headers in (
                (200,shp.URL,FakeSource(original).headers),
                (206,"https://other.example/",FakeSource(original).headers),
                (206,shp.URL,{**FakeSource(original).headers,"Content-Range":"bytes 0-200/174299765"}),
                (206,shp.URL,{**FakeSource(original).headers,"Content-Encoding":"gzip"}),
                (206,shp.URL,{**FakeSource(original).headers,"Content-Type":"text/html"}),
            ):
                with self.subTest(status=status,url=url),self.assertRaises(shp.SHPBlocked):
                    shp.verify_live(FakeSource(original,status=status,url=url,headers=headers))

    def test_fractional_derived_grid_repeatable_and_not_original_geometry(self):
        original,raw,compressed,crc=synthetic_source()
        with patch.multiple(shp,**local_patches(original,raw,compressed,crc)):
            a=shp.verify_live(FakeSource(original))
            b=shp.verify_live(FakeSource(original))
        for aa,bb in zip(a["native_window_source_derived_grids"],b["native_window_source_derived_grids"]):
            self.assertEqual(aa["derived_fraction_uint16_le_sha256"],bb["derived_fraction_uint16_le_sha256"])
            self.assertNotIn("original_polygon_geometries",str(aa))
            self.assertEqual(len(aa["derived_fraction_uint16_le_sha256"]),64)


if __name__=="__main__":
    unittest.main()
