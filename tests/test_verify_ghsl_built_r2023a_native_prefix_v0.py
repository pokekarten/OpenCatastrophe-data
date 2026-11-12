# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic GHSL TIFF header identity/geo/block-table regression tests."""
from __future__ import annotations

import math
import struct
import unittest

from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import (
    GHSLHeaderBlocked, IFD_OFFSET, KNOWN_TAGS, PREFIX_BYTES,
    PRODUCTS, PROBE_BLOCK, TILE_COUNT, inspect_tiff_prefix,
    verify_original_tiff_prefix,
)


def synthetic_header(product: str = "surface") -> bytes:
    """Not original provider bytes; build the exact supported header shape."""
    p = PRODUCTS[product]
    data = bytearray(PREFIX_BYTES)
    data[:4] = b"II\x2a\x00"
    struct.pack_into("<I", data, 4, IFD_OFFSET)
    struct.pack_into("<H", data, IFD_OFFSET, len(KNOWN_TAGS))
    off = 500
    # Matches the observed original JRC IFD: even the 43,201-wide
    # image dimensions and 512-pixel tile sizes use TIFF SHORT.
    # UInt32 scientific values are separate from IFD field encoding.
    short = {
        256: 43201, 257: 21384, 258: 32, 259: 8, 262: 1,
        277: 1, 284: 1, 317: 1, 322: 512, 323: 512, 339: 1,
    }
    tags = {tag: (3, 1, val) for tag, val in short.items()}
    tags[33550] = (12, 3, off)
    struct.pack_into("<ddd", data, off, *p["scale"], 0.)
    off += 32
    tags[33922] = (12, 6, off)
    struct.pack_into("<dddddd", data, off, 0., 0., 0., *p["origin"], 0.)
    off += 64
    tags[34735] = (3, 32, off)
    # 7 required/auxiliary GeoTIFF keys.
    geo = (1, 1, 0, 7,
           1024, 0, 1, 2,
           1025, 0, 1, 1,
           2048, 0, 1, 4326,
           2049, 34737, 7, 0,
           2054, 0, 1, 9102,
           2057, 34736, 1, 0,
           2059, 34736, 1, 1)
    struct.pack_into("<" + "H"*32, data, off, *geo)
    off += 80
    tags[34736] = (12, 2, off)
    struct.pack_into("<dd", data, off, 6378137., 298.257223563)
    off += 24
    tags[34737] = (2, 7, off)
    data[off:off+7] = b"WGS84|\x00"
    tags[324] = (4, TILE_COUNT, p["table_offsets_start"])
    tags[325] = (4, TILE_COUNT, p["table_counts_start"])
    tags[42112] = (2, 1, ord("G"))
    struct.pack_into("<I", data, p["table_offsets_start"] + PROBE_BLOCK*4,
                     p["native_block_offset"])
    struct.pack_into("<I", data, p["table_counts_start"] + PROBE_BLOCK*4,
                     p["native_block_bytes"])
    self_entries = sorted(tags.items())
    assert len(self_entries) == 19
    for i, (tag, (typ, count, value)) in enumerate(self_entries):
        struct.pack_into("<HHII", data, IFD_OFFSET + 2 + 12*i,
                         tag, typ, count, value)
    return bytes(data)


class GHSLBuiltNativePrefixTests(unittest.TestCase):
    def test_synthetic_both_products_header_geometry_and_units(self):
        for p in PRODUCTS:
            with self.subTest(product=p):
                res = inspect_tiff_prefix(synthetic_header(p), p)
                self.assertEqual(res["source_id"], PRODUCTS[p]["source_id"])
                self.assertEqual(res["tiff_dimensions"], [43201, 21384])
                self.assertEqual(res["tiff_tile_count"], TILE_COUNT)
                self.assertEqual(res["tiff_geographic_epsg_from_header_only"], 4326)
                self.assertEqual(res["fixed_source_block_index"], PROBE_BLOCK)
                self.assertEqual(res["fixed_source_block_compressed_bytes"],
                                 PRODUCTS[p]["native_block_bytes"])
                self.assertEqual(res["native_raster_cells_or_values_read"], 0)
                self.assertFalse(res["source_model_input_admitted"])

    def test_unpinned_fabricated_tiff_not_original_provenance(self):
        for p in PRODUCTS:
            with self.subTest(product=p):
                with self.assertRaisesRegex(GHSLHeaderBlocked, "SHA-256"):
                    verify_original_tiff_prefix(synthetic_header(p), p)

    def test_wrong_product_crosscheck_and_bad_prefix_length(self):
        for p in PRODUCTS:
            other = "volume" if p == "surface" else "surface"
            with self.subTest(product=p):
                with self.assertRaises(GHSLHeaderBlocked):
                    inspect_tiff_prefix(synthetic_header(p), other)
                for raw in (synthetic_header(p)[:-1], synthetic_header(p)+b"X"):
                    with self.assertRaisesRegex(GHSLHeaderBlocked, "32KiB"):
                        inspect_tiff_prefix(raw, p)
        with self.assertRaises(GHSLHeaderBlocked):
            inspect_tiff_prefix(synthetic_header(), "other")

    def test_wrong_tiff_magic_compression_dtype_crs_and_tile_block_fail_closed(self):
        base = synthetic_header()
        # Tags are in monotonically increasing order in fabricated directory.
        idx = {tag: i for i, tag in enumerate(sorted(KNOWN_TAGS))}
        changes = [
            ("magic", 0, "bytes", b"XX"),
            ("compression", IFD_OFFSET+2+12*idx[259]+8, "short", 1),
            ("bits", IFD_OFFSET+2+12*idx[258]+8, "short", 16),
            ("dtype", IFD_OFFSET+2+12*idx[339]+8, "short", 3),
            ("epsg", 500+32+64+8+8+2, "short", 3857),
            ("offset", PRODUCTS["surface"]["table_offsets_start"]+PROBE_BLOCK*4, "long", 9),
            ("bytes", PRODUCTS["surface"]["table_counts_start"]+PROBE_BLOCK*4, "long", 0),
        ]
        for label, pos, typ, value in changes:
            with self.subTest(label=label):
                data = bytearray(base)
                if typ == "bytes":
                    data[pos:pos+2] = value
                else:
                    struct.pack_into("<H" if typ == "short" else "<I", data, pos, value)
                with self.assertRaises(GHSLHeaderBlocked):
                    inspect_tiff_prefix(bytes(data), "surface")

    def test_original_short_dimensions_and_tile_tag_types_are_required(self):
        doc = synthetic_header("surface")
        tags = sorted(KNOWN_TAGS)
        for tag in (256, 257, 322, 323):
            with self.subTest(tag=tag):
                # A synthetic TIFF LONG field with the same visible numeric
                # value is *not* the reviewed original source schema.
                changed = bytearray(doc)
                struct.pack_into("<H", changed, IFD_OFFSET+2+12*tags.index(tag)+2, 4)
                with self.assertRaisesRegex(GHSLHeaderBlocked, "scalar tag type"):
                    inspect_tiff_prefix(bytes(changed), "surface")

    def test_nonfinite_coordinate_and_corrupt_directory_rejected(self):
        base = synthetic_header()
        for modify in (
            lambda b: struct.pack_into("<d", b, 500, float("nan")),
            lambda b: struct.pack_into("<d", b, 532, float("inf")),
            lambda b: struct.pack_into("<H", b, IFD_OFFSET, 700),
        ):
            data = bytearray(base)
            modify(data)
            with self.assertRaises(GHSLHeaderBlocked):
                inspect_tiff_prefix(bytes(data), "surface")


if __name__ == "__main__":
    unittest.main()
