# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic USGS S1M original 64 KiB HTTP 206 header/rights negatives."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import struct
import unittest
from unittest.mock import patch

from scripts import probe_usgs_s1m_native_header_original_v0 as s


def sample_header(*, width=10000, height=10000, big=False):
    raw = bytearray(s.BYTE_COUNT)
    if not big:
        struct.pack_into("<2sHIH", raw, 0, b"II", 42, 8, 6)
        fields = [(256, 4, 1, width), (257, 4, 1, height),
                  (259, 3, 1, 8), (33550, 12, 3, 4000),
                  (34735, 3, 12, 6000), (42113, 2, 8, 5000)]
        for i, row in enumerate(fields):
            struct.pack_into("<HHII", raw, 10 + 12 * i, *row)
        struct.pack_into("<ddd", raw, 4000, 1.0, 1.0, 0.0)
        raw[5000:5008] = b"-999999\\x00".replace(b"\\x00", b"\x00")
        struct.pack_into("<12H", raw, 6000, 1, 1, 0, 2,
                         3072, 0, 1, 6350, 4096, 0, 1, 5703)
    else:
        struct.pack_into("<2sHHHQ", raw, 0, b"II", 43, 8, 0, 16)
        struct.pack_into("<Q", raw, 16, 4)
        rows = [(256, 16, 1, width), (257, 16, 1, height),
                (34735, 3, 8, 5000), (42113, 2, 8, 6000)]
        for i, row in enumerate(rows):
            struct.pack_into("<HHQQ", raw, 24 + 20 * i, *row)
        struct.pack_into("<8H", raw, 5000, 1, 1, 0, 1, 3072, 0, 1, 6350)
        raw[6000:6008] = b"-999999\\x00".replace(b"\\x00", b"\x00")
    return bytes(raw)


class Reply:
    def __init__(self, raw=None, *, status=206, url=s.URL,
                 content_range="bytes 0-65535/447032917", media="application/octet-stream",
                 content_length="65536", encoding="identity"):
        self.raw = sample_header() if raw is None else raw
        self.status = status
        self.url = url
        self.headers = {
            "Content-Range": content_range,
            "Content-Type": media,
            "Content-Encoding": encoding,
        }
        if content_length is not None:
            self.headers["Content-Length"] = content_length
        self.read_calls = 0

    def geturl(self):
        return self.url

    def read(self, cap):
        self.read_calls += 1
        return self.raw[:cap]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class USGSS1MOriginalPrefixTests(unittest.TestCase):
    def test_original_source_contract_is_source_locked_and_not_admitted(self):
        contract, digest = s.frozen_contract()
        self.assertEqual(contract["source_ids"], ["usgs.3dep.seamless-1m.s1m"])
        self.assertEqual(contract["status"], "probe_ready")
        self.assertEqual(contract["access_scope"], ["sample"])
        self.assertEqual(contract["request_contract"]["path_templates"], [s.PATH])
        self.assertEqual(contract["rights_and_policy"]["redistribution_status"], "unknown")
        self.assertEqual(contract["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(len(digest), 64)

    def test_classic_tiff_first_ifd_and_bigtiff_conservative_parse(self):
        for big in (False, True):
            with self.subTest(big=big):
                result = s.first_ifd(sample_header(big=big))
                self.assertTrue(result["source_tiff_magic_verified"])
                self.assertTrue(result["first_ifd_fully_in_prefix"])
                self.assertEqual(result["width_from_original_ifd"], 10000)
                self.assertEqual(result["height_from_original_ifd"], 10000)
                self.assertTrue(result["geokey_tag_present"])
                self.assertTrue(result["gdal_nodata_tag_present"])
                self.assertTrue(result["original_epsg_6350_verified"])
                self.assertTrue(result["original_nodata_minus999999_verified"])
                self.assertEqual(result["original_nodata_ascii_value"], "-999999")
                self.assertEqual(result["original_vertical_epsg_5703_verified"], not big)
                self.assertEqual(result["original_one_meter_scale_verified"], not big)
                self.assertFalse(result["native_raster_science_admitted"])

    def test_incomplete_tiff_ifd_stays_explicitly_unverified(self):
        raw = bytearray(sample_header())
        struct.pack_into("<I", raw, 4, s.BYTE_COUNT + 1)
        result = s.first_ifd(bytes(raw))
        self.assertFalse(result["first_ifd_fully_in_prefix"])
        self.assertIsNone(result["width_from_original_ifd"])

    def test_invalid_magic_duplicate_tags_and_unbounded_ifd_block(self):
        for raw in (b"garbage", b"II*\0" + b"\0" * 65532,
                    b"II+\0" + b"\0" * 65532):
            with self.subTest(magic=raw[:8]), self.assertRaises(s.Blocked):
                s.first_ifd(raw)
        changed = bytearray(sample_header())
        struct.pack_into("<H", changed, 8, 600)
        with self.assertRaises(s.Blocked):
            s.first_ifd(bytes(changed))
        changed = bytearray(sample_header())
        struct.pack_into("<H", changed, 10 + 12, 256)
        with self.assertRaises(s.Blocked):
            s.first_ifd(bytes(changed))

    def test_one_exact_206_original_request_success_is_not_full_file_proof(self):
        source = sample_header()
        response = Reply(source)
        calls = []
        def opener(req, timeout):
            calls.append((req.full_url, req.get_method(), req.headers.get("Range"), timeout))
            return response
        with patch.object(s, "EXPECTED_ORIGINAL_PREFIX_SHA256", hashlib.sha256(source).hexdigest()):
            result = s.observe(
                open_request=opener,
                clock=lambda: datetime(2026, 11, 16, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(calls, [(s.URL, "GET", s.BYTE_RANGE, s.TIMEOUT)])
        self.assertEqual(result["original_prefix_sha256"], hashlib.sha256(source).hexdigest())
        self.assertEqual(result["original_prefix_bytes"], 65536)
        self.assertEqual(result["original_total_bytes_advertised_not_full_sha"], 447032917)
        self.assertEqual(response.read_calls, 1)
        self.assertFalse(result["full_original_tiff_sha256_verified"])
        self.assertFalse(result["original_source_lineage_geopackage_verified"])
        self.assertFalse(result["cat_model_input_approved"])
        self.assertFalse(result["original_source_bytes_persisted"])
        self.assertFalse(result["neon_write_performed"])
        self.assertNotIn("II*\0", str(result))

    def test_pinned_genuine_original_receipt_blocks_synthetic_drift(self):
        self.assertEqual(
            s.EXPECTED_ORIGINAL_PREFIX_SHA256,
            "56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2")
        self.assertEqual(s.EXPECTED_ORIGINAL_TOTAL_BYTES, 447032917)
        with self.assertRaisesRegex(s.Blocked, "prefix SHA"):
            s.observe(open_request=lambda req, timeout: Reply())
        receipt = (s.ROOT /
                   "docs/research/usgs-s1m-florida-original-tiff-prefix-receipt-20261116.md"
                   ).read_text(encoding="utf-8")
        self.assertIn(s.EXPECTED_ORIGINAL_PREFIX_SHA256, receipt)
        self.assertIn("43948359780", receipt)

    def test_wrong_http_200_does_not_read_body_at_all(self):
        result = Reply(status=200)
        with self.assertRaises(s.Blocked):
            s.observe(open_request=lambda req, timeout: result)
        self.assertEqual(result.read_calls, 0)

    def test_content_range_mime_length_redirect_encoding_and_body_fail_closed(self):
        samples = (
            {"content_range": "bytes 1-65536/447000000"},
            {"content_range": "bytes 0-65535/*"},
            {"content_range": "bytes 0-65535/123"},
            {"content_range": "bytes 0-65535/9999999999999"},
            {"media": "text/html"},
            {"content_length": "65537"},
            {"content_length": "65k"},
            {"encoding": "gzip"},
            {"url": "https://unreviewed.example/other.tif"},
            {"raw": b"II*\0" + b"\0" * 65531},
            {"raw": sample_header() + b"x"},
        )
        for case in samples:
            with self.subTest(case=str(case)[:90]), self.assertRaises(s.Blocked):
                s.observe(open_request=lambda req, timeout: Reply(**case))

    def test_no_network_in_cli_without_explicit_flag(self):
        with patch("sys.argv", ["probe"]):
            with self.assertRaises(SystemExit) as c:
                s.main()
        self.assertEqual(c.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
