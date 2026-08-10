# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic hydrology metrics used by preregistered validation workflows."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


class MetricInputError(ValueError):
    """Raised when a metric cannot be evaluated without ambiguous semantics."""


def _require_finite(value: float, *, context: str) -> float:
    if not math.isfinite(value):
        raise MetricInputError(f"{context} must remain finite")
    return value


def _finite_fsum(values: Iterable[float], *, context: str) -> float:
    try:
        total = math.fsum(values)
    except OverflowError as exc:
        raise MetricInputError(f"{context} must remain finite") from exc
    return _require_finite(total, context=context)


def _finite_product(left: float, right: float, *, context: str) -> float:
    return _require_finite(left * right, context=context)


def _finite_floats(values: Sequence[float]) -> tuple[float, ...]:
    converted: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MetricInputError("metric inputs must be finite numeric values")
        try:
            number = float(value)
        except OverflowError as exc:
            raise MetricInputError("metric inputs must be finite numeric values") from exc
        if not math.isfinite(number):
            raise MetricInputError("metric inputs must be finite numeric values")
        converted.append(number)
    return tuple(converted)


def relative_mean_bias(simulated: Sequence[float], observed: Sequence[float]) -> float:
    """Return preregistered relative mean bias.

    The Dresden/GloFAS comparison contract defines this metric as::

        (mean_model / mean_observed) - 1

    Inputs fail closed when the ratio would be undefined or ambiguous: unequal
    lengths, no paired values, non-finite/non-numeric values, or a zero observed
    mean. A zero simulated mean is valid and yields ``-1`` when the observed mean
    is non-zero.
    """

    if len(simulated) != len(observed):
        raise MetricInputError("simulated and observed series must have equal length")
    if not simulated:
        raise MetricInputError("at least one paired value is required")

    simulated_values = _finite_floats(simulated)
    observed_values = _finite_floats(observed)

    count = len(simulated_values)
    mean_simulated = _require_finite(
        _finite_fsum(simulated_values, context="relative mean bias simulated mean") / count,
        context="relative mean bias simulated mean",
    )
    mean_observed = _require_finite(
        _finite_fsum(observed_values, context="relative mean bias observed mean") / count,
        context="relative mean bias observed mean",
    )
    if mean_observed == 0.0:
        raise MetricInputError("relative mean bias requires a non-zero observed mean")

    ratio = _require_finite(
        mean_simulated / mean_observed,
        context="relative mean bias ratio",
    )
    return _require_finite(ratio - 1.0, context="relative mean bias result")


def pearson_correlation(simulated: Sequence[float], observed: Sequence[float]) -> float:
    """Return the preregistered Pearson correlation coefficient.

    Pearson correlation is defined for at least two paired finite observations
    with non-zero variance in both series. Unlike KGE', zero series means are
    valid. Numeric overflow or underflow in required intermediates fails closed.
    """

    if len(simulated) != len(observed):
        raise MetricInputError("simulated and observed series must have equal length")
    if len(simulated) < 2:
        raise MetricInputError("at least two paired values are required")

    simulated_values = _finite_floats(simulated)
    observed_values = _finite_floats(observed)
    count = len(simulated_values)

    mean_simulated = _require_finite(
        _finite_fsum(simulated_values, context="Pearson simulated mean") / count,
        context="Pearson simulated mean",
    )
    mean_observed = _require_finite(
        _finite_fsum(observed_values, context="Pearson observed mean") / count,
        context="Pearson observed mean",
    )
    simulated_centered = tuple(
        _require_finite(value - mean_simulated, context="Pearson simulated centered value")
        for value in simulated_values
    )
    observed_centered = tuple(
        _require_finite(value - mean_observed, context="Pearson observed centered value")
        for value in observed_values
    )
    simulated_ss = _finite_fsum(
        (
            _finite_product(value, value, context="Pearson simulated squared deviation")
            for value in simulated_centered
        ),
        context="Pearson simulated variance sum",
    )
    observed_ss = _finite_fsum(
        (
            _finite_product(value, value, context="Pearson observed squared deviation")
            for value in observed_centered
        ),
        context="Pearson observed variance sum",
    )
    if simulated_ss == 0.0 or observed_ss == 0.0:
        raise MetricInputError("Pearson correlation requires non-zero variance in both series")

    covariance_sum = _finite_fsum(
        (
            _finite_product(
                simulated_delta,
                observed_delta,
                context="Pearson covariance product",
            )
            for simulated_delta, observed_delta in zip(simulated_centered, observed_centered)
        ),
        context="Pearson covariance sum",
    )
    denominator_squared = _finite_product(
        simulated_ss,
        observed_ss,
        context="Pearson correlation denominator",
    )
    if denominator_squared == 0.0:
        raise MetricInputError("Pearson correlation denominator must remain positive")
    return _require_finite(
        covariance_sum / math.sqrt(denominator_squared),
        context="Pearson correlation",
    )


def modified_kge_prime(simulated: Sequence[float], observed: Sequence[float]) -> float:
    """Return modified Kling-Gupta Efficiency (KGE').

    This follows the CEMS/GloFAS convention based on Kling et al. (2012):

        KGE' = 1 - sqrt((r - 1)^2 + (beta - 1)^2 + (gamma - 1)^2)
        beta = mean(simulated) / mean(observed)
        gamma = CV(simulated) / CV(observed)

    where ``r`` is the Pearson correlation coefficient and ``CV = sigma / mean``.
    See the CEMS hydrological model performance documentation referenced by the
    preregistered Dresden/GloFAS source review.

    Inputs fail closed when KGE' would be undefined: unequal lengths, fewer than
    two pairs, non-finite/non-numeric values, zero means, zero variance, or any
    non-finite intermediate calculation.
    """

    if len(simulated) != len(observed):
        raise MetricInputError("simulated and observed series must have equal length")
    if len(simulated) < 2:
        raise MetricInputError("at least two paired values are required")

    simulated_values = _finite_floats(simulated)
    observed_values = _finite_floats(observed)

    count = len(simulated_values)
    mean_simulated = _require_finite(
        _finite_fsum(simulated_values, context="KGE' simulated mean") / count,
        context="KGE' simulated mean",
    )
    mean_observed = _require_finite(
        _finite_fsum(observed_values, context="KGE' observed mean") / count,
        context="KGE' observed mean",
    )
    if mean_simulated == 0.0 or mean_observed == 0.0:
        raise MetricInputError("KGE' requires non-zero means")

    simulated_centered = tuple(
        _require_finite(value - mean_simulated, context="KGE' simulated centered value")
        for value in simulated_values
    )
    observed_centered = tuple(
        _require_finite(value - mean_observed, context="KGE' observed centered value")
        for value in observed_values
    )
    simulated_ss = _finite_fsum(
        (
            _finite_product(value, value, context="KGE' simulated squared deviation")
            for value in simulated_centered
        ),
        context="KGE' simulated variance sum",
    )
    observed_ss = _finite_fsum(
        (
            _finite_product(value, value, context="KGE' observed squared deviation")
            for value in observed_centered
        ),
        context="KGE' observed variance sum",
    )
    if simulated_ss == 0.0 or observed_ss == 0.0:
        raise MetricInputError("KGE' requires non-zero variance in both series")

    covariance_sum = _finite_fsum(
        (
            _finite_product(
                simulated_delta,
                observed_delta,
                context="KGE' covariance product",
            )
            for simulated_delta, observed_delta in zip(simulated_centered, observed_centered)
        ),
        context="KGE' covariance sum",
    )
    correlation_denominator_squared = _finite_product(
        simulated_ss,
        observed_ss,
        context="KGE' correlation denominator",
    )
    if correlation_denominator_squared == 0.0:
        raise MetricInputError("KGE' correlation denominator must remain positive")
    correlation = _require_finite(
        covariance_sum / math.sqrt(correlation_denominator_squared),
        context="KGE' correlation",
    )
    beta = _require_finite(mean_simulated / mean_observed, context="KGE' beta")
    simulated_cv = _require_finite(
        math.sqrt(simulated_ss) / mean_simulated,
        context="KGE' simulated coefficient of variation",
    )
    observed_cv = _require_finite(
        math.sqrt(observed_ss) / mean_observed,
        context="KGE' observed coefficient of variation",
    )
    gamma = _require_finite(simulated_cv / observed_cv, context="KGE' gamma")

    correlation_residual = _require_finite(
        correlation - 1.0,
        context="KGE' correlation residual",
    )
    beta_residual = _require_finite(beta - 1.0, context="KGE' beta residual")
    gamma_residual = _require_finite(gamma - 1.0, context="KGE' gamma residual")
    distance_squared = _finite_fsum(
        (
            _finite_product(
                correlation_residual,
                correlation_residual,
                context="KGE' correlation residual square",
            ),
            _finite_product(
                beta_residual,
                beta_residual,
                context="KGE' beta residual square",
            ),
            _finite_product(
                gamma_residual,
                gamma_residual,
                context="KGE' gamma residual square",
            ),
        ),
        context="KGE' distance",
    )
    return _require_finite(1.0 - math.sqrt(distance_squared), context="KGE' result")
