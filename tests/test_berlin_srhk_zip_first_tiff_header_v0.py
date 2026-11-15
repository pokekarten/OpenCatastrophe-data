# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial synthetic ZIP/TIFF samples; absolutely no external source bytes."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import struct
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.berlin_srhk_zip_first_tiff_header_v0 import (
    READ_BYTES, MAX_DECOMPRESSED_PREFIX, OBJECTS, ROOT, LAST_MODIFIED, TIMEOUT,
    TiffHeaderError, inspect_prefix, decode_tiff_metadata, validate_response, probe,
)


def classic_tiff(epsg=25833):
    geo = struct.pack("<8H", 1, 1, 0, 1, 3072, 0, 1, epsg)
    return (b"II" + struct.pack("<HI", 42, 8)
            + struct.pack("<H", 1)
            + struct.pack("<HHII", 34735, 3, 8, 26)
            + struct.pack("<I", 0) + geo)


def synthetic_zip(scenario="extreme", member_content=None):
    if member_content is None:
        member_content = classic_tiff()
    name_length = 38 if scenario == "extreme" else 39
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as z:
        z.writestr("n"*(name_length-4) + ".tif", member_content)
    raw = archive.getvalue()
    assert len(raw) < READ_BYTES, len(raw)
    return raw.ljust(READ_BYTES, b"\0")


def headers(scenario="extreme"):
    return {"Content-Range": f"bytes 0-{READ_BYTES-1}/{OBJECTS[scenario][1]}",
            "Content-Length": str(READ_BYTES),
            "Content-Type": "application/zip",
            "Last-Modified": LAST_MODIFIED[scenario]}


class Fake(BytesIO):
    status = 206
    def __init__(self, scenario, raw=None, url=None, response_headers=None):
        super().__init__(synthetic_zip(scenario) if raw is None else raw)
        self.url = url or ROOT + OBJECTS[scenario][0]
        self.headers = headers(scenario) if response_headers is None else response_headers
        self.read_calls = 0
    def geturl(self):
        return self.url
    def read(self, n=-1):
        self.read_calls += 1
        return super().read(n)


class TiffSourcePrefixTests(unittest.TestCase):
    def test_projected_geokey_from_locally_generated_zip(self):
        for scenario in OBJECTS:
            with self.subTest(scenario=scenario):
                raw = synthetic_zip(scenario)
                receipt = inspect_prefix(raw, scenario=scenario,
                                         expected_512_sha=sha256(raw[:512]).hexdigest())
                self.assertTrue(receipt["prior_exact_512_byte_sha256_same"])
                self.assertEqual(receipt["projected_epsg_from_first_geokey"], 25833)
                self.assertEqual(receipt["tiff_variant"], "classic_tiff")
                self.assertEqual(receipt["tiff_byte_order"], "little")
                self.assertTrue(receipt["geokey_directory_values_available_in_prefix"])
                self.assertFalse(receipt["hazard_raster_pixels_or_buildings_sampled"])
                self.assertFalse(receipt["geotiff_full_crs_and_affine_grid_validated"])
                self.assertFalse(receipt["original_depth_units_or_nodata_validated"])
                self.assertFalse(receipt["original_tiff_prefix_or_zip_bytes_persisted"])

    def test_original_source_prefix_hash_gate_refuses_wrong_sample(self):
        raw = synthetic_zip()
        with self.assertRaisesRegex(TiffHeaderError, "pinned"):
            inspect_prefix(raw, scenario="extreme", expected_512_sha="0"*64)

    def test_big_tiff_header_accepted_without_inventing_geokeys(self):
        raw = b"II" + struct.pack("<HHHQ", 43, 8, 0, 16) + b"\0"*40
        meta = decode_tiff_metadata(raw)
        self.assertTrue(meta["original_member_tiff_header_confirmed"])
        self.assertEqual(meta["tiff_variant"], "bigtiff")
        self.assertIsNone(meta["projected_epsg_from_first_geokey"])
        self.assertFalse(meta["tiff_first_ifd_fully_available_in_prefix"])

    def test_out_of_prefix_ifd_does_not_invent_crs(self):
        prefix = b"II" + struct.pack("<HI", 42, 4_000_000) + b"\0"*100
        meta = decode_tiff_metadata(prefix)
        self.assertFalse(meta["tiff_first_ifd_fully_available_in_prefix"])
        self.assertIsNone(meta["projected_epsg_from_first_geokey"])

    def test_malicious_tiff_magic_ifd_count_and_geo_directory_rejected(self):
        for bad in (b"", b"THIS IS NOT TIFF", b"II" + struct.pack("<HI", 37, 8) + b"\0"*100):
            with self.subTest(raw=bad[:10]), self.assertRaises(TiffHeaderError):
                decode_tiff_metadata(bad)
        bad = bytearray(classic_tiff())
        struct.pack_into("<H", bad, 8, 513)
        with self.assertRaisesRegex(TiffHeaderError, "unbounded"):
            decode_tiff_metadata(bytes(bad))
        bad = bytearray(classic_tiff())
        struct.pack_into("<H", bad, 12, 4)  # wrong type
        with self.assertRaisesRegex(TiffHeaderError, "GeoKeyDirectory"):
            decode_tiff_metadata(bytes(bad))

    def test_zip_local_header_changed_or_truncated_or_over_budget_rejected(self):
        good = synthetic_zip()
        for original in (
            good[:100], good+b"EXTRA", b"bad!" + good[4:],
            good[:8] + b"bad" + good[11:],
        ):
            with self.subTest(raw_length=len(original)), self.assertRaises(TiffHeaderError):
                inspect_prefix(original, scenario="extreme",
                               expected_512_sha=sha256(original[:512]).hexdigest())

    def test_response_206_and_trusted_source_version(self):
        for scenario in OBJECTS:
            with self.subTest(scenario=scenario):
                source = synthetic_zip(scenario)
                fake = Fake(scenario, raw=source)
                calls = []
                def opener(req, timeout):
                    calls.append((req.full_url, req.get_method(), req.headers.get("Range"),
                                  req.headers.get("If-range"), timeout))
                    return fake
                from unittest.mock import patch
                with patch.dict(
                    "research_runners.berlin_srhk_zip_first_tiff_header_v0.FIRST_512_SHA",
                    {scenario: sha256(source[:512]).hexdigest()}
                ):
                    out = probe(scenario, opener=opener,
                                clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
                self.assertEqual(calls, [(ROOT + OBJECTS[scenario][0], "GET",
                                          f"bytes=0-{READ_BYTES-1}", LAST_MODIFIED[scenario], TIMEOUT)])
                self.assertEqual(fake.read_calls, 1)
                self.assertEqual(out["projected_epsg_from_first_geokey"], 25833)
                self.assertTrue(out["original_get_status_206_verified"])

    def test_ignores_failed_http_range_without_reading_body(self):
        class Ignore(Fake):
            status = 200
        fake = Ignore("extreme")
        with self.assertRaisesRegex(TiffHeaderError, "refused"):
            probe("extreme", opener=lambda req, timeout: fake)
        self.assertEqual(fake.read_calls, 0)

    def test_http_content_range_mime_and_source_mtime_mismatch_blocks(self):
        for change in (
            {"Content-Range": "bytes 1-65536/619211977"},
            {"Content-Length": "619211977"},
            {"Content-Type": "text/html"},
            {"Content-Encoding": "gzip"},
            {"Last-Modified": "Thu, 01 Jan 1970 00:00:00 GMT"},
        ):
            with self.subTest(change=change), self.assertRaises(TiffHeaderError):
                validate_response({**headers(), **change}, scenario="extreme")

    def test_tiff_prefix_decompression_remains_bounded(self):
        raw = synthetic_zip(member_content=classic_tiff() + b"\x00"*(8*MAX_DECOMPRESSED_PREFIX))
        r = inspect_prefix(raw, scenario="extreme",
                           expected_512_sha=sha256(raw[:512]).hexdigest())
        self.assertLessEqual(r["decompressed_original_tiff_prefix_bytes"], MAX_DECOMPRESSED_PREFIX)
        self.assertTrue(r["decompression_output_cap_reached"])
        self.assertEqual(r["projected_epsg_from_first_geokey"], 25833)


if __name__ == "__main__":
    unittest.main()
