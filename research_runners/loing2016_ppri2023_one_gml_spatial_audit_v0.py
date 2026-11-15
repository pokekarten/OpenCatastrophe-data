#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline audit of ONE public DDT45 2023 Loing-Aval PPRI WFS GML feature.

Not a 2016 observed inundation layer, independent field holdout or full
PPRI feature collection. Requires separately retrieved local provider GML;
does not perform WFS requests or certify original-file acquisition rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


class GMLReviewBlocked(ValueError):
    """Wrong provider/product edition, malformed or unsafe local GML."""


WFS = "{http://www.opengis.net/wfs/2.0}"
GML = "{http://www.opengis.net/gml/3.2}"
MS = "{http://mapserver.gis.umn.edu/mapserver}"
FEATURE = "N_ZONE_ALEA_PPRN_20220018_S_045"
CRS = "urn:ogc:def:crs:EPSG::2154"
_EXPECTED = {
    "ID_ZONE": "PPR_Loing-Av_F",
    "NIVALEA": "F",  # Preserve source code, do NOT guess its label.
    "NIVALEA_ST": "04",
    "DATECARTE": "2023-janvier",
    "SRCE_ANNEE": "",
    "SRCE_GEOM": "",
}
# Coordinates: original public 2016 Repères de crues pages, Lambert-93.
_SITES = (
    ("CER_LO_16_S_174", 679817.12, 6766779.20, "physical_flood_trace"),
    ("CER_LO_16_S_175", 680192.03, 6766742.32, "oral_testimony"),
)


def _ring_points(node):
    pos = node.find(f"./{GML}LinearRing/{GML}posList")
    if pos is None or not pos.text:
        raise GMLReviewBlocked("polygon ring missing 2D GML posList")
    dim = pos.get("srsDimension")
    if dim not in (None, "2"):
        raise GMLReviewBlocked("3D/other position dimension not reviewed")
    tokens = pos.text.split()
    if not (8 <= len(tokens) <= 1_000_000 and len(tokens) % 2 == 0):
        raise GMLReviewBlocked("invalid ring length or coordinate cardinality")
    try:
        coords = [(float(tokens[i]), float(tokens[i + 1]))
                  for i in range(0, len(tokens), 2)]
    except ValueError as exc:
        raise GMLReviewBlocked("invalid position token") from exc
    if any(not math.isfinite(x) or not math.isfinite(y) or
           not 0 <= x <= 1_500_000 or not 6_000_000 <= y <= 8_000_000
           for x, y in coords):
        raise GMLReviewBlocked("invalid finite Lambert-93 position")
    if coords[0] != coords[-1]:
        raise GMLReviewBlocked("polygon exterior/interior ring not closed")
    return coords


def _locate_in_ring(point, ring):
    """Return outside, inside or ambiguous boundary without snapping."""
    px, py = point
    inside = False
    prev_x, prev_y = ring[-1]
    for x, y in ring:
        dx, dy = x - prev_x, y - prev_y
        # Explicitly refuse to classify a site exactly on an edge.
        cross = (px - prev_x) * dy - (py - prev_y) * dx
        if (abs(cross) <= 1e-8 * max(1.0, abs(dx) + abs(dy))
                and min(prev_x, x) - 1e-8 <= px <= max(prev_x, x) + 1e-8
                and min(prev_y, y) - 1e-8 <= py <= max(prev_y, y) + 1e-8):
            return "boundary"
        if (y > py) != (prev_y > py):
            edge_x = x + (prev_x - x) * (py - y) / (prev_y - y)
            if px < edge_x:
                inside = not inside
        prev_x, prev_y = x, y
    return "inside" if inside else "outside"


def audit_one_gml(raw: bytes):
    if not isinstance(raw, bytes) or not 100 <= len(raw) <= 8_388_608:
        raise GMLReviewBlocked("bounded source GML bytes required")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise GMLReviewBlocked("DTD/entity declarations forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise GMLReviewBlocked("invalid well-formed XML") from exc
    if root.tag != WFS + "FeatureCollection" or root.get("numberReturned") != "1":
        raise GMLReviewBlocked("requires one original WFS 2.0 feature")
    members = root.findall(WFS + "member")
    if len(members) != 1:
        raise GMLReviewBlocked("WFS contains unexpected feature count")
    feature = members[0].find(MS + FEATURE)
    if feature is None:
        raise GMLReviewBlocked("not reviewed Loing-Aval 2023 layer")
    for name, expected in _EXPECTED.items():
        fld = feature.find(MS + name)
        if fld is None or (fld.text or "").strip() != expected:
            raise GMLReviewBlocked(f"source {name} differs from reviewed GML")
    envelope = root.find("./" + WFS + "boundedBy/" + GML + "Envelope")
    if envelope is None or envelope.get("srsName") != CRS:
        raise GMLReviewBlocked("publisher projected CRS not established")
    geom = feature.find(MS + "geometry")
    if geom is None:
        raise GMLReviewBlocked("no original geometry element")
    if geom.find(GML + "MultiSurface") is None:
        raise GMLReviewBlocked("not the reviewed projected multisurface GML geometry")
    polygons = geom.findall(".//" + GML + "Polygon")
    if not 1 <= len(polygons) <= 5000:
        raise GMLReviewBlocked("invalid bounded polygon count")
    counts = {site[0]: {"inside": 0, "on_boundary": 0} for site in _SITES}
    holes_count = 0
    for poly in polygons:
        exterior = poly.find(GML + "exterior")
        if exterior is None:
            raise GMLReviewBlocked("missing polygon exterior")
        outer = _ring_points(exterior)
        inners = poly.findall(GML + "interior")
        holes_count += len(inners)
        if holes_count > 10000:
            raise GMLReviewBlocked("too many polygon interior rings")
        # Validate the full source geometry: malformed holes are rejected even
        # when no fixed historical test mark lies inside the polygon.
        holes = [_ring_points(inner) for inner in inners]
        for site_id, x, y, _kind in _SITES:
            relation = _locate_in_ring((x, y), outer)
            if relation == "outside":
                continue
            if relation == "boundary":
                counts[site_id]["on_boundary"] += 1
                continue
            for inner in holes:
                hole_relation = _locate_in_ring((x, y), inner)
                if hole_relation != "outside":
                    relation = "outside" if hole_relation == "inside" else "boundary"
                    break
            if relation == "inside":
                counts[site_id]["inside"] += 1
            elif relation == "boundary":
                counts[site_id]["on_boundary"] += 1
    return {
        "profile": "oc-loing-aval-2023-one-wfs-feature-original-gml-v0",
        "source_kind": "2023_PPRI_HAZARD_ZONING_NOT_OBSERVED_2016_EVENT",
        "catalogue_dataset_id": "67377bf18609c51859c40b3b",
        "catalogue_license_published": "lov2",
        "gml_sha256_of_local_bytes": hashlib.sha256(raw).hexdigest(),
        "gml_local_byte_count": len(raw),
        "provider_original_http_byte_identity_independently_attested": False,
        "source_crs": CRS,
        "source_feature_id": feature.get(GML + "id"),
        "gml_schema_validated": False,
        "niva_source_code": "F",
        "source_map_month": "2023-janvier",
        "source_event_year_present": False,
        "wfs_number_returned": 1,
        "this_is_the_complete_ppri_layer": False,
        "polygons_in_one_feature": len(polygons),
        "interior_rings_in_one_feature": holes_count,
        "point_in_polygon_2016_mark_checks": [
            {
                "official_site_id": site_id, "evidence_kind": kind,
                "inside_this_2023_feature": counts[site_id]["inside"],
                "boundary_ambiguous": counts[site_id]["on_boundary"],
                "independent_2016_flood_observation": False,
            }
            for site_id, _x, _y, kind in _SITES
        ],
        "historical_2016_flood_geometry_independently_validated": False,
        "original_2016_zip_zich_acquired": False,
        "2016_event_source_to_calibration_marks_lineage_known": False,
        "building_depth_or_insured_loss_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gml-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if not args.gml_file.is_file() or args.gml_file.stat().st_size > 8_388_608:
            raise GMLReviewBlocked("missing/oversized local GML")
        result = audit_one_gml(args.gml_file.read_bytes())
    except (OSError, GMLReviewBlocked) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
