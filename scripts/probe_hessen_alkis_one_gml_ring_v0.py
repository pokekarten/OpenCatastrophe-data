#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Review 2D GML rings of ONE source ALKIS Building, without any geometry output.

Reuses exactly the reviewed WFS GetFeature COUNT=1 Hosenfeld URL and keeps
its known numberReturned=0 vs one Building XML-member contradiction blocked.
Only finite counts/boolean preflight quality flags and SHA hashes leave process.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib import error, request
from xml.etree import ElementTree as ET

from scripts import probe_hessen_alkis_one_wfs_building_v0 as wfs

SOURCE = wfs.SOURCE
URL = wfs.URL
MAX_BYTES = wfs.MAX_BYTES
TIMEOUT_SECONDS = wfs.TIMEOUT_SECONDS
GML_NS = wfs.GML_NS
WFS_NS = wfs.WFS_NS
MAX_SURFACES = 12
MAX_RINGS = 32
MAX_POINTS_PER_RING = 512
MAX_POINTS_TOTAL = 2048
# Verified WorldCover 2021 v200 N48E009 original TIFF block row/col (5,5).
BLOCK_WEST = 9 + 5 * 1024 / 12000
BLOCK_EAST = 9 + 6 * 1024 / 12000
BLOCK_NORTH = 51 - 5 * 1024 / 12000
BLOCK_SOUTH = 51 - 6 * 1024 / 12000


class RingBlocked(ValueError):
    """Original GML ring or source boundary failed a fail-closed preflight."""


def _ring_positions(ring: ET.Element) -> list[tuple[float, float]]:
    """Parse GML 3.2 posList or multiple pos: EPSG:4258 = lat, then lon."""
    dim = ring.get("srsDimension")
    lists = ring.findall(f"{{{GML_NS}}}posList")
    individual = ring.findall(f"{{{GML_NS}}}pos")
    if len(lists) == 1 and not individual:
        child = lists[0]
        dim = child.get("srsDimension", dim)
        parts = (child.text or "").split()
    elif not lists and individual:
        dims = {child.get("srsDimension", dim) for child in individual}
        if len(dims) != 1:
            raise RingBlocked("mixed coordinate dimensions within GML ring")
        dim = next(iter(dims))
        parts = [part for child in individual for part in (child.text or "").split()]
    else:
        raise RingBlocked("unsupported or ambiguous GML ring position encoding")
    if dim not in (None, "2"):
        raise RingBlocked("GML ring is not explicitly supported two-dimensional EPSG:4258")
    if len(parts) < 8 or len(parts) % 2 or len(parts) > MAX_POINTS_PER_RING*2:
        raise RingBlocked("invalid or unbounded WFS GML 2D coordinate count")
    points = []
    for i in range(0, len(parts), 2):
        try:
            lat, lon = float(parts[i]), float(parts[i+1])
        except ValueError as exc:
            raise RingBlocked("invalid GML numeric coordinate token") from exc
        if (not math.isfinite(lat) or not math.isfinite(lon)
                or not 49 <= lat <= 52 or not 7 <= lon <= 11):
            raise RingBlocked("nonfinite or geographically implausible ETRS89 coordinate")
        points.append((lon, lat))
    if len(points) < 4 or points[0] != points[-1]:
        raise RingBlocked("GML coordinate ring is not explicitly closed")
    if len(set(points[:-1])) != len(points) - 1:
        raise RingBlocked("GML ring repeats an internal position")
    twice_area = sum(
        x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points, points[1:])
    )
    if abs(twice_area) < 1e-13:
        raise RingBlocked("degenerate GML ring with zero geographic area")
    return points


def _orientation(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _self_crossing(points: list[tuple[float,float]]) -> bool:
    """Bounded planar ring preflight; not a full DE-9IM topology proof."""
    n = len(points)-1
    for i in range(n):
        a,b=points[i],points[i+1]
        if a == b:
            return True
        for j in range(i+2,n):
            if i == 0 and j == n-1:
                continue
            c,d=points[j],points[j+1]
            x,y=_orientation(a,b,c),_orientation(a,b,d)
            u,v=_orientation(c,d,a),_orientation(c,d,b)
            if x*y < -1e-20 and u*v < -1e-20:
                return True
    return False


def inspect_gml_preflight(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise RingBlocked("unreviewed original source feature bytes")
    try:
        source=wfs.inspect_feature_xml(raw, diagnostic_only=True)
    except wfs.BuildingFeatureBlocked as exc:
        raise RingBlocked("original source failed previous exact one-Building gate") from exc
    if source["original_feature_members_parsed_not_admitted"] != 1:
        raise RingBlocked("original WFS one-feature sample did not contain one Building")
    if source["geometry_crs_declared_and_matches_requested"] is not True:
        raise RingBlocked("original Building geometry lacks reviewed EPSG:4258 declaration")

    root = ET.fromstring(raw)
    members = root.findall(f"{{{WFS_NS}}}member")
    building = members[0][0]
    surfaces = [
        e for e in building.iter()
        if e.tag in (f"{{{GML_NS}}}Polygon", f"{{{GML_NS}}}PolygonPatch")
    ]
    if len(surfaces) > MAX_SURFACES:
        raise RingBlocked("unbounded GML polygon surfaces")
    if not surfaces:
        return {
            "diagnostic_status": "BLOCKED_UNSUPPORTED_NO_GML_POLYGON_SURFACE",
            "polygon_surface_count": 0,
            "gml_ring_count": 0,
            "gml_position_count": 0,
            "source_reported_number_returned": source["reported_number_returned_if_integer"],
            "parsed_original_building_members": 1,
            "provider_count_discrepancy_remains_blocked": not source["reported_member_count_consistent"],
            "all_rings_closed_nondegenerate_and_non_crossing": False,
            "all_coordinates_within_worldcover_original_block_extent": False,
            "etrs89_to_worldcover_wgs84_transform_verified": False,
            "physical_building_polygon_topology_verified": False,
            "actual_building_worldcover_overlap_verified": False,
            "model_input_approved": False,
        }

    all_points = []
    exteriors = 0
    interiors = 0
    locally_simple = True
    for surface in surfaces:
        exterior = surface.findall(f"{{{GML_NS}}}exterior/{{{GML_NS}}}LinearRing")
        holes = surface.findall(f"{{{GML_NS}}}interior/{{{GML_NS}}}LinearRing")
        if len(exterior) != 1:
            raise RingBlocked("GML polygon requires one supported exterior LinearRing")
        exteriors += 1
        interiors += len(holes)
        if exteriors + interiors > MAX_RINGS:
            raise RingBlocked("unbounded GML ring count")
        for ring in exterior + holes:
            points = _ring_positions(ring)
            if _self_crossing(points):
                locally_simple = False
            all_points.extend(points)
            if len(all_points) > MAX_POINTS_TOTAL:
                raise RingBlocked("GML ring source coordinate budget exceeded")
    in_block = all(
        BLOCK_WEST <= lon < BLOCK_EAST and BLOCK_SOUTH < lat <= BLOCK_NORTH
        for lon,lat in all_points
    )
    return {
        "diagnostic_status": (
            "GML_RING_PREFLIGHT_PASSED_SOURCE_COUNT_STILL_BLOCKED"
            if locally_simple and in_block else
            "BLOCKED_GML_RING_CROSSING_OR_BLOCK_EXTENT"
        ),
        "polygon_surface_count": len(surfaces),
        "exterior_ring_count": exteriors,
        "interior_ring_count": interiors,
        "gml_ring_count": exteriors + interiors,
        "gml_position_count": len(all_points),
        "source_reported_number_returned": source["reported_number_returned_if_integer"],
        "parsed_original_building_members": 1,
        "provider_count_discrepancy_remains_blocked": not source["reported_member_count_consistent"],
        "all_rings_closed_nondegenerate_and_non_crossing": locally_simple,
        "all_coordinates_within_worldcover_original_block_extent": in_block,
        "etrs89_to_worldcover_wgs84_transform_verified": False,
        "physical_building_polygon_topology_verified": False,
        "actual_building_worldcover_overlap_verified": False,
        "model_input_approved": False,
    }


def probe(*, open_request=wfs._open):
    # Deliberately the *same exact* URL as the previously reviewed WFS
    # one-feature probe: no additional host, bbox or feature selector.
    wfs.validate_frozen_getfeature()
    req = request.Request(
        URL, method="GET",
        headers={
            "Accept": "application/gml+xml,application/xml,text/xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Hessen-ALKIS-1Ring-Preflight/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != URL:
                raise RingBlocked("original WFS GML source status/URL mismatch")
            mime = response.headers.get("Content-Type", "").split(";",1)[0].strip().lower()
            if mime not in (
                "application/xml","text/xml","application/gml+xml",
                "application/vnd.ogc.gml","application/vnd.ogc.wfs_xml",
            ):
                raise RingBlocked("original WFS GML MIME not reviewed")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise RingBlocked("unexpected original WFS transfer coding")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
                raise RingBlocked("original WFS GML declared body too long")
            raw = response.read(MAX_BYTES+1)
    except (RingBlocked, wfs.CapabilityBlocked):
        raise
    except (error.HTTPError,error.URLError,TimeoutError,OSError) as exc:
        raise RingBlocked("official WFS one-geometry original request unavailable") from exc
    facts = inspect_gml_preflight(raw)
    return {
        "profile": "oc-hessen-alkis-one-gml-ring-geometry-preflight-v0",
        "source_id": SOURCE,
        "exact_source_operation": "original_WFS_GetFeature_COUNT1_bounded_GML_ring_diagnostic",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source_response_bytes": len(raw),
        "source_response_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_request_sha256": hashlib.sha256(("GET "+URL).encode("ascii")).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_coordinates_feature_ids_attributes_persisted": False,
        "original_coordinates_feature_ids_attributes_printed": False,
        **facts,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live",action="store_true")
    args=ap.parse_args(argv)
    if not args.live:
        ap.error("explicit --live required for one source GML diagnostic")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (RingBlocked,wfs.CapabilityBlocked,ValueError,OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "model_input_approved":False}),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
