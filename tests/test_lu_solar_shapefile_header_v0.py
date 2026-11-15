# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only solar cadastre Shapefile/DBF prefix contract tests."""
from __future__ import annotations

import json
import struct
import unittest

from research_runners.lu_solar_shapefile_header_v0 import (
    HeaderGateError, inspect, parse_dbf_header, parse_shp_header,
)


def shp_header(kind="SHP", rows=3, shape=5):
    raw = bytearray(100)
    struct.pack_into(">i", raw, 0, 9994)
    struct.pack_into(">i", raw, 24, (100 + (rows * 8 if kind == "SHX" else 300)) // 2)
    struct.pack_into("<i", raw, 28, 1000)
    struct.pack_into("<i", raw, 32, shape)
    struct.pack_into("<dddd", raw, 36, 75000.0, 75000.0, 90000.0, 85000.0)
    return bytes(raw)


def dbf_header(fields=(("hid", "C", 11), ("pv", "N", 4)), rows=3):
    head_len = 33 + len(fields) * 32
    row_len = 1 + sum(f[2] for f in fields)
    raw = bytearray(head_len)
    raw[0:4] = b"\x03\x7e\x0a\x01"
    struct.pack_into("<I", raw, 4, rows)
    struct.pack_into("<H", raw, 8, head_len)
    struct.pack_into("<H", raw, 10, row_len)
    for i, (name, kind, width) in enumerate(fields):
        pos = 32 + i * 32
        raw[pos:pos + len(name)] = name.encode("ascii")
        raw[pos + 11] = ord(kind)
        raw[pos + 16] = width
    raw[-1] = 13
    return bytes(raw)


class SolarHeadersTests(unittest.TestCase):
    def test_valid_triplet(self):
        report = inspect(dbf_header(), shp_header(), shp_header("SHX"))
        self.assertEqual(report["shapefile_record_count_unverified_against_bodies"], 3)
        self.assertTrue(report["direct_buildings_shp_field_presence"]["hid"])
        self.assertFalse(report["direct_buildings_shp_field_presence"]["tilt"])
        self.assertFalse(report["field_values_or_original_polygon_geometries_read"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("SYNTHETIC PRIVATE HOUSE", json.dumps(report))

    def test_facets_only_if_in_original_table(self):
        report = inspect(
            dbf_header((("hid", "C", 11), ("tilt", "N", 4), ("aspect", "N", 5))),
            shp_header(), shp_header("SHX"),
        )
        self.assertTrue(report["direct_buildings_shp_field_presence"]["tilt"])
        self.assertTrue(report["direct_buildings_shp_field_presence"]["aspect"])

    def test_no_false_record_count(self):
        with self.assertRaisesRegex(HeaderGateError, "record count"):
            inspect(dbf_header(rows=8), shp_header(), shp_header("SHX"))

    def test_duplicate_case_insensitive_columns_block(self):
        with self.assertRaisesRegex(HeaderGateError, "Duplicate"):
            parse_dbf_header(dbf_header((("hid", "C", 5), ("HID", "C", 6))))

    def test_invalid_dbf_physical_width(self):
        raw = bytearray(dbf_header())
        raw[10] = 1
        with self.assertRaisesRegex(HeaderGateError, "row size"):
            parse_dbf_header(bytes(raw))

    def test_invalid_dbf_field_terminator(self):
        raw = bytearray(dbf_header())
        raw[-1] = 0
        with self.assertRaisesRegex(HeaderGateError, "terminator"):
            parse_dbf_header(bytes(raw))

    def test_oversized_dbf_header_prefix_blocks(self):
        raw = bytearray(dbf_header())
        struct.pack_into("<H", raw, 8, 9000)
        with self.assertRaisesRegex(HeaderGateError, "length"):
            parse_dbf_header(bytes(raw))

    def test_nonpolygon_rejected(self):
        with self.assertRaisesRegex(HeaderGateError, "Polygon"):
            parse_shp_header(shp_header(shape=1), "SHP")

    def test_bad_shp_reserved_bytes(self):
        raw = bytearray(shp_header())
        raw[8] = 1
        with self.assertRaisesRegex(HeaderGateError, "reserved"):
            parse_shp_header(bytes(raw), "SHP")

    def test_invalid_bbox_blocks(self):
        raw = bytearray(shp_header())
        struct.pack_into("<dddd", raw, 36, 80000.0, 80000.0, 70000.0, 90000.0)
        with self.assertRaisesRegex(HeaderGateError, "bbox"):
            parse_shp_header(bytes(raw), "SHP")

    def test_shp_shx_shape_mismatch(self):
        with self.assertRaisesRegex(HeaderGateError, "disagree"):
            inspect(dbf_header(), shp_header(shape=5), shp_header("SHX", shape=15))


if __name__ == "__main__":
    unittest.main()
