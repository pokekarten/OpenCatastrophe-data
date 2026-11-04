# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Independent GEOS topology challenge to NHSL Nunavut v1.0 centroid test.

Only original, SHA-pinned release ZIPs outside Git. Source replacement costs
are NOT insured TIV; geographic coordinates do not identify individual roofs.
Provides aggregate counts/shares; never prints SAUID, geometry or raw rows.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from shapely import wkb
from shapely.geometry import Point
from shapely.ops import nearest_points

if __package__:
    from .nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )
    from .nhsl_v1_nunavut_spatial_support_v0 import (
        NHSLSpatialError, _coordinate, _haversine_km, inspect_original,
    )
else:
    from nhsl_v1_original_binary_preflight_v0 import (
        PINNED, NHSLBinaryError, _bytes, check_archive,
    )
    from nhsl_v1_nunavut_spatial_support_v0 import (
        NHSLSpatialError, _coordinate, _haversine_km, inspect_original,
    )

EXPECTED_COUNT = 103


class NHSLTopologyError(ValueError):
    """Original binary or independently checked geometry is not admissible."""


def _wkb_from_gpkg(raw: Any, srs_id: int = 4326) -> bytes:
    if not isinstance(raw, bytes) or len(raw) < 13 or raw[:3] != b"GP\x00":
        raise NHSLTopologyError("missing or invalid GeoPackage geometry header")
    flags = raw[3]
    if flags & 0xF0:
        raise NHSLTopologyError("empty/unsupported GeoPackage geometry")
    env_code = (flags >> 1) & 7
    env_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(env_code)
    if env_bytes is None or len(raw) < 8 + env_bytes + 5:
        raise NHSLTopologyError("truncated or reserved GeoPackage envelope")
    order = "little" if flags & 1 else "big"
    if int.from_bytes(raw[4:8], order, signed=True) != srs_id:
        raise NHSLTopologyError("GeoPackage SRS mismatch")
    return raw[8 + env_bytes:]


def independent_topology(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Independent GEOS covers/validity check; accepts synthetic rows for CI."""
    outside = 0
    invalid = 0
    multipart = 0
    holes = 0
    on_boundary = 0
    total = 0.0
    outside_value = 0.0
    # A valid polygon may exclude its mathematical centroid for two disjoint
    # reasons: a hole inside an exterior ring, or being outside every exterior
    # shell (e.g. a concave exterior shape). Do not infer hole membership from
    # the total number of interior rings.
    in_hole_count = 0
    outside_shell_count = 0
    in_hole_value = 0.0
    outside_shell_value = 0.0
    max_outside_distance_km = 0.0
    center_to_shape_centroid_km = []
    seen = set()
    for record in rows:
        id_ = record.get("Sauid")
        if not isinstance(id_, str) or not id_ or id_ in seen:
            raise NHSLTopologyError("invalid or duplicate SAUID")
        seen.add(id_)
        lon = _coordinate(record.get("E_SauidLon"), 180, "source longitude")
        lat = _coordinate(record.get("E_SauidLat"), 90, "source latitude")
        value = record.get("Et_AssetValue")
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise NHSLTopologyError("source replacement cost must be numeric")
        cost = float(value)
        if not math.isfinite(cost) or cost < 0 or cost > 1e15:
            raise NHSLTopologyError("invalid modeled replacement cost")
        total += cost
        try:
            geometry = wkb.loads(_wkb_from_gpkg(record.get("geom_poly")))
        except Exception as exc:
            raise NHSLTopologyError("GEOS cannot read source polygon WKB") from exc
        if geometry.geom_type not in ("Polygon", "MultiPolygon") or geometry.is_empty:
            raise NHSLTopologyError("not an actual nonempty polygon geometry")
        if not geometry.is_valid:
            invalid += 1
        parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        multipart += int(len(parts) > 1)
        holes += sum(len(part.interiors) for part in parts)
        point = Point(lon, lat)
        if geometry.touches(point):
            on_boundary += 1
        if not geometry.covers(point):
            outside += 1
            outside_value += cost
            # Use *only the corresponding original exterior shell(s)* to
            # identify whether the missing coverage is caused by an interior
            # ring. This is independent of our earlier ray-casting algorithm.
            in_exterior_shell = any(
                Polygon(part.exterior).covers(point) for part in parts
            )
            if in_exterior_shell:
                # Exact source geometry valid, yet the point lies in an
                # interior hole (not on a covered ring boundary).
                in_hole_count += 1
                in_hole_value += cost
            else:
                # Not covered by any exterior shell: includes concavity and,
                # for MultiPolygons, gaps between exterior components.
                outside_shell_count += 1
                outside_shell_value += cost
            # Shapely/GEOS computes the nearest point in its planar lon/lat CRS.
            # Haversine of the returned endpoints is only a descriptive proxy.
            foot, pt = nearest_points(geometry, point)
            max_outside_distance_km = max(
                max_outside_distance_km,
                _haversine_km(pt.x, pt.y, foot.x, foot.y)
            )
        geom_center = geometry.centroid
        center_to_shape_centroid_km.append(
            _haversine_km(lon, lat, geom_center.x, geom_center.y)
        )
    if not rows:
        raise NHSLTopologyError("empty source polygon list")
    if outside != in_hole_count + outside_shell_count:
        raise NHSLTopologyError("outside centroid category totals disagree")
    if total and abs(outside_value - in_hole_value - outside_shell_value) > 0.02:
        raise NHSLTopologyError("outside centroid category cost totals disagree")
    return {
        "source_region": "Nunavut",
        "polygons": len(rows),
        "geos_valid_geometry_count": len(rows) - invalid,
        "geos_invalid_geometry_count": invalid,
        "geos_multipart_area_count": multipart,
        "geos_interiors_hole_count": holes,
        "geos_centroids_in_or_on_polygon_count": len(rows) - outside,
        "geos_reported_centroids_outside_polygon_count": outside,
        "geos_outside_centroids_inside_an_interior_hole_count": in_hole_count,
        "geos_outside_centroids_outside_all_exterior_shells_count": outside_shell_count,
        "geos_reported_centroids_on_boundary_count": on_boundary,
        "original_modeled_total_replacement_cad_2019": round(total, 3),
        "outside_centroid_modeled_value_share": (
            round(outside_value / total, 6) if total else 0.0
        ),
        "hole_centroid_modeled_value_share": (
            round(in_hole_value / total, 6) if total else 0.0
        ),
        "outside_shell_centroid_modeled_value_share": (
            round(outside_shell_value / total, 6) if total else 0.0
        ),
        "max_outside_centroid_to_polygon_nearest_point_km_proxy": round(
            max_outside_distance_km, 6
        ),
        "max_original_centroid_to_geos_planar_centroid_km_proxy": round(
            max(center_to_shape_centroid_km), 6
        ),
        "geos_crs_interpretation": "planar_lon_lat_EPSG4326",
        "geodesic_topology_or_hazard_coverage_proven": False,
        "building_rooftops_individually_geolocated": False,
        "source_admitted": False,
        "oed_insured_locations_exportable": False,
        "admission_status": "not_admitted",
    }


def _read_original_polygon_rows(path: Path) -> list[dict[str, Any]]:
    pinned = PINNED["polygon"]
    raw = _bytes(path, pinned)
    check_archive(raw, "polygon", pinned)
    with tempfile.TemporaryDirectory(prefix="nhsl-geos-original-") as tmp:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            gpkg = zf.read(pinned["member"])
        file = Path(tmp) / "source.gpkg"
        file.write_bytes(gpkg)
        table = pinned["member"][:-5]
        con = sqlite3.connect(file.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            con.execute("PRAGMA query_only=ON")
            con.execute("PRAGMA trusted_schema=OFF")
            fields = ['Sauid', 'E_SauidLon', 'E_SauidLat', 'Et_AssetValue', 'geom_poly']
            projection = ", ".join('"' + x + '"' for x in fields)
            rows = con.execute(f'SELECT {projection} FROM "{table}"').fetchall()
            if len(rows) != EXPECTED_COUNT:
                raise NHSLTopologyError("original NHSL feature count drift")
            return [dict(zip(fields, row)) for row in rows]
        finally:
            con.close()


def original_geos_crosscheck(polygon_zip: Path, archetype_zip: Path) -> dict[str, Any]:
    # Independent GEOS check cannot replace the original file and seven-metric
    # conservation guard. Require the already-reviewed original evidence first.
    baseline = inspect_original(polygon_zip, archetype_zip)
    if not baseline["archetype_parent_centroid_agreement_passed"]:
        raise NHSLTopologyError("baseline original 103-to-2087 source proof failed")
    result = independent_topology(_read_original_polygon_rows(polygon_zip))
    if (
        result["geos_reported_centroids_outside_polygon_count"]
        != baseline["centroid_outside_polygon_count"]
    ):
        raise NHSLTopologyError("GEOS and independent WKB centroid diagnostics disagree")
    if result["geos_invalid_geometry_count"]:
        raise NHSLTopologyError("original geometry is not GEOS topologically valid")
    result["original_source_geos_crosscheck_passed"] = True
    result["original_baseline_sha256_verified"] = {
        "polygon": PINNED["polygon"]["sha256"],
        "archetype": PINNED["archetype"]["sha256"],
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--polygon-zip", required=True, type=Path)
    parser.add_argument("--archetype-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = original_geos_crosscheck(args.polygon_zip, args.archetype_zip)
    except (NHSLTopologyError, NHSLSpatialError, NHSLBinaryError,
            sqlite3.DatabaseError, OSError, zipfile.BadZipFile) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
