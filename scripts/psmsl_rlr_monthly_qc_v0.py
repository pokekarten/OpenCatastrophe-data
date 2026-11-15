# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, byte-preserving preflight for PSMSL Cuxhaven 2 (station 7) RLR monthly data.

No download, legal admission, datum conversion, or CAT-model use is performed.
Official source: https://psmsl.org/data/obtaining/stations/7.php
Format: https://psmsl.org/data/obtaining/notes.php
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

MAX_ORIGINAL_BYTES = 2 * 1024 * 1024
_STATION_ID = 7


def _year_month(value: str) -> tuple[int, int]:
    if not re.fullmatch(r"[0-9]{4}\.[0-9]{4}", value):
        raise ValueError("invalid PSMSL decimal month format")
    decimal_year = Decimal(value)
    year = int(decimal_year)
    month = int(((decimal_year - year) * 12 + Decimal("0.5")).to_integral_value(rounding=ROUND_HALF_UP))
    if not 1 <= month <= 12:
        raise ValueError("month is out of range")
    expected = Decimal(year) + (Decimal(month) - Decimal("0.5")) / 12
    if abs(decimal_year - expected) > Decimal("0.00006"):
        raise ValueError("decimal month is not centred on a calendar month")
    return year, month


def screen_original_bytes(original: bytes) -> dict[str, object]:
    """Validate a *locally supplied* original station-7 file, without transforming it."""
    if not original or len(original) > MAX_ORIGINAL_BYTES:
        raise ValueError("empty or oversized original")
    try:
        lines = original.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("non-ASCII original") from exc
    if not lines:
        raise ValueError("empty original")

    previous_month = None
    missing_months = interpolated_months = flagged_months = 0
    first_month = last_month = None
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            raise ValueError(f"blank line {line_number}")
        columns = [item.strip() for item in raw_line.split(";")]
        if len(columns) != 4:
            raise ValueError(f"invalid column count on line {line_number}")
        date_field, mean_field, missing_field, flag_field = columns
        year, month = _year_month(date_field)
        if not re.fullmatch(r"-?[0-9]+", mean_field):
            raise ValueError(f"non-integer mean level on line {line_number}")
        if not re.fullmatch(r"[0-9]{1,2}", missing_field):
            raise ValueError(f"invalid missing-day field on line {line_number}")
        if not re.fullmatch(r"[0-7]{3}", flag_field):
            raise ValueError(f"invalid octal attention flag on line {line_number}")

        mean_mm = int(mean_field)
        missing_days = int(missing_field)
        if missing_days != 99 and missing_days > calendar.monthrange(year, month)[1]:
            raise ValueError(f"impossible missing-day count on line {line_number}")
        ordinal = year * 12 + month - 1
        if previous_month is not None and ordinal != previous_month + 1:
            raise ValueError(f"missing, duplicated or unordered month on line {line_number}")
        previous_month = ordinal
        first_month = first_month or f"{year:04d}-{month:02d}"
        last_month = f"{year:04d}-{month:02d}"
        missing_months += mean_mm == -99999
        interpolated_months += missing_days == 99
        flagged_months += flag_field != "000"

    return {
        "source_id": "psmsl.global-tide-gauge-sea-level",
        "product": "PSMSL CUXHAVEN 2 RLR monthly",
        "station_id": _STATION_ID,
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "original_bytes": len(original),
        "rows": len(lines),
        "first_month": first_month,
        "last_month": last_month,
        "missing_months": missing_months,
        "interpolated_months": interpolated_months,
        "flagged_months": flagged_months,
        "source_rights_and_service_automation": "not_verified_for_this_sample",
        "station_datum_review": "required: historical MTL to MSL (-88 mm before 1984) already applied in PSMSL RLR; do not apply again",
        "cat_model_admission": "not_admitted",
        "neon_storage": "storage_not_verified",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_file", type=Path, help="existing permitted original station-7 RLR monthly file")
    args = parser.parse_args()
    try:
        with args.original_file.open("rb") as handle:
            original = handle.read(MAX_ORIGINAL_BYTES + 1)
        result = screen_original_bytes(original)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
