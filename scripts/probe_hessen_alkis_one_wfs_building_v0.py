#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exactly one candidate ALKIS Building feature via directly verified Hessen WFS.

One original WFS 2.0.0 GetFeature query; BBOX coordinates use EPSG:4258
latitude/longitude axis order. Cap at one source feature and 512 KiB.
Feature names/IDs, addresses, attributes and polygon coordinate bytes
are never emitted or persisted. No CAT model or insured exposure admission.
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
    NoRedirect, SERVICE_URL, CapabilityBlocked,
)

SOURCE = "de.hessen.inspire-alkis-2d-buildings.wfs"
QUERY = (
    "SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
    "&TYPENAMES=bu-core2d:Building&COUNT=1"
    "&SRSNAME=urn:ogc:def:crs:EPSG::4258"
    "&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"
)
URL = SERVICE_URL + "?" + QUERY
MAX_BYTES = 524_288
MAX_ELEMENTS = 30_000
TIMEOUT_SECONDS = 45
WFS_NS = "http://www.opengis.net/wfs/2.0"
GML_NS = "http://www.opengis.net/gml/3.2"
REQUESTED_CRS = "urn:ogc:def:crs:EPSG::4258"
SOURCE_CAPABILITIES_SAMPLE_SHA256 = (
    "abb7ae137eca6ffe31682b41751a258cd09e84a7445a686ca033c500cf76f2bf"
)
OFFICIAL_CATALOGUE = "https://www.geoportal.hessen.de/spatial-objects/711"


class BuildingFeatureBlocked(ValueError):
    """A source URI, WFS response or feature count violates the one-feature review."""


def validate_frozen_getfeature() -> None:
    url = urlsplit(URL)
    if (
        url.scheme != "https" or url.netloc != "inspire-hessen.de"
        or url.path != "/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs"
        or url.query != QUERY or url.fragment
        or not QUERY.endswith(
            "&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"
        )
        or "COUNT=1" not in QUERY
        or "TYPENAMES=bu-core2d:Building" not in QUERY
        or "SRSNAME=urn:ogc:def:crs:EPSG::4258" not in QUERY
        or SERVICE_URL + "?" + QUERY != URL
    ):
        raise BuildingFeatureBlocked("unreviewed WFS original building query or CRS axis order")


def _positive_count(raw: str | None, key: str) -> int | None:
    if raw is None or raw == "unknown":
        return None
    if not raw.isascii() or not raw.isdigit() or len(raw) > 9:
        raise BuildingFeatureBlocked("invalid WFS " + key)
    return int(raw)


def inspect_feature_xml(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise BuildingFeatureBlocked("unsupported WFS original XML byte size")
    up = raw.upper()
    if b"<!DOCTYPE" in up or b"<!ENTITY" in up:
        raise BuildingFeatureBlocked("XML DTD/entity source forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise BuildingFeatureBlocked("unparseable original WFS feature XML") from exc
    if root.tag != f"{{{WFS_NS}}}FeatureCollection":
        raise BuildingFeatureBlocked("WFS source responded with non-feature/exception XML")
    if sum(1 for _ in root.iter()) > MAX_ELEMENTS:
        raise BuildingFeatureBlocked("WFS XML element budget exceeded")

    members = root.findall(f"{{{WFS_NS}}}member")
    if len(members) > 1:
        raise BuildingFeatureBlocked("WFS returned more than one building member")
    for member in members:
        if len(member) != 1:
            raise BuildingFeatureBlocked("WFS building member missing exactly one feature")
        tag = member[0].tag
        if not (tag == "Building" or tag.endswith("}Building")):
            raise BuildingFeatureBlocked("WFS returned unexpected non-Building feature type")
    reported_returned = _positive_count(root.get("numberReturned"), "numberReturned")
    if reported_returned is not None and reported_returned != len(members):
        raise BuildingFeatureBlocked("WFS returned-member count contradicts header")
    reported_matched = _positive_count(root.get("numberMatched"), "numberMatched")
    if reported_matched is not None and reported_matched < len(members):
        raise BuildingFeatureBlocked("WFS matched count contradicts feature count")

    srs_names = set()
    geometry_markup = False
    for member in members:
        for child in member.iter():
            srs = child.attrib.get("srsName")
            if srs:
                if len(srs) > 160 or not all(ch.isalnum() or ch in "-./:#_" for ch in srs):
                    raise BuildingFeatureBlocked("unsafe or unexpected source CRS identifier")
                srs_names.add(srs)
            if child.tag in (
                f"{{{GML_NS}}}MultiSurface", f"{{{GML_NS}}}Surface",
                f"{{{GML_NS}}}Polygon", f"{{{GML_NS}}}posList"
            ):
                geometry_markup = True
    if len(srs_names) > 5:
        raise BuildingFeatureBlocked("too many conflicting geometry CRS declarations")
    crs_ok = bool(members) and bool(srs_names) and all(
        n in (
            "urn:ogc:def:crs:EPSG::4258",
            "http://www.opengis.net/def/crs/EPSG/0/4258",
            "EPSG:4258",
        ) for n in srs_names
    )
    # Do not emit observed geometry IDs or coordinate values.
    return {
        "original_feature_members_returned": len(members),
        "reported_number_returned_if_integer": reported_returned,
        "reported_number_matched_if_integer": reported_matched,
        "source_geometry_markup_present": geometry_markup,
        "geometry_crs_declared_and_matches_requested": crs_ok if members else None,
        "geometry_crs_independent_accuracy_verified": False,
        "actual_2d_polygon_topology_verified": False,
        "actual_building_worldcover_overlap_verified": False,
        "actual_building_survey_vintage_verified": False,
        "not_a_complete_building_inventory": True,
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
    validate_frozen_getfeature()
    req = request.Request(
        URL, method="GET",
        headers={
            "Accept": "application/gml+xml,application/xml,text/xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Hessen-ALKIS-One-Building/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != URL:
                raise BuildingFeatureBlocked("original WFS status or URL mismatch")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if mime not in (
                "application/xml", "text/xml", "application/gml+xml",
                "application/vnd.ogc.gml", "application/vnd.ogc.wfs_xml",
            ):
                raise BuildingFeatureBlocked("unexpected original WFS GML/XML MIME")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise BuildingFeatureBlocked("unreviewed WFS transfer compression")
            declared_size = response.headers.get("Content-Length")
            if declared_size is not None and (
                not declared_size.isdigit() or int(declared_size) > MAX_BYTES
            ):
                raise BuildingFeatureBlocked("original WFS Content-Length too large")
            raw = response.read(MAX_BYTES + 1)
    except (CapabilityBlocked, BuildingFeatureBlocked):
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise BuildingFeatureBlocked("bounded original WFS GetFeature unavailable") from exc
    details = inspect_feature_xml(raw)
    return {
        "profile": "oc-hessen-alkis-building-one-original-wfs-feature-v0",
        "source_id": SOURCE,
        "provider_catalogue": OFFICIAL_CATALOGUE,
        "source_original_operation": "WFS_2.0.0_GetFeature_Building_COUNT1_one_fixed_ETRS89_bbox",
        "fixed_bbox_crs": "EPSG:4258",
        "fixed_bbox_axis_order": "latitude_longitude",
        "previous_original_capabilities_sha256": SOURCE_CAPABILITIES_SAMPLE_SHA256,
        "http_status": 200,
        "original_response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "frozen_request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "feature_identifiers_addresses_or_coordinates_emitted": False,
        "source_raw_features_or_gml_persisted": False,
        **details,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("one original WFS GetFeature requires --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (BuildingFeatureBlocked, CapabilityBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
