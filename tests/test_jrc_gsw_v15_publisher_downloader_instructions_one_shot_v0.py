# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only synthetic source HTML tests; no GeoTIFF or publisher network."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
from unittest import TestCase
from unittest.mock import patch
from urllib import request

from research_runners import jrc_gsw_v15_publisher_downloader_instructions_one_shot_v0 as jrc


def html():
    body = """<!DOCTYPE html><html><body>
<h1>Global Surface Water Explorer (GSWE)</h1>
<p>downloadWaterData_Python3_v1_5.py - European Commission</p>
<p>Aggregated products: downloads a single file per tile</p>
<p>longitudes 180W to 170E, latitudes 50S to 80N (360 tiles)</p>
<pre>https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/
download2024/Aggregated/VER1-5/&lt;dataset_name&gt;/&lt;dataset_name&gt;.tif</pre>
<p>occurrence is a percentage of valid water observations</p>
<p>Monthly History. If years and tile IDs are omitted, all years, all tiles</p>
<pre>download2024/monthlyhistory/VER1-5/</pre>
</body></html>"""
    return body.encode("utf-8")


class FakeResponse(io.BytesIO):
    def __init__(self, raw=None, url=jrc.URL, status=200, media="text/html", encoding="identity"):
        super().__init__(html() if raw is None else raw)
        self.url=url
        self.status=status
        self.headers={
            "Content-Type":media,
            "Content-Encoding":encoding,
            "Content-Length":str(len(self.getvalue())),
        }
    def geturl(self):
        return self.url


class JRCInstructionsEvidenceTests(TestCase):
    def test_synthetic_publisher_scope_and_360_tile_default(self):
        raw=html()
        r=jrc.inspect_instructions(raw)
        self.assertEqual(r["original_page_full_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["original_page_body_bytes"],len(raw))
        self.assertEqual(r["original_publisher_aggregated_default_tile_count"],360)
        self.assertFalse(r["aggregated_mode_explicit_one_tile_option_verified"])
        self.assertTrue(r["publisher_monthlyhistory_without_tile_filter_is_bulk"])
        self.assertEqual(r["reviewed_future_original_tile_url"],jrc.FIXED_TIFF)
        self.assertEqual(r["single_fixed_research_tile_id"],"10E_50N")
        for field in ("publisher_downloader_executed","cloudferro_original_tile_get_performed",
                      "cloudferro_anonymous_host_quota_verified",
                      "cloudferro_automated_bulk_access_approved",
                      "original_tiff_version_correction_verified",
                      "raw_html_body_stored","raw_tiff_body_stored",
                      "scientific_cat_model_input_approved"):
            with self.subTest(field=field):
                self.assertFalse(r[field])
        self.assertEqual(r["source_asset_network_requests_approved"],0)
        self.assertNotIn("<html",json.dumps(r).lower())

    def test_http_one_original_publisher_html_exact_get_only(self):
        seen=[]
        def opened(req,timeout):
            seen.append((req.get_method(),req.full_url,req.get_header("Accept"),
                         req.get_header("Accept-encoding"),timeout))
            return FakeResponse()
        rec=jrc.probe(open_request=opened,clock=lambda:datetime(2026,11,14,16,0,tzinfo=timezone.utc))
        self.assertEqual(seen,[("GET",jrc.URL,"text/html","identity",jrc.TIMEOUT)])
        self.assertEqual(rec["retrieval_utc"],"2026-11-14T16:00:00+00:00")
        self.assertEqual(rec["original_publisher_page_get_count"],1)
        self.assertFalse(rec["original_publisher_bytes_persisted"])
        self.assertFalse(rec["direct_GitHub_runner_self_attested"])

    def test_no_implicit_network_cli(self):
        with self.assertRaises(SystemExit):
            jrc.main([])
        with self.assertRaises(SystemExit):
            jrc.main(["--one"])
        with self.assertRaises(SystemExit):
            jrc.main(["--live"])
        with patch.object(jrc,"_open",side_effect=AssertionError("no network")):
            self.assertEqual(jrc.inspect_instructions(html())["source_asset_network_requests_approved"],0)

    def test_missing_original_markers_or_wrong_host_blocks(self):
        raw=html()
        for old,new in (
            (b"360 tiles",b"36 tiles"),
            (b"downloadWaterData_Python3_v1_5.py",b"downloadWaterData_Python3_v1_4.py"),
            (b"downloads a single file per tile",b"downloads all pixels in one response"),
            (b"download2024/Aggregated/VER1-5/",b"downloads2021/Aggregated/VER1-4/"),
            (b"download2024/monthlyhistory/VER1-5/",b"monthlyhistory/VER1-4/"),
            (b"all years",b"year 2024"),
            (b"occurrence",b"not_occurrence"),
            (b"s3.waw4-1.cloudferro.com",b"unknown.example"),
        ):
            changed=raw.replace(old,new)
            with self.subTest(old=old),self.assertRaises(jrc.InstructionBlocked):
                jrc.inspect_instructions(changed)

    def test_no_binary_html_oversize_or_zero(self):
        for raw in (b"",b"\xff",b"\x00"+html(),html()+b"x"*jrc.MAX_HTML_BYTES, "str"):
            with self.subTest(raw=str(type(raw))),self.assertRaises(jrc.InstructionBlocked):
                jrc.inspect_instructions(raw)

    def test_non_200_redirect_or_content_encoding_fails_before_read(self):
        for response in (
            FakeResponse(status=206),FakeResponse(status=302),
            FakeResponse(url=jrc.URL+"/redirect"),
            FakeResponse(media="application/json"),FakeResponse(encoding="gzip")
        ):
            with self.subTest(resp=(response.status,response.url)),self.assertRaises(jrc.InstructionBlocked):
                jrc.probe(open_request=lambda req,timeout:response)

    def test_bad_declared_or_actual_html_size(self):
        for value in ("NaN","0",str(jrc.MAX_HTML_BYTES+1)):
            response=FakeResponse()
            response.headers["Content-Length"]=value
            with self.subTest(value=value),self.assertRaises(jrc.InstructionBlocked):
                jrc.probe(open_request=lambda req,timeout:response)
        oversized=FakeResponse(raw=html()+b"x"*jrc.MAX_HTML_BYTES)
        oversized.headers.pop("Content-Length")
        with self.assertRaises(jrc.InstructionBlocked):
            jrc.probe(open_request=lambda req,timeout:oversized)

    def test_direct_urllib_get_timeout_keyword_not_http_body(self):
        calls=[]
        obj=object()
        class FakeOpener:
            def open(self,req,*args,**kwargs):
                calls.append((req,args,kwargs))
                return obj
        req=request.Request(jrc.URL,method="GET")
        with patch("research_runners.jrc_gsw_v15_publisher_downloader_instructions_one_shot_v0.request.build_opener",
                   return_value=FakeOpener()):
            self.assertIs(jrc._open(req,jrc.TIMEOUT),obj)
        self.assertEqual(calls[0][0].get_method(),"GET")
        self.assertEqual(calls[0][1],())
        self.assertEqual(calls[0][2],{"timeout":jrc.TIMEOUT})
