# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict TIFF first-IFD TileOffsets/TileByteCounts acquisition preflight.

Consumes only the previously verified 4096-byte WorldCover TIFF header.
Reports a hypothetical future bounded range for metadata tables; does NOT
fetch those ranges, assume the offsets/bytecounts are trusted, read a pixel,
resolve any generic URL, or approve an insurer CAT input.
"""
from __future__ import annotations

import struct

SOURCE_PREFIX_BYTES = 4096
ORIGINAL_OBJECT_BYTES = 94_851_935
GRID_PIXELS = 36_000
TILE_PIXELS = 1024
EXPECTED_BLOCK_AXIS = (GRID_PIXELS + TILE_PIXELS - 1) // TILE_PIXELS
EXPECTED_BLOCKS = EXPECTED_BLOCK_AXIS ** 2  # 36 x 36 = 1296
ENTRY_COUNT_BYTES = 2
IFD_ENTRY_BYTES = 12
MAX_IFD_ENTRIES = 256
TABLE_BYTES = EXPECTED_BLOCKS * 4


class TileTableBlocked(ValueError):
    """Cannot prove exact safe TIFF tile-array identity from bounded header."""


def inspect_tile_table_locations(raw: bytes, *, header: dict) -> dict:
    """For classic LE TIFF, identify exact out-of-line metadata table locations."""
    if type(raw) is not bytes or len(raw) != SOURCE_PREFIX_BYTES:
        raise TileTableBlocked("only the exact 4096-byte original source header is allowed")
    if raw[:4] != b"II*\x00" or header.get("tiff_flavour") != "TIFF":
        raise TileTableBlocked("only the reviewed classic little-endian TIFF is supported")
    expected_fields = {
        "byte_order": "little",
        "first_ifd_offset": 192,
        "first_ifd_count_if_visible": 21,
        "first_ifd_fully_within_sample": True,
        "image_width_if_inline": GRID_PIXELS,
        "image_length_if_inline": GRID_PIXELS,
        "tile_width_if_inline": TILE_PIXELS,
        "tile_length_if_inline": TILE_PIXELS,
        "samples_per_pixel_if_inline": 1,
        "compression_code_if_inline": 8,
    }
    for field, expected in expected_fields.items():
        if type(header.get(field)) is not type(expected) or header[field] != expected:
            raise TileTableBlocked("unreviewed or inconsistent TIFF first-IFD parameters")

    first_ifd = struct.unpack_from("<I", raw, 4)[0]
    if first_ifd != 192:
        raise TileTableBlocked("TIFF first-directory offset drift")
    count = struct.unpack_from("<H", raw, first_ifd)[0]
    if count != 21 or count > MAX_IFD_ENTRIES:
        raise TileTableBlocked("reviewed TIFF first-directory entry count drift")
    if first_ifd + ENTRY_COUNT_BYTES + count * IFD_ENTRY_BYTES + 4 > len(raw):
        raise TileTableBlocked("first TIFF directory incomplete in fixed sample")

    locations = {}
    for i in range(count):
        entry = first_ifd + ENTRY_COUNT_BYTES + i * IFD_ENTRY_BYTES
        tag, dtype, n, ptr = struct.unpack_from("<HHII", raw, entry)
        if tag not in (324, 325):
            continue
        if tag in locations:
            raise TileTableBlocked("duplicate tile offsets or bytecounts TIFF tag")
        if dtype != 4 or n != EXPECTED_BLOCKS:
            raise TileTableBlocked("tile table is not reviewed 1296-element LONG array")
        if not SOURCE_PREFIX_BYTES <= ptr <= ORIGINAL_OBJECT_BYTES - TABLE_BYTES:
            raise TileTableBlocked("tile-array address is unsafe or not a separate header range")
        if ptr % 2:
            raise TileTableBlocked("misaligned TIFF tile-array address")
        locations[tag] = (ptr, ptr + TABLE_BYTES - 1)

    if set(locations) != {324, 325}:
        raise TileTableBlocked("both TIFF TileOffsets and TileByteCounts tags are required")
    a, b = locations[324], locations[325]
    if not (a[1] < b[0] or b[1] < a[0]):
        raise TileTableBlocked("tile offset and bytecount metadata ranges overlap")
    return {
        "expected_tiff_blocks": EXPECTED_BLOCKS,
        "blocks_per_axis": EXPECTED_BLOCK_AXIS,
        "tile_table_entries_per_array": EXPECTED_BLOCKS,
        "table_type": "TIFF_LONG32",
        "table_bytes_each": TABLE_BYTES,
        "tile_offsets_table_original_byte_range": list(a),
        "tile_bytecounts_table_original_byte_range": list(b),
        "tile_offsets_validated": False,
        "individual_block_bytecounts_validated": False,
        "tile_pixels_downloaded": False,
        "table_original_bytes_downloaded": 0,
        "next_probe_requires_separate_review": True,
    }
