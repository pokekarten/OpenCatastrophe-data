#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded synthetic address-point / building-footprint spatial challenge.

No network, private address rows, insurer data or model admission. The JSON
flag 'synthetic_only' is user-declared: it does not independently prove origin.
Return only aggregate counts; never output original feature IDs/coordinates.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import argparse
import json
import math
from pathlib import Path
import re
import sys

try:
    from shapely.geometry import Point, shape
except ImportError:  # Optional spatial dependency profile.
    Point = shape = None

SCHEMA = "oc-point-footprint-linkage-synthetic-v0"
MAX_BYTES = 2_000_000
MAX_POINTS = 250
MAX_FOOTPRINTS = 500
ID = re.compile(r"^synthetic:[A-Za-z0-9_-]{1,48}$")
TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class LinkageDiagnosticError(ValueError):
    """Reject unsupported input before silently producing false matches."""


def fields(value, expected, role):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise LinkageDiagnosticError(f"{role}: invalid field set")
    return value


def code(value, pattern, role):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise LinkageDiagnosticError(f"{role}: invalid identifier")
    return value


def date_field(value, role):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise LinkageDiagnosticError(f"{role}: invalid date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LinkageDiagnosticError(f"{role}: invalid calendar date") from exc


def coord(value, limit, role):
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
        raise LinkageDiagnosticError(f"{role}: invalid coordinate")
    return float(value)


def source(item, role):
    fields(item, ("family", "release", "as_of"), role)
    return (code(item["family"], TAG, "source family"),
            code(item["release"], TAG, "release"),
            date_field(item["as_of"], "source date"))


def polygon_geometry(value):
    if not isinstance(value, dict) or set(value) != {"type", "coordinates"}:
        raise LinkageDiagnosticError("geometry: invalid field set")
    if value["type"] not in ("Polygon", "MultiPolygon"):
        raise LinkageDiagnosticError("geometry: Polygon or MultiPolygon only")
    polys = [value["coordinates"]] if value["type"] == "Polygon" else value["coordinates"]
    if not isinstance(polys, list) or not polys:
        raise LinkageDiagnosticError("geometry: empty polygon")
    for rings in polys:
        if not isinstance(rings, list) or not rings:
            raise LinkageDiagnosticError("geometry: no rings")
        for ring in rings:
            if not isinstance(ring, list) or len(ring) < 4:
                raise LinkageDiagnosticError("geometry: invalid ring")
            for xy in ring:
                if not isinstance(xy, list) or len(xy) != 2:
                    raise LinkageDiagnosticError("geometry: only 2D coordinates")
                coord(xy[0], 180, "geometry.lon")
                coord(xy[1], 90, "geometry.lat")
    try:
        poly = shape(value)
    except Exception as exc:
        raise LinkageDiagnosticError("geometry: unparseable polygon") from exc
    if poly.is_empty or poly.has_z or not poly.is_valid or poly.area <= 0:
        raise LinkageDiagnosticError("geometry: empty, 3D, invalid or zero area")
    x1, y1, x2, y2 = poly.bounds
    if not all(math.isfinite(x) for x in (x1, y1, x2, y2)):
        raise LinkageDiagnosticError("geometry: nonfinite bounds")
    if x1 < -180 or x2 > 180 or y1 < -90 or y2 > 90 or x2-x1 >= 180:
        raise LinkageDiagnosticError("geometry: outside supported WGS84 extent")
    return poly


def evaluate(data):
    if Point is None:
        raise LinkageDiagnosticError("Shapely optional spatial dependencies unavailable")
    fields(data, ("schema_version", "synthetic_only", "crs", "event_as_of",
                  "address_source", "building_source", "addresses", "buildings"), "root")
    if data["schema_version"] != SCHEMA or data["synthetic_only"] is not True:
        raise LinkageDiagnosticError("synthetic-only input contract required")
    if data["crs"] != "EPSG:4326":
        raise LinkageDiagnosticError("CRS must be EPSG:4326 lon/lat")
    event_date = date_field(data["event_as_of"], "event_as_of")
    addr_family, _, addr_date = source(data["address_source"], "address_source")
    bldg_family, _, bldg_date = source(data["building_source"], "building_source")
    if not isinstance(data["addresses"], list) or not 1 <= len(data["addresses"]) <= MAX_POINTS:
        raise LinkageDiagnosticError("address sample budget exceeded")
    if not isinstance(data["buildings"], list) or not 1 <= len(data["buildings"]) <= MAX_FOOTPRINTS:
        raise LinkageDiagnosticError("building sample budget exceeded")

    points, seen = [], set()
    for item in data["addresses"]:
        fields(item, ("case_id", "lat", "lon"), "address")
        key = code(item["case_id"], ID, "case_id")
        if key in seen:
            raise LinkageDiagnosticError("duplicate address identity")
        seen.add(key)
        points.append(Point(coord(item["lon"], 180, "lon"), coord(item["lat"], 90, "lat")))

    polygons, seen = [], set()
    for item in data["buildings"]:
        fields(item, ("building_id", "geometry"), "building")
        key = code(item["building_id"], ID, "building_id")
        if key in seen:
            raise LinkageDiagnosticError("duplicate building identity")
        seen.add(key)
        polygons.append(polygon_geometry(item["geometry"]))

    # Deliberately bounded O(n*m): GEOS/Shapely 1.x and 2.x STRtree return
    # different index shapes. No assumption that an index establishes identity.
    counts = Counter()
    post_event = addr_date > event_date or bldg_date > event_date
    for pt in points:
        if post_event:
            counts["post_event_source_snapshot"] += 1
            continue
        interior = sum(poly.contains(pt) for poly in polygons)
        border = sum(poly.touches(pt) for poly in polygons)
        if interior > 1:
            state = "multiple_containing_footprints"
        elif interior == 1 and border:
            state = "interior_plus_boundary_ambiguity"
        elif interior == 1:
            state = "one_containing_footprint_candidate"
        elif border:
            state = "boundary_only_ambiguous"
        else:
            state = "no_containing_footprint"
        counts[state] += 1

    return {
        "schema_version": SCHEMA,
        "analysis_only": True,
        "synthetic_only": True,
        "address_count": len(points),
        "building_count": len(polygons),
        "same_declared_source_family": addr_family == bldg_family,
        "source_lineage_independence_proven": False,
        "physical_building_identity_proven": False,
        "insured_exposure_admitted": False,
        "cat_model_input_admitted": False,
        "status_counts": {k: counts[k] for k in sorted(counts)},
    }


def unique_object(pairs):
    item = {}
    for key, value in pairs:
        if key in item:
            raise LinkageDiagnosticError("duplicate JSON field")
        item[key] = value
    return item


def reject_nonfinite(value):
    raise LinkageDiagnosticError("nonfinite JSON constant")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        source = args.input
        if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_BYTES:
            raise LinkageDiagnosticError("input must be bounded regular file")
        payload = json.loads(source.read_text(encoding="utf-8"),
                             object_pairs_hook=unique_object, parse_constant=reject_nonfinite)
        print(json.dumps(evaluate(payload), sort_keys=True, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError):
        print("BLOCKED: invalid synthetic geometry or metadata", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
