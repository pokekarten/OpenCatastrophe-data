# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed CFDID CSV hierarchy preflight, without fetching or retaining source data.

The published CFDID v1.1 event IDs encode parent/sub-event relationships:
YYYY-NNN, YYYY-NNN-NN, YYYY-NNN-NN-NN. For parent-level aggregate loss
statistics use L1 rows only, never add L2/L3 rows to their parents.

The original 2026 Zenodo CSV SHA-256 was pinned in a separate research receipt.
Original-mode execution requires the operator's exact verified SHA-256.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import stat
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ID_PATTERNS = {
    "L1": re.compile(r"^\d{4}-\d{3}$"),
    "L2": re.compile(r"^\d{4}-\d{3}-\d{2}$"),
    "L3": re.compile(r"^\d{4}-\d{3}-\d{2}-\d{2}$"),
}
COLUMN_LEVEL = "Event level"
COLUMN_ID = "Event ID"
COLUMN_LOSS = "Direct economic losses (million CNY)"
COLUMN_START_YEAR = "Start year"
COLUMN_START_MONTH = "Start month"
COLUMN_START_DAY = "Start day"
COLUMN_END_YEAR = "End year"
COLUMN_END_MONTH = "End month"
COLUMN_END_DAY = "End day"
DATE_COLUMNS = {COLUMN_START_YEAR, COLUMN_START_MONTH, COLUMN_START_DAY,
                COLUMN_END_YEAR, COLUMN_END_MONTH, COLUMN_END_DAY}
EXPECTED_ORIGINAL_COUNTS = {"L1": 1391, "L2": 300, "L3": 25}
MAX_CSV_BYTES = 20 * 1024 * 1024


class PreflightError(ValueError):
    """Unusable source CSV or unsupported source structure."""


def _amount(text: str) -> Decimal | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise PreflightError("Non-numeric economic-loss value") from exc
    if not value.is_finite() or value < 0:
        raise PreflightError("Loss must be nonnegative and finite")
    return value


def _date_component(value: str, column: str, *, required: bool = False) -> int | None:
    raw = value.strip()
    if not raw:
        if required:
            raise PreflightError(f"Missing required {column}")
        return None
    if not re.fullmatch(r"[0-9]+", raw):
        raise PreflightError(f"Invalid integer {column}")
    return int(raw)


def _calendar_check(row: dict[str, str], event_id: str) -> bool:
    """Check dates without inventing exact dates for partially reported periods.

    Returns True when the start day is unknown; callers may count this quality
    flag but must not turn it into the first day of the month as an observation.
    """
    year = _date_component(row[COLUMN_START_YEAR], COLUMN_START_YEAR, required=True)
    month = _date_component(row[COLUMN_START_MONTH], COLUMN_START_MONTH, required=True)
    start_day = _date_component(row[COLUMN_START_DAY], COLUMN_START_DAY)
    end_year = _date_component(row[COLUMN_END_YEAR], COLUMN_END_YEAR)
    end_month = _date_component(row[COLUMN_END_MONTH], COLUMN_END_MONTH)
    end_day = _date_component(row[COLUMN_END_DAY], COLUMN_END_DAY)
    if year is None or month is None or year != int(event_id[:4]):
        raise PreflightError("Event ID year differs from the reported Start year")
    if not (1994 <= year <= 2023):
        raise PreflightError("CFDID source year outside 1994-2023")
    try:
        # The lower bound is for chronology checks only, not an imputed date.
        first_possible_start = date(year, month, start_day or 1)
        if end_month is not None and end_year is None:
            raise PreflightError("End month provided without End year")
        if end_day is not None and end_month is None:
            raise PreflightError("End day provided without End month")
        if end_year is not None:
            if not (1994 <= end_year <= 2023):
                raise PreflightError("End year outside 1994-2023")
            final_month = end_month or 12
            final_day = end_day or (date(end_year + (final_month == 12),
                                           final_month % 12 + 1, 1) - timedelta(days=1)).day
            final_possible_end = date(end_year, final_month, final_day)
            if final_possible_end < first_possible_start:
                raise PreflightError("End date interval precedes start date interval")
    except ValueError as exc:
        raise PreflightError("Invalid reported CFDID calendar date") from exc
    return start_day is None


def audit_csv_text(source: str, *, strict_original: bool = False) -> dict[str, object]:
    reader = csv.DictReader(io.StringIO(source, newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise PreflightError("Missing or duplicate CSV headings")
    if not ({COLUMN_LEVEL, COLUMN_ID, COLUMN_LOSS} | DATE_COLUMNS).issubset(reader.fieldnames):
        raise PreflightError("Required original CFDID headings absent")

    counts = {level: 0 for level in ID_PATTERNS}
    row_ids: set[str] = set()
    missing_parents: set[str] = set()
    required_parents: set[str] = set()
    l1_loss_records = 0
    l1_loss_total = Decimal("0")
    rows = 0
    rows_missing_start_day = 0
    for row in reader:
        rows += 1
        if None in row or any(v is None for v in row.values()):
            raise PreflightError("Unexpected extra or missing CSV columns")
        level = row[COLUMN_LEVEL].strip()
        event_id = row[COLUMN_ID].strip()
        if level not in ID_PATTERNS or not ID_PATTERNS[level].fullmatch(event_id):
            raise PreflightError("Event ID does not match declared hierarchy")
        if event_id in row_ids:
            raise PreflightError("Duplicate event ID")
        row_ids.add(event_id)
        rows_missing_start_day += int(_calendar_check(row, event_id))
        counts[level] += 1
        if level != "L1":
            required_parents.add(event_id.rsplit("-", 1)[0])
        loss = _amount(row[COLUMN_LOSS])
        if level == "L1" and loss is not None:
            l1_loss_records += 1
            l1_loss_total += loss
    if not rows:
        raise PreflightError("No source records")
    missing_parents = required_parents - row_ids
    if missing_parents:
        raise PreflightError(f"Missing parents for {len(missing_parents)} sub-event rows")
    if strict_original and counts != EXPECTED_ORIGINAL_COUNTS:
        raise PreflightError("CFDID v1.1 published event-level row counts do not match")
    # Do not publish exact event IDs, coordinates, or original row-level records.
    return {
        "rows": rows,
        "rows_missing_reported_start_day": rows_missing_start_day,
        "by_event_level": counts,
        "parent_links_present": True,
        "reported_l1_loss_records": l1_loss_records,
        "l1_reported_direct_loss_million_cny": str(l1_loss_total),
        "excludes_nested_l2_l3_from_loss_sum": True,
        "strict_original_counts_checked": strict_original,
    }


def _read_verified_csv(path: Path, sha256: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
        raise PreflightError("An independently pinned 64-digit SHA-256 is required")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CSV_BYTES:
        raise PreflightError("Source must be a regular CSV file of at most 20 MiB")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256.lower():
        raise PreflightError("Original CSV SHA-256 mismatch")
    try:
        return data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise PreflightError("Only UTF-8 CFDID CSV is supported") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True, help="Independently pinned original-file SHA-256")
    args = parser.parse_args()
    try:
        data = _read_verified_csv(args.csv, args.expected_sha256)
        result = audit_csv_text(data, strict_original=True)
    except (OSError, PreflightError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
