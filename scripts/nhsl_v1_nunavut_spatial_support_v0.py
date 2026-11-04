# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline NHSL v1.0 Nunavut polygon-vs-centroid spatial-support uncertainty.

Read only exact source-pinned original ZIPs outside Git. Proves geometric
support and archetype centroid matching, NOT roof coordinates, hazard intensity,
probabilistic site-location error, topology validity, insured TIV, or OED export.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sqlite3
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

if __package__:
    from .nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )
    from .nhsl_v1_original_sauid_reconcile_v0 import (
        NHSLReconcileError, audit_original_archives,
    )
else:
    from nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )
    from nhsl_v1_original_sauid_reconcile_v0 import (
        NHSLReconcileError, audit_original_archives,
    )

SOURCE_ID = "can.nrcan.nhsl.physical-exposure.2016-2020"
EXPECTED_AREAS = 103
EXPECTED_ARCHETYPES = 2087
MAX_COORDINATES = 300_000
MAX_POLYGONS = 5000
GRID_PROXY_KM = (0.25, 1.0, 5.0, 10.0)
EARTH_RADIUS_KM = 6371.0088
CENTROID_MATCH_DEGREES = 0.000001


class NHSLSpatialError(ValueError):
    """Source-spatial or GeoPackage binary evidence is not sufficient."""


def _coordinate(v: Any, bound: float, field: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise NHSLSpatialError(f"{field} must be numeric")
    value = float(v)
    if not math.isfinite(value) or abs(value) > bound:
        raise NHSLSpatialError(f"{field} nonfinite/out of range")
    return value


def _haversine_km(lon_a: float, lat_a: float, lon_b: float, lat_b: float) -> float:
    lat1, lat2 = math.radians(lat_a), math.radians(lat_b)
    dl = math.radians(lon_b - lon_a)
    dphi = lat2 - lat1
    h = math.sin(dphi / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, max(0.0, h))))


class _WKB:
    """Tiny, bounded 2-D ISO WKB Polygon/MultiPolygon parser, no GEOS dependency."""

    def __init__(self, raw: bytes, offset: int) -> None:
        self.raw = raw
        self.pos = offset
        self.vertices = 0

    def _unpack(self, fmt: str) -> tuple[Any, ...]:
        size = struct.calcsize(fmt)
        if self.pos + size > len(self.raw):
            raise NHSLSpatialError("truncated WKB coordinate or count")
        val = struct.unpack_from(fmt, self.raw, self.pos)
        self.pos += size
        return val

    def _parse(self, depth: int) -> list[list[list[tuple[float, float]]]]:
        if depth > 1:
            raise NHSLSpatialError("unsupported nested WKB geometry")
        (endian,) = self._unpack("B")
        if endian not in (0, 1):
            raise NHSLSpatialError("invalid WKB endian")
        order = "<" if endian == 1 else ">"
        (wkb_type,) = self._unpack(order + "I")
        if wkb_type not in (3, 6):
            raise NHSLSpatialError("non-2D or nonpolygon WKB geometry")
        if wkb_type == 6:
            (n,) = self._unpack(order + "I")
            if n < 1 or n > MAX_POLYGONS:
                raise NHSLSpatialError("invalid multi-polygon part count")
            parts = []
            for _ in range(n):
                parts.extend(self._parse(depth + 1))
            return parts

        (rings,) = self._unpack(order + "I")
        if rings < 1 or rings > MAX_POLYGONS:
            raise NHSLSpatialError("empty or unbounded polygon rings")
        polygon = []
        for _ in range(rings):
            (count,) = self._unpack(order + "I")
            self.vertices += count
            if count < 4 or self.vertices > MAX_COORDINATES:
                raise NHSLSpatialError("invalid or excessive polygon vertices")
            ring = []
            for _ in range(count):
                lon, lat = self._unpack(order + "dd")
                ring.append((_coordinate(lon, 180, "WKB longitude"),
                             _coordinate(lat, 90, "WKB latitude")))
            if ring[0] != ring[-1] or len(set(ring[:-1])) < 3:
                raise NHSLSpatialError("invalid/unclosed WKB polygon ring")
            polygon.append(ring)
        return [polygon]

    def polygons(self) -> list[list[list[tuple[float, float]]]]:
        parts = self._parse(depth=0)
        if self.pos != len(self.raw):
            raise NHSLSpatialError("unexpected trailing WKB bytes")
        return parts


def _gpkg_polygon(blob: Any, srs: int = 4326) -> list[list[list[tuple[float, float]]]]:
    if not isinstance(blob, bytes) or len(blob) < 17 or blob[:3] != b"GP\x00":
        raise NHSLSpatialError("missing/invalid GeoPackage v0 geometry")
    flags = blob[3]
    if flags & 0xF0:
        raise NHSLSpatialError("unsupported empty/reserved GPKG geometry flags")
    order = "little" if flags & 1 else "big"
    envelope = (flags >> 1) & 7
    extra = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(envelope)
    if extra is None or len(blob) < 8 + extra + 5:
        raise NHSLSpatialError("invalid GeoPackage envelope")
    if int.from_bytes(blob[4:8], order, signed=True) != srs:
        raise NHSLSpatialError("GeoPackage feature SRS mismatch")
    return _WKB(blob, 8 + extra).polygons()


def _on_segment(p: tuple[float, float], a: tuple[float, float],
                b: tuple[float, float]) -> bool:
    cross = (p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])
    scale = max(1.0, abs(b[0] - a[0]), abs(b[1] - a[1]))
    if abs(cross) > 1e-11 * scale:
        return False
    return min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12 and (
        min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12
    )


def _ring_loc(p: tuple[float, float], ring: list[tuple[float, float]]) -> int:
    """0=outside, 1=inside, 2=on boundary; planar lon/lat diagnostic only."""
    inside = False
    x, y = p
    for a, b in zip(ring, ring[1:]):
        if _on_segment(p, a, b):
            return 2
        if (a[1] > y) != (b[1] > y):
            at_x = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if at_x > x:
                inside = not inside
    return 1 if inside else 0


def _is_on_footprint(point: tuple[float, float],
                     polygons: list[list[list[tuple[float, float]]]]) -> bool:
    for rings in polygons:
        ext = _ring_loc(point, rings[0])
        if ext == 0:
            continue
        if ext == 2:
            return True
        if not any(_ring_loc(point, hole) == 1 for hole in rings[1:]):
            return True
    return False


def spatial_profile(polygons: list[dict[str, Any]],
                    archetypes: list[dict[str, Any]]) -> dict[str, Any]:
    """Scientific geometry-support proxy; pure, suitable for invented fixtures."""
    by_id: dict[str, dict[str, Any]] = {}
    radius_km = []
    outside = 0
    point_radius_by_id: dict[str, float] = {}
    value_total = 0.0
    for record in polygons:
        id_ = record.get("Sauid")
        if not isinstance(id_, str) or not id_ or id_ in by_id:
            raise NHSLSpatialError("missing or duplicate polygon SAUID")
        lon = _coordinate(record.get("E_SauidLon"), 180, "centroid longitude")
        lat = _coordinate(record.get("E_SauidLat"), 90, "centroid latitude")
        area_value = record.get("Et_AssetValue")
        if isinstance(area_value, bool) or not isinstance(area_value, (float, int)):
            raise NHSLSpatialError("missing/non-numeric replacement cost")
        value = float(area_value)
        if not math.isfinite(value) or value < 0 or value > 1e15:
            raise NHSLSpatialError("invalid replacement cost")
        parts = _gpkg_polygon(record.get("geom_poly"))
        vertices = [p for part in parts for ring in part for p in ring]
        min_lon = min(x for x, _ in vertices)
        max_lon = max(x for x, _ in vertices)
        min_lat = min(y for _, y in vertices)
        max_lat = max(y for _, y in vertices)
        if max_lon - min_lon >= 180:
            raise NHSLSpatialError("dateline-crossing longitude box not supported")
        max_vertex = max(_haversine_km(lon, lat, x, y) for x, y in vertices)
        # BBox corner radius is a simple spatial-support proxy, NOT a formal
        # topological/geodesic Hausdorff distance or a hazard-cell coverage.
        max_corner = max(
            _haversine_km(lon, lat, x, y)
            for x in (min_lon, max_lon) for y in (min_lat, max_lat)
        )
        inside = _is_on_footprint((lon, lat), parts)
        outside += not inside
        by_id[id_] = {
            "lon": lon, "lat": lat, "value": value,
            "vertex_radius_km": max_vertex,
            "bbox_corner_radius_km": max_corner,
        }
        radius_km.append(max_vertex)
        value_total += value

    if not polygons or not archetypes:
        raise NHSLSpatialError("empty exposure groups")
    count_archetypes = 0
    orphan = 0
    mismatches = 0
    max_offset_km = 0.0
    for record in archetypes:
        count_archetypes += 1
        id_ = record.get("Sauid")
        match = by_id.get(id_)
        if match is None:
            orphan += 1
            continue
        lon = _coordinate(record.get("BldgLon"), 180, "archetype longitude")
        lat = _coordinate(record.get("BldgLat"), 90, "archetype latitude")
        max_offset_km = max(max_offset_km, _haversine_km(
            lon, lat, match["lon"], match["lat"]
        ))
        if abs(lon - match["lon"]) > CENTROID_MATCH_DEGREES or (
            abs(lat - match["lat"]) > CENTROID_MATCH_DEGREES
        ):
            mismatches += 1

    def nearest_rank(q: float) -> float:
        arr = sorted(radius_km)
        return round(arr[max(0, math.ceil(q * len(arr)) - 1)], 6)

    value_proxy = {}
    for threshold in GRID_PROXY_KM:
        members = [v for v in by_id.values() if v["vertex_radius_km"] > threshold]
        value_proxy[str(threshold)] = {
            "area_count": len(members),
            "area_share": round(len(members) / len(by_id), 6),
            "replacement_value_share": round(
                sum(v["value"] for v in members) / value_total, 6
            ) if value_total else 0.0,
        }
    complete = count_archetypes == EXPECTED_ARCHETYPES and len(by_id) == EXPECTED_AREAS
    aligned = complete and not (orphan or mismatches)
    return {
        "region": "Nunavut",
        "source_candidate_id": SOURCE_ID,
        "original_source_polygon_areas": len(by_id),
        "original_source_archetypes": count_archetypes,
        "centroid_inside_polygon_count": len(by_id) - outside,
        "centroid_outside_polygon_count": outside,
        "archetype_missing_polygon_count": orphan,
        "archetype_centroid_coordinate_mismatch_count": mismatches,
        "max_archetype_to_parent_center_km": round(max_offset_km, 6),
        "archetype_parent_centroid_agreement_passed": aligned,
        "vertex_radius_proxy_km": {
            "p50": nearest_rank(0.5), "p90": nearest_rank(0.9),
            "p95": nearest_rank(0.95), "maximum": round(max(radius_km), 6),
        },
        "max_bbox_corner_radius_proxy_km": round(
            max(v["bbox_corner_radius_km"] for v in by_id.values()), 6
        ),
        "area_radius_greater_than_km": value_proxy,
        "original_modeled_total_replacement_cad_2019": round(value_total, 3),
        "radius_is_true_building_location_error": False,
        "modeled_hazard_or_losses": False,
        "individual_roof_coordinates_proven": False,
        "insured_tiv_proven": False,
        "can_export_oed": False,
        "source_model_use_approved": False,
        "source_admitted": False,
        "admission_status": "not_admitted",
    }


def _load_source_geo_rows(polygon_zip: Path, archetype_zip: Path) -> tuple[list[dict], list[dict]]:
    paths = (("polygon", polygon_zip), ("archetype", archetype_zip))
    with tempfile.TemporaryDirectory(prefix="nhsl-geometry-research-") as temp:
        outputs: dict[str, list[dict]] = {}
        for role, source in paths:
            pinned = PINNED[role]
            raw = _bytes(source, pinned)
            check_archive(raw, role, pinned)
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                gpkg = zf.read(pinned["member"])
            file = Path(temp) / (role + ".gpkg")
            file.write_bytes(gpkg)
            table = pinned["member"][:-5]
            columns = (
                '"Sauid", "E_SauidLon", "E_SauidLat", "Et_AssetValue", "geom_poly"'
                if role == "polygon" else '"Sauid", "BldgLon", "BldgLat"'
            )
            conn = sqlite3.connect(file.as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                conn.execute("PRAGMA query_only=ON")
                conn.execute("PRAGMA trusted_schema=OFF")
                cursor = conn.execute(f'SELECT {columns} FROM "{table}"')
                names = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                if len(rows) > 100_000:
                    raise NHSLSpatialError("source row budget exceeded")
                outputs[role] = [dict(zip(names, values)) for values in rows]
            finally:
                conn.close()
        return outputs["polygon"], outputs["archetype"]


def inspect_original(polygon_zip: Path, archetype_zip: Path) -> dict[str, Any]:
    conserved = audit_original_archives(polygon_zip, archetype_zip)
    if not conserved["numeric_conservation_passed"] or (
        conserved["settled_areas"] != EXPECTED_AREAS
        or conserved["archetype_records"] != EXPECTED_ARCHETYPES
    ):
        raise NHSLSpatialError("original source conservation prerequisite failed")
    polygons, archetypes = _load_source_geo_rows(polygon_zip, archetype_zip)
    result = spatial_profile(polygons, archetypes)
    result["original_sha256_verified"] = {
        role: PINNED[role]["sha256"] for role in ("polygon", "archetype")
    }
    result["original_sqlite_integrity_checked"] = True
    result["original_crosslayer_numeric_conservation_checked"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--polygon-zip", required=True, type=Path)
    parser.add_argument("--archetype-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect_original(args.polygon_zip, args.archetype_zip)
    except (NHSLSpatialError, NHSLBinaryError, NHSLReconcileError,
            KeyError, sqlite3.Error, OSError, zipfile.BadZipFile) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["archetype_parent_centroid_agreement_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
