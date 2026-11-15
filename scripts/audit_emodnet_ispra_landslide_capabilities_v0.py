#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline identity screen for one EMODnet/ISPRA 1:100k submarine landslide WFS layer.

Reads a locally supplied, separately acquired WFS 2.0 GetCapabilities XML body.
Never executes HTTP, retrieves features, promotes dataset rights or treats the
input SHA as an attested original-provider response. A user must separately
pin exact request, UTC, original bytes, final URL, status and rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SOURCE_ID = "emodnet.geology.geological-events"
WFS_URL = "https://drive.emodnet-geology.eu/geoserver/ispra/wfs?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0"
METADATA_UUID = "ecb22f233db3b5c3dfbe94939df786605a2cac3c"
CANDIDATE_NAMES = frozenset({
    "ispra:landslide_pol_100k", "ispra:landslide_pol_100k_2023",
})
MAX_BYTES = 1024 * 1024
MAX_FEATURE_TYPES = 10000
WFS = "{http://www.opengis.net/wfs/2.0}"
REVIEWED_CRS = frozenset({
    "EPSG:4326",
    "urn:ogc:def:crs:EPSG::4326",
    "http://www.opengis.net/def/crs/EPSG/0/4326",
})


class EMODnetWFSBlocked(ValueError):
    """Input cannot establish one exact, unambiguous reviewed layer identity."""


def inspect_capabilities(raw: bytes) -> dict:
    """Return provenance-limited aggregate metadata; no raw XML or source fields."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise EMODnetWFSBlocked("missing or oversized local WFS capabilities input")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EMODnetWFSBlocked("WFS metadata is not strict UTF-8") from exc
    if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise EMODnetWFSBlocked("forbidden XML NUL, DTD or entity declaration")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise EMODnetWFSBlocked("invalid WFS capabilities XML") from exc
    if root.tag != WFS + "WFS_Capabilities" or root.get("version") != "2.0.0":
        raise EMODnetWFSBlocked("not exact OGC WFS 2.0.0 capabilities")
    features = root.findall(WFS + "FeatureTypeList/" + WFS + "FeatureType")
    if not features or len(features) > MAX_FEATURE_TYPES:
        raise EMODnetWFSBlocked("invalid bounded WFS FeatureType count")
    names: set[str] = set()
    matches: list[tuple[str, ET.Element]] = []
    for feature in features:
        name = feature.findtext(WFS + "Name")
        if not name or name.strip() != name or name in names:
            raise EMODnetWFSBlocked("missing, malformed or duplicate feature type")
        names.add(name)
        if name in CANDIDATE_NAMES:
            matches.append((name, feature))
    if len(matches) != 1:
        raise EMODnetWFSBlocked("missing or ambiguous 100k landslide layer identity")
    layer_name, feature = matches[0]
    title = feature.findtext(WFS + "Title")
    if not title or not all(term in title.casefold() for term in ("landslide", "polygon")):
        raise EMODnetWFSBlocked("candidate layer scientific title mismatch")
    crs = feature.findtext(WFS + "DefaultCRS")
    if crs not in REVIEWED_CRS:
        raise EMODnetWFSBlocked("unreviewed or missing candidate default CRS")
    return {
        "schema": "emodnet-ispra-landslide-100k-wfs-capabilities-screen-v0",
        "source_id": SOURCE_ID,
        "metadata_id": METADATA_UUID,
        "expected_request_url": WFS_URL,
        "candidate_in_local_capabilities": layer_name,
        "layer_count_in_local_capabilities": len(features),
        "sample_input_byte_count": len(raw),
        "sample_input_byte_sha256": hashlib.sha256(raw).hexdigest(),
        "local_capabilities_identity_unambiguous": True,
        "original_provider_response_verified": False,
        "asset_or_feature_bytes_acquired": False,
        "commercial_automation_approved": False,
        "cat_model_input_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capabilities-xml", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.capabilities_xml.open("rb") as stream:
            report = inspect_capabilities(stream.read(MAX_BYTES + 1))
    except (OSError, EMODnetWFSBlocked):
        parser.exit(2, "BLOCKED: exact 1:100k ISPRA landslide WFS identity not proven\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
