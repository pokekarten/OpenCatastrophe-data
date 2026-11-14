#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original EIA-860 2025 generator/utility source schema receipt, not a portfolio.

Reads one frozen official EIA ZIP. No source rows, company names, or coordinates
are emitted. The three generator inventory tabs have different reporting scopes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import posixpath
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

try:
    from research_runners import eia860_annual_2025_original_zip_v0 as eia
except ModuleNotFoundError as exc:
    if exc.name != "research_runners":
        raise
    import eia860_annual_2025_original_zip_v0 as eia

GENERATOR_MEMBER = "3_1_Generator_Y2025.xlsx"
UTILITY_MEMBER = "1___Utility_Y2025.xlsx"
MAX_GENERATOR_XLSX = 12_500_000
MAX_UTILITY_XLSX = 800_000
MAX_SHEETS = 8
MAX_HEADER_ROWS = 35
MAX_XML_FILE = 160_000_000
ALLOWED_HEADERS = frozenset((
    "Plant Code", "Plant Name", "Generator ID", "Generator", "Utility ID",
    "Utility Name", "State", "Status", "Status Code", "Operating Status",
    "Operational Status", "Ownership", "Ownership Code",
    "Nameplate Capacity (MW)", "Nameplate Capacity", "Nameplate Capacity (MW) ",
    "Prime Mover", "Energy Source 1", "Energy Source Code 1",
    "Operating Year", "Retirement Year", "Technology",
    "Entity Type", "Street Address", "City", "Zip", "Zip Code",
))
# Never allow free-form source text to become a log field. Row 1 can contain
# source banners, names, or dates; only predefined column headers are reported.
SAFE_SHEET_NAME = re.compile(r"[A-Za-z0-9 _&(),.-]{1,60}\Z")
SOURCE_SHA = eia.PINNED_ORIGINAL_SHA256
SOURCE_BYTES = eia.PINNED_SOURCE_BYTES


class GeneratorRosterBlocked(ValueError):
    """Original archive, exact workbook sheets or schema cannot be established."""


def _sheets(xlsx: bytes) -> tuple[list[tuple[str, str]], list[str], ZipFile, BytesIO]:
    # Kept as one context-owned XLSX; caller closes the returned objects.
    blob = BytesIO(xlsx)
    try:
        bookzip = ZipFile(blob)
        eia._safe_zip(bookzip)
        book = eia._xml(eia._read_member(bookzip, "xl/workbook.xml", 2_000_000))
        rels = eia._xml(eia._read_member(bookzip, "xl/_rels/workbook.xml.rels", 2_000_000))
        relations = {r.get("Id"): r for r in rels.findall("{%s}Relationship" % eia.REL)}
        ss = eia._shared_strings(bookzip)
        sheets = book.findall(".//{%s}sheet" % eia.NS)
        if not 0 < len(sheets) <= MAX_SHEETS:
            raise GeneratorRosterBlocked("unexpected number of XLSX worksheets")
        out = []
        seen = set()
        for sheet in sheets:
            name = sheet.get("name", "")
            if not SAFE_SHEET_NAME.fullmatch(name) or name in seen:
                raise GeneratorRosterBlocked("unapproved or duplicate source sheet name")
            seen.add(name)
            rid = sheet.get("{%s}id" % eia.DOC_REL)
            rel = relations.get(rid)
            if rel is None or not rel.get("Type", "").endswith("/worksheet") or rel.get("TargetMode") == "External":
                raise GeneratorRosterBlocked("invalid internal sheet relationship")
            target = rel.get("Target", "")
            if target.startswith("/xl/"):
                path = target.lstrip("/")
            elif not target.startswith("/") and not target.startswith(".."):
                path = posixpath.normpath("xl/" + target)
            else:
                raise GeneratorRosterBlocked("invalid worksheet reference")
            if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", path):
                raise GeneratorRosterBlocked("unsupported worksheet path")
            out.append((name, path))
        return out, ss, bookzip, blob
    except (BadZipFile, OSError, RuntimeError, eia.EIA860ProofBlocked, ET.ParseError) as exc:
        blob.close()
        raise GeneratorRosterBlocked("corrupt original OOXML workbook") from exc


def _header_receipt(zf: ZipFile, name: str, shared: list[str]) -> dict:
    try:
        info = zf.getinfo(name)
        if info.file_size > MAX_XML_FILE:
            raise GeneratorRosterBlocked("original worksheet XML exceeds byte ceiling")
        seen = set()
        candidate_rows = 0
        rows = 0
        with zf.open(info) as f:
            for _, row in ET.iterparse(f, events=("end",)):
                if row.tag != "{%s}row" % eia.NS:
                    continue
                rows += 1
                words = set()
                for c in row.findall("{%s}c" % eia.NS):
                    # Column headers and real source values can co-exist in
                    # first 35 rows; only this fixed vocabulary can be emitted.
                    v = eia._cell_text(c, shared).strip()
                    if v in ALLOWED_HEADERS:
                        words.add(v)
                        seen.add(v)
                if "Plant Code" in words and "Generator ID" in words:
                    candidate_rows += 1
                row.clear()
                if rows >= MAX_HEADER_ROWS:
                    break
        return {
            "first_rows_scanned_at_most_35": rows,
            "fixed_allowlist_header_labels": sorted(seen),
            "plant_code_and_generator_id_same_header_row": candidate_rows,
            "raw_source_rows_or_operator_names_emitted": False,
        }
    except (KeyError, BadZipFile, OSError, RuntimeError, eia.EIA860ProofBlocked, ET.ParseError) as exc:
        raise GeneratorRosterBlocked("cannot safely inspect native worksheet") from exc


def inspect_workbook(xlsx: bytes, *, scope: str) -> dict:
    if scope not in ("generator", "utility"):
        raise GeneratorRosterBlocked("invalid workbook scope")
    limit = MAX_GENERATOR_XLSX if scope == "generator" else MAX_UTILITY_XLSX
    if type(xlsx) is not bytes or not 0 < len(xlsx) <= limit:
        raise GeneratorRosterBlocked("original workbook absent or over research size limit")
    sheets, ss, zf, buffer = _sheets(xlsx)
    try:
        result = [{"name": name, **_header_receipt(zf, path, ss)}
                  for name, path in sheets]
    finally:
        zf.close()
        buffer.close()
    if scope == "generator":
        expected = {"Operable", "Proposed", "Retired and Canceled"}
        if {x["name"] for x in result} != expected:
            raise GeneratorRosterBlocked("expected original generator reporting scope missing")
    return {
        "member": GENERATOR_MEMBER if scope == "generator" else UTILITY_MEMBER,
        "source_xlsx_sha256": sha256(xlsx).hexdigest(),
        "source_xlsx_bytes": len(xlsx),
        "worksheet_count": len(result),
        "worksheets": result,
        "raw_generator_rows_or_owner_names_exported": False,
    }


def inspect_original_zip(original: bytes) -> dict:
    try:
        meta = eia.check_original_archive(original, expected_sha256=SOURCE_SHA)
        with ZipFile(BytesIO(original)) as zf:
            eia._safe_zip(zf)
            generator = eia._read_member(zf, GENERATOR_MEMBER, MAX_GENERATOR_XLSX)
            utility = eia._read_member(zf, UTILITY_MEMBER, MAX_UTILITY_XLSX)
        gen = inspect_workbook(generator, scope="generator")
        util = inspect_workbook(utility, scope="utility")
    except (BadZipFile, OSError, RuntimeError, eia.EIA860ProofBlocked) as exc:
        raise GeneratorRosterBlocked("original full EIA source SHA/ZIP not verified") from exc
    return {
        "profile": "eia-860-2025-original-generator-utility-schema-v0",
        "source_url": eia.SOURCE_URL,
        "source_original_sha256": SOURCE_SHA,
        "source_original_bytes": len(original),
        "source_year": 2025,
        "eia_plant_sheet_records": meta["original_2025_plant_inventory_records"],
        "delaware_epa_frseia_plant_ids_confirmed": meta["delaware_ids_present_in_eia_2025_with_state_DE"],
        "generator": gen,
        "utility": util,
        "generator_owner_schedule_or_utility_operator_identity_resolved": False,
        "generator_tab_is_full_operational_history": False,
        "unit_count_equals_insured_site_count": False,
        "reinsurance_cover_or_tiv_inferred": False,
        "model_source_approval": False,
        "state": "NATIVE_GENERATOR_UTILITY_SCHEMA_RESEARCH_ONLY",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--live", action="store_true")
    g.add_argument("--original-zip", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.live:
            data = eia.fetch_exact_official_source()
        else:
            p = args.original_zip
            if p.is_symlink() or not p.is_file() or p.stat().st_size > eia.MAX_ORIGINAL_BYTES:
                raise GeneratorRosterBlocked("local original EIA ZIP missing or invalid")
            data = p.read_bytes()
        report = inspect_original_zip(data)
        report["original_download_this_run"] = args.live
    except (OSError, eia.EIA860ProofBlocked, GeneratorRosterBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
