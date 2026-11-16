# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline NOAA NCEI historical *source-event* layer-0 JSON science preflight.

Only a separately authorized response is eligible for this screen. This is not
an API client, an admission decision, a runup observation parser, or a claim of
catalogue completeness. Source: NOAA ArcGIS hazards MapServer layer 0 and NCEI
G02151 validity metadata. No raw event attributes are echoed to receipts.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from typing import Any

SOURCE_ID = "noaa.ncei.global-historical-tsunami"
LAYER_URL = "https://gis.ngdc.noaa.gov/arcgis/rest/services/web_mercator/hazards/MapServer/0"
MAX_RESPONSE_BYTES = 65_536
MAX_FEATURES = 3
FIELD_TYPES = {
    "OBJECTID": "esriFieldTypeOID", "ID": "esriFieldTypeDouble",
    "YEAR": "esriFieldTypeInteger", "MONTH": "esriFieldTypeSmallInteger",
    "DAY": "esriFieldTypeSmallInteger",
    "LATITUDE": "esriFieldTypeDouble", "LONGITUDE": "esriFieldTypeDouble",
    "EVENT_VALIDITY_CODE": "esriFieldTypeSmallInteger",
    "CAUSE_CODE": "esriFieldTypeSmallInteger",
    "NUM_RUNUP": "esriFieldTypeInteger",
    "MAX_EVENT_RUNUP": "esriFieldTypeDouble",
}


class TsunamiEventPreflightError(ValueError):
    """Untrustworthy, unsafe or scientifically ambiguous bounded input."""


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise TsunamiEventPreflightError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> None:
    raise TsunamiEventPreflightError("nonfinite JSON constant")


def _integer(value: Any, name: str, *, minimum: int, maximum: int, nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise TsunamiEventPreflightError(f"invalid {name}")
    return value


def _number(value: Any, name: str, *, minimum: float, maximum: float, nullable: bool = False) -> float | None:
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TsunamiEventPreflightError(f"invalid {name}")
    try:
        n = float(value)
    except (OverflowError, ValueError) as exc:
        raise TsunamiEventPreflightError(f"unrepresentable {name}") from exc
    if not math.isfinite(n) or not minimum <= n <= maximum:
        raise TsunamiEventPreflightError(f"{name} out of bounds")
    return n


def screen_noaa_tsunami_event_json(original: bytes) -> dict[str, object]:
    """Check one preselected, no-geometry ArcGIS layer-0 response, offline.

    An input-byte SHA is NOT evidence of source retrieval, legal permission,
    historical completeness or scientific validity for CAT modelling.
    """
    if not isinstance(original, bytes) or not 0 < len(original) <= MAX_RESPONSE_BYTES:
        raise TsunamiEventPreflightError("empty, unbounded or non-byte JSON response")
    try:
        raw = json.loads(original.decode("utf-8", errors="strict"),
                         object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise TsunamiEventPreflightError("invalid JSON encoding or syntax") from exc
    if not isinstance(raw, dict) or set(raw) - {
        "objectIdFieldName", "fields", "features", "exceededTransferLimit",
        "geometryType", "spatialReference",
    }:
        raise TsunamiEventPreflightError("unexpected ArcGIS response shape or error payload")
    transfer_limit = raw.get("exceededTransferLimit")
    if raw.get("objectIdFieldName") != "OBJECTID" or transfer_limit is True:
        raise TsunamiEventPreflightError("wrong layer OID or truncated ArcGIS result")
    # Do not accept numeric 0/0.0 as JSON false via Python's equality semantics.
    if transfer_limit is not None and transfer_limit is not False:
        raise TsunamiEventPreflightError("unexpected transfer-limit indicator")
    if raw.get("geometryType") not in (None, "esriGeometryPoint"):
        raise TsunamiEventPreflightError("source-event point layer mismatch")
    sr = raw.get("spatialReference")
    if sr is not None and (not isinstance(sr, dict) or
                           sr.get("wkid") not in (3857, 102100, None)):
        raise TsunamiEventPreflightError("unexpected ArcGIS spatial reference")
    fields = raw.get("fields")
    if not isinstance(fields, list) or len(fields) != len(FIELD_TYPES):
        raise TsunamiEventPreflightError("wrong fixed field selection")
    observed_fields: dict[str, str] = {}
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("name"), str) or not isinstance(field.get("type"), str):
            raise TsunamiEventPreflightError("invalid ArcGIS field declaration")
        name = field["name"]
        if name in observed_fields:
            raise TsunamiEventPreflightError("duplicate field name")
        observed_fields[name] = field["type"]
    if observed_fields != FIELD_TYPES:
        raise TsunamiEventPreflightError("tsunami source-event schema identity mismatch")
    features = raw.get("features")
    if not isinstance(features, list) or not 0 < len(features) <= MAX_FEATURES:
        raise TsunamiEventPreflightError("expected 1-3 bounded source-event features")
    seen_ids: set[int] = set()
    seen_oids: set[int] = set()
    validity_counts = {str(v): 0 for v in range(-1, 5)}
    without_month_or_day = 0
    without_runup_height = 0
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != {"attributes"}:
            raise TsunamiEventPreflightError("unexpected geometry, runup or feature shape")
        attrs = feature["attributes"]
        if not isinstance(attrs, dict) or set(attrs) != set(FIELD_TYPES):
            raise TsunamiEventPreflightError("unexpected or missing source-event attributes")
        oid = _integer(attrs["OBJECTID"], "OBJECTID", minimum=1, maximum=2_147_483_647)
        record_id = _number(attrs["ID"], "event ID", minimum=1, maximum=1_000_000_000)
        if not float(record_id).is_integer():
            raise TsunamiEventPreflightError("event ID is not integral")
        rid = int(record_id)
        if oid in seen_oids or rid in seen_ids:
            raise TsunamiEventPreflightError("duplicate source-event identifier")
        seen_oids.add(oid)
        seen_ids.add(rid)
        year = _integer(attrs["YEAR"], "historical year", minimum=-2100, maximum=2026)
        if year == 0:
            raise TsunamiEventPreflightError("ambiguous historical calendar year zero")
        month = _integer(attrs["MONTH"], "month", minimum=1, maximum=12, nullable=True)
        day = _integer(attrs["DAY"], "day", minimum=1, maximum=31, nullable=True)
        if day is not None and month is None:
            raise TsunamiEventPreflightError("day given without month")
        # Gregorian validity is suitable only for post-adoption years; earlier
        # reports require independent Julian/Gregorian calendar provenance.
        if year >= 1600 and month is not None and day is not None:
            try:
                dt.date(year, month, day)
            except ValueError as exc:
                raise TsunamiEventPreflightError("invalid modern Gregorian date") from exc
        without_month_or_day += month is None or day is None
        _number(attrs["LATITUDE"], "latitude", minimum=-90, maximum=90)
        _number(attrs["LONGITUDE"], "longitude", minimum=-180, maximum=180)
        validity = _integer(attrs["EVENT_VALIDITY_CODE"], "event validity", minimum=-1, maximum=4)
        _integer(attrs["CAUSE_CODE"], "cause code", minimum=0, maximum=11, nullable=True)
        _integer(attrs["NUM_RUNUP"], "runup observation count", minimum=0, maximum=100_000, nullable=True)
        runup = _number(attrs["MAX_EVENT_RUNUP"], "max event runup meters",
                        minimum=0, maximum=10_000, nullable=True)
        without_runup_height += runup is None
        validity_counts[str(validity)] += 1
    return {
        "source_id": SOURCE_ID,
        "layer_identity": LAYER_URL,
        "input_response_sha256": hashlib.sha256(original).hexdigest(),
        "input_response_bytes": len(original),
        "features_screened": len(features),
        "event_validity_counts": validity_counts,
        "historically_probable_or_definite_event_count": validity_counts["3"] + validity_counts["4"],
        "unconfirmed_or_non_tsunami_event_count": sum(validity_counts[str(i)] for i in (-1, 0, 1, 2)),
        "partially_dated_events": without_month_or_day,
        "events_without_max_runup": without_runup_height,
        "runup_record_geometry_or_inundation_verified": False,
        "historical_calendar_and_source_deduplication_verified": False,
        "complete_event_catalogue_verified": False,
        "original_provider_provenance_verified": False,
        "source_automation_rights_verified": False,
        "commercial_cat_model_use_approved": False,
        "neon_storage": "storage_not_verified",
    }
