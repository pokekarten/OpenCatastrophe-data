# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only CFDID v1.1 annual coverage reconciliation with original XLSX and CSV.

Unlike an insurance loss calibration, this is a *within-source* comparison
between CFDID L1 reported impacts and national official annual statistics.
The inputs share upstream Chinese official reports. No external downloads,
CSV rows, coordinates or source workbook are copied into Git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import stat
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from research_runners.cfdid_hierarchy_preflight_v0 import (
    PreflightError, audit_csv_text,
)

EXPECTED_CSV_SHA256 = "b2cc978a317710b5379fdc42cff787800f1bbaee505c5ce7c70370f31669f2bf"
EXPECTED_XLSX_SHA256 = "3791b32cbb4d772f7b984ba7ff03f9f3c2a1d37af3ea61e7fa1bbc07f12f7db6"
EXPECTED_CSV_MD5 = "d8e828d7484fb5876000d2efab1d44a0"
EXPECTED_XLSX_MD5 = "c2b7ae971efa5c4f886d824424141ad4"
ORIGINAL_YEARS = tuple(range(1994, 2024))
N = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
WORKSHEET = "xl/worksheets/sheet1.xml"
STRINGS = "xl/sharedStrings.xml"
MAX_WORKBOOK_BYTES = 2 * 1024 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_CSV_BYTES = 2 * 1024 * 1024

INDICATORS = (
    ("Deaths and missing persons (persons)", "Deaths and missing persons (persons)", "68.49"),
    ("Affected population (thousand persons)", "Affected population (thousand persons)", "72.24"),
    ("Affected cropland area (thousand ha)", "Affected cropland area (thousand ha)", "60.70"),
    ("Collapsed dwellings (thousand rooms)", "Collapsed dwellings (thousand rooms)", "65.67"),
    ("Direct economic losses (2023 constant prices, million CNY)",
     "Direct economic losses (million CNY, 2023 constant prices)", "74.86"),
)


def _number(value: str, label: str) -> Decimal:
    try:
        out = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise PreflightError(f"Invalid numeric value: {label}") from exc
    if not out.is_finite() or out < 0:
        raise PreflightError(f"Invalid negative/nonfinite value: {label}")
    return out


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> str | None:
    if cell.find(N + "f") is not None:
        raise PreflightError("Formula cells are not permitted; cached values may be stale")
    kind = cell.get("t")
    value = cell.find(N + "v")
    if kind == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(N + "t"))
    if value is None or value.text is None:
        return None
    if kind == "s":
        index = int(value.text)
        if index < 0 or index >= len(shared_strings):
            raise PreflightError("Bad shared string index")
        return shared_strings[index]
    if kind in (None, "n", "str"):
        return value.text
    raise PreflightError("Unsupported XLSX cell type")


def parse_original_annual_workbook(xlsx: bytes, *, years: tuple[int, ...] = ORIGINAL_YEARS) -> dict[int, tuple[Decimal, ...]]:
    if not xlsx or len(xlsx) > MAX_WORKBOOK_BYTES:
        raise PreflightError("Workbook byte size outside bounded source contract")
    try:
        with zipfile.ZipFile(io.BytesIO(xlsx)) as archive:
            members = archive.namelist()
            if WORKSHEET not in members:
                raise PreflightError("Expected original sheet1.xml missing")
            if len(members) != len(set(members)) or len(members) > 100:
                raise PreflightError("Duplicate/too many XLSX members")
            if any(info.file_size > MAX_XML_BYTES for info in archive.infolist()):
                raise PreflightError("Oversized XLSX member")
            shared_strings: list[str] = []
            if STRINGS in members:
                strings_root = ET.fromstring(archive.read(STRINGS))
                for string in strings_root.findall(N + "si"):
                    shared_strings.append("".join(t.text or "" for t in string.iter(N + "t")))
            worksheet = ET.fromstring(archive.read(WORKSHEET))
    except (zipfile.BadZipFile, ET.ParseError, OSError, ValueError) as exc:
        raise PreflightError("Original XLSX is malformed") from exc

    records: list[dict[str, str]] = []
    for row in worksheet.iter(N + "row"):
        cells: dict[str, str] = {}
        for cell in row.findall(N + "c"):
            ref = cell.get("r", "")
            if ref in cells:
                raise PreflightError("Duplicate XLSX cell reference")
            value = _cell_text(cell, shared_strings)
            if value is not None and value.strip():
                if not re.fullmatch(r"[A-F][1-9][0-9]*", ref):
                    raise PreflightError("Unexpected populated XLSX field")
                cells[ref] = value.strip()
        if cells:
            records.append(cells)
    if len(records) != len(years) + 1:
        raise PreflightError("Official workbook has missing/extra annual rows")
    expected_header = ["Year"] + [ind[1] for ind in INDICATORS]
    if [records[0].get(f"{col}1") for col in "ABCDEF"] != expected_header:
        raise PreflightError("Official workbook headers differ from v1.1 native schema")
    annual: dict[int, tuple[Decimal, ...]] = {}
    for row_index, (record, expected_year) in enumerate(zip(records[1:], years), start=2):
        if set(record) != {f"{col}{row_index}" for col in "ABCDEF"}:
            raise PreflightError("Missing or out-of-order annual workbook cells")
        year_txt = record[f"A{row_index}"]
        if not re.fullmatch(r"[0-9]{4}", year_txt) or int(year_txt) != expected_year:
            raise PreflightError("Unexpected annual benchmark year/order")
        annual[expected_year] = tuple(
            _number(record[f"{column}{row_index}"], f"{expected_year}:{column}")
            for column in "BCDEF"
        )
        if any(val == 0 for val in annual[expected_year]):
            raise PreflightError("Official annual benchmark denominator must be positive")
    return annual


def reconcile_annual_coverage(
    event_csv: str, official_xlsx: bytes, *,
    strict_original: bool = True,
    years: tuple[int, ...] = ORIGINAL_YEARS,
) -> dict[str, object]:
    source_audit = audit_csv_text(event_csv, strict_original=strict_original)
    annual = parse_original_annual_workbook(official_xlsx, years=years)
    rows = csv.DictReader(io.StringIO(event_csv, newline=""))
    required = {"Start year", "Event level"} | {ind[0] for ind in INDICATORS}
    if rows.fieldnames is None or not required.issubset(rows.fieldnames):
        raise PreflightError("CFDID impact indicators missing")
    values: dict[int, list[Decimal]] = defaultdict(lambda: [Decimal(0)] * len(INDICATORS))
    reported_counts: dict[int, list[int]] = defaultdict(lambda: [0] * len(INDICATORS))
    for row in rows:
        if row["Event level"].strip() != "L1":
            continue
        year = int(row["Start year"])
        if year not in annual:
            raise PreflightError("CFDID L1 event year missing from official annual benchmark")
        for idx, (event_field, _official_field, _paper_pct) in enumerate(INDICATORS):
            raw = row[event_field].strip()
            if raw:
                values[year][idx] += _number(raw, f"{year}:{event_field}")
                reported_counts[year][idx] += 1

    result: dict[str, dict[str, object]] = {}
    for idx, (field, _official_field, published) in enumerate(INDICATORS):
        numerator = sum((values[y][idx] for y in years), Decimal(0))
        denominator = sum((annual[y][idx] for y in years), Decimal(0))
        if denominator <= 0:
            raise PreflightError("Official aggregate denominator is nonpositive")
        percent = numerator / denominator * 100
        printed = str(percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        if strict_original and printed != published:
            raise PreflightError(f"Original L1 annual coverage differs from paper: {field}")
        result[field] = {
            "reported_l1_total": str(numerator),
            "official_annual_total": str(denominator),
            "coverage_percent": printed,
            "paper_percentage_matched": printed == published,
            "years_over_100_percent": [y for y in years if values[y][idx] > annual[y][idx]],
            "l1_nonmissing_reported_observations": sum(reported_counts[y][idx] for y in years),
        }
    return {
        "years": len(years),
        "l1_event_count": source_audit["by_event_level"]["L1"],
        "nested_events_excluded": True,
        "official_totals_share_upstream_reporting_with_cfdid": True,
        "all_published_coverage_percentages_reproduced": all(
            item["paper_percentage_matched"] for item in result.values()
        ),
        "indicators": result,
    }


def _read_verified_file(path: Path, expected_sha256: str, limit: int) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise PreflightError("Expected checksum must be a lower-case 64-digit SHA-256")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise PreflightError("Input not a bounded regular file")
    data = path.read_bytes()
    if len(data) > limit or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise PreflightError("Source byte SHA-256 mismatch")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-csv", required=True, type=Path)
    parser.add_argument("--official-xlsx", required=True, type=Path)
    parser.add_argument("--event-sha256", required=True)
    parser.add_argument("--official-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.event_sha256 != EXPECTED_CSV_SHA256 or args.official_sha256 != EXPECTED_XLSX_SHA256:
            raise PreflightError("This gate accepts only the pinned, verified CFDID v1.1 original files")
        event_bytes = _read_verified_file(args.event_csv, args.event_sha256, MAX_CSV_BYTES)
        annual_bytes = _read_verified_file(args.official_xlsx, args.official_sha256, MAX_WORKBOOK_BYTES)
        if (hashlib.md5(event_bytes).hexdigest() != EXPECTED_CSV_MD5 or
                hashlib.md5(annual_bytes).hexdigest() != EXPECTED_XLSX_MD5):
            raise PreflightError("Unexpected mismatch with original publisher MD5 receipts")
        result = reconcile_annual_coverage(event_bytes.decode("utf-8-sig"), annual_bytes)
    except (OSError, UnicodeError, PreflightError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
