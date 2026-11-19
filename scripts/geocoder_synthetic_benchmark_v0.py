#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only geocoder candidate quality benchmark.

No API, filesystem writes or source admission. Individual coordinates and
case IDs are never emitted. Comparing positions does NOT identify buildings.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import statistics
import sys

SCHEMA = "oc-geocoder-benchmark-synthetic-v0"
EARTH_RADIUS_M = 6371008.8
MAX_INPUT_BYTES = 131072
MAX_TRUTH_CASES = 200
MAX_RUNS = 5
MAX_CANDIDATES_PER_CASE = 3
CASE_RE = re.compile(r"^synthetic:[A-Za-z0-9_-]{1,48}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class GeocoderBenchmarkError(ValueError):
    """Invalid input must fail closed without publishing coordinates."""


def _fields(obj: object, required: set[str], what: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != required:
        raise GeocoderBenchmarkError(f"{what}: invalid or missing fields")
    return obj


def _token(value: object, what: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise GeocoderBenchmarkError(f"{what}: invalid identifier")
    return value


def _coordinate(value: object, limit: float, what: str) -> float:
    if type(value) not in (float, int) or not math.isfinite(value):
        raise GeocoderBenchmarkError(f"{what}: invalid coordinate")
    if not -limit <= value <= limit:
        raise GeocoderBenchmarkError(f"{what}: coordinate out of range")
    return float(value)


def _point(item: dict, what: str) -> tuple[float, float]:
    return (_coordinate(item["latitude"], 90, what),
            _coordinate(item["longitude"], 180, what))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = (math.radians(x) for x in a)
    lat2, lon2 = (math.radians(x) for x in b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, max(0.0, h))))


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def evaluate(payload: object) -> dict:
    root = _fields(payload, {"schema_version", "synthetic_only", "crs",
                             "distance_threshold_m", "truth", "runs"}, "root")
    if root["schema_version"] != SCHEMA or root["synthetic_only"] is not True:
        raise GeocoderBenchmarkError("synthetic-only versioned input required")
    if root["crs"] != "EPSG:4326":
        raise GeocoderBenchmarkError("only explicit EPSG:4326 is supported")
    threshold = root["distance_threshold_m"]
    if type(threshold) not in (float, int) or not math.isfinite(threshold) or not 1 <= threshold <= 500:
        raise GeocoderBenchmarkError("distance threshold must be 1..500 metres")

    rows = root["truth"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_TRUTH_CASES:
        raise GeocoderBenchmarkError("truth case budget exceeded or empty")
    truth: dict[str, tuple[float, float]] = {}
    for row in rows:
        _fields(row, {"case_id", "latitude", "longitude"}, "truth")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not CASE_RE.fullmatch(case_id):
            raise GeocoderBenchmarkError("only synthetic case IDs are permitted")
        if case_id in truth:
            raise GeocoderBenchmarkError("duplicate synthetic case")
        truth[case_id] = _point(row, "truth")

    runs = root["runs"]
    if not isinstance(runs, list) or not 1 <= len(runs) <= MAX_RUNS:
        raise GeocoderBenchmarkError("run budget exceeded or empty")
    reports = []
    seen_engines = set()
    snapshots = set()
    for run in runs:
        _fields(run, {"engine", "engine_version", "index_snapshot_id",
                      "candidates"}, "run")
        engine = _token(run["engine"], "engine")
        version = _token(run["engine_version"], "engine_version")
        snap = _token(run["index_snapshot_id"], "index_snapshot_id")
        if engine in seen_engines:
            raise GeocoderBenchmarkError("duplicate geocoder engine")
        seen_engines.add(engine)
        snapshots.add(snap)
        candidates = run["candidates"]
        if not isinstance(candidates, list) or len(candidates) > len(truth) * MAX_CANDIDATES_PER_CASE:
            raise GeocoderBenchmarkError("candidate budget exceeded")
        by_case: dict[str, dict[int, tuple[float, float]]] = {}
        for candidate in candidates:
            _fields(candidate, {"case_id", "rank", "latitude", "longitude"}, "candidate")
            case_id = candidate["case_id"]
            if not isinstance(case_id, str) or case_id not in truth:
                raise GeocoderBenchmarkError("unknown candidate synthetic case")
            rank = candidate["rank"]
            if type(rank) is not int or not 1 <= rank <= MAX_CANDIDATES_PER_CASE:
                raise GeocoderBenchmarkError("invalid rank")
            values = by_case.setdefault(case_id, {})
            if rank in values:
                raise GeocoderBenchmarkError("duplicate candidate rank")
            values[rank] = _point(candidate, "candidate")
        for values in by_case.values():
            if sorted(values) != list(range(1, len(values) + 1)):
                raise GeocoderBenchmarkError("candidate ranks must be contiguous from 1")

        top1 = []
        first_hits = 0
        three_hits = 0
        for case_id, actual in truth.items():
            options = by_case.get(case_id, {})
            if 1 in options:
                dist1 = _distance(actual, options[1])
                top1.append(dist1)
                if dist1 <= threshold:
                    first_hits += 1
            if any(_distance(actual, options[r]) <= threshold for r in options):
                three_hits += 1
        reports.append({
            "engine": engine,
            "engine_version": version,
            "index_snapshot_id": snap,
            "synthetic_cases": len(truth),
            "cases_with_candidates": len(by_case),
            "no_candidate_cases": len(truth) - len(by_case),
            "recall_at_1": round(first_hits / len(truth), 6),
            "recall_at_3": round(three_hits / len(truth), 6),
            "median_top1_error_m": None if not top1 else round(statistics.median(top1), 3),
            "p95_top1_error_m": None if not top1 else round(_percentile(top1, .95), 3),
        })
    return {
        "schema_version": SCHEMA,
        "synthetic_only": True,
        "distance_threshold_m": float(threshold),
        "same_index_snapshot_across_engines": len(snapshots) == 1,
        "interpretation": "coordinate_accuracy_only_not_building_identity",
        "building_identity_proven": False,
        "source_rights_admitted": False,
        "cat_model_input_admitted": False,
        "runs": reports,
    }


def _strict_pairs(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise GeocoderBenchmarkError("duplicate JSON field")
        obj[key] = value
    return obj


def _reject_nonfinite(value: str) -> None:
    raise GeocoderBenchmarkError("nonfinite JSON number")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local synthetic JSON fixture")
    args = parser.parse_args(argv)
    try:
        path = args.input
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise GeocoderBenchmarkError("input must be a bounded regular local file")
        payload = json.loads(path.read_text(encoding="utf-8"),
                             object_pairs_hook=_strict_pairs,
                             parse_constant=_reject_nonfinite)
        report = evaluate(payload)
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        # Deliberately do not echo exception values from provider rows.
        print(f"BLOCKED: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
