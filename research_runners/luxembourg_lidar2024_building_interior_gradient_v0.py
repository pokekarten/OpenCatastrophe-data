#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Local masked MNS gradients within source building polygons; aggregates only.

This is a surface-*steepness proxy*, NEVER observed roof pitch, solar-facet
orientation, roof material or admitted CAT input. No new source reads/network.
No building IDs, geometry, original cells or per-object gradients exported.
"""
from __future__ import annotations

import math

MIN_STENCIL_CENTERS = 12
MAX_SOURCE_OBJECTS = 400
MAX_SOURCE_PIXELS = 200_000
SURFACE_MIN_ABOVE_GROUND = 3.0
MAX_CELL_SLOPE_DEGREES = 70.0
SLOPE_BINS = ((0.0, 5.0, "0_to_5_degrees"),
              (5.0, 15.0, "5_to_15_degrees"),
              (15.0, 30.0, "15_to_30_degrees"),
              (30.0, 50.0, "30_to_50_degrees"),
              (50.0, MAX_CELL_SLOPE_DEGREES, "50_to_70_degrees"))


class InteriorGradientError(ValueError):
    """Cannot safely calculate this particular local source-gradient diagnostic."""


def local_gradients(polygons, terrain, surface, transform, study_polygon) -> dict:
    """2-D central differences using only four same-polygon interior neighbors.

    Two-pass occupancy ensures *no raster centre belongs to more than one
    footprint*. The finite cross stencil excludes boundary/facade differences,
    no-data neighbors, non-roof candidate cells below 3m and shared pixels.
    Even this exclusion does not reliably remove trees/dormers/other equipment.
    """
    import numpy as np
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping

    if (not isinstance(polygons, list) or not 1 <= len(polygons) <= MAX_SOURCE_OBJECTS
            or terrain.ndim != 2 or terrain.shape != surface.shape
            or not 16 <= terrain.size <= MAX_SOURCE_PIXELS
            or terrain.shape[0] < 4 or terrain.shape[1] < 4):
        raise InteriorGradientError("Invalid source polygon count or bounded raster grid")
    if (not study_polygon.is_valid or study_polygon.is_empty
            or study_polygon.area <= 0):
        raise InteriorGradientError("Invalid study polygon")
    try:
        pixel_dx = float(transform.a)
        pixel_dy = abs(float(transform.e))
        if (not math.isfinite(pixel_dx) or not math.isfinite(pixel_dy)
                or pixel_dx <= 0 or pixel_dy <= 0
                or abs(float(transform.b)) > 1e-9
                or abs(float(transform.d)) > 1e-9
                or abs(pixel_dx-pixel_dy) > 1e-6):
            raise InteriorGradientError("Non-north-up or mismatched spatial pixel dimensions")
    except (AttributeError, TypeError) as exc:
        raise InteriorGradientError("Malformed affine transform") from exc

    t = np.asarray(terrain.data, dtype=np.float64)
    s = np.asarray(surface.data, dtype=np.float64)
    valid = (~np.ma.getmaskarray(terrain)) & (~np.ma.getmaskarray(surface))
    valid &= (np.isfinite(t) & np.isfinite(s)
              & (t >= -1000) & (t <= 4000)
              & (s >= -1000) & (s <= 4000))
    if np.count_nonzero(valid) < terrain.size // 2:
        raise InteriorGradientError("Insufficient joint finite LiDAR source pixels")
    difference = s-t
    if np.any(np.abs(difference[valid]) > 200):
        raise InteriorGradientError("Nonphysical uncalibrated MNS-minus-MNT differences")
    candidate = valid & (difference >= SURFACE_MIN_ABOVE_GROUND)

    clipped = []
    occupancy = np.zeros(terrain.shape, dtype=np.uint16)
    for polygon in polygons:
        if (polygon.geom_type not in ("Polygon", "MultiPolygon")
                or polygon.is_empty or not polygon.is_valid
                or polygon.area <= 0):
            raise InteriorGradientError("Unsupported original footprint")
        clipped_polygon = polygon.intersection(study_polygon)
        if (clipped_polygon.is_empty or clipped_polygon.area <= 0
                or clipped_polygon.geom_type not in ("Polygon", "MultiPolygon")):
            raise InteriorGradientError("Original footprint misses exact study polygon")
        mask = geometry_mask([mapping(clipped_polygon)], out_shape=terrain.shape,
                             transform=transform, invert=True, all_touched=False)
        occupancy += mask.astype(np.uint16)
        clipped.append(mask)
    if int(np.count_nonzero(occupancy == 0)
           + np.count_nonzero(occupancy == 1)
           + np.count_nonzero(occupancy > 1)) != terrain.size:
        raise InteriorGradientError("Footprint pixel occupancy not conserved")

    categories = {name: 0 for _, _, name in SLOPE_BINS}
    counted, insufficient = 0, 0
    rejected_very_steep_centres = 0
    all_eligible_stencils = 0

    # Do not use a generic image gradient. All five source pixel centers of
    # each central-difference stencil must belong to the SAME source polygon,
    # be uniquely owned, finite and exceed the 3m surface-height threshold.
    delta_x = (s[1:-1, 2:] - s[1:-1, :-2]) / (2.0*pixel_dx)
    delta_y = (s[:-2, 1:-1] - s[2:, 1:-1]) / (2.0*pixel_dy)
    surface_slope_degrees = np.rad2deg(np.arctan(np.hypot(delta_x, delta_y)))
    if not np.all(np.isfinite(surface_slope_degrees[candidate[1:-1, 1:-1]])):
        raise InteriorGradientError("Nonfinite MNS interior gradient")
    acceptable_gradient = surface_slope_degrees < MAX_CELL_SLOPE_DEGREES

    for mask in clipped:
        allowed = mask & (occupancy == 1) & candidate
        stencil = (allowed[1:-1, 1:-1] & allowed[1:-1, :-2]
                   & allowed[1:-1, 2:] & allowed[:-2, 1:-1]
                   & allowed[2:, 1:-1])
        all_eligible_stencils += int(np.count_nonzero(stencil))
        excluded = int(np.count_nonzero(stencil & ~acceptable_gradient))
        rejected_very_steep_centres += excluded
        good = stencil & acceptable_gradient
        if int(np.count_nonzero(good)) < MIN_STENCIL_CENTERS:
            insufficient += 1
            continue
        median = float(np.median(surface_slope_degrees[good]))
        if not math.isfinite(median):
            raise InteriorGradientError("Nonfinite within-footprint median gradient")
        matched = False
        for low, high, category in SLOPE_BINS:
            if low <= median < high:
                categories[category] += 1
                counted += 1
                matched = True
                break
        if not matched:
            raise InteriorGradientError("Gradient outside tracked bins")
    if counted + insufficient != len(clipped) or sum(categories.values()) != counted:
        raise InteriorGradientError("Polygon counts are not conserved")

    return {
        "schema_version": "lu-lidar2024-footprint-interior-mns-gradient-diagnostic-v0",
        "source_footprint_polygons": len(polygons),
        "footprints_with_surface_gradient_proxy": counted,
        "footprints_without_enough_clean_interior_stencils": insufficient,
        "median_mns_surface_gradient_bins_not_roof_pitch": categories,
        "minimum_same_footprint_interior_stencils_per_eligible_object": MIN_STENCIL_CENTERS,
        "interior_stencil_centres_before_steepness_screen": all_eligible_stencils,
        "stencil_centres_ge_70_degrees_excluded": rejected_very_steep_centres,
        "multiply_assigned_source_pixels": int(np.count_nonzero(occupancy > 1)),
        "source_building_ids_or_raw_values_exported": False,
        "solar_facet_tilt_or_aspect_observed": False,
        "vegetation_and_rooftop_equipment_separated": False,
        "horizontal_axis_control_certified": False,
        "true_roof_pitch_validated": False,
        "model_input_admitted": False,
        "warning": (
            "DSM surface gradients within uniquely assigned, five-cell interior "
            "stencils are not roof facet inclinations. Tree canopy, dormers, "
            "facades, sampling errors and 2024/2026 survey drift can affect this "
            "research-only gradient distribution. No property-level output."
        ),
    }
