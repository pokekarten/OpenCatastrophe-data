# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded OOXML header-only peek at the *original* 2022 Kreis-region workbook.

This is a structural preflight: resolve one exact worksheet with OOXML
relationships, inspect ONLY the first/header row and report ONLY the
column labels. Source data rows (including *numeric strings*) are excluded. No actual numerical Census counts, no bulk cell export,
no GDV extraction, no insurance-location assumptions.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from zensus_regional_original_receipt_v0 import OriginalReceiptError, inspect_original_package


M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
D = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P = "{http://schemas.openxmlformats.org/package/2006/relationships}"
SHEET_TITLE = "CSV-Gebäude"
MAX_HEADER_ROWS = 1
MAX_HEADER_COLUMNS = 28
MAX_HEADING_CELLS = 120
MAX_SHARED_INDEX = 2_000_000
MAX_SHEET_XML_BYTES = 500_000_000
REF = re.compile(r"([A-Z]{1,3})[1-9][0-9]*\Z")


def _col_index(ref: str) -> int:
    m = REF.fullmatch(ref)
    if not m:
        raise OriginalReceiptError("malformed original source cell reference")
    col = 0
    for c in m.group(1):
        col = col * 26 + ord(c) - 64
    return col


def _xlsx_target(z: ZipFile, sheet_name: str) -> str:
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rel = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    except (KeyError, ET.ParseError) as exc:
        raise OriginalReceiptError("missing or invalid original worksheet relationship") from exc
    parent = wb.find(M + "sheets")
    if parent is None:
        raise OriginalReceiptError("original workbook missing sheet metadata")
    targets = [x.attrib.get(D + "id") for x in parent.findall(M + "sheet")
               if x.attrib.get("name") == sheet_name]
    if len(targets) != 1 or not targets[0]:
        raise OriginalReceiptError("required CSV-Gebäude worksheet name not unique")
    paths = [x.attrib.get("Target") for x in rel.findall(P + "Relationship")
             if x.attrib.get("Id") == targets[0]]
    if len(paths) != 1 or not paths[0]:
        raise OriginalReceiptError("required worksheet relationship cannot be resolved")
    target = paths[0]
    if target.startswith("/"):
        path = target.lstrip("/")
    else:
        path = str(PurePosixPath("xl") / target)
    parts = PurePosixPath(path).parts
    if (not path.startswith("xl/worksheets/") or
            ".." in parts or path not in z.namelist() or
            not path.endswith(".xml")):
        raise OriginalReceiptError("unsafe/unresolved worksheet path")
    return path


def _first_rows(z: ZipFile, target: str) -> tuple[list[list[tuple[str,str,str]]], set[int]]:
    info = z.getinfo(target)
    if info.file_size > MAX_SHEET_XML_BYTES:
        raise OriginalReceiptError("worksheet XML outside bounded header inspector")
    found: list[list[tuple[str,str,str]]] = []
    shared_indices: set[int] = set()
    try:
        with z.open(target, "r") as stream:
            for _, element in ET.iterparse(stream, events=("end",)):
                if element.tag != M + "row":
                    continue
                row: list[tuple[str,str,str]] = []
                for cell in element.findall(M + "c"):
                    ref = cell.attrib.get("r", "")
                    if _col_index(ref) > MAX_HEADER_COLUMNS:
                        continue
                    tag = cell.attrib.get("t", "")
                    val = cell.find(M + "v")
                    val_text = val.text if val is not None and val.text is not None else ""
                    if tag == "s":
                        if not val_text.isdecimal() or int(val_text) > MAX_SHARED_INDEX:
                            raise OriginalReceiptError("invalid bounded OOXML shared-string index")
                        shared_indices.add(int(val_text))
                        row.append((ref, "shared", val_text))
                    elif tag == "inlineStr":
                        inline = cell.find(M + "is")
                        text = "".join(n.text or "" for n in inline.iter(M + "t")) if inline is not None else ""
                        row.append((ref, "inline", text))
                    elif tag == "str":
                        row.append((ref, "formula_str", val_text))
                    elif tag == "e":
                        row.append((ref, "source_error", val_text))
                    else:
                        row.append((ref, "numeric_or_blank", ""))
                found.append(row)
                element.clear()
                if len(found) >= MAX_HEADER_ROWS:
                    break
    except (ET.ParseError, RuntimeError, OSError) as exc:
        raise OriginalReceiptError("original worksheet header XML unreadable") from exc
    return found, shared_indices


def _shared_strings(z: ZipFile, indices: set[int]) -> dict[int, str]:
    if not indices:
        return {}
    if "xl/sharedStrings.xml" not in z.namelist():
        raise OriginalReceiptError("original shared string table missing")
    found: dict[int, str] = {}
    wanted = set(indices)
    number = 0
    try:
        with z.open("xl/sharedStrings.xml") as stream:
            for _, item in ET.iterparse(stream,events=("end",)):
                if item.tag != M + "si":
                    continue
                if number in wanted:
                    found[number] = "".join(x.text or "" for x in item.iter(M + "t"))
                    wanted.remove(number)
                    if not wanted:
                        break
                number += 1
                item.clear()
                if number > MAX_SHARED_INDEX + 1:
                    break
    except (ET.ParseError, OSError, RuntimeError) as exc:
        raise OriginalReceiptError("shared-string header lookup failed") from exc
    if wanted:
        raise OriginalReceiptError("original source contains unresolved shared-string indices")
    return found


def inspect_original_gwz_header(raw: bytes) -> dict:
    receipt = inspect_original_package(raw)
    with ZipFile(BytesIO(raw)) as z:
        target = _xlsx_target(z, SHEET_TITLE)
        rows, indices = _first_rows(z, target)
        strings = _shared_strings(z, indices)
    headings = []
    for row_index, row in enumerate(rows, start=1):
        for cell_ref, kind, raw_value in row:
            if kind in ("shared", "inline", "formula_str"):
                value = strings[int(raw_value)] if kind == "shared" else raw_value
                safe = " ".join(value.split())
                if safe and len(headings) < MAX_HEADING_CELLS:
                    headings.append({"row": row_index, "cell": cell_ref,
                                     "text": safe[:90], "text_truncated": len(safe) > 90})
    return {
        "schema_version": "0.1.0",
        "original_file_sha256": receipt["original_file_sha256"],
        "sheet_exact_name": SHEET_TITLE,
        "resolved_original_sheet_path": target,
        "initial_rows_scanned": len(rows),
        "initial_shared_string_cells_resolved": len(indices),
        "bounded_header_labels_only": headings,
        "source_data_rows_exported": False,
        "numerical_census_cells_exported": False,
        "full_worksheet_semantics_verified": False,
        "2022_kreis_ags_and_population_column_admitted": False,
        "2025_insurance_company_coverage_inferred": False,
        "nextgen_cat_model_input_approved": False,
    }
