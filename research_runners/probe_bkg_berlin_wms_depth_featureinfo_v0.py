#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original official BKG WMS Berlin depth-layer metadata research; no CAT admission.

One pinned HTTPS GetCapabilities (up to 4 MiB) and, only if the exact
Berlin KOSTRA depth layer is queryable, one fixed 64x64 GetFeatureInfo.
No TIFF source file, building addresses, original WMS payload, feature
values, position results, or other user-selected URLs are persisted.
Neither GetFeatureInfo nor a map legend certifies original Int16 TIFF
depth-unit scale or scientific equivalence across map styles.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
import ssl
from urllib import error, parse, request
from xml.etree import ElementTree as ET

BASE = "https://sgx.geodatenzentrum.de/wms_starkregen"
TARGET_LAYER = "be_tiefe_agw"
MAX_CAPABILITIES_BYTES = 4 * 1024 * 1024
MAX_FEATUREINFO_BYTES = 16 * 1024
WMS_VERSION = "1.3.0"
# Static BKG EPSG:25832 64 x 64 m map square within the existing
# Berlin 200m study envelope; not a named building or entrance.
FIXED_BBOX = "798800,5827950,798864,5828014"
HTTP_TIMEOUT_SECONDS = 30
UNIT_ALIASES = {
    "mm": "millimetres", "millimeter": "millimetres",
    "millimeters": "millimetres", "millimetre": "millimetres",
    "millimetres": "millimetres",
    "cm": "centimetres", "centimeter": "centimetres",
    "centimeters": "centimetres", "centimetre": "centimetres",
    "centimetres": "centimetres",
    "m": "metres", "meter": "metres", "meters": "metres",
    "metre": "metres", "metres": "metres",
}


class BkgWmsBlocked(ValueError):
    """Original service identity or bounded format was unreviewed."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BkgWmsBlocked("BKG WMS redirected away from pinned endpoint")


def _open(req):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context())
    ).open(req, timeout=HTTP_TIMEOUT_SECONDS)


def _uri(params):
    return BASE + "?" + parse.urlencode(params)


def _read_bounded(url: str, *, max_bytes: int, opener=_open):
    if not url.startswith(BASE + "?"):
        raise BkgWmsBlocked("provider URL not pinned")
    try:
        req = request.Request(url, headers={"Accept-Encoding": "identity",
                                             "User-Agent": "OpenCatastrophe-research-WMS/0"})
        with opener(req) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise BkgWmsBlocked("unexpected original BKG WMS status or URL")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise BkgWmsBlocked("unsupported original response transfer coding")
            length = resp.headers.get("Content-Length")
            if length is not None and (not length.isdecimal() or int(length) > max_bytes):
                raise BkgWmsBlocked("original WMS response exceeds byte limit")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in ("text/xml", "application/xml", "application/json",
                             "text/plain", "application/vnd.ogc.wms_xml"):
                raise BkgWmsBlocked("unreviewed original WMS content type")
            raw = resp.read(max_bytes + 1)
            if not raw or len(raw) > max_bytes:
                raise BkgWmsBlocked("empty or oversized original WMS response")
            if length is not None and len(raw) != int(length):
                raise BkgWmsBlocked("truncated original WMS response")
            return raw, media
    except (error.URLError, OSError, TimeoutError) as exc:
        raise BkgWmsBlocked("original BKG WMS unavailable") from exc


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _children(node, name):
    return [x for x in node if _local(x.tag) == name]


def _text(node, name):
    items = _children(node, name)
    return (items[0].text or "").strip() if items else None


def inspect_capabilities(raw: bytes):
    """No DTD, entity expansion or arbitrary features; exact WMS depth layer."""
    if len(raw) > MAX_CAPABILITIES_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise BkgWmsBlocked("DTD, entity or oversized capability XML forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise BkgWmsBlocked("invalid original WMS capabilities XML") from exc
    if _local(root.tag) not in ("WMS_Capabilities", "WMT_MS_Capabilities"):
        raise BkgWmsBlocked("unexpected WMS root")
    cap = _children(root, "Capability")
    if len(cap) != 1:
        raise BkgWmsBlocked("missing or duplicate WMS Capability")
    operations = _children(cap[0], "Request")
    if len(operations) != 1:
        raise BkgWmsBlocked("missing WMS Request operation list")
    feature_formats = set()
    for node in _children(operations[0], "GetFeatureInfo"):
        feature_formats |= {x.text.strip().lower()
                            for x in _children(node, "Format") if x.text}
    parents = _children(cap[0], "Layer")
    if len(parents) != 1:
        raise BkgWmsBlocked("missing WMS root layer")
    found = []
    def recurse(node, inherited=False, depth=0):
        if depth > 15:
            raise BkgWmsBlocked("excessive WMS nested layer depth")
        flag = node.attrib.get("queryable")
        if flag not in (None, "0", "1"):
            raise BkgWmsBlocked("unreviewed WMS queryable property")
        queryable = inherited if flag is None else flag == "1"
        if _text(node, "Name") == TARGET_LAYER:
            found.append(queryable)
        for child in _children(node, "Layer"):
            recurse(child, queryable, depth+1)
    recurse(parents[0])
    if len(found) != 1:
        raise BkgWmsBlocked("expected exactly one Berlin KOSTRA WMS depth layer")
    # application/json and text/plain are independently advertised in the
    # official BKG WMS metadata; do not invent support if not in this response.
    format_used = next((fmt for fmt in ("application/json", "text/plain")
                        if fmt in feature_formats), None) if found[0] else None
    return {
        "original_layer_found": True,
        "exact_layer": TARGET_LAYER,
        "layer_queryable": found[0],
        "supported_featureinfo_format_selected": format_used,
        "provider_declared_units_or_scaling_proven": False,
        "raw_BKG_TIFF_unit_conversion_proven": False,
        "insured_building_loss_admitted": False,
    }


def _recognized_explicit_unit(s):
    if not isinstance(s, str) or len(s) > 40:
        return None
    return UNIT_ALIASES.get(s.strip().lower())


def inspect_feature_info(raw: bytes, content_type: str):
    """Only an explicit metadata field 'unit' is a candidate, never a depth."""
    if len(raw) > MAX_FEATUREINFO_BYTES:
        raise BkgWmsBlocked("too much original WMS feature info")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise BkgWmsBlocked("non-UTF8 original WMS info") from exc
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise BkgWmsBlocked("feature info contains forbidden XML entity markup")
    candidates = set()
    if content_type == "application/json":
        try:
            obj = json.loads(text)
        except (ValueError, TypeError) as exc:
            raise BkgWmsBlocked("original WMS advertised JSON is invalid") from exc
        def walk(item, depth=0):
            if depth > 8:
                raise BkgWmsBlocked("unbounded WMS info object depth")
            if isinstance(item, dict):
                for k, v in item.items():
                    if k.lower() in ("unit", "units", "unittype") and isinstance(v, str):
                        val = _recognized_explicit_unit(v)
                        if val: candidates.add(val)
                    elif isinstance(v, (dict, list)):
                        walk(v, depth+1)
            elif isinstance(item, list):
                if len(item) > 50:
                    raise BkgWmsBlocked("unreviewed number of WMS features")
                for v in item: walk(v, depth+1)
        walk(obj)
    elif content_type == "text/plain":
        for line in text.splitlines():
            match = re.fullmatch(r"\s*(?:unit|units|unittype)\s*[:=]\s*([A-Za-z]+)\s*", line, re.I)
            if match:
                val = _recognized_explicit_unit(match.group(1))
                if val: candidates.add(val)
    else:
        raise BkgWmsBlocked("unreviewed WMS feature-info content type")
    if len(candidates) > 1:
        raise BkgWmsBlocked("conflicting explicit WMS unit metadata")
    return {
        "original_featureinfo_response_sha256_only": sha256(raw).hexdigest(),
        "original_featureinfo_response_bytes": len(raw),
        "explicit_unit_label_candidate_only": next(iter(candidates)) if candidates else None,
        "original_featureinfo_value_or_coordinates_recorded": False,
        "WMS_unit_implies_original_TIFF_Int16_scale": False,
        "building_depth_or_CAT_loss_authorized": False,
    }


def probe(*, opener=_open):
    cap_uri = _uri({"SERVICE": "WMS", "VERSION": WMS_VERSION,
                    "REQUEST": "GetCapabilities"})
    raw, media = _read_bounded(cap_uri, max_bytes=MAX_CAPABILITIES_BYTES, opener=opener)
    if media not in ("text/xml", "application/xml", "application/vnd.ogc.wms_xml"):
        raise BkgWmsBlocked("original WMS GetCapabilities was not XML")
    base = inspect_capabilities(raw)
    receipt = {
        "research_profile": "bkg-berlin-original-wms-kostra-featureinfo-v0",
        "provider": "BKG",
        "provider_service": BASE,
        "original_capabilities_sha256_only": sha256(raw).hexdigest(),
        "original_capabilities_bytes": len(raw),
        **base,
        "WMS_and_original_TIFF_are_not_proven_same_numeric_encoding": True,
        "calibrated_physical_depth_available": False,
        "insurance_cat_model_input_admitted": False,
    }
    if base["supported_featureinfo_format_selected"] is not None:
        fmt = base["supported_featureinfo_format_selected"]
        info_uri = _uri({
            "SERVICE": "WMS", "VERSION": WMS_VERSION, "REQUEST": "GetFeatureInfo",
            "LAYERS": TARGET_LAYER, "QUERY_LAYERS": TARGET_LAYER, "STYLES": "",
            "CRS": "EPSG:25832", "BBOX": FIXED_BBOX,
            "WIDTH": "64", "HEIGHT": "64", "FORMAT": "image/png",
            "INFO_FORMAT": fmt, "I": "32", "J": "32", "FEATURE_COUNT": "1",
        })
        info_raw, info_media = _read_bounded(
            info_uri, max_bytes=MAX_FEATUREINFO_BYTES, opener=opener)
        if info_media != fmt:
            raise BkgWmsBlocked("WMS GetFeatureInfo media type drift")
        receipt["featureinfo"] = inspect_feature_info(info_raw, fmt)
    else:
        receipt["featureinfo"] = {
            "status": "NO_QUERYABLE_OR_SUPPORTED_FORMAT",
            "explicit_unit_label_candidate_only": None,
            "WMS_unit_implies_original_TIFF_Int16_scale": False,
            "building_depth_or_CAT_loss_authorized": False,
        }
    return receipt


def main():
    try:
        result = probe()
    except (BkgWmsBlocked, OSError, ValueError) as exc:
        raise SystemExit("BLOCKED: "+str(exc))
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
