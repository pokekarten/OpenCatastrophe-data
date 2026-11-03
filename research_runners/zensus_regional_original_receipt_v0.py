# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Byte-level receipt of one official Zensus 2022 regional XLSX, no raw commit.

The live fetch is an EXPLICIT one-off CI research step, not a generic crawler.
It only processes the official Destatis publisher URL. Inspect OOXML package
metadata (not workbook numerical cells), calculate a complete original
SHA-256 and print an auditable *non-admission* receipt. File stays in memory.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


ORIGINAL_URL = (
    "https://www.destatis.de/static/DE/zensus/gitterdaten/"
    "Regionaltabelle_Gebaeude_Wohnungen.xlsx"
)
MAX_BYTES = 36_000_000
MAX_ARCHIVE_INFLATED_BYTES = 1_200_000_000
MAX_WORKBOOK_XML_BYTES = 2_000_000
MAX_FILES = 5000
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


class OriginalReceiptError(ValueError):
    """The original is inaccessible or failed a byte/package control."""


class _OnlyPublisherRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if parts.scheme != "https" or parts.hostname != "www.destatis.de":
            raise OriginalReceiptError("redirect left verified official HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _official_url(url: str) -> None:
    if url != ORIGINAL_URL:
        raise OriginalReceiptError("only the exact pre-reviewed Destatis workbook URL is allowed")


def download_original(url: str = ORIGINAL_URL) -> bytes:
    """One HTTPS request, no external storage and no arbitrary URLs."""
    _official_url(url)
    opener = build_opener(_OnlyPublisherRedirect())
    req = Request(url, headers={
        "User-Agent": "OpenCatastrophe-Research-Original-Metadata/0.1 (public reproducibility)",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
    buffer = io.BytesIO()
    try:
        with opener.open(req, timeout=60) as resp:
            final = resp.geturl()
            if urlsplit(final).scheme != "https" or urlsplit(final).hostname != "www.destatis.de":
                raise OriginalReceiptError("source response host mismatch")
            while True:
                chunk = resp.read(min(1024 * 1024, MAX_BYTES + 1 - buffer.tell()))
                if not chunk:
                    break
                buffer.write(chunk)
                if buffer.tell() > MAX_BYTES:
                    raise OriginalReceiptError("official source body exceeds bounded input cap")
    except (OSError, TimeoutError) as exc:
        raise OriginalReceiptError(f"official source retrieval failed: {type(exc).__name__}") from exc
    return buffer.getvalue()


def inspect_original_package(raw: bytes, *, source_url: str = ORIGINAL_URL) -> dict:
    """Analyze OOXML provenance and real worksheet *names*, not confidential cells."""
    _official_url(source_url)
    if not isinstance(raw, bytes) or not 10 <= len(raw) <= MAX_BYTES:
        raise OriginalReceiptError("original XLSX has invalid byte size")
    if not raw.startswith(b"PK"):
        raise OriginalReceiptError("original XLSX is not an OOXML ZIP package")
    try:
        with ZipFile(io.BytesIO(raw), "r") as archive:
            infos = archive.infolist()
            if len(infos) > MAX_FILES or not infos:
                raise OriginalReceiptError("unexpected XLSX archive entry count")
            if any(x.file_size < 0 or x.file_size > MAX_ARCHIVE_INFLATED_BYTES for x in infos):
                raise OriginalReceiptError("OOXML entry size exceeds bound")
            if sum(x.file_size for x in infos) > MAX_ARCHIVE_INFLATED_BYTES:
                raise OriginalReceiptError("total OOXML inflated size exceeds bound")
            names = {x.filename for x in infos}
            if any(x.startswith("/") or ".." in x.split("/") for x in names):
                raise OriginalReceiptError("unsafe OOXML path")
            needed = {"[Content_Types].xml", "xl/workbook.xml"}
            if not needed.issubset(names) or not any(
                name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                for name in names
            ):
                raise OriginalReceiptError("missing original workbook/package components")
            manifest_info = archive.getinfo("xl/workbook.xml")
            if manifest_info.file_size > MAX_WORKBOOK_XML_BYTES:
                raise OriginalReceiptError("original workbook manifest is abnormally large")
            manifest = archive.read("xl/workbook.xml")
    except (BadZipFile, RuntimeError, EOFError, KeyError) as exc:
        raise OriginalReceiptError("unreadable original OOXML ZIP") from exc
    try:
        root = ET.fromstring(manifest)
    except ET.ParseError as exc:
        raise OriginalReceiptError("malformed original OOXML workbook.xml") from exc
    sheets = root.find(NS + "sheets")
    if sheets is None:
        raise OriginalReceiptError("original workbook lacks sheets")
    titles = [elem.get("name", "") for elem in sheets.findall(NS + "sheet")]
    if not titles or len(titles) > 200 or any(not name or len(name) > 150 for name in titles):
        raise OriginalReceiptError("original worksheet titles are unavailable or invalid")
    if len(titles) != len(set(titles)):
        raise OriginalReceiptError("duplicate source worksheet titles")
    methodology = any("methodik" in name.casefold() or "erläuterung" in name.casefold()
                      for name in titles)
    return {
        "schema_version": "0.1.0",
        "input_kind": "official_unmodified_original_xlsx_bytes",
        "original_publisher_url": source_url,
        "original_file_sha256": hashlib.sha256(raw).hexdigest(),
        "original_file_bytes": len(raw),
        "ooxml_package_structure_verified": True,
        "original_worksheet_count": len(titles),
        "original_worksheet_names": titles[:60],
        "methodology_named_worksheet_present": methodology,
        "csv_or_machine_readable_named_sheets": [
            name for name in titles
            if "csv" in name.casefold() or "maschinen" in name.casefold()
        ][:50],
        "original_numerical_cells_validated": False,
        "kreis_ags_column_verified": False,
        "building_population_column_verified": False,
        "suppression_symbols_methodology_checked": False,
        "district_2022_buildings_admitted": False,
        "gdv_original_data_acquired": False,
        "insurer_regional_risk_sites_observed": False,
        "nextgen_cat_model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--official-live", action="store_true")
    group.add_argument("--local-original", type=str)
    args = parser.parse_args()
    try:
        if args.official_live:
            raw = download_original()
        else:
            from pathlib import Path
            path = Path(args.local_original)
            if path.stat().st_size > MAX_BYTES:
                raise OriginalReceiptError("input file size exceeds allowed bound")
            raw = path.read_bytes()
        result = inspect_original_package(raw)
    except (OSError, OriginalReceiptError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
