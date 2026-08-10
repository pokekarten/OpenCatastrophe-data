# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic hydrology metrics used by preregistered validation workflows."""

from __future__ import annotations

import math
from collections.abc import Sequence


class MetricInputError(ValueError):
    """Raised when a metric cannot be evaluated without ambiguous semantics."""


def _finite_floats(values: Sequence[float]) -> tuple[float, ...]:
    converted: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MetricInputError("metric inputs must be finite numeric values")
        number = float(value)
        if not math.isfinite(number):
            raise MetricInputError("metric inputs must be finite numeric values")
        converted.append(number)
    return tuple(converted)


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
    two pairs, non-finite/non-numeric values, zero means, or zero variance in
    either series.
    """

    if len(simulated) != len(observed):
        raise MetricInputError("simulated and observed series must have equal length")
    if len(simulated) < 2:
        raise MetricInputError("at least two paired values are required")

    simulated_values = _finite_floats(simulated)
    observed_values = _finite_floats(observed)

    count = len(simulated_values)
    mean_simulated = math.fsum(simulated_values) / count
    mean_observed = math.fsum(observed_values) / count
    if mean_simulated == 0.0 or mean_observed == 0.0:
        raise MetricInputError("KGE' requires non-zero means")

    simulated_centered = tuple(value - mean_simulated for value in simulated_values)
    observed_centered = tuple(value - mean_observed for value in observed_values)
    simulated_ss = math.fsum(value * value for value in simulated_centered)
    observed_ss = math.fsum(value * value for value in observed_centered)
    if simulated_ss == 0.0 or observed_ss == 0.0:
        raise MetricInputError("KGE' requires non-zero variance in both series")

    covariance_sum = math.fsum(
        simulated_delta * observed_delta
        for simulated_delta, observed_delta in zip(simulated_centered, observed_centered)
    )
    correlation = covariance_sum / math.sqrt(simulated_ss * observed_ss)
    beta = mean_simulated / mean_observed
    gamma = (
        (math.sqrt(simulated_ss) / mean_simulated)
        / (math.sqrt(observed_ss) / mean_observed)
    )

    return 1.0 - math.sqrt(
        (correlation - 1.0) ** 2 + (beta - 1.0) ** 2 + (gamma - 1.0) ** 2
    )
