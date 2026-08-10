# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic metadata-only GloFAS grid matching for the Dresden pilot.

The selector deliberately uses only station/grid metadata, never discharge
values or skill scores. The preregistered Dresden rule is:

1. candidate-cell great-circle angular distance <= 0.15 degrees;
2. absolute relative upstream-area mismatch against 53,096 km^2 <= 10%;
3. select minimum area mismatch;
4. break a mismatch tie by minimum great-circle angular distance;
5. break a remaining exact tie by latitude, then longitude, ascending.

The historical >=500 km^2 calibration-scale context is not a separate selector
here because the 10% Dresden area gate already implies model upstream area >=
47,786.4 km^2. Duplicate coordinates and malformed metadata fail closed.
"""

from __future__ import annotations

import math
from typing import Iterable, NamedTuple

DRESDEN_DRAINAGE_AREA_KM2 = 53_096.0
MAX_ANGULAR_DISTANCE_DEGREES = 0.15
MAX_RELATIVE_DRAINAGE_AREA_MISMATCH = 0.10


class GridMatchError(ValueError):
    """Raised when the preregistered grid-matching contract fails closed."""


class GlofasGridCell(NamedTuple):
    latitude: float
    longitude: float
    upstream_area_km2: float


class GlofasGridMatch(NamedTuple):
    cell: GlofasGridCell
    angular_distance_degrees: float
    relative_drainage_area_mismatch: float


def _finite_number(value: float | int, where: str) -> float:
    if type(value) not in {int, float}:
        raise GridMatchError(f"{where} must be numeric and not boolean")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise GridMatchError(f"{where} cannot be represented safely") from exc
    if not math.isfinite(numeric):
        raise GridMatchError(f"{where} must be finite")
    return numeric


def _latitude(value: float | int, where: str) -> float:
    latitude = _finite_number(value, where)
    if latitude < -90.0 or latitude > 90.0:
        raise GridMatchError(f"{where} must be between -90 and 90 degrees")
    return latitude


def _longitude(value: float | int, where: str) -> float:
    longitude = _finite_number(value, where)
    if longitude < -180.0 or longitude >= 180.0:
        raise GridMatchError(f"{where} must be in canonical [-180, 180) degrees")
    return longitude


def great_circle_angular_distance_degrees(
    latitude_a: float | int,
    longitude_a: float | int,
    latitude_b: float | int,
    longitude_b: float | int,
) -> float:
    """Return spherical great-circle central angle in degrees.

    Angular distance is used directly because the preregistered neighborhood is
    expressed in degrees. No Earth-radius convention or distance-unit conversion
    is therefore introduced into the eligibility or tie-break rules.
    """

    lat_a = math.radians(_latitude(latitude_a, "latitude_a"))
    lon_a = math.radians(_longitude(longitude_a, "longitude_a"))
    lat_b = math.radians(_latitude(latitude_b, "latitude_b"))
    lon_b = math.radians(_longitude(longitude_b, "longitude_b"))

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    haversine = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2.0) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    angle = math.degrees(2.0 * math.asin(math.sqrt(haversine)))
    if not math.isfinite(angle):
        raise GridMatchError("great-circle angular distance must remain finite")
    return angle


def select_dresden_glofas_grid_cell(
    *,
    station_latitude: float | int,
    station_longitude: float | int,
    candidates: Iterable[GlofasGridCell],
) -> GlofasGridMatch:
    """Select one GloFAS cell using the frozen Dresden metadata-only rule."""

    station_lat = _latitude(station_latitude, "station_latitude")
    station_lon = _longitude(station_longitude, "station_longitude")

    try:
        iterator = iter(candidates)
    except TypeError as exc:
        raise GridMatchError("candidates must be an iterable of GlofasGridCell values") from exc

    seen_coordinates: set[tuple[float, float]] = set()
    eligible: list[GlofasGridMatch] = []
    for index, candidate in enumerate(iterator):
        if type(candidate) is not GlofasGridCell:
            raise GridMatchError(f"candidates[{index}] must be a GlofasGridCell")
        latitude = _latitude(candidate.latitude, f"candidates[{index}].latitude")
        longitude = _longitude(candidate.longitude, f"candidates[{index}].longitude")
        upstream_area = _finite_number(
            candidate.upstream_area_km2,
            f"candidates[{index}].upstream_area_km2",
        )
        if upstream_area <= 0.0:
            raise GridMatchError(f"candidates[{index}].upstream_area_km2 must be positive")

        coordinates = (latitude, longitude)
        if coordinates in seen_coordinates:
            raise GridMatchError(
                f"duplicate candidate grid coordinate: latitude={latitude}, longitude={longitude}"
            )
        seen_coordinates.add(coordinates)

        angular_distance = great_circle_angular_distance_degrees(
            station_lat,
            station_lon,
            latitude,
            longitude,
        )
        if angular_distance > MAX_ANGULAR_DISTANCE_DEGREES:
            continue

        relative_mismatch = abs(upstream_area - DRESDEN_DRAINAGE_AREA_KM2) / DRESDEN_DRAINAGE_AREA_KM2
        if not math.isfinite(relative_mismatch):
            raise GridMatchError(f"candidates[{index}] drainage-area mismatch must remain finite")
        if relative_mismatch > MAX_RELATIVE_DRAINAGE_AREA_MISMATCH:
            continue

        eligible.append(
            GlofasGridMatch(
                cell=GlofasGridCell(latitude, longitude, upstream_area),
                angular_distance_degrees=angular_distance,
                relative_drainage_area_mismatch=relative_mismatch,
            )
        )

    if not eligible:
        raise GridMatchError(
            "no GloFAS cell satisfies the frozen 0.15-degree distance and 10% drainage-area gates"
        )

    return min(
        eligible,
        key=lambda match: (
            match.relative_drainage_area_mismatch,
            match.angular_distance_degrees,
            match.cell.latitude,
            match.cell.longitude,
        ),
    )
