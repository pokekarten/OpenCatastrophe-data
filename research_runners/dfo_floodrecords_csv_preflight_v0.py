#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, SHA256-bound preflight for DFO Global Flood Records CSV v0.9.0.

Use ONLY on independently downloaded, version-pinned original bytes. This
validates provider format and normalizes dates, not data rights or flood science.
No files from the external publisher are bundled in this repository.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re

HEADER = (
    "﹟", "Glide ﹟", "Start Date", "End Date", "Country",
    "Area (km²)", "Source", "Main Cause", "Fatalities", "Displaced",
    "Severity", "Flood impact index",
)
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
DATE = re.compile(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{2})\Z")
NUMBER = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?\Z")
DECLARED_RELEASE_END_YEAR = 2023  # Publisher description; real CSV preview includes 2024.


class DFOPreflightError(ValueError):
    """Original CSV format, provenance, or scientific usage was ambiguous."""


def _date(raw: str, field: str) -> str:
    match = DATE.fullmatch(raw.strip())
    if not match:
        raise DFOPreflightError(field + " must be unambiguous M/D/YY")
    month, day, yy = (int(x) for x in match.groups())
    year = 1900 + yy if yy >= 85 else 2000 + yy
    try:
        result = date(year, month, day)
    except ValueError as exc:
        raise DFOPreflightError(field + " is not a Gregorian date") from exc
    if year < 1985 or year > 2026:
        raise DFOPreflightError(field + " outside supported DFO release calendar")
    return result.isoformat()


def _quantity(raw: str, field: str, *, integer: bool = False) -> int | str | None:
    value = raw.strip()
    if not value:
        return None  # Unknown is NEVER converted to zero.
    if not NUMBER.fullmatch(value):
        raise DFOPreflightError(field + " has invalid ASCII numeric syntax")
    if integer and "." in value:
        raise DFOPreflightError(field + " must be a count")
    try:
        amount = Decimal(value.replace(",", ""))
    except InvalidOperation as exc:
        raise DFOPreflightError(field + " is not numeric") from exc
    if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000000"):
        raise DFOPreflightError(field + " is not a supported nonnegative quantity")
    return int(amount) if integer else str(amount)


def parse_dfo_csv(blob: bytes) -> dict:
    """Produce an explicit *reported-event* table; never insured or flood-depth loss."""
    if type(blob) is not bytes or not blob or len(blob) > 25_000_000:
        raise DFOPreflightError("original CSV bytes must be nonempty and <= 25 MB")
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeError as exc:
        raise DFOPreflightError("DFO original CSV must be valid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if reader.fieldnames != list(HEADER):
        raise DFOPreflightError("unexpected DFO v0.9.0 CSV headings; refuse schema drift")
    seen = set()
    events = []
    observed_beyond_declared = 0
    for line_no, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise DFOPreflightError(f"row {line_no}: invalid CSV column count")
        raw_id = row["﹟"].strip()
        if not re.fullmatch(r"[0-9]+", raw_id) or raw_id in seen:
            raise DFOPreflightError(f"row {line_no}: invalid or duplicate source event ID")
        seen.add(raw_id)
        raw_start = row["Start Date"].strip()
        raw_end = row["End Date"].strip()
        start = _date(raw_start, "Start Date")
        end = _date(raw_end, "End Date")
        if end < start:
            raise DFOPreflightError(f"row {line_no}: end date precedes start")
        country = row["Country"].strip()
        if not country:
            raise DFOPreflightError(f"row {line_no}: empty country name")
        if int(start[:4]) > DECLARED_RELEASE_END_YEAR or int(end[:4]) > DECLARED_RELEASE_END_YEAR:
            observed_beyond_declared += 1
        events.append({
            "dfo_event_id": raw_id,
            "glide_id_unverified": row["Glide ﹟"].strip() or None,
            "original_start_date": raw_start,
            "original_end_date": raw_end,
            "start_date": start,
            "end_date": end,
            "country_text_unparsed": country,
            "reported_area_affected_km2_not_inundation": _quantity(row["Area (km²)"], "Area (km²)"),
            "reported_cause_text": row["Main Cause"].strip() or None,
            "source_label": row["Source"].strip() or None,
            "reported_fatalities": _quantity(row["Fatalities"], "Fatalities", integer=True),
            "reported_displaced": _quantity(row["Displaced"], "Displaced", integer=True),
            "reported_severity": _quantity(row["Severity"], "Severity"),
            "reported_flood_impact_index": _quantity(row["Flood impact index"], "Flood impact index"),
        })
    if not events:
        raise DFOPreflightError("no source events")
    events.sort(key=lambda e: int(e["dfo_event_id"]))
    return {
        "evidence_class": "REPORTED_HISTORICAL_FLOOD_EVENTS_NO_DEPTH_NO_INSURED_LOSS",
        "provider": "Dartmouth Flood Observatory",
        "dataset": "Global Flood Records",
        "pinned_release": "v0.9.0",
        "version_url": "https://zenodo.org/records/19288171",
        "source_csv_sha256": hashlib.sha256(blob).hexdigest(),
        "reported_event_count": len(events),
        "observed_first_start_date": min(e["start_date"] for e in events),
        "observed_last_end_date": max(e["end_date"] for e in events),
        "provider_declared_release_end_year": DECLARED_RELEASE_END_YEAR,
        "event_rows_reaching_beyond_declared_end_year": observed_beyond_declared,
        "published_release_end_year_consistent_with_csv": observed_beyond_declared == 0,
        "country_labels_are_not_geographic_boundaries": True,
        "missing_measurements_are_not_zero": True,
        "flood_depth_observed": False,
        "insured_losses_observed": False,
        "license_review_completed_by_this_preflight": False,
        "model_source_admission_approved": False,
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.csv_file.resolve() == args.out.resolve():
        raise DFOPreflightError("refusing to overwrite original source file")
    if not DIGEST.fullmatch(args.expected_source_sha256):
        raise DFOPreflightError("expected SHA256 must be lowercase hexadecimal")
    blob = args.csv_file.read_bytes()
    if hashlib.sha256(blob).hexdigest() != args.expected_source_sha256:
        raise DFOPreflightError("original source SHA256 mismatch")
    result = parse_dfo_csv(blob)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
