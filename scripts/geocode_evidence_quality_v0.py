# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline geocoder evidence challenge using synthetic-only cases.

This is a quality diagnostic, not a geocoder, an address-to-building resolver,
rights clearance, or an admission decision. Its controls are independent of
candidate ordering and never select a candidate using reference coordinates.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
import math
import statistics
from typing import Any


class GeocodeEvidenceError(ValueError):
    """Invalid, inconsistent or incomplete geocoding benchmark evidence."""


_ALLOWED_PRECISION = {
    "address_point", "building_rooftop", "parcel_centroid",
    "street_interpolation", "place_centroid", "unknown",
}
_FINE_PRECISION = {"address_point", "building_rooftop"}
_EARTH_RADIUS_METRES = 6_371_008.8


def _object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise GeocodeEvidenceError(f"{label}: incorrect field set")
    return value


def _label(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip() != value:
        raise GeocodeEvidenceError(f"{name} must be nonempty, trimmed text")
    return value


def _date(value: Any, name: str) -> date:
    if not isinstance(value, str) or len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise GeocodeEvidenceError(f"{name} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise GeocodeEvidenceError(f"{name} is not a calendar date") from exc


def _number(value: Any, name: str, lo: float, hi: float, upper_inclusive: bool = True) -> float:
    if type(value) not in (int, float):
        raise GeocodeEvidenceError(f"{name} must be numeric, not boolean")
    try:
        number = float(value)
    except OverflowError as exc:
        raise GeocodeEvidenceError(f"{name} is too large") from exc
    if not math.isfinite(number) or number < lo or (number > hi if upper_inclusive else number >= hi):
        raise GeocodeEvidenceError(f"{name} outside finite range")
    return number


def _coords(obj: dict[str, Any], name: str) -> tuple[float, float]:
    return (
        _number(obj["lat"], f"{name}.lat", -90, 90),
        _number(obj["lon"], f"{name}.lon", -180, 180, upper_inclusive=False),
    )


def _distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * _EARTH_RADIUS_METRES * math.asin(math.sqrt(max(0.0, min(1.0, h))))


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def benchmark(rows: list[dict[str, Any]], *, threshold_metres: float = 50.0) -> dict[str, Any]:
    """Measure rank-1 geocode outputs without silently authorising a building match.

    Every case requires a separately declared reference-source family, WGS84,
    fixed source snapshots and dates. Equal labels only detect *known* lineage
    overlap; different labels do not prove actual independent origins.
    The top candidate is chosen by rank alone, never by the reference point.
    """
    threshold = _number(threshold_metres, "threshold_metres", 0.001, 100_000)
    if not isinstance(rows, list) or not rows:
        raise GeocodeEvidenceError("benchmark requires one or more cases")

    seen_cases: set[tuple[str, str]] = set()
    statuses: Counter[str] = Counter()
    evaluated_errors: list[float] = []
    output: list[dict[str, Any]] = []
    for idx, raw in enumerate(rows):
        case = _object(raw, {"case_id", "engine", "reference", "candidates"}, f"case[{idx}]")
        case_id = _label(case["case_id"], "case_id")
        engine = _label(case["engine"], "engine")
        key = (case_id, engine)
        if key in seen_cases:
            raise GeocodeEvidenceError("duplicate case_id/engine")
        seen_cases.add(key)
        reference = _object(case["reference"], {"lat", "lon", "crs", "source_family", "as_of"}, "reference")
        if reference["crs"] != "EPSG:4326":
            raise GeocodeEvidenceError("reference CRS must be EPSG:4326")
        reference_point = _coords(reference, "reference")
        reference_family = _label(reference["source_family"], "reference.source_family")
        benchmark_date = _date(reference["as_of"], "reference.as_of")
        candidates = case["candidates"]
        if not isinstance(candidates, list):
            raise GeocodeEvidenceError("candidates must be a list")
        ranked: list[tuple[int, dict[str, Any]]] = []
        seen_sources: set[tuple[str, str, str]] = set()
        for cand in candidates:
            c = _object(cand, {"rank", "lat", "lon", "crs", "source_family", "source_id", "snapshot", "as_of", "precision"}, "candidate")
            if type(c["rank"]) is not int or c["rank"] < 1:
                raise GeocodeEvidenceError("candidate.rank must be positive integer")
            if c["crs"] != "EPSG:4326":
                raise GeocodeEvidenceError("candidate CRS must be EPSG:4326")
            _coords(c, "candidate")
            family = _label(c["source_family"], "source_family")
            source_id = _label(c["source_id"], "source_id")
            snapshot = _label(c["snapshot"], "snapshot")
            if (family, source_id, snapshot) in seen_sources:
                raise GeocodeEvidenceError("duplicate source feature within one case")
            seen_sources.add((family, source_id, snapshot))
            _date(c["as_of"], "candidate.as_of")
            if type(c["precision"]) is not str or c["precision"] not in _ALLOWED_PRECISION:
                raise GeocodeEvidenceError("unknown candidate precision")
            ranked.append((c["rank"], c))
        ranked.sort(key=lambda item: item[0])
        if [rank for rank, _ in ranked] != list(range(1, len(ranked) + 1)):
            raise GeocodeEvidenceError("candidate ranks must be unique and contiguous from 1")
        distance: float | None = None
        if not ranked:
            status = "no_result"
        else:
            top = ranked[0][1]
            if top["source_family"] == reference_family:
                status = "known_shared_lineage"
            elif _date(top["as_of"], "candidate.as_of") > benchmark_date:
                status = "post_reference_snapshot"
            else:
                distance = _distance_m(reference_point, _coords(top, "candidate"))
                evaluated_errors.append(distance)
                if len(ranked) != 1:
                    status = "ambiguous_candidates"
                elif top["precision"] not in _FINE_PRECISION:
                    status = "coarse_precision"
                elif distance > threshold:
                    status = "outside_threshold"
                else:
                    status = "within_threshold_analysis_only"
        statuses[status] += 1
        output.append({"case_id": case_id, "engine": engine, "status": status, "rank1_error_m": None if distance is None else round(distance, 3), "candidate_count": len(ranked)})

    return {
        "benchmark_version": "v0", "analysis_only": True,
        "threshold_m": threshold, "case_count": len(rows),
        "status_counts": {k: statuses[k] for k in sorted(statuses)},
        "rank1_median_error_m": None if not evaluated_errors else round(statistics.median(evaluated_errors), 3),
        "rank1_p95_error_m": None if not evaluated_errors else round(_percentile(evaluated_errors, 0.95), 3),
        "results": output,
    }
