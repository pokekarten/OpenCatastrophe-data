# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-wide, checksum-gated HQ100 polygon ring/coordinate quality diagnostic.

Reads every original SHP XY pair in ephemeral RAM, checks ring closure,
nonfinite positions, signed orientation, and original-vs-observed envelope.
NEVER prints geometry, individual ring, identifiers, or coordinates.

All ring facts are diagnostic; they do not validate OGC polygon topology,
SHP shell/hole assignment, ground-survey accuracy or model admission.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    inspect, HQ100OriginalError, _safe_member,
)

EXPECTED_SHA256 = "a2b107c577a06ea2d6264ef916c954767e5d9b11899b9298f58d3c18b7e35571"
MAX_VERTICES = 5_000_000
MAX_RING_PARTS = 500_000


class HQ100GeometryError(ValueError):
    pass


def check_shp(source) -> dict:
    """Read exactly one polygon record from a verified SHP stream."""
    header = source.read(100)
    if len(header) != 100 or struct.unpack_from(">i", header, 0)[0] != 9994:
        raise HQ100GeometryError("Invalid or truncated original SHP header")
    words = struct.unpack_from(">i", header, 24)[0]
    version, shape_type = struct.unpack_from("<ii", header, 28)
    if version != 1000 or shape_type != 5 or words < 50:
        raise HQ100GeometryError("Unsupported original source SHP geometry header")
    advertised_bbox = struct.unpack_from("<4d", header, 36)
    record_header = source.read(8)
    if len(record_header) != 8:
        raise HQ100GeometryError("Missing original polygon record header")
    record_number, content_words = struct.unpack(">II", record_header)
    if (record_number != 1 or content_words < 22
            or 100 + 8 + content_words * 2 != words * 2):
        raise HQ100GeometryError("Only one complete original polygon record is permitted")
    description = source.read(44)
    if len(description) != 44 or struct.unpack_from("<I", description, 0)[0] != 5:
        raise HQ100GeometryError("Expected Polygon shape descriptor")
    record_bbox = struct.unpack_from("<4d", description, 4)
    ring_count, vertex_count = struct.unpack_from("<II", description, 36)
    if (not 1 <= ring_count <= MAX_RING_PARTS
            or not 4 * ring_count <= vertex_count <= MAX_VERTICES
            or content_words * 2 != 44 + 4 * ring_count + 16 * vertex_count):
        raise HQ100GeometryError("Impossible original polygon ring/point counts")
    offset_bytes = source.read(4 * ring_count)
    if len(offset_bytes) != 4 * ring_count:
        raise HQ100GeometryError("Truncated SHP ring offsets")
    offsets = tuple(x[0] for x in struct.iter_unpack("<I", offset_bytes))
    if (offsets[0] != 0 or any(next_i - cur_i < 4 for cur_i, next_i in zip(offsets, offsets[1:]))
            or vertex_count - offsets[-1] < 4):
        raise HQ100GeometryError("Malformed or too-short source polygon rings")
    coordinates = source.read(16 * vertex_count)
    if len(coordinates) != 16 * vertex_count or source.read(1):
        raise HQ100GeometryError("Source polygon coordinate length mismatch")
    points = memoryview(coordinates)
    xmin, ymin, xmax, ymax = math.inf, math.inf, -math.inf, -math.inf
    closed = zero_area = clockwise = counterclockwise = 0
    points_consumed = 0
    for ring, start in enumerate(offsets):
        end = offsets[ring + 1] if ring + 1 < ring_count else vertex_count
        first_x, first_y = struct.unpack_from("<dd", points, 16 * start)
        if not math.isfinite(first_x) or not math.isfinite(first_y):
            raise HQ100GeometryError("Nonfinite original ring vertex")
        prior_x, prior_y = first_x, first_y
        signed_area_twice = 0.0
        for index in range(start, end):
            x, y = struct.unpack_from("<dd", points, 16 * index)
            if not math.isfinite(x) or not math.isfinite(y):
                raise HQ100GeometryError("Nonfinite original coordinate")
            xmin, ymin = min(xmin, x), min(ymin, y)
            xmax, ymax = max(xmax, x), max(ymax, y)
            # Recenter to the first point to avoid cancellation at large x/y.
            signed_area_twice += ((prior_x - first_x) * (y - first_y)
                                  - (x - first_x) * (prior_y - first_y))
            prior_x, prior_y = x, y
            points_consumed += 1
        if (prior_x, prior_y) == (first_x, first_y):
            closed += 1
        signed_area = signed_area_twice * 0.5
        if abs(signed_area) <= 1e-8:
            zero_area += 1
        elif signed_area > 0:
            counterclockwise += 1
        else:
            clockwise += 1
    measured_bbox = (xmin, ymin, xmax, ymax)
    if not (xmin < xmax and ymin < ymax):
        raise HQ100GeometryError("Degenerate full original source extent")
    bbox_matches_record = all(
        math.isclose(a, b, rel_tol=0, abs_tol=1e-4)
        for a, b in zip(measured_bbox, record_bbox))
    bbox_matches_shp = all(
        math.isclose(a, b, rel_tol=0, abs_tol=1e-4)
        for a, b in zip(measured_bbox, advertised_bbox))
    return {
        "original_polygon_records": 1,
        "source_polygon_ring_parts": ring_count,
        "original_coordinate_pairs_read_and_aggregated": points_consumed,
        "closed_ring_parts": closed,
        "open_ring_parts": ring_count - closed,
        "positive_signed_orientation_ring_parts": counterclockwise,
        "negative_signed_orientation_ring_parts": clockwise,
        "zero_or_near_zero_signed_area_ring_parts": zero_area,
        "aggregate_original_projected_bbox_rounded_m": [round(v, 1) for v in measured_bbox],
        "record_bbox_matches_all_original_vertices": bbox_matches_record,
        "file_bbox_matches_all_original_vertices": bbox_matches_shp,
        "all_original_coordinates_finite": True,
        "individual_coordinates_or_ring_geometries_exported": False,
        "source_ring_topological_validity_proven": False,
        "source_shell_hole_relationships_verified": False,
        "source_crs_axis_ground_control_verified": False,
        "source_hazard_depth_values_available_in_archive": False,
        "model_input_admitted": False,
    }


def axis_envelope_screen(bbox: list[float]) -> dict:
    """Competing source axis hypotheses; envelope plausibility is not proof."""
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise HQ100GeometryError("Pinned pyproj required for axis screening") from exc
    xmin, ymin, xmax, ymax = bbox
    x0, x1 = (xmin, xmax)
    y0, y1 = (ymin, ymax)
    transformer = Transformer.from_crs(2169, 4326, always_xy=True)
    scenarios = {}
    for label, swapped in (("as_stored_xy", False), ("swapped_xy", True)):
        positions = []
        for x in (x0, x1):
            for y in (y0, y1):
                lon, lat = transformer.transform(y, x) if swapped else transformer.transform(x, y)
                if not math.isfinite(lon) or not math.isfinite(lat):
                    raise HQ100GeometryError("Coordinate envelope transformation failed")
                positions.append((lon, lat))
        bbox_wgs84 = (
            min(v[0] for v in positions), min(v[1] for v in positions),
            max(v[0] for v in positions), max(v[1] for v in positions))
        # Published EPSG2169 Luxembourg WGS84 area of use, liberal 0.12 deg.
        within = (5.61 <= bbox_wgs84[0] < bbox_wgs84[2] <= 6.65
                  and 49.32 <= bbox_wgs84[1] < bbox_wgs84[3] <= 50.31)
        scenarios[label] = {
            "original_envelope_wgs84_rounded_4dp": [round(v, 4) for v in bbox_wgs84],
            "fits_buffered_luxembourg_epsg2169_area_of_use": within,
        }
    as_stored = scenarios["as_stored_xy"]["fits_buffered_luxembourg_epsg2169_area_of_use"]
    swapped = scenarios["swapped_xy"]["fits_buffered_luxembourg_epsg2169_area_of_use"]
    return {
        "axis_hypotheses": scenarios,
        "axis_envelope_screen": ("native_only_plausible" if as_stored and not swapped else
                                 "swapped_only_plausible" if swapped and not as_stored else
                                 "both_plausible" if as_stored and swapped else
                                 "neither_plausible"),
        "field_survey_axis_or_epoch_verified": False,
    }


def audit(source_zip: Path) -> dict:
    receipt = inspect(Path(source_zip))
    if receipt["original_zip_sha256_observed"] != EXPECTED_SHA256:
        raise HQ100GeometryError("Expected independently observed original SHA256 changed")
    with zipfile.ZipFile(source_zip) as archive:
        matches = [i for i in archive.infolist() if i.filename.lower().endswith(".shp")]
        if len(matches) != 1:
            raise HQ100GeometryError("Expected single source SHP after full original ZIP gate")
        _safe_member(matches[0])
        with archive.open(matches[0]) as stream:
            metrics = check_shp(stream)
    return {
        "profile": "lu-age-hq100-2021-original-full-ring-coordinate-qc-v0",
        "original_sha256": EXPECTED_SHA256,
        "source_geometries_retained": False,
        "source_geometry_object_class": "original single record multipart polygon",
        **metrics,
        **axis_envelope_screen(metrics["aggregate_original_projected_bbox_rounded_m"]),
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
