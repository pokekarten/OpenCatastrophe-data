# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests for JRC original-publisher HTML-only receipt."""
from __future__ import annotations

import hashlib
import io
import json
import unittest
from urllib import error
from unittest.mock import patch

from research_runners import jrc_gsw_v15_publisher_page_one_shot_v0 as jrc


def official_page() -> bytes:
    return (
        '<!DOCTYPE html><html><head><title>Global Surface Water - Data Access</title></head>'
        '<body><h1>Global Surface Water - Data Access</h1>'
        '<p>The new dataset 1984-2024 V1.5 is available.</p>'
        '<p>All data are provided free of charge without restriction of use.</p>'
        '<p>Source: EC JRC/Google</p>'
        '<p>UPDATE (November 10, 2026): corrected an anomaly on Occurrence '
        'with pixels exceeding 100%.</p>'
        '<a href="https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/">'
        'File listing V1.5</a></body></html>'
    ).encode("utf-8")


class Response(io.BytesIO):
    def __init__(self, raw=None, *, status=200, url=jrc.PUBLISHER_URL,
                 content_type="text/html", **headers):
        super().__init__(official_page() if raw is None else raw)
        self.status=status
        self._url=url
        self.headers={"Content-Type":content_type,"Content-Encoding":"identity",
                      "Content-Length":str(len(self.getvalue())),**headers}
        self.requested=[]

    def geturl(self):
        return self._url

    def read(self,n=-1):
        self.requested.append(n)
        return super().read(n)


class PublisherPageOneShotTests(unittest.TestCase):
    def test_fixed_html_metadata_only_with_real_original_sha_of_synthetic_body(self):
        raw=official_page()
        receipt=jrc.inspect_publisher_html(raw)
        self.assertEqual(receipt["source_id"],jrc.SOURCE)
        self.assertEqual(receipt["original_publisher_html_response_bytes"],len(raw))
        self.assertEqual(receipt["original_publisher_html_response_sha256"],
                         hashlib.sha256(raw).hexdigest())
        self.assertTrue(receipt["published_swift_catalogue_link_found"])
        self.assertTrue(receipt["november_10_2026_occurrence_correction_announcement_found"])
        self.assertFalse(receipt["source_original_catalogue_bytes_hashed"])
        self.assertFalse(receipt["individual_tile_original_bytes_hashed"])
        self.assertFalse(receipt["individual_tile_post_correction_bytes_verified"])
        self.assertFalse(receipt["cloudferro_service_api_terms_reviewed"])
        self.assertFalse(receipt["source_model_input_approved"])

    def test_exact_one_get_and_small_html_read_without_body_leak(self):
        calls=[]
        response=Response()
        def opener(req,timeout):
            calls.append((req.full_url,req.get_method(),req.get_header("Accept"),
                         req.get_header("Accept-encoding"),timeout))
            return response
        meta=jrc.probe(open_request=opener)
        self.assertEqual(calls,[(jrc.PUBLISHER_URL,"GET","text/html","identity",20)])
        self.assertEqual(response.requested,[jrc.MAX_HTML_BYTES+1])
        self.assertEqual(meta["http_status"],200)
        self.assertEqual(meta["retrieval_utc"].count("T"),1)
        self.assertTrue(meta["original_publisher_http_request_executed"])
        self.assertTrue(meta["no_redirects"])
        self.assertTrue(meta["no_retries"])
        self.assertFalse(meta["publisher_html_bytes_saved"])
        self.assertNotIn("<html",json.dumps(meta))

    def test_deny_forged_same_host_or_redirect_and_non200(self):
        for response in (Response(status=403),Response(status=206),
                         Response(url=jrc.PUBLISHER_URL+"/other"),
                         Response(url="https://evil.invalid/download")):
            with self.subTest(status=response.status,url=response.geturl()):
                with self.assertRaises(jrc.PublisherPageBlocked):
                    jrc.probe(open_request=lambda req,t: response)
                self.assertEqual(response.requested,[])

    def test_mismatched_media_encoding_lengths(self):
        for response in (
            Response(content_type="application/json"),
            Response(**{"Content-Encoding":"gzip"}),
            Response(**{"Content-Length":str(jrc.MAX_HTML_BYTES+1)}),
            Response(**{"Content-Length":"NaN"}),
            Response(**{"Content-Length":"0"}),
        ):
            with self.subTest(headers=response.headers):
                with self.assertRaises(jrc.PublisherPageBlocked):
                    jrc.probe(open_request=lambda req,t:response)
                self.assertEqual(response.requested,[])

    def test_response_body_over_cap_is_never_accepted(self):
        response=Response(raw=b"a"*(jrc.MAX_HTML_BYTES+1))
        response.headers.pop("Content-Length")
        with self.assertRaises(jrc.PublisherPageBlocked):
            jrc.probe(open_request=lambda req,t:response)
        self.assertEqual(response.requested,[jrc.MAX_HTML_BYTES+1])

    def test_disallow_ambiguous_link_or_incomplete_rights_context(self):
        raw=official_page()
        for changed in (
            raw.replace(jrc.ORIGINAL_CATALOGUE_URL.encode(),b"https://other.test/"),
            raw.replace(b"November 10, 2026",b"November 10, 2025"),
            raw.replace(b"exceeding 100%",b"exceeding 10%"),
            raw.replace(b"without restriction of use",b"research only"),
            raw.replace(b"Source: EC JRC/Google",b"Source: unknown"),
        ):
            with self.subTest(raw_head=changed[:65]),self.assertRaises(jrc.PublisherPageBlocked):
                jrc.inspect_publisher_html(changed)

    def test_html_text_required_and_invalid_binary_block(self):
        for raw in (b"",b"\xff",b"\x00"+official_page(),
                    official_page()+b"x"*(jrc.MAX_HTML_BYTES)):
            with self.assertRaises(jrc.PublisherPageBlocked):
                jrc.inspect_publisher_html(raw)
        with self.assertRaises(jrc.PublisherPageBlocked):
            jrc.inspect_publisher_html("HTML")

    def test_no_live_network_by_default_and_no_source_asset_calls(self):
        with self.assertRaises(SystemExit) as e:
            jrc.main([])
        self.assertNotEqual(e.exception.code,0)
        self.assertNotIn(jrc.FIXED_PRODUCT_TILE,jrc.PUBLISHER_URL)
        self.assertNotIn("cloudferro.com",jrc.PUBLISHER_URL)
        with patch.object(jrc,"_open_fixed",side_effect=AssertionError("network not authorized")):
            # Offline HTML inspection makes no network access.
            self.assertTrue(jrc.inspect_publisher_html(official_page())["published_swift_catalogue_link_found"])

    def test_http_error_must_be_blocked_without_source_details(self):
        def fail(req,timeout):
            raise error.URLError("original host temporarily down")
        with self.assertRaisesRegex(jrc.PublisherPageBlocked,"unavailable"):
            jrc.probe(open_request=fail)


if __name__=="__main__":
    unittest.main()
