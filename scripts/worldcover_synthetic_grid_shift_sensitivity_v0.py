# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Finite sensitivity of a *fabricated* footprint to pixel-grid translations.

Operates only on an already decoded 1024x1024 uint8 source block.
Uses synthetic footprint geometry, not an ALKIS building or reported survey
accuracy. Scenario offsets are exact *pixel grid units*, NOT metres.
No raw pixel arrays, coordinates, IDs or individual pixel classes are output.
"""
from __future__ import annotations

import math

from scripts.worldcover_synthetic_polygon_overlap_v0 import (
    SIDE, SCALE, SYNTHETIC_FOOTPRINT_WGS84,
    PolygonOverlapBlocked, evaluate_synthetic_polygon_in_block,
)

# 17 fixed bounded scenarios: one baseline, 8 quarter-pixel shifts,
# and 8 whole-pixel shifts. Do not infer ETRS89/WGS84 metre accuracy
# from this synthetic grid perturbation.
OFFSETS = ((0.0, 0.0),) + tuple(
    (float(dx) * scale, float(dy) * scale)
    for scale in (0.25, 1.0)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx != 0 or dy != 0
)


class SensitivityBlocked(ValueError):
    """Source class/geometry review or fixed perturbation budget failed."""


def _offset_ring(dx: float, dy: float):
    return tuple(
        (lon + dx * SCALE, lat - dy * SCALE)
        for lon, lat in SYNTHETIC_FOOTPRINT_WGS84
    )


def synthetic_grid_shift_sensitivity(pixels: bytes) -> dict:
    """Compute fractional class sensitivity for exactly 17 invented polygons."""
    if type(pixels) is not bytes or len(pixels) != SIDE * SIDE:
        raise SensitivityBlocked("only one exactly decoded original block supported")
    if len(OFFSETS) != 17 or OFFSETS[0] != (0.0, 0.0):
        raise SensitivityBlocked("reviewed synthetic translation scenarios drifted")

    results = []
    try:
        for dx, dy in OFFSETS:
            result = evaluate_synthetic_polygon_in_block(
                pixels, ring=_offset_ring(dx, dy)
            )
            if (result["model_input_approved"] is not False
                    or result["real_building_footprint_matched"] is not False
                    or result["source_pixel_values_exported"] is not False):
                raise SensitivityBlocked("underlying geometry stage wrongly admitted a real asset")
            results.append(result)
    except PolygonOverlapBlocked as exc:
        raise SensitivityBlocked("one source-pixel/synthetic-polygon scenario invalid") from exc

    if len(results) != 17:
        raise SensitivityBlocked("incomplete source shift grid")
    distributions = [
        {int(key): float(value)
         for key, value in result["area_weighted_class_fractions"].items()}
        for result in results
    ]
    union_classes = sorted(set().union(*(set(p) for p in distributions)))
    baseline = distributions[0]
    variations = [
        sum(abs(p.get(code, 0.0) - baseline.get(code, 0.0))
            for code in union_classes) / 2
        for p in distributions
    ]
    if any(not math.isfinite(v) or not 0 <= v <= 1.000001 for v in variations):
        raise SensitivityBlocked("invalid bounded total-variation metric")
    for result in results:
        if not math.isclose(sum(result["area_weighted_class_fractions"].values()),
                            1.0, abs_tol=3e-6):
            raise SensitivityBlocked("shifted polygon class shares do not sum to one")

    def majority(distribution):
        # Ties have ambiguous majority; use a deterministic tie sentinel
        # rather than asserting a confident category.
        top = max(distribution.values())
        leaders = [k for k, v in distribution.items() if abs(v-top) < 1e-6]
        return leaders[0] if len(leaders) == 1 else None

    baseline_majority = majority(baseline)
    majority_changes = any(majority(p) != baseline_majority for p in distributions[1:])
    classes = {
        str(code): {
            "minimum_fraction": round(min(p.get(code, 0.0) for p in distributions), 6),
            "maximum_fraction": round(max(p.get(code, 0.0) for p in distributions), 6),
        }
        for code in union_classes
    }
    baseline_share = {
        str(code): round(baseline.get(code, 0.0), 6)
        for code in union_classes
    }

    return {
        "profile": "oc-worldcover-synthetic-grid-shift-sensitivity-v0",
        "source_tile": "N48E009",
        "tiff_internal_block_index": 185,
        "geometry_kind": "single_fixed_invented_polygon_not_a_building",
        "shift_units": "worldcover_source_grid_pixels_not_metres",
        "perturbation_steps_pixels": [0.25, 1.0],
        "fixed_scenario_count": len(OFFSETS),
        "baseline_area_weighted_class_fractions": baseline_share,
        "shifted_class_fraction_ranges": classes,
        "maximum_total_variation_from_baseline": round(max(variations), 6),
        "baseline_majority_class_if_unique": baseline_majority,
        "any_shift_changes_majority_class": majority_changes,
        "actual_transform_accuracy_in_metres_inferred": False,
        "real_building_geometry_used": False,
        "original_source_pixel_values_exported": False,
        "source_building_survey_vintage_verified": False,
        "provider_wfs_count_discrepancy_resolved": False,
        "actual_building_worldcover_overlap_verified": False,
        "model_input_approved": False,
    }
