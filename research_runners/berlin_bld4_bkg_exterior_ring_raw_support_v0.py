#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original BKG raw-code/mask support in disjoint EXTERIOR building-distance bands.

Purely research-only; never asserts centimetres/metres, insured water depth,
access-point elevation, flood occurrence, TIV or insured loss. Geometry and
pixels are already independent, bounded source-verified in caller. No network.
"""
from __future__ import annotations

import math

from research_runners.berlin_bld4_bkg_original_raw_cell_support_v0 import (
    MAX_TESTED_BUILDINGS, RealSupportError, audit_cells,
)

# Distance from the union of ALL building polygons in metres, native EPSG:25832.
# Never overlap bands or count another building footprint as "nearby water".
BANDS_METRES = ((0, 1), (1, 3), (3, 5))
MAX_RING_AREA_M2 = 20_000.0


def audit_disjoint_exterior_bands(polygons_utm32, pilot_utm32, values, missing, grid_transform):
    """Report fractional pixel-overlap areas in three non-overlapping rings.

    The exact pilot boundary is a reprojected *polygon*, not its rectangular
    envelope. Polygon union prevents counting the same cell multiple times
    for near/overlapping buffers from distinct original buildings.
    """
    from shapely.geometry import Polygon, MultiPolygon
    from shapely.ops import unary_union

    if not 1 <= len(polygons_utm32) <= MAX_TESTED_BUILDINGS:
        raise RealSupportError("source polygon count exceeds reviewed original sample")
    if (pilot_utm32.geom_type not in ("Polygon", "MultiPolygon")
            or pilot_utm32.is_empty or not pilot_utm32.is_valid
            or not 1000 <= pilot_utm32.area <= 60_000):
        raise RealSupportError("not the bounded projected Berlin pilot polygon")
    if not all(math.isfinite(v) for v in pilot_utm32.bounds):
        raise RealSupportError("nonfinite projected pilot bounds")
    for poly in polygons_utm32:
        if (poly.is_empty or not poly.is_valid
                or poly.geom_type not in ("Polygon", "MultiPolygon")
                or not 0 < poly.area < 100_000
                or not all(math.isfinite(v) for v in poly.bounds)
                or poly.difference(pilot_utm32).area > 1e-5):
            raise RealSupportError("input geometry not clipped to verified pilot")
    source_union = unary_union(polygons_utm32)
    if not source_union.is_valid or source_union.is_empty:
        raise RealSupportError("invalid union of source buildings")
    rings = []
    for inner, outer in BANDS_METRES:
        outer_geom = source_union.buffer(outer, join_style=2)
        inner_geom = (source_union if inner == 0
                      else source_union.buffer(inner, join_style=2))
        # Intersect with exact reprojected pilot and remove every footprint;
        # including original building spaces in "external" rings is forbidden.
        ring = outer_geom.difference(inner_geom).intersection(pilot_utm32)
        ring = ring.difference(source_union)
        if (ring.is_empty or not ring.is_valid
                or ring.geom_type not in ("Polygon", "MultiPolygon")
                or not 0 < ring.area < MAX_RING_AREA_M2):
            raise RealSupportError("unsupported empty/large exterior sampling band")
        support = audit_cells([ring], values, missing, grid_transform)
        positive = support["positive_raw_code_supported_area_m2"]
        zero = support["valid_zero_raw_code_supported_area_m2"]
        no_data = support["original_nodata_supported_area_m2"]
        outside = support["outside_sample_window_area_m2"]
        area = support["clipped_building_area_in_raster_crs_m2"]
        if not math.isclose(area, positive+zero+no_data+outside,
                            rel_tol=1e-7, abs_tol=5e-5):
            raise RealSupportError("external ring category areas do not conserve")
        rings.append({
            "distance_from_source_building_union_m": [inner, outer],
            "unique_exterior_ring_area_m2": area,
            "positive_raw_integer_supported_area_m2": positive,
            "valid_numeric_zero_supported_area_m2": zero,
            "original_masked_nodata_area_m2": no_data,
            "outside_sample_window_area_m2": outside,
            "valid_numeric_support_fraction": round((positive+zero)/area, 6),
        })
    return {
        "original_buildings_count": len(polygons_utm32),
        "exterior_ring_method": "disjoint buffers of ALL original building footprints; EPSG:25832 metre distances, clipped to exact pilot polygon",
        "exterior_rings_m": [list(x) for x in BANDS_METRES],
        "bands": rings,
        "raw_int16_values_not_physical_water_depths": True,
        "positive_raw_code_not_confirmed_as_centimetres_or_metres": True,
        "building_raster_nodata_never_interpreted_as_dry": True,
        "building_access_or_entrance_levels_not_verified": True,
        "exterior_rings_not_building_loss_depth": True,
        "original_per_building_ids_coords_or_pixel_values_exported": False,
        "cat_model_or_insurer_exposure_admitted": False,
    }
