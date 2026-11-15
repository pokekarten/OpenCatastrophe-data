# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic response tests; never reach the public provider."""
import unittest
from scripts.cems_emns028_zip_prefix_receipt_v0 import probe_prefix


class Response:
    def __init__(self, *, data=b"PK\x03\x04", status=206, cr="bytes 0-3/100"):
        self.data = data
        self.status = status
        self.headers = {"Content-Range": cr, "Content-Type": "application/octet-stream"}
        self.read_n = None

    def geturl(self):
        return ("https://cems-mapping-website.s3.amazonaws.com/static/activations/"
                "EMSN028/EMNS028_AOI_FRANCE_utm31n.gdb.zip?Signature=SECRET")

    def read(self, n):
        self.read_n = n
        return self.data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Opener:
    def __init__(self, response):
        self.response = response
        self.request = None

    def open(self, req, timeout):
        self.request = req
        return self.response


class PrefixTests(unittest.TestCase):
    def test_exact_byte_cap_and_no_unsafe_promotion(self):
        r = Response()
        o = Opener(r)
        result = probe_prefix(o)
        self.assertTrue(result["source_zip_available_for_further_rights_review"])
        self.assertTrue(result["range_honored"])
        self.assertEqual(result["archive_size_bytes_from_range"], 100)
        self.assertEqual(r.read_n, 4)
        self.assertEqual(o.request.get_header("Range"), "bytes=0-3")
        self.assertEqual(o.request.get_method(), "GET")
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(result["full_source_sha256_verified"])
        self.assertFalse(result["cat_model_admitted"])

    def test_html_is_not_zip(self):
        self.assertFalse(probe_prefix(Opener(Response(data=b"<htm", status=200)))
                         ["source_zip_available_for_further_rights_review"])

    def test_200_zip_ignored_range_is_clearly_marked(self):
        z = probe_prefix(Opener(Response(status=200, cr="")))
        self.assertTrue(z["source_zip_available_for_further_rights_review"])
        self.assertFalse(z["range_honored"])

    def test_bad_content_range_is_rejected(self):
        self.assertFalse(probe_prefix(Opener(Response(cr="bytes 5-8/100")))
                         ["source_zip_available_for_further_rights_review"])

    def test_no_archive_or_magic_invalid(self):
        self.assertFalse(probe_prefix(Opener(Response(data=b"PK")))
                         ["source_zip_available_for_further_rights_review"])


if __name__ == "__main__":
    unittest.main()
