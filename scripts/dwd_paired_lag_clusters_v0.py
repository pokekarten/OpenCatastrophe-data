#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only lag and exceedance-cluster study on two pinned DWD originals.

Take the exact immutable original-archive checks and one-to-one UTC pairing
from dwd_two_station_paired_gust_v0. Never print or persist original samples,
coordinates, instrument names or identifiable event times.

Lag k: compare station-00003 at UTC t with station-00348 at UTC t+k*10 min.
A maximizing lag on *the same study data* is exploratory, not an estimated
physical propagation time. An exceedance cluster groups nearby threshold hits
at either station and is NOT a validated meteorological storm event.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

from scripts.dwd_two_station_paired_gust_v0 import (
    PairedWindBlocked, _extract, _paired_stats,
    FIRST_FILE, SECOND_FILE, FIRST_SHA, SECOND_SHA,
    FIRST_ROWS, SECOND_ROWS, START, END,
)

MAX_LAG_STEPS = 12                # +/- 120 minutes; 10 minute increments.
CLUSTER_THRESHOLD_MPS = (15.0, 20.0, 25.0)
MAX_GAP_BETWEEN_HITS_SLOTS = 6   # <= 60 minutes between consecutive threshold hits.


class WindEpisodesBlocked(ValueError):
    """Insufficient original source integrity or unsupported statistic."""


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 4:
        raise WindEpisodesBlocked("Pearson requires four aligned pairs")
    if any(not math.isfinite(v) for v in xs + ys):
        raise WindEpisodesBlocked("nonfinite values in original gust pair")
    n = len(xs)
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    a = [v - mx for v in xs]
    b = [v - my for v in ys]
    vx = math.fsum(v * v for v in a)
    vy = math.fsum(v * v for v in b)
    if vx <= 0 or vy <= 0:
        raise WindEpisodesBlocked("zero observed sample variance")
    result = math.fsum(x * y for x, y in zip(a, b)) / math.sqrt(vx * vy)
    if not math.isfinite(result) or abs(result) > 1.000001:
        raise WindEpisodesBlocked("invalid Pearson result")
    return max(-1.0, min(1.0, result))


def _lag_pair(x: list[float], y: list[float], lag_steps: int) -> tuple[list[float], list[float]]:
    if len(x) != len(y) or abs(lag_steps) >= len(x):
        raise WindEpisodesBlocked("invalid lag or paired source lengths")
    if lag_steps > 0:
        return x[:-lag_steps], y[lag_steps:]
    if lag_steps < 0:
        return x[-lag_steps:], y[:lag_steps]
    return x, y


def _lag_profile(x: list[float], y: list[float], *,
                 max_lag_steps: int = MAX_LAG_STEPS) -> dict:
    if not isinstance(max_lag_steps, int) or not 0 <= max_lag_steps <= MAX_LAG_STEPS:
        raise WindEpisodesBlocked("lag outside preregistered +/-120-minute audit")
    if len(x) != len(y) or len(x) < max_lag_steps + 4:
        raise WindEpisodesBlocked("not enough paired observations for requested lag")
    lags = []
    for k in range(-max_lag_steps, max_lag_steps + 1):
        a, b = _lag_pair(x, y, k)
        lags.append({
            "lag_minutes_station00348_relative_to_00003": k * 10,
            "paired_nonmissing_samples": len(a),
            "pearson_r_unadjusted": round(_pearson(a, b), 6),
        })
    maximum = max(row["pearson_r_unadjusted"] for row in lags)
    maxima = [row["lag_minutes_station00348_relative_to_00003"]
              for row in lags if row["pearson_r_unadjusted"] == maximum]
    return {
        "lag_sign_convention": "positive_k_means_station00348_at_t_plus_k_relative_to_station00003_t",
        "lags_minutes": lags,
        "maximum_observed_r_unadjusted": maximum,
        "maximizing_lags_minutes_ties_preserved": maxima,
        "lag_based_physical_propagation_claim": False,
        "lagged_multiple_testing_adjusted": False,
    }


def _episodes(x: list[float], y: list[float], threshold: float, *,
              max_gap_slots: int = MAX_GAP_BETWEEN_HITS_SLOTS) -> dict:
    if not math.isfinite(threshold) or threshold <= 0:
        raise WindEpisodesBlocked("invalid gust exceedance threshold")
    if not isinstance(max_gap_slots, int) or not 0 <= max_gap_slots <= 12:
        raise WindEpisodesBlocked("unreviewed exceedance gap rule")
    if len(x) != len(y):
        raise WindEpisodesBlocked("original two-station series lengths differ")
    if any(not math.isfinite(v) or v < 0 for v in x + y):
        raise WindEpisodesBlocked("invalid original nonmissing gust in cluster audit")
    hits = [i for i, (a, b) in enumerate(zip(x, y))
            if a >= threshold or b >= threshold]
    clusters = []
    if hits:
        first = last = hits[0]
        for idx in hits[1:]:
            if idx - last > max_gap_slots:
                clusters.append((first, last))
                first = idx
            last = idx
        clusters.append((first, last))
    categories = Counter()
    max_duration = 0
    for begin, finish in clusters:
        a = any(v >= threshold for v in x[begin:finish + 1])
        b = any(v >= threshold for v in y[begin:finish + 1])
        if not (a or b):
            raise WindEpisodesBlocked("cluster assignment lost original exceedance")
        categories["both_station_hits_in_cluster" if a and b else
                   "station00003_only_cluster" if a else
                   "station00348_only_cluster"] += 1
        max_duration = max(max_duration, finish - begin + 1)
    if sum(categories.values()) != len(clusters):
        raise WindEpisodesBlocked("cluster membership count does not conserve clusters")
    return {
        "threshold_mps": threshold,
        "max_quiet_gap_between_hits_minutes": max_gap_slots * 10,
        "original_10min_samples_with_either_station_exceedance": len(hits),
        "algorithmic_exceedance_cluster_count": len(clusters),
        "both_station_hits_in_cluster": categories["both_station_hits_in_cluster"],
        "station00003_only_cluster": categories["station00003_only_cluster"],
        "station00348_only_cluster": categories["station00348_only_cluster"],
        "longest_cluster_span_minutes": max_duration * 10,
        "physically_independent_storm_events_proven": False,
        "event_timestamps_emitted": False,
    }


def _study(a: dict, b: dict) -> dict:
    # The prior exact-original module enforces the shared 65,520 timestamps,
    # nonmissing original FX_10 and unique UTC cadence before any analyses.
    baseline = _paired_stats(a, b)
    times = sorted(a["shared_samples"])
    x = [a["shared_samples"][t][0] for t in times]
    y = [b["shared_samples"][t][0] for t in times]
    first_qn = [a["shared_samples"][t][1] for t in times]
    second_qn = [b["shared_samples"][t][1] for t in times]
    if len(x) != 65520:
        raise WindEpisodesBlocked("original joint window did not contain 65,520 samples")
    qn3_x = [p for p, q1, q2 in zip(x, first_qn, second_qn) if q1 == q2 == 3]
    qn3_y = [p for p, q1, q2 in zip(y, first_qn, second_qn) if q1 == q2 == 3]
    qn3_r = _pearson(qn3_x, qn3_y)
    all_r = _pearson(x, y)
    if round(all_r, 6) != baseline["pearson_r_zero_lag_unadjusted"]:
        raise WindEpisodesBlocked("baseline original zero-lag computation diverged")
    return {
        "profile": "opencatastrophe-dwd-two-station-lag-exceedance-clusters-v0",
        "paired_10min_original_observations": len(x),
        "baseline_zero_lag_pearson_r": baseline["pearson_r_zero_lag_unadjusted"],
        "qn3_only_zero_lag": {
            "paired_original_observations_both_qn3": len(qn3_x),
            "pearson_r_unadjusted": round(qn3_r, 6),
            "quality_filter": "BOTH_QN_EQ_3",
        },
        "lag_research": _lag_profile(x, y),
        "threshold_hit_clusters": [_episodes(x, y, threshold)
                                   for threshold in CLUSTER_THRESHOLD_MPS],
        "serial_dependence_adjusted": False,
        "effective_independent_storm_sample_size_estimated": False,
        "physics_propagation_or_storm_tracking_proven": False,
        "hazard_map_calibrated": False,
        "source_rows_or_event_timestamps_emitted": False,
        "model_input_approved": False,
    }


def inspect(first_path: Path, second_path: Path) -> dict:
    try:
        first = _extract(Path(first_path), station="00003", filename=FIRST_FILE,
                         digest=FIRST_SHA, expected_full_count=FIRST_ROWS)
        second = _extract(Path(second_path), station="00348", filename=SECOND_FILE,
                          digest=SECOND_SHA, expected_full_count=SECOND_ROWS)
        payload = _study(first, second)
    except PairedWindBlocked as exc:
        raise WindEpisodesBlocked("original two-station input gate blocked") from exc
    return {
        "source_station00003_zip_sha256": FIRST_SHA,
        "source_station00348_zip_sha256": SECOND_SHA,
        "source_calendar": "2010-01-01T00:00Z_to_2011-03-31T23:50Z",
        **payload,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first-zip", type=Path, required=True)
    p.add_argument("--second-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(inspect(args.first_zip, args.second_zip),
                         sort_keys=True, allow_nan=False))
    except WindEpisodesBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
