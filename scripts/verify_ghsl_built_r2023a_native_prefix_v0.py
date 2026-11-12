#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-source GHSL R2023A E2020 30ss original TIFF header gate.

Inspect only one previously acquired 32768-byte TIFF prefix. Verify immutable
original SHA-256; derive source TIFF/GeoTIFF/one native-block table metadata.
Never fetch network data, decompress pixel values, export provider bytes or
admit building exposures or CAT model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any

PROFILE = "oc-ghsl-r2023a-e2020-native-tiff-prefix-v0"
PREFIX_BYTES = 32768
IFD_OFFSET = 192
WIDTH, HEIGHT = 43201, 21384
TILE = 512
TILE_COUNT = 3570
PROBE_BLOCK = 809
KNOWN_TAGS = frozenset((
    256, 257, 258, 259, 262, 277, 284, 317, 322, 323,
    324, 325, 339, 33550, 33922, 34735, 34736, 34737, 42112,
))
PRODUCTS = {
    "surface": {
        "source_id": "ec-jrc.ghsl.ghs-built-s.r2023a",
        "prefix_sha256": "002c21c644073b889df87135a95c902eecf8859b572458a021341ae5c90b35ea",
        "first_4k_sha256": "fe98c0a0057657f973b85bb4e3f96ab610a3d702b842c973c09135bbc2490e78",
        "object_bytes": 173085842,
        "table_offsets_start": 2416,
        "table_counts_start": 16696,
        "native_block_offset": 73699060,
        "native_block_bytes": 523373,
        "unit": "square_metres_built_surface_per_cell",
        "scale": (0.00833333330032682, 0.008333333299795073),
        "origin": (-180.00124926466006, 89.0995831776456),
    },
    "volume": {
        "source_id": "ec-jrc.ghsl.ghs-built-v.r2023a",
        "prefix_sha256": "7e61b8056273ea0f2fa84913c3458da6d5c38f52f41881af20a42b0d966e76bd",
        "first_4k_sha256": "3be916bc8f2bf49cdcce38a73c44f70cca460384a6ff81dc42ca021d7c3c4038",
        "object_bytes": 187376914,
        "table_offsets_start": 2052,
        "table_counts_start": 16332,
        "native_block_offset": 80549811,
        "native_block_bytes": 570557,
        "unit": "cubic_metres_built_volume_per_cell",
        "scale": (0.008333333300325358, 0.008333333299793211),
        "origin": (-180.00124926466006, 89.09958317764332),
    },
}


class GHSLHeaderBlocked(ValueError):
    """Exact source metadata cannot be trusted for further scientific research."""


def _entry_values(prefix: bytes, entries: dict[int, tuple[int, int, int, int]],
                  tag: int) -> tuple[int | float, ...]:
    if tag not in entries:
        raise GHSLHeaderBlocked(f"required TIFF tag {tag} missing")
    typ, count, value, inline_offset = entries[tag]
    sizes = {1: 1, 3: 2, 4: 4, 12: 8}
    if typ not in sizes or count < 1 or count > TILE_COUNT:
        raise GHSLHeaderBlocked(f"unsupported TIFF tag {tag} type/count")
    length = count * sizes[typ]
    begin = inline_offset if length <= 4 else value
    if begin < 0 or length > PREFIX_BYTES or begin + length > PREFIX_BYTES:
        raise GHSLHeaderBlocked(f"TIFF tag {tag} requires bytes beyond reviewed prefix")
    fmt = {1: "B", 3: "H", 4: "I", 12: "d"}[typ]
    try:
        return struct.unpack_from("<" + fmt * count, prefix, begin)
    except struct.error as exc:
        raise GHSLHeaderBlocked(f"invalid source tag {tag} length") from exc


def inspect_tiff_prefix(prefix: bytes, product: str) -> dict[str, Any]:
    """Parse fixed TIFF and GeoTIFF metadata without relying on a source hash.

    This format parser is exposed separately for all-synthetic fixture tests.
    Scientific source provenance requires verify_original_tiff_prefix().
    """
    if product not in PRODUCTS:
        raise GHSLHeaderBlocked("unreviewed GHSL product")
    rule = PRODUCTS[product]
    if type(prefix) is not bytes or len(prefix) != PREFIX_BYTES:
        raise GHSLHeaderBlocked("expected exactly one 32KiB original source prefix")
    if prefix[:4] != b"II\x2a\x00" or struct.unpack_from("<I", prefix, 4)[0] != IFD_OFFSET:
        raise GHSLHeaderBlocked("not reviewed little-endian classic TIFF")
    n = struct.unpack_from("<H", prefix, IFD_OFFSET)[0]
    if n != 19 or IFD_OFFSET + 2 + 12*n + 4 > PREFIX_BYTES:
        raise GHSLHeaderBlocked("unexpected source IFD size/count")
    entries = {}
    for i in range(n):
        pos = IFD_OFFSET + 2 + 12*i
        tag, typ, count, val = struct.unpack_from("<HHII", prefix, pos)
        if tag in entries:
            raise GHSLHeaderBlocked("duplicate TIFF directory tag")
        entries[tag] = (typ, count, val, pos + 8)
    if set(entries) != KNOWN_TAGS:
        raise GHSLHeaderBlocked("original IFD tag identities changed")
    def scalar(tag: int, typ: int) -> int:
        if entries[tag][:2] != (typ, 1):
            raise GHSLHeaderBlocked(f"unexpected TIFF scalar tag type {tag}")
        return int(_entry_values(prefix, entries, tag)[0])
    exact = {
        # Original JRC GeoTIFF IFD stores dimensions and tile sizes as
        # TIFF SHORT (type 3), not LONG (type 4). These SHORT tags
        # describe the raster layout; individual raster values remain
        # unsigned 32-bit (BitsPerSample=32 and SampleFormat=1).
        256: (3, WIDTH), 257: (3, HEIGHT), 258: (3, 32),
        259: (3, 8), 262: (3, 1), 277: (3, 1),
        284: (3, 1), 317: (3, 1), 322: (3, TILE),
        323: (3, TILE), 339: (3, 1),
    }
    for tag, (typ, value) in exact.items():
        if scalar(tag, typ) != value:
            raise GHSLHeaderBlocked(f"original TIFF raster/coding tag {tag} drift")
    scales = _entry_values(prefix, entries, 33550)
    tie = _entry_values(prefix, entries, 33922)
    if (entries[33550][:2] != (12, 3) or entries[33922][:2] != (12, 6)
            or any(not math.isfinite(x) for x in (*scales, *tie))
            or not all(abs(scales[i] - rule["scale"][i]) < 1e-12 for i in range(2))
            or scales[2] != 0.0 or tie[:3] != (0.0, 0.0, 0.0)
            or not all(abs(tie[i + 3] - rule["origin"][i]) < 1e-9 for i in range(2))
            or tie[5] != 0.0):
        raise GHSLHeaderBlocked("original geographic pixel scale/tiepoint changed")
    keydir = _entry_values(prefix, entries, 34735)
    if (entries[34735][:2] != (3, 32)
            or keydir[:4] != (1, 1, 0, 7)):
        raise GHSLHeaderBlocked("original GeoTIFF geokey directory mismatch")
    keys = {}
    for i in range(4, len(keydir), 4):
        key, location, count, value = keydir[i:i+4]
        if key in keys:
            raise GHSLHeaderBlocked("duplicate GeoTIFF key")
        if location == 0 and count == 1:
            keys[key] = int(value)
    if (keys.get(1024) != 2 or keys.get(1025) != 1
            or keys.get(2048) != 4326 or keys.get(2054) != 9102):
        raise GHSLHeaderBlocked("not reviewed geographic EPSG:4326 PixelIsArea grid")

    table = {}
    for tag, offset in ((324, rule["table_offsets_start"]),
                        (325, rule["table_counts_start"])):
        if entries[tag][:3] != (4, TILE_COUNT, offset):
            raise GHSLHeaderBlocked(f"original TIFF block table {tag} moved")
        table[tag] = _entry_values(prefix, entries, tag)
    block_offset, block_size = table[324][PROBE_BLOCK], table[325][PROBE_BLOCK]
    if (block_offset != rule["native_block_offset"]
            or block_size != rule["native_block_bytes"]
            or block_offset + block_size > rule["object_bytes"]):
        raise GHSLHeaderBlocked("fixed original scientific block offset/size drift")
    return {
        "profile": PROFILE,
        "source_id": rule["source_id"],
        "product": product,
        "product_release": "R2023A",
        "product_epoch": 2020,
        "original_prefix_bytes_inspected": len(prefix),
        "classic_tiff_little_endian_ifd_verified": True,
        "tiff_dimensions": [WIDTH, HEIGHT],
        "tiff_compression": "deflate_code_8",
        "tiff_value_type": "unsigned_uint32",
        "tiff_tile_shape": [TILE, TILE],
        "tiff_tile_count": TILE_COUNT,
        "tiff_geographic_epsg_from_header_only": 4326,
        "tiff_pixel_scale_degrees": list(scales[:2]),
        "tiff_tiepoint_lon_lat": [tie[3], tie[4]],
        "fixed_source_block_index": PROBE_BLOCK,
        "fixed_source_block_offset": block_offset,
        "fixed_source_block_compressed_bytes": block_size,
        "source_semantic_unit_from_jrc_documentation": rule["unit"],
        "native_raster_cells_or_values_read": 0,
        "full_source_file_sha256_proven": False,
        "cog_layout_and_overviews_proven": False,
        "physical_building_identity_or_tiv_proven": False,
        "source_model_input_admitted": False,
    }


def verify_original_tiff_prefix(prefix: bytes, product: str) -> dict[str, Any]:
    """Accept only original source-specific prefixes captured and SHA-pinned."""
    summary = inspect_tiff_prefix(prefix, product)
    expected = PRODUCTS[product]
    first_hash = hashlib.sha256(prefix[:4096]).hexdigest()
    full_hash = hashlib.sha256(prefix).hexdigest()
    if (first_hash != expected["first_4k_sha256"]
            or full_hash != expected["prefix_sha256"]):
        raise GHSLHeaderBlocked("original provider SHA-256 prefix drift")
    return {
        **summary, "original_4096_sha256_verified": first_hash,
        "original_32768_sha256_verified": full_hash,
        "strict_exact_source_receipt_matched": True,
        "source_bytes_persisted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", choices=sorted(PRODUCTS), required=True)
    parser.add_argument("--input", type=Path, required=True,
                        help="private already acquired 32KiB original source prefix")
    args = parser.parse_args(argv)
    try:
        with args.input.open("rb") as stream:
            data = stream.read(PREFIX_BYTES + 1)
        result = verify_original_tiff_prefix(data, args.product)
    except (OSError, GHSLHeaderBlocked) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
