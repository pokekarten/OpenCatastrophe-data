# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Build the frozen Dresden PEGELONLINE/GloFAS holdout comparison pairs.

This module is the boundary between acquisition/alignment and skill metrics.
It deliberately does not compute KGE', Pearson correlation or bias. It turns
already selected-cell GloFAS ``dis24`` values plus UTC-converted PEGELONLINE Q
samples into one deterministic paired vector under the preregistered contract.

Key guarantees:

- exactly 1,461 physical UTC comparison days are expected (2020-2023);
- GloFAS uses the corresponding end labels 2020-01-02 through 2024-01-01;
- PEGELONLINE samples must lie inside the physical holdout and are never
  interpolated or shifted;
- each source day is aggregated only after the per-window >=90% finite-sample
  gate from :mod:`scripts.hydrology_window` passes;
- missing/non-finite GloFAS values make that day invalid rather than changing
  the denominator;
- extra or duplicate GloFAS labels and source samples outside the holdout fail
  closed instead of being silently ignored;
- output pair order is the frozen chronological GloFAS label order and is
  independent of input iteration order.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Iterable, NamedTuple

from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE,
    DRESDEN_HOLDOUT_WINDOW_START_UTC,
    HydrologyWindowError,
    aggregate_observed_discharge_for_glofas_dis24,
    dresden_holdout_glofas_timestamps,
)


class HoldoutPairError(ValueError):
    """Raised when the frozen Dresden pairing contract fails closed."""


class HoldoutDayPair(NamedTuple):
    glofas_timestamp_utc: datetime
    observed_mean_discharge_m3s: float
    glofas_mean_discharge_m3s: float


class HoldoutPairing(NamedTuple):
    expected_days: int
    valid_days: int
    valid_fraction: float
    invalid_pair_days: int
    invalid_observed_days: int
    missing_glofas_days: int
    nonfinite_glofas_days: int
    pairs: tuple[HoldoutDayPair, ...]


def required_pegelonline_utc_coverage() -> tuple[datetime, datetime]:
    """Return the exact UTC bounds that the parsed long-term JSON must cover.

    The provider-facing long-term download form may require broader civil-date
    inputs. Acquisition code must preserve that exact request separately, parse
    the JSON timestamps using their explicit source offsets, convert to UTC and
    trim to these immutable physical holdout bounds before pairing.
    """

    return (
        DRESDEN_HOLDOUT_WINDOW_START_UTC,
        DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE,
    )


def _utc_whole_second(value: object, where: str) -> datetime:
    if not isinstance(value, datetime):
        raise HoldoutPairError(f"{where} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise HoldoutPairError(f"{where} must be timezone-aware UTC")
    if value.microsecond != 0:
        raise HoldoutPairError(f"{where} must use whole seconds")
    return value


def _finite_or_missing_model_value(value: object, where: str) -> float | None:
    if type(value) not in {int, float}:
        raise HoldoutPairError(f"{where} must be numeric and not boolean")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise HoldoutPairError(f"{where} cannot be represented safely") from exc
    return numeric if math.isfinite(numeric) else None


def build_dresden_holdout_pairs(
    *,
    pegelonline_observations_utc: Iterable[tuple[datetime, float | int]],
    glofas_dis24_values: Iterable[tuple[datetime, float | int]],
    sampling_interval_seconds: int,
) -> HoldoutPairing:
    """Build deterministic valid-day discharge pairs for the frozen holdout."""

    expected_labels = tuple(dresden_holdout_glofas_timestamps())
    if len(expected_labels) != DRESDEN_HOLDOUT_EXPECTED_DAYS:
        raise HoldoutPairError("internal holdout label count does not match frozen denominator")
    expected_label_set = set(expected_labels)

    try:
        model_iterator = iter(glofas_dis24_values)
    except TypeError as exc:
        raise HoldoutPairError("glofas_dis24_values must be an iterable of timestamp/value pairs") from exc

    model_by_label: dict[datetime, float | None] = {}
    nonfinite_glofas_days = 0
    for index, item in enumerate(model_iterator):
        if type(item) not in {tuple, list} or len(item) != 2:
            raise HoldoutPairError(
                f"glofas_dis24_values[{index}] must be a two-item timestamp/value pair"
            )
        raw_timestamp, raw_value = item
        timestamp = _utc_whole_second(raw_timestamp, f"glofas_dis24_values[{index}] timestamp")
        if timestamp not in expected_label_set:
            raise HoldoutPairError(
                f"unexpected GloFAS dis24 label outside frozen holdout: {timestamp.isoformat()}"
            )
        if timestamp in model_by_label:
            raise HoldoutPairError(f"duplicate GloFAS dis24 label: {timestamp.isoformat()}")
        value = _finite_or_missing_model_value(
            raw_value,
            f"glofas_dis24_values[{index}] value",
        )
        if value is None:
            nonfinite_glofas_days += 1
        model_by_label[timestamp] = value

    try:
        source_iterator = iter(pegelonline_observations_utc)
    except TypeError as exc:
        raise HoldoutPairError(
            "pegelonline_observations_utc must be an iterable of timestamp/value pairs"
        ) from exc

    observations_by_label: dict[datetime, list[tuple[datetime, float | int]]] = {
        label: [] for label in expected_labels
    }
    seen_source_timestamps: set[datetime] = set()
    for index, item in enumerate(source_iterator):
        if type(item) not in {tuple, list} or len(item) != 2:
            raise HoldoutPairError(
                f"pegelonline_observations_utc[{index}] must be a two-item timestamp/value pair"
            )
        raw_timestamp, value = item
        timestamp = _utc_whole_second(
            raw_timestamp,
            f"pegelonline_observations_utc[{index}] timestamp",
        )
        if not (
            DRESDEN_HOLDOUT_WINDOW_START_UTC
            <= timestamp
            < DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE
        ):
            raise HoldoutPairError(
                f"PEGELONLINE observation outside frozen physical holdout: {timestamp.isoformat()}"
            )
        if timestamp in seen_source_timestamps:
            raise HoldoutPairError(f"duplicate PEGELONLINE timestamp: {timestamp.isoformat()}")
        seen_source_timestamps.add(timestamp)

        day_index = (timestamp - DRESDEN_HOLDOUT_WINDOW_START_UTC).days
        label = expected_labels[day_index]
        observations_by_label[label].append((timestamp, value))

    pairs: list[HoldoutDayPair] = []
    invalid_observed_days = 0
    missing_glofas_days = 0

    for label in expected_labels:
        try:
            observed = aggregate_observed_discharge_for_glofas_dis24(
                observations_by_label[label],
                glofas_timestamp_utc=label,
                sampling_interval_seconds=sampling_interval_seconds,
            )
        except HydrologyWindowError as exc:
            raise HoldoutPairError(
                f"PEGELONLINE window validation failed for {label.isoformat()}: {exc}"
            ) from exc

        if observed.mean_discharge_m3s is None:
            invalid_observed_days += 1

        if label not in model_by_label:
            missing_glofas_days += 1
            continue
        model_value = model_by_label[label]
        if model_value is None or observed.mean_discharge_m3s is None:
            continue

        pairs.append(
            HoldoutDayPair(
                glofas_timestamp_utc=label,
                observed_mean_discharge_m3s=observed.mean_discharge_m3s,
                glofas_mean_discharge_m3s=model_value,
            )
        )

    valid_days = len(pairs)
    invalid_pair_days = DRESDEN_HOLDOUT_EXPECTED_DAYS - valid_days
    return HoldoutPairing(
        expected_days=DRESDEN_HOLDOUT_EXPECTED_DAYS,
        valid_days=valid_days,
        valid_fraction=valid_days / DRESDEN_HOLDOUT_EXPECTED_DAYS,
        invalid_pair_days=invalid_pair_days,
        invalid_observed_days=invalid_observed_days,
        missing_glofas_days=missing_glofas_days,
        nonfinite_glofas_days=nonfinite_glofas_days,
        pairs=tuple(pairs),
    )
