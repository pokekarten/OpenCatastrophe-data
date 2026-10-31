#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only geographic point membership in an observed EFFIS burnt polygon.

Output is metadata-only; does not create exposures, monetary losses, or
underwriting information. Refuse boundary ambiguity or unsupported CRS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inspect_effis_burnt_area_v0 import (  # noqa: E402
    MAX_BYTES, _strict_object, inspect_event_json, retrieve_event,
)

MAX_SITES = 256
TOL = 1e-10
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


class OverlayError(ValueError):
    """Spatial overlap cannot be certified at this research stage."""


def _number(value, lo, hi):
    if type(value) not in (float, int) or not math.isfinite(value) or not lo <= value <= hi:
        raise OverlayError("nonfinite, out-of-range or nonnumeric coordinate")
    return float(value)


def _unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise OverlayError("duplicate JSON key")
        obj[k] = v
    return obj


def load_synthetic_sites(raw: bytes) -> tuple:
    if type(raw) is not bytes or not 0 < len(raw) <= 65536:
        raise OverlayError("bounded JSON source required")
    try:
        obj = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(
                             OverlayError("nonfinite JSON literal")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OverlayError("malformed synthetic-site JSON") from exc
    if type(obj) is not dict or set(obj) != {
        "schema_version", "crs", "synthetic_only", "sites"
    } or obj["schema_version"] != "oc-effis-synthetic-sites-v0":
        raise OverlayError("site manifest schema mismatch")
    if obj["crs"] != "OGC:CRS84" or obj["synthetic_only"] is not True:
        raise OverlayError("only explicitly synthetic lon-lat points supported")
    sites = obj["sites"]
    if type(sites) is not list or not 0 < len(sites) <= MAX_SITES:
        raise OverlayError("invalid site count")
    result, used = [], set()
    for item in sites:
        if type(item) is not dict or set(item) != {"site_id", "longitude", "latitude"}:
            raise OverlayError("only point coordinates and synthetic ID allowed")
        ident = item["site_id"]
        if type(ident) is not str or not NAME.fullmatch(ident) or ident in used:
            raise OverlayError("invalid or duplicate synthetic site ID")
        used.add(ident)
        result.append((ident, _number(item["longitude"], -180, 180),
                       _number(item["latitude"], -90, 90)))
    return tuple(sorted(result))


def _on_edge(px, py, ax, ay, bx, by):
    length = math.hypot(bx - ax, by - ay)
    if length <= TOL:
        raise OverlayError("degenerate polygon edge")
    distance = abs((px - ax) * (by - ay) - (py - ay) * (bx - ax)) / length
    return (distance <= TOL and min(ax, bx) - TOL <= px <= max(ax, bx) + TOL
            and min(ay, by) - TOL <= py <= max(ay, by) + TOL)


def _ring(point, ring):
    if type(ring) is not list or len(ring) < 4:
        raise OverlayError("missing polygon ring")
    px, py = point
    inside = False
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]
        if type(a) is not list or type(b) is not list or len(a) != 2 or len(b) != 2:
            raise OverlayError("only 2D GeoJSON positions supported")
        ax, ay = _number(a[0], -180, 180), _number(a[1], -90, 90)
        bx, by = _number(b[0], -180, 180), _number(b[1], -90, 90)
        if abs(bx - ax) > 180:
            raise OverlayError("antimeridian crossing must be split first")
        if _on_edge(px, py, ax, ay, bx, by):
            return "boundary"
        if (ay > py) != (by > py) and ax + (bx - ax) * (py - ay) / (by - ay) > px:
            inside = not inside
    return "inside" if inside else "outside"


def point_in_multipolygon(point, polygons):
    hit = False
    for poly in polygons:
        if type(poly) is not list or not poly:
            raise OverlayError("empty polygon")
        exterior = _ring(point, poly[0])
        if exterior == "boundary":
            return "boundary"
        if exterior != "inside":
            continue
        is_hole = False
        for hole in poly[1:]:
            relation = _ring(point, hole)
            if relation == "boundary":
                return "boundary"
            if relation == "inside":
                is_hole = True
                break
        if not is_hole:
            hit = True
    return "inside" if hit else "outside"


def audit_synthetic_overlay(source_bytes: bytes, event_id: int, sites_bytes: bytes) -> dict:
    receipt = inspect_event_json(source_bytes, event_id)
    if type(source_bytes) is not bytes or len(source_bytes) > MAX_BYTES:
        raise OverlayError("invalid source size")
    payload = json.loads(source_bytes.decode("utf-8-sig"), object_pairs_hook=_unique)
    polygons = payload["results"][0]["shape"]["coordinates"]
    sites = load_synthetic_sites(sites_bytes)
    site_out, count = [], 0
    for ident, lon, lat in sites:
        hit = point_in_multipolygon((lon, lat), polygons)
        if hit == "boundary":
            raise OverlayError("ambiguous spatial boundary at " + ident)
        count += int(hit == "inside")
        site_out.append({"site_id": ident, "within_observed_burnt_polygon": hit == "inside"})
    roster_bytes = json.dumps(sites, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "schema_version": "oc-effis-synthetic-point-overlay-v0",
        "status": "SYNTHETIC_GEOMETRY_ONLY",
        "peril": "WILDFIRE",
        "measure": "BINARY_BURNT_AREA_MEMBERSHIP_NOT_INTENSITY",
        "event_key": "effis:burntarea:" + str(event_id),
        "event_timestamp": receipt["event_firedate"],
        "source_payload_sha256": receipt["source_bytes_sha256"],
        "synthetic_roster_sha256": hashlib.sha256(roster_bytes).hexdigest(),
        "coordinate_system": "OGC:CRS84",
        "provider_source_mutable": True,
        "site_count": len(sites),
        "point_hits": count,
        "site_hits": site_out,
        "site_coordinates_exported": False,
        "provider_geometry_exported": False,
        "real_exposure_used": False,
        "vulnerability_applied": False,
        "gross_loss_calculated": False,
        "insured_loss_calculated": False,
        "model_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", required=True, type=int)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fetch", action="store_true")
    group.add_argument("--source-file", type=Path)
    parser.add_argument("--synthetic-sites", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    source = retrieve_event(args.event_id) if args.fetch else args.source_file.read_bytes()
    sites = args.synthetic_sites.read_bytes()
    result = audit_synthetic_overlay(source, args.event_id, sites)
    data = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.out:
        if args.source_file and args.out.resolve() == args.source_file.resolve():
            raise OverlayError("refusing to overwrite provider data")
        if args.out.resolve() == args.synthetic_sites.resolve():
            raise OverlayError("refusing to overwrite synthetic site input")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
