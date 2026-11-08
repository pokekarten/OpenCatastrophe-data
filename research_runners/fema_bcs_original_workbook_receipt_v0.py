# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded read-only FEMA-0173 original XLSX structural receipt.

Original workbook has not yet been downloaded or admitted. Emits package and
worksheet metadata only, not raw source rows or insurance claims. --official-live
is explicitly opt-in; no source bytes are persisted by this program.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

SOURCE_URL = "https://www.fema.gov/sites/default/files/documents/fema_building-codes-save-study-results.xlsx"
CATALOGUE_URL = "https://catalog.data.gov/dataset/aals-from-the-adoption-of-i-codes"
MAX_XLSX_BYTES = 48 * 1024 * 1024
MAX_EXPANDED_BYTES = 320 * 1024 * 1024
MAX_SINGLE_XML_BYTES = 150 * 1024 * 1024
MAX_ZIP_MEMBERS = 2000
MAX_SHEETS = 128
MAX_ROWS_PER_SHEET = 1048576
SHEET_XML_RE = re.compile(r"xl/worksheets/[^/]+\.xml\Z")
NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_DOCREL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PACKAGE = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": NS_MAIN, "r": NS_DOCREL, "p": NS_PACKAGE}


class OriginalFEMASourceError(ValueError):
    """Original XLSX failed a bounded source preflight."""


def _validated_zip(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if not 3 <= len(infos) <= MAX_ZIP_MEMBERS:
        raise OriginalFEMASourceError("unsafe XLSX ZIP member count")
    names: dict[str, zipfile.ZipInfo] = {}
    expanded = 0
    for item in infos:
        name = item.filename
        mode = (item.external_attr >> 16) & 0o170000
        if (not name or name in names or name.startswith("/") or "\\" in name
                or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
                or mode == 0o120000 or item.flag_bits & 1):
            raise OriginalFEMASourceError("unsafe or duplicate XLSX ZIP path")
        if (name.endswith((".bin", ".exe", ".vba"))
                or name.startswith("xl/externalLinks/")
                or name in {"xl/connections.xml", "xl/vbaProject.bin"}):
            raise OriginalFEMASourceError("XLSX macro, external link or connection not allowed")
        if item.file_size > MAX_SINGLE_XML_BYTES:
            raise OriginalFEMASourceError("XLSX single-member expansion limit exceeded")
        if item.compress_size and item.file_size > 1000 * item.compress_size:
            raise OriginalFEMASourceError("XLSX suspicious compression ratio")
        expanded += item.file_size
        if expanded > MAX_EXPANDED_BYTES:
            raise OriginalFEMASourceError("XLSX total expansion limit exceeded")
        names[name] = item
    for required in ("[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"):
        if required not in names:
            raise OriginalFEMASourceError("XLSX core package relationships missing")
    return names


def _sheet_paths(archive: zipfile.ZipFile, members: dict[str, zipfile.ZipInfo]):
    book = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {}
    for rel in relationships.findall("p:Relationship", NS):
        rid = rel.get("Id")
        target = rel.get("Target")
        if not rid or not target or rel.get("TargetMode", "Internal") != "Internal":
            raise OriginalFEMASourceError("external or malformed workbook relationship")
        if target.startswith("/"):
            path = posixpath.normpath(target.lstrip("/"))
        else:
            path = posixpath.normpath(posixpath.join("xl", target))
        if not path.startswith("xl/") or path not in members:
            raise OriginalFEMASourceError("workbook relationship target not in safe ZIP")
        targets[rid] = path
    worksheets = []
    for item in book.findall(".//m:sheets/m:sheet", NS):
        name = item.get("name", "")
        rid = item.get(f"{{{NS_DOCREL}}}id")
        path = targets.get(rid)
        if not name or len(name) > 255 or not path or not SHEET_XML_RE.fullmatch(path):
            raise OriginalFEMASourceError("invalid source worksheet relationship")
        worksheets.append((name, path, item.get("state", "visible")))
    if not 1 <= len(worksheets) <= MAX_SHEETS:
        raise OriginalFEMASourceError("invalid number of workbook sheets")
    if len({name for name, _, _ in worksheets}) != len(worksheets):
        raise OriginalFEMASourceError("duplicate worksheet names")
    return book, worksheets


def inspect_original(original: bytes, *, expected_sha256: str | None = None) -> dict:
    if type(original) is not bytes or not 1024 <= len(original) <= MAX_XLSX_BYTES:
        raise OriginalFEMASourceError("original must be a bounded XLSX byte payload")
    sha = hashlib.sha256(original).hexdigest()
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or sha != expected_sha256:
            raise OriginalFEMASourceError("original XLSX SHA-256 mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            members = _validated_zip(archive)
            book, sheet_paths = _sheet_paths(archive, members)
            sheets = []
            for name, path, visibility in sheet_paths:
                root = ET.fromstring(archive.read(path))
                sheet_data = root.find("m:sheetData", NS)
                if sheet_data is None:
                    raise OriginalFEMASourceError("worksheet has no sheetData")
                rows = sheet_data.findall("m:row", NS)
                if len(rows) > MAX_ROWS_PER_SHEET:
                    raise OriginalFEMASourceError("worksheet row budget exceeded")
                first_row = rows[0] if rows else None
                cell_refs = []
                if first_row is not None:
                    for cell in first_row.findall("m:c", NS)[:64]:
                        ref = cell.get("r", "")
                        if not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]*", ref):
                            raise OriginalFEMASourceError("invalid first-row cell reference")
                        cell_refs.append(ref)
                sheets.append({
                    "sheet_name": name,
                    "sheet_xml": path,
                    "visibility": visibility,
                    "row_element_count": len(rows),
                    "first_row_cell_references": cell_refs,
                    "formula_element_count": len(root.findall(".//m:f", NS)),
                })
            date1904 = book.find("m:workbookPr", NS)
            return {
                "evidence_class": "ORIGINAL_WORKBOOK_STRUCTURE_ONLY_NOT_ADMITTED",
                "catalogue_url": CATALOGUE_URL,
                "source_url": SOURCE_URL,
                "original_bytes": len(original),
                "original_sha256": sha,
                "prior_hash_pin_verified": expected_sha256 is not None,
                "zip_member_count": len(members),
                "date1904": bool(date1904 is not None and date1904.get("date1904") in {"1", "true"}),
                "worksheets": sheets,
                "source_cell_values_emitted": False,
                "source_rights_reviewed": False,
                "original_source_admitted": False,
                "independent_loss_validation": False,
                "aep_or_oep_calculated": False,
            }
    except (OSError, zipfile.BadZipFile, ET.ParseError, RuntimeError) as exc:
        raise OriginalFEMASourceError("original XLSX structure unreadable") from exc


def fetch_official(*, opener=urllib.request.urlopen) -> bytes:
    request = urllib.request.Request(SOURCE_URL, headers={
        "User-Agent": "OpenCatastrophe-FEMA-0173-original-metadata-check/0.1",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.1",
    })
    with opener(request, timeout=35) as response:
        parsed = urlsplit(response.geturl())
        if parsed.scheme != "https" or parsed.hostname not in {"www.fema.gov", "fema.gov"}:
            raise OriginalFEMASourceError("source redirected outside official FEMA host")
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            if not content_length.isdigit() or int(content_length) > MAX_XLSX_BYTES:
                raise OriginalFEMASourceError("source content-length outside budget")
        chunks = []
        size = 0
        while True:
            chunk = response.read(128 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_XLSX_BYTES:
                raise OriginalFEMASourceError("source streaming size budget exceeded")
            chunks.append(chunk)
        return b"".join(chunks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--official-live", action="store_true")
    mode.add_argument("--original-xlsx", type=Path)
    parser.add_argument("--expected-sha256", help="optional independently verified 64-char SHA-256")
    args = parser.parse_args(argv)
    try:
        if args.official_live:
            original = fetch_official()
        else:
            path = args.original_xlsx
            if path.is_symlink() or not path.is_file() or not 1024 <= path.stat().st_size <= MAX_XLSX_BYTES:
                raise OriginalFEMASourceError("bounded regular local file required")
            original = path.read_bytes()
        print(json.dumps(inspect_original(original, expected_sha256=args.expected_sha256),
                         sort_keys=True, indent=2, allow_nan=False))
    except (OSError, TimeoutError, OriginalFEMASourceError) as exc:
        print("BLOCKED: " + str(exc)[:140], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
