# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded XML structure preflight for one lawfully supplied PLATEAU building GML.

Never acquires provider bytes, extracts an archive, resolves external entities,
publishes building IDs, estimates exposure, validates topology or admits a model.
A parsed file is NOT evidence of a particular city/year or an original ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if __package__:
    from .plateau_citygml_catalogue_preflight_v0 import (
        CataloguePreflightError,
        read_local_metadata,
    )
else:
    from plateau_citygml_catalogue_preflight_v0 import (
        CataloguePreflightError,
        read_local_metadata,
    )

MAX_GML_BYTES = 4 * 1024 * 1024
MAX_XML_ELEMENTS = 50_000
MAX_XML_DEPTH = 64
MAX_BUILDINGS = 5_000
MAX_LOD0_POLYGONS = 400
MAX_RING_POSITIONS = 128
GML = "http://www.opengis.net/gml"
CORE = "http://www.opengis.net/citygml/2.0"
BLDG = "http://www.opengis.net/citygml/building/2.0"
EPSG6697 = "http://www.opengis.net/def/crs/EPSG/0/6697"
LODS = {
    0: {"lod0FootPrint", "lod0RoofEdge"},
    1: {"lod1Solid", "lod1MultiSurface"},
    2: {"lod2Solid", "lod2MultiSurface"},
    3: {"lod3Solid", "lod3MultiSurface"},
}
ID_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]{0,159}\Z")


def _tag(uri: str, local: str) -> str:
    return f"{{{uri}}}{local}"


class CityGMLPreflightError(ValueError):
    """A candidate local GML sample failed a bounded, non-admission check."""


def _finite_number(token: str) -> float:
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", token):
        raise CityGMLPreflightError("GML coordinate or height has invalid numeric syntax")
    value = float(token)
    if not math.isfinite(value):
        raise CityGMLPreflightError("GML coordinate or height must be finite")
    return value


def _corner(node: ET.Element | None) -> tuple[float, float, float]:
    if node is None or not node.text:
        raise CityGMLPreflightError("GML bounding envelope corner is absent")
    parts = node.text.split()
    if len(parts) != 3:
        raise CityGMLPreflightError("EPSG:6697 envelope corners must be triples")
    lat, lon, alt = (_finite_number(v) for v in parts)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and -10000 <= alt <= 10000):
        raise CityGMLPreflightError("GML bounding envelope corner is out of plausible range")
    return lat, lon, alt



def _segments_intersect(a, b, c, d) -> bool:
    """Conservative planar crossing test on small unprojected lon/lat rings.

    This only rejects an obvious local self-crossing, not a full topology check.
    """
    def orientation(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    ab_c = orientation(a, b, c)
    ab_d = orientation(a, b, d)
    cd_a = orientation(c, d, a)
    cd_b = orientation(c, d, b)
    # Collinear/touching non-adjacent segments are conservatively unresolved.
    if abs(ab_c) < 1e-20 or abs(ab_d) < 1e-20 or abs(cd_a) < 1e-20 or abs(cd_b) < 1e-20:
        def within(p, q, r):
            return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])
        return (
            abs(ab_c) < 1e-20 and within(a, b, c)
            or abs(ab_d) < 1e-20 and within(a, b, d)
            or abs(cd_a) < 1e-20 and within(c, d, a)
            or abs(cd_b) < 1e-20 and within(c, d, b)
        )
    return (ab_c > 0) != (ab_d > 0) and (cd_a > 0) != (cd_b > 0)


def _screen_lod0_polygon(polygon: ET.Element, low: tuple, high: tuple) -> bool:
    """Screen one *inline* GML exterior posList; never calculate exposure area.

    Returns False for polygons using unsupported references/interior rings.
    Invalid inline exterior rings fail closed; unresolved geometry is not passed.
    """
    xlink = "{http://www.w3.org/1999/xlink}href"
    if any(xlink in node.attrib for node in polygon.iter()):
        return False
    if polygon.find(_tag(GML, "interior")) is not None:
        return False
    exteriors = polygon.findall(_tag(GML, "exterior"))
    if len(exteriors) != 1:
        raise CityGMLPreflightError("LOD0 polygon requires exactly one inline exterior")
    rings = exteriors[0].findall(_tag(GML, "LinearRing"))
    if len(rings) != 1:
        return False  # gml:Ring or other supported CityGML form: not checked
    poslists = rings[0].findall(_tag(GML, "posList"))
    if len(poslists) != 1 or not poslists[0].text:
        return False  # gml:pos encoding or referenced coordinates: unsupported
    tokens = poslists[0].text.split()
    if len(tokens) % 3 or not 12 <= len(tokens) <= (MAX_RING_POSITIONS + 1) * 3:
        raise CityGMLPreflightError("LOD0 3D exterior ring has invalid vertex budget/dimension")
    positions = [
        tuple(_finite_number(value) for value in tokens[i:i + 3])
        for i in range(0, len(tokens), 3)
    ]
    if positions[0] != positions[-1]:
        raise CityGMLPreflightError("LOD0 exterior ring is not closed in 3D")
    if len(set(positions[:-1])) < 3:
        raise CityGMLPreflightError("LOD0 exterior ring has fewer than three distinct positions")
    for lat, lon, alt in positions:
        if (
            not low[0] - 1e-8 <= lat <= high[0] + 1e-8
            or not low[1] - 1e-8 <= lon <= high[1] + 1e-8
            or not low[2] - 0.01 <= alt <= high[2] + 0.01
        ):
            raise CityGMLPreflightError("LOD0 position falls outside the root GML envelope")
    # Use horizontal lon/lat solely for nondegeneracy and crossing screening.
    ring = [(lon, lat) for lat, lon, _ in positions]
    if len(set(ring[:-1])) != len(ring) - 1:
        raise CityGMLPreflightError("LOD0 ring repeats a non-terminal horizontal vertex")
    # Translate before the shoelace calculation to avoid cancellation when
    # longitude/latitude are ~100/35 degrees but a building is metres wide.
    origin_x, origin_y = ring[0]
    signed_double_area = math.fsum(
        (ring[i][0] - origin_x) * (ring[i + 1][1] - origin_y)
        - (ring[i + 1][0] - origin_x) * (ring[i][1] - origin_y)
        for i in range(len(ring) - 1)
    )
    if abs(signed_double_area) <= 1e-14:
        raise CityGMLPreflightError("LOD0 ring is horizontally degenerate")
    n = len(ring) - 1
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if _segments_intersect(ring[i], ring[i + 1], ring[j], ring[j + 1]):
                raise CityGMLPreflightError("LOD0 ring has a non-adjacent edge crossing")
    return True


def _screen_lod0(buildings: list[ET.Element], low: tuple, high: tuple) -> dict[str, int]:
    """Count only explicit inline rings in LOD0 footprint/roof-edge properties."""
    screened = {"lod0_footprint_inline_ring_screened_count": 0,
                "lod0_roofedge_inline_ring_screened_count": 0,
                "lod0_geometry_unresolved_property_count": 0}
    polygon_count = 0
    for building in buildings:
        for prop, key in (
            ("lod0FootPrint", "lod0_footprint_inline_ring_screened_count"),
            ("lod0RoofEdge", "lod0_roofedge_inline_ring_screened_count"),
        ):
            for geom in building.findall(_tag(BLDG, prop)):
                polygons = list(geom.iter(_tag(GML, "Polygon")))
                if not polygons or any(
                    "{http://www.w3.org/1999/xlink}href" in n.attrib
                    for n in geom.iter()
                ):
                    screened["lod0_geometry_unresolved_property_count"] += 1
                    continue
                polygon_count += len(polygons)
                if polygon_count > MAX_LOD0_POLYGONS:
                    raise CityGMLPreflightError("LOD0 polygon budget exceeded")
                for polygon in polygons:
                    if _screen_lod0_polygon(polygon, low, high):
                        screened[key] += 1
                    else:
                        screened["lod0_geometry_unresolved_property_count"] += 1
    return screened


def inspect_gml_bytes(raw: bytes) -> dict[str, object]:
    """Inspect a single small CityGML sample with no external resources or output IDs."""
    if not 0 < len(raw) <= MAX_GML_BYTES:
        raise CityGMLPreflightError("GML input is empty or exceeds 4 MiB")
    # stdlib ET does not fetch network entities, but reject all DTD/ENTITY
    # constructs rather than accepting internal expansions or parser drift.
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise CityGMLPreflightError("DTD and entity declarations are not permitted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CityGMLPreflightError("invalid or incomplete CityGML XML") from exc
    if root.tag != _tag(CORE, "CityModel"):
        raise CityGMLPreflightError("CityGML root is not core:CityModel version 2.0")

    # Strictly bound XML nesting and element count even after bounded parsing.
    node_count = 0
    known_ids: set[str] = set()
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > MAX_XML_ELEMENTS or depth > MAX_XML_DEPTH:
            raise CityGMLPreflightError("GML XML element count or depth exceeded")
        sr = node.get("srsName")
        if sr is not None and sr != EPSG6697:
            raise CityGMLPreflightError("GML contains a different or unresolved coordinate reference")
        dimension = node.get("srsDimension")
        if dimension is not None and dimension != "3":
            raise CityGMLPreflightError("GML contains a different coordinate dimension")
        id_value = node.get(_tag(GML, "id"))
        if id_value is not None:
            if not ID_PATTERN.fullmatch(id_value) or id_value in known_ids:
                raise CityGMLPreflightError("GML object IDs are malformed or duplicated")
            known_ids.add(id_value)
        stack.extend((child, depth + 1) for child in node)

    bounds = root.findall(f"./{_tag(GML, 'boundedBy')}/{_tag(GML, 'Envelope')}")
    if len(bounds) != 1:
        raise CityGMLPreflightError("GML must contain exactly one root CRS envelope")
    envelope = bounds[0]
    lower_node = envelope.find(_tag(GML, "lowerCorner"))
    upper_node = envelope.find(_tag(GML, "upperCorner"))
    dimension_on_envelope = envelope.get("srsDimension") == "3"
    dimension_on_both_corners = (
        lower_node is not None and upper_node is not None
        and lower_node.get("srsDimension") == "3"
        and upper_node.get("srsDimension") == "3"
    )
    if envelope.get("srsName") != EPSG6697 or not (
        dimension_on_envelope or dimension_on_both_corners
    ):
        raise CityGMLPreflightError("GML envelope must explicitly use EPSG:6697 in 3D")
    low = _corner(lower_node)
    high = _corner(upper_node)
    if any(a > b for a, b in zip(low, high)):
        raise CityGMLPreflightError("GML bounding envelope corner order is inverted")
    if low[:2] == high[:2]:
        raise CityGMLPreflightError("GML geographic envelope has zero horizontal extent")

    buildings = []
    for member in root.findall(_tag(CORE, "cityObjectMember")):
        buildings.extend(member.findall(_tag(BLDG, "Building")))
    if not 0 < len(buildings) <= MAX_BUILDINGS:
        raise CityGMLPreflightError("GML has no directly declared buildings or too many")
    measured_heights = 0
    lod_count = {lod: 0 for lod in LODS}
    for building in buildings:
        if not building.get(_tag(GML, "id")):
            raise CityGMLPreflightError("building is missing gml:id")
        height_nodes = building.findall(_tag(BLDG, "measuredHeight"))
        if len(height_nodes) > 1:
            raise CityGMLPreflightError("building has duplicate measuredHeight")
        if height_nodes:
            height = height_nodes[0]
            if height.get("uom") != "m" or not height.text:
                raise CityGMLPreflightError("measuredHeight must be explicitly in metres")
            meters = _finite_number(height.text.strip())
            if not 0 < meters <= 1000:
                raise CityGMLPreflightError("measuredHeight outside conservative preflight bounds")
            measured_heights += 1
        child_names = {
            child.tag[len(BLDG) + 2:]
            for child in building
            if child.tag.startswith("{" + BLDG + "}")
        }
        for lod, names in LODS.items():
            if child_names & names:
                lod_count[lod] += 1

    lod0_screened = _screen_lod0(buildings, low, high)
    return {
        **lod0_screened,
        "source_id": "jp.mlit.plateau.citygml.3d-city-models",
        "local_gml_sha256": hashlib.sha256(raw).hexdigest(),
        "local_gml_byte_count": len(raw),
        "xml_element_count": node_count,
        "building_element_count": len(buildings),
        "building_part_element_count": sum(
            1 for node in root.iter(_tag(BLDG, "BuildingPart"))
        ),
        "measured_height_m_count": measured_heights,
        "measured_height_missing_count": len(buildings) - measured_heights,
        "lod0_property_declared_building_count": lod_count[0],
        "lod1_property_declared_building_count": lod_count[1],
        "lod2_property_declared_building_count": lod_count[2],
        "lod3_property_declared_building_count": lod_count[3],
        "root_envelope_crs": "EPSG:6697",
        "root_envelope_srs_dimension": 3,
        "envelope_numeric_finite_and_ordered": True,
        "envelope_explicit_three_dimensional_declaration": True,
        "lod0_inline_ring_screen_only": True,
        "geodesic_building_area_computed": False,
        "unreferenced_geometry_resolved": False,
        "gml_ids_unique_within_sample": True,
        "evidence": "offline_user_supplied_small_gml_structure_only",
        "vertical_datum_independently_verified": False,
        "envelope_geographic_location_verified": False,
        "original_zip_member_crc_verified": False,
        "original_provider_bytes_authenticated": False,
        "municipality_release_identity_verified": False,
        "geometry_topology_validated": False,
        "height_measurement_method_verified": False,
        "full_xml_schema_validated": False,
        "licence_and_privacy_cleared": False,
        "model_input_approved": False,
        "provider_network_access": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="lawfully supplied single, small GML file")
    args = parser.parse_args(argv)
    try:
        raw = read_local_metadata(args.input, MAX_GML_BYTES)
        result = inspect_gml_bytes(raw)
    except (CataloguePreflightError, CityGMLPreflightError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
