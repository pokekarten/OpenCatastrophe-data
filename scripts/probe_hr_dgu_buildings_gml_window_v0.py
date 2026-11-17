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
BU_BASE = "{http://inspire.ec.europa.eu/schemas/bu-base/4.0}"
XLINK = "{http://www.w3.org/1999/xlink}"
FOOTPRINT_URI = "http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue/footPrint"
COMBINED_URI = "http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue/combined"
# The final legacy OGC URI was observed as the Polygon's own srsName in
# one bounded Croatian cadastral WFS GML intermediary response on 2026-11-17.
# It is an exact EPSG:3765 syntax, not permission to accept arbitrary URIs.
CRS_ALIASES = {
    "EPSG:3765",
    "urn:ogc:def:crs:EPSG::3765",
    "http://www.opengis.net/def/crs/EPSG/0/3765",
    "http://www.opengis.net/gml/srs/epsg.xml#3765",
}


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


def _cross(a: tuple[float, float], b: tuple[float, float],
           c: tuple[float, float]) -> float:
    return ((b[0] - a[0]) * (c[1] - a[1])
            - (b[1] - a[1]) * (c[0] - a[0]))


def _point_on_segment(p: tuple[float, float],
                      a: tuple[float, float], b: tuple[float, float]) -> bool:
    return (_cross(a, b, p) == 0
            and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def _segments_intersect(a: tuple[float, float], b: tuple[float, float],
                        c: tuple[float, float], d: tuple[float, float]) -> bool:
    """Closed 2D segment intersection, including touches and collinear edges."""
    if (max(a[0], b[0]) < min(c[0], d[0])
            or max(c[0], d[0]) < min(a[0], b[0])
            or max(a[1], b[1]) < min(c[1], d[1])
            or max(c[1], d[1]) < min(a[1], b[1])):
        return False
    ab_c, ab_d = _cross(a, b, c), _cross(a, b, d)
    cd_a, cd_b = _cross(c, d, a), _cross(c, d, b)
    return (
        ((ab_c > 0 > ab_d or ab_c < 0 < ab_d)
         and (cd_a > 0 > cd_b or cd_a < 0 < cd_b))
        or (_point_on_segment(c, a, b) or _point_on_segment(d, a, b)
            or _point_on_segment(a, c, d) or _point_on_segment(b, c, d))
    )


def _signed_twice_area(xy: list[tuple[float, float]]) -> float:
    """Compute projected shoelace area with translated, compensated sums.

    Untranslated EPSG:3765 x*y terms are around 1e12; subtraction can
    cancel small but nondegenerate footprints near the fixed area gate.
    """
    x0, y0 = xy[0]
    return math.fsum(
        (a[0] - x0) * (b[1] - y0) - (b[0] - x0) * (a[1] - y0)
        for a, b in zip(xy, xy[1:])
    )


def _ring_is_simple(xy: list[tuple[float, float]]) -> bool:
    """Reject repeated points and self-crossing edges in a bounded exterior."""
    edges = list(zip(xy, xy[1:]))
    if len(set(xy[:-1])) != len(xy) - 1:
        return False
    if any(a == b for a, b in edges):
        return False
    count = len(edges)
    for i, (a, b) in enumerate(edges):
        for j in range(i + 2, count):
            if i == 0 and j == count - 1:
                continue
            c, d = edges[j]
            if _segments_intersect(a, b, c, d):
                return False
    return True


def _polygon_intersects_window(xy: list[tuple[float, float]],
                               bbox: tuple[int, int, int, int]) -> bool:
    """Check an actual simple polygon/closed rectangle intersection, not its envelope.

    This detects vertices inside the window, crossing/touching boundaries and
    a window fully enclosed by a polygon. It does not establish source rights,
    location accuracy or positive-area overlap for boundary-only contacts.
    """
    bx0, by0, bx1, by1 = bbox
    corners = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
    edges = list(zip(xy, xy[1:]))
    if any(bx0 <= x <= bx1 and by0 <= y <= by1 for x, y in xy):
        return True
    if any(_segments_intersect(a, b, c, d)
           for a, b in edges for c, d in zip(corners, corners[1:] + corners[:1])):
        return True

    def contains(p: tuple[float, float]) -> bool:
        x, y = p
        inside = False
        for a, b in edges:
            if _point_on_segment(p, a, b):
                return True
            if (a[1] > y) != (b[1] > y):
                hit_x = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                if x < hit_x:
                    inside = not inside
        return inside

    return any(contains(corner) for corner in corners)


def inspect_semantic_label(raw: bytes) -> dict:
    """Report one source-labelled INSPIRE reference, without validating a footprint.

    This is a metadata-only *negative-evidence* lane for a provider returning
    'combined'. No original coordinates, feature identifiers, attributes,
    licence clearance or exposure claims may appear in its receipt. It
    deliberately does not replace inspect_gml's strict footPrint gate.
    """
    if not isinstance(raw, bytes) or not (0 < len(raw) <= MAX_BYTES):
        raise BuildingGmlError("XML is missing or exceeds fixed byte budget")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, flags=re.I):
        raise BuildingGmlError("DTD and entity declarations prohibited")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise BuildingGmlError("XML parse error") from exc
    if root.tag != WFS + "FeatureCollection" or root.get("numberReturned") != "1":
        raise BuildingGmlError("expected one WFS 2.0 original feature")
    members = root.findall(WFS + "member")
    if len(members) != 1 or len(members[0]) != 1 or members[0][0].tag != BU + "Building":
        raise BuildingGmlError("expected exactly one INSPIRE Building")
    geometries = members[0][0].findall(BU + "geometry2D")
    if len(geometries) != 1 or len(geometries[0]) != 1:
        raise BuildingGmlError("expected one direct geometry2D")
    profile = geometries[0][0]
    if profile.tag != BU_BASE + "BuildingGeometry2D":
        raise BuildingGmlError("expected bu-base BuildingGeometry2D")
    required = {
        BU_BASE + "geometry", BU_BASE + "referenceGeometry",
        BU_BASE + "horizontalGeometryReference",
    }
    if len(profile) != 3 or {child.tag for child in profile} != required:
        # Source-science troubleshooting only. Emit short *schema tag names*,
        # never XML text, attributes, original identifiers or coordinate values.
        # Keep refusal in place until every extra property is reviewed.
        names = []
        for child in list(profile)[:10]:
            local = child.tag.removeprefix(BU_BASE) if child.tag.startswith(BU_BASE) else ""
            names.append(local if re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,47}", local) else "unreviewed")
        raise BuildingGmlError(
            "unreviewed or duplicated reference geometry properties "
            f"(count={len(profile)}, schema_fields={','.join(names)})"
        )
    refs = profile.findall(BU_BASE + "referenceGeometry")
    if len(refs) != 1 or refs[0].text is None or refs[0].text.strip() != "true":
        raise BuildingGmlError("referenceGeometry must be uniquely true")
    labels = profile.findall(BU_BASE + "horizontalGeometryReference")
    label_uris = {FOOTPRINT_URI: "footPrint", COMBINED_URI: "combined"}
    if len(labels) != 1 or labels[0].get(XLINK + "href") not in label_uris:
        raise BuildingGmlError("unsupported INSPIRE horizontal reference")
    geometry = profile.findall(BU_BASE + "geometry")
    if len(geometry) != 1 or len(geometry[0]) != 1:
        raise BuildingGmlError("missing or ambiguous inline source geometry")
    polygon = geometry[0][0]
    if polygon.tag != GML + "Polygon" or polygon.get("srsName") not in CRS_ALIASES:
        raise BuildingGmlError("unsupported geometry or projected CRS for semantic audit")
    # Deliberately no coordinate inspection and no geometry-validity verdict.
    # Even a claimed footPrint here does not pass the separate strict gate.
    return {
        "receipt_profile": "hr-dgu-gml-reference-semantics-observation-v0",
        "source_id": SOURCE_ID,
        "wfs_type": FEATURE_TYPE,
        "original_xml_bytes": len(raw),
        "original_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "feature_records_checked": 1,
        "polygon_crs_declaration": CRS,
        "inspire_reference_geometry_verified": True,
        "inspire_horizontal_geometry_reference": label_uris[labels[0].get(XLINK + "href")],
        "actual_polygon_geometry_verified": False,
        "ground_footprint_verified": False,
        "reusable_source_rights_fully_reviewed": False,
        "insurer_locations_or_tiv_verified": False,
        "model_input_admitted": False,
    }


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
    # Core 2D uses bu-core2d:geometry2D enclosing the base-model
    # bu-base:BuildingGeometry2D; geometry attributes use bu-base, not
    # the bu-core2d namespace of the feature itself.
    geometries = building.findall(BU + "geometry2D")
    if len(geometries) != 1:
        raise BuildingGmlError("expected one direct core2d geometry2D profile")
    geom = geometries[0]
    if len(geom) != 1 or geom[0].tag != BU_BASE + "BuildingGeometry2D":
        raise BuildingGmlError("missing or ambiguous bu-base BuildingGeometry2D")
    profile = geom[0]
    reference_flags = profile.findall(BU_BASE + "referenceGeometry")
    if (len(reference_flags) != 1
            or reference_flags[0].text is None
            or reference_flags[0].text.strip() != "true"):
        raise BuildingGmlError("INSPIRE referenceGeometry must be uniquely true")
    horizontal_refs = profile.findall(BU_BASE + "horizontalGeometryReference")
    if len(horizontal_refs) != 1 or horizontal_refs[0].get(XLINK + "href") != FOOTPRINT_URI:
        raise BuildingGmlError("only explicitly tagged INSPIRE footPrint geometry is reviewed")
    # Reject any unreviewed direct INSPIRE property after the targeted
    # referenceGeometry/footPrint checks have reported their specific errors.
    # A second coordinate-bearing sibling must never be silently ignored.
    approved_properties = {
        BU_BASE + "geometry",
        BU_BASE + "referenceGeometry",
        BU_BASE + "horizontalGeometryReference",
    }
    if len(profile) != 3 or {child.tag for child in profile} != approved_properties:
        raise BuildingGmlError("unexpected or duplicated BuildingGeometry2D property")
    geometry_props = profile.findall(BU_BASE + "geometry")
    if len(geometry_props) != 1 or len(geometry_props[0]) != 1:
        raise BuildingGmlError("missing or ambiguous inline bu-base geometry")
    polygon = geometry_props[0][0]
    # GML point, surface, MultiSurface, hrefs and nested decoy polygons are
    # deliberately outside this single-footprint Polygon preflight.
    if polygon.tag != GML + "Polygon":
        raise BuildingGmlError("unsupported reference footprint GML geometry type")
    if len(profile.findall(".//" + GML + "Polygon")) != 1:
        raise BuildingGmlError("multiple or nested footprint polygons are unreviewed")
    # The geometry itself must declare the reviewed projected CRS. A child
    # posList/LinearRing carrying EPSG:3765 must not supply a missing
    # polygon-level CRS: otherwise the source coordinate axis semantics are
    # silently inferred from a nested attribute with different GML scope.
    if polygon.get("srsName") not in CRS_ALIASES:
        raise BuildingGmlError("polygon must directly declare reviewed EPSG:3765 CRS")
    crs_values = {
        value for element in polygon.iter()
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
    if polygon.findall(GML + "interior"):
        raise BuildingGmlError("interior rings require a separately reviewed GML profile")
    if len(polygon) != 1 or polygon[0].tag != GML + "exterior":
        raise BuildingGmlError("unexpected GML Polygon child outside reviewed single exterior")
    exteriors = polygon.findall(GML + "exterior")
    if len(exteriors) != 1:
        raise BuildingGmlError("one polygon exterior is required")
    if len(exteriors[0]) != 1 or exteriors[0][0].tag != GML + "LinearRing":
        raise BuildingGmlError("expected exactly one GML LinearRing exterior")
    # This bounded profile supports exactly one posList child, not a
    # schema-invalid mixture of posList, pos or other ring encodings.
    ring = exteriors[0][0]
    if len(ring) != 1 or ring[0].tag != GML + "posList" or not ring[0].text:
        raise BuildingGmlError("missing or ambiguous GML exterior posList")
    if len(ring[0]):
        raise BuildingGmlError("nested coordinate elements in GML posList are unreviewed")
    if any(value and value.strip() for value in (
        polygon.text, exteriors[0].text, exteriors[0].tail,
        ring.text, ring.tail, ring[0].tail,
    )):
        raise BuildingGmlError("mixed coordinate text outside GML posList is unreviewed")
    try:
        vals = [float(n) for n in ring[0].text.split()]
    except ValueError as exc:
        raise BuildingGmlError("non-numeric polygon coordinates") from exc
    if len(vals) < 10 or len(vals) % 2 or len(vals) > 4000 or not all(map(math.isfinite, vals)):
        raise BuildingGmlError("invalid, unbounded or nonfinite 2D polygon ring")
    xy = list(zip(vals[::2], vals[1::2]))
    if xy[0] != xy[-1]:
        raise BuildingGmlError("polygon exterior is not closed")
    if not _ring_is_simple(xy):
        raise BuildingGmlError("repeated vertices, zero edges or self-intersecting exterior")
    # National plausibility range is only a gross axis-swap guard.
    if any(not (200000 < x < 900000 and 4600000 < y < 5300000) for x, y in xy):
        raise BuildingGmlError("CRS axis order or national coordinate range implausible")
    twice_area = _signed_twice_area(xy)
    if not math.isfinite(twice_area) or abs(twice_area) <= 0.001:
        raise BuildingGmlError("degenerate footprint exterior")
    minx, miny, maxx, maxy = (
        min(x for x, _ in xy), min(y for _, y in xy),
        max(x for x, _ in xy), max(y for _, y in xy)
    )
    bx0, by0, bx1, by1 = BBOX
    if maxx < bx0 or minx > bx1 or maxy < by0 or miny > by1:
        raise BuildingGmlError("polygon envelope lies outside requested projected window")
    if not _polygon_intersects_window(xy, BBOX):
        raise BuildingGmlError("polygon itself does not intersect requested projected window")
    # No claims about topology/holes, completeness, insurance or cadastral validity.
    return {
        "receipt_profile": "hr-dgu-cadastral-building-gml-single-polygon-preflight-v0",
        "source_id": SOURCE_ID,
        "wfs_type": FEATURE_TYPE,
        "declared_crs": CRS,
        "original_xml_bytes": len(raw),
        "original_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "feature_records_checked": 1,
        "inspire_reference_geometry_verified": True,
        "inspire_horizontal_geometry_reference": "footPrint",
        "exterior_ring_closed": True,
        "projected_xy_plausible": True,
        "polygon_envelope_overlaps_fixed_window": True,
        "actual_polygon_intersects_fixed_window": True,
        "topology_and_inner_rings_verified": False,
        "nationwide_completeness_verified": False,
        "reusable_source_rights_fully_reviewed": False,
        "insurer_locations_or_tiv_verified": False,
        "model_input_admitted": False,
    }


def validate_content_length(declared: object, actual_bytes: int) -> None:
    """Reject malformed provider lengths before integer conversion."""
    if declared is None:
        return
    if (
        type(declared) is not str
        or len(declared) == 0
        or len(declared) > 10
        or not declared.isascii()
        or not declared.isdecimal()
    ):
        raise BuildingGmlError("invalid original WFS Content-Length")
    length = int(declared)
    if length == 0 or length > MAX_BYTES or length != actual_bytes:
        raise BuildingGmlError("incomplete or invalid declared Content-Length")


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
            validate_content_length(declared, len(data))
    except error.HTTPError as exc:
        # Never echo the upstream error body, URL, arbitrary reason or source
        # attributes. HTTP status is enough to distinguish access policy,
        # invalid request and transient infrastructure failures.
        status = exc.code if type(exc.code) is int and 100 <= exc.code <= 599 else "unknown"
        raise BuildingGmlError(f"original WFS HTTP {status}; no source admission") from exc
    except (error.URLError, TimeoutError) as exc:
        raise BuildingGmlError("original WFS network unavailable; no source admission") from exc
    return data


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="One bounded original WFS GET")
    mode.add_argument("--offline-file", type=Path, help="Inspect one local XML; no network")
    p.add_argument(
        "--audit-semantics", action="store_true",
        help="Metadata-only source-label receipt; does not validate/admit a footprint",
    )
    a = p.parse_args(argv)
    try:
        if a.live:
            raw = live_one_original()
        else:
            if a.offline_file.is_symlink() or not a.offline_file.is_file():
                raise BuildingGmlError("offline XML must be a regular file")
            with a.offline_file.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        result = inspect_semantic_label(raw) if a.audit_semantics else inspect_gml(raw)
        result["live_original_fetch_in_this_run"] = bool(a.live)
    except (BuildingGmlError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
