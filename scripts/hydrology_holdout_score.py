# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Score the frozen Dresden holdout pair vector with transparent metric states.

Pair construction, source completeness and temporal alignment remain upstream in
``scripts.hydrology_holdout``. This module never changes the valid-day sample.
It evaluates the preregistered metrics independently so a mathematically
undefined metric is reported as ``not_comparable`` without erasing other
well-defined results.
"""

from __future__ import annotations

import math
from typing import Callable, NamedTuple

from scripts.hydrology_holdout import HoldoutDayPair, HoldoutPairing
from scripts.hydrology_metrics import (
    MetricInputError,
    modified_kge_prime,
    pearson_correlation,
    relative_mean_bias,
)
from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    dresden_holdout_glofas_timestamps,
)


class HoldoutScoreError(ValueError):
    """Raised when pairing evidence is structurally inconsistent."""


class MetricOutcome(NamedTuple):
    name: str
    status: str
    value: float | None
    reason: str | None


class DresdenHoldoutScore(NamedTuple):
    status: str
    expected_days: int
    valid_days: int
    valid_fraction: float
    invalid_pair_days: int
    invalid_observed_days: int
    missing_glofas_days: int
    nonfinite_glofas_days: int
    modified_kge_prime: MetricOutcome
    pearson_correlation: MetricOutcome
    relative_mean_bias: MetricOutcome


def _finite_number(value: object, where: str) -> float:
    if type(value) not in {int, float}:
        raise HoldoutScoreError(f"{where} must be numeric and not boolean")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise HoldoutScoreError(f"{where} cannot be represented safely") from exc
    if not math.isfinite(numeric):
        raise HoldoutScoreError(f"{where} must be finite")
    return numeric


def _validate_pairing(pairing: HoldoutPairing) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if type(pairing) is not HoldoutPairing:
        raise HoldoutScoreError("pairing must be a HoldoutPairing produced by the frozen pairing contract")
    if pairing.expected_days != DRESDEN_HOLDOUT_EXPECTED_DAYS:
        raise HoldoutScoreError("pairing expected_days does not match the frozen 1,461-day holdout")
    if pairing.valid_days != len(pairing.pairs):
        raise HoldoutScoreError("pairing valid_days must equal the number of recorded pairs")
    if pairing.invalid_pair_days != pairing.expected_days - pairing.valid_days:
        raise HoldoutScoreError("pairing invalid_pair_days is inconsistent with expected/valid counts")
    if pairing.valid_days < 0 or pairing.valid_days > pairing.expected_days:
        raise HoldoutScoreError("pairing valid_days is outside the frozen holdout bounds")
    expected_fraction = pairing.valid_days / pairing.expected_days
    if pairing.valid_fraction != expected_fraction:
        raise HoldoutScoreError("pairing valid_fraction is inconsistent with expected/valid counts")
    for name, count in (
        ("invalid_observed_days", pairing.invalid_observed_days),
        ("missing_glofas_days", pairing.missing_glofas_days),
        ("nonfinite_glofas_days", pairing.nonfinite_glofas_days),
    ):
        if type(count) is not int or count < 0 or count > pairing.expected_days:
            raise HoldoutScoreError(f"pairing {name} must be an integer within holdout bounds")

    expected_labels = set(dresden_holdout_glofas_timestamps())
    previous_label = None
    observed: list[float] = []
    simulated: list[float] = []
    for index, pair in enumerate(pairing.pairs):
        if type(pair) is not HoldoutDayPair:
            raise HoldoutScoreError(f"pairing.pairs[{index}] must be a HoldoutDayPair")
        label = pair.glofas_timestamp_utc
        if label not in expected_labels:
            raise HoldoutScoreError(f"pairing.pairs[{index}] uses a label outside the frozen holdout")
        if previous_label is not None and label <= previous_label:
            raise HoldoutScoreError("pairing pairs must be unique and strictly chronological")
        previous_label = label
        observed.append(
            _finite_number(
                pair.observed_mean_discharge_m3s,
                f"pairing.pairs[{index}].observed_mean_discharge_m3s",
            )
        )
        simulated.append(
            _finite_number(
                pair.glofas_mean_discharge_m3s,
                f"pairing.pairs[{index}].glofas_mean_discharge_m3s",
            )
        )
    return tuple(simulated), tuple(observed)


def _evaluate_metric(
    name: str,
    function: Callable[[tuple[float, ...], tuple[float, ...]], float],
    simulated: tuple[float, ...],
    observed: tuple[float, ...],
) -> MetricOutcome:
    try:
        value = function(simulated, observed)
    except MetricInputError as exc:
        reason = str(exc).strip() or "metric is mathematically undefined for this frozen sample"
        return MetricOutcome(name=name, status="not_comparable", value=None, reason=reason)
    if not math.isfinite(value):
        raise HoldoutScoreError(f"{name} returned a non-finite value despite metric validation")
    return MetricOutcome(name=name, status="pass", value=value, reason=None)


def score_dresden_holdout(pairing: HoldoutPairing) -> DresdenHoldoutScore:
    """Evaluate KGE', Pearson correlation and relative mean bias independently."""

    simulated, observed = _validate_pairing(pairing)
    kge = _evaluate_metric("modified_kge_prime", modified_kge_prime, simulated, observed)
    pearson = _evaluate_metric("pearson_correlation", pearson_correlation, simulated, observed)
    bias = _evaluate_metric("relative_mean_bias", relative_mean_bias, simulated, observed)
    outcomes = (kge, pearson, bias)
    status = "pass" if all(outcome.status == "pass" for outcome in outcomes) else "not_comparable"
    return DresdenHoldoutScore(
        status=status,
        expected_days=pairing.expected_days,
        valid_days=pairing.valid_days,
        valid_fraction=pairing.valid_fraction,
        invalid_pair_days=pairing.invalid_pair_days,
        invalid_observed_days=pairing.invalid_observed_days,
        missing_glofas_days=pairing.missing_glofas_days,
        nonfinite_glofas_days=pairing.nonfinite_glofas_days,
        modified_kge_prime=kge,
        pearson_correlation=pearson,
        relative_mean_bias=bias,
    )
