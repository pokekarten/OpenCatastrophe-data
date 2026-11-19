#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Direct WFS 2.0 resultType=hits metadata only, exact Hessen ALKIS bbox.

This independently investigates contradictory GetFeature numberReturned
metadata (one Building XML member, claimed 0). No actual buildings,
GML geometry, addresses, source identifiers, coordinates or model data
may be retrieved, emitted or persisted by this operation.
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
    "&TYPENAMES=bu-core2d:Building&COUNT=1&RESULTTYPE=hits"
    "&SRSNAME=urn:ogc:def:crs:EPSG::4258"
    "&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"
)
URL = SERVICE_URL + "?" + QUERY
MAX_BYTES = 65_536
TIMEOUT_SECONDS = 45
WFS_NS = "http://www.opengis.net/wfs/2.0"
SOURCE_ONE_FEATURE_RESPONSE_SHA256 = (
    "3fef39eed3bd0d149d65f0cc5741db99e7d215e11a7115a762de26d855265f58"
)


class HitsBlocked(ValueError):
    """The publisher did not provide a valid bounded no-feature hits response."""


def validate_reviewed_hits() -> None:
    p = urlsplit(URL)
    if (
        p.scheme != "https" or p.netloc != "inspire-hessen.de"
        or p.path != "/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs"
        or p.fragment or p.query != QUERY
        or SERVICE_URL + "?" + QUERY != URL
        or "&COUNT=1&RESULTTYPE=hits" not in QUERY
        or "&SRSNAME=urn:ogc:def:crs:EPSG::4258" not in QUERY
        or not QUERY.endswith(
            "&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"
        )
    ):
        raise HitsBlocked("unauthorized original ALKIS count-only request")


def _count(value: str | None) -> int | None:
    if value in (None, "unknown"):
        return None
    if not value.isascii() or not value.isdigit() or len(value) > 9:
        raise HitsBlocked("unreviewed WFS numberMatched/numberReturned format")
    return int(value)


def inspect_hits(raw: bytes) -> dict:
    """Refuse all actual source features in a hits-only metadata response."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise HitsBlocked("invalid or oversize count-only WFS response")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise HitsBlocked("DTD/entities prohibited")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise HitsBlocked("unparseable publisher WFS hits XML") from exc
    if root.tag != f"{{{WFS_NS}}}FeatureCollection":
        raise HitsBlocked("source returned an exception or non-WFS XML response")
    if sum(1 for _ in root.iter()) > 2_000:
        raise HitsBlocked("excessive XML nodes in hits metadata")
    if root.findall(f"{{{WFS_NS}}}member"):
        raise HitsBlocked("hits-only response contains forbidden source building members")
    if any(child.tag.endswith("}Building") or child.tag == "Building"
           for child in root.iter()):
        raise HitsBlocked("hits-only response leaked building feature")
    reported_returned = _count(root.get("numberReturned"))
    reported_matched = _count(root.get("numberMatched"))
    if reported_returned not in (None, 0):
        raise HitsBlocked("hits-only response incorrectly claims nonzero features returned")

    return {
        "wfs_result_type": "hits",
        "features_in_hits_response": 0,
        "number_returned_if_integer": reported_returned,
        "number_matched_if_integer": reported_matched,
        "provider_claims_positive_matches": reported_matched is not None and reported_matched > 0,
        "provider_match_count_unknown": reported_matched is None,
        "original_feature_payload_downloaded": False,
        "source_building_polygon_validated": False,
        "model_input_approved": False,
    }


def _open(req, timeout):
    client = request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return client.open(req, timeout=timeout)


def probe(*, open_request=_open) -> dict:
    validate_reviewed_hits()
    req = request.Request(
        URL, method="GET",
        headers={
            "Accept": "application/gml+xml,application/xml,text/xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-Hessen-WFS-Hits/0.1",
        },
    )
    try:
        with open_request(req, TIMEOUT_SECONDS) as reply:
            if reply.status != 200 or reply.geturl() != URL:
                raise HitsBlocked("source returned unexpected HTTP status or URL")
            mime = reply.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in (
                "application/xml", "text/xml", "application/gml+xml",
                "application/vnd.ogc.gml", "application/vnd.ogc.wfs_xml",
            ):
                raise HitsBlocked("source returned non-reviewed XML media type")
            if reply.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise HitsBlocked("unreviewed compressed transport response")
            length = reply.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
                raise HitsBlocked("unbounded original HTTP content length")
            raw = reply.read(MAX_BYTES + 1)
    except (HitsBlocked, CapabilityBlocked):
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise HitsBlocked("official Hessen WFS count-only source unavailable") from exc
    details = inspect_hits(raw)
    return {
        "profile": "oc-hessen-alkis-wfs-building-original-hits-count-v0",
        "source": SOURCE,
        "previous_original_feature_payload_sha256": SOURCE_ONE_FEATURE_RESPONSE_SHA256,
        "fixed_bbox_crs": "EPSG:4258",
        "bbox_axis_order": "latitude_longitude",
        "http_status": 200,
        "original_hits_sample_bytes": len(raw),
        "original_hits_sample_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_get_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "raw_source_xml_stored": False,
        "source_ids_attributes_or_coordinates_emitted": False,
        **details,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("reviewed public WFS hits source requires --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HitsBlocked, CapabilityBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
