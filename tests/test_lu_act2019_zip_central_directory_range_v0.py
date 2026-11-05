# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline ZIP-directory tests: no original LiDAR bytes, provider URLs or GIS IO."""
from __future__ import annotations

import io
import re
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from research_runners.lu_act2019_zip_central_directory_range_v0 import (
    DirectoryAuditError, MAX_EOCD_TAIL_BYTES, MAX_CENTRAL_DIRECTORY_BYTES,
    RANGE_DATA_LIMIT_PER_ZIP, _bounded_http_get_range,
    _parse_central_directory, _parse_eocd, probe_one_zip, main,
)

TEST_URL=("https://download.data.public.lu/resources/"
          "lidar-2019-releve-3d-du-territoire-luxembourgeois/"
          "20200201-010000/synthetic-point-cloud.zip")


def synthetic_zip(*, comment=b"", name="synthetic.laz"):
    with io.BytesIO() as sink:
        with ZipFile(sink,"w") as z:
            z.writestr(name,b"synthetic not actually lidar data",compress_type=ZIP_STORED)
            z.writestr("synthetic-qa.txt",b"test fixture only",compress_type=ZIP_DEFLATED)
            z.comment=comment
        return sink.getvalue()


class FakeResponse:
    def __init__(self,url,code,headers,payload=b""):
        self._url=url
        self.status=code
        self.headers=headers
        self.data=payload
        self.requested=[]
    def __enter__(self):
        return self
    def __exit__(self,*a):
        return False
    def geturl(self):
        return self._url
    def read(self,n=-1):
        self.requested.append(n)
        if n<=0 or n>MAX_CENTRAL_DIRECTORY_BYTES+1:
            raise AssertionError("Unbounded or negative read prohibited")
        return self.data[:n]


class FakeOpen:
    def __init__(self,bytes_,*,ignore_range=False,unexpected_origin=False,head_size_override=None,content_range_delta=0):
        self.bytes_=bytes_
        self.ignore_range=ignore_range
        self.unexpected_origin=unexpected_origin
        self.head_size_override=head_size_override
        self.content_range_delta=content_range_delta
        self.requests=[]
        self.responses=[]
    def open(self,req,timeout):
        self.requests.append(req)
        url="https://unexpected.example/not-approved" if self.unexpected_origin else TEST_URL
        if req.get_method()=="HEAD":
            n=self.head_size_override if self.head_size_override is not None else len(self.bytes_)
            r=FakeResponse(url,200,{"Content-Length":str(n)})
        else:
            span=req.headers["Range"]
            m=re.fullmatch(r"bytes=(\d+)-(\d+)",span)
            if not m:
                raise AssertionError("Range missing")
            start,end=map(int,m.groups())
            if self.ignore_range:
                r=FakeResponse(url,200,{"Content-Length":str(len(self.bytes_))},self.bytes_)
            else:
                r=FakeResponse(url,206,{
                    "Content-Range":f"bytes {start}-{end}/{len(self.bytes_)+self.content_range_delta}",
                    "Content-Length":str(end-start+1)},
                    self.bytes_[start:end+1])
        self.responses.append(r)
        return r


class SyntheticZipDirectoryTests(unittest.TestCase):
    def test_valid_zip_central_directory_aggregates_without_file_names(self):
        data=synthetic_zip()
        start=max(0,len(data)-MAX_EOCD_TAIL_BYTES)
        meta=_parse_eocd(data[start:],total=len(data),tail_start=start)
        body=data[meta["cd_start"]:meta["cd_start"]+meta["cd_bytes"]]
        out=_parse_central_directory(body,entries_expected=meta["entries"])
        self.assertEqual(out["entry_count"],2)
        self.assertEqual(out["entry_type_counts"],{"laz":1,"txt":1})
        self.assertFalse(out["full_original_zip_sha256_verified"])
        self.assertFalse(out["actual_las_laz_headers_inspected"])
        self.assertNotIn("synthetic.laz",str(out))
        self.assertTrue(out["central_directory_sha256_not_full_archive"])

    def test_full_zip_probe_returns_only_metadata_and_one_range(self):
        f=FakeOpen(synthetic_zip())
        out=probe_one_zip(TEST_URL,opener=f)
        self.assertEqual(out["zip_metadata_exact_range_get_count"],1)
        self.assertEqual(out["entry_type_counts"],{"laz":1,"txt":1})
        self.assertTrue(out["http_range_receipts_verified"])
        self.assertEqual(len(f.requests),2)
        self.assertEqual([req.get_method() for req in f.requests],["HEAD","GET"])
        self.assertEqual(sum(len(x.data) for x in f.responses),len(f.bytes_))
        self.assertFalse(out["full_original_zip_sha256_verified"])
        self.assertNotIn(TEST_URL,str(out))

    def test_maximum_zip_comment_requires_second_directory_range(self):
        f=FakeOpen(synthetic_zip(comment=b"a"*65535))
        out=probe_one_zip(TEST_URL,opener=f)
        self.assertEqual(out["entry_count"],2)
        self.assertEqual(out["zip_metadata_exact_range_get_count"],2)
        self.assertEqual(len(f.requests),3)
        self.assertLessEqual(out["zip_metadata_total_range_response_bytes"],RANGE_DATA_LIMIT_PER_ZIP)
        self.assertNotIn("synthetic.laz",str(out))

    def test_original_directory_cannot_be_accepted_from_full_http200(self):
        with self.assertRaisesRegex(DirectoryAuditError,"honor exact byte range"):
            probe_one_zip(TEST_URL,opener=FakeOpen(synthetic_zip(),ignore_range=True))

    def test_original_directory_cannot_be_accepted_from_mismatched_range_total(self):
        with self.assertRaisesRegex(DirectoryAuditError,"Content-Range mismatch"):
            probe_one_zip(TEST_URL,opener=FakeOpen(synthetic_zip(),content_range_delta=1))

    def test_source_origin_redirect_rejected(self):
        with self.assertRaises(DirectoryAuditError):
            probe_one_zip(TEST_URL,opener=FakeOpen(synthetic_zip(),unexpected_origin=True))

    def test_index_inferred_source_size_must_be_verified(self):
        with self.assertRaises(DirectoryAuditError):
            probe_one_zip(TEST_URL,opener=FakeOpen(synthetic_zip(),head_size_override=0))

    def test_unreviewed_source_url_blocks_without_network(self):
        with self.assertRaises(ValueError):
            probe_one_zip("https://example.org/unapproved.zip",opener=FakeOpen(synthetic_zip()))

    def test_fake_eocd_rejected(self):
        with self.assertRaises(DirectoryAuditError):
            _parse_eocd(b"x"*60,total=60,tail_start=0)

    def test_fake_overlong_zip_comment_rejected(self):
        raw=synthetic_zip()+b"not-listed-trailing-bytes"
        with self.assertRaises(DirectoryAuditError):
            _parse_eocd(raw,total=len(raw),tail_start=0)

    def test_zip64_unreviewed_size_rejected(self):
        raw=bytearray(synthetic_zip())
        pos=raw.rfind(b"PK\x05\x06")
        struct.pack_into("<I",raw,pos+12,0xFFFFFFFF)
        with self.assertRaisesRegex(DirectoryAuditError,"ZIP64"):
            _parse_eocd(bytes(raw),total=len(raw),tail_start=0)

    def test_truncated_central_member_rejected(self):
        with self.assertRaises(DirectoryAuditError):
            _parse_central_directory(b"PK\x01\x02",entries_expected=1)

    def test_directory_member_traversal_rejected(self):
        raw=synthetic_zip(name="../synthetic.laz")
        info=_parse_eocd(raw,total=len(raw),tail_start=0)
        body=raw[info["cd_start"]:info["cd_start"]+info["cd_bytes"]]
        with self.assertRaisesRegex(DirectoryAuditError,"member path"):
            _parse_central_directory(body,entries_expected=info["entries"])

    def test_member_encryption_rejected(self):
        raw=bytearray(synthetic_zip())
        info=_parse_eocd(bytes(raw),total=len(raw),tail_start=0)
        flags_at=info["cd_start"]+8
        old=struct.unpack_from("<H",raw,flags_at)[0]
        struct.pack_into("<H",raw,flags_at,old|1)
        meta=_parse_eocd(bytes(raw),total=len(raw),tail_start=0)
        body=bytes(raw[meta["cd_start"]:meta["cd_start"]+meta["cd_bytes"]])
        with self.assertRaisesRegex(DirectoryAuditError,"Encrypted"):
            _parse_central_directory(body,entries_expected=meta["entries"])

    def test_strict_metadata_range_budget(self):
        data=synthetic_zip()
        with self.assertRaisesRegex(DirectoryAuditError,"budget"):
            _bounded_http_get_range(TEST_URL,start=0,end=MAX_CENTRAL_DIRECTORY_BYTES,
                                    total=MAX_CENTRAL_DIRECTORY_BYTES+2,
                                    opener=FakeOpen(data))

    def test_missing_index_blocks_without_network(self):
        self.assertEqual(main(["--original-index","synthetic-nonexistent-original-index.json"]),2)


if __name__=="__main__":
    unittest.main()
