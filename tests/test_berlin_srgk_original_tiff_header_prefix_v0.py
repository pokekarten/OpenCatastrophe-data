# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original ZIP local-header / TIFF IFD prefix safety regression."""
import io
import json
import struct
import unittest
from datetime import datetime, timezone
from hashlib import sha256
from unittest.mock import patch
import zipfile

from research_runners import berlin_srgk_original_tiff_header_prefix_v0 as p
from research_runners import berlin_srgk_depth_zip_central_range_v0 as original


def small_tiff():
    return (
        struct.pack("<2sHIH", b"II", 42, 8, 4)
        + struct.pack("<HHII", 256, 4, 1, 1024)
        + struct.pack("<HHII", 257, 4, 1, 2048)
        + struct.pack("<HHII", 34735, 3, 4, 80)
        + struct.pack("<HHII", 42113, 2, 4, 100)
        + struct.pack("<I", 0)
        + b"\0" * 2048
    )


def archive(name="sample.tif", content=None):
    content = small_tiff() if content is None else content
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, content)
        z.comment = b"Z" * 65535
    return buff.getvalue()


class Response:
    status = 206
    def __init__(self, url, raw, start, end, *, status=206):
        self.status=status
        self.url=url
        self.data=raw[start:end+1]
        self.read_calls=0
        self.headers={
            "Content-Range":f"bytes {start}-{end}/{len(raw)}",
            "Content-Encoding":"identity",
        }
    def geturl(self):
        return self.url
    def read(self, n):
        self.read_calls+=1
        return self.data[:n]
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False


def fake_source(raw, url, *, status=206):
    calls=[]
    responses=[]
    def opener(req,timeout):
        assert req.get_method()=="GET"
        assert req.full_url==url
        start,end=map(int,req.headers["Range"].removeprefix("bytes=").split("-"))
        calls.append((start,end))
        response=Response(url,raw,start,end,status=status)
        responses.append(response)
        return response
    return opener,calls,responses


def patched_original(raw, url):
    offset,size,count=original.locate_eocd(raw[-original.TAIL:],len(raw))
    central=raw[offset:offset+size]
    details=original.parse_directory(central,count)["bounded_tiff_name_samples"][0]
    return (
        {url:("synthetic",len(raw))},
        {url:{
            "directory_sha256":sha256(central).hexdigest(),
            "filename":details["name"],
            "compressed":details["compressed_size_bytes"],
            "uncompressed":details["uncompressed_size_bytes"],
        }}
    )


class TiffPrefixTests(unittest.TestCase):
    def test_realistic_classic_tiff_width_height_and_safe_tag_presence(self):
        result=p.tiff_first_ifd(small_tiff())
        self.assertTrue(result["tiff_classic_header_verified"])
        self.assertTrue(result["first_ifd_fully_in_prefix"])
        self.assertEqual(result["width_from_first_ifd"],1024)
        self.assertEqual(result["height_from_first_ifd"],2048)
        self.assertEqual(result["first_ifd_entry_count"],4)
        self.assertTrue(result["geokey_directory_tag_present"])
        self.assertTrue(result["gdal_nodata_ascii_tag_present"])
        self.assertFalse(result["original_epsg_code_or_raster_extent_verified"])
        self.assertFalse(result["original_water_depth_unit_scale_nodata_semantics_verified"])

    def test_header_supports_big_endian_and_short_inline(self):
        head=struct.pack(">2sHIH",b"MM",42,8,2)
        tags=(struct.pack(">HHI",256,3,1)+struct.pack(">H",250)+b"\0\0"
              +struct.pack(">HHII",257,4,1,300))
        result=p.tiff_first_ifd(head+tags+struct.pack(">I",0))
        self.assertEqual(result["width_from_first_ifd"],250)
        self.assertEqual(result["height_from_first_ifd"],300)

    def test_bad_magic_and_no_metadata_not_falsely_approved(self):
        for raw in (b"",b"bad",b"AB"+b"0"*20,b"II+\0"+b"0"*20):
            with self.subTest(raw=raw),self.assertRaises(p.TiffPrefixBlocked):
                p.tiff_first_ifd(raw)
        out=p.tiff_first_ifd(struct.pack("<2sHI",b"II",42,10000))
        self.assertFalse(out["first_ifd_fully_in_prefix"])
        self.assertIsNone(out["width_from_first_ifd"])
        self.assertFalse(out["original_epsg_code_or_raster_extent_verified"])

    def test_duplicate_tag_or_unbounded_ifd_fails(self):
        t=bytearray(small_tiff())
        struct.pack_into("<H",t,8,513)
        with self.assertRaisesRegex(p.TiffPrefixBlocked,"unbounded"):
            p.tiff_first_ifd(bytes(t))
        t=bytearray(small_tiff())
        struct.pack_into("<H",t,8+2+12,256)
        with self.assertRaisesRegex(p.TiffPrefixBlocked,"duplicate"):
            p.tiff_first_ifd(bytes(t))

    def test_source_pinned_five_ranges_and_no_tiff_bytes_output(self):
        url="https://gdi.berlin.de/data/ua_srgk/atom/synthetic.zip"
        raw=archive()
        self.assertGreater(len(raw),original.TAIL)
        s,e=patched_original(raw,url)
        opener,calls,_=fake_source(raw,url)
        with patch.object(original,"SOURCE_URLS",s),patch.object(p,"EXPECTED",e):
            result=p.inspect_one(url,opener)
            self.assertEqual(len(calls),5)
            self.assertEqual(result["source_range_requests"],5)
            self.assertEqual(result["width_from_first_ifd"],1024)
            self.assertFalse(result["source_original_member_bytes_or_raster_cells_persisted"])
            self.assertFalse(result["any_original_pixel_values_interpreted"])
            self.assertNotIn("Z"*100,str(result))
            self.assertNotIn("\x00"*16,str(result))

    def test_pinned_central_revision_blocks_before_local_header_access(self):
        url="https://gdi.berlin.de/data/ua_srgk/atom/synthetic.zip"
        raw=archive()
        s,e=patched_original(raw,url)
        e[url]["directory_sha256"]="0"*64
        opener,calls,_=fake_source(raw,url)
        with patch.object(original,"SOURCE_URLS",s),patch.object(p,"EXPECTED",e):
            with self.assertRaisesRegex(p.TiffPrefixBlocked,"SHA256 drift"):
                p.inspect_one(url,opener)
        self.assertEqual(len(calls),2)

    def test_ignored_range_rejected_before_any_archive_data_read(self):
        url="https://gdi.berlin.de/data/ua_srgk/atom/synthetic.zip"
        raw=archive()
        s,e=patched_original(raw,url)
        opener,calls,responses=fake_source(raw,url,status=200)
        with patch.object(original,"SOURCE_URLS",s),patch.object(p,"EXPECTED",e):
            with self.assertRaisesRegex(original.ZipIndexBlocked,"206"):
                p.inspect_one(url,opener)
        self.assertEqual(len(calls),1)
        self.assertEqual(responses[0].read_calls,0)

    def test_bad_member_deflate_prefix_rejected(self):
        url="https://gdi.berlin.de/data/ua_srgk/atom/synthetic.zip"
        raw=bytearray(archive())
        s,e=patched_original(bytes(raw),url)
        offset,cd_bytes,_=original.locate_eocd(bytes(raw)[-original.TAIL:],len(raw))
        local_fields=struct.unpack_from("<4s5H3I2H",raw,0)
        name_len,extra_len=local_fields[-2:]
        # Preserve original directory identity and destroy compressed prefix.
        start=30+name_len+extra_len
        raw[start:start+12]=b"\xff"*12
        opener,_,_=fake_source(bytes(raw),url)
        with patch.object(original,"SOURCE_URLS",s),patch.object(p,"EXPECTED",e):
            with self.assertRaisesRegex(p.TiffPrefixBlocked,"DEFLATE"):
                p.inspect_one(url,opener)

    def test_source_identity_and_size_remain_fail_closed(self):
        with self.assertRaises(p.TiffPrefixBlocked):
            p.inspect_one("https://untrusted.invalid/other.zip",None)

    def test_three_source_receipts_never_approve_cat(self):
        url="https://gdi.berlin.de/data/ua_srgk/atom/synthetic.zip"
        raw=archive()
        s,e=patched_original(raw,url)
        opener,calls,_=fake_source(raw,url)
        with patch.object(original,"SOURCE_URLS",s),patch.object(p,"EXPECTED",e):
            result=p.probe(opener=opener,
                clock=lambda:datetime(2026,11,2,tzinfo=timezone.utc))
        self.assertEqual(result["source_total_bounded_range_requests"],15)
        self.assertFalse(result["cat_model_input_approved"])
        self.assertFalse(result["second_pilot_raster_coverage_proven"])
        self.assertFalse(result["source_raster_crs_extent_depth_unit_verified"])
        self.assertEqual(len(result["source_scenarios"]),1)
        self.assertNotIn("Z"*100,json.dumps(result))


if __name__=="__main__":
    unittest.main()
