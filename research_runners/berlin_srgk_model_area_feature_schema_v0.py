#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed official Berlin SRGK WFS DescribeFeatureType, metadata only.

Discover advertised geometry-property *names* for future reviewed FES filters.
No provider feature, geometry, raster, hazard values, insurers or DB writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from urllib import error, parse, request
from xml.etree import ElementTree as ET

ROOT = "https://gdi.berlin.de/services/wfs/ua_srgk"
LAYER = "ua_srgk:a_modellgebiete"
URL = ROOT + "?" + parse.urlencode([
    ("service", "WFS"), ("version", "2.0.0"),
    ("request", "DescribeFeatureType"), ("typeNames", LAYER),
])
XSD = "{http://www.w3.org/2001/XMLSchema}"
MAX_BYTES = 524_288
MAX_ELEMENT_COUNT = 250
TIMEOUT = 40
PROFILE = "berlin-srgk-model-area-exact-xsd-geometry-property-probe-v0"


class SchemaBlocked(ValueError):
    """Unverified external schema response or unsafe source metadata."""


def inspect(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise SchemaBlocked("empty or oversized official source XSD")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise SchemaBlocked("DTD/entity is not acceptable for source XSD")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SchemaBlocked("source XML is not parseable") from exc
    if root.tag != XSD + "schema":
        raise SchemaBlocked("expected official WFS XML Schema root")
    elements = root.findall(".//" + XSD + "element")
    if len(elements) > MAX_ELEMENT_COUNT or not elements:
        raise SchemaBlocked("missing or unbounded XSD element list")
    feature_names = [e.get("name") for e in elements if e.get("name") == "a_modellgebiete"]
    if len(feature_names) != 1:
        raise SchemaBlocked("exact model-area feature element not found uniquely")
    fields = {}
    for e in elements:
        name, typ = e.get("name"), e.get("type", "")
        if not isinstance(name, str) or len(name) > 120 or (
            typ and (not isinstance(typ, str) or len(typ) > 180)
        ):
            raise SchemaBlocked("invalid or oversized XSD property")
        if name and name != "a_modellgebiete":
            if name in fields and fields[name] != typ:
                raise SchemaBlocked("ambiguous repeated XSD property type")
            fields[name] = typ
    geometry = []
    for name, typ in sorted(fields.items()):
        lowered_name, lowered_type = name.lower(), typ.lower()
        if ("geom" in lowered_name or "shape" in lowered_name
                or (("gml:" in lowered_type or "geometry" in lowered_type)
                    and ("propertytype" in lowered_type or "geometry" in lowered_type))):
            geometry.append({"property_name": name, "declared_type": typ})
    if len(geometry) > 10:
        raise SchemaBlocked("unexpected number of source geometry fields")
    return {
        "profile": PROFILE,
        "wfs_source_layer": LAYER,
        "source_xsd_root_validated": True,
        "source_declared_element_count": len(elements),
        "source_model_area_element_present": True,
        "model_area_geometry_candidate_fields": geometry,
        "geometry_candidate_count": len(geometry),
        "single_geometry_field_confirmed": len(geometry) == 1,
        "xml_imports_or_includes_not_followed": True,
        "field_names_are_metadata_not_source_feature_geometry": True,
        "pilot_bbox_filter_still_not_validated": True,
        "source_feature_or_raster_bytes_retrieved": False,
        "model_input_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SchemaBlocked("official fixed XSD source redirected")


def _get(req, timeout):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context())
    ).open(req, timeout=timeout)


def probe(*, opener=_get, clock=lambda: datetime.now(timezone.utc)):
    req = request.Request(URL, headers={"Accept": "application/xml, text/xml;q=0.9"},
                          method="GET")
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise SchemaBlocked("unverified source HTTP status or exact URL")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in ("application/xml", "text/xml", "application/xsd", "application/gml+xml"):
                raise SchemaBlocked("unexpected source schema media type")
            raw = response.read(MAX_BYTES + 1)
    except SchemaBlocked:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise SchemaBlocked("official WFS DescribeFeatureType failed") from exc
    result = inspect(raw)
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise SchemaBlocked("source time must be timezone aware")
    return {
        "exact_official_request_url": URL,
        "original_xsd_byte_count": len(raw),
        "original_xsd_sha256": sha256(raw).hexdigest(),
        "source_checked_utc": now.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_xsd_body_not_persisted": True,
        **result,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for the one fixed original schema request")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (SchemaBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
