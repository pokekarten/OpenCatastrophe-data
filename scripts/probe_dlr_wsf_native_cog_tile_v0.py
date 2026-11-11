#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded real native WSF 2019 COG inspection for one exact Munich-adjacent tile.

Two read-only HTTP Range requests: a 32-KiB TIFF header and one fixed 24,659
byte 512x512 compressed TIFF block. Do not request a full GeoTIFF or accept
caller-supplied locations/paths. Decode LZW in memory without exporting raw
provider bytes. Outputs only SHA-256 receipts, CRS, dimensions, class counts
and native window hashes; research only, no building/TIV/model admission.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SOURCE = "dlr.wsf.2019"
URL = "https://download.geoservice.dlr.de/WSF2019/files/WSF2019_v1_10_48.tif"
LICENSE_URL = "https://download.geoservice.dlr.de/WSF2019/files/WSF2019_README.txt"
HEADER_SIZE = 32768
HEADER_SHA256 = "1e881e8323d3ade63ad4453a0c1b7af6d792ae254356ceb20c197d0316ab80b7"
NATIVE_TILE_INDEX = 1793
NATIVE_TILE_OFFSET = 12156322
NATIVE_TILE_BYTES = 24659
NATIVE_TILE_SHA256 = "8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503"
SHAPE = (22487, 22487)  # native, not overview
TILE_DIMENSION = 512
LZW_CLEAR, LZW_EOI = 256, 257
WINDOWS = {
    "nonsettlement": {
        "tile_xy": (448, 432),
        "expected_255": 0,
        "rows_sha256": "ff08ea1f4b89475bb4bcf8d4a453e55058f21eba2de2daa1fb5943d1706293df",
    },
    "mixed": {
        "tile_xy": (464, 464),
        "expected_255": 482,
        "rows_sha256": "85aaf92c2b87fc7ea80359498680bca371aaa0e974d65476328bb70e314b3fce",
    },
}
PNG_SAMPLES_ARE_NOT_NATIVE = True


class NativeCOGBlocked(ValueError):
    """Provider bytes are not the exact reviewed native GeoTIFF product."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise NativeCOGBlocked("redirect not authorized for original COG")


def _fetch_range(start: int, count: int) -> tuple[bytes, int]:
    """Strict 206, Content-Range, fixed host and bounded bytes; never full GET."""
    if (start, count) not in {
        (0, HEADER_SIZE), (NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES)
    }:
        raise NativeCOGBlocked("unreviewed TIFF byte window")
    parsed = urlsplit(URL)
    if (parsed.scheme != "https"
            or parsed.netloc != "download.geoservice.dlr.de"
            or parsed.path != "/WSF2019/files/WSF2019_v1_10_48.tif"
            or parsed.query or parsed.fragment):
        raise NativeCOGBlocked("original source identity changed")
    end = start + count - 1
    request = Request(URL, method="GET", headers={
        "Range": f"bytes={start}-{end}",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-Native-COG-Range-Probe/0.1",
    })
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=30) as response:
            if response.status != 206 or response.geturl() != URL:
                raise NativeCOGBlocked("provider must honor immutable bounded HTTP Range")
            media = response.headers.get("Content-Type", "").lower().split(";")[0]
            if media not in ("image/tiff", "image/geotiff", "application/octet-stream"):
                raise NativeCOGBlocked("not the original TIFF media type")
            content_range = response.headers.get("Content-Range", "").strip()
            match = re.fullmatch(
                rf"bytes {start}-{end}/([1-9][0-9]+)", content_range
            )
            if not match:
                raise NativeCOGBlocked("Content-Range does not match exact requested bytes")
            total = int(match.group(1))
            if not 13_000_000 <= total <= 100_000_000 or total <= end:
                raise NativeCOGBlocked("unexpected full TIFF byte length")
            data = response.read(count + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise NativeCOGBlocked("original COG HTTP Range failed") from exc
    if len(data) != count:
        raise NativeCOGBlocked("partial or overlong COG byte range")
    return data, total


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_native_header(data: bytes) -> dict:
    """Parse exact little-endian ClassicTIFF IFD0, geokeys and tile index."""
    if len(data) != HEADER_SIZE or data[:4] != b"II\x2a\x00":
        raise NativeCOGBlocked("unexpected classic little-endian TIFF header")
    off = struct.unpack_from("<I", data, 4)[0]
    if off != 192:
        raise NativeCOGBlocked("original IFD0 offset changed")
    count = struct.unpack_from("<H", data, off)[0]
    if count != 19 or off + 2 + 12 * count + 4 > len(data):
        raise NativeCOGBlocked("unexpected native TIFF IFD")
    tags = {}
    for index in range(count):
        pos = off + 2 + 12 * index
        tag, typ, n, value = struct.unpack_from("<HHII", data, pos)
        if tag in tags:
            raise NativeCOGBlocked("duplicate TIFF tag")
        sizes = {1: 1, 2: 1, 3: 2, 4: 4, 12: 8}
        if typ not in sizes or n < 1 or n * sizes[typ] > HEADER_SIZE:
            raise NativeCOGBlocked("unsupported TIFF native IFD tag")
        begin = pos + 8 if n * sizes[typ] <= 4 else value
        if begin + n * sizes[typ] > len(data):
            raise NativeCOGBlocked("TIFF tag value outside bounded header")
        tags[tag] = (typ, n, begin)

    def values(tag: int) -> tuple:
        if tag not in tags:
            raise NativeCOGBlocked(f"required TIFF tag {tag} missing")
        typ, n, start = tags[tag]
        fmt = {1: "B", 2: "B", 3: "H", 4: "I", 12: "d"}[typ]
        return struct.unpack_from("<" + fmt * n, data, start)

    width, height = values(256)[0], values(257)[0]
    if (width, height) != SHAPE:
        raise NativeCOGBlocked("wrong native dimensions or overview selected")
    tests = {
        258: 8, 259: 5, 262: 1, 277: 1, 284: 1,
        317: 1, 322: TILE_DIMENSION, 323: TILE_DIMENSION, 339: 1,
    }
    for tag, expected in tests.items():
        if values(tag) != (expected,):
            raise NativeCOGBlocked(f"unexpected TIFF encoding tag {tag}")
    if 42113 in tags:
        raise NativeCOGBlocked("NoData tag appeared; requires distinct class semantics review")

    keys = values(34735)
    if len(keys) < 8 or keys[:4] != (1, 1, 0, 7):
        raise NativeCOGBlocked("GeoKeyDirectory layout changed")
    geokeys = {}
    for p in range(4, len(keys), 4):
        key, location, n, value = keys[p:p + 4]
        if key in geokeys:
            raise NativeCOGBlocked("duplicate GeoTIFF geokey")
        if location == 0 and n == 1:
            geokeys[key] = value
    if geokeys.get(2048) != 4326 or geokeys.get(1024) != 2:
        raise NativeCOGBlocked("source not WGS84 geographic GeoTIFF")
    scale = values(33550)
    tie = values(33922)
    if len(scale) != 3 or len(tie) != 6:
        raise NativeCOGBlocked("invalid GDAL pixel scale or origin")
    if (not math.isclose(scale[0], 0.00008983152841195215, abs_tol=1e-14)
            or scale[0] != scale[1] or scale[2] != 0
            or tie[:3] != (0, 0, 0)
            or not math.isclose(tie[3], 9.989984611636375, abs_tol=1e-11)
            or not math.isclose(tie[4], 50.010020350689466, abs_tol=1e-11)):
        raise NativeCOGBlocked("native geotransform changed")
    offsets, sizes = values(324), values(325)
    tiles_per_row = math.ceil(width / TILE_DIMENSION)
    ntiles = tiles_per_row * math.ceil(height / TILE_DIMENSION)
    if len(offsets) != ntiles or len(sizes) != ntiles or ntiles != 1936:
        raise NativeCOGBlocked("unexpected tile arrays or grid shape")
    tile_index = 40 * tiles_per_row + 33
    if (tile_index != NATIVE_TILE_INDEX
            or offsets[tile_index] != NATIVE_TILE_OFFSET
            or sizes[tile_index] != NATIVE_TILE_BYTES):
        raise NativeCOGBlocked("original native compressed tile index moved")
    return {
        "native_shape": [width, height],
        "raster_dtype": "uint8", "compression": "TIFF LZW", "lzw_early_change": True,
        "predictor": 1, "epsg": 4326, "nodata_tiff_tag": None,
        "geotransform": [scale[0], 0, tie[3], 0, -scale[1], tie[4]],
        "tile_index": tile_index, "tile_width": TILE_DIMENSION,
        "tile_height": TILE_DIMENSION, "tile_offset": offsets[tile_index],
        "tile_compressed_bytes": sizes[tile_index],
    }


def decode_tiff_lzw(data: bytes, *, max_output: int = TILE_DIMENSION ** 2) -> bytes:
    """Bounded MSB-first TIFF LZW with early code-size change, no dependencies."""
    if not data or len(data) > 65_536 or max_output <= 0 or max_output > 262_144:
        raise NativeCOGBlocked("compressed native tile outside reviewed bound")
    table = [bytes([i]) for i in range(256)] + [None] * 3840
    width, bitpos, next_code, last, decoded, resets = 9, 0, 258, None, bytearray(), 0

    def next_symbol() -> int:
        nonlocal bitpos
        if bitpos + width > len(data) * 8:
            raise NativeCOGBlocked("LZW stream ended before TIFF EOI")
        symbol = 0
        for i in range(width):
            p = bitpos + i
            symbol = (symbol << 1) | ((data[p // 8] >> (7 - p % 8)) & 1)
        bitpos += width
        return symbol

    for _ in range(400_000):
        code = next_symbol()
        if code == LZW_CLEAR:
            table = [bytes([i]) for i in range(256)] + [None] * 3840
            width, next_code, last = 9, 258, None
            resets += 1
            continue
        if code == LZW_EOI:
            if resets == 0 or len(decoded) != max_output:
                raise NativeCOGBlocked("LZW incomplete tile or missing CLEAR")
            return bytes(decoded)
        part = table[code] if 0 <= code < 4096 else None
        if part is None and code == next_code and last:
            part = last + last[:1]
        if part is None or len(decoded) + len(part) > max_output:
            raise NativeCOGBlocked("LZW invalid code or inflated tile bound exceeded")
        decoded.extend(part)
        if last is not None and next_code < 4096:
            table[next_code] = last + part[:1]
            next_code += 1
            if width < 12 and next_code == (1 << width) - 1:
                width += 1
        last = part
    raise NativeCOGBlocked("LZW code count exhausted without EOI")


def inspect_tile(tile: bytes, tiff: dict) -> dict:
    if _hash(tile) != NATIVE_TILE_SHA256:
        raise NativeCOGBlocked("source compressed native block SHA-256 changed")
    pixels = decode_tiff_lzw(tile)
    settlement = pixels.count(255)
    if settlement != 117_413 or pixels.count(0) != 144_731:
        raise NativeCOGBlocked("invalid native class histogram or unsupported values")
    windows = {}
    pixel_size = tiff["geotransform"][0]
    west = tiff["geotransform"][2]
    north = tiff["geotransform"][5]
    for label, rule in WINDOWS.items():
        x, y = rule["tile_xy"]
        if x < 0 or y < 0 or x + 32 > 512 or y + 32 > 512:
            raise NativeCOGBlocked("window exceeds one compressed native tile")
        rows = []
        positive = 0
        for local_y in range(y, y + 32):
            sample = pixels[local_y * 512 + x:local_y * 512 + x + 32]
            if len(sample) != 32 or any(value not in (0, 255) for value in sample):
                raise NativeCOGBlocked("unexpected native pixel class")
            positive += sample.count(255)
            rows.append("".join("1" if value == 255 else "0" for value in sample))
        digest = _hash("\n".join(rows).encode("utf-8"))
        if positive != rule["expected_255"] or digest != rule["rows_sha256"]:
            raise NativeCOGBlocked(f"sampled native {label} mask disagrees with Neon")
        global_col, global_row = 33 * 512 + x, 40 * 512 + y
        west_lon, north_lat = west + global_col * pixel_size, north - global_row * pixel_size
        windows[label] = {
            "window_global_col": global_col, "window_global_row": global_row,
            "bbox_lonlat": [west_lon, north_lat - 32 * pixel_size,
                            west_lon + 32 * pixel_size, north_lat],
            "width": 32, "height": 32, "settlement_255": positive,
            "nonsettlement_0": 1024 - positive,
            "mask_rows_sha256": digest,
        }
    return {
        "compressed_tile_sha256": _hash(tile),
        "decompressed_tile_bytes": len(pixels),
        "native_tile_histogram": {"0": 144_731, "255": 117_413},
        "windows": windows,
    }


def run_probe() -> dict:
    header, file_size = _fetch_range(0, HEADER_SIZE)
    if _hash(header) != HEADER_SHA256:
        raise NativeCOGBlocked("original TIFF 32KiB header SHA-256 changed")
    parsed = parse_native_header(header)
    tile, second_total = _fetch_range(NATIVE_TILE_OFFSET, NATIVE_TILE_BYTES)
    if second_total != file_size:
        raise NativeCOGBlocked("two native byte ranges came from differing file sizes")
    item = inspect_tile(tile, parsed)
    return {
        "source_id": SOURCE, "original_asset": URL, "source_license": "CC BY 4.0",
        "source_license_url": LICENSE_URL, "original_tiff_total_bytes": file_size,
        "original_header_sha256": _hash(header), **parsed, **item,
        "provider_bytes_persisted": False, "model_input_approved": False,
        "individual_building_count_validated": False, "insured_tiv_validated": False,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    try:
        print(json.dumps(run_probe(), sort_keys=True))
        return 0
    except NativeCOGBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
