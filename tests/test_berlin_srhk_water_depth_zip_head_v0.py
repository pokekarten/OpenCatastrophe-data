# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic HTTP HEAD only, no ZIP bytes, no provider requests."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_srhk_water_depth_zip_head_v0 import (
    MAX_REVIEWED_SIZE, OBJECTS, ROOT, TIMEOUT, ZipHeadError, inspect_headers, probe,
)


class Fake(io.BytesIO):
    status = 200
    def __init__(self, *, url, headers=None):
        super().__init__(b"")
        self.url = url
        self.headers = headers or {
            "Content-Length": "23876394",
            "Content-Type": "application/zip",
            "Accept-Ranges": "bytes",
            "ETag": '"provider-etag-not-sha256"',
            "Last-Modified": "Sun, 01 Nov 2026 12:00:00 GMT",
        }
    def geturl(self):
        return self.url


class DepthZipHeadTests(unittest.TestCase):
    def test_exact_two_scenarios_and_no_get(self):
        for scenario, name in OBJECTS.items():
            with self.subTest(scenario=scenario):
                calls = []
                def opener(req, timeout):
                    calls.append((req.full_url, req.get_method(), timeout,
                                  req.headers.get("Accept-encoding")))
                    return Fake(url=ROOT + name)
                out = probe(scenario, opener=opener,
                            clock=lambda: datetime(2026,11,1,tzinfo=timezone.utc))
                self.assertEqual(calls, [(ROOT + name, "HEAD", TIMEOUT, "identity")])
                self.assertEqual(out["declared_content_length_bytes"], 23876394)
                self.assertTrue(out["server_claims_accept_ranges_bytes"])
                self.assertFalse(out["zip_bytes_fetched"])
                self.assertFalse(out["full_object_sha256_verified"])
                self.assertFalse(out["provider_rights_or_science_admitted"])
                self.assertFalse(out["building_hazard_or_insurer_loss_calculated"])
                self.assertTrue(out["geotiff_crs_25832_vs_25833_unresolved"])
                self.assertTrue(out["no_http_get_performed"])

    def test_missing_unknown_or_oversized_byte_length_refused(self):
        for value in ("", "0", "-1", "NaN", "1e7", "٣٠٠", str(MAX_REVIEWED_SIZE+1)):
            with self.subTest(length=value), self.assertRaises(ZipHeadError):
                inspect_headers({"Content-Length": value, "Content-Type": "application/zip"}, source="extreme")

    def test_unknown_media_or_encoded_source_refused(self):
        for media in ("text/html", "application/json", "", "image/tiff"):
            with self.subTest(media=media), self.assertRaisesRegex(ZipHeadError, "Content-Type"):
                inspect_headers({"Content-Length":"400", "Content-Type":media}, source="extreme")
        with self.assertRaisesRegex(ZipHeadError, "encoded"):
            inspect_headers({"Content-Length":"400", "Content-Type":"application/zip",
                             "Content-Encoding":"gzip"}, source="extreme")

    def test_nonrange_server_not_falsely_claimed_range_verified(self):
        out=inspect_headers({"Content-Length":"400", "Content-Type":"application/octet-stream"}, source="extreme")
        self.assertFalse(out["server_claims_accept_ranges_bytes"])
        self.assertTrue(out["server_accept_ranges_not_proven_by_get"])
        self.assertFalse(out["zip_payload_magic_verified"])
        self.assertIsNone(out["declared_last_modified_utc"])

    def test_changed_method_url_status_and_scenario_blocked(self):
        with self.assertRaises(ZipHeadError):
            probe("fake", opener=lambda req,t:Fake(url=ROOT + OBJECTS["extreme"]))
        for url in ("https://evil.invalid/file.zip", ROOT+"another.zip"):
            with self.subTest(url=url), self.assertRaisesRegex(ZipHeadError, "status/URL"):
                probe("extreme", opener=lambda req,t:Fake(url=url))
        class BadStatus(Fake):
            status=206
        with self.assertRaisesRegex(ZipHeadError, "status/URL"):
            probe("extreme",opener=lambda req,t:BadStatus(url=ROOT+OBJECTS["extreme"]))

    def test_etag_not_a_hash_and_invalid_dates_refused(self):
        for bad in ("not a date", "x"*121):
            with self.subTest(bad=bad[:20]), self.assertRaises(ZipHeadError):
                inspect_headers({"Content-Length":"450","Content-Type":"application/zip",
                                 "Last-Modified":bad},source="extreme")
        with self.assertRaisesRegex(ZipHeadError, "Accept-Ranges"):
            inspect_headers({"Content-Length":"450","Content-Type":"application/zip",
                             "Accept-Ranges":"unsupported"},source="extreme")

    def test_naive_receipt_clock_rejected(self):
        with self.assertRaisesRegex(ZipHeadError, "timezone"):
            probe("extreme",
                  opener=lambda req,t:Fake(url=ROOT+OBJECTS["extreme"]),
                  clock=lambda:datetime(2026,11,1))


if __name__ == "__main__":
    unittest.main()
