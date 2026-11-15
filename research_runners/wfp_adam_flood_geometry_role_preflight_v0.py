#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline one-feature GeoJSON geometry *type* preflight for WFP ADAM floods.

Inspect a separately pinned original /items?limit=1 response. No HTTP client,
feature/coordinate export, provider redistribution, building overlap, hazard
extent estimation, commercial rights or model-source admission. A valid Polygon
does NOT establish a surveyed inundation footprint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

PROFILE = "wfp-adam-flood-event-geometry-role-preflight-v0"
SOURCE_ID = "wfp.adam.ogc-global-disaster-impact"
COLLECTION = "adam.adam_fl_events"
ORIGINAL_ENDPOINT = (
    "https://api.adam.geospatial.wfp.org/api/collections/"
    "adam.adam_fl_events/items?limit=1"
)
MAX_BYTES = 524_288
MAX_COORDINATE_PAIRS = 8_000
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ADAMGeometryError(ValueError):
    """Unexpected provider shape or unsafe interpretation of source geometry."""


def _object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ADAMGeometryError("duplicate provider JSON key")
        obj[key] = value
    return obj


def _nonfinite(_value):
    raise ADAMGeometryError("non-finite provider JSON number")


def _position(value):
    if (type(value) is not list or len(value) not in (2, 3)
            or any(type(x) not in (int, float) or not math.isfinite(x) for x in value)
            or not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90):
        raise ADAMGeometryError("coordinate must be a finite WGS84 lon/lat position")
    if len(value) == 3 and not -20_000 <= value[2] <= 200_000:
        raise ADAMGeometryError("third-coordinate plausibility bound exceeded")
    return (value[0], value[1])


def _ring(raw, counter):
    if type(raw) is not list or not 4 <= len(raw) <= MAX_COORDINATE_PAIRS:
        raise ADAMGeometryError("polygon ring must contain at least four positions")
    pairs = []
    for item in raw:
        counter[0] += 1
        if counter[0] > MAX_COORDINATE_PAIRS:
            raise ADAMGeometryError("polygon exceeds coordinate cap")
        pairs.append(_position(item))
    if pairs[0] != pairs[-1]:
        raise ADAMGeometryError("polygon ring not closed")
    if len(set(pairs[:-1])) < 3:
        raise ADAMGeometryError("polygon ring has fewer than three unique vertices")
    # Reject clearly degenerate rings; not a substitute for OGC validity checks.
    area = sum(
        pairs[i][0] * pairs[i + 1][1] - pairs[i + 1][0] * pairs[i][1]
        for i in range(len(pairs) - 1)
    )
    if not math.isfinite(area) or abs(area) < 1e-10:
        raise ADAMGeometryError("degenerate polygon ring")
    return len(pairs)


def _polygon(raw, counter):
    if type(raw) is not list or not raw or len(raw) > 128:
        raise ADAMGeometryError("polygon missing or excessive rings")
    for ring in raw:
        _ring(ring, counter)


def _geometry(value):
    if type(value) is not dict or "crs" in value:
        raise ADAMGeometryError("missing geometry or unexpected local CRS")
    typ = value.get("type")
    coords = value.get("coordinates")
    if typ == "Point":
        _position(coords)
        return "Point"
    counter = [0]
    if typ == "Polygon":
        _polygon(coords, counter)
        return "Polygon"
    if typ == "MultiPolygon":
        if type(coords) is not list or not coords or len(coords) > 64:
            raise ADAMGeometryError("multipolygon missing or excessive components")
        for polygon in coords:
            _polygon(polygon, counter)
        return "MultiPolygon"
    raise ADAMGeometryError("unreviewed flood event geometry type")


def inspect_adam_flood_event_bytes(blob: bytes, expected_sha256: str) -> dict:
    if type(expected_sha256) is not str or not DIGEST.fullmatch(expected_sha256):
        raise ADAMGeometryError("independent source SHA256 must be lowercase hex")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise ADAMGeometryError("provider response empty or too large for one-feature probe")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise ADAMGeometryError("source SHA256 mismatch")
    try:
        record = json.loads(blob.decode("utf-8"), object_pairs_hook=_object,
                            parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ADAMGeometryError("strict provider GeoJSON parse failed") from exc
    if type(record) is not dict or record.get("type") != "FeatureCollection":
        raise ADAMGeometryError("source must be GeoJSON FeatureCollection")
    if "crs" in record or record.get("id") != COLLECTION:
        raise ADAMGeometryError("source collection identity or CRS is ambiguous")
    features = record.get("features")
    if type(features) is not list or len(features) != 1:
        raise ADAMGeometryError("source must contain exactly one bounded example feature")
    for label in ("numberReturned", "numberMatched"):
        if (type(record.get(label)) is not int or record[label] < 1):
            raise ADAMGeometryError("invalid provider " + label + " count")
    if record["numberReturned"] != 1 or record["numberMatched"] < record["numberReturned"]:
        raise ADAMGeometryError("provider counts inconsistent with one-feature request")
    links = record.get("links")
    if type(links) is not list or not links:
        raise ADAMGeometryError("provider feature page links missing")
    if any(type(link) is not dict or type(link.get("rel")) is not str for link in links):
        raise ADAMGeometryError("invalid OGC link metadata")
    if record["numberMatched"] > 1 and not any(link["rel"] == "next" for link in links):
        raise ADAMGeometryError("provider omits next-page link despite more matching features")
    feature = features[0]
    if type(feature) is not dict or feature.get("type") != "Feature":
        raise ADAMGeometryError("provider example is not a Feature")
    if type(feature.get("properties")) is not dict:
        raise ADAMGeometryError("source event properties missing")
    typ = _geometry(feature.get("geometry"))
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "source_collection": COLLECTION,
        "declared_original_endpoint": ORIGINAL_ENDPOINT,
        "original_response_sha256": digest,
        "original_response_bytes": len(blob),
        "one_feature_response_checked": True,
        "observed_example_geometry_type": typ,
        "geometry_semantic_role": (
            "EVENT_LOCATION_POINT_NOT_INUNDATION" if typ == "Point"
            else "UNVERIFIED_SOURCE_POLYGON_NOT_OBSERVED_INUNDATION"
        ),
        "raw_event_or_coordinates_exported": False,
        "geometry_topology_certified": False,
        "observed_inundation_footprint_confirmed": False,
        "flood_depth_or_damaged_buildings_observed": False,
        "building_intersection_permitted": False,
        "provider_upstream_independence_reviewed": False,
        "commercial_reuse_approved": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_geojson", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.original_geojson.resolve() == args.out.resolve():
        parser.error("refusing to overwrite original source data")
    try:
        report = inspect_adam_flood_event_bytes(
            args.original_geojson.read_bytes(), args.expected_sha256
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (ADAMGeometryError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
