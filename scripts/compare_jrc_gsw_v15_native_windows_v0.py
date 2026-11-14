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
        if type(raw_mask) not in (int, float) or not math.isfinite(raw_mask) or not 0 <= raw_mask <= 1:
            raise JRCWindowComparisonBlocked(f"invalid Earth Engine mask at index {i}")
        masked = raw_mask == 0
        if ee_value is not None:
            if type(ee_value) not in (int, float) or not math.isfinite(ee_value):
                raise JRCWindowComparisonBlocked(f"invalid Earth Engine value type at index {i}")
            if not 0 <= ee_value <= 255 or ee_value != int(ee_value):
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
