#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three bounded Berlin official SRGK WFS metadata operations only.

Independent of the original GetFeature pilot/geometry probe. This does
NOT repair source BBOX behavior, infer coverage/absence of flooding, or
retrieve spatial features. No user URLs, source polygons, source original
payloads, building identifiers, insurer exposures, losses or DB writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
import ssl
import sys
from urllib import error, parse, request
from xml.etree import ElementTree as ET

BASE = "https://gdi.berlin.de/services/wfs/ua_srgk"
LAYER = "ua_srgk:a_modellgebiete"
BBOX = "391700,5819950,391900,5820150,EPSG:25833"
BASE_PARAMS = (("service", "WFS"), ("version", "2.0.0"))
SRS = "EPSG:25833"
SCHEMA_URL = BASE + "?" + parse.urlencode(BASE_PARAMS + (
    ("request", "DescribeFeatureType"), ("typeNames", LAYER),
))
HITS_PARAMS = BASE_PARAMS + (
    ("request", "GetFeature"), ("typeNames", LAYER),
    ("resultType", "hits"), ("srsName", SRS), ("count", "1"),
)
CONTROL_HITS_URL = BASE + "?" + parse.urlencode(HITS_PARAMS)
PILOT_HITS_URL = BASE + "?" + parse.urlencode(HITS_PARAMS + (("bbox", BBOX),))
CAPS = {SCHEMA_URL: 512 * 1024, CONTROL_HITS_URL: 16 * 1024,
        PILOT_HITS_URL: 16 * 1024}
MAX_FIELDS = 50
MAX_FIELD_NAME = 90
SAFE_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z_0-9.-]{0,89}$")
PROFILE = "berlin-srgk-fixed-model-area-wfs-schema-hits-v0"


class MetadataBlocked(ValueError):
    """Source returned ambiguous, untrusted or unsupported metadata."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MetadataBlocked("official Berlin WFS redirected")


def _open(req):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context())
    ).open(req, timeout=40)


def _fetch(url, *, opener=_open):
    if url not in CAPS:
        raise MetadataBlocked("unapproved metadata request")
    max_bytes = CAPS[url]
    req = request.Request(url, method="GET",
                          headers={"Accept": "application/xml,text/xml",
                                   "Accept-Encoding": "identity"})
    try:
        with opener(req) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise MetadataBlocked("original WFS status or redirect")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise MetadataBlocked("unreviewed transfer encoding")
            declared = resp.headers.get("Content-Length")
            if declared is not None:
                if not declared.isdecimal() or int(declared) > max_bytes:
                    raise MetadataBlocked("declared response too large")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/xml", "text/xml", "application/gml+xml",
                             "application/xsd+xml", "text/plain"):
                raise MetadataBlocked("unexpected source metadata content type")
            raw = resp.read(max_bytes + 1)
            if not raw or len(raw) > max_bytes:
                raise MetadataBlocked("original metadata empty or exceeds cap")
            if declared is not None and len(raw) != int(declared):
                raise MetadataBlocked("truncated official metadata")
            return raw
    except (error.URLError, TimeoutError, OSError) as exc:
        raise MetadataBlocked("original official Berlin WFS unavailable") from exc


def _xml(raw):
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= max(CAPS.values())
            or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper()):
        raise MetadataBlocked("invalid XML size or forbidden entity/DTD")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise MetadataBlocked("invalid original WFS XML") from exc


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _safe_name(name):
    return isinstance(name, str) and SAFE_NAME.fullmatch(name) is not None


def inspect_schema(raw):
    """Check XSD shape and list only public field names/possible geometry fields."""
    root = _xml(raw)
    if _local(root.tag) != "schema":
        raise MetadataBlocked("DescribeFeatureType is not XML Schema")
    elements = [e for e in root.iter() if _local(e.tag) == "element"]
    if not 1 <= len(elements) <= MAX_FIELDS:
        raise MetadataBlocked("unreviewed schema element count")
    field_names = [e.attrib["name"] for e in elements if "name" in e.attrib]
    if not field_names or not all(_safe_name(x) for x in field_names):
        raise MetadataBlocked("unreviewed WFS field names")
    candidates = sorted({
        e.attrib["name"]
        for e in elements
        if "name" in e.attrib
        and "gml:" in e.attrib.get("type", "").lower()
        and any(k in e.attrib.get("type", "").lower()
                for k in ("geometry", "polygon", "surface", "multisurface"))
    })
    if len(candidates) > 5:
        raise MetadataBlocked("unreviewed number of geometry candidates")
    return {
        "schema_is_wellformed_xsd": True,
        "named_schema_elements_count": len(field_names),
        "geometry_property_name_candidates": candidates,
        "geometry_property_type_proven_for_filter": False,
        "filter_capabilities_and_server_bbox_behavior_proven": False,
        "geometry_downloaded_or_stored": False,
    }


def _matched(value):
    if value == "unknown":
        return None
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value) if len(value) <= 12 else None
    raise MetadataBlocked("invalid hits matched count")


def inspect_hits(raw):
    """Validate count-only WFS response and reject any returned feature geometry."""
    root = _xml(raw)
    if _local(root.tag) != "FeatureCollection":
        raise MetadataBlocked("unexpected original WFS hits response")
    if any(_local(node.tag) in ("member", "featureMember", "featureMembers")
           for node in root.iter()):
        raise MetadataBlocked("count-only response unexpectedly contains source features")
    count = root.attrib.get("numberReturned")
    if count is not None and count not in ("0", 0):
        raise MetadataBlocked("hits request returned positive features")
    matched = _matched(root.attrib.get("numberMatched", "unknown"))
    return {"number_matched": matched, "original_count_only": True,
            "no_source_feature_or_coordinates_read": True}


def classify_counts(control, pilot):
    """Counts alone never prove spatial coverage or provider filtering."""
    c, p = control["number_matched"], pilot["number_matched"]
    if c is not None and p is not None and p > c:
        raise MetadataBlocked("filtered WFS matched more than full control")
    if c == 0:
        return "SOURCE_CONTROL_ZERO_NO_SPATIAL_ASSERTION"
    if c is None or p is None:
        return "COUNT_UNRESOLVED_NO_SPATIAL_ASSERTION"
    if p == 0:
        return "PILOT_HITS_ZERO_NOT_A_PROVEN_COVERAGE_OR_DRYNESS"
    return "PILOT_HITS_POSITIVE_REQUIRES_EXACT_GEOMETRY_INTERSECTION"


def probe(*, opener=_open, clock=lambda: datetime.now(timezone.utc)):
    sources = []
    for url in (SCHEMA_URL, CONTROL_HITS_URL, PILOT_HITS_URL):
        raw = _fetch(url, opener=opener)
        sources.append((raw, {"bytes": len(raw), "full_response_sha256": sha256(raw).hexdigest()}))
    schema = inspect_schema(sources[0][0])
    control = inspect_hits(sources[1][0])
    pilot = inspect_hits(sources[2][0])
    state = classify_counts(control, pilot)
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise MetadataBlocked("timezone-aware timestamp required")
    return {
        "profile": PROFILE,
        "original_service": BASE,
        "exact_feature_type": LAYER,
        "fixed_pilot_bbox_epsg25833": [391700, 5819950, 391900, 5820150],
        "timestamp_utc": now.astimezone(timezone.utc).isoformat(),
        "schema_metadata": sources[0][1],
        "control_hits_metadata": sources[1][1],
        "pilot_hits_metadata": sources[2][1],
        "schema_summary": schema,
        "control_hits_match_count": control["number_matched"],
        "pilot_hits_match_count": pilot["number_matched"],
        "source_count_comparison_status": state,
        "original_source_xml_or_feature_geometries_persisted": False,
        "original_WFS_bbox_honored_proven": False,
        "pilot_covered_or_not_covered_proven": False,
        "flood_depth_or_Cat_loss_inferred": False,
        "model_input_admitted": False,
    }


def main():
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (MetadataBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
