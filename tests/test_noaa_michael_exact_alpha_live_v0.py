# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully offline synthetic tests for NOAA TIFF per-block alpha, ranges, IFD."""

from __future__ import annotations

import io
import unittest
import urllib.error
import zlib

from research_runners.noaa_michael_exact_alpha_live_v0 import (
    SourceAlphaProbeError, TIFF_URL, fetch_range, measure_alpha,
)

W = 512
H = 512
SIZE = W * H * 4


def predicted_rgba(alpha_fn):
    """Build synthetic 8-bit RGBA and apply TIFF horizontal Predictor=2."""
    data = bytearray(SIZE)
    for y in range(H):
        for x in range(W):
            at = (y * W + x) * 4
            data[at] = x % 251
            data[at + 1] = y % 243
            data[at + 2] = (x + y) % 239
            data[at + 3] = alpha_fn(x, y)
    for y in range(H):
        for x in range(W - 1, 0, -1):
            at = (y * W + x) * 4
            for band in range(4):
                data[at + band] = (data[at + band] - data[at - 4 + band]) & 255
    return zlib.compress(data)


class FakeResponse(io.BytesIO):
    def __init__(self, source: bytes, *, start: int, total: int = 100_000,
                 status: int = 206, target_url: str = TIFF_URL,
                 etag: str = '"source-test-v1"', content_range: str | None = None):
        super().__init__(source)
        self.status = status
        self.target_url = target_url
        self.headers = {
            "ETag": etag,
            "Content-Range": content_range or
            f"bytes {start}-{start + len(source) - 1}/{total}",
        }

    def getcode(self):
        return self.status

    def geturl(self):
        return self.target_url


class NOAAOriginalAlphaLiveOfflineTests(unittest.TestCase):
    def test_all_zero_decoded_alpha_is_not_by_itself_image_admission(self):
        report = measure_alpha(zlib.compress(bytes(SIZE)))
        self.assertEqual(report["valid_pixels"], W * H)
        self.assertEqual(report["alpha_zero_pixels"], W * H)
        self.assertEqual(report["alpha_nonzero_pixels"], 0)
        self.assertIsNone(report["nonzero_alpha_pixel_extent_xy_in_block"])
        self.assertFalse(report["fema_point_on_visible_pixel_proven"])

    def test_predictor_two_restores_per_sample_alpha_row_boundaries(self):
        encoded = predicted_rgba(lambda x, y: 255 if x < 70 and y < 80 else 0)
        report = measure_alpha(encoded)
        self.assertEqual(report["alpha_nonzero_pixels"], 70 * 80)
        self.assertEqual(report["alpha_opaque_pixels"], 70 * 80)
        self.assertEqual(report["alpha_zero_pixels"], W * H - 70 * 80)
        self.assertEqual(report["nonzero_alpha_pixel_extent_xy_in_block"],
                         [0, 0, 69, 79])
        for key in ("full_image_alpha_mask_verified",
                    "fema_point_on_visible_pixel_proven", "model_input_admitted"):
            self.assertFalse(report[key])

    def test_partial_bottom_raster_tile_excludes_out_of_bounds_rows(self):
        # TIFF compressed edge blocks always decode 512 x 512, but the
        # source's final pixel-row has only 124 in-image rows.
        encoded = predicted_rgba(lambda x, y: 255 if y >= 124 else 0)
        report = measure_alpha(encoded, valid_width=512, valid_height=124)
        self.assertEqual(report["valid_pixels"], 512 * 124)
        self.assertEqual(report["alpha_nonzero_pixels"], 0)
        self.assertEqual(report["alpha_zero_pixels"], 512 * 124)

    def test_source_deflate_and_adler32_corruption_fail_closed(self):
        valid = zlib.compress(bytes(SIZE))
        for bad in (valid[:-1], valid + b"trailing", b"bad", valid[:-4] + b"\x00"*4):
            with self.subTest(length=len(bad)):
                with self.assertRaises(SourceAlphaProbeError):
                    measure_alpha(bad)
        too_many = zlib.compress(bytes(SIZE + 1))
        with self.assertRaisesRegex(SourceAlphaProbeError, "truncated, oversize"):
            measure_alpha(too_many)
        for invalid in (None, 0, -1, 512.0, True, 513):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(SourceAlphaProbeError):
                    measure_alpha(valid, valid_height=invalid)

    def test_exact_http206_byte_ranges_and_etag_are_mandatory(self):
        source = b"\x00\x01\x02\x03"
        calls = []
        def opener(req, *, timeout):
            calls.append(req)
            return FakeResponse(source, start=40)
        b, etag, total = fetch_range(40, 4, opener=opener)
        self.assertEqual(b, source)
        self.assertEqual(etag, '"source-test-v1"')
        self.assertEqual(total, 100_000)
        self.assertEqual(calls[0].headers["Range"], "bytes=40-43")
        self.assertEqual(calls[0].headers["Accept-encoding"], "identity")
        self.assertEqual(calls[0].full_url, TIFF_URL)

    def test_range_rejects_wrong_source_status_size_and_etag(self):
        source = b"\x00\x01\x02\x03"
        for kwargs in (
            {"status": 200},
            {"target_url": "https://other.invalid/tiff"},
            {"content_range": "bytes 39-42/100000"},
            {"content_range": "bytes 40-43/40"},
            {"etag": '"changed"'},
        ):
            with self.subTest(kwargs=kwargs):
                def opener(req, *, timeout):
                    return FakeResponse(source, start=40, **kwargs)
                with self.assertRaises(SourceAlphaProbeError):
                    fetch_range(40, 4, if_match='"source-test-v1"', opener=opener)

    def test_range_invalid_scope_and_response_bytes_fail(self):
        for start, size in ((-1, 3), (0, 0), (0, 1_048_577), (1_000_000_000, 1)):
            with self.subTest(start=start, size=size):
                with self.assertRaises(SourceAlphaProbeError):
                    fetch_range(start, size, opener=lambda **k: None)
        def opener(req, *, timeout):
            return FakeResponse(b"tiny", start=0)
        with self.assertRaisesRegex(SourceAlphaProbeError, "byte size mismatch"):
            fetch_range(0, 10, opener=opener)


if __name__ == "__main__":
    unittest.main()
