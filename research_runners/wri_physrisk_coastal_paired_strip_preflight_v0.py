#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline paired-pixel check from two exact small original HTTP-range responses.

No network; no raw third-party bytes committed; no event, scientific, rights or
model admission. This is ONE WRI 2y coastal TIFF row against ONE Physrisk Zarr
block, selected by explicit original-provider byte-offset table entries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

WRI_URL = ("https://aqueduct.wridata.org/AqueductFloods20/"
           "inuncoast_historical_nosub_hist_rp0002_0.tif")
ZARR_URL = ("https://os-climate-physical-risk.s3.amazonaws.com/"
            "hazard-indicators/hazard.zarr/inundation/wri/v2/"
            "inuncoast_historical_nosub_hist_0/0.7.10")
PROFILE = "wri-physrisk-2yr-coastal-1000-pixel-paired-strip-v0"
ROW = 7206
FIRST_COL = 10000
NCOLS = 1000
TIF_WIDTH = 43200
TIF_OFFSET = 15020376
TIF_STRIP_LENGTH = 2545
ZARR_BLOCK_OFFSET = 37004
ZARR_BLOCK_LENGTH = 23266
ZARR_BLOCKSIZE = 524288
ZARR_CHUNK_UNCOMPRESSED = 36000000
ZARR_CHUNK_COMPRESSED = 1162420
SHA = {
    "tiff_offset": "3b68c20cb1b4c84524ca3ff529add0a4a8301a65e89737010d66add57e0f6085",
    "tiff_bytecount": "73127703586268c82467f1ee6461b3377cf3ecb535acc8cd3bd0c55eb9c2e768",
    "tiff_strip": "9e1003f381fc224621d88ea901f40a12daadcfa7112b1fe8fc942c68cd8bca5d",
    "zarr_header": "ae3cfe008420624c637d489d4f6faaaf496ddc906a4430f512c7580619540120",
    "zarr_block": "cc8272a08fc242b33123d099a76abec19d6e64f9668b3d3931cc34485a494c0b",
}
LIMITS = {
    "tiff_offset": 4, "tiff_bytecount": 4, "tiff_strip": 2545,
    "zarr_header": 4096, "zarr_block": 23266,
}


class PixelGateError(ValueError):
    """Original byte identity, decoder, alignment or pixel semantics not proven."""


def read_pinned(path: Path, key: str) -> bytes:
    bound = LIMITS[key]
    with path.open("rb") as stream:
        raw = stream.read(bound + 1)
    if len(raw) != bound or hashlib.sha256(raw).hexdigest() != SHA[key]:
        raise PixelGateError(key + ": incomplete, oversized or wrong original-range SHA-256")
    return raw


def tiff_lzw_decode(src: bytes, expected_size: int) -> bytes:
    """Classic TIFF 9-12bit LZW, MSB-first, early-change=1, no Predictor."""
    if type(src) is not bytes or not src or expected_size <= 0:
        raise PixelGateError("invalid LZW input or decoded byte bound")
    bitpos, width, next_code = 0, 9, 258
    dictionary = {i: bytes((i,)) for i in range(256)}
    previous = None
    result = bytearray()
    found_eoi = False
    for _ in range(expected_size * 2 + 64):
        if bitpos + width > len(src) * 8:
            raise PixelGateError("TIFF LZW missing end-of-information code")
        value = 0
        for _bit in range(width):
            value = (value << 1) | ((src[bitpos >> 3] >> (7 - (bitpos & 7))) & 1)
            bitpos += 1
        if value == 256:
            width, next_code = 9, 258
            dictionary = {i: bytes((i,)) for i in range(256)}
            previous = None
            continue
        if value == 257:
            found_eoi = True
            break
        if value in dictionary and value < next_code:
            entry = dictionary[value]
        elif value == next_code and previous is not None:
            entry = previous + previous[:1]
        else:
            raise PixelGateError("unrecognized TIFF LZW code")
        if len(result) + len(entry) > expected_size:
            raise PixelGateError("decoded TIFF row exceeds expected bounded byte count")
        result.extend(entry)
        if previous is not None and next_code < 4096:
            dictionary[next_code] = previous + entry[:1]
            next_code += 1
            if width < 12 and next_code == (1 << width) - 1:
                width += 1
        previous = entry
    if not found_eoi or len(result) != expected_size:
        raise PixelGateError("TIFF LZW did not terminate at the exact row size")
    return bytes(result)


def lz4_raw_decode(src: bytes, expected_size: int) -> bytes:
    """Bounded LZ4 block decoder; no external dependency or network."""
    if type(src) is not bytes or not src or not 0 < expected_size <= 524288:
        raise PixelGateError("invalid bounded LZ4 block")
    out = bytearray()
    cursor = 0
    while cursor < len(src):
        token = src[cursor]
        cursor += 1
        literal_length = token >> 4
        if literal_length == 15:
            while True:
                if cursor >= len(src):
                    raise PixelGateError("truncated LZ4 literal extension")
                inc = src[cursor]
                cursor += 1
                literal_length += inc
                if inc != 255:
                    break
        if cursor + literal_length > len(src) or len(out) + literal_length > expected_size:
            raise PixelGateError("invalid LZ4 literal extent")
        out.extend(src[cursor:cursor + literal_length])
        cursor += literal_length
        if cursor == len(src):
            break
        if cursor + 2 > len(src):
            raise PixelGateError("truncated LZ4 match offset")
        offset = struct.unpack_from("<H", src, cursor)[0]
        cursor += 2
        if not 0 < offset <= len(out):
            raise PixelGateError("invalid LZ4 back-reference")
        match_length = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while True:
                if cursor >= len(src):
                    raise PixelGateError("truncated LZ4 match extension")
                inc = src[cursor]
                cursor += 1
                match_length += inc
                if inc != 255:
                    break
        if len(out) + match_length > expected_size:
            raise PixelGateError("LZ4 output exceeds bounded stream")
        for _ in range(match_length):
            out.append(out[-offset])
    if len(out) != expected_size:
        raise PixelGateError("LZ4 decompressed byte length mismatch")
    return bytes(out)


def decode_blosc_shuffled_block(header: bytes, compressed: bytes) -> tuple[bytes, ...]:
    if len(header) < 16 + 69 * 4:
        raise PixelGateError("missing Blosc header and offset table")
    version, compressor_version, flags, typesize, nbytes, blocksize, cbytes = struct.unpack_from(
        "<BBBBIII", header
    )
    if (version, compressor_version, flags, typesize, nbytes, blocksize, cbytes) != (
        2, 1, 33, 4, ZARR_CHUNK_UNCOMPRESSED, ZARR_BLOCKSIZE, ZARR_CHUNK_COMPRESSED
    ):
        raise PixelGateError("Blosc format/codec/shape changed")
    block_count = (nbytes + blocksize - 1) // blocksize
    offsets = struct.unpack_from("<" + "I" * block_count, header, 16)
    if offsets[1] != ZARR_BLOCK_OFFSET:
        raise PixelGateError("requested Blosc block no longer at pinned offset")
    if any(offset < 16 + block_count * 4 or offset >= cbytes for offset in offsets):
        raise PixelGateError("invalid Blosc block offsets")
    cursor = 0
    parts = []
    for _ in range(typesize):
        if cursor + 4 > len(compressed):
            raise PixelGateError("missing Blosc compressed stream size")
        n = struct.unpack_from("<I", compressed, cursor)[0]
        cursor += 4
        if not 0 < n <= len(compressed) - cursor:
            raise PixelGateError("bad Blosc compressed stream length")
        parts.append(lz4_raw_decode(bytes(compressed[cursor:cursor + n]), blocksize // typesize))
        cursor += n
    if cursor != len(compressed) or len(compressed) != ZARR_BLOCK_LENGTH:
        raise PixelGateError("Blosc block contains extra, missing or unreviewed data")
    return tuple(parts)


def compare_pixels(row: bytes, split_streams: tuple[bytes, ...],
                   first_col: int, ncols: int, local_row: int,
                   chunk_width: int, block_scalar_start: int) -> dict:
    """Compare exact Float32 bytes and independent NaN-category propagation."""
    if len(split_streams) != 4 or len({len(x) for x in split_streams}) != 1:
        raise PixelGateError("expected four equally sized byte-shuffled streams")
    if len(row) % 4 or ncols < 1 or first_col < 0 or first_col + ncols > len(row) // 4:
        raise PixelGateError("unsafe TIFF slice")
    result = {
        "source_nodata_to_derived_nan": 0,
        "source_zero_exact": 0,
        "source_positive_exact": 0,
        "mismatches": 0,
        "other_source_values": 0,
    }
    positive_pairs = []
    for offset in range(ncols):
        source_col = first_col + offset
        i = local_row * chunk_width + offset - block_scalar_start
        if i < 0 or i >= len(split_streams[0]):
            raise PixelGateError("selected Zarr cell outside one verified Blosc block")
        src_bytes = row[source_col * 4:source_col * 4 + 4]
        dst_bytes = bytes(channel[i] for channel in split_streams)
        src = struct.unpack("<f", src_bytes)[0]
        dst = struct.unpack("<f", dst_bytes)[0]
        if src == -9999:
            if math.isnan(dst):
                result["source_nodata_to_derived_nan"] += 1
            else:
                result["mismatches"] += 1
        elif src == 0:
            if src_bytes == dst_bytes:
                result["source_zero_exact"] += 1
            else:
                result["mismatches"] += 1
        elif math.isfinite(src) and src > 0:
            if src_bytes == dst_bytes:
                result["source_positive_exact"] += 1
                positive_pairs.append((source_col, src))
            else:
                result["mismatches"] += 1
        else:
            result["other_source_values"] += 1
            result["mismatches"] += 1
    result["paired_cells"] = ncols
    result["positive_examples"] = [
        {"global_col": col, "depth_m": value} for col, value in positive_pairs[:8]
    ]
    return result


def inspect_original_ranges(inputs: dict[str, bytes]) -> dict:
    if set(inputs) != set(SHA):
        raise PixelGateError("missing original-range artifact")
    for name in SHA:
        data = inputs[name]
        if type(data) is not bytes or len(data) != LIMITS[name]:
            raise PixelGateError("original response length mismatch for " + name)
        if hashlib.sha256(data).hexdigest() != SHA[name]:
            raise PixelGateError("original response SHA-256 mismatch for " + name)
    start = struct.unpack("<I", inputs["tiff_offset"])[0]
    length = struct.unpack("<I", inputs["tiff_bytecount"])[0]
    if (start, length) != (TIF_OFFSET, TIF_STRIP_LENGTH):
        raise PixelGateError("TIFF row offset/length changed")
    row = tiff_lzw_decode(inputs["tiff_strip"], TIF_WIDTH * 4)
    split = decode_blosc_shuffled_block(inputs["zarr_header"], inputs["zarr_block"])
    paired = compare_pixels(
        row, split, FIRST_COL, NCOLS, ROW % 1000, 1000,
        ZARR_BLOCKSIZE // 4, 
    )
    expected = {
        "source_nodata_to_derived_nan": 183,
        "source_zero_exact": 813,
        "source_positive_exact": 4,
        "mismatches": 0,
        "other_source_values": 0,
        "paired_cells": 1000,
    }
    if any(paired[key] != value for key, value in expected.items()):
        raise PixelGateError("real WRI/Physrisk pixel equivalence did not meet pinned outcome")
    return {
        "profile": PROFILE,
        "wri_original_tiff": WRI_URL,
        "physrisk_derived_zarr_chunk": ZARR_URL,
        "wri_source_row": ROW,
        "wri_longitude_pixel_columns": [FIRST_COL, FIRST_COL + NCOLS - 1],
        "physrisk_zarr_chunk_key": "0.7.10",
        "physrisk_blosc_block_index": 1,
        "source_read_only_range_sha256": dict(SHA),
        "counts": paired,
        "original_tiff_strips_sampled": 1,
        "derived_zarr_blocks_sampled": 1,
        "return_period_years_sampled": [2],
        "all_return_periods_verified": False,
        "all_locations_or_tiles_verified": False,
        "published_build_revision_proven": False,
        "annual_stochastic_event_catalogue_present": False,
        "rights_and_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in SHA:
        parser.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = {key: getattr(args, key) for key in SHA}
    resolved = [p.resolve() for p in paths.values()]
    if len(set(resolved)) != len(resolved) or args.out.resolve() in resolved:
        parser.error("refusing duplicate input paths or overwriting original source bytes")
    try:
        evidence = {key: read_pinned(path, key) for key, path in paths.items()}
        receipt = inspect_original_ranges(evidence)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    except (OSError, PixelGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
