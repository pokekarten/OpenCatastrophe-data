#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Byte-receipt-bound, NO-LOSS CSV preflight for two versioned EU research products.

This is only a fail-closed format and provenance preflight for independently
downloaded files. It does not redistribute any provider data, infer insured
claims, construct asset exposures, recalibrate CAT models or authorize use.
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

MAX_SOURCE_BYTES = 20_000_000
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
COUNTRY_RE = re.compile(r"[A-Z][A-Z0-9]{1,7}\Z")
EVENT_ID_RE = re.compile(r"[0-9]+\Z")
YEAR_RE = re.compile(r"[0-9]{4}\Z")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
HANZE_COLUMNS = (
    "id", "country_code", "event_start_date_year", "country_name",
    "start_date", "end_date", "event_type", "hips_label", "hips_identifier",
    "hips_version", "event_source", "admin_unit_nomenclature",
    "admin_unit_level", "admin_unit_year", "admin_unit_code",
    "area_affected", "casualty_count", "ppl_affected",
    "economic_loss_value_nominal", "currency_code",
    "economic_loss_value_eur", "reference_year_eur", "cause", "notes",
    "sources_author_year", "sources_impact_information", "change_type",
    "entry_date", "last_update",
)
EXPOSURE_COLUMNS = (
    "IndicatorCode", "Indicator", "Unit", "CountryCode", "Country",
    *(str(year) for year in range(2000, 2025)),
)

class SourcePreflightError(ValueError):
    """Input bytes or version-specific CSV semantics do not meet preflight."""

def _read(blob: bytes, expected_sha256: str, columns: tuple[str, ...]):
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_SOURCE_BYTES:
        raise SourcePreflightError("source must be nonempty bytes at most 20 MB")
    if not isinstance(expected_sha256, str) or not SHA256_RE.fullmatch(expected_sha256):
        raise SourcePreflightError("expected source SHA256 must be lowercase hex")
    observed_sha256 = hashlib.sha256(blob).hexdigest()
    if observed_sha256 != expected_sha256:
        raise SourcePreflightError("source bytes differ from independently pinned SHA256")
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeError as exc:
        raise SourcePreflightError("invalid UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise SourcePreflightError("missing CSV header") from exc
    if header != list(columns):
        raise SourcePreflightError("unexpected, missing, reordered or duplicate CSV header")
    rows = []
    try:
        for line_number, values in enumerate(reader, start=2):
            if len(values) != len(columns):
                raise SourcePreflightError(f"CSV row {line_number} width mismatch")
            rows.append(dict(zip(columns, values)))
            if len(rows) > 200_000:
                raise SourcePreflightError("row limit exceeded")
    except csv.Error as exc:
        raise SourcePreflightError("malformed quoted CSV") from exc
    if not rows:
        raise SourcePreflightError("source has no CSV rows")
    return rows, observed_sha256

def _nonnegative(raw: str, label: str) -> Decimal | None:
    if raw == "":
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise SourcePreflightError(f"{label}: invalid numeric field") from exc
    if not value.is_finite() or value < 0:
        raise SourcePreflightError(f"{label}: negative or nonfinite value")
    return value

def inspect_hanze_v302(blob: bytes, expected_sha256: str) -> dict:
    """Report bounded *economic* impact completeness without emitting values."""
    rows, digest = _read(blob, expected_sha256, HANZE_COLUMNS)
    seen = set()
    years = set()
    observed_losses = 0
    for row in rows:
        event_id = row["id"]
        if not EVENT_ID_RE.fullmatch(event_id) or event_id in seen:
            raise SourcePreflightError("invalid or repeated HANZE event ID")
        seen.add(event_id)
        if not COUNTRY_RE.fullmatch(row["country_code"]):
            raise SourcePreflightError("invalid event country code")
        if not YEAR_RE.fullmatch(row["event_start_date_year"]) or not (
            DATE_RE.fullmatch(row["start_date"]) and DATE_RE.fullmatch(row["end_date"])
        ):
            raise SourcePreflightError("invalid event date/year format; require ASCII YYYY-MM-DD")
        try:
            year = int(row["event_start_date_year"])
            start = date.fromisoformat(row["start_date"])
            end = date.fromisoformat(row["end_date"])
        except (ValueError, TypeError) as exc:
            raise SourcePreflightError("invalid event date/year") from exc
        if not 1870 <= year <= 2025 or start.year != year or not start <= end:
            raise SourcePreflightError("invalid event year/date ordering")
        years.add(year)
        if row["admin_unit_year"] not in ("", "2024"):
            raise SourcePreflightError("unexpected geographic vintage; expected NUTS/ITL 2024")
        if row["reference_year_eur"] not in ("", "2025"):
            raise SourcePreflightError("unexpected economic loss reference year")
        loss = _nonnegative(row["economic_loss_value_eur"], "economic_loss_value_eur")
        if loss is not None:
            if row["reference_year_eur"] != "2025":
                raise SourcePreflightError("observed 2025 EUR loss missing price reference year")
            observed_losses += 1
        _nonnegative(row["economic_loss_value_nominal"], "economic_loss_value_nominal")
    return {
        "source": "HANZE_v3.0.2_beta",
        "evidence_class": "FORMAT_PREFLIGHT_ONLY",
        "raw_csv_sha256": digest,
        "event_count": len(rows),
        "economic_loss_present_count": observed_losses,
        "economic_loss_missing_count": len(rows) - observed_losses,
        "observed_event_year_range": [min(years), max(years)],
        "economic_loss_stage": "reported_economic_not_insured",
        "insured_loss_calculated": False,
        "provider_rows_exported": False,
        "source_admitted": False,
    }

def inspect_residential_v2025(blob: bytes, expected_sha256: str) -> dict:
    """Check wide 2000-2024 indicator rows, not assign property valuations."""
    rows, digest = _read(blob, expected_sha256, EXPOSURE_COLUMNS)
    seen = set()
    present = 0
    for row in rows:
        code = row["IndicatorCode"].strip()
        country = row["CountryCode"].strip()
        if not code or not COUNTRY_RE.fullmatch(country):
            raise SourcePreflightError("missing indicator code or invalid country/aggregate code")
        key = (code, country)
        if key in seen:
            raise SourcePreflightError("duplicate indicator/country row")
        seen.add(key)
        if not row["Indicator"].strip() or not row["Unit"].strip() or not row["Country"].strip():
            raise SourcePreflightError("missing indicator/unit/country metadata")
        for year in range(2000, 2025):
            value = _nonnegative(row[str(year)].strip(), f"{country}/{code}/{year}")
            if value is not None:
                present += 1
    return {
        "source": "Residential_exposure_v2025",
        "evidence_class": "FORMAT_PREFLIGHT_ONLY",
        "raw_csv_sha256": digest,
        "indicator_country_row_count": len(rows),
        "numeric_cells_present": present,
        "numeric_cells_missing": len(rows) * 25 - present,
        "observed_year_column_range": [2000, 2024],
        "geographic_stage": "country_aggregates_not_asset_exposure",
        "insured_tiv_calculated": False,
        "provider_rows_exported": False,
        "source_admitted": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("hanze-v3.0.2-beta", "residential-v2025"))
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.csv_file.resolve() == args.out.resolve():
        raise SourcePreflightError("refusing to overwrite original source")
    blob = args.csv_file.read_bytes()
    if args.source == "hanze-v3.0.2-beta":
        result = inspect_hanze_v302(blob, args.expected_source_sha256)
    else:
        result = inspect_residential_v2025(blob, args.expected_source_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
