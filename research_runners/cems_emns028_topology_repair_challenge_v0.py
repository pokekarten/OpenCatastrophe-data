# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare proposed repairs for a known invalid original CEMS flood footprint.

Pure in-memory numerical diagnostics; never write repaired polygons to disk
or assert that source flood intensity, specific AOI04 extent, rights, TIV,
building damage, or model input has been validated.

Use only the exact pinned 2016 EPSG:32631 source polygon. The two distinct
Shapely 2.1 / GEOS strategies are deliberately NOT equivalent in general.
"""
from __future__ import annotations

import math
from shapely import get_num_coordinates, make_valid
from shapely.validation import explain_validity

EXPECTED_SOURCE_VALID = False
MAX_SOURCE_COORDINATES = 120_000
MAX_OUTPUT_COORDINATES = 300_000
POLYGON_TYPES = frozenset(("Polygon", "MultiPolygon"))


def _round(value: float | int | None, places: int = 6):
    if value is None:
        return None
    v = float(value)
    if not math.isfinite(v):
        return None
    return round(v, places)


def describe_candidate(geom, method: str) -> dict:
    n = int(get_num_coordinates(geom))
    valid = bool(geom.is_valid)
    polygonal = geom.geom_type in POLYGON_TYPES
    return {
        "candidate_method": method,
        "geometry_type": geom.geom_type,
        "topology_valid": valid,
        "validity_reason": explain_validity(geom)[:170],
        "empty": bool(geom.is_empty),
        "coordinates": n,
        "geometry_collection_or_nonpolygonal": not polygonal,
        "polygon_area_m2": _round(geom.area, 2) if valid and polygonal else None,
        "polygon_component_count": (
            len(geom.geoms) if geom.geom_type == "MultiPolygon"
            else 1 if geom.geom_type == "Polygon" else None
        ),
        "candidate_is_model_admitted": False,
        "candidate_is_stored": False,
    }


def compare_repair_methods(source) -> dict:
    if source.geom_type not in POLYGON_TYPES:
        raise ValueError("expected a source polygon or multipolygon")
    if source.is_empty or source.is_valid:
        raise ValueError("this preflight requires the pinned invalid original")
    if get_num_coordinates(source) > MAX_SOURCE_COORDINATES:
        raise ValueError("unbounded source geometry coordinates")
    # Explicitly keep source invalid; invalid source area is NOT
    # a scientifically meaningful baseline for any delta percentage.
    line = make_valid(source, method="linework", keep_collapsed=True)
    structure = make_valid(source, method="structure", keep_collapsed=False)
    candidates = [
        describe_candidate(line, "shapely_make_valid_linework_keepcollapsed"),
        describe_candidate(structure, "shapely_make_valid_structure_dropcollapsed"),
    ]
    # A common legacy GEOS approach is zero-width buffer. Challenge it
    # independently; it may discard overlapping/lower-dimensional parts.
    # Its output is not an endorsement or a physical ground truth.
    buffer_zero = source.buffer(0)
    buffer_zero_meta = describe_candidate(buffer_zero, "shapely_buffer_zero")
    if buffer_zero_meta["coordinates"] > MAX_OUTPUT_COORDINATES:
        raise ValueError("unbounded zero-buffer geometry expansion")

    for c in candidates:
        if c["coordinates"] > MAX_OUTPUT_COORDINATES:
            raise ValueError("unbounded geometry repair expansion")

    comparable = (
        all(c["topology_valid"] and not c["empty"] and
            c["geometry_type"] in POLYGON_TYPES for c in candidates)
    )
    area_delta = symmetric = iou = None
    if comparable:
        # Both repaired results are valid polygonal geometries.
        # This is a METHOD-to-METHOD comparison, NOT a raw-input
        # flood extent area change or a 2016 flood validation.
        a, b = float(line.area), float(structure.area)
        area_delta = _round(abs(a - b), 2)
        sym = float(line.symmetric_difference(structure).area)
        uni = float(line.union(structure).area)
        symmetric = _round(sym, 2)
        iou = _round((uni - sym) / uni, 10) if uni > 0 else None

    buffer_comparable = (
        buffer_zero_meta["topology_valid"] and not buffer_zero_meta["empty"]
        and buffer_zero_meta["geometry_type"] in POLYGON_TYPES
        and candidates[0]["topology_valid"]
        and candidates[0]["geometry_type"] in POLYGON_TYPES
    )
    buffer_area_delta = buffer_sym = buffer_iou = None
    if buffer_comparable:
        # Valid method A vs valid method C; NEVER invalid original area.
        buffer_area_delta = _round(abs(float(buffer_zero.area) - float(line.area)), 2)
        buffer_sym = _round(float(line.symmetric_difference(buffer_zero).area), 2)
        union_area = float(line.union(buffer_zero).area)
        buffer_iou = (_round((union_area - float(
            line.symmetric_difference(buffer_zero).area)) / union_area, 10)
            if union_area > 0 else None)

    return {
        "receipt_kind": "CEMS_EMSN028_INVALID_FLOOD_TOPOLOGY_REPAIR_CHALLENGE_V0",
        "source_geometry_type": source.geom_type,
        "source_topology_valid": False,
        "source_topology_reason": explain_validity(source)[:170],
        "source_coordinates": int(get_num_coordinates(source)),
        "invalid_original_algebraic_area_used_as_truth": False,
        "source_epsg_assumed_from_independent_filegdb_receipt": 32631,
        "candidates": candidates,
        "both_repairs_polygonal_and_comparable": comparable,
        "candidate_area_absolute_delta_m2": area_delta,
        "candidate_symmetric_difference_area_m2": symmetric,
        "candidate_intersection_over_union": iou,
        "zero_buffer_challenge": buffer_zero_meta,
        "zero_buffer_polygonal_and_comparable_to_linework": buffer_comparable,
        "zero_buffer_vs_linework_area_delta_m2": buffer_area_delta,
        "zero_buffer_vs_linework_symmetric_difference_m2": buffer_sym,
        "zero_buffer_vs_linework_intersection_over_union": buffer_iou,
        "methods_have_independent_physical_validation": False,
        "aoi04_specific_original_polygon_verified": False,
        "source_rights_approved": False,
        "building_or_insurer_overlay_authorized": False,
        "model_input_admitted": False,
        "derived_repair_polygons_stored": False,
    }
