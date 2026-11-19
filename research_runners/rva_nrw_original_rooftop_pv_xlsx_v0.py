# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only original-publisher NRW municipality rooftop PV POTENTIAL XLSX preflight.

No spreadsheet parser dependency, no row-level geolocation/owner printing, no
R+V policy or insured-location inference. XML/ZIP input is untrusted.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

SOURCE_URL = (
    "https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/"
    "solarkataster/photovoltaik/"
    "Dach-PV-nach-Gebaeudekategorien-Gemeindeebene_Excel.xlsx"
)
SOURCE_LANDING = (
    "https://www.opengeodata.nrw.de/produkte/umwelt_klima/"
    "energie/solarkataster/photovoltaik/"
)
SOURCE_DATE = "2026-03-12"
EXPECTED_SHA256 = "a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071"
EXPECTED_BYTES = 1506519
EXPECTED_STRUCTURE = [(6, 2), (397, 254), (397, 254), (397, 9), (397, 9)]
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 125 * 1024 * 1024
MAX_SINGLE_UNCOMPRESSED = 65 * 1024 * 1024
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
ENTRY_RE = re.compile(r"^xl/worksheets/sheet[0-9]+\.xml$")
UNSAFE = ("xl/externalLinks/", "xl/vbaProject.bin", "xl/connections.xml")


def fetch_official(*, open_url=urllib.request.urlopen):
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "OpenCatastrophe-research-metadata-preflight/0.1"},
    )
    with open_url(request, timeout=45) as response:
        chunks = []
        size = 0
        while True:
            chunk = response.read(128 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_SOURCE_BYTES:
                raise ValueError("ORIGINAL_SOURCE_TOO_LARGE")
            chunks.append(chunk)
        return b"".join(chunks)


def parse_original(original: bytes, *, expected_sha256=None, expected_bytes=None, expected_structure=None):
    if not isinstance(original, bytes):
        raise ValueError("ORIGINAL_SOURCE_NOT_BYTES")
    if not (1024 <= len(original) <= MAX_SOURCE_BYTES):
        raise ValueError("ORIGINAL_SOURCE_BAD_SIZE")
    digest = hashlib.sha256(original).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("ORIGINAL_SOURCE_SHA256_MISMATCH")
    if expected_bytes is not None and len(original) != expected_bytes:
        raise ValueError("ORIGINAL_SOURCE_BYTE_LENGTH_MISMATCH")
    try:
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            members = archive.infolist()
            if len(members) > 180:
                raise ValueError("ORIGINAL_ZIP_MEMBER_COUNT_EXCESS")
            paths = [x.filename for x in members]
            if len(set(paths)) != len(paths):
                raise ValueError("ORIGINAL_DUPLICATE_ZIP_ENTRY")
            if any(n.startswith(UNSAFE) or ".." in n.split("/") for n in paths):
                raise ValueError("ORIGINAL_EXTERNAL_OR_UNSAFE_ZIP_ENTRY")
            if sum(x.file_size for x in members) > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("ORIGINAL_ZIP_EXPANSION_EXCESS")
            if any(x.file_size > MAX_SINGLE_UNCOMPRESSED for x in members):
                raise ValueError("ORIGINAL_ZIP_SINGLE_ENTRY_EXCESS")
            if "[Content_Types].xml" not in paths or "xl/workbook.xml" not in paths:
                raise ValueError("ORIGINAL_NOT_XLSX")
            sheets = [x for x in paths if ENTRY_RE.fullmatch(x)]
            if not sheets:
                raise ValueError("ORIGINAL_WORKSHEETS_MISSING")
            if "xl/sharedStrings.xml" in paths:
                strings_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(x.itertext()) for x in strings_root.findall("m:si", NS)]
            else:
                shared = []
            workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
            names = [x.attrib.get("name", "") for x in workbook_root.findall(".//m:sheet", NS)]
            if not names:
                raise ValueError("ORIGINAL_WORKBOOK_SHEET_LIST_EMPTY")
            stats = []
            for entry in sorted(sheets):
                root = ET.fromstring(archive.read(entry))
                rows = root.findall(".//m:sheetData/m:row", NS)
                if not rows:
                    raise ValueError("ORIGINAL_EMPTY_WORKSHEET")
                formulas = root.findall(".//m:f", NS)
                if formulas:
                    raise ValueError("ORIGINAL_UNTRUSTED_FORMULAS")
                # Only return shape/column count. No municipality or coordinate values.
                max_cols = max((len(row.findall("m:c", NS)) for row in rows), default=0)
                if max_cols < 2:
                    raise ValueError("ORIGINAL_TOO_FEW_COLUMNS")
                stats.append({
                    "worksheet_xml_name": entry.split("/")[-1],
                    "occupied_row_elements": len(rows),
                    "max_occupied_columns": max_cols,
                })
    except (zipfile.BadZipFile, ET.ParseError, RuntimeError) as exc:
        raise ValueError("ORIGINAL_XLSX_BAD_STRUCTURE") from exc
    if expected_structure is not None and [
        (x["occupied_row_elements"], x["max_occupied_columns"]) for x in stats
    ] != expected_structure:
        raise ValueError("ORIGINAL_WORKSHEET_SHAPE_MISMATCH")
    return {
        "status": "ORIGINAL_BYTES_OBSERVED_RESEARCH_ONLY",
        "original_source_url": SOURCE_URL,
        "publisher_landing_url": SOURCE_LANDING,
        "publisher_listing_date": SOURCE_DATE,
        "original_sha256": digest,
        "original_bytes": len(original),
        "worksheet_count": len(sheets),
        "workbook_sheets_count": len(names),
        "shared_string_count": len(shared),
        "worksheet_structure": stats,
        "source_geography": "NRW_MUNICIPALITY_AGGREGATE",
        "source_measure": "ROOFTOP_PV_TECHNICAL_POTENTIAL_NOT_INSTALLED",
        "insured_company_sites_observed": False,
        "pv_installed_units_observed": False,
        "insurer_roof_pv_endorsement_observed": False,
        "actual_model_input_admitted": False,
        "original_sha_pinned_in_source_code": expected_sha256 is not None,
    }


def main():
    original = fetch_official()
    result = parse_original(
        original,
        expected_sha256=EXPECTED_SHA256,
        expected_bytes=EXPECTED_BYTES,
        expected_structure=EXPECTED_STRUCTURE,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TimeoutError) as exc:
        # No remote payload / URL / query leakage on failure.
        print("NRW_PV_ORIGINAL_PREFLIGHT_BLOCKED: " + str(exc)[:72], file=sys.stderr)
        sys.exit(2)
