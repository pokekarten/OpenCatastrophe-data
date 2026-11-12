#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed original Berlin ALKIS WFS 2.0.0 capabilities metadata probe.

Exactly one manually opted-in, anonymous read of the provider's published
GetCapabilities URL. No GetFeature, geometry, address, owner information,
pagination, bulk data, query inputs, retries or provider byte persistence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Callable
from urllib import error, request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
ACCESS_ID = "de.berlin.alkis-gebaeude.wfs"
CONTRACT_PATH = ROOT / "access" / (ACCESS_ID + ".json")
URL = "https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&service=WFS"
MAX_BYTES = 1_048_576
TIMEOUT = 30
MEDIA_TYPES = {"application/xml", "text/xml", "application/gml+xml"}
WFS = "{http://www.opengis.net/wfs/2.0}"
OWS = "{http://www.opengis.net/ows/1.1}"
FROZEN_LAYER = "alkis_gebaeude:gebaeude"
FROZEN_CRS = "urn:ogc:def:crs:EPSG::25833"


class BerlinWFSBlocked(ValueError):
    """Original provider metadata or reviewed legal/request gate changed."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BerlinWFSBlocked("provider redirect outside reviewed route")


def verify_reviewed_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    rights = c["rights_and_policy"]
    u = urlsplit(URL)
    if (c["access_id"] != ACCESS_ID or c["source_ids"] != [ACCESS_ID]
            or c["interface_type"] != "wfs" or c["status"] != "probe_ready"
            or c["service_root"] != "https://gdi.berlin.de"
            or c["request_contract"]["path_templates"] != ["/services/wfs/alkis_gebaeude"]
            or c["request_contract"]["allowed_operations"] != ["get_capabilities"]
            or c["access_scope"] != ["metadata"]
            or c["authentication"]["mode"] != "none"
            or c["probe_contract"]["mode"] != "metadata_get"
            or c["probe_contract"]["operation"] != "get_capabilities"
            or c["probe_contract"]["requires_credentials"] is not False
            or rights["dataset_rights_status"] != "verified"
            or rights["api_terms_status"] != "separate_reviewed"
            or rights["commercial_automation_status"] != "allowed"
            or rights["terms_url"] !=
                "https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/"
                "liegenschaftskataster/geobasisdaten-online/nutzungsbedingungen/"
            or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
            or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
            or c["operational_constraints"]["retry_policy"] != "none"
            or u.scheme != "https" or u.netloc != "gdi.berlin.de"
            or u.path != "/services/wfs/alkis_gebaeude"
            or u.query != "request=GetCapabilities&service=WFS"
            or u.fragment or u.username or u.password):
        raise BerlinWFSBlocked("Berlin metadata-only rights/request contract changed")


def inspect_capabilities(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_BYTES:
        raise BerlinWFSBlocked("original WFS capabilities byte bound invalid")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise BerlinWFSBlocked("XML external entities or DTD forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise BerlinWFSBlocked("invalid original WFS XML") from exc
    if root.tag != WFS + "WFS_Capabilities" or root.get("version") != "2.0.0":
        raise BerlinWFSBlocked("original service is not WFS 2.0.0")

    identity = root.find(OWS + "ServiceIdentification")
    if identity is None:
        raise BerlinWFSBlocked("missing official service identification")

    def required_text(parent, tag: str) -> str:
        node = parent.find(tag)
        if node is None or not node.text or not node.text.strip():
            raise BerlinWFSBlocked("missing required WFS service metadata")
        return node.text.strip()

    title = required_text(identity, OWS + "Title")
    service_type = required_text(identity, OWS + "ServiceType")
    service_version = required_text(identity, OWS + "ServiceTypeVersion")
    fees = required_text(identity, OWS + "Fees").casefold()
    access = required_text(identity, OWS + "AccessConstraints").casefold()
    if (title != "ALKIS Berlin Gebäude" or service_type != "WFS"
            or service_version != "2.0.0"
            or "datenlizenz deutschland" not in fees
            or "zero" not in fees or "2.0" not in fees
            or "keine zugriffsbeschränkungen" not in access):
        raise BerlinWFSBlocked("provider original license, access or WFS identity drift")

    provider = root.find(OWS + "ServiceProvider")
    if (provider is None
            or required_text(provider, OWS + "ProviderName")
            != "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin"):
        raise BerlinWFSBlocked("official Berlin provider identity changed")

    operation = root.find(OWS + "OperationsMetadata")
    if operation is None or not any(
        child.get("name") == "GetCapabilities"
        for child in operation.findall(OWS + "Operation")
    ):
        raise BerlinWFSBlocked("WFS GetCapabilities operation absent")

    feature_list = root.find(WFS + "FeatureTypeList")
    if feature_list is None:
        raise BerlinWFSBlocked("original WFS layer inventory missing")
    matches = []
    for feature in feature_list.findall(WFS + "FeatureType"):
        name = feature.findtext(WFS + "Name")
        if name == FROZEN_LAYER:
            matches.append(feature)
    if len(matches) != 1 or matches[0].findtext(WFS + "DefaultCRS") != FROZEN_CRS:
        raise BerlinWFSBlocked("original Berlin building layer or EPSG:25833 changed")

    # Do not retain building attributes, owner data or remote XML fields.
    return {
        "wfs_version": "2.0.0",
        "service_identity_verified": True,
        "original_licence_terms_confirmed": "DL-DE Zero 2.0",
        "service_access_constraints": "no_access_restrictions",
        "layer_id_verified": FROZEN_LAYER,
        "default_crs_verified": "EPSG:25833",
        "feature_requests_executed": 0,
        "individual_buildings_retrieved": 0,
    }


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, open_request: Callable = _open,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    verify_reviewed_contract()
    req = request.Request(URL, method="GET", headers={
        "Accept": "application/xml,text/xml",
        "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-Berlin-WFS-capabilities-metadata/0.1",
    })
    try:
        with open_request(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != URL:
                raise BerlinWFSBlocked("WFS HTTP status or original identity mismatch")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in MEDIA_TYPES:
                raise BerlinWFSBlocked("unreviewed WFS response content type")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise BerlinWFSBlocked("unreviewed WFS transfer encoding")
            length = resp.headers.get("Content-Length")
            if length is not None:
                if not length.isascii() or not length.isdecimal() or int(length) > MAX_BYTES:
                    raise BerlinWFSBlocked("unreviewed WFS response length")
            raw = resp.read(MAX_BYTES + 1)
            if length is not None and len(raw) != int(length):
                raise BerlinWFSBlocked("original WFS Content-Length mismatch")
    except BerlinWFSBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise BerlinWFSBlocked("fixed WFS capabilities request unavailable") from exc
    parsed = inspect_capabilities(raw)
    at = clock()
    if at.tzinfo is None or at.utcoffset() is None:
        raise BerlinWFSBlocked("UTC-aware receipt timestamp required")
    return {
        "profile": "oc-berlin-alkis-wfs-capabilities-one-original-metadata-v0",
        "access_id": ACCESS_ID,
        "retrieved_at_utc": at.astimezone(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(("GET " + URL).encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "access_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        **parsed,
        "raw_provider_bytes_persisted": False,
        "building_geometry_acquired": False,
        "owner_information_acquired": False,
        "scientific_model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="one manually reviewed fixed anonymous XML metadata GET")
    options = parser.parse_args(argv)
    if not options.live:
        parser.error("network disabled by default; use --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (BerlinWFSBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
