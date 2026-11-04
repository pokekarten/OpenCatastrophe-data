#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-metadata QA for 2016 Loing high-water marks; no downloads.

An exact NGF 1969 reference+offset reconciliation is NOT an original provider
byte receipt, a terrain-elevation observation or an insured asset flood depth.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


class WatermarkBlocked(ValueError):
    """Untrusted or scientifically ambiguous reported field."""


_REQUIRED = {
    "site_id", "mark_id", "source_site_url", "watercourse", "event_date",
    "survey_date", "mark_evidence", "survey_method", "vertical_datum",
    "longitude_wgs84", "latitude_wgs84", "reference_kind",
    "reference_elevation_m", "water_offset_from_reference_m",
    "published_water_surface_elevation_m",
}
_SOURCE_HOST = "www.reperesdecrues.developpement-durable.gouv.fr"
_SOURCE_PATH = re.compile(r"/site/[a-z0-9-]{1,128}")
_ID = re.compile(r"[A-Za-z0-9_]{5,80}")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,3})?")


def _unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WatermarkBlocked("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(_):
    raise WatermarkBlocked("nonfinite JSON constant")


def load_metadata(path: Path):
    if not path.is_file() or path.stat().st_size > 65536:
        raise WatermarkBlocked("local metadata JSON missing or oversized")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_json_keys,
                          parse_constant=_reject_nonfinite)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WatermarkBlocked("invalid UTF-8 JSON metadata") from exc


def _date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise WatermarkBlocked(f"invalid {field} date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise WatermarkBlocked(f"invalid {field} calendar date") from exc


def _meters(value, field):
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise WatermarkBlocked(f"{field} must be a decimal metres string with <=3 decimals")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise WatermarkBlocked(f"invalid {field}") from exc


def _coordinate(value, low, high, name):
    if type(value) not in (int, float):
        raise WatermarkBlocked(f"invalid coordinate {name}")
    # Compare bounds first to avoid float overflow on arbitrary-size JSON int.
    if not low <= value <= high:
        raise WatermarkBlocked(f"coordinate {name} outside Loing research study envelope")
    return value


def _review_one(item):
    if not isinstance(item, dict) or set(item) != _REQUIRED:
        raise WatermarkBlocked("missing or unreviewed high-water-mark fields")
    for key in ("site_id", "mark_id"):
        if not isinstance(item[key], str) or not _ID.fullmatch(item[key]):
            raise WatermarkBlocked(f"unreviewed {key}")
    url = item["source_site_url"]
    if not isinstance(url, str) or len(url) > 512:
        raise WatermarkBlocked("invalid source URL")
    p = urlsplit(url)
    if (p.scheme != "https" or p.netloc != _SOURCE_HOST or
            not _SOURCE_PATH.fullmatch(p.path) or p.query or p.fragment):
        raise WatermarkBlocked("source is not a reviewed official site page")
    if item["watercourse"] != "Le Loing":
        raise WatermarkBlocked("wrong watercourse for Loing-only evidence slice")
    event = _date(item["event_date"], "event_date")
    surveyed = _date(item["survey_date"], "survey_date")
    if not (date(2016, 5, 29) <= event <= date(2016, 6, 7)):
        raise WatermarkBlocked("not the bounded 2016 flood event window")
    if not (event < surveyed <= date(2026, 11, 4)):
        raise WatermarkBlocked("survey time must follow, not equal, flood event time")
    if item["vertical_datum"] != "NGF IGN 1969":
        raise WatermarkBlocked("vertical datum is missing or incompatible")
    _coordinate(item["longitude_wgs84"], 2.0, 3.1, "longitude")
    _coordinate(item["latitude_wgs84"], 47.5, 48.6, "latitude")
    if item["mark_evidence"] not in ("physical_flood_trace", "oral_testimony"):
        raise WatermarkBlocked("unknown mark-evidence class")
    if item["survey_method"] != "GPS":
        raise WatermarkBlocked("survey method unverified for this cohort")
    kind = item["reference_kind"]
    if kind not in ("flood_mark", "external_reference"):
        raise WatermarkBlocked("unknown vertical reference semantics")
    reference = _meters(item["reference_elevation_m"], "reference_elevation_m")
    reported_water = _meters(item["published_water_surface_elevation_m"],
                             "published_water_surface_elevation_m")
    if kind == "flood_mark":
        if item["water_offset_from_reference_m"] is not None:
            raise WatermarkBlocked("a flood-mark reference must not have a fabricated offset")
        calculated = reference
    else:
        if item["water_offset_from_reference_m"] is None:
            raise WatermarkBlocked("reference offset required for other measured bench")
        offset = _meters(item["water_offset_from_reference_m"], "water_offset_from_reference_m")
        calculated = reference + offset
    if calculated != reported_water:
        raise WatermarkBlocked("water-surface elevation does not reconcile with reference and offset")
    physical = item["mark_evidence"] == "physical_flood_trace"
    return {
        "site_id": item["site_id"], "mark_id": item["mark_id"],
        "water_surface_m_ngf_ign1969": str(reported_water),
        "event_date": event.isoformat(), "field_survey_date": surveyed.isoformat(),
        "source_type": item["mark_evidence"],
        "arithmetic_reconciled": True,
        "independent_physical_trace_candidate": physical,
        "provider_original_bytes_attested": False,
        "water_surface_uncertainty_m_established": False,
        "local_ground_elevation_verified": False,
        "inundation_depth_at_building_established": False,
        "data_reuse_and_asset_rights_reviewed": False,
        "hazard_model_input_admitted": False,
    }


def review_marks(rows):
    if not isinstance(rows, list) or not (1 <= len(rows) <= 50):
        raise WatermarkBlocked("bounded nonempty mark list required")
    reviewed = [_review_one(row) for row in rows]
    if (len({r["mark_id"] for r in reviewed}) != len(reviewed) or
            len({r["site_id"] for r in reviewed}) != len(reviewed)):
        raise WatermarkBlocked("duplicated physical source or mark identity")
    return {
        "profile": "oc-loing-2016-ngf1969-field-mark-research-v0",
        "marks_reviewed": len(reviewed),
        "physical_trace_candidates": sum(r["independent_physical_trace_candidate"] for r in reviewed),
        "marks": reviewed,
        "source_original_bytes_attested": False,
        "datum_transformation_authorized": False,
        "building_water_depths_established": False,
        "risk_or_insured_loss_model_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review_marks(load_metadata(args.metadata_json))
    except WatermarkBlocked as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
