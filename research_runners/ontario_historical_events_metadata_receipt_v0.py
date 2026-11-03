#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original-byte receipt for Ontario historical event ArcGIS layer metadata.

This script performs NO network access and NO feature queries. It does not
download geometries, text descriptions, property locations or insured losses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "ca.ontario.mnr.emergency-historical-events"
DOCUMENTATION_URL = "https://open.canada.ca/data/en/dataset/3ddd1967-a5a1-47b2-b3b9-554495581ea2"
ORIGINAL_METADATA_URL = (
    "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/"
    "LIO_OPEN_DATA/LIO_Open05/MapServer/20?f=pjson"
)
MAX_BYTES = 131072
EXPECTED_FIELDS = {
    "OGF_ID": "esriFieldTypeDouble",
    "EVENT_TYPE": "esriFieldTypeString",
    "EVENT_YEAR": "esriFieldTypeSmallInteger",
    "EVENT_NUMBER": "esriFieldTypeString",
    "LOCATION_ACCURACY": "esriFieldTypeString",
    "SHAPE": "esriFieldTypeGeometry",
    "OBJECTID": "esriFieldTypeOID",
}
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class Blocked(ValueError):
    """Fail closed when metadata identity, shape or original bytes are uncertain."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise Blocked("duplicate metadata JSON key")
        out[key] = value
    return out


def _nonfinite(value: str) -> None:
    raise Blocked("non-finite metadata number")


def inspect(original: bytes) -> dict[str, object]:
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise Blocked("empty or oversized original metadata")
    try:
        value = json.loads(
            original.decode("utf-8-sig"), object_pairs_hook=_strict_object,
            parse_constant=_nonfinite,
        )
    except (UnicodeError, ValueError) as exc:
        raise Blocked("invalid strict provider JSON") from exc
    if not isinstance(value, dict) or "error" in value or "features" in value:
        raise Blocked("expected a single layer metadata object without feature rows")
    if value.get("id") != 20 or type(value.get("id")) is not int:
        raise Blocked("wrong ArcGIS layer id")
    if value.get("name") != "Emergency Management Historical Event":
        raise Blocked("wrong Ontario historical event product")
    if value.get("type") != "Feature Layer":
        raise Blocked("unexpected ArcGIS layer type")
    if value.get("geometryType") != "esriGeometryMultipoint":
        raise Blocked("geometry must be multipoint, not an event damage polygon")
    srs = value.get("sourceSpatialReference")
    if not isinstance(srs, dict) or srs.get("wkid") != 4269:
        raise Blocked("unverified NAD83 source spatial reference")
    fields = value.get("fields")
    if not isinstance(fields, list) or not 1 <= len(fields) <= 128:
        raise Blocked("missing or excessive provider field definitions")
    actual: dict[str, str] = {}
    for field in fields:
        if not isinstance(field, dict):
            raise Blocked("invalid field definition")
        name, kind = field.get("name"), field.get("type")
        if not isinstance(name, str) or not name or name in actual:
            raise Blocked("duplicate or invalid provider field name")
        if not isinstance(kind, str) or not kind.startswith("esriFieldType"):
            raise Blocked("invalid provider field type")
        actual[name] = kind
    for name, kind in EXPECTED_FIELDS.items():
        if actual.get(name) != kind:
            raise Blocked("missing or changed field type: " + name)
    if value.get("displayField") != "EVENT_TYPE":
        raise Blocked("unexpected displayed event type")
    return {
        "candidate_id": SOURCE_ID,
        "layer_id": 20,
        "source_wkid": 4269,
        "geometry_type": "esriGeometryMultipoint",
        "field_count": len(fields),
        "required_fields_checked": sorted(EXPECTED_FIELDS),
        "event_year_field_observed": True,
        "event_type_field_observed": True,
        "event_number_field_observed": True,
        "event_id_crosswalk_verified": False,
        "single_event_polygon_available": False,
        "loss_quantities_verified": False,
        "individual_feature_rows_requested": False,
        "dataset_rights_admitted": False,
        "model_input_admitted": False,
    }


def verify(path: Path, expected_sha256: str) -> dict[str, object]:
    if not SHA_RE.fullmatch(expected_sha256):
        raise Blocked("expected SHA-256 must be 64 lowercase hexadecimal characters")
    with path.open("rb") as stream:
        original = stream.read(MAX_BYTES + 1)
    if not original or len(original) > MAX_BYTES:
        raise Blocked("empty or oversized original metadata")
    actual_hash = hashlib.sha256(original).hexdigest()
    if actual_hash != expected_sha256:
        raise Blocked("original provider metadata SHA-256 mismatch")
    result = inspect(original)
    return {
        "receipt_profile": "ontario-historical-events-original-metadata-v0",
        "documentation_url": DOCUMENTATION_URL,
        "expected_metadata_url": ORIGINAL_METADATA_URL,
        "external_original_bytes": len(original),
        "external_original_sha256": actual_hash,
        "offline_original_bytes_checked": True,
        "source_raw_bytes_committed": False,
        **result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-json", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(args.original_json, args.expected_sha256)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
