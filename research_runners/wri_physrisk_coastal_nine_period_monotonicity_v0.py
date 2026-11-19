#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, OFFLINE nine-return-period monotonicity check on one Physrisk chunk.

All nine source responses are bounded HTTP ranges captured separately outside
Git; SHA-256 is independently pinned. Nothing here proves global monotonicity,
full-object version, rights, an annual event catalogue, a loss model or an
approved NextGen data input. No network, map export or source byte persistence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from research_runners.wri_physrisk_coastal_paired_strip_preflight_v0 import (
    PixelGateError, lz4_raw_decode,
)

PROFILE = "physrisk-wri-coastal-nine-return-period-monotonicity-v0"
ZARR_URL = (
    "https://os-climate-physical-risk.s3.amazonaws.com/"
    "hazard-indicators/hazard.zarr/inundation/wri/v2/"
    "inuncoast_historical_nosub_hist_0/0.8.32"
)
PERIODS = (2, 5, 10, 25, 50, 100, 250, 500, 1000)
GLOBAL_ROW = 8100
GLOBAL_COLS = (32000, 32999)
LOCAL_ROW = GLOBAL_ROW % 1000
SAMPLE_COUNT = 1000
BLOCK_SCALARS = 524288 // 4
ORIGINAL_HEADER_BYTES = 4096
ORIGINAL_HEADER_SHA256 = "d0d1abe763ca50acc59706516a12d744d359d81c235d0ba1b9c0e1fa4b8dfad8"
OBJECT_COMPRESSED_BYTES = 2375870
OBJECT_UNCOMPRESSED_BYTES = 36000000

# Period -> (Blosc block index, inclusive offset, exclusive end, original SHA256).
# The full compressed block SHA is valid even if acquired in bounded smaller
# HTTP Range parts and concatenated outside Git in ascending-offset order.
BLOCKS = {
    2: (0, 81215, 127557, "045b4f5a6d7967e66e0ae44d34f926f5ec2b1062bbdac0cbe0d92fee4fddca7e"),
    5: (8, 390129, 499232, "79ed33e93d9a2c7dcfbc49b152609bce9bddab2987c908f0691c12dda72b688a"),
    10: (16, 519441, 632669, "343c1dd325eed5af633a50638f7f7a272c0075381874fd9951f435ff0d63383f"),
    25: (23, 798336, 912378, "2c3a6eb4ddbea6c19da6f65b4d0037630bc7889c2903dd361f48f3bc14aecf7e"),
    50: (31, 1088543, 1242360, "71980e6dc36f4735d895be13e1ab8bb9e1fd89b8f7528a8ad98c16d2951ce7f0"),
    100: (38, 1380254, 1466009, "9144355508425d0f703c309d28e919c019ca4c52841ec2e000e3c69849a5d8f5"),
    250: (46, 1657387, 1804363, "c8d36d83d2ba920a458e1e4cb54db46dfcde10c1b37a81c7e8d3869b4f9ced38"),
    500: (54, 1950955, 2110962, "2ed7f66bb72a72d604ca6e9027c09ba69e536fddaa7d7b7507745e0c1bbe3f7f"),
    1000: (61, 2256526, 2375870, "7bf594f62bc4e9c7e26311869df19188a2e77f7a72f4487dda0a5c6c26837d0d"),
}
POSITIVE_EXPECTED = (110, 213, 252, 288, 312, 334, 357, 368, 378)
NAN_EXPECTED = 72


def read_pinned(path: Path, byte_length: int, expected_sha256: str) -> bytes:
    """Reject any changed, incomplete or oversized original response file."""
    if not 0 < byte_length <= 200000:
        raise PixelGateError("invalid pinned source range length")
    with path.open("rb") as source:
        data = source.read(byte_length + 1)
    if len(data) != byte_length or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise PixelGateError("original HTTP range byte count / SHA-256 mismatch")
    return data


def verify_blosc_header(header: bytes) -> None:
    if len(header) != ORIGINAL_HEADER_BYTES:
        raise PixelGateError("bounded original Blosc header has wrong length")
    if hashlib.sha256(header).hexdigest() != ORIGINAL_HEADER_SHA256:
        raise PixelGateError("Blosc header original SHA-256 mismatch")
    original = struct.unpack_from("<BBBBIII", header)
    if original != (2, 1, 33, 4, OBJECT_UNCOMPRESSED_BYTES, 524288,
                    OBJECT_COMPRESSED_BYTES):
        raise PixelGateError("original Blosc codec, dimensions or shuffle changed")
    nblocks = (OBJECT_UNCOMPRESSED_BYTES + 524288 - 1) // 524288
    if nblocks != 69 or len(header) < 16 + nblocks * 4:
        raise PixelGateError("Blosc block table incompatible with original array")
    offsets = struct.unpack_from("<" + "I" * nblocks, header, 16)
    if len(set(offsets)) != nblocks or any(
            pos < 16 + nblocks * 4 or pos >= OBJECT_COMPRESSED_BYTES for pos in offsets):
        raise PixelGateError("invalid Blosc chunk block offsets")
    for i, rp in enumerate(PERIODS):
        block, start, stop, _sha = BLOCKS[rp]
        first = i * 1000000 + LOCAL_ROW * 1000
        last = first + SAMPLE_COUNT - 1
        if first // BLOCK_SCALARS != block or last // BLOCK_SCALARS != block:
            raise PixelGateError("selected local sample crosses unexpected Blosc blocks")
        if offsets[block] != start:
            raise PixelGateError(f"Blosc block offset changed for {rp}-year")
        following = min((pos for pos in offsets if pos > start), default=OBJECT_COMPRESSED_BYTES)
        if following != stop:
            raise PixelGateError(f"Blosc block byte extent changed for {rp}-year")


def decode_blosc_block(block: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    """Four bounded LZ4 byte-shuffle streams, each exactly 131072 bytes."""
    pos = 0
    streams = []
    for _ in range(4):
        if pos + 4 > len(block):
            raise PixelGateError("missing original Blosc compressed stream length")
        compressed_len = struct.unpack_from("<I", block, pos)[0]
        pos += 4
        if compressed_len <= 0 or pos + compressed_len > len(block):
            raise PixelGateError("invalid bounded Blosc LZ4 stream")
        streams.append(lz4_raw_decode(block[pos:pos+compressed_len], BLOCK_SCALARS))
        pos += compressed_len
    if pos != len(block):
        raise PixelGateError("unreviewed bytes trailing compressed Blosc streams")
    return tuple(streams)  # type: ignore[return-value]


def sample_values(streams: tuple[bytes, bytes, bytes, bytes],
                  period_index: int, block_index: int) -> list[float]:
    scalar_first = period_index * 1000000 + LOCAL_ROW * 1000
    local = scalar_first - block_index * BLOCK_SCALARS
    if local < 0 or local + SAMPLE_COUNT > BLOCK_SCALARS:
        raise PixelGateError("sample is not fully covered by the proven source block")
    if len(streams) != 4 or any(len(s) != BLOCK_SCALARS for s in streams):
        raise PixelGateError("missing or partial Blosc byte-shuffle stream")
    values = []
    for i in range(SAMPLE_COUNT):
        f32_bytes = bytes(stream[local + i] for stream in streams)
        values.append(struct.unpack("<f", f32_bytes)[0])
    return values


def summarize_monotonicity(period_values: dict[int, list[float]]) -> dict:
    if tuple(sorted(period_values)) != PERIODS:
        raise PixelGateError("missing, duplicated or extra return period")
    for rp in PERIODS:
        if len(period_values[rp]) != SAMPLE_COUNT:
            raise PixelGateError("different source pixel population across return periods")
    period_stats = []
    for rp in PERIODS:
        values = period_values[rp]
        nan = sum(math.isnan(x) for x in values)
        zero = sum(x == 0 for x in values)
        positive = sum(x > 0 and math.isfinite(x) for x in values)
        nonphysical = SAMPLE_COUNT - nan - zero - positive
        period_stats.append({
            "return_period_years": rp,
            "finite_zero": zero, "finite_positive": positive,
            "nan_nodata": nan, "invalid_negative_or_infinite": nonphysical,
        })
    transitions = []
    for before, after in zip(PERIODS, PERIODS[1:]):
        old, new = period_values[before], period_values[after]
        result = {"from_years": before, "to_years": after,
                  "finite_pairs": 0, "increasing": 0, "equal": 0,
                  "decreasing": 0, "both_nan": 0,
                  "nan_to_finite": 0, "finite_to_nan": 0,
                  "most_negative_delta_m": 0.0}
        for a, b in zip(old, new):
            if math.isnan(a) and math.isnan(b):
                result["both_nan"] += 1
            elif math.isnan(a):
                result["nan_to_finite"] += 1
            elif math.isnan(b):
                result["finite_to_nan"] += 1
            else:
                result["finite_pairs"] += 1
                if b > a:
                    result["increasing"] += 1
                elif b == a:
                    result["equal"] += 1
                else:
                    result["decreasing"] += 1
                    result["most_negative_delta_m"] = min(
                        result["most_negative_delta_m"], b - a)
        transitions.append(result)
    complete = sum(
        all(math.isfinite(period_values[rp][col]) for rp in PERIODS)
        for col in range(SAMPLE_COUNT)
    )
    always_missing = sum(
        all(math.isnan(period_values[rp][col]) for rp in PERIODS)
        for col in range(SAMPLE_COUNT)
    )
    return {
        "per_period": period_stats, "adjacent_transitions": transitions,
        "complete_nine_period_finite_columns": complete,
        "missing_in_all_nine_periods": always_missing,
        "unresolved_mixed_missing_columns": SAMPLE_COUNT - complete - always_missing,
        "total_adjacent_finite_comparisons": sum(x["finite_pairs"] for x in transitions),
        "total_adjacent_both_nan": sum(x["both_nan"] for x in transitions),
        "total_decreasing": sum(x["decreasing"] for x in transitions),
        "total_nan_to_finite": sum(x["nan_to_finite"] for x in transitions),
        "total_finite_to_nan": sum(x["finite_to_nan"] for x in transitions),
        "positive_depth_m_at_global_col_32146": [
            period_values[rp][146] for rp in PERIODS
        ],
    }


def require_exact_original_observations(stats: dict) -> None:
    for i, item in enumerate(stats["per_period"]):
        if (item["return_period_years"] != PERIODS[i]
                or item["nan_nodata"] != NAN_EXPECTED
                or item["finite_positive"] != POSITIVE_EXPECTED[i]
                or item["finite_zero"] != 928 - POSITIVE_EXPECTED[i]
                or item["invalid_negative_or_infinite"] != 0):
            raise PixelGateError("original per-period finite/NoData population drift")
    for i, item in enumerate(stats["adjacent_transitions"]):
        if (item["from_years"] != PERIODS[i]
                or item["to_years"] != PERIODS[i + 1]
                or item["finite_pairs"] != 928
                or item["both_nan"] != NAN_EXPECTED
                or item["decreasing"] != 0
                or item["nan_to_finite"] != 0
                or item["finite_to_nan"] != 0
                or item["increasing"] != POSITIVE_EXPECTED[i + 1]
                or item["equal"] != 928 - POSITIVE_EXPECTED[i + 1]):
            raise PixelGateError("actual adjacent return-period monotonicity or mask drift")
    if (stats["complete_nine_period_finite_columns"] != 928
            or stats["missing_in_all_nine_periods"] != NAN_EXPECTED
            or stats["unresolved_mixed_missing_columns"] != 0
            or stats["total_adjacent_finite_comparisons"] != 7424
            or stats["total_adjacent_both_nan"] != 576
            or stats["total_decreasing"] != 0):
        raise PixelGateError("original nine-period sample population not coherent")


def inspect_bounded_originals(header: bytes, blocks: dict[int, bytes]) -> dict:
    verify_blosc_header(header)
    if tuple(sorted(blocks)) != PERIODS:
        raise PixelGateError("need exactly nine independently pinned compressed blocks")
    values = {}
    for i, rp in enumerate(PERIODS):
        block_index, start, stop, sha = BLOCKS[rp]
        blob = blocks[rp]
        if type(blob) is not bytes or len(blob) != stop - start:
            raise PixelGateError("wrong original Blosc block length")
        if hashlib.sha256(blob).hexdigest() != sha:
            raise PixelGateError("original Blosc block SHA-256 mismatch")
        values[rp] = sample_values(decode_blosc_block(blob), i, block_index)
    results = summarize_monotonicity(values)
    require_exact_original_observations(results)
    return {
        "profile": PROFILE,
        "source": ZARR_URL,
        "sample_global_row": GLOBAL_ROW,
        "sample_global_cols": list(GLOBAL_COLS),
        "return_period_years": list(PERIODS),
        "header_original_sha256": ORIGINAL_HEADER_SHA256,
        "compressed_block_evidence": [
            {"rp_years": rp, "blosc_block_index": BLOCKS[rp][0],
             "original_inclusive_http_range": [BLOCKS[rp][1], BLOCKS[rp][2] - 1],
             "original_range_sha256": BLOCKS[rp][3]}
            for rp in PERIODS
        ],
        "results": results,
        "other_locations_or_chunks_verified": False,
        "original_WRI_GeoTIFF_monotonicity_verified": False,
        "WRI_1p5_year_period_present_in_derived_array": False,
        "event_catalogue_or_annual_losses_present": False,
        "global_hazard_model_calibration_approved": False,
        "rights_or_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zarr-header", type=Path, required=True)
    for rp in PERIODS:
        parser.add_argument(f"--rp-{rp}", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = [args.zarr_header] + [getattr(args, f"rp_{rp}") for rp in PERIODS]
    if len({p.resolve() for p in paths}) != len(paths) or args.out.resolve() in {
            p.resolve() for p in paths}:
        parser.error("all original source files must be distinct and may not be overwritten")
    try:
        header = read_pinned(args.zarr_header, ORIGINAL_HEADER_BYTES, ORIGINAL_HEADER_SHA256)
        blocks = {rp: read_pinned(
            getattr(args, f"rp_{rp}"), BLOCKS[rp][2] - BLOCKS[rp][1], BLOCKS[rp][3]
        ) for rp in PERIODS}
        receipt = inspect_bounded_originals(header, blocks)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    except (OSError, PixelGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
