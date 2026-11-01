#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect exactly one official Hessen INSPIRE ALKIS Building WFS GetCapabilities.

No GetFeature, original polygon/feature, identifier, owner record, query
selector, pagination, source-byte persistence or CAT model admission.
Only fixed public service metadata and digest are emitted.
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

SOURCE = "de.hessen.inspire-alkis-2d-buildings.wfs"
SERVICE_URL = "https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs"
QUERY = "SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities"
URL = SERVICE_URL + "?" + QUERY
OFFICIAL_CATALOGUE = "https://www.geoportal.hessen.de/spatial-objects/711"
MAX_BYTES = 2_097_152
MAX_ELEMENTS = 60_000
MAX_FEATURE_TYPES = 500
MAX_FEATURE_NAME_BYTES = 256
TIMEOUT_SECONDS = 45
WFS_NS = "http://www.opengis.net/wfs/2.0"
OWS_NS = "http://www.opengis.net/ows/1.1"


class CapabilityBlocked(ValueError):
    """Source request, original XML identity or bounded schema is rejected."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CapabilityBlocked("redirect outside approved exact original WFS URL")


def validate_exact_request() -> None:
    parsed = urlsplit(URL)
    if (parsed.scheme != "https" or parsed.hostname != "inspire-hessen.de"
            or parsed.netloc != "inspire-hessen.de"
            or parsed.path != "/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs"
            or parsed.query != QUERY or parsed.fragment
            or SERVICE_URL + "?" + QUERY != URL
            or MAX_BYTES != 2_097_152):
        raise CapabilityBlocked("unreviewed direct ALKIS-WFS request")


def inspect_capabilities(raw: bytes) -> dict:
    """Extract only OGC service metadata, no original XML output."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise CapabilityBlocked("invalid or oversized source XML")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise CapabilityBlocked("external or internal XML entity declarations prohibited")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CapabilityBlocked("unparseable WFS XML capabilities") from exc
    if root.tag != f"{{{WFS_NS}}}WFS_Capabilities" or root.get("version") != "2.0.0":
        raise CapabilityBlocked("not an original WFS 2.0.0 capabilities document")
    if sum(1 for _ in root.iter()) > MAX_ELEMENTS:
        raise CapabilityBlocked("unbounded WFS capabilities element count")

    all_features = root.findall(f"./{{{WFS_NS}}}FeatureTypeList/{{{WFS_NS}}}FeatureType")
    if not 0 < len(all_features) <= MAX_FEATURE_TYPES:
        raise CapabilityBlocked("missing or excessive advertised WFS feature types")
    names = []
    crs = []
    for feature in all_features:
        name = feature.findtext(f"{{{WFS_NS}}}Name")
        if not name or not name.strip() or len(name.encode("utf-8")) > MAX_FEATURE_NAME_BYTES:
            raise CapabilityBlocked("invalid advertised feature type identifier")
        if not all(ch.isalnum() or ch in "_-:." for ch in name):
            raise CapabilityBlocked("unsafe WFS feature type identifier")
        names.append(name)
        default_crs = feature.findtext(f"{{{WFS_NS}}}DefaultCRS")
        if default_crs and len(default_crs) > 200:
            raise CapabilityBlocked("excessive advertised WFS CRS")
        crs.append(default_crs)
    if len(set(names)) != len(names):
        raise CapabilityBlocked("ambiguous duplicate WFS feature types")
    operations = []
    for operation in root.findall(
        f"./{{{OWS_NS}}}OperationsMetadata/{{{OWS_NS}}}Operation"
    ):
        value = operation.get("name")
        if value and value in ("GetCapabilities", "DescribeFeatureType", "GetFeature"):
            operations.append(value)

    expected_building = [n for n in names if n.endswith(":Building") or n == "Building"]
    expected_part = [n for n in names if n.endswith(":BuildingPart") or n == "BuildingPart"]
    # A source can be operationally reachable but not expose the expected
    # building features. Report that fact, do not force WFS use or approval.
    return {
        "advertised_feature_type_count": len(names),
        "advertised_feature_types": names[:30],
        "feature_type_names_truncated": len(names) > 30,
        "building_feature_types": expected_building,
        "building_part_feature_types": expected_part,
        "building_feature_type_present": bool(expected_building),
        "building_part_feature_type_present": bool(expected_part),
        "advertises_getfeature": "GetFeature" in operations,
        "advertises_describefeaturetype": "DescribeFeatureType" in operations,
        "advertises_getcapabilities": "GetCapabilities" in operations,
        "building_default_crs_if_advertised": [
            crs[i] for i, name in enumerate(names) if name in expected_building
        ],
        "actual_building_feature_geometry_verified": False,
        "actual_building_feature_count_verified": False,
        "feature_query_authorized": False,
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
    validate_exact_request()
    req = request.Request(
        URL, method="GET",
        headers={
            "Accept": "application/xml,text/xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Hessen-ALKIS-WFS-Capabilities/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != URL:
                raise CapabilityBlocked("WFS source status or original request URL drift")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if mime not in ("application/xml", "text/xml", "application/vnd.ogc.wfs_xml"):
                raise CapabilityBlocked("unreviewed original WFS XML transport MIME")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise CapabilityBlocked("unreviewed HTTP content encoding")
            size = response.headers.get("Content-Length")
            if size is not None and (not size.isdigit() or int(size) > MAX_BYTES):
                raise CapabilityBlocked("WFS XML Content-Length exceeds reviewed cap")
            raw = response.read(MAX_BYTES + 1)
    except CapabilityBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise CapabilityBlocked("direct official Hessen ALKIS WFS GetCapabilities unavailable") from exc
    result = inspect_capabilities(raw)
    return {
        "profile": "oc-hessen-alkis-original-wfs-2-getcapabilities-v0",
        "source_id": SOURCE,
        "provider_catalogue": OFFICIAL_CATALOGUE,
        "source_original_operation": "WFS_2.0.0_GetCapabilities_exact_url_only",
        "original_http_status": 200,
        "sample_bytes": len(raw),
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "fixed_get_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "raw_xml_or_building_attributes_persisted": False,
        "source_feature_identifiers_or_coordinates_printed": False,
        **result,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("the official direct source request requires explicit --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (CapabilityBlocked, ValueError, OSError) as exc:
        print(json.dumps({
            "status": "BLOCKED", "reason": str(exc),
            "model_input_approved": False,
        }), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
