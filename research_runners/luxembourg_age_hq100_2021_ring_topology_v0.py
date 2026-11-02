# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Full original-source AGE HQ100 independent-ring GEOS topology diagnostic.

Original SHA1/SHA256/CRC/record and finite-XY checks precede this step.
Checks each of 6,379 source rings as an *individual polygon* only.
This cannot validate shell/hole assignment or topology of the full multipart
record; source GEOS errors and potentially unsafe complexity are quarantined.
Original per-ring XY, vertex lists, centroids and geometry are never emitted.
"""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    HQ100OriginalError, _safe_member, inspect,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    check_shp, HQ100GeometryError, EXPECTED_SHA256,
)

MAX_RING_VERTEX_COMPLEXITY = 2_000_000
SAFE_REASONS = {
    "Ring Self-intersection", "Self-intersection",
    "Too few points in geometry component", "Nested shells",
    "Hole lies outside shell", "Disconnected interior",
    "Invalid Coordinate", "Duplicate Rings", "other_invalid_topology",
}


class RingTopologyCounter:
    def __init__(self, *, max_ring_vertices=MAX_RING_VERTEX_COMPLEXITY):
        if (not isinstance(max_ring_vertices, int) or isinstance(max_ring_vertices, bool)
                or not 4 <= max_ring_vertices <= MAX_RING_VERTEX_COMPLEXITY):
            raise ValueError("Unbounded ring complexity limit")
        self.max_ring_vertices = max_ring_vertices
        self.seen = 0
        self.valid = 0
        self.invalid = 0
        self.skipped_complex = 0
        self.topology_errors = 0
        self.invalid_reasons = Counter()

    def observe(self, points) -> None:
        from shapely.geometry import Polygon
        from shapely.validation import explain_validity
        from shapely.errors import GEOSException
        self.seen += 1
        if len(points) > self.max_ring_vertices:
            self.skipped_complex += 1
            return
        try:
            geom = Polygon(points)
            if geom.is_valid and not geom.is_empty and geom.area > 0:
                self.valid += 1
            else:
                self.invalid += 1
                # Never log GEOS invalidity's embedded coordinate values.
                reason = explain_validity(geom).split("[", 1)[0].strip()
                self.invalid_reasons[
                    reason if reason in SAFE_REASONS else "other_invalid_topology"] += 1
        except (GEOSException, ValueError, TypeError, OverflowError):
            self.topology_errors += 1

    def summary(self, expected) -> dict:
        if (self.seen != expected or
                self.valid + self.invalid + self.skipped_complex + self.topology_errors != expected
                or sum(self.invalid_reasons.values()) != self.invalid):
            raise HQ100GeometryError("Original source ring topology diagnostic count mismatch")
        return {
            "source_rings_examined_total": self.seen,
            "individually_valid_nonzero_area_rings": self.valid,
            "individually_invalid_rings": self.invalid,
            "invalid_ring_topology_reasons_aggregate": dict(sorted(self.invalid_reasons.items())),
            "complex_ring_geometry_test_skipped": self.skipped_complex,
            "geos_ring_test_errors": self.topology_errors,
            "individual_original_ring_geometry_or_location_exported": False,
            "full_multipart_polygon_ogc_validity_verified": False,
            "correct_exterior_hole_nesting_verified": False,
            "building_to_hazard_overlap_authorized": False,
            "flood_depth_available_or_inferred": False,
            "model_input_admitted": False,
        }


def audit(original_zip: Path) -> dict:
    receipt = inspect(original_zip)
    if receipt["original_zip_sha256_observed"] != EXPECTED_SHA256:
        raise HQ100GeometryError("Original provider SHA256 drift")
    collector = RingTopologyCounter()
    with zipfile.ZipFile(original_zip) as z:
        items = [x for x in z.infolist() if x.filename.lower().endswith(".shp")]
        if len(items) != 1:
            raise HQ100GeometryError("Only one original SHP expected")
        _safe_member(items[0])
        with z.open(items[0]) as stream:
            source = check_shp(stream, ring_diagnostic=collector.observe)
    return {
        "profile": "lu-age-hq100-2021-original-per-ring-geos-topology-v0",
        "sha256_original_verified": EXPECTED_SHA256,
        "original_source_coordinate_pair_count": source["original_coordinate_pairs_read_and_aggregated"],
        "source_ring_population": source["source_polygon_ring_parts"],
        **collector.summary(source["source_polygon_ring_parts"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_zip), indent=2, sort_keys=True, allow_nan=False))
    except (OSError, HQ100OriginalError, HQ100GeometryError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
