#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original-provider ArcGIS *metadata* schema preflight, not source admission.

Caller supplies exact UTF-8 API layer JSON snapshots and independent SHA-256
receipts. This code cannot authenticate the origin of caller-provided bytes;
it never accesses publisher services, rows, geometries or insurer data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_SNAPSHOT_BYTES = 2_000_000
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
PROFILES = {
    "fpa_fod_7": {
        "id": 0,
        "name": "Fire_FPA_FOD_7th_Fires",
        "geometry": "esriGeometryPoint",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0?f=pjson",
        "fields": {
            "fod_id": "esriFieldTypeInteger",
            "fpa_id": "esriFieldTypeString",
            "mtbs_id": "esriFieldTypeString",
            "fire_year": "esriFieldTypeSmallInteger",
            "ics_209_plus_incident_join_id": "esriFieldTypeString",
        },
    },
    "mtbs_perimeters_2024": {
        "id": 82,
        "name": "2024 Burned Area Boundaries",
        "geometry": "esriGeometryPolygon",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82?f=pjson",
        "fields": {
            "fire_id": "esriFieldTypeString",
            "year": "esriFieldTypeSmallInteger",
            "fire_type": "esriFieldTypeString",
            "perim_id": "esriFieldTypeString",
            "map_id": "esriFieldTypeInteger",
        },
    },
}


class OriginalLayerBlocked(ValueError):
    """Required source, schema or byte evidence is missing or inconsistent."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OriginalLayerBlocked("duplicate JSON key")
        result[key] = value
    return result


def _bad_number(value: str):
    raise OriginalLayerBlocked("nonfinite JSON number")


def inspect_layer(blob: bytes, expected_sha256: str, profile: str) -> dict:
    """Check a bounded caller-provided ArcGIS REST metadata snapshot by type."""
    if profile not in PROFILES:
        raise OriginalLayerBlocked("unknown original provider profile")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_SNAPSHOT_BYTES:
        raise OriginalLayerBlocked("empty or oversized original-layer metadata")
    if type(expected_sha256) is not str or not SHA256_RE.fullmatch(expected_sha256):
        raise OriginalLayerBlocked("lowercase 64-character SHA-256 receipt required")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise OriginalLayerBlocked("ArcGIS metadata byte SHA-256 mismatch")
    try:
        payload = json.loads(
            blob.decode("utf-8"), object_pairs_hook=_object, parse_constant=_bad_number
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OriginalLayerBlocked("invalid UTF-8 or ArcGIS JSON metadata") from exc
    if not isinstance(payload, dict) or "error" in payload:
        raise OriginalLayerBlocked("ArcGIS REST error or non-object metadata")
    expected = PROFILES[profile]
    if type(payload.get("id")) is not int or payload["id"] != expected["id"]:
        raise OriginalLayerBlocked("unexpected layer number; do not follow current/latest alias")
    if payload.get("name") != expected["name"]:
        raise OriginalLayerBlocked("provider product/year or edition changed")
    if payload.get("type") != "Feature Layer" or payload.get("geometryType") != expected["geometry"]:
        raise OriginalLayerBlocked("unexpected feature/geometry type")
    sr = payload.get("spatialReference")
    if not isinstance(sr, dict) or type(sr.get("wkid")) is not int or sr["wkid"] != 4269:
        raise OriginalLayerBlocked("original service spatial reference is not NAD83 EPSG:4269")
    fields = payload.get("fields")
    if not isinstance(fields, list) or not 0 < len(fields) <= 200:
        raise OriginalLayerBlocked("ArcGIS field schema absent or unreasonable")
    by_name = {}
    for field in fields:
        if not isinstance(field, dict):
            raise OriginalLayerBlocked("malformed ArcGIS field")
        name, type_name = field.get("name"), field.get("type")
        if (not isinstance(name, str) or not name or not isinstance(type_name, str)
                or not type_name.startswith("esriFieldType")):
            raise OriginalLayerBlocked("malformed ArcGIS field name/type")
        normalized = name.casefold()
        if normalized in by_name:
            raise OriginalLayerBlocked("duplicate case-insensitive field name")
        by_name[normalized] = (name, type_name)
    for required, field_type in expected["fields"].items():
        if required not in by_name:
            raise OriginalLayerBlocked("required original field absent: " + required)
        if by_name[required][1] != field_type:
            raise OriginalLayerBlocked("original field type changed: " + required)

    if profile == "fpa_fod_7":
        # The endpoint is a mutable *current edition* alias; a layer name and
        # apparently correct fields alone NEVER prove archival byte identity.
        source_edition = "FPA_FOD_20260615 (claimed by source layer name only)"
        mapped = {
            "fpa_record_id": by_name["fod_id"][0],
            "mtbs_id": by_name["mtbs_id"][0],
            "fire_year": by_name["fire_year"][0],
        }
    else:
        source_edition = "MTBS 2024 boundary subset (live service; release NOT fixed)"
        mapped = {
            "mtbs_component_id": by_name["perim_id"][0],
            "mtbs_id": by_name["fire_id"][0],
            "fire_year": by_name["year"][0],
            "event_kind": by_name["fire_type"][0],
        }
    return {
        "profile": profile,
        "authoritative_metadata_url_for_independent_receipt": expected["url"],
        "supplied_metadata_sha256": digest,
        "layer_id": expected["id"],
        "layer_name": expected["name"],
        "service_crs": "EPSG:4269",
        "geometry": expected["geometry"],
        "required_field_count": len(expected["fields"]),
        "source_to_research_projection_field_map": mapped,
        "native_layer_profile_valid": True,
        "source_edition_note": source_edition,
        "authenticated_original_publisher_bytes": False,
        "native_row_values_examined": False,
        "native_field_semantics_and_nullability_validated": False,
        "original_source_file_sha256_pinned": False,
        "individual_event_join_proven": False,
        "source_rights_or_cat_admission_granted": False,
    }


def inspect_pair(
    fpa_blob: bytes, fpa_sha256: str,
    mtbs_blob: bytes, mtbs_sha256: str,
) -> dict:
    fpa = inspect_layer(fpa_blob, fpa_sha256, "fpa_fod_7")
    mtbs = inspect_layer(mtbs_blob, mtbs_sha256, "mtbs_perimeters_2024")
    return {
        "audit": "us-wildfire-original-arcgis-metadata-schema-v0",
        "state": "PROVIDED_LAYER_SCHEMA_COMPATIBLE_RESEARCH_ONLY",
        "fpa_fod": fpa,
        "mtbs_2024_boundary": mtbs,
        "crs_transformation_needed_for_same_coordinate_system": False,
        "point_polygon_join_approved": False,
        "value_and_geometric_support_verified": False,
        "source_independence_or_loss_model_fitness_proven": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("fpa", "mtbs"):
        p.add_argument("--" + name + "-metadata", required=True, type=Path)
        p.add_argument("--" + name + "-sha256", required=True)
    a = p.parse_args(argv)
    try:
        for path in (a.fpa_metadata, a.mtbs_metadata):
            if not path.is_file() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
                raise OriginalLayerBlocked("missing or oversized local metadata")
        result = inspect_pair(
            a.fpa_metadata.read_bytes(), a.fpa_sha256,
            a.mtbs_metadata.read_bytes(), a.mtbs_sha256)
    except (OriginalLayerBlocked, OSError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
