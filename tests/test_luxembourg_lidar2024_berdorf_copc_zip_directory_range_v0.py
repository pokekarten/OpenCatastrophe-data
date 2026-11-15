# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only two-source village ZIP metadata: no real archive bytes."""
from __future__ import annotations
from io import BytesIO
import json
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_STORED
import unittest
from research_runners.luxembourg_lidar2024_berdorf_copc_zip_directory_range_v0 import (
    SOURCES, BerdorfZipError, count_fixed_tiles, inspect, inspect_group,
)
from research_runners.luxembourg_lidar2024_copc_group_resource_head_v0 import RESOURCES
from research_runners.luxembourg_lidar2024_city_copc_zip_directory_range_v0 import (
    ZIP_TAIL_BYTES, parse_eocd, ZipRangeError
)


def fake_zip(names):
    output=BytesIO()
    with ZipFile(output,"w",compression=ZIP_STORED) as z:
        for name in names:
            z.writestr(name,b"NOT_REAL_LIDAR")
    return output.getvalue()


class FakeResponse:
    def __init__(self,code,body,headers):
        self.code=code; self.body=body; self.headers=headers; self.read_calls=0
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def getcode(self): return self.code
    def info(self): return self.headers
    def read(self,n):
        self.read_calls+=1
        return self.body[:n]


class FakeOpener:
    def __init__(self):
        self.source={}
        self.log=[]
        self.archive_body_reads=0
        for name,conf in SOURCES.items():
            uuid,slug=RESOURCES[name]
            uri="https://download.data.public.lu/resources/lidar2024/"+slug.lower().replace("_","-")+".zip"
            names=[tile+".laz" for tile in conf["tiles"]]+["UNRELATED_TILE.laz"]
            archive=fake_zip(names)
            self.source[uuid]={"config":conf,"url":uri,"zip":archive,"sha1":conf["sha1"]}
    def open(self,request,timeout):
        method=request.get_method()
        uri=request.full_url
        self.log.append((method,uri,request.get_header("Range")))
        for uuid,info in self.source.items():
            if uri.endswith("/"+uuid+"/"):
                original={
                    "id":uuid, "filesize":info["config"]["size"],"url":info["url"],
                    "checksum":{"type":"sha1","value":info["sha1"]}
                }
                return FakeResponse(200,json.dumps(original).encode(),{})
            if uri==info["url"]:
                size=info["config"]["size"]
                if method=="HEAD":
                    return FakeResponse(200,b"",{"Content-Length":str(size)})
                rng=request.get_header("Range")
                if not rng or not rng.startswith("bytes="):
                    raise AssertionError("Only bounded range GET is authorized")
                start,end=[int(x) for x in rng[6:].split("-")]
                if start==size-ZIP_TAIL_BYTES and end==size-1:
                    z=info["zip"]
                    content=bytes(ZIP_TAIL_BYTES-len(z))+z
                else:
                    z=info["zip"]
                    content=z[start:end+1]
                self.archive_body_reads+=len(content)
                return FakeResponse(206,content,{
                    "Content-Range":f"bytes {start}-{end}/{size}",
                    "Content-Length":str(end-start+1)
                })
        raise AssertionError("Unknown URL supplied to fake HTTP opener")


class BerdorfGroupsTests(unittest.TestCase):
    def setUp(self):
        self.opener=FakeOpener()

    def test_both_original_predeclared_groups_only_metadata(self):
        report=inspect(opener=self.opener)
        self.assertEqual(report["original_source_groups_checked"],2)
        self.assertEqual(report["actual_laz_point_bytes_read"],0)
        self.assertEqual(report["actual_original_zip_archive_payload_bytes_read"],0)
        self.assertTrue(report["original_source_metadata_only"])
        self.assertEqual(len(self.opener.log),8) # JSON,HEAD,tail,CD per group
        for r in report["results"]:
            self.assertEqual(r["fixed_village_source_tile_names_found_exactly_once"],2)
            self.assertEqual(r["declared_original_laz_member_count"],3)
            self.assertFalse(r["source_point_class_2_5_6_measured"])
            self.assertFalse(r["cat_model_input_admitted"])
        self.assertNotIn("92500_98500.laz",json.dumps(report))

    def test_unknown_site_rejected_before_network(self):
        with self.assertRaisesRegex(BerdorfZipError,"Unreviewed"):
            inspect_group("private-residence",opener=self.opener)
        self.assertEqual(self.opener.log,[])

    def test_missing_fixed_tile_fails(self):
        source=next(iter(SOURCES.values()))
        z=fake_zip([source["tiles"][0]+".laz","OTHER.laz"])
        tail=bytes(ZIP_TAIL_BYTES-len(z))+z
        meta=parse_eocd(tail,full_size=1701393927)
        directory=z[meta["directory_start"]:meta["directory_end"]+1]
        with self.assertRaisesRegex(BerdorfZipError,"missing"):
            count_fixed_tiles(directory,members=meta["members"],tiles=source["tiles"])

    def test_duplicate_fixed_tile_fails(self):
        source=next(iter(SOURCES.values()))
        z=fake_zip([source["tiles"][0]+".laz",
                    "backup/"+source["tiles"][0]+".laz",
                    source["tiles"][1]+".laz"])
        tail=bytes(ZIP_TAIL_BYTES-len(z))+z
        meta=parse_eocd(tail,full_size=1701393927)
        directory=z[meta["directory_start"]:meta["directory_end"]+1]
        with self.assertRaisesRegex(BerdorfZipError,"duplicated"):
            count_fixed_tiles(directory,members=meta["members"],tiles=source["tiles"])

    def test_source_not_a_laz_blocks(self):
        source=next(iter(SOURCES.values()))
        z=fake_zip([source["tiles"][0]+".txt",source["tiles"][1]+".laz"])
        tail=bytes(ZIP_TAIL_BYTES-len(z))+z
        meta=parse_eocd(tail,full_size=1701393927)
        directory=z[meta["directory_start"]:meta["directory_end"]+1]
        with self.assertRaisesRegex(BerdorfZipError,"not named"):
            count_fixed_tiles(directory,members=meta["members"],tiles=source["tiles"])

    def test_source_size_drift_fails_before_zip_range(self):
        uuid=next(iter(self.opener.source))
        self.opener.source[uuid]["config"]={**self.opener.source[uuid]["config"],"size":12345}
        with self.assertRaisesRegex(BerdorfZipError,"drift"):
            inspect(self.opener)
        self.assertEqual(len(self.opener.log),1)

    def test_publisher_checksum_drift_blocks_before_head(self):
        uuid=next(iter(self.opener.source))
        self.opener.source[uuid]["sha1"]="0"*40
        with self.assertRaisesRegex(BerdorfZipError,"drift"):
            inspect(self.opener)
        self.assertEqual(len(self.opener.log),1)

    def test_untrusted_provider_host_blocks_before_head(self):
        uuid=next(iter(self.opener.source))
        self.opener.source[uuid]["url"]="https://attacker.invalid/resources/lidar2024-c030-r028.zip"
        with self.assertRaisesRegex(BerdorfZipError,"Unreviewed"):
            inspect(self.opener)
        self.assertEqual(len(self.opener.log),1)

    def test_canonical_directory_parser_rejects_path_traversal(self):
        source=next(iter(SOURCES.values()))
        z=fake_zip(["../"+source["tiles"][0]+".laz",source["tiles"][1]+".laz"])
        tail=bytes(ZIP_TAIL_BYTES-len(z))+z
        meta=parse_eocd(tail,full_size=1701393927)
        directory=z[meta["directory_start"]:meta["directory_end"]+1]
        with self.assertRaisesRegex(ZipRangeError,"Unsafe"):
            count_fixed_tiles(directory,members=meta["members"],tiles=source["tiles"])


if __name__=="__main__":
    unittest.main()
