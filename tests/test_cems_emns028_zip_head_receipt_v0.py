# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic HEAD tests. No external HTTP requests."""
import unittest
from urllib.request import Request
from scripts.cems_emns028_zip_head_receipt_v0 import (
    OfficialRedirectOnly, SOURCE_URL, assert_expected_destination, probe,
)


class FakeResponse:
    status = 200
    headers = {"Content-Length": "12345", "Content-Type": "application/zip"}

    def geturl(self):
        return ("https://cems-mapping-website.s3.amazonaws.com/static/activations/"
                "EMSN028/EMNS028_AOI_FRANCE_utm31n.gdb.zip?Signature=SECRET")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, response=None):
        self.response = response or FakeResponse()
        self.request = None

    def open(self, req, timeout):
        self.request = req
        assert timeout <= 20
        return self.response


class HeadTests(unittest.TestCase):
    def test_static_official_source(self):
        self.assertEqual(assert_expected_destination(SOURCE_URL),
                         "mapping.emergency.copernicus.eu")

    def test_metadata_only_and_no_signed_query(self):
        opener = FakeOpener()
        result = probe(opener)
        self.assertTrue(result["head_accessible"])
        self.assertEqual(opener.request.get_method(), "HEAD")
        self.assertEqual(result["content_length_bytes"], 12345)
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(result["archive_sha256_verified"])
        self.assertFalse(result["aoi04_observed_flood_polygon_verified"])
        self.assertFalse(result["cat_model_admitted"])

    def test_missing_content_length_not_verified_access(self):
        class NoLength(FakeResponse):
            headers = {"Content-Type": "application/octet-stream"}
        self.assertFalse(probe(FakeOpener(NoLength()))["head_accessible"])

    def test_forbidden_external_redirect(self):
        with self.assertRaisesRegex(ValueError, "off-allowlist"):
            assert_expected_destination(
                "https://evil.example/EMNS028_AOI_FRANCE_utm31n.gdb.zip")

    def test_reject_wrong_product_and_http(self):
        with self.assertRaises(ValueError):
            assert_expected_destination(
                "https://mapping.emergency.copernicus.eu/download/EMSN028/OTHER.zip")
        with self.assertRaises(ValueError):
            assert_expected_destination(SOURCE_URL.replace("https://", "http://"))

    def test_redirect_disallows_other_host(self):
        req = Request(SOURCE_URL, method="HEAD")
        with self.assertRaises(ValueError):
            OfficialRedirectOnly().redirect_request(
                req, None, 302, "moved", {},
                "https://other.invalid/EMNS028_AOI_FRANCE_utm31n.gdb.zip")

    def test_non_success_response_fails_closed(self):
        class NonOk(FakeResponse):
            status = 403
        self.assertFalse(probe(FakeOpener(NonOk()))["head_accessible"])


if __name__ == "__main__":
    unittest.main()
