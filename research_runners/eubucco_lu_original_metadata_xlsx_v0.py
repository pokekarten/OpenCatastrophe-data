#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-byte EUBUCCO v0.2 source metadata XLSX Luxembourg audit.

Inspects only public provider source-dataset metadata. Never processes building
geometries, attribute values, insured assets, claims, persons, or model inputs.
No third-party workbook bytes are persisted by this program.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ORIGINAL_URL = "https://s3.eubucco.com/eubucco/v0.2/additional/input-datasets-metadata.xlsx"
MAX_ORIGINAL_BYTES = 5 * 1024 * 1024
MAX_UNPACKED_BYTES = 20 * 1024 * 1024
MAX_ROWS_PER_SHEET = 25_000
MAX_MATCHED_ROWS = 60
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SHEET = re.compile(r"xl/worksheets/sheet[0-9]+\.xml\Z")
CELL_REF = re.compile(r"([A-Z]{1,3})([0-9]+)\Z")
LU_TEXT = re.compile(r"\bluxembourg\b", re.I)


class SourceMetadataError(ValueError):
    """Original source workbook does not match the strict read-only contract."""


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _valid_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    mode = (info.external_attr >> 16) & 0o170000
    if (not name or name.startswith("/") or "\\" in name
            or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
            or mode == 0o120000 or info.flag_bits & 1
            or name.startswith("xl/externalLinks/")
            or name.endswith((".bin", ".vba", ".exe"))
            or info.file_size > MAX_UNPACKED_BYTES):
        raise SourceMetadataError("unsafe XLSX archive member")
    if info.compress_size and info.file_size > 1000 * info.compress_size:
        raise SourceMetadataError("unbounded XML decompression ratio")


def _text(node: ET.Element) -> str:
    return "".join(n.text or "" for n in node.iter() if n.tag == f"{{{NS['m']}}}t")


def _col_index(name: str) -> int:
    result = 0
    for char in name:
        result = result * 26 + ord(char) - 64
    return result


def _read_shared(archive: zipfile.ZipFile) -> list[str]:
    try:
        xml = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml)
    values = [_text(item) for item in root.findall("m:si", NS)]
    if len(values) > 100_000:
        raise SourceMetadataError("shared string count exceeds budget")
    return values


def _get_cell(cell: ET.Element, shared: list[str]) -> str:
    typ = cell.get("t", "")
    if typ == "inlineStr":
        element = cell.find("m:is", NS)
        return _text(element) if element is not None else ""
    v = cell.find("m:v", NS)
    if v is None:
        return ""
    text = v.text or ""
    if typ == "s":
        try:
            idx = int(text)
            if idx < 0:
                raise ValueError("negative string index")
            return shared[idx]
        except (ValueError, IndexError) as exc:
            raise SourceMetadataError("invalid shared string index") from exc
    return text


def _safe(value: str) -> str:
    # Limit output of individual *public source-metadata* cells; never print
    # original building/property rows or full metadata workbook.
    value = "".join(ch for ch in value.strip() if ch.isprintable())
    return value[:240]


def _is_luxembourg(text: str) -> bool:
    compact = text.strip()
    return bool(LU_TEXT.search(compact) or compact.upper() in ("LU", "LUX", "LU00", "LU000"))


def inspect(path: Path, *, expected_sha256: str | None = None) -> dict:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ORIGINAL_BYTES:
        raise SourceMetadataError("source must be a bounded, regular local XLSX")
    actual = _sha(path)
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or expected_sha256 != actual:
            raise SourceMetadataError("source metadata XLSX SHA-256 mismatch")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if not 3 <= len(infos) <= 500:
                raise SourceMetadataError("unexpected XLSX ZIP size")
            if len({i.filename for i in infos}) != len(infos):
                raise SourceMetadataError("duplicate ZIP member names")
            for info in infos:
                _valid_member(info)
            if sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
                raise SourceMetadataError("XLSX expanded XML budget exceeded")
            names = set(archive.namelist())
            if "xl/workbook.xml" not in names or "[Content_Types].xml" not in names:
                raise SourceMetadataError("missing core Excel workbook XML")
            sheets = sorted(name for name in names if SHEET.fullmatch(name))
            if not 1 <= len(sheets) <= 20:
                raise SourceMetadataError("no bounded worksheet XML")
            shared = _read_shared(archive)
            matches = []
            sheet_counts = {}
            for sheet in sheets:
                root = ET.fromstring(archive.read(sheet))
                rows = root.findall(".//m:sheetData/m:row", NS)
                if len(rows) > MAX_ROWS_PER_SHEET:
                    raise SourceMetadataError("worksheet row budget exceeded")
                sheet_counts[sheet] = len(rows)
                for row in rows:
                    fields = {}
                    for cell in row.findall("m:c", NS):
                        reference = cell.get("r", "")
                        ref_match = CELL_REF.fullmatch(reference)
                        if ref_match is None:
                            raise SourceMetadataError("cell reference missing or invalid")
                        if _col_index(ref_match.group(1)) > 256:
                            raise SourceMetadataError("source metadata column budget exceeded")
                        value = _get_cell(cell, shared)
                        if value:
                            fields[ref_match.group(1)] = _safe(value)
                    if any(_is_luxembourg(v) for v in fields.values()):
                        if len(matches) >= MAX_MATCHED_ROWS:
                            raise SourceMetadataError("too many Luxembourg metadata rows for review")
                        # Sheet row indexes and public source-metadata only, no
                        # complete source XLSX output / original building records.
                        matches.append({
                            "sheet": sheet, "row": int(row.get("r", "0")),
                            "metadata_cells": dict(sorted(fields.items())) if len(fields) <= 36
                                              else dict(sorted(fields.items())[:36]),
                        })
    except (zipfile.BadZipFile, ET.ParseError, RuntimeError, OSError) as exc:
        raise SourceMetadataError("cannot safely inspect original XLSX") from exc
    return {
        "profile": "eubucco-v02-lu-original-source-metadata-v0",
        "official_source": ORIGINAL_URL,
        "source_metadata_bytes": path.stat().st_size,
        "original_metadata_sha256": actual,
        "independent_prior_sha256_verified": expected_sha256 is not None,
        "worksheet_row_counts": sheet_counts,
        "luxembourg_source_metadata_row_count": len(matches),
        "luxembourg_source_metadata_rows": matches,
        "no_building_geometries_read": True,
        "source_lineage_independence_verified": False,
        "licence_and_model_input_admitted": False,
        "original_workbook_exported_or_persisted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-xlsx", required=True, type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.original_xlsx, expected_sha256=args.expected_sha256)
    except (OSError, SourceMetadataError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
