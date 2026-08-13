# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only CRS/intersection adapter for the EU flood exposure Phase A1 pilot."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from math import ceil, hypot, isfinite
from typing import Sequence

import shapely
from pyproj import Transformer
from pyproj.exceptions import ProjError
from shapely.geometry.base import BaseGeometry

from scripts.eu_flood_exposure_semantic import CensusCell, HazardSupport

SOURCE_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:3035"
TRANSFORM_CONFIG_ID = "eu_flood_spatial_a1_epsg4326_to_epsg3035_v3"
FRACTION_TOLERANCE = 1e-9
SOURCE_SEGMENT_MAX_DEGREES = 1e-4
MAX_DENSIFIED_SEGMENTS = 200_000


class SpatialTransformError(ValueError):
    """Raised when synthetic spatial support cannot be transformed or allocated safely."""


@dataclass(frozen=True)
class SpatialHazardSupport:
    """Synthetic WGS84 hazard polygon carrying the existing A0 support semantics."""

    support_id: str
    geometry_wgs84: BaseGeometry
    depth_m: Decimal | str | int | float | None = None
    nodata: bool = False
    permanent_water: bool = False
    spurious_depth: bool = False


def transform_metadata() -> dict[str, object]:
    """Return the immutable transform contract identity used by this A1 adapter."""

    return {
        "config_id": TRANSFORM_CONFIG_ID,
        "source_crs": SOURCE_CRS,
        "target_crs": TARGET_CRS,
        "axis_order": "xy_lon_lat_to_easting_northing",
        "allow_ballpark": False,
        "only_best": True,
        "fraction_tolerance": format(FRACTION_TOLERANCE, ".1e"),
        "source_segment_max_degrees": format(SOURCE_SEGMENT_MAX_DEGREES, ".1e"),
        "max_densified_segments": MAX_DENSIFIED_SEGMENTS,
        "input_kind": "fixture",
        "scientific_role": "test_fixture",
    }


@lru_cache(maxsize=1)
def _transformer() -> Transformer:
    try:
        return Transformer.from_crs(
            SOURCE_CRS,
            TARGET_CRS,
            always_xy=True,
            allow_ballpark=False,
            only_best=True,
        )
    except (ProjError, ValueError) as exc:
        raise SpatialTransformError("cannot initialize the reviewed CRS transformation") from exc


def _coordinate_pairs(geometry: BaseGeometry) -> list[tuple[float, float]]:
    coordinates = shapely.get_coordinates(geometry)
    pairs: list[tuple[float, float]] = []
    for row in coordinates:
        x = float(row[0])
        y = float(row[1])
        if not isfinite(x) or not isfinite(y):
            raise SpatialTransformError("geometry contains non-finite coordinates")
        pairs.append((x, y))
    if not pairs:
        raise SpatialTransformError("geometry must contain coordinates")
    return pairs


def _validate_polygonal_geometry(
    geometry: object,
    *,
    label: str,
    positive_area: bool = True,
) -> BaseGeometry:
    if not isinstance(geometry, BaseGeometry):
        raise SpatialTransformError(f"{label} must be a Shapely geometry")
    if geometry.is_empty:
        raise SpatialTransformError(f"{label} must not be empty")
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise SpatialTransformError(f"{label} must be polygonal")
    if not geometry.is_valid:
        raise SpatialTransformError(f"{label} must be valid")
    _coordinate_pairs(geometry)
    area = float(geometry.area)
    if not isfinite(area):
        raise SpatialTransformError(f"{label} area must be finite")
    if positive_area and area <= 0:
        raise SpatialTransformError(f"{label} must have positive area")
    return geometry


def _validate_wgs84_coordinates(geometry: BaseGeometry) -> None:
    for longitude, latitude in _coordinate_pairs(geometry):
        if longitude < -180 or longitude > 180:
            raise SpatialTransformError("WGS84 longitude must be in [-180, 180]")
        if latitude < -90 or latitude > 90:
            raise SpatialTransformError("WGS84 latitude must be in [-90, 90]")


def _enforce_densification_budget(geometry: BaseGeometry) -> None:
    """Reject geometry whose reviewed segmentization policy would be too expensive."""

    polygons = (geometry,) if geometry.geom_type == "Polygon" else tuple(geometry.geoms)
    estimated_segments = 0
    for polygon in polygons:
        rings = (polygon.exterior, *tuple(polygon.interiors))
        for ring in rings:
            coordinates = ring.coords
            for index in range(1, len(coordinates)):
                x1, y1 = coordinates[index - 1][:2]
                x2, y2 = coordinates[index][:2]
                source_length = hypot(float(x2) - float(x1), float(y2) - float(y1))
                estimated_segments += max(
                    1,
                    ceil(source_length / SOURCE_SEGMENT_MAX_DEGREES),
                )
                if estimated_segments > MAX_DENSIFIED_SEGMENTS:
                    raise SpatialTransformError(
                        "geometry exceeds the pre-transform densification budget"
                    )


def transform_wgs84_geometry(geometry: BaseGeometry) -> BaseGeometry:
    """Transform one synthetic polygon from WGS84 lon/lat into EPSG:3035."""

    source = _validate_polygonal_geometry(geometry, label="geometry_wgs84")
    _validate_wgs84_coordinates(source)
    _enforce_densification_budget(source)
    source = shapely.segmentize(source, max_segment_length=SOURCE_SEGMENT_MAX_DEGREES)
    source = _validate_polygonal_geometry(source, label="geometry_wgs84")
    transformer = _transformer()

    def project(x, y):
        return transformer.transform(x, y, errcheck=True)

    try:
        projected = shapely.transform(source, project, interleaved=False)
    except (ProjError, ValueError, TypeError) as exc:
        raise SpatialTransformError("geometry transformation failed") from exc
    return _validate_polygonal_geometry(projected, label="transformed geometry")


def _bounded_fraction(numerator: float, denominator: float, *, label: str) -> float:
    if not isfinite(numerator) or not isfinite(denominator) or denominator <= 0:
        raise SpatialTransformError(f"{label} requires finite positive denominator")
    fraction = numerator / denominator
    if fraction < -FRACTION_TOLERANCE or fraction > 1 + FRACTION_TOLERANCE:
        raise SpatialTransformError(f"{label} must be in [0, 1]")
    if abs(fraction) <= FRACTION_TOLERANCE:
        return 0.0
    if abs(fraction - 1) <= FRACTION_TOLERANCE:
        return 1.0
    return fraction


def _positive_area(geometry: BaseGeometry, *, label: str) -> float:
    area = float(geometry.area)
    if not isfinite(area) or area < 0:
        raise SpatialTransformError(f"{label} area must be finite and non-negative")
    return area


def build_spatial_census_cell(
    *,
    cell_id: str,
    population: Decimal | str | int | float,
    census_geometry_epsg3035: BaseGeometry,
    aoi_geometry_epsg3035: BaseGeometry,
    supports: Sequence[SpatialHazardSupport],
) -> CensusCell:
    """Convert synthetic spatial overlays into one existing A0 ``CensusCell``."""

    census = _validate_polygonal_geometry(
        census_geometry_epsg3035, label="census_geometry_epsg3035"
    )
    aoi = _validate_polygonal_geometry(aoi_geometry_epsg3035, label="aoi_geometry_epsg3035")
    census_area = float(census.area)

    clipped_aoi = census.intersection(aoi)
    clipped_aoi_area = _positive_area(clipped_aoi, label="AOI intersection")
    aoi_fraction = _bounded_fraction(
        clipped_aoi_area, census_area, label="aoi_fraction"
    )

    seen_support_ids: set[str] = set()
    clipped_supports: list[tuple[SpatialHazardSupport, BaseGeometry, float]] = []
    for support in sorted(supports, key=lambda item: item.support_id):
        if (
            not isinstance(support.support_id, str)
            or not support.support_id
            or support.support_id != support.support_id.strip()
        ):
            raise SpatialTransformError("support_id must be a non-empty trimmed string")
        if support.support_id in seen_support_ids:
            raise SpatialTransformError(f"duplicate spatial support id: {support.support_id}")
        seen_support_ids.add(support.support_id)

        projected = transform_wgs84_geometry(support.geometry_wgs84)
        if clipped_aoi_area == 0:
            continue
        clipped = projected.intersection(clipped_aoi)
        area = _positive_area(clipped, label=f"support {support.support_id} intersection")
        fraction = _bounded_fraction(area, census_area, label="support fraction")
        if fraction == 0:
            continue
        clipped_supports.append((support, clipped, fraction))

    for index, (_, left, _) in enumerate(clipped_supports):
        for _, right, _ in clipped_supports[index + 1 :]:
            overlap = left.intersection(right)
            overlap_fraction = _bounded_fraction(
                _positive_area(overlap, label="support overlap"),
                census_area,
                label="support overlap fraction",
            )
            if overlap_fraction > FRACTION_TOLERANCE:
                raise SpatialTransformError("spatial hazard supports overlap with positive area")

    total_support_fraction = sum((item[2] for item in clipped_supports), 0.0)
    if total_support_fraction - aoi_fraction > FRACTION_TOLERANCE:
        raise SpatialTransformError("spatial hazard support exceeds clipped AOI")

    a0_supports = tuple(
        HazardSupport(
            support.support_id,
            Decimal(str(fraction)),
            support.depth_m,
            nodata=support.nodata,
            permanent_water=support.permanent_water,
            spurious_depth=support.spurious_depth,
        )
        for support, _, fraction in clipped_supports
    )
    return CensusCell(
        cell_id,
        population,
        Decimal(str(aoi_fraction)),
        a0_supports,
    )
