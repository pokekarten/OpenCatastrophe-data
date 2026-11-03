# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GEOS OGC-validity challenge of the *publisher's own* AGE GeoJSON groupings.

Use only after full publisher SHA1 and JSON structure/coordinate validation.
Never repair individual original polygons or emit source per-group coordinates,
identifiers, error text, individual geometry stats, or source locations.
Bound per-polygon complexity and preserve every skipped group as unresolved.

This is an OGC polygon-per-group diagnostic, NOT validity proof for the
complete MultiPolygon feature, hydraulic flood scenario or insured property.
"""
from __future__ import annotations

from collections import Counter

MAX_GEOS_POLYGON_GROUP_VERTICES = 120_000
MAX_OPTIONAL_MEGA_GROUP_VERTICES = 1_200_000
MAX_PUBLISHER_GROUPS = 100_000
ALLOWED_OGC_REASON_LABELS = {
    "Self-intersection",
    "Ring Self-intersection",
    "Hole lies outside shell",
    "Holes are nested",
    "Nested shells",
    "Disconnected interior",
    "Too few points in geometry component",
    "Duplicate Rings",
    "Invalid Coordinate",
}


class GroupTopologyError(ValueError):
    """The original publisher geometry cannot be safely examined."""


def _polygons(obj):
    kind = obj.get("type")
    if kind == "FeatureCollection":
        features = obj.get("features", [])
    elif kind == "Feature":
        features = [obj]
    elif kind in ("Polygon", "MultiPolygon"):
        features = [{"geometry": obj}]
    else:
        raise GroupTopologyError("Publisher root geometry not polygonal")
    if not isinstance(features, list) or not 1 <= len(features) <= MAX_PUBLISHER_GROUPS:
        raise GroupTopologyError("Oversized source feature group")
    for feat in features:
        geom = feat.get("geometry")
        if not isinstance(geom, dict):
            raise GroupTopologyError("Missing publisher polygon geometry")
        shape = geom.get("type")
        coords = geom.get("coordinates")
        if not isinstance(coords, list):
            raise GroupTopologyError("Publisher source coordinates unavailable")
        if shape == "Polygon":
            yield coords
        elif shape == "MultiPolygon":
            yield from coords
        else:
            raise GroupTopologyError("Unexpected nonpolygon publisher geometry")


def challenge_publisher_groups(obj: dict, *, max_group_vertices: int =
                               MAX_GEOS_POLYGON_GROUP_VERTICES,
                               invalid_repair_challenger=None) -> dict:
    if (not isinstance(max_group_vertices, int) or isinstance(max_group_vertices, bool)
            or not 4 <= max_group_vertices <= MAX_OPTIONAL_MEGA_GROUP_VERTICES):
        raise GroupTopologyError("Invalid bounded original GEOS group complexity")
    try:
        from shapely.geometry import Polygon
        from shapely.validation import explain_validity
        from shapely.errors import GEOSException
        import shapely
    except ImportError as exc:
        raise GroupTopologyError("Pinned Shapely required") from exc
    if shapely.__version__ != "2.2.0":
        raise GroupTopologyError("Unpinned Shapely in source diagnostic")
    n = valid = invalid = skipped = errors = 0
    groups_with_holes = 0
    quarantined_vertex_total = 0
    quarantined_hole_total = 0
    largest_group_vertices = 0
    reasons = Counter()
    for rings in _polygons(obj):
        n += 1
        if n > MAX_PUBLISHER_GROUPS:
            raise GroupTopologyError("Unbounded official polygon groups")
        if not isinstance(rings, list) or not rings:
            raise GroupTopologyError("Missing original polygon ring group")
        groups_with_holes += len(rings) > 1
        npoints = sum(len(r) for r in rings)
        largest_group_vertices = max(largest_group_vertices, npoints)
        if npoints > max_group_vertices:
            skipped += 1
            quarantined_vertex_total += npoints
            quarantined_hole_total += len(rings) - 1
            continue
        try:
            geom = Polygon(rings[0], rings[1:])
            if geom.is_valid and not geom.is_empty and geom.area > 0:
                valid += 1
            else:
                invalid += 1
                if invalid_repair_challenger is not None:
                    invalid_repair_challenger.observe(geom, point_count=npoints)
                # GEOS error explanations embed original coordinates. The
                # published report carries ONLY a strict reason category.
                reason = explain_validity(geom).split("[", 1)[0].strip()
                reasons[reason if reason in ALLOWED_OGC_REASON_LABELS
                        else "other_invalid_group_topology"] += 1
        except (GEOSException, ValueError, TypeError, OverflowError):
            errors += 1
    if n < 1 or n != valid + invalid + skipped + errors or sum(reasons.values()) != invalid:
        raise GroupTopologyError("Original publisher polygon group count not conserved")
    repair_summary = (invalid_repair_challenger.summary(expected_invalid=invalid)
                      if invalid_repair_challenger is not None else None)
    return {
        "profile": "lu-age-hq2021-publisher-original-geojson-group-OGC-v0",
        "original_publisher_groups_examined": n,
        "publisher_groups_with_assigned_holes": groups_with_holes,
        "individually_geos_valid_publisher_polygon_groups": valid,
        "individually_geos_invalid_publisher_polygon_groups": invalid,
        "invalid_group_ogc_reason_categories_only": dict(sorted(reasons.items())),
        "publisher_groups_over_vertex_complexity_budget": skipped,
        "source_polygon_group_vertex_budget_applied": max_group_vertices,
        "largest_source_polygon_group_point_count": largest_group_vertices,
        "quarantined_publisher_polygon_group_point_total": quarantined_vertex_total,
        "quarantined_publisher_polygon_group_hole_ring_total": quarantined_hole_total,
        "publisher_group_geos_errors": errors,
        "every_original_publisher_group_tested": skipped == 0 and errors == 0,
        "whole_original_publisher_multipolygon_OGC_validity_verified": False,
        "source_polygons_repaired_or_admitted": False,
        "original_source_coordinates_or_feature_ids_exported": False,
        "hydraulic_depth_intensity_or_insurer_TIV_verified": False,
        "CAT_loss_input_admitted": False,
        **({"invalid_publisher_group_repair_sensitivity": repair_summary}
           if repair_summary is not None else {}),
    }
