# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded WFS hits-only probes for two official Cologne city Open Data services.

Offline unless explicitly invoked with --live. No feature data is requested,
downloaded or retained, and results do not admit model data or licences.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

SOURCES = {
    "tree": {
        "candidate_id": "de.koeln.city-tree-register.2026",
        "url": (
            "https://geoportal.stadt-koeln.de/wss/service/baumkataster_extern_wfs/guest"
            "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
            "&TYPENAMES=ms:baumkataster&RESULTTYPE=hits&COUNT=1"
        ),
    },
    "kgg": {
        "candidate_id": "de.koeln.statistik.rbs-geopackage.2026",
        "url": (
            "https://geoportal.stadt-koeln.de/arcgis/services/basiskarten/kgg"
            "/MapServer/WFSServer?SERVICE=WFS&VERSION=2.0.0"
            "&REQUEST=GetFeature&TYPENAMES=Basiskarten_kgg:Stadtviertel"
            "&RESULTTYPE=hits&COUNT=1"
        ),
    },
}
MAX_RESPONSE_BYTES = 64_000
WFS_NAMESPACE = "http://www.opengis.net/wfs/2.0"


class WfsProbeError(ValueError):
    """WFS hits evidence fails a bounded metadata or safety requirement."""


class DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_hits(payload: bytes) -> dict[str, object]:
    """Validate a feature-free WFS 2.0 hits response, and record its byte hash."""
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise WfsProbeError("empty or oversized WFS hits response")
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise WfsProbeError("DTD and entities forbidden")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise WfsProbeError("invalid WFS XML") from exc
    if root.tag != "{" + WFS_NAMESPACE + "}FeatureCollection":
        raise WfsProbeError("response is not WFS 2.0 FeatureCollection")
    if root.attrib.get("numberReturned") != "0":
        raise WfsProbeError("hits-only response unexpectedly returns features")
    if any(element.tag.rsplit("}", 1)[-1] in {"member", "featureMember", "featureMembers"}
           for element in root.iter() if element is not root):
        raise WfsProbeError("hits response includes feature elements")
    matched = root.attrib.get("numberMatched")
    if matched is None or not matched.isdigit():
        raise WfsProbeError("missing or invalid numberMatched")
    timestamp = root.attrib.get("timeStamp")
    if not timestamp:
        raise WfsProbeError("missing provider timestamp")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WfsProbeError("invalid provider timestamp") from exc
    return {
        "wfs_version": "2.0.0",
        "number_matched_reported": int(matched),
        "number_returned": 0,
        "provider_timestamp": timestamp,
        "response_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "count_query_limit": 1,
        "total_inventory_established": False,
        "original_features_acquired": False,
        "external_bytes_persisted": False,
        "model_admitted": False,
        "verified_live": False,
    }


def probe_live(source: str) -> dict[str, object]:
    """Single fixed official GetFeature/hits request; no redirects, cookies or credentials."""
    if source not in SOURCES:
        raise WfsProbeError("unsupported source")
    spec = SOURCES[source]
    url = str(spec["url"])
    request = Request(
        url,
        headers={
            "Accept": "text/xml,application/xml",
            "User-Agent": "OpenCatastrophe-data-WFS-hits-preflight/1",
        },
        method="GET",
    )
    try:
        with build_opener(DenyRedirects).open(request, timeout=20) as response:
            if response.status != 200 or response.geturl() != url:
                raise WfsProbeError("unexpected HTTP status or redirection")
            if response.headers.get_content_type().lower() not in {"text/xml", "application/xml"}:
                raise WfsProbeError("response is not XML")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_RESPONSE_BYTES:
                raise WfsProbeError("response advertises too many bytes")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise WfsProbeError("WFS request failed its fixed network boundary") from exc
    receipt = parse_hits(payload)
    receipt.update({
        "source": source,
        "candidate_id": spec["candidate_id"],
        "provider_url": url,
        "request_operation": "WFS GetFeature resultType=hits",
        "verified_live": True,
    })
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=tuple(SOURCES), required=True)
    parser.add_argument("--live", action="store_true", help="opt in to one public metadata-only WFS GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; use --live for a source metadata request")
    try:
        print(json.dumps(probe_live(args.source), sort_keys=True))
        return 0
    except WfsProbeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
