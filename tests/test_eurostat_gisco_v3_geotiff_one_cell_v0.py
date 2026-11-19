# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only synthetic GeoTIFF and ZIP fixtures; zero original provider data."""
from __future__ import annotations

import hashlib
import struct
import unittest
import zlib

from research_runners.eurostat_gisco_v3_geotiff_one_cell_v0 import (
    BANDS, COL, HEIGHT, MEMBER, NODATA, ORIGINAL_RANGE_SHA256,
    REQUEST_RANGE_BYTES, ROW, SCANLINE_BYTES, SourceGateError,
    parse_original_tiff_prefix, parse_bounded_original_zip_range,
)

# This synthetic archive uses no real Eurostat population measurements.
SYNTHETIC_POPULATION_BANDS = (
    101, 50, 51, 20, 70, 11, 57, 90, 5, 6, 93, 6, 2, 1
)


def synthetic_tiff(*, srid=3035, nodata="-9999", names=BANDS,
                   pixel=SYNTHETIC_POPULATION_BANDS, break_strip=False):
    meta = ("<GDALMetadata>\n" + "".join(
        f'  <Item name="DESCRIPTION" sample="{i}" role="description">{name}</Item>\n'
        for i, name in enumerate(names)
    ) + "</GDALMetadata>\n").encode("utf-8")
    assert 100 <= len(meta) + 1 <= 1008

    pixel_values = bytearray(struct.pack("<i", NODATA) * (5700 * 14))
    struct.pack_into("<14i", pixel_values, COL * 14 * 4, *pixel)
    assert len(pixel_values) == SCANLINE_BYTES
    compressed_strip = zlib.compress(pixel_values)
    if break_strip:
        compressed_strip = compressed_strip[:-1] + bytes((compressed_strip[-1] ^ 0x01,))
    raw = bytearray(38_312 + len(compressed_strip))
    struct.pack_into("<2sHI", raw, 0, b"II", 42, 8)

    tags = (
        (256, 3, 1, 5700), (257, 3, 1, 4600), (258, 3, 14, 242),
        (259, 3, 1, 8), (262, 3, 1, 1), (273, 4, HEIGHT, 18670),
        (277, 3, 1, 14), (278, 3, 1, 1), (279, 4, HEIGHT, 270),
        (284, 3, 1, 1), (317, 3, 1, 1), (338, 3, 13, 37070),
        (339, 3, 14, 37096), (33550, 12, 3, 38132),
        (33922, 12, 6, 38156), (34735, 3, 32, 38204),
        (34737, 2, 38, 38268), (42112, 2, len(meta) + 1, 37124),
        (42113, 2, len(nodata) + 1, 38306),
    )
    assert len(tags) == 19
    struct.pack_into("<H", raw, 8, len(tags))
    for index, entry in enumerate(tags):
        struct.pack_into("<HHII", raw, 10 + 12 * index, *entry)
    struct.pack_into("<14H", raw, 242, *(32,) * 14)
    struct.pack_into("<I", raw, 270 + ROW * 4, len(compressed_strip))
    struct.pack_into("<I", raw, 18670 + ROW * 4, 38312)
    struct.pack_into("<13H", raw, 37070, *(0,) * 13)
    struct.pack_into("<14H", raw, 37096, *(2,) * 14)
    raw[37124:37124 + len(meta)] = meta
    raw[37124 + len(meta)] = 0
    struct.pack_into("<3d", raw, 38132, 1000, 1000, 0)
    struct.pack_into("<6d", raw, 38156, 0, 0, 0, 900000, 5500000, 0)
    keys = (
        1, 1, 0, 7,
        1024, 0, 1, 1,
        1025, 0, 1, 1,
        1026, 34737, 30, 0,
        2049, 34737, 7, 30,
        2054, 0, 1, 9102,
        3072, 0, 1, srid,
        3076, 0, 1, 9001,
    )
    assert len(keys) == 32
    struct.pack_into("<32H", raw, 38204, *keys)
    raw[38268:38268 + 38] = b"ETRS89-extended / LAEA Europe|ETRS89|" + bytes((0,))
    raw[38306:38306 + len(nodata) + 1] = nodata.encode("ascii") + b"\0"
    raw[38312:38312 + len(compressed_strip)] = compressed_strip
    return bytes(raw)


def synthetic_bounded_zip_range(tiff):
    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(tiff) + compressor.flush()
    name = MEMBER.encode("utf-8")
    header = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, 8,
                         0, 0, 0, 0, 0, len(name), 0)
    data = header + name + compressed
    assert len(data) <= REQUEST_RANGE_BYTES
    # Padding imitates one bounded byte-range; it is NOT the full provider ZIP.
    return data.ljust(REQUEST_RANGE_BYTES, b"\0")


class OriginalCensusRasterPixelTests(unittest.TestCase):
    def test_synthetic_14_band_1km_pixel_with_verified_native_tiff(self):
        receipt = parse_original_tiff_prefix(synthetic_tiff())
        self.assertEqual(receipt["source_crs"], "EPSG:3035")
        self.assertEqual(receipt["cell_center_epsg3035_x_m"], 5018500)
        self.assertEqual(receipt["cell_center_epsg3035_y_m"], 5399500)
        self.assertEqual(receipt["census_band_values"]["T"], 101)
        self.assertEqual(receipt["census_band_values"]["M"], 50)
        self.assertEqual(receipt["census_band_values"]["F"], 51)
        self.assertTrue(receipt["source_strip_zlib_adler_verified"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertFalse(receipt["whole_archive_sha256_verified"])

    def test_synthetic_zip_source_binding_and_no_full_archive_claim(self):
        raw = synthetic_bounded_zip_range(synthetic_tiff())
        sha = hashlib.sha256(raw).hexdigest()
        self.assertNotEqual(sha, ORIGINAL_RANGE_SHA256)
        receipt = parse_bounded_original_zip_range(raw, sha)
        self.assertEqual(receipt["original_range_sha256"], sha)
        self.assertEqual(receipt["original_range_bytes"], REQUEST_RANGE_BYTES)
        self.assertEqual(receipt["source_nodata"], -9999)
        self.assertFalse(receipt["source_bytes_persisted_by_runner"])
        self.assertFalse(receipt["commercial_underwriting_authorized"])

    def test_wrong_original_range_hash_and_size_are_blocked(self):
        raw = synthetic_bounded_zip_range(synthetic_tiff())
        with self.assertRaisesRegex(SourceGateError, "SHA mismatch"):
            parse_bounded_original_zip_range(raw, ORIGINAL_RANGE_SHA256)
        with self.assertRaisesRegex(SourceGateError, "exactly 49152"):
            parse_bounded_original_zip_range(raw[:-1], hashlib.sha256(raw[:-1]).hexdigest())

    def test_wrong_epsg_nodata_band_map_and_bad_strip_block(self):
        for args in (
            {"srid": 4326}, {"nodata": "-8888"},
            {"names": ("X",) + BANDS[1:]},
            {"pixel": (NODATA,) + SYNTHETIC_POPULATION_BANDS[1:]},
            {"break_strip": True},
        ):
            with self.subTest(args=args):
                with self.assertRaises(SourceGateError):
                    parse_original_tiff_prefix(synthetic_tiff(**args))

    def test_unavailable_and_unaligned_cell_block(self):
        raw = synthetic_tiff()
        with self.assertRaises(SourceGateError):
            parse_original_tiff_prefix(raw, row=-1)
        with self.assertRaises(SourceGateError):
            parse_original_tiff_prefix(raw, col=5700)
        with self.assertRaises(SourceGateError):
            parse_original_tiff_prefix(raw, row=0)


if __name__ == "__main__":
    unittest.main()
