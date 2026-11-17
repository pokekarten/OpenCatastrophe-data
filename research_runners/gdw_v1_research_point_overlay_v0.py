# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, aggregate GDW reservoir/exposure point overlay rehearsal.

This does not ingest source data or insured exposure, and never emits raw
identifiers, coordinates, polygons, join records, damage or model-ready inputs.
All geometry is caller-provided synthetic Shapely data; provider authenticity,
rights, hydraulic flood extent, datum, exposures and CAT admission remain open.

The GDW original source's approved geometry-only gate is reused verbatim;
invalid/boundary/outside-paired reservoirs cannot enter an overlay.
"""
from __future__ import annotations

import math

from research_runners.gdw_v1_original_spatial_quality_v0 import (
    is_native_reservoir_overlay_geometry_candidate,
)

PROFILE = "gdw-v1-synthetic-research-reservoir-point-overlay-v0"
MAX_SYNTHETIC_RESERVOIRS = 32
MAX_SYNTHETIC_EXPOSURES = 128


class GDWResearchOverlayBlocked(ValueError):
    """The source/exposure or research-only execution boundary was not met."""


def _valid_exposure_point(value: object) -> bool:
    try:
        from shapely.geometry import Point
        from shapely.errors import GEOSException
    except ImportError:
        return False
    if not isinstance(value, Point):
        return False
    try:
        return bool(
            not value.is_empty and not value.has_z
            and math.isfinite(value.x) and math.isfinite(value.y)
            and -180 <= value.x <= 180 and -90 <= value.y <= 90
        )
    except (ValueError, TypeError, OverflowError, GEOSException):
        return False


def _excluded_footprint_bounds(shape: object) -> tuple[float, float, float, float] | None:
    """Use only coarse bounds to quarantine exposure points near an excluded area.

    A malformed/non-polygon/empty/out-of-domain footprint has unknown extent;
    callers must quarantine ALL exposure points rather than infer uniqueness.
    Bounding boxes are an over-exclusion, never an independent flood footprint.
    """
    try:
        from shapely.geometry.base import BaseGeometry
        if (not isinstance(shape, BaseGeometry)
                or shape.geom_type not in ("Polygon", "MultiPolygon")
                or shape.is_empty):
            return None
        west, south, east, north = shape.bounds
        if (not all(math.isfinite(v) for v in (west, south, east, north))
                or west < -180 or east > 180 or south < -90 or north > 90
                or west > east or south > north):
            return None
        return west, south, east, north
    except Exception:
        return None


def screen_synthetic_reservoir_exposure_points(
    reservoir_dam_pairs: list[tuple[object, object]] | tuple[tuple[object, object], ...],
    exposure_points: list[object] | tuple[object, ...],
    *,
    synthetic_research_only: bool,
) -> dict[str, object]:
    """Report counts of possible point-to-reservoir geometry matches only.

    synthetic_research_only=True is a caller assertion, not proof of synthetic
    provenance. It is deliberately a small finite, no-files/no-network helper;
    it cannot approve real insurer exposures or validate the entire GDW v1 ZIP.

    A point strictly in exactly one eligible reservoir is a bounded synthetic
    match, never a globally unique or scientific/insured exposure join. A
    border touch on any other eligible polygon makes even one interior hit
    ambiguous; two strictly containing polygons are also ambiguous. Importantly,
    an excluded polygon is NOT evidence of geographic absence: if its coarse
    bounding rectangle covers a point, that point is quarantined even when
    one other eligible polygon contains it. An excluded unknown/unparseable
    footprint extent quarantines every point; no unique inference is allowed.
    """
    if synthetic_research_only is not True:
        raise GDWResearchOverlayBlocked("synthetic-only research consent is required")
    if (type(reservoir_dam_pairs) not in (list, tuple)
            or type(exposure_points) not in (list, tuple)
            or len(reservoir_dam_pairs) > MAX_SYNTHETIC_RESERVOIRS
            or len(exposure_points) > MAX_SYNTHETIC_EXPOSURES):
        raise GDWResearchOverlayBlocked("unsupported synthetic input collection or size")

    eligible = []
    excluded_bounds = []
    unknown_exclusion_extents = 0
    excluded = 0
    for pair in reservoir_dam_pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise GDWResearchOverlayBlocked("malformed reservoir/dam pair")
        shape, dam_point = pair
        if is_native_reservoir_overlay_geometry_candidate(shape, dam_point):
            eligible.append(shape)
        else:
            excluded += 1
            bounds = _excluded_footprint_bounds(shape)
            if bounds is None:
                unknown_exclusion_extents += 1
            else:
                excluded_bounds.append(bounds)

    if excluded != len(excluded_bounds) + unknown_exclusion_extents:
        raise GDWResearchOverlayBlocked("excluded reservoir extents do not reconcile")

    counts = {
        "points_quarantined_near_excluded_or_unknown_footprints": 0,
        "single_candidate_interior_points": 0,
        "multiple_or_boundary_ambiguous_points": 0,
        "boundary_only_excluded_points": 0,
        "outside_all_screened_reservoirs_points": 0,
    }
    for point in exposure_points:
        if not _valid_exposure_point(point):
            raise GDWResearchOverlayBlocked("non-WGS84 or malformed synthetic exposure point")
        # Even a GEOS-invalid source polygon may still occupy a footprint.
        # Only a coarse bbox is touched: do not query invalid polygon interior,
        # repair its geometry or assume that dropping it proves no overlap.
        if (unknown_exclusion_extents
                or any(w <= point.x <= e and s <= point.y <= n
                       for w, s, e, n in excluded_bounds)):
            counts["points_quarantined_near_excluded_or_unknown_footprints"] += 1
            continue
        inside = 0
        touching = 0
        try:
            for shape in eligible:
                if shape.contains(point):
                    inside += 1
                elif shape.covers(point):
                    touching += 1
        except Exception as exc:
            # Geometry engine/point failures must never become a false zero.
            raise GDWResearchOverlayBlocked("synthetic spatial relation unavailable") from exc
        if inside > 1 or (inside > 0 and touching > 0):
            counts["multiple_or_boundary_ambiguous_points"] += 1
        elif inside == 1:
            counts["single_candidate_interior_points"] += 1
        elif touching:
            counts["boundary_only_excluded_points"] += 1
        else:
            counts["outside_all_screened_reservoirs_points"] += 1

    if excluded + len(eligible) != len(reservoir_dam_pairs):
        raise GDWResearchOverlayBlocked("reservoir screen did not reconcile")
    if sum(counts.values()) != len(exposure_points):
        raise GDWResearchOverlayBlocked("point overlay screen did not reconcile")
    return {
        "schema_version": PROFILE,
        "source_id": "globaldamwatch.gdw.v1.0",
        "source_original_archive_loaded": False,
        "original_source_identity_or_rights_verified_by_this_run": False,
        "only_synthetic_geometries_permitted": True,
        "research_input_reservoir_pairs": len(reservoir_dam_pairs),
        "native_geometry_candidate_pairs": len(eligible),
        "native_geometry_excluded_pairs": excluded,
        "excluded_footprint_coarse_bounds_known": len(excluded_bounds),
        "excluded_footprint_extents_unknown": unknown_exclusion_extents,
        "synthetic_exposure_points": len(exposure_points),
        **counts,
        "excluded_footprint_contact_scientifically_resolved": False,
        "global_geospatial_join_uniqueness_proven": False,
        "hydraulic_inundation_or_failure_hazard_proven": False,
        "insured_exposure_or_value_verified": False,
        "external_exposure_coordinates_or_ids_emitted": False,
        "individual_join_records_or_source_geometries_emitted": False,
        "third_party_source_bytes_persisted": False,
        "CAT_model_input_approved": False,
    }
