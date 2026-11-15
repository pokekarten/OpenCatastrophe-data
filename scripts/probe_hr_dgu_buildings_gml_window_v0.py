#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed GML polygon preflight for one original Croatian cadastral building.

This is a *bounded source-science challenge*, not an exposure/admission tool.
Only --live makes one request to the fixed official WFS endpoint. --offline-file
accepts caller-supplied original XML or a synthetic test sample. Receipts never
print source feature IDs, geometry coordinates, addresses, or owner attributes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib import error, parse, request
import xml.etree.ElementTree as ET

PROVIDER = "https://api.uredjenazemlja.hr/services/inspire/bu/wfs"
SOURCE_ID = "hr.dgu.inspire-buildings-wfs-atom.2026"
FEATURE_TYPE = "bu:Building"
CRS = "EPSG:3765"
BBOX = (459000, 5074500, 459600, 5075100)
MAX_BYTES = 512 * 1024
TIMEOUT_SECONDS = 15
WFS = "{http://www.opengis.net/wfs/2.0}"
GML = "{http://www.opengis.net/gml/3.2}"
BU = "{http://inspire.ec.europa.eu/schemas/bu-core2d/4.0}"
CRS_ALIASES = {"EPSG:3765", "urn:ogc:def:crs:EPSG::3765", "http://www.opengis.net/def/crs/EPSG/0/3765"}


class BuildingGmlError(ValueError):
    """Fail closed on any ambiguous provider geometry or response."""


def fixed_url() -> str:
    params = {
        "SERVICE": "WFS", "REQUEST": "GetFeature", "VERSION": "2.0.0",
        "TYPENAMES": FEATURE_TYPE, "COUNT": "1", "STARTINDEX": "0",
        "SRSNAME": CRS,
        "BBOX": ",".join(str(n) for n in BBOX) + "," + CRS,
    }
    return PROVIDER + "?" + parse.urlencode(params)


def inspect_gml(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not (0 < len(raw) <= MAX_BYTES):
        raise BuildingGmlError("XML is missing or exceeds fixed byte budget")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, flags=re.I):
        raise BuildingGmlError("DTD and entity declarations prohibited")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise BuildingGmlError("XML parse error") from exc
    if root.tag != WFS + "FeatureCollection" or root.get("numberReturned") != "1":
        raise BuildingGmlError("expected exactly one WFS 2.0 feature, not an exception/empty result")
    members = root.findall(WFS + "member")
    if len(members) != 1 or len(members[0]) != 1:
        raise BuildingGmlError("expected one and only one WFS member")
    building = members[0][0]
    if building.tag != BU + "Building":
        raise BuildingGmlError("WFS member is not the original cadastral BU Building")
    geometries = building.findall(".//" + BU + "geometry2D")
    if len(geometries) != 1:
        raise BuildingGmlError("building has missing or ambiguous geometry2D")
    geom = geometries[0]
    polygons = geom.findall(".//" + GML + "Polygon")
    # Explicitly do not certify multi-polygon, gml:Surface patch or geometry href.
    if len(polygons) != 1 or len(geom.findall(".//" + GML + "Surface")):
        raise BuildingGmlError("unsupported or absent single GML Polygon")
    crs_values = {
        value for element in geom.iter()
        for key, value in element.attrib.items() if key == "srsName"
    }
    if not crs_values or not crs_values.issubset(CRS_ALIASES):
        raise BuildingGmlError("missing, inconsistent or unexpected inline EPSG:3765 CRS")
    dims = {
        value for element in geom.iter()
        for key, value in element.attrib.items() if key in {"srsDimension", "dimension"}
    }
    if dims and dims != {"2"}:
        raise BuildingGmlError("GML geometry must have two coordinate dimensions")
    exteriors = polygons[0].findall(GML + "exterior")
    if len(exteriors) != 1:
        raise BuildingGmlError("one polygon exterior is required")
    lists = exteriors[0].findall(".//" + GML + "posList")
    if len(lists) != 1 or not lists[0].text:
        raise BuildingGmlError("missing or ambiguous GML exterior posList")
    try:
        vals = [float(n) for n in lists[0].text.split()]
    except ValueError as exc:
        raise BuildingGmlError("non-numeric polygon coordinates") from exc
    if len(vals) < 10 or len(vals) % 2 or len(vals) > 4000 or not all(map(math.isfinite, vals)):
        raise BuildingGmlError("invalid, unbounded or nonfinite 2D polygon ring")
    xy = list(zip(vals[::2], vals[1::2]))
    if xy[0] != xy[-1]:
        raise BuildingGmlError("polygon exterior is not closed")
    # National plausibility range is only a gross axis-swap guard.
    if any(not (200000 < x < 900000 and 4600000 < y < 5300000) for x, y in xy):
        raise BuildingGmlError("CRS axis order or national coordinate range implausible")
    twice_area = sum(
        a[0] * b[1] - b[0] * a[1] for a, b in zip(xy, xy[1:])
    )
    if not math.isfinite(twice_area) or abs(twice_area) <= 0.001:
        raise BuildingGmlError("degenerate footprint exterior")
    minx, miny, maxx, maxy = (
        min(x for x, _ in xy), min(y for _, y in xy),
        max(x for x, _ in xy), max(y for _, y in xy)
    )
    bx0, by0, bx1, by1 = BBOX
    if maxx < bx0 or minx > bx1 or maxy < by0 or miny > by1:
        raise BuildingGmlError("polygon envelope lies outside requested projected window")
    # No claims about topology/holes, completeness, insurance or cadastral validity.
    return {
        "receipt_profile": "hr-dgu-cadastral-building-gml-single-polygon-preflight-v0",
        "source_id": SOURCE_ID,
        "wfs_type": FEATURE_TYPE,
        "declared_crs": CRS,
        "original_xml_bytes": len(raw),
        "original_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "feature_records_checked": 1,
        "exterior_ring_closed": True,
        "projected_xy_plausible": True,
        "polygon_envelope_overlaps_fixed_window": True,
        "topology_and_inner_rings_verified": False,
        "nationwide_completeness_verified": False,
        "reusable_source_rights_fully_reviewed": False,
        "insurer_locations_or_tiv_verified": False,
        "model_input_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BuildingGmlError("redirect rejected for pinned WFS query")


def live_one_original() -> bytes:
    url = fixed_url()
    opener = request.build_opener(NoRedirect())
    req = request.Request(url, headers={"Accept": "application/gml+xml, application/xml"}, method="GET")
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != url:
                raise BuildingGmlError("provider response URL/status differs from pinned request")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise BuildingGmlError("compressed transfer encoding not part of this byte profile")
            data = response.read(MAX_BYTES + 1)
            declared = response.headers.get("Content-Length")
            if declared is not None and (not declared.isdecimal() or int(declared) != len(data)):
                raise BuildingGmlError("incomplete or invalid declared Content-Length")
    except (error.URLError, TimeoutError) as exc:
        raise BuildingGmlError("original WFS unavailable; no source admission") from exc
    return data


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="One bounded original WFS GET")
    mode.add_argument("--offline-file", type=Path, help="Inspect one local XML; no network")
    a = p.parse_args(argv)
    try:
        if a.live:
            raw = live_one_original()
        else:
            if a.offline_file.is_symlink() or not a.offline_file.is_file():
                raise BuildingGmlError("offline XML must be a regular file")
            with a.offline_file.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        result = inspect_gml(raw)
        result["live_original_fetch_in_this_run"] = bool(a.live)
    except (BuildingGmlError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
