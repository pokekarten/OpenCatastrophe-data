# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only GDW v1 independent ring-structure and geodesic diagnostics.

Two deliberately narrow independent checks on a pinned original SHP ZIP:
(1) exact repeated interior ring vertices from raw pyshp point arrays, with
    no GEOS topology operation; this is not a complete ring validity test.
(2) WGS84 polygon area using GeographicLib's Python PolygonArea instead of
    PROJ's pyproj Geod, on the SAME two GEOS counterfactual polygons. This
    checks the numerical area computation, NOT independent GEOS geometry.
Nothing approves original source geometry, CAT models or publication of bytes.
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
from research_runners import gdw_v1_invalid_polygons_area_sensitivity_v0 as sensitivity

SOURCE = "globaldamwatch.gdw.v1.0"
PROFILE = "gdw-v1-independent-ring-vertex-and-geodesic-20261117-v0"
MAX_SOURCE_VERTICES_PER_FEATURE = 30_000
MAX_TOTAL_GEODESIC_SOURCE_VERTICES = 250_000


class IndependentDiagnosticError(ValueError):
    pass


def has_nonclosure_ring_vertex_repeat(source_shape) -> bool:
    """Independent exact pyshp-vertex witness, not a complete validity test.

    The expected final closing vertex does not count as a self-touch.
    Duplicate vertices elsewhere in the SAME ring do count. Separate rings
    that touch are not treated as a same-ring repeat.
    """
    points = source_shape.points
    starts = list(source_shape.parts)
    if (not points or not starts or starts[0] != 0
            or any(type(p) is not int or p < 0 for p in starts)
            or starts != sorted(set(starts))):
        raise IndependentDiagnosticError("malformed original SHP ring offsets")
    for start, end in zip(starts, starts[1:] + [len(points)]):
        if end <= start or end > len(points):
            raise IndependentDiagnosticError("malformed original SHP ring bounds")
        ring = points[start:end]
        if len(ring) < 4:
            raise IndependentDiagnosticError("short original polygon ring")
        all_vertices = [tuple(xy) for xy in ring]
        if any(len(xy) != 2 or not all(math.isfinite(q) for q in xy)
               for xy in all_vertices):
            raise IndependentDiagnosticError("nonfinite original polygon ring")
        ring_without_closure = (all_vertices[:-1]
                                if all_vertices[0] == all_vertices[-1]
                                else all_vertices)
        seen = set()
        for xy in ring_without_closure:
            if xy in seen:
                return True
            seen.add(xy)
    return False


def _geographiclib_ring_area_m2(coords) -> float:
    from geographiclib.geodesic import Geodesic
    from geographiclib.polygonarea import PolygonArea

    polygon = PolygonArea(Geodesic.WGS84, False)
    for longitude, latitude in coords:
        if not (math.isfinite(longitude) and math.isfinite(latitude)
                and -180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise IndependentDiagnosticError("invalid polygon coordinate")
        polygon.AddPoint(latitude, longitude)
    _n, _perimeter, signed_area = polygon.Compute(reverse=False, sign=True)
    if not math.isfinite(signed_area):
        raise IndependentDiagnosticError("nonfinite GeographicLib ring area")
    return abs(signed_area)


def geographiclib_area_km2(polygonal) -> float:
    """Pure-Python GeographicLib area of GEOS-derived polygon parts."""
    total = 0.0
    for part in sensitivity._polygons(polygonal):
        outer = _geographiclib_ring_area_m2(part.exterior.coords)
        holes = sum(_geographiclib_ring_area_m2(ring.coords)
                    for ring in part.interiors)
        signed = outer - holes
        if signed < -1.0:
            raise IndependentDiagnosticError("geodesic holes exceed shell")
        total += max(0.0, signed) / 1_000_000.0
    if not math.isfinite(total) or total < 0 or total > 50_000_000:
        raise IndependentDiagnosticError("invalid independent WGS84 area")
    return total


def compare_geodesic_counterfactuals(original_geometry, geod) -> float:
    """Max per-feature area mismatch; fail closed on material disagreement."""
    import shapely
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    linework = shapely.make_valid(original_geometry, method="linework",
                                  keep_collapsed=True)
    buffer_zero = original_geometry.buffer(0)
    biggest = 0.0
    for candidate in (linework, buffer_zero):
        parts = list(sensitivity._polygons(candidate))
        candidate_poly = unary_union(parts) if parts else Polygon()
        if candidate_poly.is_empty or not candidate_poly.is_valid:
            raise IndependentDiagnosticError("empty/invalid counterfactual output")
        proj_area = sensitivity._area_km2(candidate_poly, geod)
        independent_area = geographiclib_area_km2(candidate_poly)
        discrepancy = abs(proj_area - independent_area)
        if discrepancy > max(1e-6, 1e-8 * max(proj_area, independent_area)):
            raise IndependentDiagnosticError("independent WGS84 area mismatch")
        biggest = max(biggest, discrepancy)
    return biggest


def audit(original_zip: Path) -> dict:
    # Verify immutable publisher ZIP before importing optional GIS readers.
    evidence = pre.inspect(original_zip, expected_sha256=sensitivity.EXACT_SHA256)
    if evidence["original_sha256"] != sensitivity.EXACT_SHA256:
        raise IndependentDiagnosticError("wrong source archive SHA256")

    from pyproj import Geod
    from shapely.geometry import shape
    from shapely.validation import explain_validity

    geod = Geod(ellps="WGS84")
    valid = 0
    invalid = 0
    repeated_native_vertices = 0
    geodesic_checked = 0
    geodesic_domain_excluded = 0
    geodesic_vertex_budget_excluded = 0
    geodesic_source_vertex_budget_used = 0
    max_geodesic_discrepancy = 0.0
    with zipfile.ZipFile(original_zip) as z:
        members = pre._members(z)
        reader, idx = spatial._open_reader(z, members, "GDW_reservoirs_v1_0")
        try:
            for row in reader.iterShapeRecords():
                spatial._check_id(row.record, idx)  # validate; never publish
                geom = shape(row.shape.__geo_interface__)
                if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty:
                    raise IndependentDiagnosticError("original polygon type changed")
                if geom.is_valid:
                    valid += 1
                    continue
                invalid += 1
                if spatial._validity_reason_family(explain_validity(geom)) != "ring_self_intersection":
                    raise IndependentDiagnosticError("unreviewed native invalidity class")
                repeated_native_vertices += int(
                    has_nonclosure_ring_vertex_repeat(row.shape))
                west, south, east, north = geom.bounds
                if (not all(math.isfinite(v) for v in (west, south, east, north))
                        or not (-180 <= west <= east <= 180
                                and -90 <= south <= north <= 90)):
                    raise IndependentDiagnosticError("invalid original geographic extent")
                if east - west > 180 or south < -85 or north > 85:
                    geodesic_domain_excluded += 1
                    continue
                vertices = len(row.shape.points)
                if (vertices > MAX_SOURCE_VERTICES_PER_FEATURE
                        or geodesic_source_vertex_budget_used + vertices
                           > MAX_TOTAL_GEODESIC_SOURCE_VERTICES):
                    geodesic_vertex_budget_excluded += 1
                    continue
                max_geodesic_discrepancy = max(
                    max_geodesic_discrepancy,
                    compare_geodesic_counterfactuals(geom, geod))
                geodesic_source_vertex_budget_used += vertices
                geodesic_checked += 1
        finally:
            reader.close()
    if valid != 35_074 or invalid != 221 or valid + invalid != 35_295:
        raise IndependentDiagnosticError("original source population changed")
    if (geodesic_checked + geodesic_domain_excluded
            + geodesic_vertex_budget_excluded != invalid):
        raise IndependentDiagnosticError("incomplete original source coverage")
    return {
        "source_id": SOURCE,
        "profile": PROFILE,
        "original_sha256": sensitivity.EXACT_SHA256,
        "original_reservoir_count": valid + invalid,
        "original_geos_invalid_count": invalid,
        "exact_raw_ring_repeated_vertex_witness_count": repeated_native_vertices,
        "raw_ring_witness_is_complete_topology_check": False,
        "numerically_crosschecked_counterfactuals": geodesic_checked,
        "independent_geodesic_domain_excluded": geodesic_domain_excluded,
        "independent_geodesic_vertex_budget_excluded": geodesic_vertex_budget_excluded,
        "independent_geodesic_source_vertex_budget_used":
            geodesic_source_vertex_budget_used,
        "max_wgs84_area_mismatch_km2": max_geodesic_discrepancy,
        "geodesic_area_implementation":
            "GeographicLib 2.1 Python PolygonArea vs PROJ Geod 3.7.2",
        "independent_topology_engine_verified": False,
        "same_geos_counterfactual_geometry_used": True,
        "source_geometries_ids_coordinates_or_bytes_exported": False,
        "source_geometry_repaired_or_overwritten": False,
        "CAT_model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        print(json.dumps(audit(args.original_zip), sort_keys=True,
                         allow_nan=False))
    except Exception:
        # No exception text, source IDs, coordinates or WKT in Actions logs.
        print("BLOCKED: GDW independent diagnostics failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
