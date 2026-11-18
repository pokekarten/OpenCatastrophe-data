#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two immutable JRC GHSL E2020 native source-block research probes.

Each explicit product performs ONLY two HTTPS byte-range reads against its
fixed unsigned S3 object: 32KiB original TIFF prefix and exactly one native
compressed TIFF block. Verify 206, Content-Range, source size, source header
SHA-256, GeoTIFF coordinates, coding and tile-table byte position BEFORE
decompressing the single 512x512 uint32 block into memory. Output only
aggregate statistics for one fixed 32x32 research window and source SHA
receipts; never persist original bytes, individual cells, asset positions,
buildings, TIV, hazard intensity or CAT-model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zlib

from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import (
    PREFIX_BYTES, PRODUCTS, GHSLHeaderBlocked, verify_original_tiff_prefix,
)

ROOT = "https://jrc-ghsl.s3.eu-central-1.amazonaws.com"
FILES = {
    "surface": "/ghs-built-s/r2023a/4326/30asec/2020/GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif",
    "volume": "/ghs-built-v/r2023a/4326/30asec/2020/GHS_BUILT_V_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif",
}
TILE_SIDE = 512
NATIVE_BYTES = TILE_SIDE * TILE_SIDE * 4
WINDOW_SIDE = 32
WINDOW_LOCAL_X, WINDOW_LOCAL_Y = 445, 291
UINT32_NODATA_CANDIDATE = 0xffffffff
MAX_ORIGINAL_REQUEST_BYTES = 600_000


class GHSLNativeBlocked(ValueError):
    """A request, source-block identity or decoded datum failed closed."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GHSLNativeBlocked("redirect of original JRC source not authorized")


def _fetch_range(product: str, start: int, length: int, *, opener=None) -> bytes:
    if product not in PRODUCTS or product not in FILES:
        raise GHSLNativeBlocked("product not on exact original-source whitelist")
    cfg = PRODUCTS[product]
    allowed = {(0, PREFIX_BYTES), (cfg["native_block_offset"], cfg["native_block_bytes"])}
    if ((start, length) not in allowed or type(start) is not int
            or type(length) is not int or not 0 < length <= MAX_ORIGINAL_REQUEST_BYTES):
        raise GHSLNativeBlocked("unreviewed or overlarge original source byte range")
    url = ROOT + FILES[product]
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "jrc-ghsl.s3.eu-central-1.amazonaws.com"
            or parts.query or parts.fragment or parts.path != FILES[product]):
        raise GHSLNativeBlocked("source origin/path drift")
    end = start + length - 1
    req = Request(url, method="GET", headers={
        "Range": f"bytes={start}-{end}",
        "Accept-Encoding": "identity",
        "Accept": "application/octet-stream,binary/octet-stream,image/tiff",
        "User-Agent": "OpenCatastrophe-GHSL-Native-Fixed-Block/0.1",
    })
    open_request = opener if opener is not None else build_opener(
        ProxyHandler({}), NoRedirect()
    ).open
    try:
        with open_request(req, timeout=45) as response:
            if response.status != 206 or response.geturl() != url:
                raise GHSLNativeBlocked("provider did not return original exact HTTP 206")
            if (response.headers.get("Content-Range", "") !=
                    f"bytes {start}-{end}/{cfg['object_bytes']}"):
                raise GHSLNativeBlocked("source Content-Range or full file size drift")
            if response.headers.get("Content-Length", "") != str(length):
                raise GHSLNativeBlocked("original source Content-Length drift")
            media = response.headers.get("Content-Type", "").lower().split(";", 1)[0]
            if media not in ("binary/octet-stream", "application/octet-stream", "image/tiff"):
                raise GHSLNativeBlocked("source MIME not the reviewed TIFF")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise GHSLNativeBlocked("unreviewed source content encoding")
            raw = response.read(length + 1)
    except GHSLNativeBlocked:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise GHSLNativeBlocked("fixed original JRC source range unavailable") from exc
    if len(raw) != length:
        raise GHSLNativeBlocked("short or overlong original source range")
    return raw


def aggregate_native_block(compressed: bytes, *, expected_bytes: int | None = None) -> dict:
    """Bounded TIFF Deflate uint32 decode; inspect only a fixed 32x32 window.

    expected_bytes=None is permitted only for synthetic test fixture calls;
    live source requests are exact length-checked by _fetch_range().
    """
    if (type(compressed) is not bytes or len(compressed) == 0
            or len(compressed) > MAX_ORIGINAL_REQUEST_BYTES
            or (expected_bytes is not None and
                (type(expected_bytes) is not int or len(compressed) != expected_bytes))):
        raise GHSLNativeBlocked("source compressed block bytes outside reviewed limit")
    try:
        decompressor = zlib.decompressobj()
        decoded = decompressor.decompress(compressed, NATIVE_BYTES + 1)
    except zlib.error as exc:
        raise GHSLNativeBlocked("invalid TIFF Deflate source coding") from exc
    if (len(decoded) != NATIVE_BYTES or not decompressor.eof
            or decompressor.unused_data or decompressor.unconsumed_tail):
        raise GHSLNativeBlocked("source tile uint32 output length/bomb/trailing data rejected")
    zero = positive = potential_nodata = 0
    sum_positive = 0
    min_positive = max_positive = None
    window = bytearray()
    for row in range(WINDOW_LOCAL_Y, WINDOW_LOCAL_Y + WINDOW_SIDE):
        first = (row * TILE_SIDE + WINDOW_LOCAL_X) * 4
        segment = decoded[first:first+WINDOW_SIDE*4]
        if len(segment) != WINDOW_SIDE*4:
            raise GHSLNativeBlocked("fixed native spatial window outside decoded TIFF")
        window.extend(segment)
        for (val,) in struct.iter_unpack("<I", segment):
            if val == 0:
                zero += 1
            elif val == UINT32_NODATA_CANDIDATE:
                potential_nodata += 1
            else:
                positive += 1
                sum_positive += val
                min_positive = val if min_positive is None else min(val, min_positive)
                max_positive = val if max_positive is None else max(val, max_positive)
    if zero + positive + potential_nodata != WINDOW_SIDE**2:
        raise GHSLNativeBlocked("invalid fixed 32x32 window class accounting")
    return {
        "original_source_compressed_block_sha256": hashlib.sha256(compressed).hexdigest(),
        "original_source_decoded_block_sha256": hashlib.sha256(decoded).hexdigest(),
        "native_decoded_uint32_cells": TILE_SIDE*TILE_SIDE,
        "native_block_decoded_bytes": NATIVE_BYTES,
        "fixed_original_window_shape": [WINDOW_SIDE, WINDOW_SIDE],
        "fixed_original_window_global_col_row": [
            44*TILE_SIDE+WINDOW_LOCAL_X, 9*TILE_SIDE+WINDOW_LOCAL_Y
        ],
        "fixed_window_uint32_le_sha256": hashlib.sha256(window).hexdigest(),
        "fixed_window_zero_cells": zero,
        "fixed_window_positive_non_sentinel_cells": positive,
        "fixed_window_potential_uint32_max_sentinel_cells": potential_nodata,
        "fixed_window_positive_sum_raw_source_units": sum_positive,
        "fixed_window_min_positive_value": min_positive,
        "fixed_window_max_positive_value": max_positive,
        "uint32_max_nodata_semantics_approved": False,
        "physical_area_metres_from_angular_grid_proven": False,
        "individual_source_raster_pixels_persisted": False,
        "insurer_exposure_or_tiv_inferred": False,
        "model_input_approved": False,
    }


def run_probe(product: str) -> dict:
    if product not in PRODUCTS:
        raise GHSLNativeBlocked("unknown original product")
    cfg = PRODUCTS[product]
    header = _fetch_range(product, 0, PREFIX_BYTES)
    try:
        meta = verify_original_tiff_prefix(header, product)
    except GHSLHeaderBlocked as exc:
        raise GHSLNativeBlocked("original TIFF prefix verification rejected") from exc
    tile = _fetch_range(product, cfg["native_block_offset"],
                        cfg["native_block_bytes"])
    outcome = aggregate_native_block(tile, expected_bytes=cfg["native_block_bytes"])
    return {
        "source_id": cfg["source_id"],
        "original_tiff_url": ROOT + FILES[product],
        "product_epoch": 2020,
        "original_source_header_sha256": cfg["prefix_sha256"],
        "original_source_file_size_from_exact_content_range": cfg["object_bytes"],
        "original_source_native_block_index": meta["fixed_source_block_index"],
        "original_source_native_block_bytes": cfg["native_block_bytes"],
        "original_source_native_block_offset": cfg["native_block_offset"],
        "original_data_unit_from_publisher": cfg["unit"],
        **outcome,
        "source_bytes_saved_or_committed": False,
        "source_modified": False,
        "full_original_geotiff_sha256_verified": False,
        "native_window_scientifically_calibrated": False,
        "source_product_admitted": False,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True, choices=sorted(PRODUCTS))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live is required for reviewed fixed original HTTP Range")
    try:
        print(json.dumps(run_probe(args.product), sort_keys=True, allow_nan=False))
        return 0
    except (GHSLNativeBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
