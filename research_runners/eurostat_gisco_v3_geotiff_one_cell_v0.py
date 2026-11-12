#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only original Eurostat Census 2021 V3 GeoTIFF one-pixel preflight.

Source is EXACT 49152-byte original HTTP Range beginning at the TIFF member
local ZIP header within the fixed V3 ZIP. SHA-256 is of this RANGE ONLY, never
of the whole ZIP/TIFF. No internet, original provider bytes or private data
written by this runner. Only one 1-km population grid cell and metadata leave
the process; source-science and CAT/underwriting admission remain false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib
from xml.etree import ElementTree

SOURCE_ID = "eurostat.gisco.census-population-grid.2021"
ORIGINAL_ARCHIVE = (
    "https://gisco-services.ec.europa.eu/census/2021/"
    "Eurostat_Census-GRID_2021_V3.zip"
)
MEMBER = "Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.tiff"
ZIP_HEADER_ABSOLUTE_OFFSET = 535_021_482
REQUEST_RANGE_BYTES = 49_152
RANGE_SPEC = "bytes=535021482-535070633"
ORIGINAL_RANGE_SHA256 = (
    "80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155"
)
ROW = 100
COL = 4118
WIDTH = 5700
HEIGHT = 4600
BANDS = (
    "T", "M", "F", "Y_LT15", "Y_1564", "Y_GE65", "EMP",
    "NAT", "EU_OTH", "OTH", "SAME", "CHG_IN", "CHG_OUT", "POPULATED",
)
SCANLINE_BYTES = WIDTH * len(BANDS) * 4
MAX_TIFF_PREFIX_BYTES = 250_000
MAX_STRIP_COMPRESSED_BYTES = 8_192
PIXEL_METRES = 1000
NODATA = -9999


class SourceGateError(ValueError):
    """Original source identity / shape / scientific meaning not verified."""


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise SourceGateError(message)


def _span(body: bytes, offset: int, size: int) -> bytes:
    _require(0 <= offset <= len(body) and 0 <= size <= len(body) - offset,
             "source prefix does not contain the referenced metadata or strip")
    return body[offset:offset + size]


def _u16(body: bytes, offset: int) -> int:
    return struct.unpack("<H", _span(body, offset, 2))[0]


def _u32(body: bytes, offset: int) -> int:
    return struct.unpack("<I", _span(body, offset, 4))[0]


def _read_tiff_tags(raw: bytes) -> dict[int, tuple[int, int, int]]:
    _require(raw[:4] == b"II*\\x00".replace(b"\\x00", b"\x00"),
             "expected little-endian classic TIFF")
    start = _u32(raw, 4)
    _require(start == 8, "unexpected first TIFF IFD offset")
    entries = _u16(raw, start)
    _require(15 <= entries <= 40, "unexpected original IFD tag count")
    tags = {}
    for i in range(entries):
        tag, kind, count, value = struct.unpack(
            "<HHII", _span(raw, start + 2 + 12 * i, 12)
        )
        _require(tag not in tags, "duplicate TIFF tag")
        tags[tag] = (kind, count, value)
    return tags


def parse_original_tiff_prefix(tiff: bytes, row: int = ROW, col: int = COL) -> dict:
    """Decode one truly complete 14-band population cell; check zlib/Adler."""
    _require(isinstance(tiff, bytes) and 38_400 <= len(tiff) <= MAX_TIFF_PREFIX_BYTES,
             "original TIFF decompressed prefix is missing or too large")
    tags = _read_tiff_tags(tiff)

    def tag(index: int, kind: int, count: int) -> int:
        _require(index in tags, "required GeoTIFF tag missing")
        actual = tags[index]
        _require(actual[:2] == (kind, count), "GeoTIFF tag type/count drift")
        return actual[2]

    _require(tag(256, 3, 1) == WIDTH and tag(257, 3, 1) == HEIGHT,
             "2021 V3 grid width/height drift")
    _require(tag(259, 3, 1) == 8 and tag(277, 3, 1) == len(BANDS),
             "source TIFF must be DEFLATE-compressed 14-band raster")
    _require(tag(278, 3, 1) == 1 and tag(284, 3, 1) == 1,
             "expected one scanline per strip and pixel-interleaved bands")
    _require(tag(317, 3, 1) == 1, "unexpected TIFF predictor")

    bits = struct.unpack("<14H", _span(tiff, tag(258, 3, 14), 28))
    sample_formats = struct.unpack("<14H", _span(tiff, tag(339, 3, 14), 28))
    _require(bits == (32,) * 14 and sample_formats == (2,) * 14,
             "all 14 data bands must be signed 32-bit integer")
    _require(0 <= row < HEIGHT and 0 <= col < WIDTH,
             "out-of-range source cell index")
    offset_table = tag(273, 4, HEIGHT)
    bytecount_table = tag(279, 4, HEIGHT)
    strip_offset = _u32(tiff, offset_table + 4 * row)
    strip_length = _u32(tiff, bytecount_table + 4 * row)
    _require(6 <= strip_length <= MAX_STRIP_COMPRESSED_BYTES,
             "scanline strip is absent or too large")
    strip = _span(tiff, strip_offset, strip_length)

    scale = struct.unpack("<3d", _span(tiff, tag(33550, 12, 3), 24))
    tie = struct.unpack("<6d", _span(tiff, tag(33922, 12, 6), 48))
    _require(scale == (1000.0, 1000.0, 0.0)
             and tie == (0.0, 0.0, 0.0, 900000.0, 5500000.0, 0.0),
             "unexpected CRS affine transform")

    geokey_size = tags[34735][1] if 34735 in tags else -1
    _require(8 <= geokey_size <= 64 and tags[34735][0] == 3,
             "invalid GeoKey directory")
    keys = struct.unpack("<" + "H" * geokey_size,
                         _span(tiff, tags[34735][2], 2 * geokey_size))
    count = keys[3]
    _require(keys[:3] == (1, 1, 0) and geokey_size == 4 + 4 * count,
             "malformed GeoKey directory")
    srid = {
        keys[4 + 4 * i]: (keys[5 + 4 * i], keys[6 + 4 * i], keys[7 + 4 * i])
        for i in range(count)
    }.get(3072)
    _require(srid == (0, 1, 3035), "must be projected EPSG:3035")

    nodata = _span(tiff, tag(42113, 2, 6), 6)
    _require(nodata == b"-9999\x00", "NoData value changed")
    meta_value = tags.get(42112)
    _require(meta_value is not None and meta_value[0] == 2
             and 100 <= meta_value[1] <= 4096, "GDAL metadata missing")
    text = _span(tiff, meta_value[2], meta_value[1]).rstrip(b"\x00")
    try:
        xml = ElementTree.fromstring(text.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, ElementTree.ParseError) as exc:
        raise SourceGateError("GDAL band names malformed") from exc
    band_labels = [
        (int(node.get("sample", "-1")), node.text)
        for node in xml.findall("Item")
        if node.get("name") == "DESCRIPTION"
    ]
    _require(band_labels == list(enumerate(BANDS)), "unexpected GDAL bands")

    # zlib wrapper verifies source Adler-32, unlike header-only/partial scans.
    decoder = zlib.decompressobj(wbits=15)
    try:
        scanline = decoder.decompress(strip, SCANLINE_BYTES + 1)
        scanline += decoder.flush()
    except zlib.error as exc:
        raise SourceGateError("original source strip failed zlib CRC/Adler check") from exc
    _require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
             and len(scanline) == SCANLINE_BYTES,
             "source strip did not inflate to a complete 14-band raster row")
    values = struct.unpack_from("<14i", scanline, col * 14 * 4)
    result = dict(zip(BANDS, values))
    _require(0 < result["T"] < 2_000_000 and result["POPULATED"] == 1,
             "source-selected raster pixel does not have population")
    _require(all(value >= 0 or value in (-8888, -9999)
                 for value in values[:-1]), "invalid census disclosure sentinel")
    return {
        "source_id": SOURCE_ID,
        "product_version": "Eurostat_Census-GRID_2021_V3",
        "row_zero_based": row,
        "col_zero_based": col,
        "cell_center_epsg3035_x_m": tie[3] + (col + 0.5) * scale[0],
        "cell_center_epsg3035_y_m": tie[4] - (row + 0.5) * scale[1],
        "source_crs": "EPSG:3035",
        "resolution_metres": PIXEL_METRES,
        "source_nodata": NODATA,
        "census_band_values": result,
        "source_strip_zlib_adler_verified": True,
        "source_strip_bytes": strip_length,
        "read_only_single_aggregate_cell": True,
        "whole_archive_sha256_verified": False,
        "model_input_approved": False,
    }


def parse_bounded_original_zip_range(
    data: bytes,
    expected_sha256: str = ORIGINAL_RANGE_SHA256,
    row: int = ROW,
    col: int = COL,
) -> dict:
    _require(isinstance(data, bytes) and len(data) == REQUEST_RANGE_BYTES,
             "bounded original ZIP Range must be exactly 49152 bytes")
    _require(re.fullmatch(r"[0-9a-f]{64}", expected_sha256 or "") is not None,
             "explicit external source SHA-256 is required")
    sha = hashlib.sha256(data).hexdigest()
    _require(sha == expected_sha256, "original source HTTP Range SHA mismatch")

    _require(_u32(data, 0) == 0x04034B50, "wrong local ZIP header")
    _require(_u16(data, 8) == 8, "original ZIP TIFF member must use deflate")
    name_len, extra_len = _u16(data, 26), _u16(data, 28)
    name_bytes = _span(data, 30, name_len)
    _require(name_bytes.decode("utf-8") == MEMBER, "unexpected ZIP member")
    offset = 30 + name_len + extra_len
    _require(offset < REQUEST_RANGE_BYTES - 1, "no ZIP compressed bytes found")
    inflator = zlib.decompressobj(wbits=-15)
    try:
        tiff = inflator.decompress(data[offset:], MAX_TIFF_PREFIX_BYTES + 1)
    except zlib.error as exc:
        raise SourceGateError("original outer ZIP deflate failed") from exc
    _require(len(tiff) <= MAX_TIFF_PREFIX_BYTES and not inflator.unconsumed_tail,
             "unsafe ZIP inflation ratio or prefix limit")
    result = parse_original_tiff_prefix(tiff, row=row, col=col)
    result.update({
        "original_archive_url": ORIGINAL_ARCHIVE,
        "zip_member": MEMBER,
        "original_zip_member_local_header_offset": ZIP_HEADER_ABSOLUTE_OFFSET,
        "exact_original_http_range": RANGE_SPEC,
        "original_range_sha256": sha,
        "original_range_bytes": len(data),
        "outer_zip_deflate_stream_completed": inflator.eof,
        "original_tiff_member_full_bytes_available": False,
        "source_bytes_persisted_by_runner": False,
        "commercial_underwriting_authorized": False,
    })
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-range", type=Path, required=True,
                        help="externally acquired exact original 49152-byte ZIP HTTP Range")
    parser.add_argument("--expected-sha256", default=ORIGINAL_RANGE_SHA256)
    args = parser.parse_args(argv)
    try:
        path = args.original_range
        if path.is_symlink() or not path.is_file() or path.stat().st_size != REQUEST_RANGE_BYTES:
            raise SourceGateError("original source range file absent, linked or wrong size")
        receipt = parse_bounded_original_zip_range(
            path.read_bytes(), args.expected_sha256)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (SourceGateError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
