# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline PSMSL Revised Local Reference monthly-file format preflight.

No station is acquired here; this checks independently authorized local source
bytes only. Service rights, RLR datum history, science and admission stay open.
Publisher specification: https://psmsl.org/data/obtaining/notes.php
"""

from __future__ import annotations

import argparse
import calendar
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "psmsl.global-tide-gauge-sea-level"
MAX_BYTES = 2 * 1024 * 1024
MAX_MONTHS = 6000
DATE_RE = re.compile(r"\d{4}\.\d{4}\Z")
FLAG_RE = re.compile(r"[0-7]{3}\Z")
INT_RE = re.compile(r"-?\d+\Z")


class PSMSLPreflightError(ValueError):
    """Original file fails the RLR monthly grammar or declared time semantics."""


def _month(decimal_text: str, line: int) -> tuple[int, int]:
    if not DATE_RE.fullmatch(decimal_text):
        raise PSMSLPreflightError(f"line {line}: expected YYYY.dddd month")
    try:
        date = Decimal(decimal_text)
    except InvalidOperation as exc:
        raise PSMSLPreflightError(f"line {line}: invalid decimal year") from exc
    year = int(date)
    if not 1600 <= year <= 2100:
        raise PSMSLPreflightError(f"line {line}: year outside review window")
    for month in range(1, 13):
        expected = Decimal(year) + (Decimal(month) - Decimal('0.5')) / Decimal(12)
        if abs(date - expected) <= Decimal('0.000051'):
            return year, month
    raise PSMSLPreflightError(f"line {line}: non-calendar-month decimal")


def audit_bytes(raw: bytes, *, station_id: int) -> dict[str, object]:
    """Return exact *input* digest, not an independently verified provider digest."""
    if not isinstance(station_id, int) or isinstance(station_id, bool) or not 1 <= station_id <= 999999:
        raise PSMSLPreflightError('invalid numeric station ID')
    if not raw or len(raw) > MAX_BYTES or b'\x00' in raw:
        raise PSMSLPreflightError('empty, oversized or binary input')
    try:
        text = raw.decode('ascii')
    except UnicodeDecodeError as exc:
        raise PSMSLPreflightError('non-ASCII station file') from exc
    lines = text.splitlines()
    if not lines or len(lines) > MAX_MONTHS:
        raise PSMSLPreflightError('no monthly records or too many records')
    missing_monthly_means = interpolated_months = caution_flags = mtl_flags = 0
    previous_key: int | None = None
    for line, value in enumerate(lines, 1):
        fields = [field.strip() for field in value.split(';')]
        if len(fields) != 4:
            raise PSMSLPreflightError(f'line {line}: expected four semicolon-separated fields')
        year, month = _month(fields[0], line)
        key = year * 12 + month - 1
        if previous_key is not None and key != previous_key + 1:
            raise PSMSLPreflightError(f'line {line}: month gap, duplicate or time reversal')
        previous_key = key
        msl, missing_days, flag_text = fields[1:]
        if not INT_RE.fullmatch(msl) or not INT_RE.fullmatch(missing_days):
            raise PSMSLPreflightError(f'line {line}: non-integer mm or missing-day count')
        msl_int = int(msl)
        days = int(missing_days)
        if days != 99 and not (0 <= days <= calendar.monthrange(year, month)[1]):
            raise PSMSLPreflightError(f'line {line}: invalid missing days')
        if not FLAG_RE.fullmatch(flag_text):
            raise PSMSLPreflightError(f'line {line}: malformed octal flag')
        # PSMSL octal-coded flag bits: 001 caution, 010 mean tidal level.
        flags = int(flag_text, 8)
        caution_flags += bool(flags & 0o001)
        mtl_flags += bool(flags & 0o010)
        missing_monthly_means += msl_int == -99999
        interpolated_months += days == 99
    return {
        'source_id': SOURCE_ID,
        'station_id_claimed': station_id,
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'input_bytes': len(raw),
        'calendar_month_count': len(lines),
        'missing_monthly_means': missing_monthly_means,
        'interpolated_months': interpolated_months,
        'caution_flag_months': caution_flags,
        'mean_tidal_level_flag_months': mtl_flags,
        'provider_origin_verified': False,
        'station_datum_and_authority_reviewed': False,
        'api_terms_verified': False,
        'scientific_model_admission': False,
        'neon_write_readback': 'not_tested',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('local_file', type=Path, help='already-authorized local RLR monthly file outside Git')
    parser.add_argument('--station-id', type=int, required=True)
    args = parser.parse_args()
    try:
        with args.local_file.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        print(json.dumps(audit_bytes(raw, station_id=args.station_id), sort_keys=True))
    except (OSError, PSMSLPreflightError) as exc:
        parser.exit(status=2, message=f'BLOCKED: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
