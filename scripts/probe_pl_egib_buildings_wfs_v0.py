#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, bounded original Polish GUGiK EGiB WFS *metadata-only* receipt.

By default this program reads three externally obtained ORIGINAL XML files
offline. Only explicit --live contacts the fixed public GUGiK WFS endpoint.
No GetFeature polygon/row extraction, insured data, source admission or writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PROVIDER_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/EGIB/WFS/UslugaZbiorcza"
SOURCE_ID = "pl.gugik.egib-building-parcels.2026"
FEATURE_TYPE = "ms:budynki"
EXPECTED_CRS = "urn:ogc:def:crs:EPSG::2180"
EXPECTED_FIELDS = (
    "geom",
    "ID_BUDYNKU",
    "RODZAJ",
    "KONDYGNACJE_NADZIEMNE",
    "KONDYGNACJE_PODZIEMNE",
)
WFS = "{http://www.opengis.net/wfs/2.0}"
XS = "{http://www.w3.org/2001/XMLSchema}"
MAX_XML_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 15


class ProviderMetadataError(ValueError):
    """Original provider metadata differs from the pinned bounded contract."""


def provider_requests() -> dict[str, str]:
    """Build only fixed original public metadata requests, never user URLs."""
    common = {"SERVICE": "WFS", "VERSION": "2.0.0"}
    extras = {
        "capabilities": {"REQUEST": "GetCapabilities"},
        "schema": {"REQUEST": "DescribeFeatureType", "TYPENAMES": FEATURE_TYPE},
        "hits": {
            "REQUEST": "GetFeature",
            "TYPENAMES": FEATURE_TYPE,
            "RESULTTYPE": "hits",
            "COUNT": "1",
        },
    }
    return {
        name: PROVIDER_URL + "?" + urllib.parse.urlencode({**common, **extra})
        for name, extra in extras.items()
    }


def _xml(raw: bytes, expected_root: str) -> ET.Element:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_XML_BYTES:
        raise ProviderMetadataError("missing or oversized original XML")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ProviderMetadataError("DOCTYPE / entity declarations are forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ProviderMetadataError("invalid original XML") from exc
    if root.tag != expected_root:
        raise ProviderMetadataError("unexpected WFS/XML root or exception report")
    return root


def _parse_capabilities(raw: bytes) -> dict:
    root = _xml(raw, WFS + "WFS_Capabilities")
    if root.get("version") != "2.0.0":
        raise ProviderMetadataError("provider did not advertise WFS 2.0.0")
    matching = []
    for feature in root.findall(".//" + WFS + "FeatureType"):
        name = feature.findtext(WFS + "Name")
        if name == FEATURE_TYPE:
            matching.append(feature)
    if len(matching) != 1:
        raise ProviderMetadataError("missing or duplicated ms:budynki layer")
    crs = matching[0].findtext(WFS + "DefaultCRS")
    if crs != EXPECTED_CRS:
        raise ProviderMetadataError("building DefaultCRS must be EPSG:2180")
    return {"wfs_version": "2.0.0", "layer": FEATURE_TYPE, "declared_crs": crs}


def _parse_schema(raw: bytes) -> dict:
    root = _xml(raw, XS + "schema")
    complex_types = [
        element
        for element in root.findall(".//" + XS + "complexType")
        if element.get("name") == "budynkiType"
    ]
    if len(complex_types) != 1:
        raise ProviderMetadataError("expected budynkiType missing or duplicated")
    fields = {
        item.get("name"): item.get("type")
        for item in complex_types[0].findall(".//" + XS + "element")
    }
    if any(field not in fields for field in EXPECTED_FIELDS):
        raise ProviderMetadataError("original building field contract changed")
    if fields["geom"] not in ("gml:SurfacePropertyType", "gml:MultiSurfacePropertyType"):
        raise ProviderMetadataError("original building geometry is not a GML surface")
    # A field's existence does not prove a non-null value in any actual building.
    return {
        "advertised_fields_only": list(EXPECTED_FIELDS),
        "geometry_property_kind": fields["geom"],
        "field_values_inspected": False,
    }


def _parse_hits(raw: bytes) -> dict:
    root = _xml(raw, WFS + "FeatureCollection")
    if root.get("numberReturned") != "0":
        raise ProviderMetadataError("metadata-only hits returned feature records")
    if root.findall(".//{http://mapserver.gis.umn.edu/mapserver}budynki"):
        raise ProviderMetadataError("building records returned in hits response")
    # COUNT=1 deliberately constrains the provider operation. numberMatched is
    # NOT used as a national total; different servers apply COUNT differently.
    return {
        "metadata_hits_response": True,
        "records_returned": 0,
        "nationwide_feature_count_known": False,
        "response_timestamp_as_reported": root.get("timeStamp"),
    }


def inspect_original_xml(capabilities: bytes, schema: bytes, hits: bytes) -> dict:
    caps = _parse_capabilities(capabilities)
    fields = _parse_schema(schema)
    response = _parse_hits(hits)
    source_bytes = {
        key: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        for key, raw in (
            ("GetCapabilities", capabilities),
            ("DescribeFeatureType", schema),
            ("GetFeature_hits_count1", hits),
        )
    }
    return {
        "receipt_version": "pl-gugik-egib-buildings-wfs-native-metadata-v0",
        "source_id": SOURCE_ID,
        "provider_url": PROVIDER_URL,
        "capabilities": caps,
        "schema": fields,
        "hits": response,
        "original_xml_byte_receipts": source_bytes,
        "original_source_geometry_downloaded": False,
        "national_coverage_and_counts_verified": False,
        "commercial_redistribution_rights_verified": False,
        "scientific_source_review_verified": False,
        "insurer_location_or_tiv_verified": False,
        "model_input_admitted": False,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Even a same-origin redirect could silently remove RESULTTYPE=hits
        # or change the requested feature type. Never follow redirects.
        raise ProviderMetadataError("provider metadata redirect refused")


def _fetch_bounded(url: str) -> bytes:
    if url not in provider_requests().values():
        raise ProviderMetadataError("unapproved metadata URL")
    opener = urllib.request.build_opener(_NoRedirect())
    request = urllib.request.Request(
        url, headers={"Accept": "application/xml, text/xml"}, method="GET")
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_XML_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderMetadataError("live provider metadata unavailable") from exc
    if not 0 < len(raw) <= MAX_XML_BYTES:
        raise ProviderMetadataError("original XML exceeds byte budget")
    return raw


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="Explicit fixed-host live metadata fetch")
    mode.add_argument("--offline", action="store_true", help="Read local original XML receipts")
    p.add_argument("--capabilities-file", type=Path)
    p.add_argument("--schema-file", type=Path)
    p.add_argument("--hits-file", type=Path)
    a = p.parse_args(argv)
    try:
        urls = provider_requests()
        if a.live:
            if any((a.capabilities_file, a.schema_file, a.hits_file)):
                raise ProviderMetadataError("--live does not accept local files")
            values = {name: _fetch_bounded(url) for name, url in urls.items()}
        else:
            files = {
                "capabilities": a.capabilities_file,
                "schema": a.schema_file,
                "hits": a.hits_file,
            }
            if not all(files.values()):
                raise ProviderMetadataError("all three original local XML files required")
            values = {}
            for name, path in files.items():
                if path.is_symlink() or not path.is_file():
                    raise ProviderMetadataError("original XML must be a regular file")
                with path.open("rb") as stream:
                    values[name] = stream.read(MAX_XML_BYTES + 1)
        result = inspect_original_xml(**values)
    except (ProviderMetadataError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
