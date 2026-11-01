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
    if envelope.get("srsName") != EPSG6697 or envelope.get("srsDimension") != "3":
        raise CityGMLPreflightError("GML envelope must explicitly use EPSG:6697 in 3D")
    low = _corner(envelope.find(_tag(GML, "lowerCorner")))
    high = _corner(envelope.find(_tag(GML, "upperCorner")))
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

    return {
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
