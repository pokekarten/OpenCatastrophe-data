# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only vulnerability curve semantic gate; does not read provider data.

A numeric column is not a universal damage ratio. This reusable preflight checks
explicit source identities and units before any loss engine could consume values.
It intentionally has no network, filesystem, parser or model execution.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


class CurveSemanticsError(ValueError):
    """Reject ambiguous or physically impossible curve inputs."""


OUTPUT_METRICS = frozenset(
    {"fractional_damage_ratio", "repair_rate", "pipe_repairs_per_km"}
)
MAX_CURVE_POINTS = 4096  # bounded metadata preflight, never a raster/asset stream


def validate_curve_semantics(
    *,
    source_curve_id: str,
    asset_class: str,
    source_intensity_unit: str,
    model_intensity_unit: str,
    output_metric: str,
    points: Sequence[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    """Validate synthetic points, preserving units and non-fractional outputs.

    No interpolation, unit conversion, insurance valuation, cost inflation or
    statistical independence is inferred from a successful validation.
    """
    if not all(
        isinstance(value, str) and value.strip()
        for value in (source_curve_id, asset_class, source_intensity_unit, model_intensity_unit)
    ):
        raise CurveSemanticsError("source curve ID, asset class, and both units are required")
    if source_intensity_unit != model_intensity_unit:
        raise CurveSemanticsError("explicit scientifically reviewed unit conversion required")
    if output_metric not in OUTPUT_METRICS:
        raise CurveSemanticsError("unknown or ambiguous output metric is not admitted")
    if (not isinstance(points, Sequence) or isinstance(points, (str, bytes))
            or not 1 <= len(points) <= MAX_CURVE_POINTS):
        raise CurveSemanticsError("curve requires a bounded sequence of numeric point pairs")
    clean: list[tuple[float, float]] = []
    previous = None
    for point in points:
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise CurveSemanticsError("each point must be (intensity, consequence)")
        raw_x, raw_y = point
        if isinstance(raw_x, bool) or isinstance(raw_y, bool):
            raise CurveSemanticsError("booleans are not numeric intensities or consequences")
        try:
            x, y = float(raw_x), float(raw_y)
        except (TypeError, ValueError, OverflowError) as exc:
            raise CurveSemanticsError("curve points must be numeric") from exc
        if not math.isfinite(x) or not math.isfinite(y) or x < 0 or y < 0:
            raise CurveSemanticsError("curve points must be finite and nonnegative")
        if previous is not None and x <= previous:
            raise CurveSemanticsError("intensities must be strictly increasing")
        if output_metric == "fractional_damage_ratio" and y > 1:
            raise CurveSemanticsError("fractional damage ratio must be between 0 and 1")
        clean.append((x, y))
        previous = x
    return tuple(clean)
