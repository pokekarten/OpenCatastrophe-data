# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte-locked NRW solar roof PV data: municipal row integrity, statewide aggregates.

This is not insured R+V properties or the number of *installed* PV systems.
Only totals across 396 publisher municipalities are emitted, never raw rows.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
import io
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

from research_runners import rva_nrw_original_rooftop_pv_xlsx_v0 as source
from research_runners import rva_nrw_original_pv_schema_observation_v0 as schema

CLASSES = (
    "Wohngebäude", "Gewerbe und Industrie", "Öffentliche Gebäude",
    "Landwirtschaft", "Sonstige Gebäude", "Nicht zuordbar", "Insgesamt",
)
YEARS = tuple(range(1990, 2026))
SHEETS = (
    ("Bestand Leistung", "Bestand Leistung [kW]", "kW"),
    ("Bestand Ertrag", "Bestand Ertrag [kWh]", "kWh"),
    ("Potenzial Leistung", "Potenzial Leistung [kW]", "kW"),
    ("Potenzial Ertrag", "Potenzial Ertrag [kWh]", "kWh"),
)
EXPECTED_MUNICIPALITY_COUNT = 396
AGS = re.compile(r"^[0-9]{8}$")
MAX_AMOUNT = Decimal("1000000000000000000")


def decimal_amount(raw: str) -> Decimal:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > 45:
        raise ValueError("SOURCE_NUMERIC_REQUIRED")
    try:
        val = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("SOURCE_NUMERIC_INVALID") from exc
    if not val.is_finite() or val < 0 or val > MAX_AMOUNT:
        raise ValueError("SOURCE_NUMERIC_NEGATIVE_NONFINITE_OR_TOO_LARGE")
    return val


def expected_headers(prefix: str, is_yearly: bool) -> dict[int, str]:
    names = {2: "AGS", 3: "Gemeinde"}
    for j, category in enumerate(CLASSES):
        if is_yearly:
            for year in YEARS:
                # Source has year-major ordering, so j offsets within each year.
                names[4 + (year - YEARS[0]) * len(CLASSES) + j] = (
                    f"{prefix} {year} {category}"
                )
        else:
            names[4 + j] = f"{prefix} {category}"
    return names


def parse_row_cells(row: ET.Element, shared: list[str]) -> dict[int, str]:
    cells = {}
    for c in row.findall("m:c", source.NS):
        idx = schema._column_index(c.get("r", "")) + 1
        if idx in cells:
            raise ValueError("SOURCE_DUPLICATE_CELL")
        cells[idx] = schema._cell_text(c, shared)
    return cells


def check_ags(records: list[dict[int, str]]) -> set[str]:
    codes = []
    for row in records:
        value = row.get(2, "")
        if not AGS.fullmatch(value) or not row.get(3, "").strip():
            raise ValueError("SOURCE_MUNICIPALITY_AGSCODE_OR_LABEL_INVALID")
        codes.append(value)
    if len(set(codes)) != len(codes):
        raise ValueError("SOURCE_DUPLICATE_AGS")
    if len(codes) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError("SOURCE_MUNICIPALITY_COUNT_CHANGED")
    return set(codes)


def verify_and_aggregate(original: bytes) -> dict:
    source.parse_original(
        original, expected_sha256=source.EXPECTED_SHA256,
        expected_bytes=source.EXPECTED_BYTES,
        expected_structure=source.EXPECTED_STRUCTURE,
    )
    # Run through identical safe schema parser too, to preserve original label/role.
    original_shape = schema.describe(original, pinned=True)
    names = [s["sheet_title"] for s in original_shape["spreadsheet_sheets"]]
    if names[1:] != [x[0] for x in SHEETS]:
        raise ValueError("SOURCE_WORKSHEET_MEASURES_CHANGED")
    aggregate = []
    expected_key_set = None
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        shared = schema._shared_strings(archive)
        for sheet_no, (sheet_name, prefix, units) in enumerate(SHEETS, 2):
            root = ET.fromstring(archive.read(f"xl/worksheets/sheet{sheet_no}.xml"))
            source_rows = root.findall(".//m:sheetData/m:row", source.NS)
            if len(source_rows) != EXPECTED_MUNICIPALITY_COUNT + 1:
                raise ValueError("SOURCE_WORKSHEET_ROW_COUNT_CHANGED")
            header = parse_row_cells(source_rows[0], shared)
            is_yearly = sheet_no in (2, 3)
            wanted = expected_headers(prefix, is_yearly)
            if set(header) != set(wanted) or any(header[c] != v for c, v in wanted.items()):
                raise ValueError("SOURCE_COLUMN_TAXONOMY_CHANGED")
            rows = [parse_row_cells(r, shared) for r in source_rows[1:]]
            key_set = check_ags(rows)
            if expected_key_set is None:
                expected_key_set = key_set
            elif key_set != expected_key_set:
                raise ValueError("SOURCE_CROSS_SHEET_AGS_SET_MISMATCH")
            nvals = len(CLASSES) * (len(YEARS) if is_yearly else 1)
            amount_keys = tuple(range(4, 4 + nvals))
            totals = {col: Decimal(0) for col in amount_keys}
            mismatch = 0
            max_abs_residual = Decimal(0)
            for row in rows:
                if set(row) != set(wanted):
                    raise ValueError("SOURCE_ROW_CELL_COMPLETENESS_CHANGED")
                numeric = {c: decimal_amount(row[c]) for c in amount_keys}
                for c, val in numeric.items():
                    totals[c] += val
                for start in range(4, 4 + nvals, len(CLASSES)):
                    subtotal = sum((numeric[start+i] for i in range(6)), Decimal(0))
                    residual = subtotal - numeric[start+6]
                    if residual:
                        mismatch += 1
                    max_abs_residual = max(max_abs_residual, abs(residual))
            if is_yearly:
                # One selected column year is reported, not a cumulative fleet.
                selected_year = 2025
                first = 4 + (selected_year - YEARS[0]) * len(CLASSES)
                selected = {CLASSES[j]: str(totals[first+j]) for j in range(len(CLASSES))}
            else:
                selected_year = None
                selected = {CLASSES[j]: str(totals[4+j]) for j in range(len(CLASSES))}
            aggregate.append({
                "sheet_title": sheet_name,
                "publisher_measure": prefix,
                "units_exact_header": units,
                "year_column_scope": "single_2025_publisher_column_not_known_as_installed_stock" if is_yearly else "nonannual_technical_potential",
                "selected_column_year": selected_year,
                "NRW_aggregate_by_building_type": selected,
                "sum_of_6_categories_vs_publisher_total":
                    {"rows_or_row_year_groups_with_nonzero_difference": mismatch,
                     "maximum_abs_difference_in_source_units": str(max_abs_residual),
                     "not_forced_to_balance": True},
            })
    return {
        "schema": "NRW_ROOF_PV_AGGREGATES_SOURCE_20260312_V0",
        "publisher": "LANUK_NRW_OPEN_GEODATA",
        "source_sha256": source.EXPECTED_SHA256,
        "source_original_bytes": source.EXPECTED_BYTES,
        "verified_distinct_8digit_AGS_per_sheet": EXPECTED_MUNICIPALITY_COUNT,
        "geographic_scope": "NRW_MUNICIPALITIES_SOURCE_VINTAGE_UNVALIDATED",
        "printed_values_grain": "NRW_AGGREGATE_BY_BUILDING_CATEGORY_ONLY",
        "company_RV_real_locations_observed": False,
        "company_RV_TIV_observed": False,
        "installed_rooftop_PV_units_observed": False,
        "building_category_sensitivity_only": True,
        "source_admitted_to_CAT_models": False,
        "issuer_2025_RV_policy_crosswalk_established": False,
        "sheets": aggregate,
    }


def main() -> int:
    original = source.fetch_official()
    result = verify_and_aggregate(original)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TimeoutError, ET.ParseError) as exc:
        print(f"NRW_PV_ORIGINAL_AGGREGATE_BLOCKED: {type(exc).__name__}", file=sys.stderr)
        sys.exit(2)
