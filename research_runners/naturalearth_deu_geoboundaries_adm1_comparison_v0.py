# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent original-source Germany border comparison, RESEARCH ONLY.

Compare original Natural Earth v5.1.1 country polygon DEU with the union of
16 original geoBoundaries gbOpen DEU ADM1 (year represented 2021).
These sources differ by scale, vintage, provenance and boundary philosophy:
disagreement must NOT be treated as a legal-border error or auto-repaired.
Neither original provider bytes nor coordinate arrays leave this process.
No model, building, insured exposure or country-location admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from research_runners.geoboundaries_deu_adm1_original_geojson_v0 import (
    BoundaryGeometryError,
    SOURCE_LFS_SIZE,
    SOURCE_LFS_OID_SHA256,
    inspect_geojson_bytes,
)
from scripts.naturalearth_admin0_geojson_preflight import (
    GeojsonBlocked,
    ORIGINAL_BYTES,
    ORIGINAL_SHA256,
    inspect_original_geojson,
)

PROFILE = "naturalearth-v511-deu-vs-geoboundaries-adm1-2021-epsg3035-v0"
ANALYSIS_CRS = "EPSG:3035"
COMPARE_YEAR = 2021
ADMIN1_COUNT = 16
MAX_NATURAL_BYTES = 1_048_576
MAX_GEOBOUNDARIES_BYTES = 7_340_032
MAX_ADMIN1_INTERIOR_OVERLAP_DEG2 = 1e-8


class IndependentBorderBlocked(ValueError):
    """Immutable source identity or scientific comparison failed closed."""


def _boundary_disagreement_distance_profile(natural_equal, admin_equal) -> dict:
    """Allocate the planar symmetric difference by distance from *either* source border.

    This is a diagnostic of two *competing* source boundaries, not a division
    into coastlines, inland borders or legally correct country territory.
    The EPSG:3035 metre buffers have a finite-arc discretisation (quad_segs=4).
    No feature geometry, sample point, per-ADM1 attribute or coordinates leave.
    """
    from shapely.ops import unary_union
    import shapely

    try:
        disagreement = natural_equal.symmetric_difference(admin_equal)
        mismatch_km2 = disagreement.area / 1_000_000
        if not math.isfinite(mismatch_km2) or mismatch_km2 < 0:
            raise IndependentBorderBlocked("invalid projected mismatch area")
        if mismatch_km2 == 0:
            bands = (0.0, 0.0, 0.0, 0.0)
        else:
            border_lines = unary_union(
                [natural_equal.boundary, admin_equal.boundary]
            )
            if border_lines.is_empty:
                raise IndependentBorderBlocked("missing comparison border")
            remaining = []
            for distance_metres in (1000, 5000, 10000):
                # The buffer is a geometric tolerance *around both input
                # boundaries*, not an assertion that any line is coastline.
                corridor = border_lines.buffer(distance_metres, quad_segs=4)
                beyond_km2 = disagreement.difference(corridor).area / 1_000_000
                if not math.isfinite(beyond_km2):
                    raise IndependentBorderBlocked("nonfinite distance-band area")
                remaining.append(beyond_km2)
            r1, r5, r10 = remaining
            tol = max(1e-3, 1e-6 * mismatch_km2)
            if (r1 < -tol or r5 < -tol or r10 < -tol
                    or r1 > mismatch_km2 + tol
                    or r5 > r1 + tol or r10 > r5 + tol):
                raise IndependentBorderBlocked("nonmonotonic mismatch distance bands")
            bands = (mismatch_km2-r1, r1-r5, r5-r10, r10)
            if any(b < -tol for b in bands) or abs(sum(bands)-mismatch_km2) > tol:
                raise IndependentBorderBlocked("nonconservative mismatch distance bins")
            bands = tuple(max(0.0, b) for b in bands)
    except (ValueError, TypeError, OverflowError, shapely.errors.GEOSException) as exc:
        raise IndependentBorderBlocked("distance-band geometry operation failed") from exc

    a, b, c, d = bands
    return {
        "boundary_proximity_method": (
            "original_geometries_projected_EPSG3035; GEOS_2D_planar_distance_to_"
            "EITHER_input_boundary; quad_segs=4; not_geodetic_distance"
        ),
        "boundary_proximity_threshold_metres": [1000, 5000, 10000],
        "boundary_proximity_total_disagreement_km2": round(mismatch_km2, 3),
        "disagreement_within_1km_of_either_source_border_km2": round(a, 3),
        "disagreement_between_1km_and_5km_from_both_borders_km2": round(b, 3),
        "disagreement_between_5km_and_10km_from_both_borders_km2": round(c, 3),
        "disagreement_farther_than_10km_from_either_border_km2": round(d, 3),
        "disagreement_farther_than_10km_fraction": (
            round(d / mismatch_km2, 6) if mismatch_km2 else 0.0
        ),
        "disagreement_bins_preserve_area": True,
        "source_border_disagreement_is_coastal_or_inland_classified": False,
        "boundary_reference_is_authoritative": False,
        "model_input_approved_by_distance_profile": False,
    }


def compare_geometries(natural_de, admin1_geometries: list) -> dict:
    """Synthetic-testable scientific core. Only aggregates leave the function."""
    import shapely
    from shapely.ops import transform, unary_union
    from pyproj import Transformer

    if (natural_de.geom_type not in ("Polygon", "MultiPolygon") or
            natural_de.is_empty or not natural_de.is_valid):
        raise IndependentBorderBlocked("natural-de source geometry invalid")
    xmin, ymin, xmax, ymax = natural_de.bounds
    if not (5 <= xmin < xmax <= 16 and 47 <= ymin < ymax <= 56):
        raise IndependentBorderBlocked("natural-de geographic coverage outside ceiling")
    if len(admin1_geometries) != ADMIN1_COUNT:
        raise IndependentBorderBlocked("expected 16 independent admin1 geometries")
    for geo in admin1_geometries:
        if (geo.geom_type not in ("Polygon", "MultiPolygon") or
                geo.is_empty or not geo.is_valid):
            raise IndependentBorderBlocked("invalid original admin1 geometry")
        x0, y0, x1, y1 = geo.bounds
        if not (5 <= x0 < x1 <= 16 and 47 <= y0 < y1 <= 56):
            raise IndependentBorderBlocked("admin1 geometry outside German extent")
    # In the validated source the 16 ADM1 units have no material interior
    # overlaps; enforce that here too and do not silently union away duplicates.
    for i, left in enumerate(admin1_geometries):
        for other in admin1_geometries[i+1:]:
            if left.intersects(other):
                overlap = left.intersection(other).area
                if not math.isfinite(overlap) or overlap > MAX_ADMIN1_INTERIOR_OVERLAP_DEG2:
                    raise IndependentBorderBlocked("material overlap in admin1 source")
    try:
        combined = unary_union(admin1_geometries)
        if combined.is_empty or not combined.is_valid:
            raise IndependentBorderBlocked("invalid union of 16 administrative polygons")
        transformer = Transformer.from_crs("EPSG:4326", ANALYSIS_CRS, always_xy=True)
        natural_equal = transform(transformer.transform, natural_de)
        admin_equal = transform(transformer.transform, combined)
        if (not natural_equal.is_valid or not admin_equal.is_valid or
                natural_equal.is_empty or admin_equal.is_empty):
            raise IndependentBorderBlocked("invalid equal-area projected geometry")
        nat_area = float(natural_equal.area) / 1e6
        adm_area = float(admin_equal.area) / 1e6
        common = float(natural_equal.intersection(admin_equal).area) / 1e6
        nat_only = float(natural_equal.difference(admin_equal).area) / 1e6
        adm_only = float(admin_equal.difference(natural_equal).area) / 1e6
        union_area = float(natural_equal.union(admin_equal).area) / 1e6
    except (ValueError, TypeError, OverflowError, shapely.errors.GEOSException) as exc:
        raise IndependentBorderBlocked("spatial overlay or equal-area projection failed") from exc

    values = (nat_area, adm_area, common, nat_only, adm_only, union_area)
    if (not all(math.isfinite(x) and x >= 0 for x in values)
            or min(nat_area, adm_area, union_area) <= 0
            or common > min(nat_area,adm_area)*(1+1e-8)
            or common > union_area*(1+1e-8)):
        raise IndependentBorderBlocked("nonfinite/inconsistent projected areas")
    # EPSG3035 is an equal-area projection. Tolerance applies to geometric
    # floating-point overlay, not to a disputed-border acceptance threshold.
    tol = max(1e-3, 1e-6 * union_area)
    if (abs(nat_area-common-nat_only) > tol
            or abs(adm_area-common-adm_only) > tol
            or abs(union_area-common-nat_only-adm_only) > tol):
        raise IndependentBorderBlocked("nonconservative projected area partition")
    proximity = _boundary_disagreement_distance_profile(natural_equal, admin_equal)
    proximity_delta = abs(
        proximity["boundary_proximity_total_disagreement_km2"] - (nat_only+adm_only)
    )
    if proximity_delta > max(0.01, 1e-6 * union_area):
        raise IndependentBorderBlocked("distance-band total differs from polygon disagreement")
    return {
        **proximity,
        "compared_admin1_geometries": len(admin1_geometries),
        "comparison_crs": ANALYSIS_CRS,
        "area_unit": "km2_approx_equal_area_projection_not_source_truth",
        "natural_earth_area_km2": round(nat_area, 3),
        "geoboundaries_admin1_union_area_km2": round(adm_area, 3),
        "common_area_km2": round(common, 3),
        "natural_earth_only_area_km2": round(nat_only, 3),
        "geoboundaries_only_area_km2": round(adm_only, 3),
        "union_area_km2": round(union_area, 3),
        "intersect_over_union": round(common/union_area, 6),
        "admin1_union_covered_by_natural_earth_fraction": round(common/adm_area, 6),
        "natural_earth_covered_by_admin1_union_fraction": round(common/nat_area, 6),
        "source_or_model_geometries_exported": False,
        "automatic_geometries_repaired_or_snapped": False,
        "independent_reference_confirms_legal_border": False,
        "model_input_approved": False,
    }


def compare_original_bytes(natural: bytes, admin1: bytes) -> dict:
    """Strict exact SHA/length before parsing; source data never returned."""
    if (type(natural) is not bytes or len(natural) != ORIGINAL_BYTES
            or len(natural) > MAX_NATURAL_BYTES
            or hashlib.sha256(natural).hexdigest() != ORIGINAL_SHA256):
        raise IndependentBorderBlocked("Natural Earth immutable original source mismatch")
    if (type(admin1) is not bytes or len(admin1) != SOURCE_LFS_SIZE
            or len(admin1) > MAX_GEOBOUNDARIES_BYTES
            or hashlib.sha256(admin1).hexdigest() != SOURCE_LFS_OID_SHA256):
        raise IndependentBorderBlocked("geoBoundaries original source or LFS mismatch")
    try:
        natural_receipt = inspect_original_geojson(natural)
        geo_receipt = inspect_geojson_bytes(
            admin1, expected_sha256=SOURCE_LFS_OID_SHA256,
            expected_size=SOURCE_LFS_SIZE)
    except (GeojsonBlocked, BoundaryGeometryError, RecursionError, OverflowError) as exc:
        raise IndependentBorderBlocked("one original provider geometry quality gate failed") from exc
    if (natural_receipt["feature_count"] != 177
            or geo_receipt["features"] != 16
            or not geo_receipt["all_polygons_ogc_valid"]):
        raise IndependentBorderBlocked("frozen source coverage or topology mismatch")

    from shapely.geometry import shape
    try:
        ne = json.loads(natural.decode("utf-8"))
        gb = json.loads(admin1.decode("utf-8"))
        candidates = [x for x in ne["features"]
                      if x["properties"].get("ADM0_A3") == "DEU"]
        if (len(candidates) != 1
                or candidates[0]["properties"].get("ISO_A2") != "DE"):
            raise IndependentBorderBlocked("unexpected Natural Earth DEU feature identity")
        natural_geom = shape(candidates[0]["geometry"])
        admin_geoms = [shape(feature["geometry"]) for feature in gb["features"]]
        comparison = compare_geometries(natural_geom, admin_geoms)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise IndependentBorderBlocked("source feature selection failed") from exc
    return {
        "profile": PROFILE,
        "natural_earth_source_id": natural_receipt["source_id"],
        "natural_earth_theme_version": natural_receipt["product_version"],
        "natural_earth_source_sha256": ORIGINAL_SHA256,
        "natural_earth_original_bytes": ORIGINAL_BYTES,
        "geoboundaries_source_id": geo_receipt["source_id"],
        "geoboundaries_original_sha256": SOURCE_LFS_OID_SHA256,
        "geoboundaries_original_bytes": SOURCE_LFS_SIZE,
        "geoboundaries_source_year": COMPARE_YEAR,
        "distinct_providers_and_products_compared": True,
        "different_scale_and_year_policy": "descriptive_comparison_no_border_authority",
        "worldwide_original_nat_earth_topology_qa_pass": False,
        **comparison,
    }


def _read_original(path: Path, expected_size: int, byte_budget: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_size:
        raise IndependentBorderBlocked("not exact pinned regular original file")
    with path.open("rb") as f:
        raw = f.read(byte_budget + 1)
    if len(raw) != expected_size:
        raise IndependentBorderBlocked("original read length mismatch")
    return raw


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--natural-earth-original", type=Path, required=True)
    p.add_argument("--geoboundaries-original", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        a = _read_original(args.natural_earth_original, ORIGINAL_BYTES, MAX_NATURAL_BYTES)
        b = _read_original(args.geoboundaries_original, SOURCE_LFS_SIZE, MAX_GEOBOUNDARIES_BYTES)
        receipt = compare_original_bytes(a, b)
    except (OSError, IndependentBorderBlocked, ValueError, OverflowError, RecursionError):
        # Do not emit filenames, raw input bytes, source feature IDs, or GEOS
        # errors with embedded original coordinate positions.
        print("BLOCKED: original-source DEU cross-provider geometry comparison", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
