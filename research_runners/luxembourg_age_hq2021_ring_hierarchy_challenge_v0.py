# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""AGE 2021 HQ10/HQ100/HQext original SHP ring hierarchy *challenge*.

The ESRI Shapefile Polygon winding convention (clockwise exterior, CCW
interior) is only a hypothesis; it does not imply that this publisher
encoded every source ring correctly. For *individually valid* rings,
query bounded spatial indexes and test full GEOS shell.covers(hole).
Original-invalid rings remain unresolved, never automatically repaired.

No original geometry, individual ring bounds, coordinates, locations or
joinable source identifiers are exported. National aggregate counts only.
No full multipolygon geometry is rebuilt or admitted into CAT models.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    HQ100OriginalError, inspect, _safe_member,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    HQ100GeometryError, check_shp, EXPECTED_SHA256 as HQ100_SHA,
)
from research_runners.luxembourg_age_hq2021_sibling_source_receipts_v0 import (
    SOURCES, audit as sibling_receipt,
)
from research_runners.luxembourg_age_hq2021_sibling_full_geometry_quality_v0 import (
    EXPECTED_SHA256 as SIBLING_SHA,
)

MAX_RING_COUNT = 20000
MAX_CANDIDATES_PER_HOLE = 512


class HierarchyChallengeError(ValueError):
    """Source cannot be evaluated safely without provider geometry admission."""


class SourceRingHierarchy:
    def __init__(self, *, max_candidates=MAX_CANDIDATES_PER_HOLE):
        if (not isinstance(max_candidates, int) or isinstance(max_candidates, bool)
                or not 1 <= max_candidates <= MAX_CANDIDATES_PER_HOLE):
            raise HierarchyChallengeError("Unbounded spatial index candidate limit")
        self.max_candidates = max_candidates
        self.seen = 0
        self.negative_winding = 0
        self.positive_winding = 0
        self.zero_winding = 0
        self.valid_shells = []
        self.invalid_shell_envelopes = []
        self.valid_holes = []
        self.invalid_hole_count = 0

    def observe(self, points) -> None:
        from shapely.geometry import Polygon, box
        from shapely.errors import GEOSException
        self.seen += 1
        if self.seen > MAX_RING_COUNT or len(points) < 4:
            raise HierarchyChallengeError("Original multipart ring budget exceeded")
        x0, y0 = points[0]
        if (not math.isfinite(x0) or not math.isfinite(y0)
                or points[-1] != points[0]):
            raise HierarchyChallengeError("Source ring nonfinite/open")
        # Recenter for numeric cancellation safety; coordinates never logged.
        signed2 = math.fsum(
            (points[i][0]-x0) * (points[i+1][1]-y0)
            - (points[i+1][0]-x0) * (points[i][1]-y0)
            for i in range(len(points)-1)
        )
        if not math.isfinite(signed2) or abs(signed2) < 2e-8:
            self.zero_winding += 1
            return
        try:
            ring = Polygon(points)
            valid = ring.is_valid and not ring.is_empty and ring.area > 0
        except (GEOSException, ValueError, TypeError, OverflowError) as exc:
            raise HierarchyChallengeError("Original GEOS ring could not be represented") from exc
        if signed2 < 0:
            self.negative_winding += 1
            if valid:
                self.valid_shells.append(ring)
            else:
                self.invalid_shell_envelopes.append(box(*ring.bounds))
        else:
            self.positive_winding += 1
            if valid:
                self.valid_holes.append(ring)
            else:
                self.invalid_hole_count += 1

    def summary(self, *, expected_rings: int) -> dict:
        from shapely.strtree import STRtree
        from shapely.errors import GEOSException
        if self.seen != expected_rings or self.seen > MAX_RING_COUNT:
            raise HierarchyChallengeError("Original source ring population not conserved")
        if self.seen != self.negative_winding + self.positive_winding + self.zero_winding:
            raise HierarchyChallengeError("Source signed ring winding count does not conserve")
        shells = self.valid_shells
        bad_shells = self.invalid_shell_envelopes
        tree = STRtree(shells) if shells else None
        invalid_tree = STRtree(bad_shells) if bad_shells else None
        exactly_one = multiple = uncovered = 0
        potentially_affected_by_invalid_shell = 0
        candidate_budget_quarantined = 0
        geos_errors = 0
        total_exact_checks = 0
        for hole in self.valid_holes:
            # Invalid-shell bounding boxes are only a *possible* cover,
            # never a basis to authorize an original source hole.
            suspect = 0
            if invalid_tree is not None:
                for i in invalid_tree.query(hole):
                    if bad_shells[int(i)].envelope.covers(hole.envelope):
                        suspect += 1
            if suspect:
                potentially_affected_by_invalid_shell += 1
            candidates = [] if tree is None else tree.query(hole)
            if len(candidates) > self.max_candidates:
                candidate_budget_quarantined += 1
                continue
            covers = 0
            for idx in candidates:
                shell = shells[int(idx)]
                if not shell.envelope.covers(hole.envelope):
                    continue
                total_exact_checks += 1
                try:
                    if shell.covers(hole):
                        covers += 1
                except (GEOSException, ValueError, OverflowError):
                    geos_errors += 1
            if covers == 0:
                uncovered += 1
            elif covers == 1:
                exactly_one += 1
            else:
                multiple += 1
        if (exactly_one + multiple + uncovered + candidate_budget_quarantined
                != len(self.valid_holes)):
            raise HierarchyChallengeError("Original hole candidate population not conserved")
        # Some "uncovered" holes might belong to invalid exteriors or
        # overlap an outer ring without exact containment.
        return {
            "original_shapefile_polygon_winding_convention_hypothesis": (
                "clockwise_exterior_counterclockwise_hole"),
            "original_ring_count": self.seen,
            "clockwise_exterior_candidate_rings": self.negative_winding,
            "counterclockwise_hole_candidate_rings": self.positive_winding,
            "zero_orientation_rings": self.zero_winding,
            "geos_valid_clockwise_exterior_candidates": len(shells),
            "geos_invalid_clockwise_exterior_candidates": len(bad_shells),
            "geos_valid_counterclockwise_hole_candidates": len(self.valid_holes),
            "geos_invalid_counterclockwise_hole_candidates": self.invalid_hole_count,
            "valid_holes_with_exactly_one_valid_shell_cover": exactly_one,
            "valid_holes_with_multiple_valid_shell_covers": multiple,
            "valid_holes_with_no_valid_shell_cover": uncovered,
            "valid_holes_with_possible_invalid_shell_bbox_cover": (
                potentially_affected_by_invalid_shell),
            "valid_holes_quarantined_by_spatial_candidate_cap": candidate_budget_quarantined,
            "valid_shell_hole_full_geos_covers_checks": total_exact_checks,
            "geos_cover_test_errors": geos_errors,
            "ring_hierarchy_fully_authorized": False,
            "invalid_rings_auto_repaired": False,
            "full_original_multipart_polygon_topology_verified": False,
            "real_flood_depth_observed": False,
            "flood_building_intersection_authorized": False,
            "source_geometries_or_ring_identifiers_persisted": False,
            "cat_loss_model_input_admitted": False,
        }


def audit(path: Path, scenario: str) -> dict:
    if scenario == "hq100":
        receipt = inspect(path)
        expected = HQ100_SHA
        n_rings = next(x["shp_total_polygon_ring_parts"]
                       for x in receipt["format_header_inventory_only"] if x["format"] == ".shp")
    elif scenario in SIBLING_SHA:
        receipt = sibling_receipt(path, scenario=scenario)
        expected = SIBLING_SHA[scenario]
        n_rings = receipt["original_source_ring_parts"]
    else:
        raise HierarchyChallengeError("Unknown original hazard scenario")
    observed_sha = receipt.get("original_zip_sha256_observed", receipt.get("observed_sha256"))
    if observed_sha != expected:
        raise HierarchyChallengeError("Original byte-pinned source has changed")
    collector = SourceRingHierarchy()
    with zipfile.ZipFile(path) as archive:
        members = [x for x in archive.infolist() if x.filename.lower().endswith(".shp")]
        if len(members) != 1:
            raise HierarchyChallengeError("Expected exactly one original polygon source")
        _safe_member(members[0])
        with archive.open(members[0]) as src:
            dimensions = check_shp(src, ring_diagnostic=collector.observe)
    if dimensions["source_polygon_ring_parts"] != n_rings:
        raise HierarchyChallengeError("Source record and ring-count conservation failed")
    result = collector.summary(expected_rings=n_rings)
    if (result["zero_orientation_rings"] != 0 or
            result["geos_cover_test_errors"] != 0 or
            result["valid_holes_quarantined_by_spatial_candidate_cap"] != 0):
        # Fail-closed means report test outcome with no admission, not
        # throwing away the diagnostic; uncertainty stays explicit.
        result["source_hierarchy_contains_unresolved_geometry"] = True
    else:
        result["source_hierarchy_contains_unresolved_geometry"] = bool(
            result["geos_invalid_clockwise_exterior_candidates"]
            or result["geos_invalid_counterclockwise_hole_candidates"]
            or result["valid_holes_with_multiple_valid_shell_covers"]
            or result["valid_holes_with_no_valid_shell_cover"]
            or result["valid_holes_with_possible_invalid_shell_bbox_cover"])
    return {
        "profile": "lu-age-2021-original-winding-shell-hole-challenge-v0",
        "scenario": scenario,
        "source_original_sha256": expected,
        **result,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", choices=["hq10", "hq100", "hqext"], required=True)
    p.add_argument("--source-zip", type=Path, required=True)
    args = p.parse_args()
    try:
        print(json.dumps(audit(args.source_zip, args.scenario),
                         indent=2, sort_keys=True, allow_nan=False))
    except (OSError, HQ100OriginalError, HQ100GeometryError,
            HierarchyChallengeError, zipfile.BadZipFile) as exc:
        p.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
