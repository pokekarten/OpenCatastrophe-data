# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline faked network responses: never fetch national original COG bytes."""
from __future__ import annotations

import hashlib
import unittest

from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    CogRangeError, RANGE_BYTES, read_header_range
)


class SyntheticResponse:
    def __init__(self, status=206, content_range="bytes 0-4095/40123456789",
                 data=None, length="4096"):
        self.status=status
        self.meta={"Content-Range":content_range,"Content-Length":length}
        self.data=data if data is not None else b"II+\x00"+bytes(RANGE_BYTES-4)
        self.read_count=0
    def __enter__(self):
        return self
    def __exit__(self,*args):
        pass
    def getcode(self):
        return self.status
    def info(self):
        return self.meta
    def read(self,count):
        self.read_count+=1
        return self.data


class SyntheticOpener:
    def __init__(self,response):
        self.response=response
        self.requests=[]
    def open(self,request,timeout):
        self.requests.append((request,timeout))
        return self.response


class OfficialCogRangeTests(unittest.TestCase):
    def test_pinned_4k_bigtiff_response(self):
        source=SyntheticResponse()
        opener=SyntheticOpener(source)
        receipt=read_header_range("MNS",opener=opener)
        self.assertTrue(receipt["range_verified"])
        self.assertEqual(receipt["range_request_bytes"],4096)
        self.assertEqual(receipt["provider_http_status"],206)
        self.assertEqual(receipt["tiff_header_format"],"BigTIFF")
        self.assertEqual(receipt["first_4k_sha256_only_not_full_file"],hashlib.sha256(source.data).hexdigest())
        self.assertFalse(receipt["source_full_file_sha256_verified"])
        self.assertFalse(receipt["actual_building_heights_measured"])
        self.assertEqual(source.read_count,1)
        req,timeout=opener.requests[0]
        self.assertEqual(req.get_header("Range"),"bytes=0-4095")
        self.assertIn("MNS_Lidar2024.tif",req.full_url)
        self.assertEqual(timeout,20)

    def test_allows_both_official_mnt_and_mns(self):
        for asset in ("MNT","MNS"):
            with self.subTest(asset=asset):
                opener=SyntheticOpener(SyntheticResponse())
                report=read_header_range(asset,opener=opener)
                self.assertEqual(report["asset"],asset)

    def test_does_not_read_on_server_full_download_response(self):
        response=SyntheticResponse(status=200)
        with self.assertRaisesRegex(CogRangeError,"did not honour"):
            read_header_range("MNS",opener=SyntheticOpener(response))
        self.assertEqual(response.read_count,0)

    def test_strict_content_range_mismatch_blocks(self):
        for cr in ("bytes 0-8191/40123456789","bytes 0-4095/*","bytes 1-4096/40123456789"):
            with self.subTest(cr=cr),self.assertRaisesRegex(CogRangeError,"Content-Range"):
                read_header_range("MNT",opener=SyntheticOpener(SyntheticResponse(content_range=cr)))

    def test_full_file_declared_size_outside_budget_blocks(self):
        for total in ("9","999999999999"):
            with self.subTest(total=total),self.assertRaisesRegex(CogRangeError,"byte count"):
                read_header_range("MNS",opener=SyntheticOpener(SyntheticResponse(content_range="bytes 0-4095/"+total)))

    def test_unexpected_fragment_byte_length_blocks(self):
        with self.assertRaisesRegex(CogRangeError,"Truncated"):
            read_header_range("MNT",opener=SyntheticOpener(SyntheticResponse(data=b"II+\x00"+bytes(100))))

    def test_response_content_length_mismatch_blocks(self):
        with self.assertRaisesRegex(CogRangeError,"content-length"):
            read_header_range("MNT",opener=SyntheticOpener(SyntheticResponse(length="4000")))

    def test_not_a_geotiff_header_blocks(self):
        with self.assertRaisesRegex(CogRangeError,"not a TIFF"):
            read_header_range("MNT",opener=SyntheticOpener(SyntheticResponse(data=b"JSON"+bytes(4092))))

    def test_unknown_asset_cannot_inject_url(self):
        with self.assertRaisesRegex(CogRangeError,"Unrecognized"):
            read_header_range("http://example.org/",opener=SyntheticOpener(SyntheticResponse()))


if __name__=="__main__":
    unittest.main()
