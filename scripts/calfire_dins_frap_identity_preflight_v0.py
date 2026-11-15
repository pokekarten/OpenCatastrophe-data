# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline *candidate only* DINS ↔ FRAP wildfire incident-identity preflight.

No HTTP, geometry, addresses, parcel/policy data, damage counts, or loss estimates.
A syntactically matching incident ID does NOT prove event identity or permit joins.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MAX_BYTES = 16384
DINS_SOURCE = "us.calfire.dins.structure-damage"
FRAP_SOURCE = "us.calfire.frap.historical-fire-perimeters.firep25-1"
DINS_FIELDS = {"incident_number", "calfire_unit", "incident_start_date", "hazard_type"}
FRAP_FIELDS = {"inc_num", "unit_id", "alarm_date", "year", "irwinid"}
TOP_FIELDS = {
    "schema_version", "origin", "dins_source_id", "frap_source_id",
    "dins", "frap_candidates", "source_receipts",
}
DINS_INCIDENT = re.compile(r"CA([A-Z]{3}) ([0-9]{6})\Z")
FRAP_INC = re.compile(r"[A-Z0-9]{1,8}\Z")
UNIT = re.compile(r"[A-Z]{3}\Z")
IRWIN = re.compile(r"\{?[0-9a-fA-F-]{36}\}?\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class IncidentIdentityError(ValueError):
    """Unsafe, unsupported or malformed source-summary contract."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IncidentIdentityError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise IncidentIdentityError("nonfinite JSON constants forbidden")


def _fixed_date(s: Any) -> date:
    if type(s) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        raise IncidentIdentityError("date must be ISO YYYY-MM-DD")
    try:
        result = date.fromisoformat(s)
    except ValueError as exc:
        raise IncidentIdentityError("invalid Gregorian date") from exc
    if not 2013 <= result.year <= 2100:
        raise IncidentIdentityError("out-of-scope incident year")
    return result


def _fields(obj: Any, required: set[str], label: str) -> dict[str, Any]:
    if type(obj) is not dict or set(obj) != required:
        raise IncidentIdentityError(label + " keys do not match the safe schema")
    return obj


def preflight_incident_pair(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise IncidentIdentityError("input byte size outside fixed limit")
    try:
        obj = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IncidentIdentityError("invalid UTF-8 JSON") from exc
    _fields(obj, TOP_FIELDS, "top-level")
    if (
        obj["schema_version"] != "1.0.0"
        or obj["dins_source_id"] != DINS_SOURCE
        or obj["frap_source_id"] != FRAP_SOURCE
    ):
        raise IncidentIdentityError("incorrect source/version identity")
    origin = obj["origin"]
    receipts = _fields(obj["source_receipts"], {"dins_sha256", "frap_sha256"}, "receipts")
    if origin == "synthetic":
        if any(value is not None for value in receipts.values()):
            raise IncidentIdentityError("synthetic summary cannot claim source receipts")
    elif origin == "externally_prepared_incident_metadata":
        if any(type(value) is not str or not SHA.fullmatch(value) for value in receipts.values()):
            raise IncidentIdentityError("external metadata requires two source snapshot SHA256 labels")
    else:
        raise IncidentIdentityError("unsupported origin")
    dins = _fields(obj["dins"], DINS_FIELDS, "DINS incident")
    if dins["hazard_type"] != "Fire":
        raise IncidentIdentityError("source includes other hazard types; only Fire is eligible")
    number, unit = dins["incident_number"], dins["calfire_unit"]
    if type(number) is not str or type(unit) is not str or not UNIT.fullmatch(unit):
        raise IncidentIdentityError("invalid DINS incident number or CAL FIRE unit")
    identifier = DINS_INCIDENT.fullmatch(number)
    if identifier is None:
        raise IncidentIdentityError("unsupported DINS incident number format; manual crosswalk only")
    if identifier.group(1) != unit:
        raise IncidentIdentityError("DINS number/unit conflict")
    started = _fixed_date(dins["incident_start_date"])
    rows = obj["frap_candidates"]
    if type(rows) is not list or not (1 <= len(rows) <= 25):
        raise IncidentIdentityError("only 1..25 preselected FRAP incident headers allowed")
    identical = 0
    for row in rows:
        _fields(row, FRAP_FIELDS, "FRAP incident")
        local, unit_id = row["inc_num"], row["unit_id"]
        if (
            type(local) is not str or not FRAP_INC.fullmatch(local)
            or type(unit_id) is not str or not UNIT.fullmatch(unit_id)
        ):
            raise IncidentIdentityError("malformed FRAP incident identifiers")
        if type(row["year"]) is not int or not 2013 <= row["year"] <= 2100:
            raise IncidentIdentityError("FRAP YEAR_ must be integer")
        alarm = _fixed_date(row["alarm_date"])
        if alarm.year != row["year"]:
            raise IncidentIdentityError("FRAP YEAR_ does not agree with ALARM_DATE")
        irwin = row["irwinid"]
        if irwin is not None and (type(irwin) is not str or not IRWIN.fullmatch(irwin)):
            raise IncidentIdentityError("invalid optional FRAP IRWINID shape")
        # Exact six-digit text, NOT integer coercion, suffix-only matches or name fuzzy joins.
        # ID/date/unit agreement is still a *candidate* and cannot prove unique geometry.
        if (
            local == identifier.group(2)
            and unit_id == unit
            and alarm.year == started.year
            and abs((alarm - started).days) <= 3
        ):
            identical += 1

    status = (
        "no_candidate" if identical == 0
        else "candidate_requires_original_identity_review" if identical == 1
        else "ambiguous_candidates_quarantined"
    )
    return {
        "schema_version": "1.0.0",
        "dins_source_id": DINS_SOURCE,
        "frap_source_id": FRAP_SOURCE,
        "origin": origin,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "source_receipts_supplied_not_verified": origin != "synthetic",
        "candidate_count": identical,
        "status": status,
        "source_field_concordance": "DINS INCIDENTNUM/CALFIREUNIT/INCIDENTSTARTDATE vs FRAP INC_NUM/UNIT_ID/ALARM_DATE/YEAR_",
        "provider_confirmed_event_identity": False,
        "external_feature_rows_read": 0,
        "automatic_polygon_to_building_join_allowed": False,
        "exposure_denominator_validated": False,
        "insured_loss_inferred": False,
        "model_data_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        result = preflight_incident_pair(raw)
    except (OSError, IncidentIdentityError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
