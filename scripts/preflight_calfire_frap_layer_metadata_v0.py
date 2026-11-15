# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline metadata-only preflight for pinned CAL FIRE FRAP firep25_1 layer 0.

The input must be an independently obtained, separately authorized original
ArcGIS layer-metadata JSON document. This script does not issue HTTP requests,
read fire polygons or incident features, or authorize any data acquisition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_METADATA_BYTES = 524_288
LAYER_NAME = "California_Fire_Perimeters__all_"
REQUIRED_FIELDS = {
    "OBJECTID": "esriFieldTypeOID",
    "YEAR_": "esriFieldTypeSmallInteger",
    "UNIT_ID": "esriFieldTypeString",
    "FIRE_NAME": "esriFieldTypeString",
    "INC_NUM": "esriFieldTypeString",
    "IRWINID": "esriFieldTypeString",
    "ALARM_DATE": "esriFieldTypeDate",
    "CONT_DATE": "esriFieldTypeDate",
    "GlobalID": "esriFieldTypeGlobalID",
}
UNSAFE_PAYLOAD_KEYS = frozenset({
    "features", "feature", "results", "edits", "attachments", "records", "geometry",
})


class FrapMetadataError(ValueError):
    """Wrong source, drifting metadata schema, or prohibited feature data."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise FrapMetadataError("duplicate JSON key")
        out[key] = value
    return out


def _nonfinite(value: str) -> None:
    raise FrapMetadataError("nonfinite JSON constant")


def preflight_frap_layer(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_METADATA_BYTES):
        raise FrapMetadataError("layer metadata exceeds bounded byte contract")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FrapMetadataError("input must be original UTF-8 ArcGIS layer metadata JSON") from exc
    if type(payload) is not dict or UNSAFE_PAYLOAD_KEYS.intersection(payload):
        raise FrapMetadataError("not a metadata-only layer object")
    if (
        type(payload.get("id")) is not int or payload["id"] != 0
        or payload.get("name") != LAYER_NAME
        or payload.get("type") != "Feature Layer"
        or payload.get("geometryType") != "esriGeometryPolygon"
        or payload.get("objectIdField") != "OBJECTID"
        or payload.get("globalIdField") != "GlobalID"
    ):
        raise FrapMetadataError("wrong FRAP layer identity, object IDs, or geometry")
    extent = payload.get("extent")
    if type(extent) is not dict or type(extent.get("spatialReference")) is not dict:
        raise FrapMetadataError("missing original layer CRS")
    sr = extent["spatialReference"]
    if type(sr.get("wkid")) is not int or sr["wkid"] not in (102100, 3857):
        raise FrapMetadataError("FRAP service view CRS drift; do not assume EPSG3310")
    latest = sr.get("latestWkid")
    if latest is not None and (type(latest) is not int or latest != 3857):
        raise FrapMetadataError("layer CRS alias inconsistent with Web Mercator")
    time_info = payload.get("timeInfo")
    if (
        type(time_info) is not dict
        or time_info.get("startTimeField") != "ALARM_DATE"
        or time_info.get("endTimeField") != "CONT_DATE"
    ):
        raise FrapMetadataError("original event discovery and containment time fields changed")
    fields = payload.get("fields")
    if type(fields) is not list or not fields:
        raise FrapMetadataError("no source field descriptors")
    types: dict[str, str] = {}
    for field in fields:
        if type(field) is not dict:
            raise FrapMetadataError("non-object field descriptor")
        name, kind = field.get("name"), field.get("type")
        if type(name) is not str or not (0 < len(name) <= 128) or type(kind) is not str or not kind:
            raise FrapMetadataError("invalid name/type descriptor")
        if name in types:
            raise FrapMetadataError("duplicate field name")
        types[name] = kind
    for name, expected in REQUIRED_FIELDS.items():
        if types.get(name) != expected:
            raise FrapMetadataError("required original field missing/type drift: " + name)
    return {
        "contract": "CALFIRE-FRAP-FIREP25-1-LAYER0-METADATA-PREFLIGHT-v0",
        "layer_name": LAYER_NAME,
        "layer_id": 0,
        "source_candidate_id": "us.calfire.frap.historical-fire-perimeters.firep25-1",
        "input_metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "input_metadata_bytes": len(raw),
        "field_count": len(types),
        "year_field_type": types["YEAR_"],
        "gis_view_crs_wkid": sr["wkid"],
        "source_time_fields": ["ALARM_DATE", "CONT_DATE"],
        "feature_rows_read": 0,
        "fire_perimeter_geometry_read": False,
        "provider_revision_verified": False,
        "provider_original_bytes_attested_by_preflight": False,
        "event_to_dins_identity_proven": False,
        "external_source_use_authorized": False,
        "model_data_admitted": False,
        "scientific_warning": (
            "Official current ArcGIS view YEAR_ is SmallInteger, whereas the older "
            "2023 FRAP fire-history dictionary says Text; source version and layer "
            "schema cannot be substituted. Web Mercator view is not the native "
            "geodatabase's historical CRS; final perimeters are not fire intensity."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            data = stream.read(MAX_METADATA_BYTES + 1)
        result = preflight_frap_layer(data)
    except (OSError, FrapMetadataError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
