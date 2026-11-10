# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-identity and science preflight for one EA 3.3% defended OGC API.

Input: one independently obtained *metadata-only* JSON response from an exact
provider endpoint, selected by --document. No HTTP requests, asset/feature data,
GIS operations, loss estimates, URL following, or source admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MAX_BYTES = 65_536
DATASET_UUID = "767c96e6-b149-4744-9d4d-34b32f6c0e1b"
COLLECTION = "Rivers_1in30_Sea_1in30_defended_depths"
STORAGE_CRS = "http://www.opengis.net/def/crs/EPSG/0/27700"
BBOX_CRS = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
BBOX = [-6.9869611877272115, 49.881385801260535, 2.0755019347798958, 55.810777963189906]
PROFILE = "EA-DEFENDED-3P3-OGC-API-METADATA-PREFLIGHT-v0"
# Original exact response bodies were read via third-party transport on 2026-11-10.
# Hash matching attests exact bytes versus this observation, NOT provider authenticity.
RECEIPTS = {
    "landing": (3863, "84792937c27156e4fc6c79a0aad81abb985b414494c3cd94b7476d273ffe76a1"),
    "conformance": (1910, "89131744b55b74343dd3684d0381f3a024a1ce2b6c9d659752b2ef8ca8181284"),
    "collections": (6448, "633ee4f556b91b235860d0cd430e2a2e66fca37f41a3733bf080555080789349"),
    "collection": (5727, "e3728a3c0f1a37a01c4fdcb80eb66f0b93dc98f8523cdc3c6c9fbed05649a384"),
    "queryables": (1232, "494963373e369d1cfc4e0ebe075d25c6b7424f03899e4eb8a80cc1fdb29e8b11"),
}
EXPECTED_FIELDS = {
    "depth_band": {"type": "string", "description": "string"},
    "flood_source": {"type": "string", "description": "string"},
    "shape_length": {"type": "number", "description": "number"},
    "shape_area": {"type": "number", "description": "number"},
    "shape": {"$ref": "https://geojson.org/schema/Geometry.json"},
}


class EAOgcMetadataError(ValueError):
    """Untrusted source metadata, drift or incorrect spatial semantics."""


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise EAOgcMetadataError("duplicate JSON key")
        obj[key] = value
    return obj


def _bad_constant(value: str) -> None:
    raise EAOgcMetadataError("nonfinite JSON number")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise EAOgcMetadataError("overflowed JSON float")
    return parsed


def _bbox(doc: dict[str, Any]) -> None:
    extent = doc.get("extent")
    spatial = extent.get("spatial") if type(extent) is dict else None
    if type(spatial) is not dict or spatial.get("crs") != BBOX_CRS:
        raise EAOgcMetadataError("missing / wrong CRS84 bounding-box CRS")
    bbox = spatial.get("bbox")
    if type(bbox) is not list or len(bbox) != 1 or bbox[0] != BBOX:
        raise EAOgcMetadataError("published spatial extent differs from pinned metadata")


def _links(doc: dict[str, Any]) -> list[dict[str, Any]]:
    links = doc.get("links")
    if type(links) is not list or not links or any(type(item) is not dict for item in links):
        raise EAOgcMetadataError("missing or malformed OGC metadata links")
    return links


def _has_link(links: list[dict[str, Any]], rel: str, suffix: str) -> bool:
    prefix = "https://environment.data.gov.uk/geoservices/datasets/" + DATASET_UUID + "/ogc/features/v1"
    return any(
        item.get("rel") == rel
        and item.get("type") == "application/json"
        and item.get("href") == prefix + suffix
        for item in links
    )


def inspect_metadata(raw: bytes, document: str) -> dict[str, Any]:
    if document not in RECEIPTS:
        raise EAOgcMetadataError("unknown fixed metadata document")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise EAOgcMetadataError("empty / unbounded metadata input")
    try:
        obj = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object,
            parse_constant=_bad_constant,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EAOgcMetadataError("invalid UTF-8 JSON metadata") from exc
    if type(obj) is not dict or any(key in obj for key in ("features", "items", "geometry", "coordinates")):
        raise EAOgcMetadataError("expected metadata, not geospatial features")
    if document == "landing":
        if (obj.get("title") != "WFS"
            or "Environment Agency" not in str(obj.get("description", "")) 
            or not _has_link(_links(obj), "data", "/collections?f=application%2Fjson")):
            raise EAOgcMetadataError("unexpected OGC landing/service identity")
    elif document == "conformance":
        standards = obj.get("conformsTo")
        if type(standards) is not list or not {
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-2/1.0/conf/crs",
        }.issubset(set(x for x in standards if type(x) is str)):
            raise EAOgcMetadataError("OGC Features core / CRS declarations missing")
        _links(obj)
    elif document == "collections":
        items = obj.get("collections")
        if type(items) is not list or len(items) != 1 or type(items[0]) is not dict:
            raise EAOgcMetadataError("expected exactly one published depth collection")
        if items[0].get("id") != COLLECTION:
            raise EAOgcMetadataError("3.3% defended depth collection identity changed")
        _bbox(items[0])
        _links(obj)
    elif document == "collection":
        if obj.get("id") != COLLECTION or obj.get("storageCrs") != STORAGE_CRS:
            raise EAOgcMetadataError("collection or native EPSG:27700 differs")
        crs = obj.get("crs")
        if type(crs) is not list or not {STORAGE_CRS, BBOX_CRS}.issubset(set(crs)):
            raise EAOgcMetadataError("declared collection coordinate systems changed")
        _bbox(obj)
        _links(obj)
    else:
        if obj.get("type") != "object" or obj.get("properties") != EXPECTED_FIELDS:
            raise EAOgcMetadataError("flood-depth-band fields or exact types differ")
        if obj.get("title") != "Rivers 1In30 Sea 1In30 Defended Depths":
            raise EAOgcMetadataError("queryables title changed")
        _links(obj)
    size, expected = RECEIPTS[document]
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "profile": PROFILE,
        "document": document,
        "dataset_id": DATASET_UUID,
        "collection_id": COLLECTION,
        "source_response_bytes": len(raw),
        "source_response_sha256": digest,
        "matches_original_observed_bytes": (len(raw) == size and digest == expected),
        "provider_authenticity_proven_by_this_parser": False,
        "native_collection_crs": STORAGE_CRS,
        "extent_crs": BBOX_CRS,
        "document_proves_native_storage_crs": document == "collection",
        "document_proves_extent_crs": document in ("collections", "collection"),
        "document_proves_depth_band_field_type": document == "queryables",
        "geographic_coverage_of_actual_features_verified": False,
        "depth_band_text_values_and_millimetre_mapping_verified": False,
        "shape_area_and_length_units_verified": False,
        "depth_band_is_string_not_metres": True,
        "has_verified_unavailable_class_values": False,
        "verified_property_flood_depth": False,
        "actual_provider_features_read": 0,
        "provider_requests_performed": 0,
        "external_resource_links_followed": 0,
        "source_rights_approved": False,
        "model_data_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", required=True, choices=tuple(RECEIPTS))
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        result = inspect_metadata(raw, args.document)
    except (OSError, EAOgcMetadataError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
