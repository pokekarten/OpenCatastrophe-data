#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect one exact Hessen ALKIS WFS 2.0 Building DescribeFeatureType XSD.

Read only official schema bytes, never follow xsd:import/schemaLocation,
retrieve GML building features, emit source attributes/coordinates, admit
assets or alter insurance databases. Explicitly preserve original source
GetFeature numberReturned discrepancy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from urllib import error, request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from scripts.probe_hessen_alkis_wfs_capabilities_v0 import (
    SERVICE_URL, NoRedirect, CapabilityBlocked,
)

SOURCE_ID = "de.hessen.inspire-alkis-2d-buildings.wfs"
QUERY = (
    "SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType"
    "&TYPENAMES=bu-core2d:Building"
)
URL = SERVICE_URL + "?" + QUERY
XSD_NS = "http://www.w3.org/2001/XMLSchema"
BUILDING_NS = "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0"
MAX_BYTES = 524_288
MAX_ELEMENTS = 20_000
MAX_IMPORTS = 80
TIMEOUT_SECONDS = 45
EXPECTED_CAPABILITIES_SHA256 = (
    "abb7ae137eca6ffe31682b41751a258cd09e84a7445a686ca033c500cf76f2bf"
)
OBSERVED_WFS_FEATURE_RESPONSE_SHA256 = (
    "3fef39eed3bd0d149d65f0cc5741db99e7d215e11a7115a762de26d855265f58"
)


class SchemaBlocked(ValueError):
    """The original service did not supply the exact reviewed schema format."""


def validate_exact_source() -> None:
    parts = urlsplit(URL)
    if (
        parts.scheme != "https"
        or parts.netloc != "inspire-hessen.de"
        or parts.path != "/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs"
        or parts.query != QUERY
        or parts.fragment
        or SERVICE_URL + "?" + QUERY != URL
        or MAX_BYTES != 524_288
    ):
        raise SchemaBlocked("unreviewed Hessen original WFS DescribeFeatureType URL")


def inspect_xsd(raw: bytes) -> dict:
    """Return finite schema *metadata*, never copied XML/attributes/URLs."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise SchemaBlocked("original schema empty or over reviewed source byte cap")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise SchemaBlocked("XSD document cannot contain a DTD or entity definition")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SchemaBlocked("source response is not valid XSD XML") from exc
    if root.tag != f"{{{XSD_NS}}}schema":
        raise SchemaBlocked("WFS source returned exception or non-XSD document")
    elements = list(root.iter())
    if len(elements) > MAX_ELEMENTS:
        raise SchemaBlocked("source schema XML element count exceeded")
    target = root.get("targetNamespace")
    if target not in (BUILDING_NS, None):
        raise SchemaBlocked("returned schema targets an unrelated source namespace")

    imports = root.findall(f"./{{{XSD_NS}}}import")
    includes = root.findall(f"./{{{XSD_NS}}}include")
    if len(imports) + len(includes) > MAX_IMPORTS:
        raise SchemaBlocked("unbounded XSD dependency references")
    declared = root.findall(f"./{{{XSD_NS}}}element")
    names = [entry.get("name") for entry in declared]
    if any(not name or len(name) > 180 for name in names):
        raise SchemaBlocked("invalid source XSD global element name")
    if len(names) != len(set(names)):
        raise SchemaBlocked("duplicate global XSD element declarations")

    building = [elem for elem in declared if elem.get("name") == "Building"]
    if len(building) > 1:
        raise SchemaBlocked("ambiguous duplicate building global declaration")
    declared_type = building[0].get("type") if building else None
    if declared_type is not None and (
        len(declared_type) > 200 or
        not all(x.isalnum() or x in "-_.:" for x in declared_type)
    ):
        raise SchemaBlocked("unexpected Building XSD declared type")

    # This parser does not resolve any import to reach the complexType body.
    # Missing global Building declaration can be an aggregator XSD with
    # imports; report uncertainty rather than claiming schema verified.
    return {
        "schema_root_is_xsd": True,
        "target_namespace_matches_building_if_declared": target == BUILDING_NS,
        "global_element_count": len(declared),
        "global_building_element_declared": bool(building),
        "building_type_local_declaration_if_present": declared_type,
        "xsd_import_count_not_followed": len(imports),
        "xsd_include_count_not_followed": len(includes),
        "schema_dependencies_downloaded": 0,
        "building_type_structure_fully_resolved": False,
        "provider_getfeature_number_returned_discrepancy_resolved": False,
        "source_building_polygon_validated": False,
        "model_input_approved": False,
    }


def _open(req: request.Request, timeout: int):
    client = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return client.open(req, timeout=timeout)


def probe(*, open_request=_open) -> dict:
    validate_exact_source()
    req = request.Request(
        URL, method="GET",
        headers={
            "Accept": "application/xml,text/xml,application/xsd+xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Hessen-ALKIS-Building-XSD/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as reply:
            if reply.status != 200 or reply.geturl() != URL:
                raise SchemaBlocked("WFS original DescribeFeatureType status/URL not approved")
            mime = reply.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in (
                "text/xml", "application/xml", "application/xsd+xml",
                "application/gml+xml",
            ):
                raise SchemaBlocked("WFS source returned unexpected XSD MIME")
            if reply.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SchemaBlocked("unreviewed HTTP content encoding")
            length = reply.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
                raise SchemaBlocked("WFS original schema response oversized")
            raw = reply.read(MAX_BYTES + 1)
    except (CapabilityBlocked, SchemaBlocked):
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise SchemaBlocked("direct original Hessen ALKIS DescribeFeatureType unavailable") from exc
    facts = inspect_xsd(raw)
    return {
        "profile": "oc-hessen-alkis-building-describefeaturetype-v0",
        "source_id": SOURCE_ID,
        "original_operation": "WFS_2.0.0_DescribeFeatureType_Building_exact",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 200,
        "original_xsd_sample_bytes": len(raw),
        "original_xsd_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_get_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prior_original_capabilities_sha256": EXPECTED_CAPABILITIES_SHA256,
        "prior_original_getfeature_sha256": OBSERVED_WFS_FEATURE_RESPONSE_SHA256,
        "raw_source_xml_persisted": False,
        "source_building_attributes_or_coordinates_emitted": False,
        **facts,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("source DescribeFeatureType disabled without explicit --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (SchemaBlocked, CapabilityBlocked, ValueError, OSError) as exc:
        print(json.dumps({
            "status": "BLOCKED", "reason": str(exc), "model_input_approved": False,
        }), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
