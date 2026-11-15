#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, aggregate-only GHS-AGE R2025A 1km *coarse* pixel-window QA.

Input: externally projected single-band UInt8 pixel bytes plus metadata from a
separately trusted raster reader. The digest authenticates this small window
ONLY against the caller's expected digest; it is NOT a full JRC ZIP/TIFF hash
or an independent original-source identity. No network, GIS data, coordinates,
real provider pixels, or model input admission is provided by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE_ID = "ec-jrc.ghsl.ghs-age.r2025a"
PRODUCT = "GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0"
TIFF_MEMBER = PRODUCT + ".tif"
WINDOW_MAX_SIDE = 32
WINDOW_MAX_PIXELS = 1024
META_FIELDS = frozenset((
    "product_id", "raster_member", "crs_identifier", "data_type",
    "band_count", "window_width", "window_height", "pixel_width_m",
    "pixel_height_m", "rotation_x", "rotation_y", "declared_nodata",
))


class GHSAGEBlocked(ValueError):
    """A bounded, scientifically unadmitted sample failed the safety gate."""


def _exact_number(value, expected: float) -> bool:
    return (type(value) in (int, float)
            and math.isfinite(value) and value == expected)


def inspect_window(pixels: bytes, metadata: dict, expected_sha256: str) -> dict:
    """Check byte-aligned UInt8 age codes and exact source-scoped grid metadata.

    No GDAL/geographic or JRC asset provenance is checked in this stage.
    A caller-provided hash alone cannot establish original source identity.
    """
    if (type(metadata) is not dict or set(metadata) != META_FIELDS
            or type(pixels) is not bytes):
        raise GHSAGEBlocked("incorrect sample input shape")
    if (metadata["product_id"] != PRODUCT
            or metadata["raster_member"] != TIFF_MEMBER):
        raise GHSAGEBlocked("coarse 1km version or raster member mismatch")
    if metadata["crs_identifier"] != "ESRI:54009":
        raise GHSAGEBlocked("GHS-AGE raster must be World Mollweide")
    if metadata["data_type"] != "UInt8" or type(metadata["band_count"]) is not int
            or metadata["band_count"] != 1):
        raise GHSAGEBlocked("GHS-AGE raster must be one UInt8 band")
    width, height = metadata["window_width"], metadata["window_height"]
    if (type(width) is not int or type(height) is not int
            or not 1 <= width <= WINDOW_MAX_SIDE
            or not 1 <= height <= WINDOW_MAX_SIDE
            or width * height > WINDOW_MAX_PIXELS
            or len(pixels) != width * height):
        raise GHSAGEBlocked("window is oversized or byte count differs")
    if not (_exact_number(metadata["pixel_width_m"], 1000)
            and _exact_number(metadata["pixel_height_m"], -1000)
            and _exact_number(metadata["rotation_x"], 0)
            and _exact_number(metadata["rotation_y"], 0)):
        raise GHSAGEBlocked("GHS-AGE 1km pixel grid/resolution mismatch")
    # The authoritative product classes are 0..5. A separately extracted
    # nodata=255 declaration can be represented without equating 0 to missing.
    # This DOES NOT verify the original TIFF NoData tag independently.
    nodata = metadata["declared_nodata"]
    if nodata is not None and (type(nodata) is not int or nodata != 255):
        raise GHSAGEBlocked("unreviewed or class-colliding NoData value")
    if (type(expected_sha256) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)):
        raise GHSAGEBlocked("missing exact local window checksum")
    digest = hashlib.sha256(pixels).hexdigest()
    if digest != expected_sha256:
        raise GHSAGEBlocked("local projected pixel-window SHA mismatch")
    counts = [0] * 6
    missing = 0
    for code in pixels:
        if code <= 5:
            counts[code] += 1
        elif code == 255 and nodata == 255:
            missing += 1
        else:
            raise GHSAGEBlocked("unknown age class or unverified NoData")
    if sum(counts) + missing != len(pixels):
        raise GHSAGEBlocked("inconsistent categorical raster total")
    return {
        "source_id": SOURCE_ID,
        "profile": "ghsl-age-r2025a-coarse-1km-offline-pixel-window-v0",
        "exact_product": PRODUCT,
        "crs_from_supplied_metadata": "ESRI:54009",
        "nominal_pixel_size_metres": 1000,
        "class_codes": [0, 1, 2, 3, 4, 5],
        "class_counts": {str(k): v for k, v in enumerate(counts)},
        "not_built_up_cells_class_zero": counts[0],
        "built_stock_age_class_cells_1_to_5": sum(counts[1:]),
        "declared_nodata_cells": missing,
        "declared_nodata_from_external_metadata_not_independently_verified":
            nodata is not None,
        "window_cell_count": len(pixels),
        "window_sha256": digest,
        "window_sha256_matches_caller_provided_digest": True,
        "original_zip_sha256_independently_verified": False,
        "original_tiff_sha256_independently_verified": False,
        "raster_georeferencing_independently_verified": False,
        "raster_pixels_proven_original_jrc": False,
        "full_global_raster_coverage_verified": False,
        "window_is_statistically_representative": False,
        "individual_building_construction_year_verified": False,
        "CAT_model_input_approved": False,
        "source_cells_coordinates_or_policy_values_exported": False,
    }


def _unique_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GHSAGEBlocked("duplicate metadata JSON field")
        result[key] = value
    return result


def _reject_constant(_):
    raise GHSAGEBlocked("nonfinite metadata constant")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-bytes", type=Path, required=True)
    parser.add_argument("--metadata-json", type=Path, required=True)
    parser.add_argument("--window-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if (args.window_bytes.is_symlink() or args.metadata_json.is_symlink()
                or not args.window_bytes.is_file()
                or not args.metadata_json.is_file()):
            raise GHSAGEBlocked("unsafe or absent local file")
        with args.window_bytes.open("rb") as fp:
            pixels = fp.read(WINDOW_MAX_PIXELS + 1)
        with args.metadata_json.open("rb") as fp:
            metadata_raw = fp.read(4097)
        if len(metadata_raw) > 4096:
            raise GHSAGEBlocked("metadata JSON oversized")
        metadata = json.loads(metadata_raw.decode("utf-8"),
                              object_pairs_hook=_unique_json_pairs,
                              parse_constant=_reject_constant)
        result = inspect_window(pixels, metadata, args.window_sha256)
    except (GHSAGEBlocked, OSError, UnicodeError, ValueError, RecursionError):
        print("BLOCKED: unverified GHS-AGE 1km coarse pixel window", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
