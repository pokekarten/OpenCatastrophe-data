# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed time/completeness primitives for the Dresden hydrology holdout.

The preregistered comparison contract is now explicit:

- PEGELONLINE timestamps are interpreted as year-round Central European
  standard time (fixed UTC+01:00), never as a daylight-saving timezone;
- the source sampling interval is supplied explicitly by the caller after it
  has been frozen from source metadata;
- GloFAS ``dis24`` is a 24-hour mean whose timestamp marks the end of the
  averaging period, so a value at UTC timestamp ``T`` maps to ``[T-24h, T)``;
- a source window is valid only when at least 90% of its expected regular-grid
  observations are present and finite;
- the observed daily discharge paired to a valid GloFAS day is the arithmetic
  mean of those finite source-Q samples on that exact frozen grid;
- duplicate, off-grid or out-of-window timestamps fail closed.

This module does not select a GloFAS grid cell, interpolate missing values,
search for a better time shift or compute skill metrics.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Iterable, NamedTuple

SECONDS_PER_DAY = 24 * 60 * 60
PEGELONLINE_STANDARD_OFFSET = timezone(timedelta(hours=1))
UTC = timezone.utc
DRESDEN_HOLDOUT_WINDOW_START_UTC = datetime(2020, 1, 1, tzinfo=UTC)
DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE = datetime(2024, 1, 1, tzinfo=UTC)
DRESDEN_HOLDOUT_EXPECTED_DAYS = (
    DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE - DRESDEN_HOLDOUT_WINDOW_START_UTC
).days
DRESDEN_HOLDOUT_FIRST_GLOFAS_TIMESTAMP_UTC = DRESDEN_HOLDOUT_WINDOW_START_UTC + timedelta(days=1)
DRESDEN_HOLDOUT_LAST_GLOFAS_TIMESTAMP_UTC = DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE


class HydrologyWindowError(ValueError):
    """Raised when a hydrology comparison-window contract fails closed."""


class WindowCompleteness(NamedTuple):
    expected_count: int
    present_count: int
    finite_count: int
    required_finite_count: int
    finite_fraction: float
    valid: bool


class ObservedDischargeWindow(NamedTuple):
    window_start_utc: datetime
    window_end_utc: datetime
    completeness: WindowCompleteness
    mean_discharge_m3s: float | None


def dresden_holdout_glofas_timestamps() -> tuple[datetime, ...]:
    """Return the frozen chronological GloFAS ``dis24`` labels for 2020-2023."""

    return tuple(
        DRESDEN_HOLDOUT_FIRST_GLOFAS_TIMESTAMP_UTC + timedelta(days=index)
        for index in range(DRESDEN_HOLDOUT_EXPECTED_DAYS)
    )


def pegelonline_standard_time_to_utc(value: str) -> datetime:
    """Interpret a PEGELONLINE local timestamp as fixed CET (UTC+01:00)."""

    if type(value) is not str or not value.strip():
        raise HydrologyWindowError("PEGELONLINE timestamp must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HydrologyWindowError("PEGELONLINE timestamp must be ISO-8601 local time") from exc
    if parsed.tzinfo is not None or parsed.utcoffset() is not None:
        raise HydrologyWindowError(
            "PEGELONLINE source timestamp must be timezone-naive before fixed CET conversion"
        )
    return parsed.replace(tzinfo=PEGELONLINE_STANDARD_OFFSET).astimezone(UTC)


def _require_utc_whole_second(value: datetime, where: str) -> datetime:
    if not isinstance(value, datetime):
        raise HydrologyWindowError(f"{where} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise HydrologyWindowError(f"{where} must be timezone-aware UTC")
    if value.microsecond != 0:
        raise HydrologyWindowError(f"{where} must be aligned to whole seconds")
    return value


def glofas_dis24_window(glofas_timestamp_utc: datetime) -> tuple[datetime, datetime]:
    """Return the fixed half-open 24-hour interval represented by GloFAS ``dis24``.

    CEMS documents the ``dis24`` timestamp as the end of the 24-hour averaging
    period. This function therefore performs no inference or empirical shift.
    """

    end = _require_utc_whole_second(glofas_timestamp_utc, "glofas_timestamp_utc")
    return end - timedelta(days=1), end


def expected_observations_per_24h(sampling_interval_seconds: int) -> int:
    """Return the exact number of source slots in one 24-hour comparison window."""

    if type(sampling_interval_seconds) is not int or sampling_interval_seconds <= 0:
        raise HydrologyWindowError("sampling_interval_seconds must be a positive integer")
    if SECONDS_PER_DAY % sampling_interval_seconds != 0:
        raise HydrologyWindowError(
            "sampling interval must divide the 24-hour comparison window exactly"
        )
    return SECONDS_PER_DAY // sampling_interval_seconds


def _inspect_source_window(
    observations: Iterable[tuple[datetime, float | int]],
    *,
    window_start_utc: datetime,
    sampling_interval_seconds: int,
) -> tuple[WindowCompleteness, tuple[float, ...]]:
    start = _require_utc_whole_second(window_start_utc, "window_start_utc")
    expected_count = expected_observations_per_24h(sampling_interval_seconds)
    window_end_utc = start + timedelta(days=1)
    seen: set[datetime] = set()
    finite_values: list[float] = []

    try:
        iterator = iter(observations)
    except TypeError as exc:
        raise HydrologyWindowError("observations must be an iterable of timestamp/value pairs") from exc

    for index, item in enumerate(iterator):
        if type(item) not in {tuple, list} or len(item) != 2:
            raise HydrologyWindowError(
                f"observations[{index}] must be a two-item timestamp/value pair"
            )
        timestamp, value = item
        timestamp = _require_utc_whole_second(timestamp, f"observations[{index}] timestamp")
        if timestamp < start or timestamp >= window_end_utc:
            raise HydrologyWindowError(f"observations[{index}] timestamp is outside the 24-hour window")
        delta = timestamp - start
        delta_seconds = delta.days * SECONDS_PER_DAY + delta.seconds
        if delta_seconds % sampling_interval_seconds != 0:
            raise HydrologyWindowError(f"observations[{index}] timestamp is off the frozen sampling grid")
        if timestamp in seen:
            raise HydrologyWindowError(f"duplicate source timestamp: {timestamp.isoformat()}")
        seen.add(timestamp)

        if type(value) not in {int, float}:
            raise HydrologyWindowError(f"observations[{index}] value must be numeric and not boolean")
        try:
            numeric = float(value)
        except OverflowError as exc:
            raise HydrologyWindowError(f"observations[{index}] value cannot be represented safely") from exc
        if math.isfinite(numeric):
            finite_values.append(numeric)

    present_count = len(seen)
    finite_count = len(finite_values)
    required_finite_count = (9 * expected_count + 9) // 10
    finite_fraction = finite_count / expected_count
    completeness = WindowCompleteness(
        expected_count=expected_count,
        present_count=present_count,
        finite_count=finite_count,
        required_finite_count=required_finite_count,
        finite_fraction=finite_fraction,
        valid=finite_count >= required_finite_count,
    )
    return completeness, tuple(finite_values)


def assess_source_window(
    observations: Iterable[tuple[datetime, float | int]],
    *,
    window_start_utc: datetime,
    sampling_interval_seconds: int,
) -> WindowCompleteness:
    """Assess the preregistered 90% source-observation completeness rule.

    ``window_start_utc`` identifies the start of the already-established
    GloFAS-aligned 24-hour interval. This function does not infer, shift or
    search for that boundary.
    """

    completeness, _finite_values = _inspect_source_window(
        observations,
        window_start_utc=window_start_utc,
        sampling_interval_seconds=sampling_interval_seconds,
    )
    return completeness


def aggregate_observed_discharge_for_glofas_dis24(
    observations: Iterable[tuple[datetime, float | int]],
    *,
    glofas_timestamp_utc: datetime,
    sampling_interval_seconds: int,
) -> ObservedDischargeWindow:
    """Aggregate source ``Q`` for one preregistered GloFAS ``dis24`` window.

    The arithmetic mean is returned only when the 90% finite-observation gate
    passes. Missing/non-finite samples are never interpolated or substituted.
    ``mean_discharge_m3s`` is ``None`` for an invalid comparison day.
    """

    window_start_utc, window_end_utc = glofas_dis24_window(glofas_timestamp_utc)
    completeness, finite_values = _inspect_source_window(
        observations,
        window_start_utc=window_start_utc,
        sampling_interval_seconds=sampling_interval_seconds,
    )
    if not completeness.valid:
        return ObservedDischargeWindow(
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
            completeness=completeness,
            mean_discharge_m3s=None,
        )

    try:
        total = math.fsum(finite_values)
    except OverflowError as exc:
        raise HydrologyWindowError("observed discharge sum must remain finite") from exc
    if not math.isfinite(total):
        raise HydrologyWindowError("observed discharge sum must remain finite")
    mean_discharge_m3s = total / len(finite_values)
    if not math.isfinite(mean_discharge_m3s):
        raise HydrologyWindowError("observed discharge mean must remain finite")
    return ObservedDischargeWindow(
        window_start_utc=window_start_utc,
        window_end_utc=window_end_utc,
        completeness=completeness,
        mean_discharge_m3s=mean_discharge_m3s,
    )