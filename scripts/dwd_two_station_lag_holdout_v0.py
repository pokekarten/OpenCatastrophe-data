#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Chronological holdout of lag findings from two SHA-pinned DWD originals.

Use 2010-Q1 as PRIMARY lag-selection period and 2011-Q1 as predeclared temporal
holdout (same winter-season calendar months). Separately check a discovery
from all of 2010 against the SAME 2011-Q1 holdout. A split avoids choosing
the best lag on the validation values, but does not create independent storms
or establish propagation time, field calibration or statistical significance.
No raw measurements or event time stamps are logged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import sys

from scripts.dwd_two_station_paired_gust_v0 import (
    PairedWindBlocked, _extract, _paired_stats,
    FIRST_FILE, SECOND_FILE, FIRST_SHA, SECOND_SHA,
    FIRST_ROWS, SECOND_ROWS, START, END,
)
from scripts.dwd_paired_lag_clusters_v0 import (
    MAX_LAG_STEPS, WindEpisodesBlocked, _pearson, _lag_pair, _lag_profile,
)

PERIODS = {
    "discovery_same_season_2010_q1": (
        datetime(2010, 1, 1, 0, 0), datetime(2010, 3, 31, 23, 50), 12960,
    ),
    "discovery_all_2010": (
        datetime(2010, 1, 1, 0, 0), datetime(2010, 12, 31, 23, 50), 52560,
    ),
    "holdout_2011_q1": (
        datetime(2011, 1, 1, 0, 0), datetime(2011, 3, 31, 23, 50), 12960,
    ),
}
HOLDOUT_MONTHS = (
    ("2011-01", datetime(2011, 1, 1), datetime(2011, 1, 31, 23, 50), 4464),
    ("2011-02", datetime(2011, 2, 1), datetime(2011, 2, 28, 23, 50), 4032),
    ("2011-03", datetime(2011, 3, 1), datetime(2011, 3, 31, 23, 50), 4464),
)


class DWDHoldoutBlocked(ValueError):
    """The original source or strict calendar split is not adequate for this audit."""


def _slice_window(x: list[float], y: list[float], first: datetime,
                  last: datetime, expected_count: int, qx: list[int] | None = None,
                  qy: list[int] | None = None) -> tuple:
    if first < START or last > END or first > last:
        raise DWDHoldoutBlocked("requested analysis window is outside original measured calendar")
    if any(t.second or t.microsecond or t.minute % 10 for t in (first, last)):
        raise DWDHoldoutBlocked("holdout dates do not align with 10-minute UTC grid")
    start_step = int((first - START).total_seconds() // 600)
    end_step = int((last - START).total_seconds() // 600) + 1
    if end_step - start_step != expected_count or len(x) != len(y) or len(x) != 65520:
        raise DWDHoldoutBlocked("fixed holdout calendar sample count drifted")
    result = (x[start_step:end_step], y[start_step:end_step])
    if any(len(v) != expected_count for v in result):
        raise DWDHoldoutBlocked("calendar window boundaries incomplete")
    if qx is None or qy is None:
        return result
    if len(qx) != len(x) or len(qy) != len(y):
        raise DWDHoldoutBlocked("quality arrays differ from paired observations")
    return (*result, qx[start_step:end_step], qy[start_step:end_step])


def _fixed_lag_score(x: list[float], y: list[float], lag_minutes: int,
                     quality_x: list[int] | None = None,
                     quality_y: list[int] | None = None) -> dict:
    if (not isinstance(lag_minutes, int) or lag_minutes % 10
            or abs(lag_minutes) > MAX_LAG_STEPS * 10):
        raise DWDHoldoutBlocked("holdout lag differs from preapproved 10-minute steps")
    k = lag_minutes // 10
    a, b = _lag_pair(x, y, k)
    result = {
        "lag_minutes_station00348_relative_to_00003": lag_minutes,
        "paired_samples": len(a),
        "pearson_r_unadjusted": round(_pearson(a, b), 6),
    }
    if quality_x is not None and quality_y is not None:
        qa, qb = _lag_pair(quality_x, quality_y, k)
        q3 = [(v, w) for v, w, q, s in zip(a, b, qa, qb) if q == s == 3]
        if len(q3) < 4:
            raise DWDHoldoutBlocked("QN3 exact-lag validation insufficient")
        result["qn3_only"] = {
            "paired_samples": len(q3),
            "pearson_r_unadjusted": round(
                _pearson([v for v, _ in q3], [w for _, w in q3]), 6),
        }
    return result


def _evaluate_split(train: tuple[list[float], list[float]],
                    holdout: tuple[list[float], list[float], list[int], list[int]],
                    *, training_label: str) -> dict:
    tx, ty = train
    hx, hy, hqx, hqy = holdout
    discovery = _lag_profile(tx, ty)
    # Select lag using discovery only. Deterministic tie rule is minimum
    # absolute minute offset, then smallest signed minute value.
    tied = discovery["maximizing_lags_minutes_ties_preserved"]
    selected = min(tied, key=lambda lag: (abs(lag), lag))
    train_zero = _fixed_lag_score(tx, ty, 0)
    selected_train = _fixed_lag_score(tx, ty, selected)
    holdout_zero = _fixed_lag_score(hx, hy, 0, hqx, hqy)
    holdout_selected = _fixed_lag_score(hx, hy, selected, hqx, hqy)
    gain = round(
        holdout_selected["pearson_r_unadjusted"] -
        holdout_zero["pearson_r_unadjusted"], 6)
    monthly = []
    for name, begin, end, count in HOLDOUT_MONTHS:
        # The holdout arrays are already Jan-Mar only, so indexing here uses
        # calendar offsets relative to fixed Jan-1 holdout, never raw events.
        offset = int((begin - PERIODS["holdout_2011_q1"][0]).total_seconds() // 600)
        ax, ay = hx[offset:offset + count], hy[offset:offset + count]
        aq, bq = hqx[offset:offset + count], hqy[offset:offset + count]
        if len(ax) != count or len(ay) != count:
            raise DWDHoldoutBlocked("monthly holdout calendar count drift")
        baseline = _fixed_lag_score(ax, ay, 0)
        result = _fixed_lag_score(ax, ay, selected, aq, bq)
        monthly.append({
            "month_utc": name,
            "samples_at_zero_lag": baseline["paired_samples"],
            "r_at_zero_lag": baseline["pearson_r_unadjusted"],
            "samples_at_training_selected_lag": result["paired_samples"],
            "r_at_training_selected_lag": result["pearson_r_unadjusted"],
            "delta_r_selected_minus_zero": round(
                result["pearson_r_unadjusted"] -
                baseline["pearson_r_unadjusted"], 6),
        })
    return {
        "training_definition": training_label,
        "training_original_pairs": len(tx),
        "discovery_lags_scanned": 2 * MAX_LAG_STEPS + 1,
        "discovery_zero_lag": train_zero,
        "discovery_selected_lag": selected_train,
        "discovery_tied_best_lags_minutes": tied,
        "selection_tie_break_rule": "minimum_absolute_lag_then_minimum_signed_lag",
        "holdout_original_pairs": len(hx),
        "holdout_zero_lag": holdout_zero,
        "holdout_training_selected_lag": holdout_selected,
        "holdout_delta_r_selected_minus_zero": gain,
        "holdout_monthly_fixed_lag_checks": monthly,
        "lag_selected_using_holdout_values": False,
        "physical_travel_time_confirmed": False,
        "serial_dependence_adjusted": False,
    }


def study(first: dict, second: dict) -> dict:
    baseline = _paired_stats(first, second)
    a, b = first["shared_samples"], second["shared_samples"]
    times = sorted(a)
    if (len(times) != 65520 or times[0] != START or times[-1] != END
            or any(t != START + timedelta(minutes=10*i) for i, t in enumerate(times))):
        raise DWDHoldoutBlocked("source-pair observation grid is not complete at 10-minute resolution")
    x = [a[t][0] for t in times]
    y = [b[t][0] for t in times]
    qx = [a[t][1] for t in times]
    qy = [b[t][1] for t in times]
    if any(v is None or not math.isfinite(v) for v in x + y):
        raise DWDHoldoutBlocked("original holdout source contains missing or nonfinite gust")
    hold = _slice_window(x, y, *PERIODS["holdout_2011_q1"], qx=qx, qy=qy)
    seasonal = _slice_window(x, y, *PERIODS["discovery_same_season_2010_q1"])
    full2010 = _slice_window(x, y, *PERIODS["discovery_all_2010"])
    primary = _evaluate_split(
        seasonal, holdout=hold, training_label="2010_Q1_same_months_as_2011_Q1")
    sensitivity = _evaluate_split(
        full2010, holdout=hold, training_label="2010_FULL_YEAR_vs_2011_Q1")
    if (len(seasonal[0]) + len(hold[0]) > len(x) or
            len(full2010[0]) + len(hold[0]) != len(x)):
        raise DWDHoldoutBlocked("fixed training and holdout windows are not disjoint")
    return {
        "profile": "opencatastrophe-dwd-fx10-temporal-lag-holdout-v0",
        "full_original_paired_samples": len(x),
        "full_original_zero_lag_r": baseline["pearson_r_zero_lag_unadjusted"],
        "primary_same_season_chronological_holdout": primary,
        "secondary_full_year_chronological_holdout": sensitivity,
        "same_season_comparison_keeps_calendar_months": True,
        "calendar_2010_discovery_precedes_2011_holdout": True,
        "no_separate_storm_events_or_independent_station_network_validated": True,
        "out_of_sample_physical_hazard_predictive_skill_proven": False,
        "source_rows_or_event_timestamps_emitted": False,
        "model_input_approved": False,
    }


def inspect(first_path: Path, second_path: Path) -> dict:
    try:
        first = _extract(Path(first_path), station="00003", filename=FIRST_FILE,
                         digest=FIRST_SHA, expected_full_count=FIRST_ROWS)
        second = _extract(Path(second_path), station="00348", filename=SECOND_FILE,
                          digest=SECOND_SHA, expected_full_count=SECOND_ROWS)
        result = study(first, second)
    except (PairedWindBlocked, WindEpisodesBlocked) as exc:
        raise DWDHoldoutBlocked("frozen original source or lag statistics fail closed") from exc
    return {
        "source_station00003_zip_sha256": FIRST_SHA,
        "source_station00348_zip_sha256": SECOND_SHA,
        "full_original_utc_window": "2010-01-01T00:00Z_to_2011-03-31T23:50Z",
        **result,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-zip", required=True, type=Path)
    parser.add_argument("--second-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = inspect(args.first_zip, args.second_zip)
    except DWDHoldoutBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(output, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
