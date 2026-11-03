# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic hazard -> ratio curve -> fictional gross EUR -> toy CAT-XL bridge.

No external files, network access, provider curves, insured portfolios, vendor
model execution, or model-input admission. This is an isolated arithmetic proof.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from typing import Any

from research_runners.ci_curve_semantics_v0 import (
    CurveSemanticsError,
    validate_curve_semantics,
)
from research_runners.synthetic_catxl_loss_math_v0 import allocate


class SyntheticCurveBridgeError(ValueError):
    """A synthetic-only or scientific-unit boundary was violated."""


def _decimal(value: Any, *, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise SyntheticCurveBridgeError(f"{label}: expected a finite numeric value")
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SyntheticCurveBridgeError(f"{label}: invalid numeric value") from exc
    if not v.is_finite() or v < 0:
        raise SyntheticCurveBridgeError(f"{label}: expected finite nonnegative value")
    return v


def _ratio_at(intensity: Decimal, points: tuple[tuple[float, float], ...]) -> Decimal:
    """Bounded linear interpolation only, with no out-of-domain extrapolation."""
    x = [Decimal(str(p[0])) for p in points]
    y = [Decimal(str(p[1])) for p in points]
    if not x[0] <= intensity <= x[-1]:
        raise SyntheticCurveBridgeError("hazard intensity outside synthetic curve support")
    for i, grid in enumerate(x):
        if intensity == grid:
            return y[i]
        if intensity < grid:
            with localcontext() as context:
                context.prec = 36
                ratio = y[i - 1] + (
                    (y[i] - y[i - 1]) * (intensity - x[i - 1]) / (grid - x[i - 1])
                )
            if not Decimal(0) <= ratio <= Decimal(1):
                raise SyntheticCurveBridgeError("invalid interpolated fractional loss")
            return ratio
    return y[-1]


def fictional_event_loss_cells(
    *,
    positions_eur: Mapping[str, int],
    intensities: Mapping[str, int | float | Decimal],
    curve_points: Sequence[tuple[float, float]],
    source_curve_id: str,
    asset_class: str,
    curve_unit: str,
    event_unit: str,
    output_metric: str,
) -> dict[str, int]:
    """Turn a purely invented asset/hazard snapshot into fictional EUR loss cells.

    The source and asset class must carry SYNTH- identities. The only accepted
    consequence is an explicit fractional damage ratio: pipe repairs and repair
    rates cannot be translated to monetary loss without another model.
    """
    if not isinstance(source_curve_id, str) or not source_curve_id.startswith("SYNTH-"):
        raise SyntheticCurveBridgeError("only SYNTH- curve identities are allowed")
    if not isinstance(asset_class, str) or not asset_class.startswith("SYNTH-"):
        raise SyntheticCurveBridgeError("only SYNTH- asset classes are allowed")
    if output_metric != "fractional_damage_ratio":
        raise SyntheticCurveBridgeError("repair metrics cannot imply fractional insured loss")
    try:
        points = validate_curve_semantics(
            source_curve_id=source_curve_id,
            asset_class=asset_class,
            source_intensity_unit=curve_unit,
            model_intensity_unit=event_unit,
            output_metric=output_metric,
            points=curve_points,
        )
    except CurveSemanticsError as exc:
        raise SyntheticCurveBridgeError(str(exc)) from exc
    if not isinstance(positions_eur, Mapping) or not 1 <= len(positions_eur) <= 100:
        raise SyntheticCurveBridgeError("bounded synthetic positions required")
    for name, amount in positions_eur.items():
        if (
            not isinstance(name, str) or not name.startswith("SYNTH-")
            or len(name) > 24 or type(amount) is not int
            or not 1 <= amount <= 10**12
        ):
            raise SyntheticCurveBridgeError("invalid synthetic EUR exposure position")
    if not isinstance(intensities, Mapping) or not 1 <= len(intensities) <= 100:
        raise SyntheticCurveBridgeError("bounded synthetic hazard intensities required")
    if not set(intensities).issubset(positions_eur):
        raise SyntheticCurveBridgeError("unknown synthetic exposure in hazard event")

    cells: dict[str, int] = {}
    for asset_id, value in intensities.items():
        intensity = _decimal(value, label="synthetic hazard intensity")
        ratio = _ratio_at(intensity, points)
        with localcontext() as context:
            context.prec = 36
            amount = (Decimal(positions_eur[asset_id]) * ratio).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        euro = int(amount)
        if not 0 <= euro <= positions_eur[asset_id]:
            raise SyntheticCurveBridgeError("synthetic loss violates asset value bound")
        cells[asset_id] = euro
    return cells


def synthetic_hazard_to_catxl(
    *,
    positions_eur: dict[str, int],
    hazard_events: list[dict[str, Any]],
    toy_treaty: dict[str, Any],
    curve_points: Sequence[tuple[float, float]],
    source_curve_id: str,
    asset_class: str,
    curve_unit: str,
    output_metric: str,
) -> dict[str, Any]:
    """Demonstrate a strictly fictional hazard-to-gross-to-ceded/net chain."""
    if type(hazard_events) is not list or not 1 <= len(hazard_events) <= 366:
        raise SyntheticCurveBridgeError("bounded synthetic event list required")
    losses: list[dict[str, Any]] = []
    for event in hazard_events:
        if type(event) is not dict or set(event) != {
            "event_id", "date", "peril", "intensity_unit", "intensities"
        }:
            raise SyntheticCurveBridgeError("exact fictional hazard event fields required")
        if type(event["event_id"]) is not str or not event["event_id"].startswith("FICTIONAL-"):
            raise SyntheticCurveBridgeError("event must be explicitly fictional")
        cells = fictional_event_loss_cells(
            positions_eur=positions_eur,
            intensities=event["intensities"],
            curve_points=curve_points,
            source_curve_id=source_curve_id,
            asset_class=asset_class,
            curve_unit=curve_unit,
            event_unit=event["intensity_unit"],
            output_metric=output_metric,
        )
        losses.append({
            "event_id": event["event_id"],
            "date": event["date"],
            "peril": event["peril"],
            "losses_eur": cells,
        })
    result = allocate(positions_eur, losses, toy_treaty)
    return {
        **result,
        "curve_to_gross_bridge": "SYNTHETIC_ONLY_BOUNDED_LINEAR_INTERPOLATION",
        "hazard_input_real": False,
        "vulnerability_input_real": False,
        "exposure_input_real": False,
        "commercial_use_cleared": False,
    }
