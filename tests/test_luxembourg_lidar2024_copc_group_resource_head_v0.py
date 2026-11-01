# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network deterministic official LiDAR 2024 three-resource HEAD tests."""
from __future__ import annotations

import json
import unittest
from urllib.parse import urlsplit

from research_runners.luxembourg_lidar2024_copc_group_resource_head_v0 import (
    RESOURCES, ArchiveReceiptError, inspect, _resource_entry,
)


class FakeResponse:
    def __init__(self,status=200,data=b"",headers=None):
        self.status=status
        self.body=data
        self.headers=headers or {}
        self.read_calls=0
    def getcode(self):
        return self.status
    def read(self,n=-1):
        self.read_calls+=1
        return self.body[:n]
    def info(self):
        return self.headers
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class FakeOpener:
    def __init__(self):
        self.records={}
        self.headers={}
        self.requests=[]
        self.head_responses=[]
    def open(self,request,timeout):
        self.requests.append((request.get_method(),request.full_url,timeout))
        if request.get_method()=="HEAD":
            result=FakeResponse(headers=self.headers.get(request.full_url,{"Content-Length":"1700000000"}))
            self.head_responses.append(result)
            return result
        resource_id=request.full_url.rstrip("/").split("/")[-1]
        return FakeResponse(data=json.dumps(self.records[resource_id]).encode("utf8"))


class COPCGroupTests(unittest.TestCase):
    def setUp(self):
        self.o=FakeOpener()
        for name,(rid,slug) in RESOURCES.items():
            url="https://download.data.public.lu/resources/lidar-2024/"+slug.lower()+".zip"
            self.o.records[rid]={"id":rid,"url":url,"size":1700000000,
                                 "checksum":{"type":"sha1","value":"a"*40}}
            self.o.headers[url]={"Content-Length":"1700000000"}

    def test_three_exact_official_metadata_and_head_only(self):
        report=inspect(opener=self.o)
        self.assertEqual(report["official_resource_records_queried"],3)
        self.assertEqual(report["original_archive_bytes_acquired"],0)
        self.assertEqual(report["total_source_group_bytes_head_declared"],5100000000)
        self.assertEqual(len(self.o.requests),6)
        self.assertEqual([m for m,_,_ in self.o.requests],["GET","HEAD"]*3)
        self.assertTrue(all(x["publisher_reported_checksums_unverified"]=={"sha1":"a"*40}
                            for x in report["resources"]))
        self.assertTrue(all(x["original_zip_bytes_downloaded"]==0 for x in report["resources"]))
        self.assertTrue(all(r.read_calls==0 for r in self.o.head_responses))
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("private_address",json.dumps(report))

    def test_wrong_resource_id_rejected(self):
        rid=next(iter(RESOURCES.values()))[0]
        self.o.records[rid]["id"]="not-original-resource"
        with self.assertRaisesRegex(ArchiveReceiptError,"UUID"):
            inspect(self.o)

    def test_untrusted_host_and_http_scheme_rejected_before_head(self):
        rid=next(iter(RESOURCES.values()))[0]
        for u in ("https://evil.invalid/Lidar2024_C020_R013.zip",
                  "http://download.data.public.lu/resources/Lidar2024_C020_R013.zip",
                  "https://download.data.public.lu/resources/Lidar2024_C020_R013.zip?sig=private",
                  "https://user:pass@download.data.public.lu/resources/Lidar2024_C020_R013.zip"):
            with self.subTest(url=u):
                self.o.records[rid]["url"]=u
                self.o.requests.clear()
                with self.assertRaisesRegex(ArchiveReceiptError,"origin"):
                    inspect(self.o)
                self.assertEqual([x[0] for x in self.o.requests],["GET"])
        self.o.records[rid]["url"]="https://download.data.public.lu/resources/lidar-2024_c020_r013.zip"

    def test_wrong_archive_group_slug_blocked(self):
        rid=next(iter(RESOURCES.values()))[0]
        self.o.records[rid]["url"]="https://download.data.public.lu/resources/other-original.zip"
        with self.assertRaisesRegex(ArchiveReceiptError,"name"):
            inspect(self.o)

    def test_source_catalogue_and_head_size_mismatch_blocked(self):
        name,(rid,slug)=next(iter(RESOURCES.items()))
        self.o.records[rid]["size"]=1700000001
        with self.assertRaisesRegex(ArchiveReceiptError,"disagree"):
            inspect(self.o)

    def test_missing_head_content_length_blocks(self):
        rid,slug=next(iter(RESOURCES.values()))
        url=self.o.records[rid]["url"]
        self.o.headers[url]={}
        with self.assertRaisesRegex(ArchiveReceiptError,"Content-Length"):
            inspect(self.o)

    def test_head_is_not_get_and_never_reads_large_file(self):
        report=inspect(self.o)
        self.assertEqual(len(self.o.head_responses),3)
        self.assertTrue(all(x.read_calls==0 for x in self.o.head_responses))
        self.assertEqual(report["original_archive_bytes_acquired"],0)

    def test_missing_resource_url_blocked(self):
        rid,_=next(iter(RESOURCES.values()))
        self.o.records[rid].pop("url")
        with self.assertRaisesRegex(ArchiveReceiptError,"download URL"):
            inspect(self.o)

    def test_invalid_unverified_checksum_not_claimed(self):
        rid,_=next(iter(RESOURCES.values()))
        self.o.records[rid]["checksum"]={"type":"sha256","value":"not-an-actual-sha"}
        receipt=inspect(self.o)
        self.assertEqual(receipt["resources"][0]["publisher_reported_checksums_unverified"],{})

    def test_bounded_metadata_size(self):
        rid,_=next(iter(RESOURCES.values()))
        self.o.records[rid]["blob"]="x"*300000
        with self.assertRaisesRegex(ArchiveReceiptError,"strict body cap"):
            inspect(self.o)

    def test_non_json_resource_blocks(self):
        rid,_=next(iter(RESOURCES.values()))
        self.o.records[rid]=["not","a","resource"]
        with self.assertRaisesRegex(ArchiveReceiptError,"JSON object"):
            inspect(self.o)


if __name__=="__main__":
    unittest.main()
