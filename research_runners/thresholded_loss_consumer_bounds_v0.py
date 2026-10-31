# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative counterfactual bounds for a *declared* thresholded loss view.

Assumption: every omitted nonnegative asset-event loss is <= explicit maximum.
NOT a claim that OpenQuake `risk_by_event` omitted rows or uses this formula.
A source reviewer must independently establish dropped record counts and rule.
The bound is on a lossy view, not insured coverage or scientific calibration.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction


class LossBoundError(ValueError):
    pass


@dataclass(frozen=True)
class Interval:
    lower_eur: int
    upper_eur: int


def _money(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 10**16:
        raise LossBoundError(f'{name} requires bounded nonnegative integer EUR')
    return value


def event_loss_interval(*, retained_loss_eur: int, omitted_count: int,
                        max_omitted_eur: int) -> Interval:
    """Worst-case [observed, observed+n*max omitted] under explicit assumption."""
    retained = _money(retained_loss_eur, 'retained_loss_eur')
    count = _money(omitted_count, 'omitted_count')
    maximum = _money(max_omitted_eur, 'max_omitted_eur')
    if count > 1_000_000:
        raise LossBoundError('declared omitted_count exceeds research budget')
    upper = retained + count * maximum
    if upper > 10**16:
        raise LossBoundError('loss upper bound exceeds supported amount')
    return Interval(retained, upper)


def occurrence_xl_interval(loss: Interval, *, attachment_eur: int,
                           limit_eur: int) -> Interval:
    """One synthetic occurrence layer; no reinstatement or policy semantics."""
    if type(loss) is not Interval:
        raise LossBoundError('bounded loss interval required')
    lower = _money(loss.lower_eur, 'loss.lower_eur')
    upper = _money(loss.upper_eur, 'loss.upper_eur')
    attachment = _money(attachment_eur, 'attachment_eur')
    limit = _money(limit_eur, 'limit_eur')
    if lower > upper or limit == 0:
        raise LossBoundError('invalid loss interval or layer')
    apply = lambda loss: min(max(loss-attachment, 0), limit)
    return Interval(apply(lower), apply(upper))


def weighted_annual_loss_interval(worlds: tuple[tuple[Fraction, Interval], ...]) -> tuple[Fraction, Fraction]:
    if type(worlds) is not tuple or not worlds:
        raise LossBoundError('complete weighted world catalogue required')
    total = Fraction()
    lo = hi = Fraction()
    for entry in worlds:
        if type(entry) is not tuple or len(entry) != 2:
            raise LossBoundError('each world must be an exact (probability, interval) pair')
        weight, interval = entry
        if type(weight) is not Fraction or weight <= 0 or type(interval) is not Interval:
            raise LossBoundError('positive rational probability and interval required')
        lower = _money(interval.lower_eur, 'world.lower_eur')
        upper = _money(interval.upper_eur, 'world.upper_eur')
        if lower > upper:
            raise LossBoundError('world loss interval inverted')
        total += weight
        lo += weight*lower
        hi += weight*upper
    if total != 1:
        raise LossBoundError('world probabilities must sum to one')
    return lo, hi


def weighted_exceedance_bounds(worlds: tuple[tuple[Fraction, Interval], ...],
                               *, threshold_eur: int) -> tuple[Fraction, Fraction]:
    """Strict P(annual loss > threshold) lower/upper; no implied time mapping."""
    threshold = _money(threshold_eur, 'threshold_eur')
    weighted_annual_loss_interval(worlds)  # validates probability measure
    sure = sum((p for p, i in worlds if i.lower_eur > threshold), Fraction())
    possible = sum((p for p, i in worlds if i.upper_eur > threshold), Fraction())
    return sure, possible
