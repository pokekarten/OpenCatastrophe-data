# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, offline WGS84 coordinate -> header-derived WorldCover grid cell.

This is an exposure-enrichment *index candidate*, not a raster-pixel
retrieval, observed building footprint, insured exposure or CAT model input.
The only supported source is one already verified ESA v200 N48E009
four-KiB header receipt. Do not accept unverified/other GeoTIFF grids.
"""
from __future__ import annotations

import math
from typing import Any

SOURCE_ID = "esa.worldcover.2021.v200"
TILE_ID = "N48E009"
ORIGINAL_HEADER_SHA256 = "a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529"
BOUNDS_WGS84 = (9.0, 48.0, 12.0, 51.0)
DIMENSION = 36_000
INTERNAL_TILE = 1024
SPACING = 3.0 / DIMENSION
RECEIPT_PROFILE = "oc-esa-worldcover-v200-tiff-header-v0"


class CellIndexBlocked(ValueError):
    """The candidate source/CRS identity or input point is not trustworthy."""


def validate_source_header(receipt: dict[str, Any]) -> None:
    """Check explicit exact original prefix identity and grid contract only."""
    if type(receipt) is not dict or (
        receipt.get("profile") != RECEIPT_PROFILE
        or receipt.get("source_id") != SOURCE_ID
        or receipt.get("tile_id") != TILE_ID
        or receipt.get("sample_sha256") != ORIGINAL_HEADER_SHA256
        or receipt.get("sample_bytes") != 4096
        or receipt.get("geo_grid_verified_from_prefix_only") is not True
        or receipt.get("geokey_geographic_crs_if_complete") != 4326
        or receipt.get("geokey_model_type_if_complete") != 2
        or receipt.get("geokey_raster_type_if_complete") != 1
        or receipt.get("header_tile_bounds_lonlat_if_verified") != list(BOUNDS_WGS84)
        or receipt.get("image_width_if_inline") != DIMENSION
        or receipt.get("image_length_if_inline") != DIMENSION
        or receipt.get("tile_width_if_inline") != INTERNAL_TILE
        or receipt.get("tile_length_if_inline") != INTERNAL_TILE
        or receipt.get("external_bytes_persisted") is not False
        or receipt.get("raster_values_inspected") is not False
        or receipt.get("model_input_approved") is not False
        or receipt.get("full_original_sha256_verified") is not False
    ):
        raise CellIndexBlocked("unsupported or unverified WorldCover 4 KiB source receipt")
    scale = receipt.get("pixel_scale_degrees_if_complete")
    if (type(scale) is not list or len(scale) != 2
            or any(type(v) not in (float, int) or not math.isfinite(v) for v in scale)
            or any(abs(v - SPACING) > 1e-12 for v in scale)):
        raise CellIndexBlocked("source pixel scale is not the frozen verified grid")


def wgs84_lonlat_to_cell(
    receipt: dict[str, Any], longitude: float, latitude: float,
) -> dict[str, Any]:
    """Report row/column and block index, never a land-cover class value.

    WGS84 lon,lat degrees. For PixelIsArea, west/north boundaries are
    inclusive; east/south boundaries exclusive. Out-of-tile inputs are
    explicitly reported without inventing neighboring tile identities.
    """
    validate_source_header(receipt)
    if any(type(v) not in (int, float) or not math.isfinite(v)
           for v in (longitude, latitude)):
        raise CellIndexBlocked("longitude/latitude must be finite WGS84 numbers")
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise CellIndexBlocked("coordinates outside WGS84 world bounds")
    west, south, east, north = BOUNDS_WGS84
    basic = {
        "source": SOURCE_ID,
        "tile": TILE_ID,
        "coordinate_crs": "EPSG:4326",
        "grid_evidence": "exact_4k_header_only",
        "raster_pixel_value_retrieved": False,
        "model_input_approved": False,
    }
    if not (west <= longitude < east and south < latitude <= north):
        return {**basic, "inside_verified_tile": False,
                "pixel_row": None, "pixel_column": None,
                "internal_tile_row": None, "internal_tile_column": None}
    column = math.floor((longitude - west) / SPACING)
    row = math.floor((north - latitude) / SPACING)
    if not (0 <= column < DIMENSION and 0 <= row < DIMENSION):
        # Float rounding at a geographic boundary must not be clamped into
        # a potentially wrong source pixel.
        return {**basic, "inside_verified_tile": False,
                "pixel_row": None, "pixel_column": None,
                "internal_tile_row": None, "internal_tile_column": None}
    return {
        **basic, "inside_verified_tile": True,
        "pixel_row": row, "pixel_column": column,
        "internal_tile_row": row // INTERNAL_TILE,
        "internal_tile_column": column // INTERNAL_TILE,
        "row_within_internal_tile": row % INTERNAL_TILE,
        "column_within_internal_tile": column % INTERNAL_TILE,
    }
