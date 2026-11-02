# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hazard-overlay algorithm falsifier using synthetic-only spatial supports.

No historical flood, depth, return period, storm, physical hazard or insurer
location is supplied. Supports are artificial relative bounding-box cutouts
for comparing TWO repair algorithms' spatial area intersection semantics.
Only anonymized, country-wide aggregated disagreement counters are printed.
"""
from __future__ import annotations

import math

from shapely.geometry import box
from shapely.errors import GEOSException


class SupportChallengeError(ValueError):
    """Unexpected synthetic geometry or nonfinite overlay result."""


def compare_repair_supports(linework, structure, source_bounds: tuple) -> dict:
    """Return support-level difference counts without any location/value leak.

    Supports are three fixed fractions of the original geometry's envelope:
    left half, upper half, and the central quarter; no event-specific hazards.
    Both inputs must be valid projected polygonal repaired candidates. The
    rectangle geometries are transient and not exported or persisted.
    """
    if (not isinstance(source_bounds, tuple) or len(source_bounds) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v)
                   for v in source_bounds)):
        raise SupportChallengeError("Nonfinite or malformed original envelope")
    x0, y0, x1, y1 = source_bounds
    if not (x0 < x1 and y0 < y1):
        raise SupportChallengeError("Degenerate source envelope")
    for geom in (linework, structure):
        if (geom.is_empty or not geom.is_valid or
                geom.geom_type not in ("Polygon", "MultiPolygon")):
            raise SupportChallengeError("Repair must be valid nonempty polygonal set")
    mx, my = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.5
    qx0, qx1 = x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75
    qy0, qy1 = y0 + (y1 - y0) * 0.25, y0 + (y1 - y0) * 0.75
    probes = (
        box(x0, y0, mx, y1),
        box(x0, my, x1, y1),
        box(qx0, qy0, qx1, qy1),
    )
    disagreements = 0
    presence_disagreements = 0
    absolute_area_difference = 0.0
    try:
        for probe in probes:
            a = linework.intersection(probe).area
            b = structure.intersection(probe).area
            if not (math.isfinite(a) and math.isfinite(b) and a >= 0 and b >= 0):
                raise SupportChallengeError("Nonfinite synthetic support area")
            # Numeric metric in projected source metre-squared units.
            tolerance = max(1e-6, 1e-8 * max(a, b))
            disagreements += abs(a - b) > tolerance
            presence_disagreements += (a > tolerance) != (b > tolerance)
            absolute_area_difference += abs(a - b)
    except (GEOSException, ValueError, OverflowError) as exc:
        raise SupportChallengeError("Synthetic support intersection failed") from exc
    if not math.isfinite(absolute_area_difference):
        raise SupportChallengeError("Unbounded area difference")
    return {
        "synthetic_probe_count": 3,
        "synthetic_intersection_area_disagreements": disagreements,
        "synthetic_wet_presence_disagreements": presence_disagreements,
        "synthetic_absolute_intersection_area_delta_projected_m2": absolute_area_difference,
    }
