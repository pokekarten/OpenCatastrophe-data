# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic negative tests: no provider network calls or source bytes."""
from __future__ import annotations

import io
import json
import struct
import unittest
from unittest.mock import patch

from scripts import probe_esa_worldcover_tiff_header_v0 as wc
from scripts.parse_worldcover_geotiff_grid_v0 import GeoGridBlocked, inspect_geotiff_grid


def tiff_bytes() -> bytes:
    raw = bytearray(wc.BYTES)
    raw[:4] = bytes((73, 73, 42, 0))  # Little-endian classic TIFF.
    struct.pack_into("<I", raw, 4, 8)
    struct.pack_into("<H", raw, 8, 1)
    struct.pack_into("<HHII", raw, 10, 256, 4, 1, 34560)  # image width tag only.
    struct.pack_into("<I", raw, 22, 0)
    return bytes(raw)


def big_tiff_bytes() -> bytes:
    raw = bytearray(wc.BYTES)
    raw[:4] = bytes((73, 73, 43, 0))
    struct.pack_into("<HHQ", raw, 4, 8, 0, 16)
    struct.pack_into("<Q", raw, 16, 0)
    return bytes(raw)


class Response(io.BytesIO):
    def __init__(self, data=None, *, status=206, url=wc.URL, headers=None):
        super().__init__(tiff_bytes() if data is None else data)
        self.status = status
        self.url = url
        self.headers = {
            "Content-Type": "binary/octet-stream",
            "Content-Length": "4096",
            "Content-Range": wc.CONTENT_RANGE,
        } if headers is None else headers
        self.bytes_requested = []

    def geturl(self):
        return self.url

    def read(self, n=-1):
        self.bytes_requested.append(n)
        return super().read(n)


def geo_sample(*, epsg=4326, srcx=9.0, srcy=51.0, scale=None,
               key_location=0, out_of_range=False) -> bytes:
    """Synthetic, explicit 3x3 degree GeoTIFF metadata; no provider data."""
    raw = bytearray(tiff_bytes())
    # width, height, pixel scale, model tiepoint, GeoKey directory
    entries = [
        (256, 4, 1, 36000), (257, 4, 1, 36000),
        (33550, 12, 3, 800),
        (33922, 12, 6, 840),
        (34735, 3, 16, 900 if not out_of_range else 100000),
    ]
    struct.pack_into("<H", raw, 8, len(entries))
    for idx, item in enumerate(entries):
        struct.pack_into("<HHII", raw, 10 + idx * 12, *item)
    pix = 3 / 36000 if scale is None else scale
    struct.pack_into("<3d", raw, 800, pix, pix, 0.0)
    struct.pack_into("<6d", raw, 840, 0., 0., 0., srcx, srcy, 0.)
    keys = (1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, 1,
            2048, key_location, 1, epsg)
    struct.pack_into("<16H", raw, 900, *keys)
    return bytes(raw)


class WorldCoverRangeTests(unittest.TestCase):
    def test_real_checked_in_reviewed_contract(self):
        timeout, digest = wc.reviewed_contract()
        self.assertEqual(timeout, 60)
        self.assertEqual(len(digest), 64)

    def test_valid_exact_range_and_sample_hash_without_byte_leakage(self):
        calls = []
        response = Response()
        def mock_open(req, timeout):
            calls.append((req.full_url, req.get_method(),
                          req.get_header("Range"),
                          req.get_header("Accept-encoding"), timeout))
            return response
        rec = wc.probe(open_request=mock_open)
        self.assertEqual(calls, [(wc.URL, "GET", "bytes=0-4095", "identity", 60)])
        self.assertEqual(response.bytes_requested, [wc.BYTES + 1])
        self.assertEqual(rec["sample_bytes"], wc.BYTES)
        self.assertEqual(rec["tiff_flavour"], "TIFF")
        self.assertTrue(rec["first_ifd_fully_within_sample"])
        self.assertEqual(rec["first_ifd_count_if_visible"], 1)
        self.assertFalse(rec["full_original_sha256_verified"])
        self.assertFalse(rec["cog_layout_verified"])
        self.assertFalse(rec["crs_verified"])
        self.assertFalse(rec["raster_values_inspected"])
        self.assertFalse(rec["external_bytes_persisted"])
        self.assertFalse(rec["model_input_approved"])
        self.assertEqual(rec["image_width_if_inline"], 34560)
        self.assertIsNone(rec["image_length_if_inline"])
        self.assertFalse(rec["raster_dimensions_proven_by_header_only"])
        self.assertEqual(len(rec["sample_sha256"]), 64)

    def test_dimensions_and_geotiff_tag_id_presence_are_read_from_ifd_only(self):
        raw = bytearray(tiff_bytes())
        tags = [
            (256, 4, 1, 34560),  # image width, LONG
            (257, 4, 1, 34560),  # image height, LONG
            (259, 3, 1, 8),  # compression, SHORT
            (277, 3, 1, 1),  # samples per pixel, SHORT
            (322, 4, 1, 512),  # tile width
            (323, 4, 1, 512),  # tile height
            (34735, 3, 4, 5000),  # GeoKeyDirectoryTag offset OUTSIDE sample
        ]
        struct.pack_into("<H", raw, 8, len(tags))
        for index, tag in enumerate(tags):
            struct.pack_into("<HHII", raw, 10 + 12 * index, *tag)
        result = wc.inspect_tiff_header(bytes(raw))
        self.assertEqual(result["image_width_if_inline"], 34560)
        self.assertEqual(result["image_length_if_inline"], 34560)
        self.assertEqual(result["compression_code_if_inline"], 8)
        self.assertEqual(result["samples_per_pixel_if_inline"], 1)
        self.assertEqual(result["tile_width_if_inline"], 512)
        self.assertEqual(result["tile_length_if_inline"], 512)
        self.assertEqual(result["geotiff_ifd_tag_ids_present"], [34735])
        self.assertTrue(result["raster_dimensions_proven_by_header_only"])
        self.assertNotIn("EPSG", json.dumps(result))

    def test_duplicate_inline_tags_or_zero_width_are_rejected(self):
        raw = bytearray(tiff_bytes())
        struct.pack_into("<H", raw, 8, 2)
        struct.pack_into("<HHII", raw, 22, 256, 4, 1, 12345)
        with self.assertRaisesRegex(wc.HeaderBlocked, "duplicate"):
            wc.inspect_tiff_header(bytes(raw))
        raw = bytearray(tiff_bytes())
        struct.pack_into("<HHII", raw, 10, 256, 4, 1, 0)
        with self.assertRaisesRegex(wc.HeaderBlocked, "implausible"):
            wc.inspect_tiff_header(bytes(raw))

    def test_big_tiff_magic_and_ifd_range(self):
        sample = wc.inspect_tiff_header(big_tiff_bytes())
        self.assertEqual(sample["tiff_flavour"], "BigTIFF")
        self.assertTrue(sample["first_ifd_fully_within_sample"])
        self.assertEqual(sample["first_ifd_count_if_visible"], 0)

    def test_first_ifd_beyond_sample_remains_unknown(self):
        raw = bytearray(tiff_bytes())
        struct.pack_into("<I", raw, 4, wc.BYTES + 1024)
        sample = wc.inspect_tiff_header(bytes(raw))
        self.assertFalse(sample["first_ifd_fully_within_sample"])
        self.assertIsNone(sample["first_ifd_count_if_visible"])

    def test_geotiff_grid_exact_header_epsg4326_and_coordinates(self):
        raw = geo_sample()
        result = inspect_geotiff_grid(raw, width=36000, height=36000)
        self.assertEqual(result["geokey_geographic_crs_if_complete"], 4326)
        self.assertEqual(result["geokey_model_type_if_complete"], 2)
        self.assertEqual(result["geokey_raster_type_if_complete"], 1)
        self.assertEqual(result["header_tile_bounds_lonlat_if_verified"],
                         [9.0, 48.0, 12.0, 51.0])
        self.assertTrue(result["geo_grid_verified_from_prefix_only"])
        self.assertEqual(result["pixel_scale_degrees_if_complete"],
                         [3/36000, 3/36000])

    def test_wrong_crs_or_grid_extent_is_not_promoted(self):
        for raw in (geo_sample(epsg=3857), geo_sample(srcx=11.0),
                    geo_sample(srcy=50.0), geo_sample(scale=0.1),
                    geo_sample(out_of_range=True)):
            with self.subTest(sha=hash(raw)), self.assertFalse(
                inspect_geotiff_grid(raw, width=36000, height=36000)[
                    "geo_grid_verified_from_prefix_only"
                ]
            ):
                pass
        self.assertFalse(inspect_geotiff_grid(
            geo_sample(), width=35999, height=36000
        )["geo_grid_verified_from_prefix_only"])

    def test_geotiff_bad_references_and_nonfinite_block(self):
        with self.assertRaisesRegex(GeoGridBlocked, "not directly encoded"):
            inspect_geotiff_grid(geo_sample(key_location=34735),
                                 width=36000, height=36000)
        raw = bytearray(geo_sample())
        struct.pack_into("<d", raw, 800, float("nan"))
        with self.assertRaisesRegex(GeoGridBlocked, "invalid GeoTIFF pixel"):
            inspect_geotiff_grid(bytes(raw), width=36000, height=36000)
        raw = bytearray(geo_sample())
        # Add a second ModelPixelScale entry, as a provider ambiguity.
        struct.pack_into("<H", raw, 8, 6)
        struct.pack_into("<HHII", raw, 70, 33550, 12, 3, 800)
        with self.assertRaisesRegex(GeoGridBlocked, "duplicate GeoTIFF"):
            inspect_geotiff_grid(bytes(raw), width=36000, height=36000)

    def test_real_probe_receipt_will_not_certify_full_raster(self):
        response = Response(data=geo_sample())
        receipt = wc.probe(open_request=lambda req, timeout: response)
        self.assertTrue(receipt["geo_grid_verified_from_prefix_only"])
        self.assertFalse(receipt["crs_verified"])
        self.assertFalse(receipt["full_original_sha256_verified"])
        self.assertFalse(receipt["cog_layout_verified"])
        self.assertFalse(receipt["model_input_approved"])

    def test_reject_response_status_length_range_media_and_redirect(self):
        normal = {"Content-Type": "binary/octet-stream",
                  "Content-Length": "4096", "Content-Range": wc.CONTENT_RANGE}
        responses = [
            Response(status=200),  # Server ignored Range: never read full body.
            Response(status=403),
            Response(url="https://evil.invalid/other"),
            Response(headers={**normal, "Content-Length": "94851935"}),
            Response(headers={**normal, "Content-Range": "bytes 1-4096/94851935"}),
            Response(headers={**normal, "Content-Range": "bytes 0-4095/94851936"}),
            Response(headers={**normal, "Content-Type": "text/html"}),
            Response(headers={**normal, "Content-Encoding": "gzip"}),
            Response(data=b"wrong" * 100),
            Response(data=tiff_bytes() + b"x"),
        ]
        for response in responses:
            with self.subTest(status=response.status, headers=response.headers):
                with self.assertRaises(wc.HeaderBlocked):
                    wc.probe(open_request=lambda req, timeout: response)

    def test_wrong_tiff_magic_and_invalid_directory_blocked(self):
        invalid = [
            b"html" + bytes(wc.BYTES - 4),
            bytes(wc.BYTES),
            bytes((73, 73, 42, 0)) + bytes(wc.BYTES - 4),
        ]
        for data in invalid:
            with self.subTest(prefix=data[:8]), self.assertRaises(wc.HeaderBlocked):
                wc.inspect_tiff_header(data)

    def test_no_alternative_url_or_unreviewed_contract(self):
        with patch.object(wc, "URL", "https://different.invalid/other.tif"):
            with self.assertRaises(wc.HeaderBlocked):
                wc.reviewed_contract()

    def test_explicit_network_opt_in(self):
        with self.assertRaises(SystemExit) as e:
            wc.main([])
        self.assertNotEqual(e.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
