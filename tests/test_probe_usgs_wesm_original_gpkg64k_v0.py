# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests for one pinned source-original WESM GeoPackage HTTP206."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import struct
import unittest
from unittest.mock import patch

from scripts import probe_usgs_wesm_original_gpkg64k_v0 as p


def sqlite_header(*, page_size=4096, pages=5000, app_id=p.GPKG_APPLICATION_ID):
    raw = bytearray(p.COUNT)
    raw[:16] = p.MAGIC
    struct.pack_into(">H", raw, 16, 1 if page_size == 65536 else page_size)
    raw[18:20] = b"\x01\x01"
    raw[20:24] = bytes((0, 64, 32, 32))
    struct.pack_into(">I", raw, 28, pages)
    struct.pack_into(">I", raw, 44, 4)
    struct.pack_into(">I", raw, 56, 1)
    struct.pack_into(">I", raw, 60, 10400)
    struct.pack_into(">I", raw, 68, app_id)
    struct.pack_into(">I", raw, 96, 3046001)
    return bytes(raw)


class Response:
    def __init__(self, *, raw=None, status=206, url=p.URL,
                 content_range="bytes 0-65535/20480000",
                 mime="application/octet-stream", length="65536",
                 encoding="identity"):
        self.status = status
        self.url = url
        self.raw = sqlite_header() if raw is None else raw
        self.headers = {
            "Content-Range": content_range,
            "Content-Type": mime,
            "Content-Encoding": encoding,
        }
        if length is not None:
            self.headers["Content-Length"] = length
        self.reads = 0
    def geturl(self):
        return self.url
    def read(self, max_bytes):
        self.reads += 1
        return self.raw[:max_bytes]
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False


class OriginalGPKGTests(unittest.TestCase):
    def test_source_contract_is_exact_and_not_raw_data_admission(self):
        self.assertEqual(len(p.frozen_contract()), 64)
        self.assertEqual(p.URL,
            "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg")
        self.assertEqual(p.RANGE, "bytes=0-65535")

    def test_sqlite_header_native_gpkg_page_identity_only(self):
        result = p.sqlite_original_header(sqlite_header(), 20480000)
        self.assertTrue(result["native_sqlite_format_3_verified"])
        self.assertTrue(result["native_ogc_gpkg_application_id_verified"])
        self.assertEqual(result["source_sqlite_page_size_bytes"], 4096)
        self.assertEqual(result["source_sqlite_declared_page_count"], 5000)
        self.assertEqual(result["source_gpkg_application_id_hex"], "0x47504b47")
        self.assertFalse(result["original_gpkg_contents_srs_geometry_verified"])
        self.assertFalse(result["original_wesm_workunit_polygon_count_verified"])

    def test_one_and_only_one_source_range_request_receipt(self):
        response = Response()
        calls = []
        def opener(req, timeout):
            calls.append((req.full_url, req.get_method(),
                          req.headers.get("Range"), timeout))
            return response
        with patch.object(p, "EXPECTED_TOTAL", 20480000), \
             patch.object(p, "EXPECTED_PREFIX_SHA", sha256(response.raw).hexdigest()):
            out = p.observe(opener=opener,
                clock=lambda: datetime(2026,11,16,22,20,tzinfo=timezone.utc))
        self.assertEqual(calls, [(p.URL, "GET", p.RANGE, p.TIMEOUT)])
        self.assertEqual(response.reads, 1)
        self.assertEqual(out["original_prefix_sha256"], sha256(response.raw).hexdigest())
        self.assertEqual(out["original_total_bytes_advertised_not_full_hash"], 20480000)
        self.assertEqual(out["source_sqlite_page_size_bytes"], 4096)
        self.assertEqual(out["source_gpkg_user_version"], 10400)
        self.assertNotIn("SQLite format 3", str(out))
        for k in ("original_full_wesm_gpkg_sha256_verified",
                  "original_wesm_csv_to_gpkg_version_parity_verified",
                  "original_florida_s1m_source_workunit_spatial_join_verified",
                  "original_geo_source_bytes_persisted",
                  "neon_write_performed", "cat_model_input_approved"):
            self.assertIs(out[k], False)

    def test_advertised_original_gpkg_total_is_strictly_pinned(self):
        self.assertEqual(p.EXPECTED_TOTAL, 3827232768)
        self.assertEqual(p.COUNT, 65536)
        response = Response()
        with self.assertRaisesRegex(p.Blocked, "full-object size drift"):
            p.observe(opener=lambda req, timeout: response)
        self.assertEqual(response.reads, 0)

    def test_genuine_source_sha_pin_and_spoofed_prefix_blocked(self):
        self.assertEqual(p.EXPECTED_PREFIX_SHA,
            "0344f898d4946a915ca0c3a5d0078fd72dc222179c54d8e9413a067c8ce5be88")
        self.assertEqual(p.EXPECTED_TOTAL, 3827232768)
        receipt = (
            p.ROOT / "docs/research/usgs-wesm-gpkg-original-64k-receipt-20261116.md"
        ).read_text(encoding="utf-8")
        self.assertIn(p.EXPECTED_PREFIX_SHA, receipt)
        self.assertIn("43968769537", receipt)
        response = Response()
        with patch.object(p, "EXPECTED_TOTAL", 20480000):
            with self.assertRaisesRegex(p.Blocked, "prefix SHA drift"):
                p.observe(opener=lambda req, timeout: response)
        self.assertEqual(response.reads, 1)

    def test_http_200_ignored_range_rejected_before_source_body(self):
        response = Response(status=200)
        with self.assertRaisesRegex(p.Blocked,"HTTP206"):
            p.observe(opener=lambda req,timeout:response)
        self.assertEqual(response.reads, 0)

    def test_original_header_invalid_magic_page_count_and_gpkg_id(self):
        options = (
            (sqlite_header(app_id=0), 20480000),
            (sqlite_header(pages=4000), 20480000),
            (sqlite_header(page_size=2048), 20480000),
            (sqlite_header(), 20480001),
            (sqlite_header(), 0),
            (sqlite_header()[:-1], 20480000),
            (b"bad" + sqlite_header()[3:], 20480000),
        )
        for data, total in options:
            with self.subTest(total=total, start=data[:4]), self.assertRaises(p.Blocked):
                p.sqlite_original_header(data,total)

    def test_network_shape_encoding_host_mime_and_length_fail_closed(self):
        scenarios = (
            {"status":200},
            {"url":"https://unreviewed.invalid/WESM.gpkg"},
            {"content_range":"bytes 1-65536/20480000"},
            {"content_range":"bytes 0-65535/*"},
            {"content_range":"bytes 0-65535/100"},
            {"mime":"text/html"},
            {"encoding":"gzip"},
            {"length":"65537"},
            {"length":"64k"},
            {"raw":sqlite_header()[:-1]},
            {"raw":sqlite_header()+b"x"},
        )
        for scenario in scenarios:
            with self.subTest(scenario=repr(scenario)[:90]), self.assertRaises(p.Blocked):
                p.observe(opener=lambda req,timeout:Response(**scenario))

    def test_no_implicit_original_download(self):
        with patch("sys.argv", ["probe"]):
            with self.assertRaises(SystemExit) as e:
                p.main()
        self.assertEqual(e.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
