# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded, metadata-only preflight for the official NRW HWRM WMS service.

Offline by default. --live makes exactly one fixed, anonymous GetCapabilities
request; it never downloads flood rasters, buildings, tiles or model inputs.
A successful result is NOT rights approval, source admission or model fitness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

CAPABILITIES_URL = (
    "https://www.wms.nrw.de/umwelt/wasser/HW_Gefahrenkarte"
    "?REQUEST=GetCapabilities&SERVICE=WMS"
)
MAX_RESPONSE_BYTES = 4_000_000
MAX_REPORTED_LAYERS = 10


class SourceProbeError(ValueError):
    """Provider bytes do not satisfy this exact metadata contract."""


class BlockRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_wms_capabilities(payload: bytes) -> dict[str, object]:
    """Validate the original WMS XML without asserting specific flood layers."""
    if not payload or len(payload) > MAX_RESPONSE_BYTES:
        raise SourceProbeError("empty or oversized WMS response")
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise SourceProbeError("DTD/entities forbidden")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise SourceProbeError("invalid XML") from exc
    root_name = root.tag.rsplit("}", 1)[-1]
    namespace = root.tag.split("}", 1)[0][1:] if root.tag.startswith("{") else ""
    if root_name not in {"WMS_Capabilities", "WMT_MS_Capabilities"}:
        raise SourceProbeError("response is not a WMS capabilities document")
    if namespace not in {"", "http://www.opengis.net/wms"}:
        raise SourceProbeError("unexpected WMS XML namespace")
    version = root.attrib.get("version", "")
    if version not in {"1.1.1", "1.3.0"}:
        raise SourceProbeError("unexpected WMS version")
    service_name = root.findtext("./{*}Service/{*}Name", default="")
    service_title = root.findtext("./{*}Service/{*}Title", default="")
    service_terms = root.findtext("./{*}Service/{*}AccessConstraints", default="")
    if service_name.strip() not in {"WMS", "OGC:WMS"} or not service_title.strip():
        raise SourceProbeError("missing WMS service identity")
    if not service_terms.strip():
        raise SourceProbeError("WMS service terms missing from original metadata")
    capability = root.find("./{*}Capability")
    if capability is None:
        raise SourceProbeError("missing WMS Capability section")
    request = capability.find("./{*}Request")
    if request is None or request.find("./{*}GetCapabilities") is None or request.find("./{*}GetMap") is None:
        raise SourceProbeError("missing WMS GetCapabilities/GetMap operation")
    names = sorted({
        element.text.strip()
        for element in capability.findall(".//{*}Layer/{*}Name")
        if element.text and element.text.strip()
    })
    if not names or any(len(name) > 256 or any(ord(ch) < 32 for ch in name) for name in names):
        raise SourceProbeError("missing or malformed WMS layer names")
    return {
        "wms_version": version,
        "named_layer_count": len(names),
        "first_layer_names": names[:MAX_REPORTED_LAYERS],
        "response_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "service_access_constraints_sha256": hashlib.sha256(
            service_terms.encode("utf-8")
        ).hexdigest(),
        "service_mentions_attribution": (
            "namensnennung" in service_terms.casefold()
            or "dl-de/by-2-0" in service_terms.casefold()
        ),
        "rights_reviewed": False,
        "verified_live": False,
        "sample_policy": "receipt_only",
        "model_admitted": False,
        "external_bytes_persisted": False,
    }


def probe_live() -> dict[str, object]:
    """Single exact-host HTTPS GET with redirect/size/content-type hard gates."""
    request = Request(
        CAPABILITIES_URL,
        headers={"Accept": "application/xml,text/xml", "User-Agent": "OpenCatastrophe-data-source-preflight/1"},
        method="GET",
    )
    opener = build_opener(BlockRedirects)
    try:
        with opener.open(request, timeout=20) as response:
            if response.status != 200 or response.geturl() != CAPABILITIES_URL:
                raise SourceProbeError("unexpected status or endpoint redirect")
            content_type = response.headers.get_content_type().lower()
            if content_type not in {"text/xml", "application/xml", "application/vnd.ogc.wms_xml"}:
                raise SourceProbeError("unexpected response content type")
            expected_length = response.headers.get("Content-Length")
            if expected_length and int(expected_length) > MAX_RESPONSE_BYTES:
                raise SourceProbeError("provider metadata too large")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise SourceProbeError("network/status/size gate failed") from exc
    result = parse_wms_capabilities(payload)
    result["verified_live"] = True
    result["operation"] = "WMS GetCapabilities"
    result["source_id"] = "de.nrw.lanuk.hwrm-hqhaeufig-flood.2026"
    result["provider_url"] = CAPABILITIES_URL
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly allow the one fixed external metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default: pass --live for the fixed public metadata probe")
    try:
        print(json.dumps(probe_live(), sort_keys=True))
    except SourceProbeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
