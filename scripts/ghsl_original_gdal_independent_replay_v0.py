#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent GDAL/LibTIFF original GHSL E2020 tile replay (research only).

For each whitelisted product, reuse the existing exact one-header+one-block
HTTP-206 source acquisition and source SHA/GeoTIFF gate. Wrap the already
fetched compressed native 512x512 tile in a minimal TIFF only in RAM and let
GDAL/LibTIFF (not Python struct/zlib) decode it independently. Compare original
sha256 and 32x32 research aggregate to trusted-main run 43309743505.
No external raw bytes, reconstructed file or individual pixel is persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import warnings
import zlib
from datetime import datetime, timezone

from scripts.probe_ghsl_built_native_original_block_v0 import (
    FILES, GHSLNativeBlocked, MAX_ORIGINAL_REQUEST_BYTES, NATIVE_BYTES,
    ROOT, TILE_SIDE, UINT32_NODATA_CANDIDATE, WINDOW_LOCAL_X, WINDOW_LOCAL_Y,
    WINDOW_SIDE, _fetch_range,
)
from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import (
    GHSLHeaderBlocked, PREFIX_BYTES, PRODUCTS, verify_original_tiff_prefix,
)

# Independently acquired and decoded exact JRC blocks; original main Actions
# run https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43309743505
# These are ORIGINAL source receipts, not synthetic targets or reference truth.
ORIGINAL_EXPECTED = {
    "surface": {
        "compressed_sha256": "eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9",
        "decoded_sha256": "1d961e2c951e4db8df6e22776903aa06ea943a9f49728ef4a8fa8178506c8923",
        "window_sha256": "2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106",
        "positive": 937, "zero": 87, "potential_nodata": 0,
        "sum_positive": 74802406, "min_positive": 1, "max_positive": 321677,
    },
    "volume": {
        "compressed_sha256": "578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c",
        "decoded_sha256": "e91e026954d2f37d19c48ea87b3e33207e8c67e0efdda0d5c66589a3e751b5f5",
        "window_sha256": "2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9",
        "positive": 937, "zero": 87, "potential_nodata": 0,
        "sum_positive": 520775503, "min_positive": 1, "max_positive": 3168579,
    },
}


class IndependentGHSLBlocked(ValueError):
    """Untrusted original bytes or nonreproducible native raster values."""


def make_ram_only_one_tile_tiff(compressed: bytes) -> bytes:
    """TIFF 6.0 local in-memory decoder wrapper, NOT original GeoTIFF file.

    No CRS/GeoKeys are invented: original-source geographic metadata is
    validated separately by verify_original_tiff_prefix().
    """
    if type(compressed) is not bytes or not 0 < len(compressed) <= MAX_ORIGINAL_REQUEST_BYTES:
        raise IndependentGHSLBlocked("unreviewed compressed tile length")
    tags = {
        256: (4, TILE_SIDE), 257: (4, TILE_SIDE), 258: (3, 32),
        259: (3, 8), 262: (3, 1), 277: (3, 1), 284: (3, 1),
        317: (3, 1), 322: (4, TILE_SIDE), 323: (4, TILE_SIDE),
        325: (4, len(compressed)), 339: (3, 1),
    }
    n = len(tags) + 1
    offset = (8 + 2 + 12*n + 4 + 15) & ~15
    tags[324] = (4, offset)
    prefix = bytearray(offset)
    struct.pack_into("<2sHI", prefix, 0, b"II", 42, 8)
    struct.pack_into("<H", prefix, 8, n)
    for i, (tag, (typ, value)) in enumerate(sorted(tags.items())):
        struct.pack_into("<HHII", prefix, 10 + 12*i, tag, typ, 1, value)
    return bytes(prefix) + compressed


def decode_gdal_aggregate(compressed: bytes) -> dict:
    """Return hashes and aggregates only. All raster cells remain transient."""
    try:
        import numpy as np
        import rasterio
        from rasterio.errors import NotGeoreferencedWarning, RasterioIOError
    except ImportError as exc:
        raise IndependentGHSLBlocked("pinned rasterio/numpy dependency unavailable") from exc
    # LibTIFF can silently truncate an over-inflating stream into one tile.
    # Require the entire exact Deflate frame to decode to precisely the
    # reviewed 1MiB native tile BEFORE using GDAL for independent cell values.
    # This is an input-envelope check, not the independent numeric decoder.
    try:
        stream = zlib.decompressobj()
        inflated = stream.decompress(compressed, NATIVE_BYTES + 1)
        if (len(inflated) != NATIVE_BYTES or not stream.eof
                or stream.unused_data or stream.unconsumed_tail):
            raise IndependentGHSLBlocked("native source Deflate envelope length/trailing bytes invalid")
    except zlib.error as exc:
        raise IndependentGHSLBlocked("invalid TIFF source Deflate frame") from exc
    blob = make_ram_only_one_tile_tiff(compressed)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", NotGeoreferencedWarning)
            with rasterio.MemoryFile(blob) as mem:
                with mem.open() as ds:
                    if (ds.driver != "GTiff" or ds.count != 1
                            or ds.width != TILE_SIDE or ds.height != TILE_SIDE
                            or ds.dtypes != ("uint32",)
                            or ds.block_shapes != [(TILE_SIDE, TILE_SIDE)]
                            or ds.nodata is not None):
                        raise IndependentGHSLBlocked("GDAL TIFF dimensions or unsigned cell type changed")
                    cells = ds.read(1)
    except IndependentGHSLBlocked:
        raise
    except (RasterioIOError, RuntimeError, ValueError, OSError) as exc:
        raise IndependentGHSLBlocked("independent GDAL/libtiff decode failed") from exc
    if cells.shape != (TILE_SIDE, TILE_SIDE) or cells.dtype.kind != "u" or cells.dtype.itemsize != 4:
        raise IndependentGHSLBlocked("non uint32 GDAL output")
    decoded = np.asarray(cells, dtype="<u4", order="C").tobytes(order="C")
    if len(decoded) != NATIVE_BYTES:
        raise IndependentGHSLBlocked("not 1MiB decoded native TIFF block")
    window = np.ascontiguousarray(
        cells[WINDOW_LOCAL_Y:WINDOW_LOCAL_Y + WINDOW_SIDE,
              WINDOW_LOCAL_X:WINDOW_LOCAL_X + WINDOW_SIDE], dtype="<u4"
    )
    if window.shape != (WINDOW_SIDE, WINDOW_SIDE):
        raise IndependentGHSLBlocked("invalid fixed original window geometry")
    zero = window == 0
    sentinel = window == UINT32_NODATA_CANDIDATE
    positives = window[(~zero) & (~sentinel)]
    return {
        "independent_method": "rasterio/GDAL/libtiff Deflate in RAM",
        "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "window_sha256": hashlib.sha256(window.tobytes(order="C")).hexdigest(),
        "positive": int(positives.size),
        "zero": int(np.count_nonzero(zero)),
        "potential_nodata": int(np.count_nonzero(sentinel)),
        "sum_positive": int(positives.sum(dtype=np.uint64)),
        "min_positive": int(positives.min()) if positives.size else None,
        "max_positive": int(positives.max()) if positives.size else None,
        "native_decoded_uint32_count": TILE_SIDE*TILE_SIDE,
        "fixed_window_cells": WINDOW_SIDE*WINDOW_SIDE,
        "original_pixels_or_reconstructed_tiff_saved": False,
        "independent_GDAL_decode_validates_original_georeferencing": False,
        "separate_original_prefix_GeoTIFF_proven": True,
        "nodata_semantics_validated": False,
        "insurance_CAT_model_input_approved": False,
    }


def validate_original_gdal_result(compressed: bytes, product: str) -> dict:
    if product not in ORIGINAL_EXPECTED or product not in PRODUCTS:
        raise IndependentGHSLBlocked("unreviewed source product")
    if type(compressed) is not bytes or len(compressed) != PRODUCTS[product]["native_block_bytes"]:
        raise IndependentGHSLBlocked("original source block length drift")
    sha = hashlib.sha256(compressed).hexdigest()
    if sha != ORIGINAL_EXPECTED[product]["compressed_sha256"]:
        raise IndependentGHSLBlocked("original source block SHA-256 drift")
    result = decode_gdal_aggregate(compressed)
    for key, expected in ORIGINAL_EXPECTED[product].items():
        if key == "compressed_sha256":
            continue
        if result[key] != expected:
            raise IndependentGHSLBlocked(f"independent original GDAL disagreement: {key}")
    return {
        **result,
        "original_compressed_source_sha256": sha,
        "original_2026_11_12_main_result_reproduced": True,
        "research_only": True,
        "model_input_approved": False,
    }


def run_original_replay(product: str) -> dict:
    if product not in ORIGINAL_EXPECTED:
        raise IndependentGHSLBlocked("source not allowlisted")
    rule = PRODUCTS[product]
    header = _fetch_range(product, 0, PREFIX_BYTES)
    try:
        meta = verify_original_tiff_prefix(header, product)
    except GHSLHeaderBlocked as exc:
        raise IndependentGHSLBlocked("frozen original TIFF header gate failed") from exc
    compressed = _fetch_range(product, rule["native_block_offset"], rule["native_block_bytes"])
    evidence = validate_original_gdal_result(compressed, product)
    return {
        "source_id": rule["source_id"],
        "exact_original_source_url": ROOT + FILES[product],
        "original_prefix_sha256": rule["prefix_sha256"],
        "original_native_block_index": meta["fixed_source_block_index"],
        "original_native_compressed_block_bytes": rule["native_block_bytes"],
        "original_source_epoch": 2020,
        "independent_replay_utc": datetime.now(timezone.utc).isoformat(),
        "external_requests_exactly_two_source_range_reads": True,
        **evidence,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", choices=sorted(ORIGINAL_EXPECTED), required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("only explicit trusted-main --live allows provider source requests")
    try:
        print(json.dumps(run_original_replay(args.product), sort_keys=True, allow_nan=False))
        return 0
    except (IndependentGHSLBlocked, GHSLNativeBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
