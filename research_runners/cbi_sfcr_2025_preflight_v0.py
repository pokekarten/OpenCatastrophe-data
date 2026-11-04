# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, read-only structural preflight for a locally acquired 2025 Irish SFCR CSV.

This gate never downloads the publisher CSV, admits a model input, estimates
insured exposure, writes a database, or exports company-level observations.
The CSV must be acquired and rights-reviewed separately outside Git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TextIO

EXPECTED_HEADER = (
    "ReportingDate", "InstitutionName", "InstitutionNumber", "LEICode",
    "InstitutionType", "year_end", "templates", "row_full_name",
    "col_full_name", "row_name", "col_name", "row_code", "col_code",
    "comprow", "compcolumn", "Euro_value_or_percentage_value",
    "Euro_value_thousand_or_percentage_value", "Local_value_or_percentage_value",
)
NUMERIC_COLUMNS = EXPECTED_HEADER[-3:]
MAX_BYTES = 24 * 1024 * 1024
MAX_ROWS = 200_000
MAX_FIELD_LENGTH = 8192
TEMPLATE_RE = re.compile(r"S\.\d{2}\.\d{2}\.\d{2}\Z")
LEI_RE = re.compile(r"[A-Z0-9]{20}\Z")
DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}\Z")


class PreflightError(ValueError):
    """The input is not a valid bounded 2025 SFCR structural evidence sample."""


def _number(raw: str) -> bool:
    if raw.strip() == "":
        return False
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise PreflightError("non-numeric financial field") from exc
    if not value.is_finite():
        raise PreflightError("non-finite financial field")
    if value.adjusted() > 18:
        raise PreflightError("implausibly large numeric magnitude")
    return True


def inspect_csv(stream: TextIO) -> dict:
    """Validate format and aggregate shape without returning named undertaking data."""
    reader = csv.DictReader(stream, restkey="_extra")
    if reader.fieldnames is None:
        raise PreflightError("empty CSV")
    header = tuple(value.strip().lstrip("\ufeff") for value in reader.fieldnames)
    if header != EXPECTED_HEADER:
        raise PreflightError("unexpected 2025 SFCR column names/order")
    template_counts: Counter[str] = Counter()
    institution_ids: set[str] = set()
    dates: set[str] = set()
    missing_lei = 0
    filled_values: Counter[str] = Counter()
    row_count = 0
    try:
        for row in reader:
            row_count += 1
            if row_count > MAX_ROWS:
                raise PreflightError("CSV exceeds declared row bound")
            if None in row or "_extra" in row or any(v is None for v in row.values()):
                raise PreflightError("truncated or extra CSV fields")
            if any(len(value) > MAX_FIELD_LENGTH for value in row.values()):
                raise PreflightError("unbounded CSV field")
            dt = row["ReportingDate"].strip()
            if not DATE_RE.fullmatch(dt):
                raise PreflightError("reporting date must be DD/MM/YYYY")
            try:
                parsed = date(int(dt[6:]), int(dt[3:5]), int(dt[:2]))
            except ValueError as exc:
                raise PreflightError("invalid reporting date") from exc
            if parsed.year != 2025 or row["year_end"].strip() != "2025":
                raise PreflightError("mixed reporting year; review exact source identity")
            if not row["InstitutionName"].strip() or not row["InstitutionType"].strip():
                raise PreflightError("missing undertaking identity/type")
            entity_id = row["InstitutionNumber"].strip()
            if not re.fullmatch(r"[0-9]+", entity_id):
                raise PreflightError("missing or malformed institution number")
            lei = row["LEICode"].strip()
            if not lei:
                missing_lei += 1
            elif not LEI_RE.fullmatch(lei):
                raise PreflightError("malformed LEI (format only; checksum unverified)")
            template = row["templates"].strip()
            if not TEMPLATE_RE.fullmatch(template):
                raise PreflightError("unexpected QRT template code")
            for col in ("row_code", "col_code"):
                code = row[col].strip()
                if code and not re.fullmatch((r"R\d{4}" if col == "row_code" else r"C\d{4}"), code):
                    raise PreflightError("invalid QRT row/column code")
            for col in NUMERIC_COLUMNS:
                if _number(row[col]):
                    filled_values[col] += 1
            dates.add(dt)
            institution_ids.add(entity_id)
            template_counts[template] += 1
    except (csv.Error, UnicodeError) as exc:
        raise PreflightError("malformed CSV stream") from exc
    if not row_count:
        raise PreflightError("no SFCR data rows")
    return {
        "profile": "cbi-sfcr-2025-offline-structural-preflight-v0",
        "source_year": 2025,
        "row_count": row_count,
        "distinct_institution_numbers": len(institution_ids),
        "distinct_reporting_dates": len(dates),
        "rows_with_missing_lei": missing_lei,
        "qrt_template_row_counts": dict(sorted(template_counts.items())),
        "populated_numeric_field_counts": dict(sorted(filled_values.items())),
        "source_level_only": True,
        "company_observations_exported": False,
        "rights_cleared": False,
        "model_input_admitted": False,
        "insured_tiv_or_cat_loss_inferred": False,
        "source_byte_sha256": None,
    }


def inspect_file(path: Path) -> dict:
    path = path.resolve(strict=True)
    repo_root = Path(__file__).resolve().parents[1]
    if path.is_relative_to(repo_root):
        raise PreflightError("source-data bytes must remain outside public Git checkout")
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise PreflightError("source path is not a bounded local CSV file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            result = inspect_csv(handle)
    except UnicodeError as exc:
        raise PreflightError("original CSV requires an explicit encoding review") from exc
    result["source_byte_sha256"] = digest.hexdigest()
    result["source_byte_count"] = path.stat().st_size
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Locally acquired original 2025 CSV outside this repository")
    args = parser.parse_args(argv)
    try:
        result = inspect_file(args.csv)
    except (PreflightError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "STRUCTURE_CHECKED_NOT_ADMITTED", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
