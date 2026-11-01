# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline reconciliation for geometry-free FEMA cohort aggregate query results.

This guard checks that *three independent group-by query results* agree on a
single bounded public FEMA cohort. It never downloads provider rows, infers
individual building identity, estimates insured damage, or admits model inputs.
Only source-native aggregate counts, without location coordinates, are accepted.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any

SERVICE_ITEM = "e56e3d16fa144684bd532edbf298042c"
LEVELS = frozenset(("UNK", "DES", "MAJ", "MIN", "AFF", "NOD"))
COUNTY = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")
COHORT_FIELDS = frozenset((
    "service_item_id", "disaster_number", "event_date_utc_ms",
    "assessment_type", "damage_type", "census_count", "level_counts",
    "county_level_counts", "date_groups",
))
COUNTY_ROW_FIELDS = frozenset(("state", "county", "damage_level", "count"))
DATE_ROW_FIELDS = frozenset(("event_date_utc_ms", "image_date_utc_ms", "production_date_utc_ms", "count"))
MAX_COUNTRY_REGIONS = 100


class ReconciliationError(ValueError):
    """Source aggregates conflict, leak prohibited fields, or are incomplete."""


def _count(value: Any) -> int:
    if type(value) is not int or not 0 < value <= 2_000_000_000:
        raise ReconciliationError("counts must be positive, bounded integers")
    return value


def _timestamp(value: Any) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 4_102_444_800_000:
        raise ReconciliationError("provider dates must be UTC epoch milliseconds or null")
    return value


def reconcile(payload: Any) -> dict[str, Any]:
    """Fail closed on inconsistent complete aggregates for a single FEMA disaster.

    As with source layer queries, returnGeometry=false is mandatory upstream;
    this function also rejects any embedded geometry, raw IDs or extra fields.
    """
    if type(payload) is not dict or set(payload) != COHORT_FIELDS:
        raise ReconciliationError("aggregate contract fields do not match")
    if payload["service_item_id"] != SERVICE_ITEM:
        raise ReconciliationError("wrong provider service item/version")
    if type(payload["disaster_number"]) is not str or not re.fullmatch(r"DR-[0-9]{4}", payload["disaster_number"]):
        raise ReconciliationError("cohort needs exact FEMA disaster number")
    if payload["assessment_type"] != "RS" or payload["damage_type"] != "WI":
        raise ReconciliationError("only remote sensing wind assessments, not observed claims")
    event_ms = _timestamp(payload["event_date_utc_ms"])
    if event_ms is None:
        raise ReconciliationError("event date must be explicit")
    if event_ms % 86400000 != 0:
        raise ReconciliationError("event must be pinned to an exact UTC date")
    total = _count(payload["census_count"])

    levels = payload["level_counts"]
    if type(levels) is not dict or not levels or not set(levels) <= LEVELS:
        raise ReconciliationError("damage-level aggregate includes invalid/unreviewed values")
    for count in levels.values():
        _count(count)
    if sum(levels.values()) != total:
        raise ReconciliationError("damage-level counts do not reconcile to cohort census")

    counties = payload["county_level_counts"]
    if type(counties) is not list or not 1 <= len(counties) <= MAX_COUNTRY_REGIONS:
        raise ReconciliationError("missing or unbounded county groups")
    seen = set()
    combined = Counter()
    regional = Counter()
    for row in counties:
        if type(row) is not dict or set(row) != COUNTY_ROW_FIELDS:
            raise ReconciliationError("county group contains extra/missing fields")
        state, county, level = row["state"], row["county"], row["damage_level"]
        if state != "FL" or type(county) is not str or not COUNTY.fullmatch(county) or level not in LEVELS:
            raise ReconciliationError("invalid state/county/damage class")
        key = (state, county, level)
        if key in seen:
            raise ReconciliationError("duplicate county/damage cell would inflate the cohort")
        seen.add(key)
        n = _count(row["count"])
        combined[level] += n
        regional[county] += n
    if dict(combined) != levels:
        raise ReconciliationError("county-class total differs from damage-level source counts")

    dates = payload["date_groups"]
    if type(dates) is not list or not 1 <= len(dates) <= 100:
        raise ReconciliationError("date aggregate missing or unbounded")
    seen_dates = set()
    missing_image = missing_production = 0
    for row in dates:
        if type(row) is not dict or set(row) != DATE_ROW_FIELDS:
            raise ReconciliationError("date group contains extra/missing fields")
        if _timestamp(row["event_date_utc_ms"]) != event_ms:
            raise ReconciliationError("date aggregate event mismatch")
        img, prod = _timestamp(row["image_date_utc_ms"]), _timestamp(row["production_date_utc_ms"])
        key = (img, prod)
        if key in seen_dates:
            raise ReconciliationError("duplicate date aggregate key")
        seen_dates.add(key)
        n = _count(row["count"])
        missing_image += n if img is None else 0
        missing_production += n if prod is None else 0
    if sum(_count(row["count"]) for row in dates) != total:
        raise ReconciliationError("date aggregate differs from census")

    return {
        "profile": "fema_single_disaster_aggregate_reconciliation_v0",
        "source_item_id": SERVICE_ITEM,
        "disaster_number": payload["disaster_number"],
        "event_day_utc": datetime.fromtimestamp(event_ms / 1000, tz=timezone.utc).date().isoformat(),
        "total_assessments": total,
        "assessment_type": "RS",
        "damage_type": "WI",
        "damage_level_counts": {x: levels.get(x, 0) for x in ("NOD", "AFF", "MIN", "MAJ", "DES", "UNK")},
        "unique_counties": len(regional),
        "largest_county_share": max(regional.values()) / total,
        "missing_image_date_assessments": missing_image,
        "missing_production_date_assessments": missing_production,
        "field_observed_assessments_verified": 0,
        "property_count_verified": False,
        "scientific_independence_proven": False,
        "automatic_building_join_allowed": False,
        "model_input_admitted": False,
        "source_bytes_downloaded": False,
    }
