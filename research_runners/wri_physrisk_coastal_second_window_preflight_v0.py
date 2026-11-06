#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-source crosscheck for WRI coastal 100-year flood, Bay of Bengal.

Seven original provider HTTP Range response files, source-hashed and bounded:
two 4-byte TIFF strip-table values, one 4291-byte LZW strip, a 4096-byte
Blosc chunk header, and three adjacent partial HTTP ranges of ONE 85755-byte
Zarr chunk block. No HTTP, third-party raw data output, insurance loss or
source/admission approval. Distinct from the original Gulf Coast 2-year proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import (
    PixelGateError, compare_pixels, lz4_raw_decode, tiff_lzw_decode,
)

PROFILE = "wri-physrisk-100yr-bay-of-bengal-1000-pixel-pair-v0"
WRI_URL = ("https://aqueduct.wridata.org/AqueductFloods20/"
           "inuncoast_historical_nosub_hist_rp0100_0.tif")
ZARR_URL = ("https://os-climate-physical-risk.s3.amazonaws.com/"
            "hazard-indicators/hazard.zarr/inundation/wri/v2/"
            "inuncoast_historical_nosub_hist_0/0.8.32")
ROW = 8100
FIRST_COL = 32000
NCOLS = 1000
RETURN_PERIOD = 100
RETURN_PERIOD_INDEX = 5
ZARR_CHUNK_LOCAL_ROW = 100
ZARR_BLOCK_INDEX = 38
ZARR_UNCOMPRESSED_BLOCK_SIZE = 524288
ZARR_BLOCK_OFFSET = 1380254
ZARR_BLOCK_NEXT_OFFSET = 1466009
ZARR_COMPRESSED_OBJECT_LENGTH = 2375870
ZARR_TOTAL_UNCOMPRESSED = 36000000
TIFF_STRIP_OFFSET = 17824039
TIFF_STRIP_BYTES = 4291
TIFF_WIDTH = 43200

# Each payload is the exact original independent HTTP Range response.
# All arrays/raster samples remain outside Git.
HTTP_RANGES = {
    "tiff_offset": (WRI_URL, 46328494, 46328497),
    "tiff_bytecount": (WRI_URL, 46242094, 46242097),
    "tiff_strip": (WRI_URL, TIFF_STRIP_OFFSET, TIFF_STRIP_OFFSET + TIFF_STRIP_BYTES - 1),
    "zarr_header": (ZARR_URL, 0, 4095),
    "zarr_part0": (ZARR_URL, 1380254, 1410253),
    "zarr_part1": (ZARR_URL, 1410254, 1440253),
    "zarr_part2": (ZARR_URL, 1440254, 1466008),
}
DIGEST = {
    "tiff_offset": "241a517ef24d0a4d13ecc1223a5e15673fd57de102e3b7e6e8414bce187b10e2",
    "tiff_bytecount": "d4251ca6381f532ec18b0ba155f27737f25a8abfddde141cab0ac80f7a171bf0",
    "tiff_strip": "272f3ca2ddb9c39e2218e96980c34d4ed60b04d651023a3e4da4e6ffa127b5fd",
    "zarr_header": "d0d1abe763ca50acc59706516a12d744d359d81c235d0ba1b9c0e1fa4b8dfad8",
    "zarr_part0": "ea204ee2f7a0380e1ee0507c410690fded8173425a52aa933a3b54d7433464fd",
    "zarr_part1": "3aa2077b06753066c10b9bc1ae127e1dd986407bfeaa1e40a457b5c897a71d55",
    "zarr_part2": "0845dd587ce5d4ca91b718140de8e554cf12c47dadca0ded0b22c26796c68450",
}
COMPLETE_BLOCK_SHA256 = "9144355508425d0f703c309d28e919c019ca4c52841ec2e000e3c69849a5d8f5"


def read_exact_range(path: Path, key: str) -> bytes:
    if key not in HTTP_RANGES:
        raise PixelGateError("unknown source part key")
    _url, start, end = HTTP_RANGES[key]
    limit = end - start + 1
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) != limit or hashlib.sha256(data).hexdigest() != DIGEST[key]:
        raise PixelGateError(key + ": original response truncated, oversized or SHA256 changed")
    return data


def parse_blosc_block(header: bytes, payload: bytes) -> tuple[bytes, ...]:
    """Validate full layout and decompress only the pinned Blosc block #38."""
    if len(header) != 4096 or len(payload) != ZARR_BLOCK_NEXT_OFFSET - ZARR_BLOCK_OFFSET:
        raise PixelGateError("invalid Blosc metadata or exact compressed block length")
    version, codec_version, flags, typesize, total_bytes, blocksize, cbytes = (
        struct.unpack_from("<BBBBIII", header))
    if (version, codec_version, flags, typesize, total_bytes, blocksize, cbytes) != (
            2, 1, 33, 4, ZARR_TOTAL_UNCOMPRESSED,
            ZARR_UNCOMPRESSED_BLOCK_SIZE, ZARR_COMPRESSED_OBJECT_LENGTH):
        raise PixelGateError("unexpected original Zarr Blosc codec, size or byte shuffle")
    blocks = (total_bytes + blocksize - 1) // blocksize
    if blocks != 69 or len(header) < 16 + blocks * 4:
        raise PixelGateError("invalid Blosc original block count")
    offsets = struct.unpack_from("<" + "I" * blocks, header, 16)
    if len(set(offsets)) != len(offsets) or any(
            pos < 16 + blocks * 4 or pos >= cbytes for pos in offsets):
        raise PixelGateError("invalid Blosc block-offset index")
    end = min((pos for pos in offsets if pos > offsets[ZARR_BLOCK_INDEX]), default=cbytes)
    if (offsets[ZARR_BLOCK_INDEX], end) != (
            ZARR_BLOCK_OFFSET, ZARR_BLOCK_NEXT_OFFSET):
        raise PixelGateError("original Blosc block boundaries drifted")
    at = 0
    streams = []
    for _ in range(typesize):
        if at + 4 > len(payload):
            raise PixelGateError("truncated Blosc LZ4 stream length")
        encoded_size = struct.unpack_from("<I", payload, at)[0]
        at += 4
        if encoded_size <= 0 or at + encoded_size > len(payload):
            raise PixelGateError("invalid Blosc LZ4 byte count")
        streams.append(lz4_raw_decode(payload[at:at+encoded_size], blocksize // typesize))
        at += encoded_size
    if at != len(payload):
        raise PixelGateError("unreviewed trailing bytes in Blosc block")
    return tuple(streams)


def inspect_real_paired_ranges(inputs: dict[str, bytes]) -> dict:
    if set(inputs) != set(DIGEST):
        raise PixelGateError("missing original HTTP response range")
    for name in DIGEST:
        data = inputs[name]
        _url, start, end = HTTP_RANGES[name]
        if type(data) is not bytes or len(data) != end - start + 1:
            raise PixelGateError(name + ": invalid exact response length")
        if hashlib.sha256(data).hexdigest() != DIGEST[name]:
            raise PixelGateError(name + ": original response hash mismatch")
    if struct.unpack("<I", inputs["tiff_offset"])[0] != TIFF_STRIP_OFFSET:
        raise PixelGateError("WRI TIFF strip pointer differs from original IFD")
    if struct.unpack("<I", inputs["tiff_bytecount"])[0] != TIFF_STRIP_BYTES:
        raise PixelGateError("WRI TIFF strip bytecount differs from original IFD")
    payload = b"".join(inputs[f"zarr_part{i}"] for i in range(3))
    if hashlib.sha256(payload).hexdigest() != COMPLETE_BLOCK_SHA256:
        raise PixelGateError("reassembled Blosc original block SHA256 differs")
    row = tiff_lzw_decode(inputs["tiff_strip"], TIFF_WIDTH * 4)
    streams = parse_blosc_block(inputs["zarr_header"], payload)
    # Return-period index 5 and local row 100, each 1,000 columns wide.
    # Single 524,288-byte Blosc block #38 represents 131,072 Float32 cells.
    scalar_row = RETURN_PERIOD_INDEX * 1000 + ZARR_CHUNK_LOCAL_ROW
    checked = compare_pixels(
        row, streams, FIRST_COL, NCOLS, scalar_row, 1000,
        ZARR_BLOCK_INDEX * (ZARR_UNCOMPRESSED_BLOCK_SIZE // 4),
    )
    expected = {
        "source_nodata_to_derived_nan": 72,
        "source_zero_exact": 594,
        "source_positive_exact": 334,
        "mismatches": 0,
        "other_source_values": 0,
        "paired_cells": 1000,
    }
    if any(checked[k] != v for k, v in expected.items()):
        raise PixelGateError("second source window failed independent exact pair check")
    return {
        "profile": PROFILE, "wri_original_tiff": WRI_URL,
        "physrisk_zarr_chunk": ZARR_URL,
        "wri_global_row": ROW, "wri_global_col_range": [FIRST_COL, FIRST_COL + NCOLS - 1],
        "return_period_years": [RETURN_PERIOD],
        "physrisk_return_period_index": RETURN_PERIOD_INDEX,
        "derived_chunk_key": "0.8.32", "derived_blosc_block_index": ZARR_BLOCK_INDEX,
        "sha256_original_range_files": dict(DIGEST),
        "sha256_reassembled_blosc_block": COMPLETE_BLOCK_SHA256,
        "pairing_counts": checked,
        "different_region_than_gulf_coast_first_proof": True,
        "different_return_period_than_gulf_coast_first_proof": True,
        "all_regions_verified": False,
        "all_return_periods_verified": False,
        "original_full_asset_sha256_verified": False,
        "producer_commit_version_verified": False,
        "coastal_defences_modelled": False,
        "independent_cat_events_present": False,
        "rights_and_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in DIGEST:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = {name: getattr(args, name) for name in DIGEST}
    resolved = {path.resolve() for path in paths.values()}
    if len(resolved) != len(paths) or args.out.resolve() in resolved:
        parser.error("do not reuse original range path or overwrite source bytes")
    try:
        original = {name: read_exact_range(path, name) for name, path in paths.items()}
        receipt = inspect_real_paired_ranges(original)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    except (OSError, PixelGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
