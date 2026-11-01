# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-testable FEMA damage assessment *provenance* gate.

The input is a tightly projected, geometry-free subset of a FEMA FeatureServer
response. It does not download FEMA data, infer building identities, calculate
insured loss, or grant rights/model admission.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import math
import re
from typing import Any

SOURCE_ID = "us.fema.historical-geospatial-damage-assessments"
SOURCE_LAYER = (
    "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
    "FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0"
)
REQUIRED_ATTRIBUTES = frozenset({
    "OBJECTID", "DIS_NUMBER", "EVENT_DATE", "ASMT_TYPE", "DMG_LEVEL",
    "DMG_TYPE", "IN_DEPTH", "IMG_DATE", "PROD_DATE",
})
DAMAGE_CODES = ("NOD", "AFF", "MIN", "MAJ", "DES", "UNK")
OBSERVATION_METHODS = ("FA", "RS", "MOD")
# Provider domain codes verified against the public FEMA ArcGIS FeatureServer.
# Unknown codes indicate upstream drift, never observed evidence.
PROVIDER_ASSESSMENT_CODES = frozenset(("MOD", "RS", "FA", "OTH", "UNK"))
PROVIDER_DAMAGE_TYPE_CODES = frozenset(("UNK", "EQ", "FI", "FL", "WI", "IS", "MUL", "OTH"))
MAX_RECORDS = 2000  # Service advertises a 2,000-record maximum per query.


class PreflightError(ValueError):
    """Refuse malformed or scientifically misleading source-like input."""


def _day(value: Any) -> date:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise PreflightError("event_day_utc must be an ISO YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PreflightError("invalid Gregorian event_day_utc") from exc


def _arcgis_day(value: Any, field: str, *, required: bool = False) -> date | None:
    if value is None and not required:
        return None
    if type(value) is not int or value < 0 or value > 4102444800000:
        raise PreflightError(f"{field} must be UTC epoch milliseconds or null")
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date()


def _disaster(value: Any) -> str:
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9-]{1,10}", value):
        raise PreflightError("DIS_NUMBER must be a bounded source-native string")
    return value


def _code(value: Any, field: str) -> str:
    if type(value) is not str or not re.fullmatch(r"[A-Z]{2,3}", value):
        raise PreflightError(f"{field} must be a source-native 2-3 character code")
    return value


def _depth(value: Any) -> bool:
    if value is None:
        return False
    if type(value) not in (int, float):
        raise PreflightError("IN_DEPTH must be finite nonnegative feet or null")
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise PreflightError("IN_DEPTH must be finite nonnegative feet or null") from exc
    if not math.isfinite(number) or number < 0:
        raise PreflightError("IN_DEPTH must be finite nonnegative feet or null")
    return True


def preflight(payload: Any) -> dict[str, Any]:
    """Return privacy-safe aggregate evidence; never output feature/geometry IDs.

    Payload contains event_disaster_number, event_day_utc and features, whose
    only child field is attributes with exactly REQUIRED_ATTRIBUTES.
    Caller must project these fields with returnGeometry=false; no network used.
    """
    if type(payload) is not dict or set(payload) != {
        "event_disaster_number", "event_day_utc", "features"
    }:
        raise PreflightError("expected event_disaster_number, event_day_utc, features")
    target_disaster = _disaster(payload["event_disaster_number"])
    target_day = _day(payload["event_day_utc"])
    features = payload["features"]
    if type(features) is not list or not 1 <= len(features) <= MAX_RECORDS:
        raise PreflightError("features must contain 1..2000 records")

    observed = Counter()
    by_level = Counter()
    seen = set()
    recognized_field_candidates = 0
    field_unknown_damage = 0
    unknown_or_other_methods = 0
    depth_count = 0
    missing_image_date = 0
    image_before_event = 0
    production_before_event = 0
    missing_production_date = 0
    image_after_production = 0

    for feature in features:
        if type(feature) is not dict or set(feature) != {"attributes"}:
            raise PreflightError("features must be geometry-free, projected attributes")
        a = feature["attributes"]
        if type(a) is not dict or set(a) != REQUIRED_ATTRIBUTES:
            raise PreflightError("unexpected/missing provider fields in projection")
        oid = a["OBJECTID"]
        if type(oid) is not int or oid <= 0 or oid in seen:
            raise PreflightError("OBJECTID must be a unique positive integer")
        seen.add(oid)
        if _disaster(a["DIS_NUMBER"]) != target_disaster:
            raise PreflightError("multiple FEMA disaster numbers in one batch")
        if _arcgis_day(a["EVENT_DATE"], "EVENT_DATE", required=True) != target_day:
            raise PreflightError("event timestamp outside frozen event day")

        method = _code(a["ASMT_TYPE"], "ASMT_TYPE")
        level = _code(a["DMG_LEVEL"], "DMG_LEVEL")
        damage_type = _code(a["DMG_TYPE"], "DMG_TYPE")
        if method not in PROVIDER_ASSESSMENT_CODES:
            raise PreflightError("unrecognized provider ASMT_TYPE")
        if damage_type not in PROVIDER_DAMAGE_TYPE_CODES:
            raise PreflightError("unrecognized provider DMG_TYPE")
        if level not in DAMAGE_CODES:
            raise PreflightError("unrecognized DMG_LEVEL")
        img_date = _arcgis_day(a["IMG_DATE"], "IMG_DATE")
        prod_date = _arcgis_day(a["PROD_DATE"], "PROD_DATE")
        depth_count += int(_depth(a["IN_DEPTH"]))

        # Unrecognized codes are never silently promoted to field observations.
        bucket = method if method in OBSERVATION_METHODS else "OTHER_OR_UNKNOWN"
        observed[bucket] += 1
        by_level[(bucket, level)] += 1
        if bucket == "OTHER_OR_UNKNOWN":
            unknown_or_other_methods += 1
        if img_date is None:
            missing_image_date += 1
        elif img_date < target_day:
            image_before_event += 1
        if prod_date is None:
            missing_production_date += 1
        elif prod_date < target_day:
            production_before_event += 1
        if img_date is not None and prod_date is not None and img_date > prod_date:
            image_after_production += 1
        if bucket == "FA":
            if level == "UNK":
                field_unknown_damage += 1
            elif (
                prod_date is not None
                and prod_date >= target_day
                and (img_date is None or target_day <= img_date <= prod_date)
            ):
                recognized_field_candidates += 1

    methods = ("FA", "RS", "MOD", "OTHER_OR_UNKNOWN")
    return {
        "profile": "fema_geospatial_damage_aggregate_preflight_v0",
        "source_id": SOURCE_ID,
        "role": "research_only_not_model_input",
        "event_disaster_number": target_disaster,
        "event_day_utc": target_day.isoformat(),
        "record_count": len(features),
        "assessment_counts": {key: observed[key] for key in methods},
        "damage_counts_by_method": {
            key: {level: by_level[(key, level)] for level in DAMAGE_CODES}
            for key in methods
        },
        "potential_field_observed_holdout_count": recognized_field_candidates,
        "unknown_field_damage_count": field_unknown_damage,
        "unverified_assessment_method_count": unknown_or_other_methods,
        "non_null_inundation_depth_count": depth_count,
        "inundation_depth_unit": "feet_provider_may_model_or_observe",
        "missing_imagery_date_count": missing_image_date,
        "imagery_before_event_count": image_before_event,
        "production_before_event_count": production_before_event,
        "missing_production_date_count": missing_production_date,
        "imagery_after_production_count": image_after_production,
        "scientific_independence_proven": False,
        "automatic_building_join_allowed": False,
        "model_input_admitted": False,
        "raw_data_redistribution_allowed": False,
    }


if __name__ == "__main__":
    raise SystemExit(
        "Use preflight() with locally constructed, separately reviewed attributes"
    )
