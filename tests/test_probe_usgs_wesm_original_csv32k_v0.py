# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original WESM CSV HTTP206 semantics: synthetic bytes, no provider body."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import unittest
from unittest.mock import patch

from scripts import probe_usgs_wesm_original_csv32k_v0 as s


def synthetic(prefix=None):
    if prefix is None:
        prefix = b"workunit_id,project_id,lpc_category,sourcedem_category,seamless_category,seamless_reason\n"
    return (prefix + b"PRIVATE ORIGINAL ROW NEVER PRINTED\n" + b"Z" * s.BYTES)[:s.BYTES]


class Response:
    def __init__(self, raw=None, status=206, url=s.URL, content_range="bytes 0-32767/12000000",
                 length="32768", mime="application/octet-stream", encoding="identity"):
        self.body = synthetic() if raw is None else raw
        self.url = url
        self.status = status
        self.headers = {"Content-Range":content_range, "Content-Encoding":encoding,
                        "Content-Type":mime}
        if length is not None:
            self.headers["Content-Length"] = length
        self.reads = 0
    def geturl(self): return self.url
    def read(self, cap):
        self.reads += 1
        return self.body[:cap]
    def __enter__(self): return self
    def __exit__(self, *_): return False


class OriginalWESMTests(unittest.TestCase):
    def test_exact_source_contract_review_is_not_model_admission(self):
        self.assertEqual(len(s.validate_contract()), 64)
        self.assertEqual(s.URL, "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv")

    def test_csv_first_header_only_and_privacy_boundary(self):
        data = s.original_csv_column_header(synthetic())
        self.assertTrue(data["has_workunit_identity_field"])
        self.assertTrue(data["has_project_identity_field"])
        self.assertTrue(data["has_seamless_quality_category_field"])
        self.assertEqual(data["original_header_column_count"], 6)
        self.assertFalse(data["original_data_row_values_read"])
        self.assertNotIn("PRIVATE ORIGINAL ROW", str(data))

    def test_one_original_http206_returns_only_snapshot_prefix_hash(self):
        response = Response()
        requests = []
        def opener(req, timeout):
            requests.append((req.get_method(), req.full_url, req.headers.get("Range"),timeout))
            return response
        with patch.object(s, "EXPECTED_PREFIX_SHA", hashlib.sha256(response.body).hexdigest()):
            out = s.probe(opener=opener,clock=lambda: datetime(2026,11,16,21,30,tzinfo=timezone.utc))
        self.assertEqual(requests, [("GET",s.URL,s.RANGE,s.TIMEOUT)])
        self.assertEqual(out["original_prefix_sha256"],hashlib.sha256(response.body).hexdigest())
        self.assertEqual(out["advertised_full_csv_bytes_not_full_hash"],12000000)
        self.assertEqual(response.reads,1)
        for k in ("full_original_wesm_csv_sha256_verified","original_wesm_geopackage_verified",
                  "florida_s1m_spatial_workunit_join_verified", "source_bytes_persisted",
                  "neon_write_performed", "cat_model_input_approved"):
            self.assertIs(out[k], False)
        self.assertNotIn("PRIVATE ORIGINAL ROW", str(out))

    def test_real_original_prefix_identity_is_frozen_and_synthetic_drift_blocks(self):
        self.assertEqual(s.EXPECTED_PREFIX_SHA,
                         "19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d")
        self.assertEqual(s.EXPECTED_WHOLE_CSV_BYTES, 2267051)
        with self.assertRaisesRegex(s.Blocked, "original source prefix SHA"):
            s.probe(opener=lambda req, timeout: Response())
        receipt = (s.ROOT / "docs/research/usgs-wesm-original-csv-header-receipt-20261116.md"
                   ).read_text(encoding="utf-8")
        self.assertIn(s.EXPECTED_PREFIX_SHA, receipt)
        self.assertIn("43961768133", receipt)

    def test_http200_range_ignored_never_reads_source_body(self):
        response = Response(status=200)
        with self.assertRaisesRegex(s.Blocked,"HTTP206"):
            s.probe(opener=lambda req,timeout: response)
        self.assertEqual(response.reads,0)

    def test_malformed_source_header_duplicate_and_injection_rejected(self):
        bad = (
            b"",b"bad\n",b"a,a,project_id,lpc_category,sourcedem_category,seamless_category\n",
            b"<html>,project_id,lpc_category,sourcedem_category,seamless_category\n",
            b"good,bad\nheader,other,a,b,c\n",
            b"hello\x00,project_id,lpc_category,sourcedem_category,seamless_category\n",
            b"a,b,c,d,e\xff\n",
        )
        for x in bad:
            with self.subTest(header=x[:24]),self.assertRaises(s.Blocked):
                s.original_csv_column_header(synthetic(x))

    def test_unreviewed_original_http_range_length_mime_redirect_and_body_rejected(self):
        cases = (
            {"url":"https://untrusted.example/WESM.csv"},
            {"content_range":"bytes 0-65536/12000000"},
            {"content_range":"bytes 0-32767/*"},
            {"content_range":"bytes 0-32767/1024"},
            {"mime":"text/html"},
            {"encoding":"gzip"},
            {"length":"99999"},
            {"length":"32k"},
            {"raw":synthetic() + b"a"},
            {"raw":synthetic()[:-1]},
        )
        for c in cases:
            with self.subTest(case=repr(c)[:80]),self.assertRaises(s.Blocked):
                s.probe(opener=lambda req,timeout: Response(**c))

    def test_cli_refuses_implicit_network(self):
        with patch("sys.argv",["probe-wesm"]):
            with self.assertRaises(SystemExit) as cm:
                s.main()
            self.assertEqual(cm.exception.code, 2)


if __name__=="__main__":
    unittest.main()
