# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline original-byte and privacy-safe structural preflight for Marche 2022.

Only source identity, workbook structure and Form A *counts* are reported.
Never print or retain individual survey identifiers, coordinates, free text,
or property/business damage records. No source bytes in Git.

Frozen Zenodo v1.0.1: https://doi.org/10.5281/zenodo.17457884
Concept DOI (not pinned version): https://doi.org/10.5281/zenodo.15591850
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

N = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PREFIX = {
    "industrial": "Industrial activities dataset/",
    "residential": "Residential building dataset/",
}
EXPECTED = {
    "industrial": {
        "filename": "Industrial activities dataset.zip",
        "bytes": 929330,
        "md5": "a96690a9037dd11cf6cdaae414998dc9",
        "sha256": "a4e5a142450e3a9c63e0dcb964b674a55ca180a7c44ec852ecd8e48638d29847",
        "form_a_records": 133,
        "dictionary_sheets": 7,
        "zip_members": 15,
    },
    "residential": {
        "filename": "Residential building dataset.zip",
        "bytes": 891047,
        "md5": "ddd017a153d38cb042e4cf2bcf59adf4",
        "sha256": "4785f5eae8940e5c8033758aac11d1b2d8b7e5f75fe19efab497dfd5453802cd",
        "form_a_records": 123,
        "dictionary_sheets": 9,
        "zip_members": 14,
    },
}
MAX_ORIGINAL_BYTES = 3 * 1024 * 1024
MAX_ZIP_ENTRIES = 30
MAX_TOTAL_UNCOMPRESSED = 5 * 1024 * 1024
MAX_XLSX_MEMBER = 2 * 1024 * 1024


class SourceStructureError(ValueError):
    """Invalid, mismatched or unsafe public survey dataset."""


def _zip_checked(data: bytes, *, max_entries: int, max_total: int) -> zipfile.ZipFile:
    if len(data) > MAX_ORIGINAL_BYTES or not data:
        raise SourceStructureError("Original archive exceeds bounded size")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        infos = archive.infolist()
        if not infos or len(infos) > max_entries:
            raise SourceStructureError("Unexpected archive member count")
        if len({info.filename for info in infos}) != len(infos):
            raise SourceStructureError("Duplicate archive filenames")
        total = 0
        for info in infos:
            filename = info.filename
            # Fail closed on traversal, absolute paths, and symlinks.
            if (filename.startswith("/") or "\\" in filename or
                    any(segment in (".", "..") for segment in filename.split("/")) or
                    not filename or info.file_size > MAX_XLSX_MEMBER):
                raise SourceStructureError("Unsafe archive member path or size")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SourceStructureError("Symlink is not permitted")
            total += info.file_size
        if total > max_total:
            raise SourceStructureError("Uncompressed archive size exceeds bound")
        if archive.testzip() is not None:
            raise SourceStructureError("ZIP CRC mismatch")
        return archive
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError) as exc:
        raise SourceStructureError("Malformed or corrupted ZIP archive") from exc


def _shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in si.iter(N + "t"))
        for si in root.findall(N + "si")
    ]


def _cell_text(cell: ET.Element, strings: list[str]) -> str:
    if cell.find(N + "f") is not None:
        raise SourceStructureError("Workbook formulas are not allowed in Form A data")
    kind = cell.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(N + "t"))
    val = cell.find(N + "v")
    if val is None or val.text is None:
        return ""
    if kind == "s":
        try:
            return strings[int(val.text)]
        except (ValueError, IndexError) as exc:
            raise SourceStructureError("Malformed shared-string reference") from exc
    return val.text


def _form_a_parent_count(raw: bytes, *, expected_count: int) -> int:
    with _zip_checked(raw, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as book:
        try:
            document = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
            strings = _shared_strings(book)
        except (KeyError, ET.ParseError) as exc:
            raise SourceStructureError("Form A workbook worksheet cannot be parsed") from exc

    ids: set[str] = set()
    observed_rows = 0
    saw_header = False
    for row in document.iter(N + "row"):
        try:
            row_num = int(row.get("r", "0"))
        except ValueError as exc:
            raise SourceStructureError("Invalid Form A row number") from exc
        if row_num < 3:
            continue
        cells: dict[str, str] = {}
        other_populated = False
        for cell in row.findall(N + "c"):
            address = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]+)([0-9]+)", address)
            if not match or int(match.group(2)) != row_num or match.group(1) in cells:
                raise SourceStructureError("Malformed or duplicate Form A cell address")
            # Inspect only identifier A and public header labels E/F; never coordinates.
            if row_num == 3 and match.group(1) in ("A", "E", "F"):
                cells[match.group(1)] = _cell_text(cell, strings)
            elif row_num >= 4 and match.group(1) == "A":
                cells["A"] = _cell_text(cell, strings)
            elif row_num >= 4 and _cell_text(cell, strings).strip():
                other_populated = True
        if row_num == 3:
            saw_header = (
                cells.get("A") == "ID" and
                cells.get("E") == "Latitude" and
                cells.get("F") == "Longitude"
            )
            continue
        if row_num >= 4:
            identifier = cells.get("A", "").strip()
            if not identifier and not other_populated:
                # Source XLSX contains visually styled but completely empty rows.
                # Do not convert them into missing-ID survey observations.
                continue
            if not identifier or identifier in ids:
                raise SourceStructureError("Blank or duplicate Form A parent identifier")
            ids.add(identifier)  # local only; identifiers are never output
            observed_rows += 1

    if not saw_header or observed_rows != expected_count:
        raise SourceStructureError("Form A header or parent sample count differs from publisher")
    return observed_rows


def _workbook_sheet_count(raw: bytes) -> int:
    with _zip_checked(raw, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as book:
        try:
            document = ET.fromstring(book.read("xl/workbook.xml"))
        except (KeyError, ET.ParseError) as exc:
            raise SourceStructureError("Workbook manifest cannot be parsed") from exc
    return len(list(document.iter(N + "sheet")))


def audit_archive(data: bytes, sector: str, *, count_override: int | None = None,
                  verify_release_hash: bool = True) -> dict[str, object]:
    """Emit aggregate-only QA; overrides are solely for synthetic regression tests."""
    if sector not in EXPECTED:
        raise SourceStructureError("Unsupported dataset sector")
    item = EXPECTED[sector]
    if verify_release_hash and (
        len(data) != item["bytes"] or
        hashlib.md5(data).hexdigest() != item["md5"] or
        hashlib.sha256(data).hexdigest() != item["sha256"]
    ):
        raise SourceStructureError("Original publisher MD5/SHA-256/byte count mismatch")

    with _zip_checked(data, max_entries=MAX_ZIP_ENTRIES, max_total=MAX_TOTAL_UNCOMPRESSED) as archive:
        names = archive.namelist()
        prefix = PREFIX[sector]
        if any(not name.startswith(prefix) for name in names):
            raise SourceStructureError("Unexpected file outside release dataset prefix")
        required = [prefix + f"Form_{form}.xlsx" for form in "ABCDE"]
        dictionary = prefix + ("Data_dictionary.xlsx" if sector == "industrial"
                               else "Data dictionary.xlsx")
        if not all(name in names for name in required + [dictionary]):
            raise SourceStructureError("Required original survey workbook/dictionary missing")
        if verify_release_hash and len(names) != item["zip_members"]:
            raise SourceStructureError("Original ZIP member count changed")

        counts = {}
        for form, path in zip("ABCDE", required):
            raw = archive.read(path)
            sheet_count = _workbook_sheet_count(raw)
            if sheet_count < 1:
                raise SourceStructureError("Form workbook has no sheets")
            counts[form] = sheet_count
            if form == "A":
                sample = _form_a_parent_count(
                    raw, expected_count=count_override or item["form_a_records"]
                )
        dictionary_sheets = _workbook_sheet_count(archive.read(dictionary))
        if dictionary_sheets != item["dictionary_sheets"]:
            raise SourceStructureError("Survey data dictionary workbook structure changed")

    return {
        "published_dataset_version": "1.0.1",
        "sector": sector,
        "form_a_unique_parent_survey_count": sample,
        "three_header_rows_excluded": True,
        "data_dictionary_sheet_count": dictionary_sheets,
        "form_workbook_sheet_counts": counts,
        "publisher_md5_and_sha256_matched": verify_release_hash,
        "contains_original_row_level_data_in_output": False,
        "model_admitted": False,
    }


def _read_original(path: Path, sector: str) -> bytes:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ORIGINAL_BYTES:
        raise SourceStructureError("Original must be a bounded regular file")
    data = path.read_bytes()
    if len(data) != EXPECTED[sector]["bytes"]:
        raise SourceStructureError("Frozen original byte count differs")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--industrial-zip", type=Path, required=True)
    parser.add_argument("--residential-zip", type=Path, required=True)
    args = parser.parse_args()
    try:
        industrial = audit_archive(_read_original(args.industrial_zip, "industrial"), "industrial")
        residential = audit_archive(_read_original(args.residential_zip, "residential"), "residential")
        total = industrial["form_a_unique_parent_survey_count"] + residential["form_a_unique_parent_survey_count"]
        if total != 256:
            raise SourceStructureError("Published total of 256 parent surveys not reproduced")
    except (OSError, SourceStructureError, ET.ParseError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "zenodo_release": "10.5281/zenodo.17457884",
        "original_parent_surveys": total,
        "privacy_safe": True,
        "research_only_not_admitted": True,
        "industrial": industrial,
        "residential": residential,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
