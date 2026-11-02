# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP central index + adversarial HTTP Range gates, no live source."""
import io
import json
import struct
import unittest
import zipfile
from datetime import datetime, timezone
from unittest.mock import patch

from research_runners import berlin_srgk_depth_zip_central_range_v0 as m


def archive(names=("area/foo.tif", "readme.txt")):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.writestr(name,b"test-only example synthetic bytes")
    return buf.getvalue()


class Response:
    def __init__(self,url,data,start,end,full_size,status=206,wrong_range=False):
        self.url=url
        self.content=data[start:end+1]
        self.status=status
        self.read_calls=0
        cr=(start+1 if wrong_range else start)
        self.headers={"Content-Range":f"bytes {cr}-{end}/{full_size}",
                      "Content-Encoding":"identity"}
    def geturl(self):
        return self.url
    def read(self,n):
        self.read_calls+=1
        return self.content[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return None


def fake_source(data,url="https://gdi.berlin.de/data/ua_srgk/atom/test.zip",
                *,status=206,wrong_range=False):
    calls=[]
    responses=[]
    def fake(req,timeout):
        calls.append((req.full_url,req.get_method(),req.headers.get("Range")))
        assert req.full_url==url
        assert req.get_method()=="GET"
        s,e=map(int,req.headers["Range"].removeprefix("bytes=").split("-"))
        r=Response(url,data,s,e,len(data),status,wrong_range)
        responses.append(r)
        return r
    return fake,calls,responses


class OriginalZipIndexTests(unittest.TestCase):
    def test_parse_real_stdlib_zip_central_directory_only(self):
        data=archive()
        offset,size,members=m.locate_eocd(data,len(data))
        out=m.parse_directory(data[offset:offset+size],members)
        self.assertEqual(members,2)
        self.assertEqual(out["central_suffix_counts"],{".tif":1,"other":1})
        self.assertEqual(out["bounded_tiff_name_samples"][0]["name"],"area/foo.tif")
        self.assertTrue(out["all_original_member_bodies_unread"])

    def test_exact_two_small_range_reads_for_one_source(self):
        data=archive()
        url="https://gdi.berlin.de/data/ua_srgk/atom/test.zip"
        fake,calls,_=fake_source(data,url)
        with patch.object(m,"SOURCE_URLS",{url:("selten",len(data))}):
            out=m.inspect_one(url,fake)
        self.assertEqual(out["source_get_requests"],2)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][1],"GET")
        self.assertTrue(calls[0][2].startswith("bytes="))
        self.assertEqual(out["central_suffix_counts"][".tif"],1)
        self.assertLess(out["source_bytes_transferred"],m.TAIL+m.MAX_CENTRAL_BYTES)

    def test_http_server_ignoring_range_rejected_before_body_read(self):
        data=archive()
        url="https://gdi.berlin.de/data/ua_srgk/atom/test.zip"
        fake,calls,responses=fake_source(data,url,status=200)
        with patch.object(m,"SOURCE_URLS",{url:("selten",len(data))}):
            with self.assertRaisesRegex(m.ZipIndexBlocked,"206"):
                m.inspect_one(url,fake)
        self.assertEqual(len(calls),1)
        self.assertEqual(responses[0].read_calls,0)

    def test_original_source_size_or_range_drift_fails(self):
        data=archive()
        url="https://gdi.berlin.de/data/ua_srgk/atom/test.zip"
        fake,_,_=fake_source(data,url,wrong_range=True)
        with patch.object(m,"SOURCE_URLS",{url:("selten",len(data))}):
            with self.assertRaisesRegex(m.ZipIndexBlocked,"size or byte range"):
                m.inspect_one(url,fake)

    def test_bad_eocd_trailer_rejects_before_index_lookup(self):
        data=bytearray(archive())
        data[-22:-18]=b"XXXX"
        with self.assertRaisesRegex(m.ZipIndexBlocked,"EOCD"):
            m.locate_eocd(bytes(data),len(data))
        with self.assertRaises(m.ZipIndexBlocked):
            m.locate_eocd(b"no-zip",6)

    def test_zip64_or_disk_split_or_overlarge_directory_refused(self):
        data=bytearray(archive())
        pos=len(data)-22
        self.assertEqual(data[pos:pos+4],b"PK\x05\x06")
        struct.pack_into("<H",data,pos+10,0xFFFF)
        with self.assertRaisesRegex(m.ZipIndexBlocked,"ZIP64"):
            m.locate_eocd(bytes(data),len(data))
        data=bytearray(archive())
        struct.pack_into("<H",data,len(data)-22+4,1)
        with self.assertRaisesRegex(m.ZipIndexBlocked,"multi-volume"):
            m.locate_eocd(bytes(data),len(data))

    def test_malicious_zip_paths_or_duplicate_names_refused(self):
        for name in ("../private.tif","C:/abs/file.tif","/root/private.tif",
                     "foo\\bar.tif","x/./test.tif"):
            data=archive((name,))
            offset,size,n=m.locate_eocd(data,len(data))
            with self.subTest(name=name),self.assertRaisesRegex(m.ZipIndexBlocked,"unsafe"):
                m.parse_directory(data[offset:offset+size],n)
        data=archive(("duplicate.tif","duplicate.tif"))
        offset,size,n=m.locate_eocd(data,len(data))
        with self.assertRaisesRegex(m.ZipIndexBlocked,"duplicate"):
            m.parse_directory(data[offset:offset+size],n)

    def test_truncated_central_or_wrong_signature_rejected(self):
        data=archive()
        offset,size,n=m.locate_eocd(data,len(data))
        with self.assertRaises(m.ZipIndexBlocked):
            m.parse_directory(data[offset:offset+size-1],n)
        damaged=bytearray(data[offset:offset+size])
        damaged[:4]=b"oops"
        with self.assertRaisesRegex(m.ZipIndexBlocked,"signature"):
            m.parse_directory(bytes(damaged),n)

    def test_three_original_source_index_receipts_remain_nonadmitted(self):
        sample=archive()
        urls={
          f"https://gdi.berlin.de/data/ua_srgk/atom/synthetic-{i}.zip":
            (f"synthetic-{i}",len(sample))
          for i in range(3)
        }
        calls=[]
        def opener(req,timeout):
            calls.append(req.full_url)
            s,e=map(int,req.headers["Range"].removeprefix("bytes=").split("-"))
            return Response(req.full_url,sample,s,e,len(sample))
        with patch.object(m,"SOURCE_URLS",urls):
            out=m.probe(opener=opener,
                        clock=lambda:datetime(2026,11,2,tzinfo=timezone.utc))
        self.assertEqual(len(calls),6)
        self.assertEqual(out["total_source_range_get_requests"],6)
        self.assertFalse(out["any_complete_source_zip_downloaded"])
        self.assertFalse(out["any_original_tiff_or_raster_pixel_decoded"])
        self.assertFalse(out["insurer_exposure_or_cat_model_admitted"])
        self.assertEqual(len(out["official_source_scenarios"]),3)
        self.assertNotIn("test-only example synthetic bytes",json.dumps(out))

    def test_refuse_unknown_url_and_unbounded_interval(self):
        with self.assertRaisesRegex(m.ZipIndexBlocked,"unapproved"):
            m.fetch_range("https://other.invalid/a.zip",0,1)
        known=next(iter(m.SOURCE_URLS))
        with self.assertRaisesRegex(m.ZipIndexBlocked,"not safe"):
            m.fetch_range(known,0,m.MAX_CENTRAL_BYTES)
        with self.assertRaises(m.ZipIndexBlocked):
            m.fetch_range(known,-1,20)


if __name__=="__main__":
    unittest.main()
