# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed synthetic-only BAG usable-area multiplicity QA.

This consumes STRIPPED, independently normalised mock observations, not raw
PDOK BAG features (which can include addresses and household references).
A BAG verblijfsobject (unit) may relate to one or MORE pand (building) IDs.
Count a unit's area once globally; do not copy its floor area to each linked
building. A unit's usable area is NOT whole-building gross floor area, physical
volume, reinstatement cost, or actual insurance TIV.
"""

from __future__ import annotations

from datetime import date
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 1_500_000
MAX_RECORDS = 5000
ID = re.compile(r"[A-Za-z0-9_.:-]{1,80}\Z")
ACTIVE_UNIT_STATUS = "Verblijfsobject in gebruik"


class BagUnitAreaError(ValueError):
    """Input contains disallowed data, missing evidence or invalid cardinality."""


def _strict(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise BagUnitAreaError("duplicate JSON key")
        obj[k] = v
    return obj


def _constant(_):
    raise BagUnitAreaError("nonfinite JSON constant")


def load(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise BagUnitAreaError("input exceeds bounded byte budget")
    return json.loads(p.read_text(encoding="utf-8"),
                      object_pairs_hook=_strict, parse_constant=_constant)


def _fields(row, expected, name):
    if not isinstance(row, dict) or set(row) != expected:
        raise BagUnitAreaError(f"{name}: unexpected, personal or missing input field")
    return row


def _id(value, name):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise BagUnitAreaError(f"{name}: invalid identifier")
    return value


def _rows(value, name):
    if not isinstance(value, list) or len(value) > MAX_RECORDS:
        raise BagUnitAreaError(f"{name}: invalid or oversized array")
    return value


def audit(payload):
    _fields(payload, {"schema", "as_of_date", "buildings", "units"}, "payload")
    if payload["schema"] != "bag-unit-area-normalised-v0":
        raise BagUnitAreaError("expected normalised analysis-only schema")
    when = payload["as_of_date"]
    try:
        if not isinstance(when, str) or date.fromisoformat(when).isoformat() != when:
            raise ValueError
    except ValueError as exc:
        raise BagUnitAreaError("invalid as_of_date") from exc

    buildings = {}
    for row in _rows(payload["buildings"], "buildings"):
        r = _fields(row, {"pand_id", "active"}, "building")
        pid = _id(r["pand_id"], "pand_id")
        if pid in buildings:
            raise BagUnitAreaError("duplicate BAG pand identity")
        if type(r["active"]) is not bool:
            raise BagUnitAreaError("building.active must be boolean")
        buildings[pid] = r["active"]
    if not buildings:
        raise BagUnitAreaError("no building references for unit-multiplicity QA")

    seen_units = set()
    statuses = Counter()
    totals = Counter()
    known_area_total = 0
    accepted_area_total = 0
    for row in _rows(payload["units"], "units"):
        r = _fields(row, {"unit_id", "area_m2", "pand_ids", "status"}, "unit")
        uid = _id(r["unit_id"], "unit_id")
        if uid in seen_units:
            raise BagUnitAreaError("duplicate BAG verblijfsobject unit")
        seen_units.add(uid)
        area = r["area_m2"]
        if type(area) is not int or area < 1 or area > 10_000_000:
            raise BagUnitAreaError("unit area must be a bounded positive integer")
        status = r["status"]
        if not isinstance(status, str) or not 1 <= len(status) <= 100:
            raise BagUnitAreaError("invalid unit status")
        references = r["pand_ids"]
        if not isinstance(references, list) or len(references) > 16:
            raise BagUnitAreaError("invalid pand array")
        ids = [_id(pid, "unit pand_id") for pid in references]
        if len(set(ids)) != len(ids):
            raise BagUnitAreaError("duplicate BAG pand reference within unit")
        statuses[status] += 1
        totals["all_units"] += 1
        if status != ACTIVE_UNIT_STATUS:
            totals["excluded_nonstandard_or_inactive_units"] += 1
            continue

        totals["active_unit_count"] += 1
        known_area_total += area
        if not ids:
            totals["active_units_without_building_link"] += 1
            totals["area_without_building_link_m2"] += area
        elif any(pid not in buildings for pid in ids):
            totals["active_units_with_unresolved_building_ids"] += 1
            totals["area_with_unresolved_building_ids_m2"] += area
        elif any(buildings[pid] is False for pid in ids):
            totals["active_units_with_non_active_building_link"] += 1
            totals["area_with_non_active_building_link_m2"] += area
        elif len(ids) != 1:
            totals["active_units_spanning_multiple_buildings"] += 1
            totals["area_ambiguous_multiple_buildings_m2"] += area
        else:
            totals["active_units_with_single_active_building"] += 1
            accepted_area_total += area

    excluded_active = (
        totals["area_without_building_link_m2"]
        + totals["area_with_unresolved_building_ids_m2"]
        + totals["area_with_non_active_building_link_m2"]
        + totals["area_ambiguous_multiple_buildings_m2"]
    )
    conservation = known_area_total == accepted_area_total + excluded_active
    if not conservation:
        raise BagUnitAreaError("active usable-area conservation invariant failed")

    # No original unit IDs, individual addresses, building IDs, timestamps
    # from a real provider, or per-building allocations in the output.
    return {
        "schema": "bag-unit-area-multiplicity-audit-v0",
        "analysis_only": True,
        "provider_feature_bytes_included": False,
        "source_admitted": False,
        "rights_reviewed": False,
        "gross_floor_area_verified": False,
        "rebuilding_volume_verified": False,
        "rebuild_value_or_insured_tiv_authorized": False,
        "as_of_date": when,
        "building_reference_count": len(buildings),
        "building_reference_active_count": sum(buildings.values()),
        "unit_count": len(seen_units),
        "status_counts": dict(sorted(statuses.items())),
        "active_unit_count": totals["active_unit_count"],
        "active_total_usable_area_m2": known_area_total,
        "active_unambiguously_linked_usable_area_m2": accepted_area_total,
        "active_units_with_single_active_building": totals["active_units_with_single_active_building"],
        "active_units_spanning_multiple_buildings": totals["active_units_spanning_multiple_buildings"],
        "area_ambiguous_multiple_buildings_m2": totals["area_ambiguous_multiple_buildings_m2"],
        "active_units_without_building_link": totals["active_units_without_building_link"],
        "area_without_building_link_m2": totals["area_without_building_link_m2"],
        "active_units_with_unresolved_building_ids": totals["active_units_with_unresolved_building_ids"],
        "area_with_unresolved_building_ids_m2": totals["area_with_unresolved_building_ids_m2"],
        "active_units_with_non_active_building_link": totals["active_units_with_non_active_building_link"],
        "area_with_non_active_building_link_m2": totals["area_with_non_active_building_link_m2"],
        "excluded_nonstandard_or_inactive_units": totals["excluded_nonstandard_or_inactive_units"],
        "conservation_check_passed": conservation,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="STRIPPED synthetic-only normalised JSON; no original address fields")
    args = parser.parse_args(argv)
    try:
        result = audit(load(args.input))
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
