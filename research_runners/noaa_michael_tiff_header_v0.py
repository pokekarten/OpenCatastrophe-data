# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, offline first-4096-byte TIFF/GeoTIFF cross-check against NOAA STAC.

Inspects metadata only; never reads raster pixels or fetches network data.
The 4096-byte range does not establish the full file SHA-256, alpha coverage,
scene capture time, asset licence, building identity, or FEMA independence.
"""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Any

from research_runners.noaa_michael_stac_preflight_v0 import preflight as stac_preflight

_HEADER_LEN = 4096
_TYPE_SIZES = {2: 1, 3: 2, 4: 4, 12: 8}
_REQUIRED = (256, 257, 258, 259, 262, 277, 284, 322, 323, 324, 325, 338, 33550, 33922, 34735)
_MAX_TAGS = 96


class TIFFHeaderError(ValueError):
    """Incomplete or contradictory original image-header evidence."""


def _table(data: bytes) -> dict[int, tuple[int, int, int, int]]:
    if len(data) != _HEADER_LEN or data[:4] != b"II*\x00":
        raise TIFFHeaderError("expected exactly 4096 original little-endian classic TIFF header bytes")
    ifd = struct.unpack_from("<I", data, 4)[0]
    if not 8 <= ifd <= 256 or ifd + 2 > len(data):
        raise TIFFHeaderError("invalid TIFF first IFD pointer")
    n = struct.unpack_from("<H", data, ifd)[0]
    if not 1 <= n <= _MAX_TAGS or ifd + 2 + 12 * n + 4 > len(data):
        raise TIFFHeaderError("invalid TIFF tag directory bounds")
    tags = {}
    for i in range(n):
        offset = ifd + 2 + i * 12
        tag, typ, count, value = struct.unpack_from("<HHII", data, offset)
        if tag in tags or typ not in _TYPE_SIZES or not 1 <= count <= 1024:
            raise TIFFHeaderError("duplicate or unsupported TIFF tag/type/count")
        size = count * _TYPE_SIZES[typ]
        value_start = offset + 8 if size <= 4 else value
        if value_start < 0 or value_start + size > len(data):
            # Original header might legally refer to data outside the first
            # 4 KiB; it simply cannot meet this bounded proof contract.
            if tag in _REQUIRED:
                raise TIFFHeaderError("required TIFF metadata is outside the 4 KiB evidence")
        tags[tag] = (typ, count, value_start, size)
    for tag in _REQUIRED:
        if tag not in tags:
            raise TIFFHeaderError("required TIFF tag absent")
    return tags


def _vals(data: bytes, tags: dict, tag: int, expected_type: int) -> tuple[Any, ...]:
    typ, count, offset, size = tags[tag]
    if typ != expected_type or offset + size > len(data):
        raise TIFFHeaderError(f"TIFF tag {tag} unavailable or unexpected type")
    fmt = {3: "H", 4: "I", 12: "d"}[typ]
    return struct.unpack_from("<" + fmt * count, data, offset)


def _single(data: bytes, tags: dict, tag: int, typ: int) -> int:
    vals = _vals(data, tags, tag, typ)
    if len(vals) != 1:
        raise TIFFHeaderError(f"TIFF tag {tag} must contain one integer")
    return vals[0]


def preflight(header: Any, stac_item: Any) -> dict[str, Any]:
    """Compare exact TIFF header fields to an already constrained NOAA item."""
    if type(header) is not bytes:
        raise TIFFHeaderError("original TIFF 4096-byte range must be bytes")
    try:
        stac = stac_preflight(stac_item)
    except (ValueError, TypeError, KeyError) as exc:
        raise TIFFHeaderError("upstream STAC metadata failed its own gate") from exc
    tags = _table(header)
    width, height = _single(header, tags, 256, 3), _single(header, tags, 257, 3)
    if [height, width] != stac["raster_dimensions"]:
        raise TIFFHeaderError("original TIFF width/height differ from STAC projected shape")
    if (_vals(header, tags, 258, 3) != (8, 8, 8, 8)
        or _single(header, tags, 259, 3) != 8
        or _single(header, tags, 262, 3) != 2
        or _single(header, tags, 277, 3) != 4
        or _single(header, tags, 284, 3) != 1
        or _vals(header, tags, 338, 3) != (2,)):
        raise TIFFHeaderError("original TIFF RGB-alpha/DEFLATE profile differs from examined item")
    tw, th = _single(header, tags, 322, 3), _single(header, tags, 323, 3)
    if (tw, th) != (512, 512):
        raise TIFFHeaderError("unexpected original raster tile block dimensions")
    tiles = ((width + tw - 1) // tw) * ((height + th - 1) // th)
    offsets, sizes = _vals(header, tags, 324, 4), _vals(header, tags, 325, 4)
    if len(offsets) != tiles or len(sizes) != tiles or any(x < _HEADER_LEN for x in offsets) or any(x <= 0 for x in sizes):
        raise TIFFHeaderError("original TIFF offset/byte-count array does not match its tile grid")
    sx, sy, sz = _vals(header, tags, 33550, 12)
    px, py, pz, gx, gy, gz = _vals(header, tags, 33922, 12)
    if (not all(math.isfinite(v) for v in (sx, sy, sz, px, py, pz, gx, gy, gz))
        or not 0 < sx < 0.001 or not 0 < sy < 0.001
        or sz != 0 or (px, py, pz, gz) != (0, 0, 0, 0)):
        raise TIFFHeaderError("ambiguous model pixel scale or tiepoint")
    western, northern = gx, gy
    eastern, southern = gx + width * sx, gy - height * sy
    bbox = stac_item["bbox"]
    if any(abs(a - b) > 1e-4 for a, b in zip(
        (western, southern, eastern, northern), bbox
    )):
        raise TIFFHeaderError("original GeoTIFF pixel footprint does not match STAC bbox")
    geokeys = _vals(header, tags, 34735, 3)
    if len(geokeys) < 8 or geokeys[:3] != (1, 1, 0):
        raise TIFFHeaderError("GeoKey directory header invalid")
    nkeys = geokeys[3]
    if len(geokeys) != 4 + 4 * nkeys:
        raise TIFFHeaderError("GeoKey directory incomplete")
    crs = []
    for i in range(nkeys):
        key, loc, count, value = geokeys[4 + 4 * i:8 + 4 * i]
        if key == 2048 and loc == 0 and count == 1:
            crs.append(value)
    if crs != [4326]:
        raise TIFFHeaderError("original TIFF geographic EPSG code not 4326")

    return {
        "profile": "noaa_michael_2018_4k_tiff_source_header_v0",
        "tile_id_from_stac_only": stac["tile_id"],
        "range_bytes_read": _HEADER_LEN,
        "partial_header_sha256": hashlib.sha256(header).hexdigest(),
        "original_tiff_format_valid": True,
        "original_raster_and_georeference_match_stac": True,
        "raster_width_pixels": width,
        "raster_height_pixels": height,
        "block_size_pixels": [tw, th],
        "tile_block_count": tiles,
        "declared_crs": "EPSG:4326",
        "original_full_file_hash_verified": False,
        "asset_identity_bound_by_full_hash": False,
        "image_alpha_coverage_measured": False,
        "independent_fema_damage_validation_proven": False,
        "model_input_admitted": False,
    }
