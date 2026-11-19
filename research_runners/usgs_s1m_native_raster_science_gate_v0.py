# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline USGS S1M native raster metadata science gate (synthetic input only).

This pure metadata checker does not fetch provider bytes, prove a TIFF or
GeoPackage was inspected, approve rights or admit a CAT-model input. It is
intentionally independent of the TNMAccess product-catalogue preflight because
two other PRs independently harden that catalogue parser.
"""
from __future__ import annotations

import math


class Blocked(ValueError):
    """Reject a metadata profile that does not match published S1M semantics."""


# Published S1M CONUS reference values are product documentation, NOT
# independently observed GeoTIFF or associated source-lineage GeoPackage data.
PUBLISHED_S1M_HORIZONTAL_EPSG = 6350  # NAD83(2011) / CONUS Albers
PUBLISHED_S1M_VERTICAL_EPSG = 5703  # NAVD88
PUBLISHED_S1M_GEOID = "GEOID18"
PUBLISHED_S1M_NODATA = -999999


def check_raster_science_profile(profile: object) -> dict[str, object]:
    """Screen caller-extracted *metadata*, not source pixels or their provenance.

    Passing is NOT an original GeoTIFF receipt, GeoPackage lineage review, or
    permission to use the material for a catastrophe model.
    """
    fields = {
        "product", "raster_format", "pixel_data_type", "horizontal_epsg",
        "vertical_epsg", "geoid_model", "horizontal_units", "vertical_units",
        "pixel_size_x_m", "pixel_size_y_m", "nodata_value",
    }
    if type(profile) is not dict or set(profile) != fields:
        raise Blocked("missing or unexpected S1M raster-profile fields")
    if profile["product"] != "USGS 3DEP S1M" or profile["raster_format"] != "COG GeoTIFF":
        raise Blocked("wrong S1M product or raster format")
    if profile["pixel_data_type"] not in ("Float32", "Float64"):
        raise Blocked("S1M published floating-point raster type mismatch")
    if (
        type(profile["horizontal_epsg"]) is not int
        or profile["horizontal_epsg"] != PUBLISHED_S1M_HORIZONTAL_EPSG
        or type(profile["vertical_epsg"]) is not int
        or profile["vertical_epsg"] != PUBLISHED_S1M_VERTICAL_EPSG
    ):
        raise Blocked("S1M CRS mismatch; legacy project UTM must not substitute")
    if (
        profile["geoid_model"] != PUBLISHED_S1M_GEOID
        or profile["horizontal_units"] != "m"
        or profile["vertical_units"] != "m"
    ):
        raise Blocked("S1M geoid or linear units mismatch")
    for field in ("pixel_size_x_m", "pixel_size_y_m"):
        value = profile[field]
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)) or value != 1:
            raise Blocked("S1M one-metre raster spacing mismatch")
    value = profile["nodata_value"]
    if (
        type(value) not in (int, float)
        or (type(value) is float and not math.isfinite(value))
        or value != PUBLISHED_S1M_NODATA
    ):
        raise Blocked("S1M -999999 NoData sentinel mismatch")
    return {
        "status": "declared_profile_semantics_consistent_only",
        "published_horizontal_epsg": PUBLISHED_S1M_HORIZONTAL_EPSG,
        "published_vertical_epsg": PUBLISHED_S1M_VERTICAL_EPSG,
        "published_nodata": PUBLISHED_S1M_NODATA,
        "original_tiff_bytes_verified": False,
        "source_lineage_gpkg_verified": False,
        "void_fill_and_blending_verified": False,
        "model_input_admitted": False,
    }


