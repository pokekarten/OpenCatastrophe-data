# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline NASA COOLR polygon-layer metadata identity and provenance screen.

T0 only: no provider requests, feature records, geometry, data admission, or
commercial rights decision. Report and inventory polygons cannot be silently
combined as independent landslide events.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

SOURCE_ID = "nasa.coolr.landslides"
MAX_METADATA_BYTES = 131_072
LAYERS = {
    "reports_polygon": {
        "name": "egdb.sde.nasa_coolr_reports_poly",
        "identity": "COOLR_Reports_Polygons/FeatureServer/0",
        "required": {
            "objectid": "esriFieldTypeOID", "event_id": "esriFieldTypeInteger",
            "event_date": "esriFieldTypeDate", "source_name": "esriFieldTypeString",
            "source_link": "esriFieldTypeString", "event_import_source": "esriFieldTypeString",
            "event_import_id": "esriFieldTypeString", "latitude": "esriFieldTypeDouble",
            "longitude": "esriFieldTypeDouble",
        },
        "excluded": {"citation", "method"},
    },
    "events_polygon": {
        "name": "egdb.sde.nasa_coolr_events_poly",
        "identity": "COOLR_Events_Polygons/FeatureServer/0",
        "required": {
            "objectid": "esriFieldTypeOID", "event_id": "esriFieldTypeInteger",
            "event_date": "esriFieldTypeDate", "source_name": "esriFieldTypeString",
            "source_link": "esriFieldTypeString", "citation": "esriFieldTypeString",
            "method": "esriFieldTypeString", "landslide_trigger": "esriFieldTypeString",
            "latitude": "esriFieldTypeDouble", "longitude": "esriFieldTypeDouble",
        },
        "excluded": {"event_import_source", "event_import_id"},
    },
}
FIELD_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")


class CoolrMetadataError(ValueError):
    """Unsafe, missing, or ambiguous NASA layer metadata."""


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise CoolrMetadataError("duplicate JSON key")
        result[name] = value
    return result


def _nonfinite(_: str) -> None:
    raise CoolrMetadataError("nonfinite JSON number")


def _coordinate(value: object, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CoolrMetadataError("invalid geographic bounding coordinate")
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise CoolrMetadataError("unrepresentable geographic coordinate") from exc
    if not math.isfinite(number) or not lower <= number <= upper:
        raise CoolrMetadataError("coordinate outside longitude/latitude bounds")
    return number


def screen_coolr_polygon_layer_metadata(original: bytes, *, layer_kind: str) -> dict[str, object]:
    """Validate a separately obtained ArcGIS *layer metadata* response only.

    The caller must pin the exact NASA service/layer request beforehand. The
    supplied bytes' SHA-256 does not independently establish provider origin.
    """
    if not isinstance(layer_kind, str) or layer_kind not in LAYERS:
        raise CoolrMetadataError("unknown COOLR product/layer identity")
    if not isinstance(original, bytes) or not 0 < len(original) <= MAX_METADATA_BYTES:
        raise CoolrMetadataError("empty or oversized metadata bytes")
    try:
        obj = json.loads(original.decode("utf-8", "strict"),
                         object_pairs_hook=_pairs_unique, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise CoolrMetadataError("unreadable ArcGIS metadata JSON") from exc
    cfg = LAYERS[layer_kind]
    if not isinstance(obj, dict) or obj.get("error") is not None:
        raise CoolrMetadataError("ArcGIS error instead of layer metadata")
    if (obj.get("id") != 0 or isinstance(obj.get("id"), bool) or
            obj.get("name") != cfg["name"] or obj.get("type") != "Feature Layer" or
            obj.get("geometryType") != "esriGeometryPolygon"):
        raise CoolrMetadataError("COOLR layer identity or geometry mismatch")
    oid_field = obj.get("objectIdField", "objectid")
    if not isinstance(oid_field, str) or oid_field.lower() != "objectid":
        raise CoolrMetadataError("unrecognized ObjectID field")
    if any(obj.get(key) is not None and obj.get(key) is not False for key in ("hasZ", "hasM")):
        raise CoolrMetadataError("unexpected 3D or measure geometry")
    if obj.get("isDataVersioned") is not None and obj.get("isDataVersioned") is not False:
        raise CoolrMetadataError("unexpected historical-version semantics")
    if obj.get("supportsQueryWithHistoricMoment") is not None and obj.get("supportsQueryWithHistoricMoment") is not False:
        raise CoolrMetadataError("unexpected historic-moment capability")
    caps = obj.get("capabilities")
    if not isinstance(caps, str) or "Query" not in {x.strip() for x in caps.split(",")}:
        raise CoolrMetadataError("layer lacks the documented Query operation")
    count = obj.get("maxRecordCount")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 2000:
        raise CoolrMetadataError("provider record-cap contract changed")
    ext = obj.get("extent")
    if not isinstance(ext, dict) or not isinstance(ext.get("spatialReference"), dict):
        raise CoolrMetadataError("missing EPSG:4326 geographic extent")
    sr = ext["spatialReference"]
    if sr.get("wkid") != 4326 or isinstance(sr.get("wkid"), bool):
        raise CoolrMetadataError("COOLR polygon extent CRS no longer EPSG:4326")
    xmin = _coordinate(ext.get("xmin"), -180, 180)
    xmax = _coordinate(ext.get("xmax"), -180, 180)
    ymin = _coordinate(ext.get("ymin"), -90, 90)
    ymax = _coordinate(ext.get("ymax"), -90, 90)
    if not (xmin < xmax and ymin < ymax):
        raise CoolrMetadataError("empty or inverted geographic extent")
    fields = obj.get("fields")
    if not isinstance(fields, list) or not len(cfg["required"]) <= len(fields) <= 100:
        raise CoolrMetadataError("missing or oversized feature-field inventory")
    inventory: dict[str, str] = {}
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("name"), str) or not isinstance(field.get("type"), str):
            raise CoolrMetadataError("malformed ArcGIS field")
        field_name = field["name"]
        if not FIELD_NAME.fullmatch(field_name) or field_name.lower() in inventory:
            raise CoolrMetadataError("unsafe or duplicate ArcGIS field name")
        if not field["type"].startswith("esriFieldType") or len(field["type"]) > 48:
            raise CoolrMetadataError("unrecognized ArcGIS field type")
        inventory[field_name.lower()] = field["type"]
    if any(inventory.get(field) != field_type for field, field_type in cfg["required"].items()):
        raise CoolrMetadataError("missing required report/event lineage field or field-type mismatch")
    if cfg["excluded"].intersection(inventory):
        raise CoolrMetadataError("cross-product report/event fields present")
    return {
        "source_id": SOURCE_ID,
        "layer_kind": layer_kind,
        "documented_layer_identity": cfg["identity"],
        "original_caller_supplied_metadata_sha256": hashlib.sha256(original).hexdigest(),
        "input_metadata_bytes": len(original),
        "required_field_types_screened": len(cfg["required"]),
        "other_fields_not_used_or_admitted": len(fields) - len(cfg["required"]),
        "polygon_crs": "EPSG:4326",
        "report_records_observed": False,
        "event_inventory_records_observed": False,
        "report_event_deduplication_proven": False,
        "actual_geometries_checked": False,
        "contributor_citations_verified": False,
        "provider_byte_provenance_verified": False,
        "dataset_or_api_commercial_rights_verified": False,
        "cat_model_input_admitted": False,
        "neon_storage": "not_performed",
    }
