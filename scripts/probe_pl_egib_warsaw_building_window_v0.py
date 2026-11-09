#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original EGiB WFS 2.0 Warsaw two-building *geometry QA* receipt.

Original data remain outside Git; emit no feature geometry, identifiers or
attribute values. Only --live performs a fixed HTTPS WFS GetFeature request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

PROVIDER = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/EGIB/WFS/UslugaZbiorcza"
FEATURE_TYPE = "ms:budynki"
CRS = "urn:ogc:def:crs:EPSG::2180"
# Coordinates below are invented fixed research windows in Poland's PL-1992.
# GeoJSON response is x=easting, y=northing; request BBOX uses the official
# EPSG:2180 AXIS definition northing,easting (WFS 2.0 CRS axis order).
WARSAW_XY = (636500.0, 486500.0, 637500.0, 487500.0)
MAX_RETURNED = 2
MAX_BYTES = 256 * 1024
TIMEOUT = 15
SCRIPT_ROOT = Path(__file__).resolve().parents[1]


class BuildingWindowError(ValueError):
    """Fail-closed research observation: not an insurance data admission."""


def request_url() -> str:
    xmin, ymin, xmax, ymax = WARSAW_XY
    axis_bbox = f"{ymin:g},{xmin:g},{ymax:g},{xmax:g},EPSG:2180"
    options = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": FEATURE_TYPE,
        "COUNT": str(MAX_RETURNED),
        "SRSNAME": "EPSG:2180",
        "BBOX": axis_bbox,
        "OUTPUTFORMAT": "application/json",
    }
    return PROVIDER + "?" + urllib.parse.urlencode(options)


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BuildingWindowError("duplicate original GeoJSON key")
        result[key] = value
    return result


def _no_constant(_):
    raise BuildingWindowError("non-finite JSON constant")


def _rings(geometry: dict) -> list[list[list]]:
    if not isinstance(geometry, dict):
        raise BuildingWindowError("missing geometry")
    kind = geometry.get("type")
    coords = geometry.get("coordinates")
    if kind == "Polygon" and isinstance(coords, list):
        polygons = [coords]
    elif kind == "MultiPolygon" and isinstance(coords, list):
        polygons = coords
    else:
        raise BuildingWindowError("original geometry not Polygon/MultiPolygon")
    rings = []
    if not polygons or len(polygons) > 20:
        raise BuildingWindowError("invalid polygon/part count")
    for poly in polygons:
        if not isinstance(poly, list) or not 1 <= len(poly) <= 20:
            raise BuildingWindowError("invalid ring count")
        for ring in poly:
            if not isinstance(ring, list) or not 4 <= len(ring) <= 20000:
                raise BuildingWindowError("invalid polygon ring size")
            if ring[0] != ring[-1]:
                raise BuildingWindowError("unclosed original polygon ring")
            rings.append(ring)
    return rings


def _segment_intersects_window(a: list, b: list) -> bool:
    """Liang–Barsky segment/axis-aligned rectangle contact, not bbox only."""
    x0, y0, x1, y1 = WARSAW_XY
    dx, dy = b[0] - a[0], b[1] - a[1]
    lower, upper = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]),
                 (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                lower = max(lower, t)
            else:
                upper = min(upper, t)
            if lower > upper:
                return False
    return True


def _inside_ring(point: tuple[float, float], ring: list[list]) -> bool:
    """Even-odd test; source topology remains unverified independently."""
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]):
        ax, ay = a
        bx, by = b
        if (ay > y) != (by > y) and x < ax + (bx - ax) * (y - ay) / (by - ay):
            inside = not inside
    return inside


def _polygon_intersects_window(geometry: dict) -> bool:
    # Check actual polygon segments / interior, not merely bbox overlap.
    # The first ring is exterior; subsequent rings are holes. If the entire
    # target window lies inside a hole, the building DOES NOT intersect it.
    polygons = ([geometry["coordinates"]] if geometry["type"] == "Polygon"
                else geometry["coordinates"])
    x0, y0, x1, y1 = WARSAW_XY
    corners = ((x0, y0), (x0, y1), (x1, y0), (x1, y1))
    for polygon in polygons:
        if any(_segment_intersects_window(a, b) for ring in polygon
               for a, b in zip(ring, ring[1:])):
            return True
        if any(_inside_ring(corner, polygon[0])
               and not any(_inside_ring(corner, hole) for hole in polygon[1:])
               for corner in corners):
            return True
    return False


def inspect_original_geojson(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise BuildingWindowError("missing or oversized original GeoJSON")
    try:
        src = json.loads(raw, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise BuildingWindowError("invalid original GeoJSON") from exc
    if not isinstance(src, dict) or src.get("type") != "FeatureCollection":
        raise BuildingWindowError("original source not a FeatureCollection")
    if src.get("name") != "budynki":
        raise BuildingWindowError("wrong original layer (buildings required)")
    source_crs = src.get("crs")
    crs_properties = source_crs.get("properties") if isinstance(source_crs, dict) else None
    if (not isinstance(source_crs, dict)
            or source_crs.get("type") != "name"
            or not isinstance(crs_properties, dict)
            or crs_properties.get("name") != CRS):
        raise BuildingWindowError("GeoJSON CRS mismatch; stop axis conversion")
    items = src.get("features")
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_RETURNED:
        raise BuildingWindowError("zero or excessive building features; cannot prove window")
    x0, y0, x1, y1 = WARSAW_XY
    counts = {"ID_BUDYNKU": 0, "RODZAJ": 0,
              "KONDYGNACJE_NADZIEMNE": 0, "KONDYGNACJE_PODZIEMNE": 0}
    geometries = []
    point_count = 0
    for feature in items:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise BuildingWindowError("invalid building feature")
        props = feature.get("properties")
        if not isinstance(props, dict) or not {"ID_BUDYNKU", "RODZAJ"} <= props.keys():
            raise BuildingWindowError("original building ID and type fields missing")
        for key in counts:
            if key in props and props[key] is not None and props[key] != "":
                counts[key] += 1
        rings = _rings(feature.get("geometry"))
        box = [math.inf, math.inf, -math.inf, -math.inf]
        for ring in rings:
            point_count += len(ring)
            if point_count > 30000:
                raise BuildingWindowError("original vertex budget exceeded")
            for pt in ring:
                if (not isinstance(pt, list) or len(pt) != 2
                        or any(type(v) not in (float, int) or not math.isfinite(v)
                               for v in pt)):
                    raise BuildingWindowError("invalid/nonfinite XY coordinate")
                x, y = pt  # Output GeoJSON coordinates are east, north
                box[0] = min(box[0], x)
                box[1] = min(box[1], y)
                box[2] = max(box[2], x)
                box[3] = max(box[3], y)
        if box[2] <= box[0] or box[3] <= box[1]:
            raise BuildingWindowError("degenerate building footprint")
        if (not (box[0] <= x1 and box[2] >= x0 and box[1] <= y1 and box[3] >= y0)
                or not _polygon_intersects_window(feature["geometry"])):
            raise BuildingWindowError("geometry does not intersect declared XY target window")
        geometries.append(feature["geometry"]["type"])
    return {
        "profile": "pl-gugik-egib-warsaw-two-building-axis-window-v0",
        "provider": PROVIDER,
        "original_response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "source_file_sha_independently_pinned": False,
        "feature_type": FEATURE_TYPE,
        "wfs_version": "2.0.0",
        "declared_crs": CRS,
        "request_bbox_order": "northing,easting,northing,easting",
        "geojson_coordinate_order": "easting,northing",
        "verified_intersection_count": len(geometries),
        "geometry_types_seen": sorted(set(geometries)),
        "observed_nonempty_field_counts_sample_only": counts,
        "individual_building_ids_or_geometries_output": False,
        "source_bytes_written_by_script": False,
        "nationwide_geometry_coverage_verified": False,
        "complete_topological_validity_verified": False,
        "licensed_use_of_all_source_attributes_verified": False,
        "actual_insured_property_or_tiv_verified": False,
        "model_input_admitted": False,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BuildingWindowError("unapproved original provider redirect")


def _fetch() -> bytes:
    url = request_url()  # fixed official HTTPS endpoint and exact two-item query
    opener = urllib.request.build_opener(_NoRedirect())
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise BuildingWindowError("original provider unavailable") from exc
    if not 0 < len(raw) <= MAX_BYTES:
        raise BuildingWindowError("original response exceeds byte budget")
    return raw


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true",
                      help="Explicit original provider two-feature request; never writes data")
    mode.add_argument("--source-json", type=Path,
                      help="External pre-obtained original GeoJSON, no automatic network access")
    a = p.parse_args(argv)
    try:
        if a.live:
            raw = _fetch()
        else:
            path = a.source_json
            if path.is_symlink() or not path.is_file():
                raise BuildingWindowError("external original must be a regular non-symlink file")
            if path.resolve().is_relative_to(SCRIPT_ROOT):
                raise BuildingWindowError("original provider assets may not be stored in Git checkout")
            with path.open("rb") as f:
                raw = f.read(MAX_BYTES + 1)
        result = inspect_original_geojson(raw)
    except (OSError, BuildingWindowError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
