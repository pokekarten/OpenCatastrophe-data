# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline BNPB 2025 XLSX original-byte and dimensionality preflight (no admission).

Usage: python -m research_runners.bnpb_2025_damage_workbook_preflight_v0 \
    --resource province_houses --original-xlsx /secure/path/original.xlsx \
    [--expected-sha256 independently_pinned_hash]

Never downloads, republishes, exports source rows or infers severity by province.
The two official BNPB XLSX resources are DIFFERENT statistical dimensions.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

DATASET_URL = "https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025"
RESOURCE_IDS = {
    "province_houses": "43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636",
    "peril_severity_summary": "6e947c9c-2404-4c02-b743-34dc5320f399",
}
MAX_ORIGINAL_BYTES = 8 * 1024 * 1024
MAX_EXPANDED_BYTES = 40 * 1024 * 1024
MAX_SINGLE_MEMBER = 10 * 1024 * 1024
MAX_ZIP_MEMBERS = 150
MAX_ROWS = 1500
MAX_CELLS = 35000
MAX_SHEETS = 15
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
HEADER_PROVINCE = {"provinsi", "banjir", "gempabumi", "tanah longsor"}
HEADER_SUMMARY = {"jenis bencana", "jumlah kejadian", "rumah rusak berat", "rumah rusak sedang", "rumah rusak ringan"}
PERILS = {
    "banjir", "cuaca ekstrem", "erupsi gunung api", "gelombang pasang dan abrasi",
    "gempabumi", "kebakaran hutan dan lahan", "kekeringan", "tanah longsor", "tsunami",
}
SEVERITY = {"rumah rusak berat", "rumah rusak sedang", "rumah rusak ringan"}
MISSING = {"", "-", "—", "–", "n/a", "na", "null", "tidak tersedia", "tidak ada"}


class BnpbWorkbookError(ValueError):
    """A workbook failed a security, source-identity, type or grain check."""


def _clean(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _safe_members(z: zipfile.ZipFile) -> set[str]:
    infos = z.infolist()
    if not 4 <= len(infos) <= MAX_ZIP_MEMBERS:
        raise BnpbWorkbookError("unsafe XLSX ZIP member count")
    total = 0
    names: set[str] = set()
    for item in infos:
        path = item.filename
        mode = (item.external_attr >> 16) & 0o170000
        if (not path or path in names or path.startswith("/") or "\\" in path
            or any(p in {"", ".", ".."} for p in path.rstrip("/").split("/"))
            or mode == 0o120000 or item.flag_bits & 1):
            raise BnpbWorkbookError("unsafe XLSX member/duplicate path")
        if (path.startswith("xl/externalLinks/") or path in {"xl/connections.xml", "xl/vbaProject.bin"}
            or path.lower().endswith((".bin", ".vba", ".exe"))):
            raise BnpbWorkbookError("external workbook link, macro or binary prohibited")
        total += item.file_size
        if item.file_size > MAX_SINGLE_MEMBER or total > MAX_EXPANDED_BYTES:
            raise BnpbWorkbookError("XLSX expansion budget exceeded")
        if item.compress_size and item.file_size > 1000 * item.compress_size:
            raise BnpbWorkbookError("suspicious XLSX compression ratio")
        names.add(path)
    if not {"[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"} <= names:
        raise BnpbWorkbookError("missing essential XLSX package parts")
    return names


def _sheet_paths(z: zipfile.ZipFile, names: set[str]) -> list[tuple[str, str]]:
    book = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets: dict[str, str] = {}
    for rel in rels.findall(f"{{{PKG}}}Relationship"):
        rid = rel.get("Id", "")
        target = rel.get("Target", "")
        if rel.get("TargetMode", "Internal") != "Internal" or not rid or not target:
            raise BnpbWorkbookError("external/invalid workbook relationship")
        if target.startswith("/"):
            path = posixpath.normpath(target.lstrip("/"))
        else:
            path = posixpath.normpath(posixpath.join("xl", target))
        if path not in names or not path.startswith("xl/"):
            raise BnpbWorkbookError("workbook relationship outside XLSX package")
        targets[rid] = path
    sheet_paths = []
    for s in book.findall(f".//{{{NS}}}sheets/{{{NS}}}sheet"):
        rid = s.get(f"{{{REL}}}id", "")
        name = s.get("name", "")
        target = targets.get(rid, "")
        if (not name or not target or not re.fullmatch(r"xl/worksheets/[^/]+\.xml", target)
            or s.get("state", "visible") != "visible"):
            raise BnpbWorkbookError("unreadable or hidden worksheet identity")
        sheet_paths.append((name, target))
    if not 1 <= len(sheet_paths) <= MAX_SHEETS:
        raise BnpbWorkbookError("invalid worksheet count")
    return sheet_paths


def _shared_strings(z: zipfile.ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    result = []
    for item in root.findall(f"{{{NS}}}si"):
        result.append("".join(n.text or "" for n in item.iter(f"{{{NS}}}t")))
    return result


def _read_rows(z: zipfile.ZipFile, path: str, strings: list[str]) -> list[dict[int, tuple[str, str]]]:
    root = ET.fromstring(z.read(path))
    if root.findall(f".//{{{NS}}}f"):
        raise BnpbWorkbookError("worksheet formulas not accepted as original data values")
    body = root.find(f"{{{NS}}}sheetData")
    if body is None:
        raise BnpbWorkbookError("missing worksheet sheetData")
    elements = body.findall(f"{{{NS}}}row")
    if len(elements) > MAX_ROWS:
        raise BnpbWorkbookError("worksheet row count exceeds budget")
    rows = []
    cells_total = 0
    prior_row_number = 0
    for row in elements:
        row_label = row.get("r", "")
        if not re.fullmatch(r"[1-9][0-9]{0,6}", row_label):
            raise BnpbWorkbookError("missing or invalid worksheet row number")
        current_row_number = int(row_label)
        if current_row_number <= prior_row_number or current_row_number > 1048576:
            raise BnpbWorkbookError("duplicate or unordered worksheet row number")
        prior_row_number = current_row_number
        cells: dict[int, tuple[str, str]] = {}
        for cell in row.findall(f"{{{NS}}}c"):
            cells_total += 1
            if cells_total > MAX_CELLS:
                raise BnpbWorkbookError("worksheet cell count exceeds budget")
            ref = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]{1,2})([1-9][0-9]{0,5})", ref)
            if not match or int(match[2]) != current_row_number:
                raise BnpbWorkbookError("invalid cell reference or row mismatch")
            col = 0
            for letter in match[1]:
                col = col * 26 + ord(letter) - ord("A") + 1
            col -= 1
            if col in cells:
                raise BnpbWorkbookError("duplicate cell in worksheet row")
            t = cell.get("t", "n")
            if t == "inlineStr":
                el = cell.find(f"{{{NS}}}is")
                value = "" if el is None else "".join(n.text or "" for n in el.iter(f"{{{NS}}}t"))
                kind = "text"
            else:
                v = cell.find(f"{{{NS}}}v")
                value = v.text if v is not None and v.text is not None else ""
                if t == "s":
                    try:
                        value = strings[int(value)]
                    except (IndexError, ValueError) as exc:
                        raise BnpbWorkbookError("invalid shared string reference") from exc
                    kind = "text"
                elif t == "n":
                    kind = "numeric"
                elif t == "str":
                    kind = "text"
                else:
                    raise BnpbWorkbookError("unsupported or error cell type")
            cells[col] = (value, kind)
        rows.append(cells)
    return rows


def _to_count(value: str, kind: str, *, column: str) -> int | None:
    cleaned = _clean(value)
    if cleaned in MISSING:
        return None
    # Accept digits in text-typed official KEKERINGAN / TSUNAMI fields, but never
    # reinterpret '—' or unknown sentinel as a zero. Reject fractional counts.
    if kind not in {"text", "numeric"}:
        raise BnpbWorkbookError(f"unsupported count cell type in {column}")
    try:
        numeric = Decimal(value.strip())
    except InvalidOperation as exc:
        raise BnpbWorkbookError(f"unrecognised count/missing marker in {column}") from exc
    if not numeric.is_finite() or numeric < 0 or numeric != numeric.to_integral_value():
        raise BnpbWorkbookError(f"negative/fractional/non-finite count in {column}")
    if numeric > 100000000:
        raise BnpbWorkbookError(f"implausibly huge count in {column}")
    return int(numeric)


def inspect_original(raw: bytes, *, resource: str, expected_sha256: str | None = None) -> dict:
    if resource not in RESOURCE_IDS:
        raise BnpbWorkbookError("unknown BNPB resource identity")
    if type(raw) is not bytes or not 250 <= len(raw) <= MAX_ORIGINAL_BYTES:
        raise BnpbWorkbookError("original XLSX byte budget exceeded or missing")
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and (not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
                                       or digest != expected_sha256):
        raise BnpbWorkbookError("original XLSX SHA-256 pin mismatch")
    required = HEADER_PROVINCE if resource == "province_houses" else HEADER_SUMMARY
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = _safe_members(z)
            strings = _shared_strings(z, names)
            candidates = []
            for sheet_name, sheet_path in _sheet_paths(z, names):
                rows = _read_rows(z, sheet_path, strings)
                for offset, header in enumerate(rows[:15]):
                    headers = {_clean(val): col for col, (val, _) in header.items() if val.strip()}
                    if required <= headers.keys():
                        if len(headers) != sum(bool(val.strip()) for val, _ in header.values()):
                            raise BnpbWorkbookError("duplicate or overlapping header name")
                        candidates.append((sheet_name, offset, headers, rows))
            if len(candidates) != 1:
                raise BnpbWorkbookError("expected exactly one sheet/header matching pinned resource grain")
            sheet, offset, headers, rows = candidates[0]
            if resource == "province_houses" and (SEVERITY & headers.keys()):
                raise BnpbWorkbookError("unexpected severity columns: distinct source grains cannot be combined")
            if resource == "peril_severity_summary" and "provinsi" in headers:
                raise BnpbWorkbookError("province×peril×severity crosswalk not established in this resource")
            target_cols = sorted((PERILS & headers.keys()) if resource == "province_houses"
                                 else ((SEVERITY | {"jumlah kejadian"}) & headers.keys()))
            if not target_cols:
                raise BnpbWorkbookError("no expected count columns")
            missing = {h: 0 for h in target_cols}
            row_count = 0
            province_keys: set[str] = set()
            peril_keys: set[str] = set()
            for row in rows[offset + 1:]:
                if not row or all(not v.strip() for v, _ in row.values()):
                    continue
                if resource == "province_houses":
                    province = row.get(headers["provinsi"], ("", "text"))[0].strip()
                    if not province:
                        raise BnpbWorkbookError("missing province identity")
                    key = province.casefold()
                    if key in province_keys:
                        raise BnpbWorkbookError("duplicate province identifier")
                    province_keys.add(key)
                else:
                    peril = row.get(headers["jenis bencana"], ("", "text"))[0].strip()
                    if not peril:
                        raise BnpbWorkbookError("missing event/peril identity")
                    key = _clean(peril)
                    if key in peril_keys:
                        raise BnpbWorkbookError("duplicate event/peril identity")
                    peril_keys.add(key)
                for name in target_cols:
                    value, kind = row.get(headers[name], ("", "text"))
                    if _to_count(value, kind, column=name) is None:
                        missing[name] += 1
                row_count += 1
            if not row_count:
                raise BnpbWorkbookError("no source rows after matched header")
    except (zipfile.BadZipFile, OSError, ET.ParseError, RuntimeError) as exc:
        raise BnpbWorkbookError("not a valid bounded OOXML workbook") from exc
    return {
        "evidence_class": "BNPB_2025_ORIGINAL_WORKBOOK_GRAIN_AND_TYPES_ONLY_NOT_ADMITTED",
        "official_dataset_url": DATASET_URL,
        "resource_name": resource,
        "official_resource_id": RESOURCE_IDS[resource],
        "original_bytes": len(raw),
        "original_sha256": digest,
        "independent_sha256_pin_verified": expected_sha256 is not None,
        "worksheet_name": sheet,
        "header_row_element_index": offset,
        "source_data_row_count": row_count,
        "expected_numeric_columns": target_cols,
        "missing_cell_counts_not_zero": missing,
        "province_key_count": len(province_keys) if resource == "province_houses" else None,
        "province_peril_severity_crosswalk_established": False,
        "source_values_or_claims_exported": False,
        "commercial_rights_reviewed": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource", required=True, choices=tuple(RESOURCE_IDS))
    parser.add_argument("--original-xlsx", required=True, type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    try:
        path = args.original_xlsx
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ORIGINAL_BYTES:
            raise BnpbWorkbookError("requires bounded regular original local XLSX")
        result = inspect_original(path.read_bytes(), resource=args.resource,
                                  expected_sha256=args.expected_sha256)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, BnpbWorkbookError) as exc:
        print("BLOCKED: " + str(exc)[:180], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
