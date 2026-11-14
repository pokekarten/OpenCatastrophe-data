# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic tests: exact TIFF 4KiB original partial transport only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from scripts import preflight_jrc_gsw_v15_original_range_receipt_v0 as jrc


def fake_tiff() -> bytes:
    data = bytearray(jrc.PREFIX_BYTES)
    data[:4] = b"II*\x00"
    struct.pack_into("<I", data, 4, 8)
    entries = (
        (256, 4, 1, 40000), (257, 4, 1, 40000),
        (258, 3, 1, 8), (259, 3, 1, 1), (277, 3, 1, 1),
    )
    struct.pack_into("<H", data, 8, len(entries))
    for i, e in enumerate(entries):
        struct.pack_into("<HHII", data, 10 + 12*i, *e)
    struct.pack_into("<I", data, 10 + 12*len(entries), 0)
    return bytes(data)


def headers(total=18000000) -> dict[str, str]:
    return {
        "Content-Type": "image/tiff",
        "Content-Length": "4096",
        "Content-Range": f"bytes 0-4095/{total}",
        "Content-Encoding": "identity",
    }


def validate(**updates):
    kwargs = {
        "source_url": jrc.SOURCE_URL,
        "http_status": 206,
        "response_headers": headers(),
        "original_range_bytes": fake_tiff(),
    }
    kwargs.update(updates)
    return jrc.inspect_external_original_range(**kwargs)


class JRCTiffRangeTests(unittest.TestCase):
    def test_exact_bounded_original_206_with_tiff_prefix(self):
        r=validate()
        self.assertEqual(r["original_prefix_bytes"], 4096)
        self.assertEqual(r["claimed_whole_original_tiff_bytes_from_http_header_only"],18000000)
        self.assertEqual(r["original_prefix_sha256"],hashlib.sha256(fake_tiff()).hexdigest())
        self.assertTrue(r["first_ifd_fully_within_prefix"])
        self.assertTrue(r["expected_10_degree_tile_shape_if_inline"])
        self.assertTrue(r["one_byte_single_band_if_inline"])
        self.assertEqual(r["tiff_flavour"],"TIFF")
        self.assertEqual(r["supplied_response_http_status"],206)
        self.assertEqual(r["supplied_original_response_content_range"],"bytes 0-4095/18000000")

    def test_all_explicit_model_correction_source_network_flags_false(self):
        r=validate()
        for k in (
            "original_tiff_whole_body_sha256_verified",
            "original_post_2026_11_10_corrected_asset_verified",
            "source_anonymous_host_service_permission_reviewed",
            "current_research_source_access_contract_authorizes_range_request",
            "original_provider_request_executed_by_this_validator",
            "source_original_prefix_bytes_saved_by_this_validator",
            "native_geoaffine_crs_and_pixel_values_verified",
            "scientific_cat_model_input_approved",
        ):
            with self.subTest(k=k):
                self.assertFalse(r[k])

    def test_200_full_body_no_partial_range_is_rejected(self):
        for status in (200,201,302,403,404,416,500,True):
            with self.subTest(status=status),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(http_status=status)

    def test_wrong_original_fixed_provider_or_alternate_google_rejected(self):
        for url in (
            jrc.SOURCE_URL.replace("s3.waw4-1.cloudferro.com","storage.googleapis.com"),
            jrc.SOURCE_URL+"?download=true",
            jrc.SOURCE_URL.replace("VER1-5","VER1-4"),
            "",
        ):
            with self.subTest(url=url),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(source_url=url)

    def test_wrong_declared_original_range_or_partial_length(self):
        for value in (
            "bytes 0-8191/18000000",
            "bytes 1-4096/18000000",
            "bytes */18000000",
            "bytes 0-4095/*",
            "bytes 0-4095/0",
            "bytes 0-4095/4096",
            "bytes 0-4095/20000000001",
            "bytes 0-4095/0018000000",
            "BYTES 0-4095/18000000",
        ):
            h=headers()
            h["Content-Range"]=value
            with self.subTest(value=value),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(response_headers=h)

    def test_content_length_range_body_must_all_be_consistent(self):
        for size in ("0","4095","8192","bogus","+4096"):
            h=headers()
            h["Content-Length"]=size
            with self.subTest(size=size),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(response_headers=h)
        for body in (b"",fake_tiff()[:300],fake_tiff()+b"0",None):
            with self.subTest(body=str(type(body))),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(original_range_bytes=body)

    def test_no_compressed_media_html_or_non_native_raster(self):
        for changed in (
            {"Content-Type":"text/html"},
            {"Content-Type":"application/json"},
            {"Content-Type":"image/png"},
            {"Content-Encoding":"gzip"},
            {"Content-Encoding":"br"},
        ):
            h=headers()
            h.update(changed)
            with self.subTest(changed=changed),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(response_headers=h)
        h=headers()
        h["Content-Type"]="application/octet-stream"
        self.assertTrue(validate(response_headers=h)["first_ifd_fully_within_prefix"])

    def test_duplicate_case_fold_headers_and_bad_types_block(self):
        for h in (
            {"Content-Length":"4096","content-length":"4096", "Content-Type":"image/tiff","Content-Range":"bytes 0-4095/15000000"},
            {1:"value","Content-Type":"image/tiff"},
            {"Content-Type":None},
            None,
        ):
            with self.subTest(h=h),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(response_headers=h)

    def test_invalid_tiff_data_cannot_become_positive_transport_proof(self):
        for raw in (bytes(4096), b"not-a-tiff"+bytes(4086), bytes([255])*4096):
            with self.subTest(raw=raw[:15]),self.assertRaises(jrc.JRCOriginalRangeBlocked):
                validate(original_range_bytes=raw)

    def test_no_network_or_bulk_downloader_in_module(self):
        txt=Path(jrc.__file__).read_text(encoding="utf-8")
        for forbidden in ("urlopen(", "requests.get(", "http.client", "boto3", "urllib.request",
                          "cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/",
                          "def download", "threading", "multiprocessing"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,txt)
