# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, quarantined GEOS repair sensitivity for invalid AGE GeoJSON groups.

Works ONLY on already-verified, individually invalid publisher polygon groups.
Both `make_valid(linework)` and `make_valid(structure)` are compared in
temporary memory. Source coordinates and candidate geometry are NEVER output.

The area reported here is the sum of *individual candidate areas*, NOT a
national inundation footprint or an insured-loss input. The source polygons
are invalid, so their nominal source area cannot be treated as ground truth.
"""
from __future__ import annotations

from collections import Counter
import math

MAX_REPAIR_GROUP_VERTICES = 50_000


class GroupRepairChallengeError(ValueError):
    """A bounded non-admitting source repair research check failed."""


def _polygon_parts(geom):
    if geom.is_empty:
        return [], False
    if geom.geom_type == "Polygon":
        return [geom], False
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        polygons = []
        debris = False
        for part in geom.geoms:
            found, nonpolygon = _polygon_parts(part)
            polygons.extend(found)
            debris = debris or nonpolygon
        return polygons, debris
    return [], True


class InvalidPublisherGroupRepairChallenge:
    def __init__(self, *, max_vertices=MAX_REPAIR_GROUP_VERTICES):
        if (not isinstance(max_vertices, int) or isinstance(max_vertices, bool)
                or not 4 <= max_vertices <= MAX_REPAIR_GROUP_VERTICES):
            raise GroupRepairChallengeError("Invalid original group repair vertex cap")
        self.max_vertices = max_vertices
        self.invalid_seen = 0
        self.quarantined = 0
        self.linework_failed = 0
        self.linework_usable = 0
        self.structure_failed = 0
        self.methods_agree = 0
        self.methods_disagree = 0
        self.linework_debris = 0
        self.source_nominal_zero = 0
        self.source_nominal_nonzero = 0
        self.source_area_relative_delta_gt_1pct = 0
        self.source_area_relative_delta_gt_10pct = 0
        self.methods_area_relative_delta_gt_1pct = 0
        self.candidate_areas = 0.0
        self.source_nominal_areas = 0.0
        self.polygon_piece_counts = Counter()

    def observe(self, original, *, point_count: int) -> None:
        from shapely import make_valid
        from shapely.ops import unary_union
        from shapely.errors import GEOSException
        self.invalid_seen += 1
        if point_count > self.max_vertices:
            self.quarantined += 1
            return
        try:
            nominal = float(original.area)
            if not math.isfinite(nominal) or nominal < 0:
                self.linework_failed += 1
                return
            raw_line = make_valid(original, method="linework")
            polygons, debris = _polygon_parts(raw_line)
            if not polygons or any(not p.is_valid or p.is_empty or p.area <= 0
                                   for p in polygons):
                self.linework_failed += 1
                return
            polygonal_line = unary_union(polygons)
            if (not polygonal_line.is_valid or polygonal_line.is_empty
                    or not math.isfinite(polygonal_line.area)
                    or polygonal_line.area <= 0):
                self.linework_failed += 1
                return
            area_line = polygonal_line.area
            self.linework_usable += 1
            self.linework_debris += bool(debris)
            self.polygon_piece_counts["one" if len(polygons) == 1 else "multiple"] += 1
            self.source_nominal_areas += nominal
            self.candidate_areas += area_line
            if nominal <= 1e-12:
                self.source_nominal_zero += 1
            else:
                self.source_nominal_nonzero += 1
                difference = abs(area_line - nominal) / nominal
                self.source_area_relative_delta_gt_1pct += difference > 0.01
                self.source_area_relative_delta_gt_10pct += difference > 0.1
            try:
                raw_structure = make_valid(original, method="structure", keep_collapsed=True)
                structures, _ = _polygon_parts(raw_structure)
                if not structures or any(not p.is_valid or p.is_empty or p.area <= 0
                                         for p in structures):
                    self.structure_failed += 1
                    continue_agree = False
                else:
                    polygonal_structure = unary_union(structures)
                    if (not polygonal_structure.is_valid or polygonal_structure.is_empty
                            or not math.isfinite(polygonal_structure.area)
                            or polygonal_structure.area <= 0):
                        self.structure_failed += 1
                        continue_agree = False
                    else:
                        continue_agree = True
                if continue_agree:
                    if polygonal_line.equals(polygonal_structure):
                        self.methods_agree += 1
                    else:
                        self.methods_disagree += 1
                        if (abs(area_line - polygonal_structure.area) /
                                max(area_line, polygonal_structure.area)) > 0.01:
                            self.methods_area_relative_delta_gt_1pct += 1
            except (GEOSException, ValueError, TypeError, OverflowError):
                self.structure_failed += 1
        except (GEOSException, ValueError, TypeError, OverflowError):
            # Source GEOS exceptions can embed coordinates: count, never log.
            self.linework_failed += 1

    def summary(self, *, expected_invalid: int) -> dict:
        if (expected_invalid != self.invalid_seen
                or self.invalid_seen != self.quarantined + self.linework_failed + self.linework_usable
                or self.linework_usable != self.structure_failed + self.methods_agree
                + self.methods_disagree
                or self.linework_usable != self.source_nominal_nonzero + self.source_nominal_zero
                or self.linework_usable != sum(self.polygon_piece_counts.values())
                or not math.isfinite(self.candidate_areas)
                or not math.isfinite(self.source_nominal_areas)):
            raise GroupRepairChallengeError("Invalid source publisher group comparison population mismatch")
        return {
            "profile": "lu-age-hq2021-invalid-publisher-polygon-group-repair-sensitivity-v0",
            "original_invalid_publisher_group_population": self.invalid_seen,
            "repair_vertex_limit_per_original_group": self.max_vertices,
            "original_invalid_groups_above_repair_vertex_cap": self.quarantined,
            "linework_usable_publisher_groups": self.linework_usable,
            "linework_failures": self.linework_failed,
            "linework_candidate_single_polygon_groups": self.polygon_piece_counts["one"],
            "linework_candidate_split_multipolygon_groups": self.polygon_piece_counts["multiple"],
            "linework_repairs_with_nonpolygon_debris": self.linework_debris,
            "structure_repairs_failed": self.structure_failed,
            "linework_structure_equal_polygonal_sets": self.methods_agree,
            "linework_structure_different_polygonal_sets": self.methods_disagree,
            "repair_methods_area_difference_above_1pct": self.methods_area_relative_delta_gt_1pct,
            "invalid_original_zero_nominal_area_groups": self.source_nominal_zero,
            "invalid_original_nonzero_nominal_area_groups": self.source_nominal_nonzero,
            "original_nominal_vs_linework_area_change_above_1pct": self.source_area_relative_delta_gt_1pct,
            "original_nominal_vs_linework_area_change_above_10pct": self.source_area_relative_delta_gt_10pct,
            "sum_original_invalid_group_nominal_area_m2_not_ground_truth": round(self.source_nominal_areas, 2),
            "sum_linework_repair_candidate_group_area_m2_not_union": round(self.candidate_areas, 2),
            "original_group_geometry_or_location_exported": False,
            "repair_candidates_or_geometry_written": False,
            "complete_original_source_multipolygon_validity_proven": False,
            "hydraulic_floodplain_area_or_depth_proven": False,
            "building_overlay_or_cat_model_input_authorized": False,
        }
