#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, OFFLINE original-byte receipt gate for one synthetic/externally acquired ComCat response.

This module does not fetch USGS, approve rights, record provider event data, or
claim contemporary product availability. The caller must independently acquire
and retain original bytes in an authorised private environment after rights review.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
import re

EXACT_QUERY = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&limit=1&orderby=time&eventtype=earthquake&nodata=204"
)
MAX_ORIGINAL_BYTES = 1_048_576
_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ComCatOriginalBlocked(ValueError):
    """Invalid or unproven original-response evidence."""


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ComCatOriginalBlocked("duplicate original JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise ComCatOriginalBlocked("non-finite original JSON value")


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        # Very large JSON integers must fail closed, not crash the verifier.
        return False


def verify_original_response(
    original_body: bytes, *,
    exact_query: str,
    received_at_utc: str,
    media_type: str,
) -> dict:
    """Inspect supplied exact original response bytes, never persisted or printed.

    Receipt time is caller-ASSERTED, not independent proof of historical access.
    A valid receipt is NOT a licence or scientifically admitted source.
    """
    if exact_query != EXACT_QUERY:
        raise ComCatOriginalBlocked("original request differs from the exact frozen query")
    if not isinstance(received_at_utc, str) or not _UTC.fullmatch(received_at_utc):
        raise ComCatOriginalBlocked("receipt requires second-precision UTC timestamp")
    try:
        datetime.fromisoformat(received_at_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ComCatOriginalBlocked("invalid receipt calendar time") from exc
    if media_type != "application/json":
        raise ComCatOriginalBlocked("original response media type not permitted")
    if type(original_body) is not bytes or not 0 < len(original_body) <= MAX_ORIGINAL_BYTES:
        raise ComCatOriginalBlocked("missing or oversized original response")
    try:
        obj = json.loads(
            original_body.decode("utf-8"),
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComCatOriginalBlocked("invalid UTF-8 JSON original response") from exc
    if not isinstance(obj, dict) or obj.get("type") != "FeatureCollection":
        raise ComCatOriginalBlocked("not a ComCat GeoJSON FeatureCollection")
    features = obj.get("features")
    metadata = obj.get("metadata")
    if (not isinstance(features, list) or len(features) != 1
            or not isinstance(metadata, dict) or type(metadata.get("count")) is not int
            or metadata["count"] != 1):
        raise ComCatOriginalBlocked("exact one-event response count mismatch")
    feature = features[0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise ComCatOriginalBlocked("invalid event feature")
    fid = feature.get("id")
    p = feature.get("properties")
    g = feature.get("geometry")
    if not isinstance(fid, str) or not _ID.fullmatch(fid):
        raise ComCatOriginalBlocked("invalid event identity")
    if not isinstance(p, dict) or p.get("type") != "earthquake":
        raise ComCatOriginalBlocked("non-earthquake event")
    if not _finite_number(p.get("time")) or not _finite_number(p.get("updated")):
        raise ComCatOriginalBlocked("missing event time/update semantics")
    if not isinstance(g, dict) or g.get("type") != "Point":
        raise ComCatOriginalBlocked("missing point origin geometry")
    coordinates = g.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 3:
        raise ComCatOriginalBlocked("origin must have longitude, latitude and depth")
    lon, lat, depth = coordinates
    if (not all(_finite_number(n) for n in coordinates)
            or not -180 <= lon <= 180 or not -90 <= lat <= 90
            or not -100 <= depth <= 1000):
        raise ComCatOriginalBlocked("invalid event origin coordinates/depth")
    # These are response-STRUCTURE checks, not scientific origin verification.
    return {
        "schema_version": "1.0.0",
        "classification": "OFFLINE_ORIGINAL_BODY_SHAPE_ONLY_NOT_ADMITTED",
        "frozen_request": EXACT_QUERY,
        "received_at_utc_asserted": received_at_utc,
        "original_body_bytes": len(original_body),
        "original_body_sha256": hashlib.sha256(original_body).hexdigest(),
        "event_count": 1,
        "event_id_published": False,
        "rights_approved": False,
        "source_model_admitted": False,
        "live_provider_request_executed": False,
        "historical_availability_proven": False,
    }
