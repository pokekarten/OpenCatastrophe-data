#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Third real-source WRI/Physrisk 1,000-cell comparison: Europe North Sea, 100y.

Read only externally captured, tiny exact HTTP Range byte files from original
WRI GeoTIFF and derived Physrisk Zarr. Never downloads, copies raster assets
into Git, assumes global validity, or admits models/insurance losses.
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

PROFILE = "wri-physrisk-coastal-europe-rp100-third-paired-proof-v0"
WRI_URL = ("https://aqueduct.wridata.org/AqueductFloods20/"
           "inuncoast_historical_nosub_hist_rp0100_0.tif")
PHYSRISK_URL = (
    "https://os-climate-physical-risk.s3.amazonaws.com/"
    "hazard-indicators/hazard.zarr/inundation/wri/v2/"
    "inuncoast_historical_nosub_hist_0/0.4.22"
)
GLOBAL_ROW = 4560
FIRST_COL = 22000
COLS = 1000
PERIOD_YEARS = 100
PERIOD_INDEX = 5
CHUNK_KEY = "0.4.22"
CHUNK_LOCAL_ROW = 560
BLOSC_BLOCK_INDEX = 42
BLOSC_BLOCK_BEGIN = 1118968
BLOSC_BLOCK_END = 1169976
SOURCE_TIFF_STRIP_BEGIN = 9532356
SOURCE_TIFF_STRIP_LENGTH = 2717
HEADER_LENGTH = 4096
EXPECTED_COMPRESSED_OBJECT_BYTES = 1751433
EXPECTED_RAW_CHUNK_BYTES = 36000000
SINGLE_BLOSC_BLOCK_DECODED_BYTES = 524288
WRI_WIDTH = 43200

# Source URL, original inclusive HTTP range, independently pinned SHA-256.
# No third-party source bytes appear in code or tests.
SOURCES = {
    "wri_row_offset": (
        WRI_URL, 46314334, 46314337,
        "e0566cbf3b0a881e353c75e0ac62b41d391941947f8aa85fd5b93f4814d9e01b",
    ),
    "wri_row_length": (
        WRI_URL, 46227934, 46227937,
        "4079d31186209119f8b7d75a5375b4db0991f7e149e621c6369ddc422f749f8f",
    ),
    "wri_strip": (
        WRI_URL, SOURCE_TIFF_STRIP_BEGIN,
        SOURCE_TIFF_STRIP_BEGIN + SOURCE_TIFF_STRIP_LENGTH - 1,
        "aa32aef31052fadef112ab337c0c609f085965e8a7ad4eabdfd0e3e4e0e0f911",
    ),
    "zarr_header": (
        PHYSRISK_URL, 0, HEADER_LENGTH - 1,
        "c1fa76465612674450949a993c2ce31ffcbfc3cb2ee8b5d3d9dc1d828f81432d",
    ),
    "zarr_part0": (
        PHYSRISK_URL, BLOSC_BLOCK_BEGIN, BLOSC_BLOCK_BEGIN + 30000 - 1,
        "cd154830e94a6a5bb6d96b35b55868fa6c2029635c3cbe589bceb2eb45793068",
    ),
    "zarr_part1": (
        PHYSRISK_URL, BLOSC_BLOCK_BEGIN + 30000, BLOSC_BLOCK_END - 1,
        "6cfb0ea208674c0455faafe5a1f6b675ff8b59c1a9f39252ee13c66b46cf9609",
    ),
}


def read_original(path: Path, key: str) -> bytes:
    if key not in SOURCES:
        raise PixelGateError("unexpected original-source key")
    _url, begin, end, digest = SOURCES[key]
    size = end - begin + 1
    if not 0 < size <= 40000:
        raise PixelGateError("original source range exceeds the strictly bounded limit")
    with path.open("rb") as stream:
        raw = stream.read(size + 1)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise PixelGateError(key + ": original source range incomplete or SHA256 changed")
    return raw


def split_original_blosc(header: bytes, payload: bytes) -> tuple[bytes, ...]:
    if len(header) != HEADER_LENGTH or len(payload) != BLOSC_BLOCK_END - BLOSC_BLOCK_BEGIN:
        raise PixelGateError("wrong Zarr compressed header/block lengths")
    ver, codec_ver, flags, width, nbytes, blocksize, cbytes = struct.unpack_from(
        "<BBBBIII", header
    )
    if (ver, codec_ver, flags, width, nbytes, blocksize, cbytes) != (
            2, 1, 33, 4, EXPECTED_RAW_CHUNK_BYTES,
            SINGLE_BLOSC_BLOCK_DECODED_BYTES, EXPECTED_COMPRESSED_OBJECT_BYTES):
        raise PixelGateError("original Zarr block codec/format/header changed")
    nblocks = (nbytes + blocksize - 1) // blocksize
    if nblocks != 69 or len(header) < 16 + nblocks * 4:
        raise PixelGateError("unexpected chunk block count")
    offsets = struct.unpack_from("<" + "I" * nblocks, header, 16)
    if len(set(offsets)) != nblocks:
        raise PixelGateError("duplicate compressed Zarr block offsets")
    if any(x < 16 + nblocks * 4 or x >= cbytes for x in offsets):
        raise PixelGateError("invalid compressed Zarr block offset")
    selected = offsets[BLOSC_BLOCK_INDEX]
    following = min((x for x in offsets if x > selected), default=cbytes)
    if (selected, following) != (BLOSC_BLOCK_BEGIN, BLOSC_BLOCK_END):
        raise PixelGateError("original Zarr block byte boundaries changed")
    scalar_start = PERIOD_INDEX * 1000000 + CHUNK_LOCAL_ROW * 1000
    scalar_end = scalar_start + COLS - 1
    if scalar_start // (blocksize // 4) != BLOSC_BLOCK_INDEX or (
            scalar_end // (blocksize // 4) != BLOSC_BLOCK_INDEX):
        raise PixelGateError("sample row does not fit selected compressed block")
    at = 0
    streams = []
    for _ in range(width):
        if at + 4 > len(payload):
            raise PixelGateError("compressed stream length missing")
        size = struct.unpack_from("<I", payload, at)[0]
        at += 4
        if not 0 < size <= len(payload) - at:
            raise PixelGateError("compressed stream length invalid")
        streams.append(lz4_raw_decode(payload[at:at+size], blocksize // width))
        at += size
    if at != len(payload):
        raise PixelGateError("unreviewed bytes remain after compressed stream decoding")
    return tuple(streams)


def inspect_range_pair(inputs: dict[str, bytes]) -> dict:
    if set(inputs) != set(SOURCES):
        raise PixelGateError("missing/replaced original HTTP source response")
    for key, original in inputs.items():
        _url, start, end, digest = SOURCES[key]
        if type(original) is not bytes or len(original) != end-start+1:
            raise PixelGateError(key + ": original source length invalid")
        if hashlib.sha256(original).hexdigest() != digest:
            raise PixelGateError(key + ": original source SHA256 invalid")
    original_offset = struct.unpack("<I", inputs["wri_row_offset"])[0]
    original_size = struct.unpack("<I", inputs["wri_row_length"])[0]
    if (original_offset, original_size) != (
            SOURCE_TIFF_STRIP_BEGIN, SOURCE_TIFF_STRIP_LENGTH):
        raise PixelGateError("WRI original strip pointer/size changed")
    raw_row = tiff_lzw_decode(inputs["wri_strip"], WRI_WIDTH * 4)
    block = inputs["zarr_part0"] + inputs["zarr_part1"]
    streams = split_original_blosc(inputs["zarr_header"], block)
    comparison = compare_pixels(
        raw_row, streams, FIRST_COL, COLS,
        PERIOD_INDEX * 1000 + CHUNK_LOCAL_ROW, 1000,
        BLOSC_BLOCK_INDEX * (SINGLE_BLOSC_BLOCK_DECODED_BYTES // 4),
    )
    exact = {
        "source_nodata_to_derived_nan": 93,
        "source_zero_exact": 819,
        "source_positive_exact": 88,
        "mismatches": 0,
        "other_source_values": 0,
        "paired_cells": COLS,
    }
    if any(comparison[key] != value for key, value in exact.items()):
        raise PixelGateError("third European original-to-derived 100y pair failed")
    return {
        "profile": PROFILE,
        "WRI_original_TIFF": WRI_URL,
        "Physrisk_derived_Zarr": PHYSRISK_URL,
        "global_row": GLOBAL_ROW,
        "global_col_first": FIRST_COL,
        "global_col_last": FIRST_COL + COLS - 1,
        "return_period_years": PERIOD_YEARS,
        "return_period_index": PERIOD_INDEX,
        "Zarr_chunk_key": CHUNK_KEY,
        "Zarr_block_index": BLOSC_BLOCK_INDEX,
        "original_http_range_evidence": {
            key: {"byte_range_inclusive": [source[1], source[2]], "sha256": source[3]}
            for key, source in SOURCES.items()
        },
        "comparison": comparison,
        "all_locations_verified": False,
        "all_return_periods_original_tiff_verified": False,
        "producer_build_commit_verified": False,
        "global_hazard_science_and_rights_review_complete": False,
        "physical_events_and_insured_losses_present": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in SOURCES:
        parser.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = {key: getattr(args, key) for key in SOURCES}
    sources = [p.resolve() for p in paths.values()]
    if len(set(sources)) != len(paths) or args.out.resolve() in sources:
        parser.error("source input paths must be independent and never overwritten")
    try:
        original = {key: read_original(file, key) for key, file in paths.items()}
        receipt = inspect_range_pair(original)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    except (OSError, PixelGateError) as error:
        print("BLOCKED: "+str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
