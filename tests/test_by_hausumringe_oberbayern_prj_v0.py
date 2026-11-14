# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic projection ZIP member tests. NO original BVV projection or polygons."""
from __future__ import annotations

import hashlib
import importlib.util
from unittest import TestCase
from unittest.mock import patch
import struct
import zlib

from research_runners import by_hausumringe_oberbayern_prj_v0 as prj


HAS_PYPROJ=importlib.util.find_spec("pyproj") is not None


def synthetic_zip():
    # Synthetic, generated from public EPSG definitions; not the LDBV bytes.
    from pyproj import CRS
    wkt=CRS.from_epsg(25832).to_wkt(version="WKT1_ESRI")
    wkt=wkt.replace("ETRS_1989_UTM_Zone_32N", "ETRS89_UTM_zone_32N")
    raw=wkt.encode("ascii")
    z=zlib.compressobj(level=6,wbits=-15)
    comp=z.compress(raw)+z.flush()
    crc=zlib.crc32(raw)
    payload=bytearray(30+len(prj.NAME)+len(comp))
    struct.pack_into("<4sHHHHHIIIHH",payload,0,b"PK\x03\x04",20,0,8,0,0,
                     crc,len(comp),len(raw),len(prj.NAME),0)
    payload[30:30+len(prj.NAME)]=prj.NAME
    payload[30+len(prj.NAME):]=comp
    return bytes(payload),raw,comp,crc


def meta():
    return {
        "Content-Range":f"bytes {prj.START}-{prj.END}/{prj.TOTAL}",
        "Content-Type":"application/zip",
        "Content-Length":str(prj.LIMIT),
        "Content-Encoding":"identity",
    }


class FailClosedInputTests(TestCase):
    def test_short_full_get_redirect_or_nonzip_fail_before_dependency(self):
        for body,status,url in (
            (b"",206,prj.URL),(b"X"*prj.LIMIT,200,prj.URL),
            (b"X"*prj.LIMIT,206,"https://not-ldbv.example/"),
            (b"X"*prj.LIMIT,206,prj.URL),
        ):
            with self.subTest(length=len(body),status=status,url=url):
                with self.assertRaises(prj.ProjectionBlocked):
                    prj.inspect_projection(body,status=status,response_url=url,headers=meta())

    def test_wrong_range_encoding_and_media_fail_before_dependency(self):
        bad=(
            {"Content-Range":"bytes 0-300/174299765"},
            {"Content-Length":"174299765"},
            {"Content-Encoding":"gzip"},
            {"Content-Type":"text/html"},
        )
        for h in bad:
            with self.subTest(h=h):
                headers=meta();headers.update(h)
                with self.assertRaises(prj.ProjectionBlocked):
                    prj.inspect_projection(b"X"*prj.LIMIT,status=206,response_url=prj.URL,headers=headers)

    def test_exact_original_source_frozen_and_no_automatic_bulk(self):
        self.assertEqual(prj.START,275602)
        self.assertEqual(prj.END,275902)
        self.assertEqual(prj.LIMIT,301)
        self.assertEqual(prj.EXPECTED_UNCOMPRESSED,388)
        self.assertEqual(prj.SOURCE,"de.bayern.hausumringe")


class SyntheticProjectionTests(TestCase):
    @__import__("unittest").skipUnless(HAS_PYPROJ,"pinned PROJ dependency exercised in dedicated workflow")
    def test_generated_nonprovider_crs_25832_decodes_without_source_byte_leak(self):
        body,wkt,compressed,crc=synthetic_zip()
        with patch.multiple(prj,
                            LIMIT=len(body),
                            END=prj.START+len(body)-1,
                            EXPECTED_COMPRESSED=len(compressed),
                            EXPECTED_UNCOMPRESSED=len(wkt),
                            EXPECTED_CRC32=crc,
                            SOURCE_DEFLATE_SHA256=hashlib.sha256(compressed).hexdigest(),
                            SOURCE_WKT_SHA256=hashlib.sha256(wkt).hexdigest()):
            h={"Content-Range":f"bytes {prj.START}-{prj.END}/{prj.TOTAL}",
               "Content-Type":"application/zip","Content-Length":str(len(body))}
            receipt=prj.inspect_projection(body,status=206,response_url=prj.URL,headers=h)
        self.assertEqual(receipt["independent_pyproj_epsg"],25832)
        self.assertTrue(receipt["original_projection_member_complete"])
        self.assertFalse(receipt["original_polygon_coordinates_retrieved"])
        self.assertFalse(receipt["model_input_approved"])

    @__import__("unittest").skipUnless(HAS_PYPROJ,"pinned PROJ dependency exercised in dedicated workflow")
    def test_modified_compressed_bytes_or_crc_fail_closed(self):
        body,wkt,compressed,crc=synthetic_zip()
        with patch.multiple(prj,
                            LIMIT=len(body),END=prj.START+len(body)-1,
                            EXPECTED_COMPRESSED=len(compressed),
                            EXPECTED_UNCOMPRESSED=len(wkt),
                            EXPECTED_CRC32=crc,
                            SOURCE_DEFLATE_SHA256=hashlib.sha256(compressed).hexdigest(),
                            SOURCE_WKT_SHA256=hashlib.sha256(wkt).hexdigest()):
            h={"Content-Range":f"bytes {prj.START}-{prj.END}/{prj.TOTAL}",
               "Content-Type":"application/zip"}
            changed=bytearray(body);changed[-1]^=1
            with self.assertRaises(prj.ProjectionBlocked):
                prj.inspect_projection(bytes(changed),status=206,response_url=prj.URL,headers=h)
            changed=bytearray(body);changed[14]^=1
            with self.assertRaises(prj.ProjectionBlocked):
                prj.inspect_projection(bytes(changed),status=206,response_url=prj.URL,headers=h)


if __name__=="__main__":
    __import__("unittest").main()
