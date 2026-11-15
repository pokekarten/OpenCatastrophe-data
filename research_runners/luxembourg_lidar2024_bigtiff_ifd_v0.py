#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded BigTIFF IFD metadata from exact 2024 Luxembourg official COGs.

Only HTTP 206 4-KiB pages, max 16 pages per asset; no tile pixel data,
source raster export, source-independent building heights or CAT admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from research_runners.luxembourg_lidar2024_cog_range_capability_v0 import (
    OFFICIAL_BASE, FILES, MIN_TOTAL_BYTES, MAX_TOTAL_BYTES,
)

BLOCK = 4096
MAX_PAGES = 16
MAX_HEADER_OFFSET = 1024 * 1024
PIN_FIRST_PAGE_SHA256 = "c2bceb795e786013f8d235e3aa3fe5707e75faf6a6be39b2a3d7da67113161c8"
TYPES = {1: ("B", 1), 2: ("s", 1), 3: ("H", 2), 4: ("I", 4),
         5: ("II", 8), 6: ("b", 1), 7: ("B", 1), 8: ("h", 2),
         9: ("i", 4), 11: ("f", 4), 12: ("d", 8),
         16: ("Q", 8), 17: ("q", 8), 18: ("Q", 8)}
CONTENT_RANGE = re.compile(r"bytes ([0-9]+)-([0-9]+)/([1-9][0-9]*)\Z")


class MetadataBlockError(ValueError):
    """Stop when original source or bounded TIFF metadata are not reliable."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MetadataBlockError("Unreviewed network redirect")


class FixedAssetPages:
    """Strict exact-source 206 byte-range cache with hard total network cap."""

    def __init__(self, asset, opener=None, expected_first_sha=PIN_FIRST_PAGE_SHA256):
        if asset not in FILES:
            raise MetadataBlockError("Unreviewed official asset")
        self.asset = asset
        self.url = OFFICIAL_BASE + FILES[asset]
        self.opener = opener if opener is not None else build_opener(_NoRedirect())
        self.expected_first_sha = expected_first_sha
        self.pages = {}
        self.total = None

    def _page(self, num: int) -> bytes:
        if not isinstance(num, int) or num < 0 or num * BLOCK >= MAX_HEADER_OFFSET:
            raise MetadataBlockError("TIFF metadata pointer outside bounded header area")
        if num in self.pages:
            return self.pages[num]
        if len(self.pages) >= MAX_PAGES:
            raise MetadataBlockError("Remote metadata request budget exceeded")
        start = num * BLOCK
        end = start + BLOCK - 1
        request = Request(self.url, method="GET", headers={
            "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-LiDAR2024-BigTIFF-metadata/0",
        })
        try:
            with self.opener.open(request, timeout=20) as res:
                if res.getcode() != 206:
                    raise MetadataBlockError("Source ignored HTTP range; no body read")
                rng = res.info().get("Content-Range", "")
                match = CONTENT_RANGE.fullmatch(rng)
                if not match or int(match.group(1)) != start or int(match.group(2)) != end:
                    raise MetadataBlockError("Original byte position not verified")
                total = int(match.group(3))
                if not MIN_TOTAL_BYTES <= total <= MAX_TOTAL_BYTES:
                    raise MetadataBlockError("Original total size outside frozen bounds")
                if self.total is not None and total != self.total:
                    raise MetadataBlockError("Original resource total changed between requests")
                declared = res.info().get("Content-Length")
                if declared is not None and declared != str(BLOCK):
                    raise MetadataBlockError("Incorrect content-length for exact byte range")
                raw = res.read(BLOCK + 1)
                if len(raw) != BLOCK:
                    raise MetadataBlockError("Truncated or oversized source response")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise MetadataBlockError("Source metadata HTTP request failed") from exc
        if num == 0 and (self.expected_first_sha is not None and
                          hashlib.sha256(raw).hexdigest() != self.expected_first_sha):
            raise MetadataBlockError("Original 4KiB first-page SHA-256 drift")
        self.total = total
        self.pages[num] = raw
        return raw

    def read(self, offset: int, count: int) -> bytes:
        if (not isinstance(offset, int) or not isinstance(count, int) or
                offset < 0 or count < 1 or count > 8192 or
                offset + count > MAX_HEADER_OFFSET):
            raise MetadataBlockError("Unsafe TIFF metadata read span")
        out = bytearray()
        while count:
            page = offset // BLOCK
            data = self._page(page)
            index = offset % BLOCK
            part = min(count, BLOCK - index)
            out.extend(data[index:index + part])
            offset += part
            count -= part
        return bytes(out)


def _scalar(reader, tag_values, key: int, *, allowed_types=(3, 4, 16)):
    if key not in tag_values:
        raise MetadataBlockError("Required tiled TIFF tag missing")
    typ, count, value = tag_values[key]
    if typ not in allowed_types or count != 1:
        raise MetadataBlockError("Unexpected TIFF scalar tag type")
    return struct.unpack(reader.endian + TYPES[typ][0], value[:TYPES[typ][1]])[0]


def _payload(reader, tag_values, key, *, required=False, allowed=(3, 12, 2), max_items=128):
    if key not in tag_values:
        if required:
            raise MetadataBlockError("Required TIFF GeoKey/pixel scale missing")
        return None
    typ, cnt, value = tag_values[key]
    if typ not in allowed or not 1 <= cnt <= max_items:
        raise MetadataBlockError("Unsupported TIFF metadata array type/size")
    format_, width = TYPES[typ]
    nbytes = cnt * width
    payload = (value[:nbytes] if nbytes <= 8 else
               reader.read(struct.unpack(reader.endian + "Q", value)[0], nbytes))
    if typ == 2:
        try:
            return payload.rstrip(b"\x00").decode("ascii")
        except UnicodeDecodeError as exc:
            raise MetadataBlockError("Non-ASCII GeoTIFF text metadata") from exc
    return list(struct.unpack(reader.endian + (format_ * cnt), payload))


def inspect(asset: str, *, opener=None, expected_first_sha=PIN_FIRST_PAGE_SHA256) -> dict:
    reader = FixedAssetPages(asset, opener=opener, expected_first_sha=expected_first_sha)
    header = reader.read(0, 16)
    if header[:4] == b"II+\x00":
        reader.endian = "<"
    elif header[:4] == b"MM\x00+":
        reader.endian = ">"
    else:
        raise MetadataBlockError("Original is not a BigTIFF")
    if struct.unpack(reader.endian + "HH", header[4:8]) != (8, 0):
        raise MetadataBlockError("Unsupported BigTIFF offset size or reserved bits")
    ifd_offset = struct.unpack(reader.endian + "Q", header[8:16])[0]
    if ifd_offset < 16 or ifd_offset >= MAX_HEADER_OFFSET or ifd_offset % 2:
        raise MetadataBlockError("First IFD pointer invalid or outside fixed metadata budget")
    count = struct.unpack(reader.endian + "Q", reader.read(ifd_offset, 8))[0]
    if not 8 <= count <= 256:
        raise MetadataBlockError("Unexpected BigTIFF first IFD tag count")
    raw = reader.read(ifd_offset + 8, count * 20 + 8)
    tags = {}
    for i in range(count):
        start = i * 20
        tag, typ, values = struct.unpack(reader.endian + "HHQ", raw[start:start + 12])
        if tag in tags or typ not in TYPES or values > (1 << 36):
            raise MetadataBlockError("Duplicate TIFF tag or unsupported tag type")
        tags[tag] = (typ, values, raw[start + 12:start + 20])
    width = _scalar(reader, tags, 256)
    height = _scalar(reader, tags, 257)
    tile_w = _scalar(reader, tags, 322)
    tile_h = _scalar(reader, tags, 323)
    compression = _scalar(reader, tags, 259)
    bits = _scalar(reader, tags, 258)
    if 324 not in tags or 325 not in tags:
        raise MetadataBlockError("Source is not a tiled GeoTIFF")
    if not 1 <= width <= 1000000 or not 1 <= height <= 1000000:
        raise MetadataBlockError("Raster dimensions outside envelope")
    if not 16 <= tile_w <= 4096 or not 16 <= tile_h <= 4096:
        raise MetadataBlockError("Unreasonable internal TIFF tile shape")
    if bits not in (8, 16, 32, 64):
        raise MetadataBlockError("Unreviewed raster sample-bit size")
    expected_tiles = math.ceil(width / tile_w) * math.ceil(height / tile_h)
    if tags[324][1] != expected_tiles or tags[325][1] != expected_tiles:
        raise MetadataBlockError("Tile-offset and byte-count population inconsistent")
    scale = _payload(reader, tags, 33550, required=True, allowed=(12,), max_items=3)
    tiepoint = _payload(reader, tags, 33922, required=True, allowed=(12,), max_items=6)
    geokeys = _payload(reader, tags, 34735, required=True, allowed=(3,), max_items=128)
    if len(scale) != 3 or len(tiepoint) != 6 or len(geokeys) < 4:
        raise MetadataBlockError("Incomplete GeoTIFF coordinate metadata")
    if not all(math.isfinite(x) for x in scale + tiepoint) or not 0 < scale[0] <= 10 or not 0 < scale[1] <= 10:
        raise MetadataBlockError("Unsupported native raster pixel scale")
    if geokeys[0] != 1 or geokeys[3] * 4 + 4 != len(geokeys):
        raise MetadataBlockError("Invalid GeoTIFF key directory")
    epsg = None
    for i in range(4, len(geokeys), 4):
        key_id, tag_location, size, val = geokeys[i:i+4]
        if key_id == 3072 and tag_location == 0 and size == 1:
            epsg = val
    if epsg != 2169:
        raise MetadataBlockError("Original COG CRS is not declared EPSG:2169")
    if not 0 < expected_tiles <= 20000000:
        raise MetadataBlockError("Excessive raster tile population")
    # Fingerprint the *georeferencing grid* rather than exposing source tiepoint
    # coordinates. Equal digests across MNT/MNS indicate equal DECLARED grids
    # in the first IFD, not validated ground control or pixel-level heights.
    grid_sha256 = hashlib.sha256(json.dumps({
        "width": width, "height": height,
        "pixel_scale": scale, "tiepoint": tiepoint, "epsg": epsg,
    }, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    sample_format = (_scalar(reader, tags, 339)
                     if 339 in tags else None)
    if sample_format not in (None, 1, 2, 3):
        raise MetadataBlockError("Unreviewed sample format")
    return {
        "profile": "lu-lidar2024-cog-bigtiff-metadata-v0",
        "asset": asset, "source_full_bytes_from_http": reader.total,
        "first_4kiB_sha256_prior_match": expected_first_sha is not None,
        "raster_width_pixels": width, "raster_height_pixels": height,
        "internal_tile_width_pixels": tile_w, "internal_tile_height_pixels": tile_h,
        "internal_tile_count": expected_tiles,
        "bits_per_sample": bits, "tiff_compression_code": compression,
        "sample_format_code": sample_format,
        "declared_georeference_grid_sha256_only": grid_sha256,
        "declared_projected_epsg": epsg,
        "pixel_size_x_units": scale[0], "pixel_size_y_units": scale[1],
        "source_metadata_range_requests": len(reader.pages),
        "source_metadata_bytes_read": BLOCK * len(reader.pages),
        "max_per_asset_metadata_bytes": BLOCK * MAX_PAGES,
        "full_source_hash_verified": False,
        "raster_pixel_values_read": False,
        "source_height_values_computed": False,
        "coordinate_axis_and_vertical_datum_certified": False,
        "CAT_model_input_admitted": False,
        "original_source_bytes_persisted": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asset", choices=sorted(FILES), required=True)
    a = p.parse_args(argv)
    try:
        print(json.dumps(inspect(a.asset), sort_keys=True, indent=2, allow_nan=False))
    except (MetadataBlockError, OSError) as exc:
        p.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
