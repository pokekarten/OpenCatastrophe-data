# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned Natural Earth 110m Admin-0 OGC topology and ambiguous-overlap screen.

Reads one already-authorized immutable original GeoJSON file OFFLINE.  It does
not download data, publish provider geometries or country identifiers, repair
polygons, create geopolitical crosswalks, or approve CAT exposure/model use.

This screen intentionally performs *planar* OGC validity and overlap checks in
longitude/latitude: overlap is a diagnostic, NEVER an area measurement in m².
Antimeridian-spanning shapes are excluded from pairwise overlap comparisons
rather than silently unwound. No independent national boundary validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any

from scripts.naturalearth_admin0_geojson_preflight import (
    ORIGINAL_BYTES,
    ORIGINAL_SHA256,
    GeojsonBlocked,
    inspect_original_geojson,
)

PROFILE = "oc-naturalearth-v511-admin0-topology-original-v0"
MAX_BYTES = 1_048_576
# Tiny planar intersection-area epsilon in CRS84 DEGREE^2, not physical area.
# A smaller positive overlap still counts as non-zero if above this threshold.
PLANAR_INTERIOR_EPSILON = 1e-12


class NaturalEarthTopologyError(ValueError):
    """A bounded source input, geometry or topology operation failed."""


def _reason_family(text: str) -> str:
    """Whitelisted GEOS category only; diagnostic often embeds private coords."""
    key = text.partition("[")[0].strip().lower().replace(" ", "_").replace("-", "_")
    return {
        "self_intersection": "self_intersection",
        "ring_self_intersection": "ring_self_intersection",
        "hole_lies_outside_shell": "hole_outside_shell",
        "nested_shells": "nested_shells",
        "holes_are_nested": "nested_holes",
        "disconnected_interior": "disconnected_interior",
        "too_few_points_in_geometry_component": "too_few_points",
        "invalid_coordinate": "invalid_coordinate",
        "ring_is_not_closed": "open_ring",
    }.get(key, "other_invalid_geos_reason")


def inspect_topology(original: bytes, *, require_pinned_identity: bool = True) -> dict[str, Any]:
    """Fail closed on source bytes, then summarize topology without raw geometry."""
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise NaturalEarthTopologyError("missing or oversized original GeoJSON")
    # Shared strict parser establishes byte SHA, release identity and IDs first.
    try:
        structural = inspect_original_geojson(
            original, require_pinned_identity=require_pinned_identity
        )
    except (GeojsonBlocked, ValueError, OverflowError, RecursionError) as exc:
        raise NaturalEarthTopologyError("original structural/identity gate failed") from exc

    from shapely.geometry import shape
    from shapely.strtree import STRtree
    from shapely.validation import explain_validity
    import shapely

    # The strict shared gate has already checked UTF-8, no duplicate keys,
    # no NaNs, ring closure, country IDs, 177 features and the exact SHA.
    document = json.loads(original.decode("utf-8"))
    valid_geometries: list[Any] = []
    invalid_reasons: Counter[str] = Counter()
    antimeridian_ambiguous = 0
    valid = 0
    empty_or_zero = 0
    source_geometry_types: Counter[str] = Counter()
    for feature in document["features"]:
        try:
            geometry = shape(feature["geometry"])
            source_geometry_types[geometry.geom_type] += 1
            if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                raise NaturalEarthTopologyError("nonpolygon geometry after source gate")
            if geometry.is_empty:
                empty_or_zero += 1
                continue
            xmin, ymin, xmax, ymax = geometry.bounds
            if not all(math.isfinite(n) for n in (xmin, ymin, xmax, ymax)):
                raise NaturalEarthTopologyError("nonfinite original geometry bounds")
            # An invalid bow-tie ring can have zero Shapely planar area.
            # Check validity BEFORE area to preserve its causal failure family.
            if not geometry.is_valid:
                invalid_reasons[_reason_family(explain_validity(geometry))] += 1
                continue
            if not math.isfinite(geometry.area) or geometry.area <= 0:
                empty_or_zero += 1
                continue
            valid += 1
            # Prevent interpreting Cartesian intersections of wrap-spanning
            # features as country border overlaps on the globe.
            if xmax - xmin > 180:
                antimeridian_ambiguous += 1
            else:
                valid_geometries.append(geometry)
        except (ValueError, TypeError, OverflowError, shapely.errors.GEOSException) as exc:
            raise NaturalEarthTopologyError("GEOS source geometry processing failed") from exc

    # STRtree indexes a limited array of at most 177 polygons. Candidate
    # intersections on plain CRS84 are diagnostics, not disputed-border truth.
    overlapping_pairs = 0
    touching_pairs = 0
    if valid_geometries:
        try:
            tree = STRtree(valid_geometries)
            for i, left in enumerate(valid_geometries):
                for pos in tree.query(left, predicate="intersects"):
                    j = int(pos)
                    if j <= i:
                        continue
                    intersection = left.intersection(valid_geometries[j])
                    if intersection.is_empty:
                        continue
                    if intersection.area > PLANAR_INTERIOR_EPSILON:
                        overlapping_pairs += 1
                    else:
                        touching_pairs += 1
        except (ValueError, TypeError, OverflowError, shapely.errors.GEOSException) as exc:
            raise NaturalEarthTopologyError("GEOS overlap diagnostic failed") from exc

    feature_count = structural["feature_count"]
    invalid = sum(invalid_reasons.values())
    if valid + invalid + empty_or_zero != feature_count:
        raise NaturalEarthTopologyError("topological feature-count reconciliation failed")
    return {
        "profile": PROFILE,
        "source_id": structural["source_id"],
        "version": structural["product_version"],
        "original_sha256": structural["original_sha256"],
        "original_bytes": structural["original_bytes"],
        "feature_count": feature_count,
        "source_geometry_types": dict(sorted(source_geometry_types.items())),
        "ogc_valid_features": valid,
        "ogc_invalid_features": invalid,
        "empty_or_zero_area_features": empty_or_zero,
        "invalid_reason_families": dict(sorted(invalid_reasons.items())),
        "antimeridian_width_gt_180_features_excluded_from_overlap": antimeridian_ambiguous,
        "planar_crs84_material_overlap_pairs": overlapping_pairs,
        "planar_crs84_touching_pairs": touching_pairs,
        "planar_overlap_area_is_physical_km2": False,
        "topology_qa_pass": invalid == 0 and empty_or_zero == 0,
        "ambiguous_country_point_joins_may_remain": True,
        "independent_national_boundary_completeness_verified": False,
        "country_code_alignment_verified": False,
        "precise_border_or_cadastral_use_approved": False,
        "CAT_model_input_approved": False,
        "original_or_modified_geometries_persisted": False,
        "automatic_repairs_performed": False,
    }


def audit_file(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size != ORIGINAL_BYTES:
        raise NaturalEarthTopologyError("expected exact regular pinned source file")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) != ORIGINAL_BYTES:
        raise NaturalEarthTopologyError("original size drift")
    import hashlib
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise NaturalEarthTopologyError("original SHA-256 drift")
    return inspect_topology(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-geojson", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_file(args.original_geojson)
    except (OSError, NaturalEarthTopologyError, ValueError, OverflowError, RecursionError):
        # Never emit untrusted provider coordinates, source paths, raw GEOS
        # messages containing point locations, or original provider content.
        print("BLOCKED: Natural Earth original source identity/topology audit", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
