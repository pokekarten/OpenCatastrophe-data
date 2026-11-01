#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only OGC WMS capabilities metadata, never building or roof features.

This checks a small official 2025 solar service capabilities response only.
Even a queryable WMS is not necessarily a reusable vector-data download.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

MAX_BYTES = 2_000_000
MAX_LAYERS = 500
ROOF_KEYWORDS = ("dach", "roof", "toiture", "facet", "teilfl", "solar")


class WMSMetadataError(ValueError):
    """WMS response cannot be used as verified service capability evidence."""


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def child(parent: ET.Element, name: str):
    return next((x for x in parent if localname(x.tag) == name), None)


def descendants(parent: ET.Element, name: str):
    return (x for x in parent.iter() if localname(x.tag) == name)


def node_text(parent: ET.Element, name: str) -> str:
    node = child(parent, name)
    return ((node.text or "").strip() if node is not None else "")[:240]


def parse_capabilities(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not 80 <= len(raw) <= MAX_BYTES:
        raise WMSMetadataError("Missing, empty or oversized WMS metadata body")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise WMSMetadataError("XML DTD and entity definitions are forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise WMSMetadataError("Invalid WMS XML") from exc
    if localname(root.tag) not in ("WMS_Capabilities", "WMT_MS_Capabilities"):
        raise WMSMetadataError("Not a WMS capabilities response")
    version = root.attrib.get("version", "")
    if version not in ("1.1.1", "1.3.0"):
        raise WMSMetadataError("Unexpected WMS service version")
    capability = child(root, "Capability")
    if capability is None:
        raise WMSMetadataError("Missing WMS Capability section")
    request = child(capability, "Request")
    if request is None:
        raise WMSMetadataError("Missing WMS Request section")
    format_info = []
    fi = child(request, "GetFeatureInfo")
    if fi is not None:
        format_info = sorted(set((x.text or "").strip() for x in descendants(fi, "Format") if (x.text or "").strip()))
    root_layer = child(capability, "Layer")
    if root_layer is None:
        raise WMSMetadataError("Missing WMS root layer")
    names = set()
    layers = []

    def walk(layer: ET.Element, parent_queryable: bool, depth: int):
        if depth > 12 or len(layers) >= MAX_LAYERS:
            raise WMSMetadataError("Unbounded WMS layer tree")
        queryable = (layer.get("queryable", "1" if parent_queryable else "0") == "1")
        name, title = node_text(layer, "Name"), node_text(layer, "Title")
        if name:
            if name in names:
                raise WMSMetadataError("Repeated WMS layer name")
            names.add(name)
            crs = sorted(set((x.text or "").strip() for x in layer
                             if localname(x.tag) in ("CRS", "SRS") and (x.text or "").strip()))
            matched = any(term in (title + " " + name).casefold() for term in ROOF_KEYWORDS)
            layers.append({
                "layer_name": name[:120],
                "title": title,
                "queryable_advertised": queryable,
                "coordinate_reference_systems_declared_locally": crs[:20],
                "roof_related_name_candidate": matched,
            })
        for x in layer:
            if localname(x.tag) == "Layer":
                walk(x, queryable, depth + 1)

    walk(root_layer, False, 0)
    if not layers:
        raise WMSMetadataError("No named layer advertised")
    service = child(root, "Service")
    title = node_text(service, "Title") if service is not None else ""
    return {
        "schema_version": "lu-2025-solar-wms-capability-audit-v0",
        "wms_version": version,
        "service_title": title,
        "named_layer_count": len(layers),
        "get_feature_info_advertised": fi is not None,
        "get_feature_info_formats": format_info[:30],
        "named_layers": layers,
        "roof_name_candidates": [x["layer_name"] for x in layers if x["roof_related_name_candidate"]],
        "actual_roof_tilt_aspect_data_read": False,
        "vector_download_supported_verified": False,
        "featureinfo_response_verified": False,
        "source_rights_for_reuse_verified": False,
        "model_input_admitted": False,
        "interpretation": (
            "Advertised map layers/queryability are service metadata only. "
            "WMS GetMap raster != original building features; GetFeatureInfo advertised "
            "does not prove an actual accessible attribute response or bulk rights. "
            "Do not infer tilt/aspect/area3d values or a building join."
        ),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capabilities", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        f = args.capabilities
        if not f.is_file() or f.is_symlink() or not 80 <= f.stat().st_size <= MAX_BYTES:
            raise WMSMetadataError("Local input must be a bounded nonsymlink XML file")
        result = parse_capabilities(f.read_bytes())
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2))
    except (OSError, WMSMetadataError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
