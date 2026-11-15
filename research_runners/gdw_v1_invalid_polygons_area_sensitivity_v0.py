# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only area/coverage sensitivity of GDW v1's 221 invalid reservoir rings.

Never edits, exports or persists original geometry/IDs. A local original
Figshare v1 SHP archive must match the independently pinned full ZIP SHA-256.
Two GEOS counterfactuals are compared; neither is a scientifically approved
repair. Run real data only on a reviewed trusted main workflow.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import zipfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_runners import gdw_v1_shapefile_archive_preflight_v0 as pre
from research_runners import gdw_v1_original_spatial_quality_v0 as spatial

SOURCE = "globaldamwatch.gdw.v1.0"
PROFILE = "gdw-v1-invalid-polygon-two-method-sensitivity-v0"
EXACT_SHA256 = spatial.PINNED_SHA256
EXPECTED_INVALID = 221
EXPECTED_POLYGONS = 35_295
EXPECTED_POINTS = 41_145


class GDWSensitivityError(ValueError):
    """The source archive or scientific counterfactual failed closed."""


def _polygons(geom):
    """Flatten only area-bearing pieces; discard collapsed line/point outputs."""
    if geom.geom_type == "Polygon":
        if not geom.is_empty:
            yield geom
    elif geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        for part in geom.geoms:
            yield from _polygons(part)


def _area_km2(geom, geod) -> float:
    from shapely.geometry.polygon import orient

    total = 0.0
    for part in _polygons(geom):
        # Geod requires CCW outer rings and CW holes for a positive area.
        area_m2, _ = geod.geometry_area_perimeter(orient(part, sign=1.0))
        if not math.isfinite(area_m2):
            raise GDWSensitivityError("nonfinite geodesic polygon area")
        total += abs(area_m2) / 1_000_000.0
    if not math.isfinite(total) or total < 0 or total > 50_000_000:
        raise GDWSensitivityError("invalid geodesic area magnitude")
    return total


def examine_invalid(geometry, barrier, geod) -> dict | None:
    """Private per-feature result; caller MUST publish only its aggregates.

    Returns None when geodesic comparisons are unsafe (antimeridian/polar
    domain); such exclusions are counted, never silently interpreted.
    """
    import shapely
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    if (geometry.geom_type not in ("Polygon", "MultiPolygon")
            or geometry.is_empty or geometry.is_valid):
        raise GDWSensitivityError("expected one nonempty native-invalid reservoir")
    west, south, east, north = geometry.bounds
    if not all(math.isfinite(v) for v in (west, south, east, north)):
        raise GDWSensitivityError("nonfinite original geographic bounds")
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise GDWSensitivityError("original polygon outside WGS84 bounds")
    if east - west > 180 or south < -85 or north > 85:
        return None  # Distortion/wrap: exclude, never silently normalize.

    linework = shapely.make_valid(geometry, method="linework", keep_collapsed=True)
    buffer_zero = geometry.buffer(0)
    parts_linework, parts_buffer = list(_polygons(linework)), list(_polygons(buffer_zero))
    p_linework = unary_union(parts_linework) if parts_linework else Polygon()
    p_buffer = unary_union(parts_buffer) if parts_buffer else Polygon()
    if (not p_linework.is_valid or not p_buffer.is_valid
            or any(p.geom_type != "Polygon" or p.is_empty for p in parts_linework + parts_buffer)):
        raise GDWSensitivityError("a counterfactual remains invalid")
    union = p_linework.union(p_buffer)
    overlap = p_linework.intersection(p_buffer)
    a, b = _area_km2(p_linework, geod), _area_km2(p_buffer, geod)
    common, either = _area_km2(overlap, geod), _area_km2(union, geod)
    if common > either * (1 + 1e-8) or either < max(a, b) * (1 - 1e-8):
        raise GDWSensitivityError("geodesic overlay areas violate conservation")
    return {
        "linework_area_km2": a,
        "buffer_zero_area_km2": b,
        "overlap_km2": common,
        "union_km2": either,
        "area_abs_delta_km2": abs(a - b),
        "linework_parts": len(parts_linework),
        "buffer_zero_parts": len(parts_buffer),
        "linework_barrier_covered": p_linework.covers(barrier),
        "buffer_zero_barrier_covered": p_buffer.covers(barrier),
        "any_nonpolygonal_linework_output": linework.geom_type == "GeometryCollection"
            and any(part.geom_type not in ("Polygon", "MultiPolygon")
                    for part in linework.geoms)
            or not parts_linework,
    }


def summarize(cases: list[dict | None], *, expected: int = EXPECTED_INVALID) -> dict:
    if len(cases) != expected:
        raise GDWSensitivityError("full invalid-polygon population not processed")
    valid = [case for case in cases if case is not None]
    excluded = len(cases) - len(valid)
    totals = {k: sum(c[k] for c in valid) for k in
              ("linework_area_km2", "buffer_zero_area_km2", "overlap_km2",
               "union_km2", "area_abs_delta_km2", "linework_parts",
               "buffer_zero_parts")}
    n = len(valid)
    significant = sum(
        abs(c["linework_area_km2"] - c["buffer_zero_area_km2"])
        > max(0.000001, 0.01 * max(c["linework_area_km2"], c["buffer_zero_area_km2"]))
        for c in valid
    )
    area_iou = (totals["overlap_km2"] / totals["union_km2"]
                if totals["union_km2"] > 0 else None)
    return {
        "source_id": SOURCE,
        "profile": PROFILE,
        "source_original_full_zip_sha256": EXACT_SHA256,
        "original_invalid_polygon_count": expected,
        "geodesic_comparable_invalid_polygons": n,
        "excluded_antimeridian_or_polar_cases": excluded,
        "complete_geodesic_population_evaluated": excluded == 0,
        "counterfactual_methods": ["GEOS make_valid(linework)", "GEOS buffer(0)"],
        "linework_area_km2_sum": totals["linework_area_km2"],
        "buffer_zero_area_km2_sum": totals["buffer_zero_area_km2"],
        "absolute_per_feature_area_delta_km2_sum": totals["area_abs_delta_km2"],
        "intersection_area_km2_sum": totals["overlap_km2"],
        "union_area_km2_sum": totals["union_km2"],
        "area_weighted_jaccard_of_alternatives": area_iou,
        "material_area_difference_over_1pct_count": significant,
        "linework_polygon_component_count": totals["linework_parts"],
        "buffer_zero_polygon_component_count": totals["buffer_zero_parts"],
        "paired_barrier_covered_by_linework": sum(c["linework_barrier_covered"] for c in valid),
        "paired_barrier_covered_by_buffer_zero": sum(c["buffer_zero_barrier_covered"] for c in valid),
        "paired_barrier_coverage_disagreement": sum(
            c["linework_barrier_covered"] != c["buffer_zero_barrier_covered"] for c in valid),
        "linework_nonpolygonal_output_count": sum(
            c["any_nonpolygonal_linework_output"] for c in valid),
        "source_geometries_or_ids_exported": False,
        "source_geometry_overwritten_or_repaired": False,
        "independent_gis_engine_checked": False,
        "CAT_model_input_approved": False,
        "method_difference_is_not_a_ground_truth_error": True,
    }


def audit(original_zip: Path) -> dict:
    """Only pinned full original SHP ZIP, no new downloads, no side effects."""
    import shapely
    from pyproj import Geod
    from shapely.geometry import Point, shape
    from shapely.validation import explain_validity

    # Fail closed before source records enter the scientific calculation.
    receipt = pre.inspect(original_zip, expected_sha256=EXACT_SHA256)
    if (receipt["original_sha256"] != EXACT_SHA256
            or receipt["dbf_point_only_id_count"] != 5850):
        raise GDWSensitivityError("frozen original ZIP identity or ID counts changed")
    points = {}
    cases = []
    seen = set()
    polygons = 0
    geod = Geod(ellps="WGS84")
    with zipfile.ZipFile(original_zip) as z:
        members = pre._members(z)
        bars, idx = spatial._open_reader(z, members, "GDW_barriers_v1_0")
        try:
            for row in bars.iterShapeRecords():
                key = spatial._check_id(row.record, idx)
                if key in points or len(row.shape.points) != 1:
                    raise GDWSensitivityError("duplicate or nonpoint original barrier")
                lon, lat = row.shape.points[0]
                if (not all(math.isfinite(v) for v in (lon, lat))
                        or not -180 <= lon <= 180 or not -90 <= lat <= 90):
                    raise GDWSensitivityError("invalid original barrier coordinate")
                points[key] = Point(lon, lat)
        finally:
            bars.close()
        if len(points) != EXPECTED_POINTS:
            raise GDWSensitivityError("barrier count changed")
        reservoirs, idx = spatial._open_reader(z, members, "GDW_reservoirs_v1_0")
        try:
            for row in reservoirs.iterShapeRecords():
                key = spatial._check_id(row.record, idx)
                if key not in points or key in seen:
                    raise GDWSensitivityError("source reservoir point-ID relationship changed")
                seen.add(key)
                polygons += 1
                geom = shape(row.shape.__geo_interface__)
                if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty:
                    raise GDWSensitivityError("original reservoir geometry type changed")
                if not geom.is_valid:
                    if spatial._validity_reason_family(explain_validity(geom)) != "ring_self_intersection":
                        raise GDWSensitivityError("unreviewed native invalidity family")
                    cases.append(examine_invalid(geom, points[key], geod))
        finally:
            reservoirs.close()
    if polygons != EXPECTED_POLYGONS or len(cases) != EXPECTED_INVALID:
        raise GDWSensitivityError("original feature count or invalidity drift")
    return {
        **summarize(cases),
        "original_archive_bytes": receipt["original_bytes"],
        "original_valid_polygon_count": polygons - len(cases),
        "geodesic_area_units": "square kilometres (WGS84 geodesic; counterfactual only)",
        "geometry_engine_version": shapely.geos_version_string,
        "shapely_version": shapely.__version__,
        "pyproj_geodesic_ellipsoid": "WGS84",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(audit(args.original_zip), sort_keys=True, indent=2, allow_nan=False))
    except (GDWSensitivityError, pre.GDWArchiveError, spatial.GDWSpatialError,
            OSError, ValueError, zipfile.BadZipFile) as exc:
        # Avoid accidentally printing provider coordinate or source ID from GEOS.
        print("BLOCKED: original GDW scientific sensitivity validation failed",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
