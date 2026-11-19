# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP prefix/HTTP range proof, no real network or source ZIP."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import struct
import unittest

from research_runners.berlin_srhk_depth_zip_prefix_v0 import (
    BYTE_COUNT, OBJECTS, RANGE, ROOT, TIMEOUT, PrefixError, inspect, probe,
)


def prefix(*, magic=b"PK\x03\x04", method=8, flags=0, name=b"synthetic.tif"):
    header = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, flags, method,
                         0, 0, 0, 0, 0, len(name), 0)
    raw = (header + name).ljust(BYTE_COUNT, b"\0")
    return magic + raw[4:]


def response_headers(scenario):
    return {"Content-Type": "application/zip", "Content-Length": str(BYTE_COUNT),
            "Content-Range": f"bytes 0-511/{OBJECTS[scenario][1]}"}


class Response(io.BytesIO):
    status = 206
    def __init__(self, *, scenario, body=None, url=None, headers=None):
        super().__init__(prefix() if body is None else body)
        self.url = url or ROOT + OBJECTS[scenario][0]
        self.headers = response_headers(scenario) if headers is None else headers
    def geturl(self):
        return self.url


class PrefixTests(unittest.TestCase):
    def test_both_exact_urls_get_only_512_bytes_with_original_length(self):
        for scenario, (filename, full_size) in OBJECTS.items():
            with self.subTest(scenario=scenario):
                calls = []
                def opener(req, timeout):
                    calls.append((req.full_url, req.get_method(), req.headers.get("Range"),
                                  req.headers.get("Accept-encoding"), timeout))
                    return Response(scenario=scenario)
                out = probe(scenario, opener=opener,
                            clock=lambda: datetime(2026,11,1,tzinfo=timezone.utc))
                self.assertEqual(calls, [(ROOT+filename, "GET", RANGE, "identity", TIMEOUT)])
                self.assertEqual(out["original_head_declared_object_bytes"], full_size)
                self.assertEqual(out["original_sample_bytes"], 512)
                self.assertTrue(out["http_partial_content_range_confirmed"])
                self.assertTrue(out["zip_first_file_local_signature_confirmed"])
                self.assertEqual(out["zip_first_file_compression_method_code"], 8)
                self.assertFalse(out["zip_decompression_or_tiff_bytes_performed"])
                self.assertFalse(out["building_or_insurer_database_modified"])
                self.assertFalse(out["original_provider_prefix_bytes_persisted"])
                self.assertFalse(out["true_source_crs_and_depth_values_verified"])
                self.assertEqual(len(out["original_sample_sha256_only"]), 64)
                self.assertNotIn("synthetic.tif", str(out))

    def test_range_ignored_server_and_wrong_source_url_blocked(self):
        class Full(Response):
            status = 200
        with self.assertRaisesRegex(PrefixError, "honor exact fixed range"):
            probe("extreme", opener=lambda req,t:Full(scenario="extreme"))
        with self.assertRaisesRegex(PrefixError, "honor exact fixed range"):
            probe("extreme", opener=lambda req,t:Response(
                scenario="extreme", url="https://else.invalid/zip"))
        with self.assertRaises(PrefixError):
            probe("unknown", opener=lambda req,t:Response(scenario="extreme"))

    def test_wrong_total_unknown_range_header_and_binary_type_blocked(self):
        scenario = "extreme"
        for change in (
            {"Content-Range": "bytes 0-511/12345"},
            {"Content-Range": "bytes 1-512/619211977"},
            {"Content-Range": "bytes 0-512/619211977"},
            {"Content-Length": "513"},
            {"Content-Type": "text/html"},
            {"Content-Encoding": "gzip"},
        ):
            with self.subTest(change=change):
                headers = {**response_headers(scenario), **change}
                with self.assertRaises(PrefixError):
                    inspect(prefix(), headers, scenario=scenario)

    def test_wrong_zip_magic_short_payload_and_encrypted_header_blocked(self):
        for raw in (prefix(magic=b"evil"), prefix(flags=1),
                    prefix()[:128], prefix()+b"extra",
                    b"0" * BYTE_COUNT):
            with self.subTest(first=raw[:8]), self.assertRaises(PrefixError):
                inspect(raw, response_headers("extreme"), scenario="extreme")

    def test_name_not_full_or_zero_length_blocked(self):
        for name in (b"", b"x"*500, b"a\x00b"):
            with self.subTest(name_len=len(name)), self.assertRaises(PrefixError):
                inspect(prefix(name=name), response_headers("extraordinary"),
                        scenario="extraordinary")

    def test_no_unverified_mime_or_naive_clock(self):
        with self.assertRaisesRegex(PrefixError, "UTC source receipt clock"):
            probe("extreme", opener=lambda req,t:Response(scenario="extreme"),
                  clock=lambda:datetime(2026,11,1))


if __name__ == "__main__":
    unittest.main()
