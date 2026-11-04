#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original WRI historical riverine RP100 *one-row* Bavaria-window source proof.

Reads only three externally captured, independently SHA-256-pinned original
Aqueduct GeoTIFF HTTP Range responses; no network, raw data output, protected
building join, defence corrections, source admission or CAT loss calculations.
The related six original TIFF profile byte ranges are pinned/checked by the
wri_bavaria_riverine_defence_spatial_candidate_v0.py metadata gate.
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
    PixelGateError, tiff_lzw_decode,
)
from research_runners.wri_bavaria_riverine_defence_spatial_candidate_v0 import (
    RIVERINE_ORIGINAL, WIDTH,
)

PROFILE = "wri-riverine-bavaria-real-100yr-554-cell-one-row-v0"
ROW = 5000
COLUMNS = (22684, 23237)  # inclusive; only the LfU source bbox longitude span
SOURCE_STRIP_OFFSET = 28730421
SOURCE_COMPRESSED_BYTES = 6541
RANGES = {
    "offset": (92095742, 92095745,
               "a12803f9f96d7240493012204aa9c94c0f0b6663693443f8204e44a0262f6b15"),
    "bytecount": (92009342, 92009345,
                  "aded26cfbb510c2b40c76ebbba6034131b1a38780768eea915b9cef81fa6609e"),
    "strip": (SOURCE_STRIP_OFFSET, SOURCE_STRIP_OFFSET+SOURCE_COMPRESSED_BYTES-1,
              "35b4e90ec28ef3fbc5794ebf6bf1f9854b303571e108d47033102728e0c1becc"),
}


def read_pinned(path: Path, key: str) -> bytes:
    if key not in RANGES:
        raise PixelGateError("unknown WRI original range part")
    begin, end, digest = RANGES[key]
    limit = end - begin + 1
    with path.open("rb") as stream:
        result = stream.read(limit + 1)
    if len(result) != limit or hashlib.sha256(result).hexdigest() != digest:
        raise PixelGateError("original source range changed, truncated or oversized")
    return result


def summarize_row_5000(raw_float32: bytes) -> dict:
    if type(raw_float32) is not bytes or len(raw_float32) != WIDTH * 4:
        raise PixelGateError("WRI original decoded Float32 row must be exactly 172800 bytes")
    values = struct.unpack_from("<" + "f"*WIDTH, raw_float32)
    picked = values[COLUMNS[0]:COLUMNS[1]+1]
    nodata = sum(v == -9999 for v in picked)
    zero = sum(v == 0 for v in picked)
    positive = [v for v in picked if v > 0 and math.isfinite(v)]
    invalid = len(picked) - nodata - zero - len(positive)
    return {
        "world_grid_row": ROW,
        "global_col_first": COLUMNS[0],
        "global_col_last": COLUMNS[1],
        "sampled_raster_pixels": len(picked),
        "nodata": nodata,
        "finite_zero_depths": zero,
        "finite_positive_depths": len(positive),
        "other_invalid_values": invalid,
        "minimum_positive_depth_metres": min(positive) if positive else None,
        "maximum_positive_depth_metres": max(positive) if positive else None,
        "raster_row_centre_latitude_degrees": 90-(ROW+.5)/120,
        "longitude_range_of_pixel_centres_degrees": [
            -180+(COLUMNS[0]+.5)/120,
            -180+(COLUMNS[1]+.5)/120,
        ],
    }


def inspect_original_source_ranges(inputs: dict[str, bytes]) -> dict:
    if set(inputs) != set(RANGES):
        raise PixelGateError("missing original riverine row source ranges")
    for key, data in inputs.items():
        start, end, digest = RANGES[key]
        if type(data) is not bytes or len(data) != end-start+1 or (
                hashlib.sha256(data).hexdigest() != digest):
            raise PixelGateError("original WRI row range SHA256 or extent mismatch")
    source_pointer = struct.unpack("<I", inputs["offset"])[0]
    source_length = struct.unpack("<I", inputs["bytecount"])[0]
    if source_pointer != SOURCE_STRIP_OFFSET or source_length != SOURCE_COMPRESSED_BYTES:
        raise PixelGateError("TIFF source IFD strip index/length differs")
    row = tiff_lzw_decode(inputs["strip"], WIDTH*4)
    stats = summarize_row_5000(row)
    if (stats["sampled_raster_pixels"] != 554
            or stats["nodata"] != 0
            or stats["finite_zero_depths"] != 529
            or stats["finite_positive_depths"] != 25
            or stats["other_invalid_values"] != 0
            or not math.isclose(stats["maximum_positive_depth_metres"],
                                1.1153450012207031, rel_tol=0, abs_tol=1e-7)
            or not math.isclose(stats["minimum_positive_depth_metres"],
                                0.11534500122070312, rel_tol=0, abs_tol=1e-7)):
        raise PixelGateError("actual riverine Bavaria row intensity categories drifted")
    return {
        "profile": PROFILE,
        "provider": "World Resources Institute",
        "original_riverine_GeoTIFF": RIVERINE_ORIGINAL,
        "source_return_period_years": 100,
        "source_model": "historical WATCH 1980 riverine, not coastal",
        "original_range_evidence": {
            key: {"inclusive_bytes": [value[0], value[1]],
                  "sha256": value[2]} for key, value in RANGES.items()
        },
        "comparison": stats,
        "all_hazard_raster_rows_verified": False,
        "defence_geometry_actual_pixel_join_completed": False,
        "specific_building_depth_or_flood_probability_determined": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offset", type=Path, required=True)
    parser.add_argument("--bytecount", type=Path, required=True)
    parser.add_argument("--strip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    sources = {"offset": args.offset, "bytecount": args.bytecount, "strip": args.strip}
    if (len({p.resolve() for p in sources.values()}) != len(sources)
            or args.out.resolve() in {p.resolve() for p in sources.values()}):
        parser.error("all source HTTP ranges must be different and may not be overwritten")
    try:
        proof = inspect_original_source_ranges({
            key: read_pinned(p, key) for key, p in sources.items()
        })
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(proof, sort_keys=True, indent=2)+"\n",
                            encoding="utf-8")
    except (OSError, PixelGateError) as exc:
        print("BLOCKED: "+str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
