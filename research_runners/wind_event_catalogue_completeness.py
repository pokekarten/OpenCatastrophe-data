# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Validate declarations in a monthly wind-event manifest; never infer zeros."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


INPUT_SCHEMA = "WIND_EVENT_CATALOGUE_MONTHLY_INPUT_V1"
OUTPUT_SCHEMA = "WIND_EVENT_CATALOGUE_COMPLETENESS_V1"
MONTH_RE = re.compile(r"\d{4}-(?:0[1-9]|1[0-2])\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _fail_if(condition: bool, message: str) -> None:
    if condition:
        raise ValueError(message)


def _month(value: object, field: str) -> datetime:
    _fail_if(not isinstance(value, str) or MONTH_RE.fullmatch(value) is None,
             f"{field} must use YYYY-MM")
    return datetime.strptime(value, "%Y-%m")


def _required_text(value: object, field: str) -> str:
    _fail_if(not isinstance(value, str) or not value.strip(), f"{field} must be nonempty text")
    _fail_if(value != value.strip(), f"{field} must not have surrounding whitespace")
    return value


def audit(data: object) -> dict:
    """Check a declared month/event ledger, without authenticating its sources.

    ``source_sha256`` values are format-checked only. An independent original
    reader must hash downloaded source bytes and prove event/footprint fields.
    """
    _fail_if(type(data) is not dict, "manifest must be an object")
    _fail_if(data.get("schema") != INPUT_SCHEMA, "unsupported manifest schema")

    start_value = _month(data.get("first_month"), "first_month")
    end_value = _month(data.get("last_month"), "last_month")
    _fail_if(end_value < start_value, "Reversed coverage")
    first_month = start_value.strftime("%Y-%m")
    last_month = end_value.strftime("%Y-%m")

    tracker = _required_text(data.get("tracking_algorithm"), "tracking_algorithm")
    product_version = _required_text(data.get("product_version"), "product_version")
    deliveries = data.get("months")
    _fail_if(type(deliveries) is not list, "months must be a list")

    expected: list[str] = []
    current = start_value
    while current <= end_value:
        expected.append(current.strftime("%Y-%m"))
        current = datetime(current.year + (current.month == 12), current.month % 12 + 1, 1)

    months: set[str] = set()
    event_ids: set[str] = set()
    missing_footprints: list[str] = []
    zero_event_months: list[str] = []
    for index, delivery in enumerate(deliveries):
        field = f"months[{index}]"
        _fail_if(type(delivery) is not dict, f"{field} must be an object")
        month_value = delivery.get("month")
        month_start = _month(month_value, f"{field}.month")
        month = month_start.strftime("%Y-%m")
        _fail_if(month not in expected, f"unexpected month: {month}")
        _fail_if(month in months, f"duplicate month: {month}")
        _fail_if(delivery.get("tracking_algorithm") != tracker,
                 f"mixed tracking algorithms at {month}")
        _fail_if(delivery.get("product_version") != product_version,
                 f"mixed product versions at {month}")
        _fail_if(delivery.get("delivery_complete") is not True,
                 f"incomplete source delivery at {month}")

        digest = delivery.get("source_sha256")
        _fail_if(not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None,
                 f"invalid source_sha256 at {month}")
        events = delivery.get("events")
        _fail_if(type(events) is not list, f"events must be a list at {month}")
        if not events:
            zero_event_months.append(month)
        for event_index, event in enumerate(events):
            event_field = f"{field}.events[{event_index}]"
            _fail_if(type(event) is not dict, f"{event_field} must be an object")
            identity = _required_text(event.get("event_id"), f"{event_field}.event_id")
            _fail_if(identity in event_ids, f"duplicate physical event identity: {identity}")
            event_ids.add(identity)
            footprint_verified = event.get("footprint_verified")
            _fail_if(type(footprint_verified) is not bool,
                     f"{event_field}.footprint_verified must be boolean")
            if not footprint_verified:
                missing_footprints.append(identity)
        months.add(month)

    missing_months = sorted(set(expected) - months)
    month_coverage_complete = not missing_months
    event_footprints_complete = not missing_footprints
    return {
        "schema": OUTPUT_SCHEMA,
        "first_month": first_month,
        "last_month": last_month,
        "tracking_algorithm": tracker,
        "product_version": product_version,
        "missing_months": missing_months,
        "explicit_zero_event_months": zero_event_months,
        "distinct_declared_events": len(event_ids),
        "events_without_verified_footprint": missing_footprints,
        "manifest_month_coverage_complete": month_coverage_complete,
        "manifest_event_footprints_complete": event_footprints_complete,
        "declared_catalogue_structure_complete": (
            month_coverage_complete and event_footprints_complete
        ),
        "source_bytes_independently_verified": False,
        "frequency_weights_verified": False,
        "annual_risk_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = audit(data)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
