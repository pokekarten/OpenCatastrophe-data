# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded source-metadata-only canary for the NRW LoD2 OGC API collection.

No feature/item/bbox/raster requests, arbitrary URLs, authentication, pagination,
credentials, raw records or model inputs. All provider bytes remain ephemeral.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

SOURCE_ID = "de.nrw.geobasis-lod2-ogc-features.2026"
METADATA_URL = "https://ogc-api.nrw.de/3dg/v1/collections/building?f=json"
MAX_BYTES = 131072


class MetadataProbeError(ValueError):
    """Unsafe/invalid source metadata or unsupported transport."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise MetadataProbeError("redirects blocked: fixed source identity required")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise MetadataProbeError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _reject_number(value: str) -> None:
    raise MetadataProbeError(f"non-finite JSON number: {value}")


def assess(raw: bytes, *, media_type: str = "application/json") -> dict[str, Any]:
    """Validate provider collection metadata without returning provider feature rows."""
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise MetadataProbeError("empty, non-bytes or oversized response")
    content_type = media_type.split(";", 1)[0].lower().strip()
    if content_type not in {"application/json", "application/geo+json"}:
        raise MetadataProbeError("expected JSON metadata media type")
    try:
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_reject_number
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MetadataProbeError("not valid UTF-8 JSON metadata") from exc
    if not isinstance(document, dict) or document.get("id") != "building":
        raise MetadataProbeError("collection id mismatch")
    # Reject a feature/item payload, even if it happens to contain an id field.
    if "features" in document or "geometry" in document or document.get("type") in ("Feature", "FeatureCollection"):
        raise MetadataProbeError("feature payload is outside metadata-only scope")
    if "links" not in document or not isinstance(document["links"], list):
        raise MetadataProbeError("collection metadata has no OGC links")
    if not document["links"] or not all(
        isinstance(link, dict)
        and isinstance(link.get("rel"), str) and bool(link["rel"].strip())
        and isinstance(link.get("href"), str) and bool(link["href"].strip())
        for link in document["links"]
    ):
        raise MetadataProbeError("invalid collection links")
    # Persist only booleans and exact byte identity, never response body or links.
    matches = []
    for field in ("numberMatched", "itemCount"):
        value = document.get(field)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise MetadataProbeError(f"invalid {field}")
            matches.append(value)
    if len(matches) == 2 and matches[0] != matches[1]:
        raise MetadataProbeError("conflicting count metadata")
    extent = document.get("extent")
    if extent is not None and not isinstance(extent, dict):
        raise MetadataProbeError("invalid collection extent")
    return {
        "profile": "oc-nrw-lod2-collection-metadata-v0",
        "source_id": SOURCE_ID,
        "fixed_url": METADATA_URL,
        "http_media_type": content_type,
        "original_metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "original_metadata_bytes": len(raw),
        "collection_id_verified": True,
        "collection_links_present": True,
        "advertised_feature_count": matches[0] if matches else None,
        "extent_object_present": extent is not None,
        "source_feature_bytes_acquired": False,
        "admission_status": "not_admitted",
        "rights_review_complete": False,
        "scientific_fitness_verified": False,
        "cat_model_input_approved": False,
    }


def fetch_fixed_metadata() -> tuple[bytes, str]:
    """Single fixed HTTPS metadata GET; never follow redirects or fetch features."""
    request = Request(
        METADATA_URL,
        headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-source-metadata-canary/0"},
        method="GET",
    )
    opener = build_opener(_RejectRedirects())
    try:
        with opener.open(request, timeout=12) as response:
            if response.status != 200 or response.geturl() != METADATA_URL:
                raise MetadataProbeError("unexpected HTTP status or effective URL")
            declared_length = response.headers.get("Content-Length")
            if declared_length is not None:
                try:
                    length = int(declared_length)
                except ValueError as exc:
                    raise MetadataProbeError("invalid Content-Length") from exc
                if length < 1 or length > MAX_BYTES:
                    raise MetadataProbeError("Content-Length outside bound")
            raw = response.read(MAX_BYTES + 1)
            return raw, response.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise MetadataProbeError(f"metadata request blocked: {type(exc).__name__}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="One exact provider metadata GET; no item requests")
    mode.add_argument("--offline-json", type=Path, help="Locally authored synthetic JSON fixture only")
    args = parser.parse_args(argv)
    try:
        if args.live:
            raw, media_type = fetch_fixed_metadata()
        else:
            if args.offline_json.stat().st_size > MAX_BYTES:
                raise MetadataProbeError("fixture exceeds metadata response bound")
            raw, media_type = args.offline_json.read_bytes(), "application/json"
        receipt = assess(raw, media_type=media_type)
        receipt["origin_verified_by_live_transport"] = bool(args.live)
        receipt["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    except (MetadataProbeError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
