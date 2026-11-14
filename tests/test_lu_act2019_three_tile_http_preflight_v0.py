# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests for bounded official ACT 2019 LiDAR tile probes."""
from __future__ import annotations

from pathlib import Path
import unittest
from urllib.error import HTTPError

from research_runners.lu_act2019_three_tile_http_preflight_v0 import (
    MAX_REMOTE_BYTES, EXPECTED_TOTAL_SITES, TileProbeError,
    build_site_windows, decode_total_length, probe_one, run, select_site_urls,
    validate_response_origin,
)

TEST_URL=("https://download.data.public.lu/resources/"
          "lidar-2019-releve-3d-du-territoire-luxembourgeois/"
          "20200221-123456/synthetic-not-real-point-data.zip")


class FakeResponse:
    def __init__(self,url,code=200,headers=None,prefix=b"",):
        self.url=url
        self.status=code
        self.headers=headers or {}
        self.prefix=prefix
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,n):
        self.read_sizes.append(n)
        if n != 4:
            raise AssertionError("Test reader asked for an unbounded body")
        return self.prefix[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class FakeOpen:
    def __init__(self,head,limited):
        self.responses=[head,limited]
        self.requests=[]
    def open(self,req,timeout):
        self.requests.append((req.get_method(),req.headers,timeout))
        if not self.responses:
            raise AssertionError("Unexpected source call")
        return self.responses.pop(0)


class OriginalTileHTTPTests(unittest.TestCase):
    def fake(self,*,length="345678901",status=206,range_length=None,prefix=b"PK\x03\x04"):
        head=FakeResponse(TEST_URL,headers={"Content-Length":length})
        response=FakeResponse(
            TEST_URL,code=status,
            headers={"Content-Range":"bytes 0-3/"+(range_length or length)},
            prefix=prefix)
        return FakeOpen(head,response),head,response

    def test_valid_range_headers_and_zip_prefix_while_never_downloading(self):
        opener,head,range_resp=self.fake()
        result=probe_one(TEST_URL,opener=opener)
        self.assertEqual(result["head_http"],200)
        self.assertEqual(result["head_content_length_bytes"],345678901)
        self.assertEqual(result["range_http"],206)
        self.assertTrue(result["range_206_supported"])
        self.assertTrue(result["range_full_size_matches_head"])
        self.assertTrue(result["first_four_bytes_zip_local_header"])
        self.assertFalse(result["original_archive_full_sha256_verified"])
        self.assertFalse(result["full_zip_download_attempted"])
        self.assertEqual(range_resp.read_sizes,[4])
        self.assertEqual([x[0] for x in opener.requests],["HEAD","GET"])
        self.assertEqual(len(opener.requests),2)
        self.assertNotIn(TEST_URL,str(result))

    def test_http200_range_ignored_never_treated_as_ranged(self):
        opener,head,ranged=self.fake(status=200)
        output=probe_one(TEST_URL,opener=opener)
        self.assertFalse(output["range_206_supported"])
        self.assertEqual(ranged.read_sizes,[])
        self.assertFalse(output["first_four_bytes_zip_local_header"])

    def test_bad_zip_prefix_not_full_integrity(self):
        opener,*_=self.fake(prefix=b"NOPE")
        output=probe_one(TEST_URL,opener=opener)
        self.assertTrue(output["range_206_supported"])
        self.assertFalse(output["first_four_bytes_zip_local_header"])
        self.assertFalse(output["original_archive_full_sha256_verified"])

    def test_mismatched_range_size_flagged(self):
        opener,*_=self.fake(range_length="345678902")
        output=probe_one(TEST_URL,opener=opener)
        self.assertFalse(output["range_full_size_matches_head"])

    def test_missing_remote_size_skips_range(self):
        opener,*_=self.fake(length="invalid")
        out=probe_one(TEST_URL,opener=opener)
        self.assertIsNone(out["head_content_length_bytes"])
        self.assertEqual(len(opener.requests),1)

    def test_enormous_source_size_skips_data(self):
        opener,*_=self.fake(length=str(MAX_REMOTE_BYTES+1))
        out=probe_one(TEST_URL,opener=opener)
        self.assertIsNone(out["head_content_length_bytes"])
        self.assertEqual(len(opener.requests),1)

    def test_invalid_original_url_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError,"Unreviewed original"):
            probe_one("https://other.example/private.zip")

    def test_redirect_origin_rejected_without_unsafe_echo(self):
        with self.assertRaises(TileProbeError):
            validate_response_origin(FakeResponse("https://other.example/private"),TEST_URL)

    def test_head_error_does_not_prove_access(self):
        class NoNetwork:
            def open(self,*args,**kw):
                raise TimeoutError("synthetic offline")
        out=probe_one(TEST_URL,opener=NoNetwork())
        self.assertIsNone(out["head_http"])
        self.assertFalse(out["range_206_supported"])

    def test_zero_invalid_and_nontext_http_sizes_blocked(self):
        for x in (None,"0","3","-5","1e4","1.2",str(MAX_REMOTE_BYTES+1),345):
            with self.subTest(x=x):
                self.assertIsNone(decode_total_length(x))
        self.assertEqual(decode_total_length("4"),4)

    def test_total_source_tile_scope_frozen(self):
        self.assertEqual(EXPECTED_TOTAL_SITES,3)

    def test_requires_all_predeclared_sites_before_optional_geometry_import(self):
        with self.assertRaisesRegex(ValueError,"FeatureCollection"):
            select_site_urls({},{})

    def test_missing_actual_original_index_fails_closed(self):
        with self.assertRaises(ValueError):
            run(Path("synthetic-absent-index.geojson"))


if __name__=="__main__":
    unittest.main()
