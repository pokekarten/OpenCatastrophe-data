# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only make_valid(linework) diagnosis of invalid original ACT polygons.

No original geometry, ID, coordinates, or per-object repair is emitted.
GEOS area on an INVALID source polygon is a nominal calculation, not
independently observed floor area or ground truth. No automatic admission.
"""
from __future__ import annotations

from collections import Counter
import math

from shapely import make_valid
from shapely.errors import GEOSException
from shapely.ops import unary_union


def _components(geometry) -> tuple[list, bool]:
    """Find nonempty polygon components and lower-dimensional repair debris."""
    if geometry.is_empty:
        return [], False
    if geometry.geom_type == "Polygon":
        return [geometry], False
    if geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
        polygons = []
        debris = False
        for child in geometry.geoms:
            children, nonpoly = _components(child)
            polygons.extend(children)
            debris |= nonpoly
        return polygons, debris
    return [], True


class RepairDiagnostics:
    def __init__(self) -> None:
        self.cases = 0
        self.outcomes: Counter[str] = Counter()
        self.with_nonpolygon_debris = 0
        self.nonfinite_nominal_area = 0
        self.nonpositive_nominal_area = 0
        self.relative_comparable = 0
        self.relative_delta_gt_1pct = 0
        self.relative_delta_gt_5pct = 0
        self.relative_delta_gt_20pct = 0
        self.absolute_deltas = []
        self.structure_usable = 0
        self.structure_unusable = 0
        self.structure_polygon_count_disagreements = 0
        self.structure_area_disagreements = 0
        self.structure_topological_set_disagreements = 0
        self.structure_symdiff_area_disagreements = 0

    def observe(self, original) -> None:
        """Evaluate a single invalid in-memory source polygon; aggregate only."""
        if original.is_valid or original.is_empty:
            raise ValueError("Only nonempty invalid source polygons can be assessed")
        self.cases += 1
        try:
            candidate = make_valid(original, method="linework")
            polygons, debris = _components(candidate)
            if (not candidate.is_valid or not polygons
                    or any(not p.is_valid or p.is_empty or not math.isfinite(p.area)
                           or p.area <= 0 for p in polygons)):
                self.outcomes["unusable_or_not_polygonal"] += 1
                return
            after = math.fsum(p.area for p in polygons)
            if not math.isfinite(after) or after <= 0:
                self.outcomes["unusable_or_not_polygonal"] += 1
                return
            before = original.area
            if not math.isfinite(before):
                self.nonfinite_nominal_area += 1
                self.outcomes["unusable_or_not_polygonal"] += 1
                return
            self.outcomes["single_polygon" if len(polygons) == 1 else "multiple_polygons"] += 1
            if debris:
                self.with_nonpolygon_debris += 1
            # Independent GEOS repair strategy challenge, also ephemeral only.
            # Same numerical area is not evidence of an accurate building boundary.
            try:
                challenger = make_valid(original, method="structure", keep_collapsed=True)
                alt_polygons, _ = _components(challenger)
                if (not challenger.is_valid or not alt_polygons
                        or any(not p.is_valid or p.is_empty or not math.isfinite(p.area)
                               or p.area <= 0 for p in alt_polygons)):
                    self.structure_unusable += 1
                else:
                    alt_area = math.fsum(p.area for p in alt_polygons)
                    if not math.isfinite(alt_area) or alt_area <= 0:
                        self.structure_unusable += 1
                    else:
                        # Compare the *valid repaired polygon sets* rather than
                        # just their total area. Polygon lines/points are ignored
                        # for this set comparison but tracked separately above.
                        a = unary_union(polygons)
                        b = unary_union(alt_polygons)
                        diff_area = a.symmetric_difference(b).area
                        if not math.isfinite(diff_area):
                            raise ValueError("Nonfinite geometric challenge")
                        tolerance = max(1e-6, 1e-8 * max(alt_area, after))
                        self.structure_usable += 1
                        self.structure_polygon_count_disagreements += len(alt_polygons) != len(polygons)
                        self.structure_area_disagreements += abs(alt_area - after) > tolerance
                        self.structure_topological_set_disagreements += not a.equals(b)
                        self.structure_symdiff_area_disagreements += diff_area > tolerance
            except (GEOSException, ValueError, TypeError, OverflowError):
                self.structure_unusable += 1
            delta = abs(after - before)
            self.absolute_deltas.append(delta)
            if before <= 0:
                self.nonpositive_nominal_area += 1
            else:
                self.relative_comparable += 1
                ratio = delta / before
                self.relative_delta_gt_1pct += ratio > 0.01
                self.relative_delta_gt_5pct += ratio > 0.05
                self.relative_delta_gt_20pct += ratio > 0.20
        except (GEOSException, ValueError, TypeError, OverflowError):
            self.outcomes["unusable_or_not_polygonal"] += 1

    def summary(self, expected: int) -> dict:
        if self.cases != expected or sum(self.outcomes.values()) != expected:
            raise ValueError("Repair diagnosis does not conserve invalid source population")
        if (self.structure_usable + self.structure_unusable !=
                self.outcomes["single_polygon"] + self.outcomes["multiple_polygons"]):
            raise ValueError("Independent repair challenger does not conserve usable linework cases")
        changes = sorted(self.absolute_deltas)
        mid = (len(changes) - 1) // 2
        p95 = math.ceil(len(changes) * 0.95) - 1
        return {
            "invalid_original_polygons_assessed": self.cases,
            "repair_algorithm": "Shapely 2.1.2 / GEOS make_valid(method=linework)",
            "repair_single_polygon": self.outcomes["single_polygon"],
            "repair_multiple_polygons": self.outcomes["multiple_polygons"],
            "repair_unusable_or_not_polygonal": self.outcomes["unusable_or_not_polygonal"],
            "repair_with_nonpolygon_debris": self.with_nonpolygon_debris,
            "structure_challenge_usable": self.structure_usable,
            "structure_challenge_unusable": self.structure_unusable,
            "structure_vs_linework_polygon_count_disagreements": self.structure_polygon_count_disagreements,
            "structure_vs_linework_area_disagreements_over_tolerance": self.structure_area_disagreements,
            "structure_vs_linework_topological_set_disagreements": self.structure_topological_set_disagreements,
            "structure_vs_linework_symmetric_difference_area_disagreements_over_tolerance": self.structure_symdiff_area_disagreements,
            "area_change_comparable_nonzero_nominal": self.relative_comparable,
            "nonpositive_nominal_invalid_polygon_area": self.nonpositive_nominal_area,
            "nonfinite_nominal_invalid_polygon_area": self.nonfinite_nominal_area,
            "absolute_nominal_vs_repaired_area_change_sum_m2": round(math.fsum(changes), 2),
            "absolute_nominal_vs_repaired_area_change_median_m2": round(changes[mid], 2) if changes else None,
            "absolute_nominal_vs_repaired_area_change_p95_m2": round(changes[p95], 2) if changes else None,
            "relative_delta_over_1pct_of_nonzero_nominal": self.relative_delta_gt_1pct,
            "relative_delta_over_5pct_of_nonzero_nominal": self.relative_delta_gt_5pct,
            "relative_delta_over_20pct_of_nonzero_nominal": self.relative_delta_gt_20pct,
            "nominal_invalid_polygon_area_is_ground_truth": False,
            "all_repaired_polygons_quarantined_for_manual_scientific_review": True,
            "automatically_repaired_source_geometries_persisted": False,
            "building_geometry_model_input_approved": False,
        }
