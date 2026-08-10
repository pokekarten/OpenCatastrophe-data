# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Parse pre-target PEGELONLINE metadata for the Dresden hydrology holdout.

The parser is deliberately provider-shaped but dependency-free. It accepts the
station object returned by the PEGELONLINE REST-v2 station endpoint or the
station list returned by ``stations.json?includeTimeseries=true``. Provider
objects may gain additional backward-compatible attributes; only the scientific
fields OpenCatastrophe relies on are interpreted strictly.

No measurements are accepted. A response containing ``currentMeasurement`` is
rejected so metadata resolution cannot silently become target-value inspection.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from scripts.dresden_acquisition_intent import (
    PEGELONLINE_STATION_NUMBER,
    PEGELONLINE_STATION_UUID,
)
from scripts.hydrology_window import expected_observations_per_24h

PEGELONLINE_STATION_SHORTNAME = "DRESDEN"
PEGELONLINE_WATER_SHORTNAME = "ELBE"
PEGELONLINE_Q_SHORTNAME = "Q"
PEGELONLINE_Q_LONGNAME = "ABFLUSS_ROHDATEN"
PEGELONLINE_Q_UNIT = "m³/s"
SECONDS_PER_MINUTE = 60
PEGELONLINE_REST_V2_BASE = "https://pegelonline.wsv.de/webservices/rest-api/v2"


class PegelonlineMetadataError(ValueError):
    """Raised when provider metadata cannot satisfy the frozen Dresden contract."""


def _reject_constant(value: str) -> None:
    raise PegelonlineMetadataError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PegelonlineMetadataError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_provider_json_bytes(raw: bytes) -> Any:
    """Load UTF-8 provider JSON while rejecting duplicate keys and NaN/Infinity."""

    if type(raw) is not bytes or not raw:
        raise PegelonlineMetadataError("provider response must be non-empty bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PegelonlineMetadataError("provider response must be valid UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except PegelonlineMetadataError:
        raise
    except json.JSONDecodeError as exc:
        raise PegelonlineMetadataError(f"provider response is not valid JSON: {exc}") from exc


def pegelonline_metadata_request_url() -> str:
    """Return the exact metadata-only REST-v2 request for the frozen station UUID."""

    return (
        f"{PEGELONLINE_REST_V2_BASE}/stations/{PEGELONLINE_STATION_UUID}.json"
        "?includeTimeseries=true"
    )


def _station_from_payload(payload: Any) -> dict[str, Any]:
    if type(payload) is dict:
        return payload
    if type(payload) is not list:
        raise PegelonlineMetadataError("provider JSON root must be a station object or station array")

    matches: list[dict[str, Any]] = []
    for index, value in enumerate(payload):
        if type(value) is not dict:
            raise PegelonlineMetadataError(f"stations[{index}] must be an object")
        if value.get("uuid") == PEGELONLINE_STATION_UUID:
            matches.append(value)
    if len(matches) != 1:
        raise PegelonlineMetadataError(
            "station array must contain exactly one frozen Dresden station UUID"
        )
    return matches[0]


def _exact_text(value: Any, expected: str, where: str) -> str:
    if type(value) is not str or value != expected:
        raise PegelonlineMetadataError(f"{where} must equal {expected!r}")
    return value


def _coordinate(value: Any, where: str, *, minimum: float, maximum: float, upper_exclusive: bool) -> float:
    if type(value) not in {int, float}:
        raise PegelonlineMetadataError(f"{where} must be a finite numeric value and not boolean")
    try:
        number = float(value)
    except OverflowError as exc:
        raise PegelonlineMetadataError(f"{where} must be finite") from exc
    if not math.isfinite(number):
        raise PegelonlineMetadataError(f"{where} must be finite")
    if number < minimum or (number >= maximum if upper_exclusive else number > maximum):
        bracket = f"[{minimum}, {maximum})" if upper_exclusive else f"[{minimum}, {maximum}]"
        raise PegelonlineMetadataError(f"{where} must be in {bracket}")
    return number


def parse_pegelonline_station_metadata(payload: Any) -> dict[str, Any]:
    """Return the exact Dresden metadata needed to finalize acquisition intent."""

    station = _station_from_payload(payload)
    _exact_text(station.get("uuid"), PEGELONLINE_STATION_UUID, "station.uuid")
    _exact_text(station.get("number"), PEGELONLINE_STATION_NUMBER, "station.number")
    _exact_text(station.get("shortname"), PEGELONLINE_STATION_SHORTNAME, "station.shortname")

    water = station.get("water")
    if type(water) is not dict:
        raise PegelonlineMetadataError("station.water must be an object")
    _exact_text(water.get("shortname"), PEGELONLINE_WATER_SHORTNAME, "station.water.shortname")

    latitude = _coordinate(
        station.get("latitude"),
        "station.latitude",
        minimum=-90.0,
        maximum=90.0,
        upper_exclusive=False,
    )
    longitude = _coordinate(
        station.get("longitude"),
        "station.longitude",
        minimum=-180.0,
        maximum=180.0,
        upper_exclusive=True,
    )

    timeseries = station.get("timeseries")
    if type(timeseries) is not list:
        raise PegelonlineMetadataError("station.timeseries must be an array")
    q_series: list[dict[str, Any]] = []
    for index, value in enumerate(timeseries):
        if type(value) is not dict:
            raise PegelonlineMetadataError(f"station.timeseries[{index}] must be an object")
        if "currentMeasurement" in value:
            raise PegelonlineMetadataError(
                "metadata response must not include currentMeasurement target values"
            )
        if value.get("shortname") == PEGELONLINE_Q_SHORTNAME:
            q_series.append(value)
    if len(q_series) != 1:
        raise PegelonlineMetadataError("station must expose exactly one Q time series")

    q = q_series[0]
    _exact_text(q.get("longname"), PEGELONLINE_Q_LONGNAME, "Q.longname")
    _exact_text(q.get("unit"), PEGELONLINE_Q_UNIT, "Q.unit")
    equidistance = q.get("equidistance")
    if type(equidistance) is not int or equidistance <= 0:
        raise PegelonlineMetadataError("Q.equidistance must be a positive integer number of minutes")
    sampling_interval_seconds = equidistance * SECONDS_PER_MINUTE
    try:
        expected_count = expected_observations_per_24h(sampling_interval_seconds)
    except ValueError as exc:
        raise PegelonlineMetadataError(
            f"Q.equidistance cannot define an exact 24-hour sampling grid: {exc}"
        ) from exc

    return {
        "provider_contract": "PEGELONLINE REST API v2 station metadata",
        "request_url": pegelonline_metadata_request_url(),
        "station_number": PEGELONLINE_STATION_NUMBER,
        "station_uuid": PEGELONLINE_STATION_UUID,
        "station_shortname": PEGELONLINE_STATION_SHORTNAME,
        "water_shortname": PEGELONLINE_WATER_SHORTNAME,
        "latitude_wgs84": latitude,
        "longitude_wgs84": longitude,
        "q_shortname": PEGELONLINE_Q_SHORTNAME,
        "q_longname": PEGELONLINE_Q_LONGNAME,
        "q_unit": PEGELONLINE_Q_UNIT,
        "q_equidistance_minutes": equidistance,
        "q_sampling_interval_seconds": sampling_interval_seconds,
        "expected_observations_per_24h": expected_count,
    }


def parse_pegelonline_metadata_bytes(raw: bytes) -> dict[str, Any]:
    return parse_pegelonline_station_metadata(load_provider_json_bytes(raw))


def canonical_metadata_bytes(metadata: dict[str, Any]) -> bytes:
    if type(metadata) is not dict:
        raise PegelonlineMetadataError("parsed metadata must be an object")
    try:
        return json.dumps(
            metadata,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PegelonlineMetadataError(f"parsed metadata is not canonical JSON data: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse a saved PEGELONLINE Dresden station-metadata response without loading measurements."
    )
    parser.add_argument("path", type=Path, help="Saved UTF-8 JSON response from the metadata-only REST-v2 request")
    args = parser.parse_args(argv)
    try:
        raw = args.path.read_bytes()
        metadata = parse_pegelonline_metadata_bytes(raw)
    except (OSError, PegelonlineMetadataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_metadata_bytes(metadata) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
