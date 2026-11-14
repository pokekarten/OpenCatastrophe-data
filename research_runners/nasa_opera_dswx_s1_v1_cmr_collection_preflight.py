# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, exact-identity preflight for OPERA DSWx-S1 v1 CMR collection metadata.

No network, credentials, downloads, granules, public source bytes, or model
admission. Pass only externally supplied response *bytes* from a separately
approved, fixed CMR request. A passing synthetic test is not a T1 receipt.

CMR Search API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
NASA product: https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

COLLECTION_CONCEPT = "C2949811996-POCLOUD"
PRODUCT = "OPERA_L3_DSWX-S1_V1"
VERSION = "1.0"
MAX_RESPONSE_BYTES = 131072
ALLOWED_MEDIA_TYPES = frozenset({
    "application/json", "application/vnd.nasa.cmr.umm_results+json",
})
# CMR documents a concept_id[] exact collection search. No caller-selectable
# URL, host, page, source ID, spatial or temporal scope is supported here.
FIXED_REQUEST = (
    "https://cmr.earthdata.nasa.gov/search/collections.umm_json"
    "?concept_id%5B%5D=C2949811996-POCLOUD&page_size=1"
)


class CmrCollectionBlocked(ValueError):
    """Response cannot establish the declared bounded collection identity."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CmrCollectionBlocked("duplicate JSON member")
        result[key] = value
    return result


def _no_invalid_constant(_value: str) -> None:
    raise CmrCollectionBlocked("non-JSON numeric constant")


def _has_umm_errors(value: Any) -> bool:
    if type(value) is dict:
        return "_errors" in value or any(_has_umm_errors(v) for v in value.values())
    if type(value) is list:
        return any(_has_umm_errors(v) for v in value)
    return False


def validate_collection_response(
    *, request_url: str, status: int, content_type: str,
    body: bytes, redirect_count: int = 0,
) -> dict[str, object]:
    """Fail closed on a single response's format and exact OPERA identity.

    The caller must separately substantiate the HTTPS transport/DNS/redirect
    safety, rights and API authorization before acquiring any provider bytes.
    Original SHA is over exactly the supplied bytes; no transform is hashed.
    """
    if request_url != FIXED_REQUEST:
        raise CmrCollectionBlocked("request not the fixed CMR collection query")
    if type(status) is not int or status != 200:
        raise CmrCollectionBlocked("unsuccessful HTTP status")
    if type(redirect_count) is not int or redirect_count != 0:
        raise CmrCollectionBlocked("redirected response")
    if type(content_type) is not str or content_type.split(";", 1)[0].strip().lower() not in ALLOWED_MEDIA_TYPES:
        raise CmrCollectionBlocked("unexpected content type")
    if type(body) is not bytes or not 0 < len(body) <= MAX_RESPONSE_BYTES:
        raise CmrCollectionBlocked("body missing, wrong type or over byte budget")
    try:
        value = json.loads(body.decode("utf-8"),
                           object_pairs_hook=_no_duplicate_keys,
                           parse_constant=_no_invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CmrCollectionBlocked("invalid CMR UTF-8 or JSON") from exc
    if type(value) is not dict or type(value.get("hits")) is not int or value["hits"] != 1:
        raise CmrCollectionBlocked("not exactly one search hit")
    items = value.get("items")
    if type(items) is not list or len(items) != 1 or type(items[0]) is not dict:
        raise CmrCollectionBlocked("not exactly one collection record")
    item = items[0]
    meta, umm = item.get("meta"), item.get("umm")
    if type(meta) is not dict or type(umm) is not dict or _has_umm_errors(umm):
        raise CmrCollectionBlocked("missing or invalid UMM record")
    if (meta.get("concept-id") != COLLECTION_CONCEPT
            or meta.get("concept-type") != "collection"
            or meta.get("deleted") is not False
            or type(meta.get("revision-id")) is not int
            or meta["revision-id"] < 1):
        raise CmrCollectionBlocked("mismatched, deleted or unversioned collection")
    if umm.get("ShortName") != PRODUCT or umm.get("Version") != VERSION:
        raise CmrCollectionBlocked("wrong OPERA product or version")
    return {
        "schema_version": "nasa-opera-dswx-s1-cmr-collection-preflight-v0",
        "collection_concept_id": COLLECTION_CONCEPT,
        "product": PRODUCT,
        "product_version": VERSION,
        "cmr_revision_id": meta["revision-id"],
        "original_response_bytes": len(body),
        "original_response_sha256": hashlib.sha256(body).hexdigest(),
        "source_asset_or_granule_acquired": False,
        "dataset_rights_or_api_terms_approved": False,
        "commercial_use_or_redistribution_approved": False,
        "scientific_validity_or_cat_model_admitted": False,
        "neon_storage_verified": False,
    }
