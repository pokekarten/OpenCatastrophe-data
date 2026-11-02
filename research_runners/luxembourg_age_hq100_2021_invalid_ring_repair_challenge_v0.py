# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Quarantined repair-algorithm challenge for individually invalid AGE HQ100 rings.

Only process original self-intersecting rings below a bounded vertex limit,
in ephemeral memory. Compare independent GEOS linework and structure methods
as a *technical sensitivity diagnostic*, NOT a floodplain repair algorithm.
Never print individual original geometry, IDs, per-ring metrics or coordinates.
"""
from __future__ import annotations

from collections import Counter
import math


MAX_REPAIR_RING_VERTICES = 50000


def _polygons(geom) -> tuple[list, bool]:
    if geom.is_empty:
        return [], False
    if geom.geom_type == "Polygon":
        return [geom], False
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        parts = []
        debris = False
        for piece in geom.geoms:
            sub, nonpolygon = _polygons(piece)
            parts.extend(sub)
            debris |= nonpolygon
        return parts, debris
    return [], True


class InvalidRingRepairChallenger:
    def __init__(self, *, limit: int = MAX_REPAIR_RING_VERTICES):
        if not isinstance(limit, int) or isinstance(limit, bool) or not 4 <= limit <= MAX_REPAIR_RING_VERTICES:
            raise ValueError("Unsafe repair ring complexity limit")
        self.limit = limit
        self.invalid_observed = 0
        self.skipped = 0
        self.failed = 0
        self.usable = 0
        self.structure_failed = 0
        self.linework_nondebris = 0
        self.same_repair_polygon_set = 0
        self.different_repair_polygon_set = 0
        self.original_boundary_same = 0
        self.original_boundary_different = 0
        self.nominal_area_delta_over_1pct = 0
        self.nominal_area_comparable = 0
        self.linework_parts = Counter()
        self.max_nominal_invalid_ring_area = 0.0
        self.invalid_nominal_area_sum = 0.0
        self.candidate_area_sum = 0.0

    def observe(self, ring, num_vertices: int) -> None:
        """Ring is an already diagnosed invalid Shapely Polygon, transient only."""
        self.invalid_observed += 1
        if num_vertices > self.limit:
            self.skipped += 1
            return
        try:
            from shapely import make_valid
            from shapely.ops import unary_union
            from shapely.errors import GEOSException
            nominal = float(ring.area)
            if not math.isfinite(nominal) or nominal < 0:
                self.failed += 1
                return
            linework = make_valid(ring, method="linework")
            parts, has_debris = _polygons(linework)
            if (not linework.is_valid or not parts
                    or any(not p.is_valid or p.is_empty or not math.isfinite(p.area) or p.area <= 0 for p in parts)):
                self.failed += 1
                return
            assembled = unary_union(parts)
            repaired = float(assembled.area)
            if not math.isfinite(repaired) or repaired <= 0:
                self.failed += 1
                return
            same_boundary = ring.boundary.equals(assembled.boundary)
            self.usable += 1
            self.linework_nondebris += not has_debris
            self.linework_parts["single" if len(parts) == 1 else "multiple"] += 1
            self.invalid_nominal_area_sum += nominal
            self.candidate_area_sum += repaired
            self.max_nominal_invalid_ring_area = max(self.max_nominal_invalid_ring_area, nominal)
            self.original_boundary_same += same_boundary
            self.original_boundary_different += not same_boundary
            if nominal > 0:
                self.nominal_area_comparable += 1
                self.nominal_area_delta_over_1pct += abs(repaired - nominal) / nominal > 0.01
            try:
                structural = make_valid(ring, method="structure", keep_collapsed=True)
                alt, _ = _polygons(structural)
                if not structural.is_valid or not alt or any(not x.is_valid for x in alt):
                    self.structure_failed += 1
                else:
                    other = unary_union(alt)
                    if not math.isfinite(other.area) or other.area <= 0:
                        self.structure_failed += 1
                    elif assembled.equals(other):
                        self.same_repair_polygon_set += 1
                    else:
                        self.different_repair_polygon_set += 1
            except (GEOSException, ValueError, TypeError, OverflowError):
                self.structure_failed += 1
        except (GEOSException, ValueError, TypeError, OverflowError):
            # GEOS errors sometimes contain original coordinates; aggregate only.
            self.failed += 1

    def summary(self, *, expected_invalid: int) -> dict:
        if (self.invalid_observed != expected_invalid or
                self.usable + self.failed + self.skipped != expected_invalid or
                self.original_boundary_same + self.original_boundary_different != self.usable or
                self.same_repair_polygon_set + self.different_repair_polygon_set +
                self.structure_failed != self.usable or
                sum(self.linework_parts.values()) != self.usable):
            raise ValueError("Original invalid ring population not conserved")
        return {
            "original_invalid_ring_count": self.invalid_observed,
            "quarantined_above_vertex_cap": self.skipped,
            "bounded_repair_comparisons_usable": self.usable,
            "bounded_linework_repairs_failed": self.failed,
            "linework_repairs_without_nonpolygon_debris": self.linework_nondebris,
            "linework_result_single_polygon_rings": self.linework_parts["single"],
            "linework_result_multipolygon_rings": self.linework_parts["multiple"],
            "structure_method_failed": self.structure_failed,
            "repair_methods_agree_topological_set": self.same_repair_polygon_set,
            "repair_methods_disagree_topological_set": self.different_repair_polygon_set,
            "original_boundary_lineal_set_unchanged": self.original_boundary_same,
            "original_boundary_lineal_set_changed": self.original_boundary_different,
            "nominal_source_area_vs_repaired_change_over_1pct": self.nominal_area_delta_over_1pct,
            "nominal_source_area_comparable": self.nominal_area_comparable,
            "sum_invalid_rings_nominal_area_projected_m2": round(self.invalid_nominal_area_sum, 2),
            "sum_repair_candidate_ring_area_projected_m2": round(self.candidate_area_sum, 2),
            "maximum_invalid_ring_nominal_area_projected_m2": round(self.max_nominal_invalid_ring_area, 2),
            "invalid_source_area_is_scientific_ground_truth": False,
            "original_source_ring_or_location_exported": False,
            "repair_cannot_be_used_as_flood_extent_without_full_source_topology_review": True,
            "numeric_hazard_depth_observed": False,
            "CAT_model_input_admitted": False,
        }
