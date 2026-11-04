#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded EIA-860 *annual 2025* original ZIP -> plant-ID coverage receipt.

The first live run captures a source ZIP/body hash and its 2025 Plant worksheet.
Do not equate EPA FRS programme IDs to annual EIA, GEM projects, owners, TIV,
policies, insurance company exposures or CAT model inputs. No raw data stored.
Live network access requires explicit --live on the exact official EIA URL.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import posixpath
import re
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

SOURCE_URL = "https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip"
SOURCE_RIGHTS_URL = "https://www.eia.gov/about/copyrights_reuse.php"
PLANT_MEMBER = "2___Plant_Y2025.xlsx"
MAX_ORIGINAL_BYTES = 28_000_000
# The 2026-11-04 byte-range central-directory inspection indicated 23,622,347
# archive bytes. It did not authenticate the complete ZIP or prove immutability.
PROVISIONAL_BYTE_RANGE_LENGTH = 23_622_347
MAX_MEMBER_BYTES = 8_000_000
MAX_XML_BYTES = 150_000_000
MAX_WORKBOOK_FILES = 100
MAX_PLANTS = 50_000
HEX = re.compile(r"[0-9a-f]{64}\Z")
PLANT_CODE = re.compile(r"[0-9]{1,6}\Z")
STATE = re.compile(r"[A-Z]{2}\Z")
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"

# Exact source-reported 2026-11-04 EPA FRS programme-link plant code cohort:
# 15 unique Delaware EIA-860 programme IDs across three city queries, plus
# one separate PA (ORIS 3136) source-identity challenge. These are *not* 2025
# annual EIA observations or insurer assets until checked independently.
EPA_DE_CODES = (
    "599", "7318", "57337", "57349", "67391", "10030",
    "63700", "591", "593", "7153", "59922", "597", "61934",
    "67572", "58110",
)
EPA_PA_CHALLENGE = "3136"


class EIA860ProofBlocked(ValueError):
    """Original-source identity, workbook semantics or coverage is not proven."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EIA860ProofBlocked("unexpected redirect from frozen EIA original ZIP endpoint")


def _read_member(zf: ZipFile, name: str, max_bytes: int) -> bytes:
    try:
        info = zf.getinfo(name)
    except KeyError as exc:
        raise EIA860ProofBlocked("exact expected original workbook member not found") from exc
    if info.is_dir() or info.file_size > max_bytes:
        raise EIA860ProofBlocked("ZIP member exceeds approved uncompressed byte ceiling")
    with zf.open(info) as inp:
        buf = inp.read(max_bytes + 1)
    if len(buf) > max_bytes or len(buf) != info.file_size:
        raise EIA860ProofBlocked("ZIP member size integrity failed")
    return buf


def _safe_zip(zf: ZipFile) -> None:
    items = zf.infolist()
    if not 0 < len(items) <= MAX_WORKBOOK_FILES:
        raise EIA860ProofBlocked("ZIP contains unsupported number of members")
    names = set()
    for item in items:
        path = item.filename
        if (path in names or path.startswith("/") or "\\" in path or
                ".." in path.split("/") or not path or
                item.file_size > MAX_XML_BYTES):
            raise EIA860ProofBlocked("unsafe, duplicate or unbounded ZIP member path")
        names.add(path)


def _xml(raw: bytes):
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise EIA860ProofBlocked("invalid XLSX XML metadata") from exc


def _plant_sheet_path(zf: ZipFile) -> str:
    book = _xml(_read_member(zf, "xl/workbook.xml", 2_000_000))
    sheets = book.findall(".//{%s}sheet" % NS)
    match = [s for s in sheets if s.get("name") == "Plant"]
    if len(match) != 1:
        raise EIA860ProofBlocked("expected exactly one annual EIA Plant worksheet")
    rid = match[0].get("{%s}id" % DOC_REL)
    rels = _xml(_read_member(zf, "xl/_rels/workbook.xml.rels", 2_000_000))
    matching = [r for r in rels.findall("{%s}Relationship" % REL)
                if r.get("Id") == rid and r.get("Type", "").endswith("/worksheet")]
    if len(matching) != 1 or matching[0].get("TargetMode") == "External":
        raise EIA860ProofBlocked("Plant worksheet relationship unverified")
    target = matching[0].get("Target", "")
    if target.startswith("/xl/"):
        path = target.lstrip("/")
    elif not target.startswith("/") and not target.startswith(".."):
        path = posixpath.normpath("xl/" + target)
    else:
        raise EIA860ProofBlocked("unsafe Plant sheet reference")
    if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", path):
        raise EIA860ProofBlocked("Plant worksheet resolved to unsupported path")
    return path


def _shared_strings(zf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = _xml(_read_member(zf, "xl/sharedStrings.xml", MAX_XML_BYTES))
    values = []
    for si in root.findall("{%s}si" % NS):
        # Exclude auxiliary phonetic markup from text identity.
        values.append("".join(t.text or "" for t in si.findall(".//{%s}t" % NS)))
    return values


def _cell_text(cell, shared: list[str]) -> str:
    kind = cell.get("t", "")
    if kind == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//{%s}t" % NS))
    v = cell.find("{%s}v" % NS)
    value = v.text if v is not None else None
    if value is None:
        return ""
    if kind == "s":
        if not value.isdigit() or int(value) >= len(shared):
            raise EIA860ProofBlocked("invalid original XLSX shared-string index")
        return shared[int(value)]
    if kind in ("", "n", "str"):
        return value
    # Reject formula error values instead of coercing them to plant IDs.
    if kind == "e":
        raise EIA860ProofBlocked("error cell in source plant worksheet")
    return value


def _col_number(ref: str) -> int:
    m = re.fullmatch(r"([A-Z]{1,3})[1-9][0-9]*", ref)
    if not m:
        raise EIA860ProofBlocked("invalid XLSX cell reference")
    v = 0
    for c in m.group(1):
        v = v * 26 + ord(c) - 64
    if v > 250:
        raise EIA860ProofBlocked("plant sheet column exceeds research limit")
    return v


def _plant_rows(xlsx: bytes) -> tuple[int, dict[str, str]]:
    try:
        with ZipFile(BytesIO(xlsx)) as wb:
            _safe_zip(wb)
            sheet = _plant_sheet_path(wb)
            shared = _shared_strings(wb)
            raw = _read_member(wb, sheet, MAX_XML_BYTES)
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise EIA860ProofBlocked("invalid or corrupt source Plant XLSX") from exc
    header = None
    plant_states = {}
    row_number = 0
    try:
        for _, elem in ET.iterparse(BytesIO(raw), events=("end",)):
            if elem.tag != "{%s}row" % NS:
                continue
            row_number += 1
            cells = {}
            for cell in elem.findall("{%s}c" % NS):
                col = _col_number(cell.get("r", ""))
                if col in cells:
                    raise EIA860ProofBlocked("repeated column in source XLSX row")
                cells[col] = _cell_text(cell, shared).strip()
            if header is None:
                cols = {v: k for k, v in cells.items() if v}
                if "Plant Code" in cols and "State" in cols and "Plant Name" in cols:
                    header = (cols["Plant Code"], cols["State"])
                elif row_number > 30:
                    raise EIA860ProofBlocked("no exact EIA annual Plant Code / State / Plant Name header")
                elem.clear()
                continue
            code = cells.get(header[0], "")
            st = cells.get(header[1], "")
            if not code and not st:
                elem.clear()
                continue
            if (not PLANT_CODE.fullmatch(code) or int(code) == 0 or
                    not STATE.fullmatch(st)):
                raise EIA860ProofBlocked("invalid plant code/state in annual Plant worksheet")
            normalized = str(int(code))
            if normalized in plant_states:
                raise EIA860ProofBlocked("duplicate annual EIA plant code")
            plant_states[normalized] = st
            if len(plant_states) > MAX_PLANTS:
                raise EIA860ProofBlocked("unbounded EIA annual plant inventory")
            elem.clear()
    except ET.ParseError as exc:
        raise EIA860ProofBlocked("malformed Plant worksheet XML") from exc
    if header is None or not plant_states:
        raise EIA860ProofBlocked("missing annual Plant inventory observations")
    return len(plant_states), plant_states


def check_original_archive(original: bytes, *, expected_sha256: str | None = None) -> dict:
    """Return only source hashes and aggregate identity counts; no actual raw rows."""
    if type(original) is not bytes or not 0 < len(original) <= MAX_ORIGINAL_BYTES:
        raise EIA860ProofBlocked("missing or oversized official source original ZIP")
    actual = sha256(original).hexdigest()
    if expected_sha256 is not None and (
            type(expected_sha256) is not str or not HEX.fullmatch(expected_sha256) or
            expected_sha256 != actual):
        raise EIA860ProofBlocked("original EIA ZIP SHA-256 mismatch against pinned receipt")
    try:
        with ZipFile(BytesIO(original)) as outer:
            _safe_zip(outer)
            member_names = outer.namelist()
            sheet_bytes = _read_member(outer, PLANT_MEMBER, MAX_MEMBER_BYTES)
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise EIA860ProofBlocked("corrupt or unrecognized original EIA annual ZIP") from exc
    count, states = _plant_rows(sheet_bytes)
    de_found = sum(x in states and states[x] == "DE" for x in EPA_DE_CODES)
    de_wrong = sum(x in states and states[x] != "DE" for x in EPA_DE_CODES)
    de_absent = sum(x not in states for x in EPA_DE_CODES)
    pa_present = EPA_PA_CHALLENGE in states
    pa_state_agrees = pa_present and states[EPA_PA_CHALLENGE] == "PA"
    if de_found + de_wrong + de_absent != len(EPA_DE_CODES):
        raise EIA860ProofBlocked("source research cohort failed row conservation")
    return {
        "profile": "eia860-annual-2025-official-plant-archive-v0",
        "source_url": SOURCE_URL,
        "provider_rights_url": SOURCE_RIGHTS_URL,
        "source_annual_vintage": 2025,
        "source_zip_body_sha256": actual,
        "source_zip_original_bytes": len(original),
        "source_zip_member_count": len(member_names),
        "plant_workbook_name": PLANT_MEMBER,
        "plant_workbook_sha256": sha256(sheet_bytes).hexdigest(),
        "plant_workbook_bytes": len(sheet_bytes),
        "original_2025_plant_inventory_records": count,
        "epa_delaware_source_reported_eia860_ids": len(EPA_DE_CODES),
        "delaware_ids_present_in_eia_2025_with_state_DE": de_found,
        "delaware_ids_present_with_state_mismatch": de_wrong,
        "delaware_ids_absent_from_eia_2025_plant_sheet": de_absent,
        "separate_pa_oris_3136_present_in_eia_2025": pa_present,
        "separate_pa_oris_3136_state_PA": pa_state_agrees,
        "source_byte_sha_pinned_before_download": expected_sha256 is not None,
        "original_source_zip_members_parsed": True,
        "source_full_archive_vendor_signed_digest_verified": False,
        "historical_2025_membership_is_current_2026_operating_status": False,
        "epa_frs_link_proves_physical_site_coordinates": False,
        "eia_plant_is_an_individual_generator_or_building": False,
        "eia_owner_row_proves_policyholder_or_insurer": False,
        "gem_plant_join_confirmed": False,
        "source_rights_or_model_admission_granted": False,
        "state": "REVIEW_STATE_MISMATCH" if de_wrong or (pa_present and not pa_state_agrees)
                 else "ANNUAL_2025_PLANT_ID_COVERAGE_RESEARCH_ONLY",
    }


def fetch_exact_official_source() -> bytes:
    req = Request(
        SOURCE_URL, headers={"Accept": "application/zip,application/x-zip-compressed",
                             "User-Agent": "OpenCatastrophe-data original EIA source research (read-only)"})
    try:
        with build_opener(_NoRedirect).open(req, timeout=50) as response:
            if response.status != 200 or response.geturl() != SOURCE_URL:
                raise EIA860ProofBlocked("unexpected EIA ZIP source HTTP status or redirect")
            return response.read(MAX_ORIGINAL_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise EIA860ProofBlocked("official EIA ZIP network fetch unavailable") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--original-zip", type=Path)
    parser.add_argument("--expected-original-sha256")
    args = parser.parse_args(argv)
    try:
        if args.live:
            data = fetch_exact_official_source()
        else:
            path = args.original_zip
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ORIGINAL_BYTES:
                raise EIA860ProofBlocked("require bounded local regular original archive")
            data = path.read_bytes()
        report = check_original_archive(data, expected_sha256=args.expected_original_sha256)
        report["acquired_via_exact_official_https_this_run"] = args.live
        report["capture_date_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    except (OSError, EIA860ProofBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_STATE_MISMATCH" else 0


if __name__ == "__main__":
    raise SystemExit(main())
