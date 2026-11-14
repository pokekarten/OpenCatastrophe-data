# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline positional comparison of *separately* decoded JRC Occurrence windows.

A GeoTIFF byte (255 = NoData) and an Earth Engine mask (0 = invalid,
nonzero = valid, possibly fractional) are different representations.
This routine never fetches datasets, assumes geospatial co-registration,
changes mask weights, or claims corrected-source/model-input provenance.
"""
from __future__ import annotations

import hashlib
import math

SOURCE_ID = "ec-jrc.global-surface-water.1984-2024"
GEE_ASSET = "projects/global-surface-water/assets/GSW1_5/Occurrence"
MAX_PIXELS = 65_536


class JRCWindowComparisonBlocked(ValueError):
    """Invalid, ambiguous or non-native raster/window representation."""


def compare_native_occurrence_windows(
    geotiff_occurrence: bytes,
    earth_engine_occurrence: list[int | float | None] | tuple[int | float | None, ...],
    earth_engine_mask: list[int | float] | tuple[int | float, ...],
) -> dict[str, object]:
    """Compare same-index *supplied* samples; no geospatial parity assertion.

    Earth Engine masks may be fractional. Positive masks mean values are
    present; mask values are NOT multiplied into occurrence percentages.
    The source supplies independently decoded *native* (not RGB, resampled,
    reprojected or visualized) windows and must verify spatial alignment
    outside this helper. Never call this on compressed source TIFF bytes.
    """
    if type(geotiff_occurrence) is not bytes or not 1 <= len(geotiff_occurrence) <= MAX_PIXELS:
        raise JRCWindowComparisonBlocked("expected 1..65536 decoded GeoTIFF uint8 pixels")
    if type(earth_engine_occurrence) not in (list, tuple) or type(earth_engine_mask) not in (list, tuple):
        raise JRCWindowComparisonBlocked("Earth Engine values and masks must be separate arrays")
    count = len(geotiff_occurrence)
    if len(earth_engine_occurrence) != count or len(earth_engine_mask) != count:
        raise JRCWindowComparisonBlocked("pixel and mask array lengths differ")
    result_counts = {
        "both_native_valid": 0,
        "equal_valid_occurrence_percent": 0,
        "different_valid_occurrence_percent": 0,
        "geotiff_valid_earth_engine_masked": 0,
        "earth_engine_valid_geotiff_nodata": 0,
        "both_nodata": 0,
        "earth_engine_fractional_valid_mask": 0,
        "earth_engine_masked_numeric_placeholder": 0,
        "maximum_absolute_difference_on_valid_overlap": None,
    }
    max_abs_difference = None
    for i, (tiff, ee_value, raw_mask) in enumerate(
        zip(geotiff_occurrence, earth_engine_occurrence, earth_engine_mask)
    ):
        if 100 < tiff < 255:
            raise JRCWindowComparisonBlocked(f"invalid GeoTIFF occurrence percentage at index {i}")
        # Never convert an unbounded Python integer into a float via
        # math.isfinite: 10**1000 would raise OverflowError instead of our
        # well-defined blocked input error.
        if type(raw_mask) not in (int, float):
            raise JRCWindowComparisonBlocked(f"invalid Earth Engine mask at index {i}")
        if not 0 <= raw_mask <= 1 or (
            type(raw_mask) is float and not math.isfinite(raw_mask)
        ):
            raise JRCWindowComparisonBlocked(f"invalid Earth Engine mask at index {i}")
        masked = raw_mask == 0
        if ee_value is not None:
            if type(ee_value) not in (int, float):
                raise JRCWindowComparisonBlocked(f"invalid Earth Engine value type at index {i}")
            if not 0 <= ee_value <= 255 or (
                type(ee_value) is float and not math.isfinite(ee_value)
            ):
                raise JRCWindowComparisonBlocked(f"invalid Earth Engine value type at index {i}")
            if ee_value != int(ee_value):
                raise JRCWindowComparisonBlocked(f"invalid/non-native Earth Engine occurrence at index {i}")
        elif not masked:
            raise JRCWindowComparisonBlocked(f"valid Earth Engine mask without data at index {i}")
        if not masked and ee_value is not None and ee_value > 100:
            raise JRCWindowComparisonBlocked(f"out-of-range valid Earth Engine occurrence at index {i}")
        if masked and ee_value is not None:
            result_counts["earth_engine_masked_numeric_placeholder"] += 1
        if 0 < raw_mask < 1:
            result_counts["earth_engine_fractional_valid_mask"] += 1
        if tiff == 255 and masked:
            result_counts["both_nodata"] += 1
        elif tiff == 255:
            result_counts["earth_engine_valid_geotiff_nodata"] += 1
        elif masked:
            result_counts["geotiff_valid_earth_engine_masked"] += 1
        else:
            result_counts["both_native_valid"] += 1
            diff = abs(tiff - int(ee_value))
            max_abs_difference = max(diff, max_abs_difference or 0)
            if diff == 0:
                result_counts["equal_valid_occurrence_percent"] += 1
            else:
                result_counts["different_valid_occurrence_percent"] += 1
    result_counts["maximum_absolute_difference_on_valid_overlap"] = max_abs_difference
    return {
        "profile": "jrc-gsw-v15-geotiff-vs-gee-masked-native-window-offline-v0",
        "source_id": SOURCE_ID,
        "earth_engine_asset_id": GEE_ASSET,
        "caller_supplied_decoded_geotiff_window_sha256": hashlib.sha256(geotiff_occurrence).hexdigest(),
        "caller_supplied_positional_pixel_count": count,
        **result_counts,
        "supplied_window_positional_values_equal_if_overlap": (
            None if result_counts["both_native_valid"] == 0
            else result_counts["different_valid_occurrence_percent"] == 0
        ),
        "earth_engine_fractional_masks_used_as_weights": False,
        "geospatial_grid_alignment_independently_verified": False,
        "original_geotiff_and_gee_source_identities_verified": False,
        "post_2026_11_10_correction_verified": False,
        "source_asset_byte_provenance_verified": False,
        "original_source_requests_executed": False,
        "raw_external_source_values_persisted": False,
        "model_input_approved": False,
    }


# Google Earth Engine PixelGrid has six ordered affine coefficients:
# [x_scale, x_shear, x_translate, y_shear, y_scale, y_translate].
# Pixel (0,0) is its upper-left corner; using only 'scale' can move the grid.
# FAO identifies JRC GSW 1.5 Occurrence as EPSG:4326, 0.00025 degrees.
_GRID_KEYS = frozenset({
    "crs", "transform", "raster_width", "raster_height",
    "left", "top", "width", "height",
})
_GRID_RESOLUTION_DEGREES = 0.00025
_GRID_TOL_DEGREES = 1e-12
_MAX_RASTER_SIDE = 2_000_000


def _supplied_grid(grid: dict[str, object], name: str) -> dict[str, object]:
    """Validate caller-supplied native-grid metadata, never assert provenance."""
    if type(grid) is not dict or set(grid) != _GRID_KEYS:
        raise JRCWindowComparisonBlocked(f"{name}: wrong pixel-grid metadata keys")
    if grid["crs"] != "EPSG:4326" or type(grid["crs"]) is not str:
        raise JRCWindowComparisonBlocked(f"{name}: unsupported CRS")
    for key in ("raster_width", "raster_height", "left", "top", "width", "height"):
        value = grid[key]
        if type(value) is not int:
            raise JRCWindowComparisonBlocked(f"{name}: non-integer {key}")
        if key in ("raster_width", "raster_height"):
            if not 1 <= value <= _MAX_RASTER_SIDE:
                raise JRCWindowComparisonBlocked(f"{name}: invalid {key}")
        elif key in ("left", "top"):
            if not 0 <= value < _MAX_RASTER_SIDE:
                raise JRCWindowComparisonBlocked(f"{name}: invalid {key}")
        elif not 1 <= value <= MAX_PIXELS:
            raise JRCWindowComparisonBlocked(f"{name}: invalid {key}")
    if (grid["width"] * grid["height"] > MAX_PIXELS
            or grid["left"] + grid["width"] > grid["raster_width"]
            or grid["top"] + grid["height"] > grid["raster_height"]):
        raise JRCWindowComparisonBlocked(f"{name}: window outside bounded native grid")
    transform = grid["transform"]
    if type(transform) not in (list, tuple) or len(transform) != 6:
        raise JRCWindowComparisonBlocked(f"{name}: expected 6 affine coefficients")
    for coefficient in transform:
        # Bound huge integers *before* numeric float conversion.
        if (type(coefficient) not in (int, float)
                or not -360 <= coefficient <= 360
                or (type(coefficient) is float and not math.isfinite(coefficient))):
            raise JRCWindowComparisonBlocked(f"{name}: unsafe affine coefficient")
    xs, xsh, xt, ysh, ys, yt = transform
    if (abs(xs - _GRID_RESOLUTION_DEGREES) > _GRID_TOL_DEGREES
            or abs(ys + _GRID_RESOLUTION_DEGREES) > _GRID_TOL_DEGREES
            or abs(xsh) > _GRID_TOL_DEGREES
            or abs(ysh) > _GRID_TOL_DEGREES):
        raise JRCWindowComparisonBlocked(f"{name}: non-native resolution, rotation or shear")
    # Validate corners of the supplied window, not just pixel resolution.
    x0 = xs * grid["left"] + xsh * grid["top"] + xt
    y0 = ysh * grid["left"] + ys * grid["top"] + yt
    x1 = x0 + xs * grid["width"] + xsh * grid["height"]
    y1 = y0 + ysh * grid["width"] + ys * grid["height"]
    if not (-180 <= x0 <= 180 and -180 <= x1 <= 180
            and -90 <= y0 <= 90 and -90 <= y1 <= 90):
        raise JRCWindowComparisonBlocked(f"{name}: window beyond geographic coordinates")
    return {
        "crs": grid["crs"],
        "window_width": grid["width"],
        "window_height": grid["height"],
        "upper_left": (x0, y0),
        "lower_right": (x1, y1),
    }


def inspect_supplied_native_window_grid_pair(
    geotiff_grid: dict[str, object], earth_engine_grid: dict[str, object],
) -> dict[str, object]:
    """Require consistent *supplied* grid coordinates, not original-source proof.

    The two sources may have different parent raster origins and dimensions:
    a JRC 10-degree TIFF tile may be paired with a window in a global GEE
    asset. Per-source native grids, window offsets and native resolution
    must lead to the *same* four geographic window corner coordinates.
    """
    a = _supplied_grid(geotiff_grid, "GeoTIFF")
    b = _supplied_grid(earth_engine_grid, "GEE")
    if (a["window_width"], a["window_height"]) != (
            b["window_width"], b["window_height"]):
        raise JRCWindowComparisonBlocked("GeoTIFF/GEE window shapes differ")
    for corner in ("upper_left", "lower_right"):
        if any(abs(av - bv) > _GRID_TOL_DEGREES for av, bv in zip(a[corner], b[corner])):
            raise JRCWindowComparisonBlocked(
                "GeoTIFF/GEE window native affine locations differ"
            )
    return {
        "profile": "jrc-gsw-v15-native-supplied-grid-pair-offline-v0",
        "source_id": SOURCE_ID,
        "native_grid_crs_expected": "EPSG:4326",
        "native_pixel_size_degrees_expected": _GRID_RESOLUTION_DEGREES,
        "caller_supplied_grid_metadata_compatible": True,
        "caller_supplied_window_width": a["window_width"],
        "caller_supplied_window_height": a["window_height"],
        "caller_supplied_window_pixel_count": a["window_width"] * a["window_height"],
        "grid_metadata_provider_authenticated": False,
        "geospatial_grid_alignment_independently_verified": False,
        "native_unresampled_source_data_independently_verified": False,
        "post_2026_11_10_correction_verified": False,
        "model_input_approved": False,
    }


def compare_native_occurrence_windows_with_grid(
    geotiff_occurrence: bytes,
    earth_engine_occurrence: list[int | float | None] | tuple[int | float | None, ...],
    earth_engine_mask: list[int | float] | tuple[int | float, ...],
    geotiff_grid: dict[str, object], earth_engine_grid: dict[str, object],
) -> dict[str, object]:
    """Compare values only after fail-closed caller-provided grid preflight.

    Numeric match still cannot authenticate native/reviewed source pixels.
    """
    grid = inspect_supplied_native_window_grid_pair(geotiff_grid, earth_engine_grid)
    if len(geotiff_occurrence) != grid["caller_supplied_window_pixel_count"]:
        raise JRCWindowComparisonBlocked("decoded source pixels do not fit supplied window")
    result = compare_native_occurrence_windows(
        geotiff_occurrence, earth_engine_occurrence, earth_engine_mask
    )
    return {**result, **grid}
