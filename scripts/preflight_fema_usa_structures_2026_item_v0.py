#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only original metadata preflight for FEMA USA Structures 2026 Esri view.

The caller supplies previously obtained *original* public JSON bodies.
No HTTP client, feature query, pagination, export, upload or model admission.
The published federal layer must not be confused with a regional ArcGIS service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SOURCE_ID = "fema.usa-structures"
ITEM_ID = "0ec8512ad21e4bb987d7e848d14e7e24"
SERVICE = (
    "https://services2.arcgis.com/FiaPA4ga0iQKduv3/"
    "arcgis/rest/services/USA_Structures_View/FeatureServer"
)
WRONG_REGIONAL_ITEM_ID = "a51353d9b1d14b2ea3dc2f2eefb220d3"
MAX_BYTES = 65536


class StructuresMetadataBlocked(ValueError):
    """Unexpected official source identity, revision, bytes or semantics."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for k, v in pairs:
        if k in result:
            raise StructuresMetadataBlocked("duplicate metadata JSON key")
        result[k] = v
    return result


def _nonfinite(value: str) -> None:
    raise StructuresMetadataBlocked("non-finite source number")


def _load(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise StructuresMetadataBlocked("metadata original bytes outside exact 64KiB limit")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StructuresMetadataBlocked("metadata is not strict UTF-8 JSON") from exc
    if type(doc) is not dict or "error" in doc:
        raise StructuresMetadataBlocked("provider metadata object missing or error")
    return doc


def inspect_source_item_and_view(item_raw: bytes, view_raw: bytes) -> dict[str, Any]:
    item = _load(item_raw)
    view = _load(view_raw)
    if (
        item.get("id") != ITEM_ID
        or item.get("type") != "Feature Service"
        or item.get("owner") != "Esri_US_Federal_Data"
        or item.get("access") != "public"
        or item.get("url") != SERVICE
        or type(item.get("licenseInfo")) is not str
        or "CC BY 4.0" not in item["licenseInfo"]
    ):
        raise StructuresMetadataBlocked("national public item identity or CC-BY label drift")

    if view.get("serviceItemId") != ITEM_ID or view.get("serviceItemId") == WRONG_REGIONAL_ITEM_ID:
        raise StructuresMetadataBlocked("service is not the national linked Esri public item")
    extent = view.get("fullExtent")
    if type(extent) is not dict:
        raise StructuresMetadataBlocked("missing national view full extent")
    spatial = extent.get("spatialReference")
    if (
        type(spatial) is not dict
        or spatial.get("latestWkid") != 3857
        or any(type(extent.get(x)) not in (float, int) for x in ("xmin", "ymin", "xmax", "ymax"))
        or any(not math.isfinite(extent[x]) for x in ("xmin", "ymin", "xmax", "ymax"))
        or not (extent["xmin"] < -1e7 and extent["xmax"] > 1e7)
        or not (extent["ymin"] < 0 < extent["ymax"])
    ):
        raise StructuresMetadataBlocked("extent is regional, non-worldwide or malformed")

    layers = view.get("layers")
    if (
        type(layers) is not list
        or len(layers) != 1
        or type(layers[0]) is not dict
        or layers[0].get("id") != 0
        or layers[0].get("name") != "USA_Structures_A"
        or layers[0].get("type") != "Feature Layer"
        or layers[0].get("geometryType") != "esriGeometryPolygon"
    ):
        raise StructuresMetadataBlocked("public view layer identity or geometry drift")
    return {
        "schema": "fema-usa-structures-original-public-view-metadata-preflight-v0",
        "source_id": SOURCE_ID,
        "published_2026_public_item_id": ITEM_ID,
        "service_item_identity_matches": True,
        "published_item_cc_by_4_label": True,
        "full_extent_wkid": 3857,
        "layer_id": 0,
        "layer_name": "USA_Structures_A",
        "item_response_bytes": len(item_raw),
        "item_response_sha256": hashlib.sha256(item_raw).hexdigest(),
        "view_response_bytes": len(view_raw),
        "view_response_sha256": hashlib.sha256(view_raw).hexdigest(),
        "original_provider_bytes_persisted": False,
        "provider_features_read": 0,
        "commercial_bulk_api_permission_verified": False,
        "source_data_or_model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-json", type=Path, required=True)
    parser.add_argument("--service-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.item_json.open("rb") as f:
            item = f.read(MAX_BYTES + 1)
        with args.service_json.open("rb") as f:
            view = f.read(MAX_BYTES + 1)
        result = inspect_source_item_and_view(item, view)
    except (OSError, StructuresMetadataBlocked) as exc:
        # Do not include any original provider JSON in logs.
        parser.exit(2, "BLOCKED: original source item/view identity or bounds\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
