# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Observe only official source workbook semantics and aggregate cell types, not municipality rows.

This analysis verifies the exact published original before extracting a small
privacy-safe, non-insurer schema receipt. It never emits town names, AGS keys,
coordinates, real property identifiers, row-level data, or unvalidated sums.
"""
from __future__ import annotations

from collections import Counter
import io
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

from research_runners import rva_nrw_original_rooftop_pv_xlsx_v0 as source

NS = source.NS
MAX_HEADER_SAMPLE = 30
MAX_HEADER_LENGTH = 100
MAX_INTRO_CHARS = 100
RE_CODE5 = re.compile(r"^[0-9]{5}$")
RE_CODE8 = re.compile(r"^[0-9]{8}$")
RE_HEADER_FIELD = re.compile(
    r"Gemeind|AGS|Gewa|Geb.aud|Dach|Solar|PV|Potential|Potenzial|Strom|"
    r"Fl.che|Fl.aeche|Leistung|kWp|MWp|MWh|GWh|Anzahl|Klasse|Kategorie|"
    r"EFH|MFH|Gewerbe|Wohngeb|Haushalt|Stand", re.I
)
RE_CELL = re.compile(r"^([A-Z]{1,3})([1-9][0-9]*)$")


def _safe_label(label: str) -> str:
    if not isinstance(label, str):
        return ""
    # Labels only in the header row; no municipality/owner names in rows below it.
    result = "".join(ch for ch in label if ch.isprintable())
    result = re.sub(r"\s+", " ", result).strip()
    return result[:MAX_HEADER_LENGTH]


def _column_index(ref: str) -> int:
    m = RE_CELL.fullmatch(ref)
    if m is None:
        raise ValueError("SOURCE_CELL_REF_MALFORMED")
    k = 0
    for ch in m.group(1):
        k = k * 26 + (ord(ch) - ord("A") + 1)
    return k - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(si.itertext()) for si in root.findall("m:si", NS)]


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    value = cell.find("m:v", NS)
    kind = cell.get("t", "")
    if kind == "s":
        if value is None or value.text is None:
            raise ValueError("SOURCE_MISSING_SHARED_INDEX")
        idx = int(value.text)
        if idx < 0 or idx >= len(shared):
            raise ValueError("SOURCE_SHARED_STRING_OOB")
        return shared[idx]
    if kind == "inlineStr":
        elt = cell.find("m:is", NS)
        return "".join(elt.itertext()) if elt is not None else ""
    return value.text or "" if value is not None else ""


def _sheet_snapshot(root: ET.Element, shared: list[str], sheet_name: str) -> dict:
    rows = root.findall(".//m:sheetData/m:row", NS)
    if not rows:
        raise ValueError("SOURCE_EMPTY_SHEET")
    first = rows[0]
    header_cells = first.findall("m:c", NS)
    headers = []
    seen = set()
    for cell in header_cells:
        idx = _column_index(cell.get("r", ""))
        if idx in seen:
            raise ValueError("SOURCE_DUPLICATE_HEADER_COORD")
        seen.add(idx)
        label = _safe_label(_cell_text(cell, shared))
        headers.append({"column_1based": idx + 1, "header": label})
    headers.sort(key=lambda x: x["column_1based"])
    hints = [item for item in headers if RE_HEADER_FIELD.search(item["header"])]
    candidate_key_counts = {"five_digits_first_4_cols": 0, "eight_digits_first_4_cols": 0}
    raw_kinds = Counter()
    occupied = 0
    suppressed = Counter()
    for row in rows[1:]:
        for cell in row.findall("m:c", NS):
            idx = _column_index(cell.get("r", ""))
            val = _cell_text(cell, shared)
            if not val:
                raw_kinds["empty"] += 1
                continue
            occupied += 1
            raw_kinds[("shared_text" if cell.get("t") == "s" else
                       "inline_text" if cell.get("t") == "inlineStr" else
                       "numeric" if cell.get("t") in (None, "n") else
                       "other_type")] += 1
            if val in ("-", ".", "/", "x", "X", "..."):
                suppressed[val] += 1
            if idx < 4:
                candidate_key_counts["five_digits_first_4_cols"] += bool(RE_CODE5.fullmatch(val))
                candidate_key_counts["eight_digits_first_4_cols"] += bool(RE_CODE8.fullmatch(val))
    return {
        "sheet_title": _safe_label(sheet_name),
        "rows_with_xml_elements": len(rows),
        "first_row_cell_count": len(header_cells),
        "body_row_elements": len(rows) - 1,
        "body_occupied_cells": occupied,
        "body_cell_types": dict(sorted(raw_kinds.items())),
        "candidate_key_format_counts_unassigned_columns": candidate_key_counts,
        "possible_suppression_tokens": dict(sorted(suppressed.items())),
        "first_header_labels_only": headers[:MAX_HEADER_SAMPLE],
        "last_header_labels_only": headers[-4:] if len(headers) > MAX_HEADER_SAMPLE else [],
        "domain_header_hints_only": hints[:MAX_HEADER_SAMPLE],
    }


def describe(original: bytes, *, pinned: bool = True) -> dict:
    source.parse_original(
        original,
        expected_sha256=source.EXPECTED_SHA256 if pinned else None,
        expected_bytes=source.EXPECTED_BYTES if pinned else None,
        expected_structure=source.EXPECTED_STRUCTURE if pinned else None,
    )
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        shared = _shared_strings(archive)
        wb = ET.fromstring(archive.read("xl/workbook.xml"))
        names = [x.attrib["name"] for x in wb.findall(".//m:sheet", NS)]
        expected_names = len(source.EXPECTED_STRUCTURE) if pinned else len(names)
        if len(names) != expected_names:
            raise ValueError("SOURCE_WORKBOOK_NAMES_MISMATCH")
        # The original is known to contain sheet1..sheet5 without a remapping;
        # this is a source-shape probe only, not a key-based workbook join.
        sheets = []
        for i, name in enumerate(names, 1):
            xml_name = f"xl/worksheets/sheet{i}.xml"
            if xml_name not in archive.namelist():
                raise ValueError("SOURCE_NONCANONICAL_SHEET_RELATION")
            root = ET.fromstring(archive.read(xml_name))
            sheets.append(_sheet_snapshot(root, shared, name))
    return {
        "schema": "NRW_PV_MUNICIPALITY_BUILDING_CATEGORIES_ORIGINAL_SCHEMA_V0",
        "original_sha256": source.EXPECTED_SHA256 if pinned else "SYNTHETIC_FIXTURE",
        "original_source_rights": "publisher_DL_DE_ZERO_2.0_edition_review",
        "actual_pv_installations_verified": False,
        "actual_rv_sites_or_insured_values_verified": False,
        "building_category_semantics_validated": False,
        "rva_model_input_admitted": False,
        "spreadsheet_sheets": sheets,
    }


def main() -> int:
    data = source.fetch_official()
    receipt = describe(data, pinned=True)
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TimeoutError, ET.ParseError) as exc:
        print(f"NRW_PV_SCHEMA_ORIGINAL_BLOCKED: {type(exc).__name__}", file=sys.stderr)
        sys.exit(2)
