# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic *synthetic-only* rain -> sewer-level lag challenge.

The original Blue Heart rain and sewer ZIP central directories have a complete
index path crosswalk, but real telemetry, UTC logger provenance, periods,
authorizations and model applicability are NOT inspected by this runner.
It accepts no file paths, provider assets, geographic sites or claimed losses.

Two separately generated synthetic storm windows prove fixed-lag estimation,
quality/time/unit gating and independent holdout scoring. This is a software
contract test, NOT a hydrologic calibration or an insured-loss model.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from research_runners.blue_heart_index_preflight_v0 import (
    BlueHeartPreflightError,
    explicit_utc_timestamp,
    parse_quality_label,
)

PROFILE = "blue-heart-synthetic-rain-sewer-lag-challenge-v0"
STEP_SECONDS = 300
MAX_POINTS = 96
CANDIDATE_LAGS = (0, 1, 2, 3, 4)
FIXED_DECAY = 0.55


class SyntheticRainSewerError(ValueError):
    """Unverified measurement semantics or scientifically invalid fit."""


@dataclass(frozen=True)
class SyntheticSample:
    timestamp: str
    rainfall_depth_mm_per_step: float
    sewer_level_mm: float
    rain_qc: str = "1"
    sewer_qc: str = "1"


@dataclass(frozen=True)
class SyntheticStorm:
    name: str
    samples: tuple[SyntheticSample, ...]
    source_class: str = "synthetic_test_only"
    rainfall_unit: str = "mm_per_5_minutes"
    sewer_level_unit: str = "mm"


def _number(value: object, field: str, lower: float, upper: float) -> float:
    if type(value) not in (float, int):
        raise SyntheticRainSewerError(f"{field} must be numeric")
    try:
        numeric = float(value)
    except (ValueError, OverflowError) as exc:
        raise SyntheticRainSewerError(f"{field} outside numeric limits") from exc
    if not math.isfinite(numeric) or not lower <= numeric <= upper:
        raise SyntheticRainSewerError(f"{field} outside reviewed bounds")
    return numeric


def validate_storm(storm: SyntheticStorm) -> tuple[list[datetime], list[float], list[float], float]:
    """Explicit UTC, fixed five-minute, QC-good, no imputation or unknown units."""

    if type(storm) is not SyntheticStorm or storm.source_class != "synthetic_test_only":
        raise SyntheticRainSewerError("real or unknown source material is not accepted")
    if storm.rainfall_unit != "mm_per_5_minutes" or storm.sewer_level_unit != "mm":
        raise SyntheticRainSewerError("incorrect rainfall/sewer measurement units")
    if not isinstance(storm.name, str) or not storm.name.startswith("SYNTHETIC_"):
        raise SyntheticRainSewerError("invalid synthetic event identity")
    if not 20 <= len(storm.samples) <= MAX_POINTS:
        raise SyntheticRainSewerError("unbounded or incomplete event window")

    timestamps: list[datetime] = []
    rainfall: list[float] = []
    level: list[float] = []
    for row in storm.samples:
        if type(row) is not SyntheticSample:
            raise SyntheticRainSewerError("unrecognized synthetic row type")
        try:
            instant = datetime.fromisoformat(explicit_utc_timestamp(row.timestamp))
            rain_status = parse_quality_label(row.rain_qc)[0]
            level_status = parse_quality_label(row.sewer_qc)[0]
        except BlueHeartPreflightError as exc:
            raise SyntheticRainSewerError("invalid UTC timestamp or QC label") from exc
        if rain_status != "good" or level_status != "good":
            raise SyntheticRainSewerError("suspect/bad observations require an explicit exclusion policy")
        if timestamps and (instant - timestamps[-1]).total_seconds() != STEP_SECONDS:
            raise SyntheticRainSewerError("time gap, overlapping clock or wrong step")
        timestamps.append(instant)
        rainfall.append(_number(row.rainfall_depth_mm_per_step, "rainfall", 0, 40))
        level.append(_number(row.sewer_level_mm, "sewer level", 0, 2500))

    if sum(rainfall) <= 0:
        raise SyntheticRainSewerError("dry window cannot estimate response lag")
    if any(v != 0 for v in rainfall[:4]):
        raise SyntheticRainSewerError("initial dry four-bin calibration baseline required")
    baseline = level[0]
    if any(abs(level[i] - baseline) > 1e-9 for i in range(4)):
        raise SyntheticRainSewerError("initial sewer baseline is not stationary")
    return timestamps, rainfall, level, baseline


def _estimate_response(
    rain: Sequence[float],
    level: Sequence[float],
    baseline: float,
    lag_steps: int,
    decay: float,
) -> tuple[float, float]:
    """Fit response gain with causal fixed first-order reservoir decay."""

    if not 0 <= lag_steps <= 4:
        raise SyntheticRainSewerError("unsupported response lag")
    x = [(rain[t - lag_steps] if t >= lag_steps else 0.0) for t in range(1, len(rain))]
    y = [
        level[t] - baseline - decay * (level[t - 1] - baseline)
        for t in range(1, len(level))
    ]
    denom = sum(v * v for v in x)
    if denom <= 0:
        raise SyntheticRainSewerError("no rainfall excitation at the candidate lag")
    gain = sum(v * w for v, w in zip(x, y)) / denom
    if not math.isfinite(gain) or not 0 <= gain <= 500:
        raise SyntheticRainSewerError("nonphysical synthetic rainfall response gain")
    mse = sum((w - gain * v) ** 2 for v, w in zip(x, y)) / len(y)
    return gain, math.sqrt(mse)


def _holdout_rmse(
    rain: Sequence[float], levels: Sequence[float], baseline: float,
    *, lag_steps: int, gain: float, decay: float,
) -> float:
    """No fitting or parameter selection on holdout observations."""

    predicted = baseline
    errors: list[float] = []
    for t in range(len(rain)):
        if t > 0:
            predicted = baseline + decay * (predicted - baseline) + gain * (
                rain[t - lag_steps] if t >= lag_steps else 0.0
            )
        errors.append(predicted - levels[t])
    return math.sqrt(sum(x * x for x in errors) / len(errors))


def challenge(train: SyntheticStorm, holdout: SyntheticStorm) -> dict[str, object]:
    """Fit on event 1; independently score event 2 with fixed settings."""

    tr_time, tr_rain, tr_level, tr_base = validate_storm(train)
    ho_time, ho_rain, ho_level, ho_base = validate_storm(holdout)
    if tr_time[-1] >= ho_time[0] or train.name == holdout.name:
        raise SyntheticRainSewerError("training and holdout events must be separate")
    fits = [
        (*_estimate_response(tr_rain, tr_level, tr_base, lag, FIXED_DECAY), lag)
        for lag in CANDIDATE_LAGS
    ]
    gain, train_rmse, selected = min(fits, key=lambda f: (f[1], f[2]))
    holdout_rmse = _holdout_rmse(
        ho_rain, ho_level, ho_base,
        lag_steps=selected, gain=gain, decay=FIXED_DECAY,
    )
    return {
        "profile": PROFILE,
        "source_class": "synthetic_test_only",
        "training_points": len(tr_rain),
        "holdout_points": len(ho_rain),
        "candidate_lags_minutes": [v * STEP_SECONDS // 60 for v in CANDIDATE_LAGS],
        "selected_lag_minutes": selected * STEP_SECONDS // 60,
        "lag_decay_fixed_not_fitted": FIXED_DECAY,
        "calibrated_synthetic_gain_mm_level_per_mm_rain": round(gain, 9),
        "training_response_rmse_mm": round(train_rmse, 9),
        "independent_holdout_rmse_mm": round(holdout_rmse, 9),
        "original_blue_heart_telemetry_used": False,
        "device_timezone_verified": False,
        "real_hydraulic_calibration_completed": False,
        "cat_event_set_or_insurer_loss_admitted": False,
    }


def synthetic_storm(name: str, start: str, rainfall: Sequence[float], *,
                    lag_steps: int = 2, gain: float = 3.5,
                    baseline: float = 100.0) -> SyntheticStorm:
    """Generate a causally lagged synthetic fixture with explicit UTC instants."""

    if not isinstance(name, str) or not name.startswith("SYNTHETIC_"):
        raise SyntheticRainSewerError("synthetic fixture name is required")
    if len(rainfall) < 20 or len(rainfall) > MAX_POINTS:
        raise SyntheticRainSewerError("invalid synthetic fixture length")
    try:
        at = datetime.fromisoformat(explicit_utc_timestamp(start))
    except BlueHeartPreflightError as exc:
        raise SyntheticRainSewerError("synthetic start must specify UTC offset") from exc
    gain = _number(gain, "synthetic gain", 0, 500)
    decay = FIXED_DECAY
    base = _number(baseline, "synthetic baseline", 0, 2500)
    if type(lag_steps) is not int or lag_steps not in CANDIDATE_LAGS:
        raise SyntheticRainSewerError("unsupported synthetic lag")
    rows: list[SyntheticSample] = []
    response = 0.0
    for i, depth in enumerate(rainfall):
        val = _number(depth, "synthetic rainfall", 0, 40)
        if i:
            forcing = _number(rainfall[i - lag_steps], "synthetic rainfall", 0, 40) if i >= lag_steps else 0.0
            response = decay * response + gain * forcing
        rows.append(SyntheticSample(
            timestamp=(at + timedelta(seconds=STEP_SECONDS * i)).isoformat(),
            rainfall_depth_mm_per_step=val,
            sewer_level_mm=base + response,
        ))
    return SyntheticStorm(name=name, samples=tuple(rows))


def demo() -> dict[str, object]:
    """Two different, disjoint deterministic synthetic storms; no provider bytes."""

    rain_train = ([0.0] * 5 + [0.2, 1.5, 5.0, 9.0, 4.0, 1.5, 0.2] + [0.0] * 24)
    rain_holdout = ([0.0] * 7 + [0.6, 2.3, 7.0, 4.0, 0.5] + [0.0] * 24)
    train = synthetic_storm("SYNTHETIC_TRAIN", "2026-04-12T00:00:00+00:00", rain_train)
    holdout = synthetic_storm("SYNTHETIC_HOLDOUT", "2026-04-15T00:00:00+00:00", rain_holdout)
    return challenge(train, holdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Blue Heart synthetic rain/sewer lag software challenge")
    parser.add_argument("--synthetic-demo", action="store_true", help="Run only internally generated synthetic observations")
    args = parser.parse_args()
    if not args.synthetic_demo:
        parser.error("only --synthetic-demo is supported; original source inputs are not admitted")
    print(json.dumps(demo(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
