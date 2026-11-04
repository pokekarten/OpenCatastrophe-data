#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-original EIA-860 annual 2025 generator Owner workbook schema proof.

Strictly metadata-only. This research pass identifies workbook/worksheet grain;
it neither interprets a missing Owner row nor exports anyone's ownership records.
"""
from __future__ import annotations

import argparse
from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path
import posixpath
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

from research_runners import eia860_annual_2025_original_zip_v0 as eia

OWNER_MEMBER = "4___Owner_Y2025.xlsx"
MAX_OWNER_XLSX = 1_200_000
MAX_SHEET_XML = 8_000_000
MAX_SHEETS = 8
MAX_FIRST_ROWS = 35
# Header evidence is a subset of fixed ordinary column names; do not print
# arbitrary source text even if a source row resembles a header.
HEADER_KEYS = (
    "Plant Code", "Plant ID", "Plant Name", "Generator ID", "Generator",
    "Owner Name", "Owner", "Owner Code", "Owner Utility ID",
    "Operator", "Operator Code", "Percent Owned", "Percentage Owned",
    "Percent of Generator Owned", "Ownership Percentage", "State",
    "Reporting Year", "Report Year", "Utility ID",
)


class OwnerSchemaBlocked(ValueError):
    """Annual original owner source unsupported, incomplete or unverified."""


def _workbook_sheet_paths(wb: ZipFile) -> list[tuple[str, str]]:
    book = eia._xml(eia._read_member(wb,"xl/workbook.xml", 2_000_000))
    rels = eia._xml(eia._read_member(wb,"xl/_rels/workbook.xml.rels", 2_000_000))
    rid = {r.get("Id"):r for r in rels.findall("{%s}Relationship" % eia.REL)}
    sheets = book.findall(".//{%s}sheet" % eia.NS)
    if not 0 < len(sheets) <= MAX_SHEETS:
        raise OwnerSchemaBlocked("unexpected owner XLSX worksheet count")
    result=[]
    for sheet in sheets:
        name = sheet.get("name","")
        if not re.fullmatch(r"[A-Za-z0-9 _-]{1,60}", name):
            raise OwnerSchemaBlocked("unexpected workbook worksheet title")
        rel=rid.get(sheet.get("{%s}id" % eia.DOC_REL))
        if rel is None or not rel.get("Type","").endswith("/worksheet") or rel.get("TargetMode")=="External":
            raise OwnerSchemaBlocked("missing internal owner worksheet relationship")
        dest=rel.get("Target","")
        if dest.startswith("/xl/"):
            path=dest[1:]
        elif not dest.startswith("/") and not dest.startswith(".."):
            path=posixpath.normpath("xl/"+dest)
        else:
            raise OwnerSchemaBlocked("unsafe original workbook relation")
        if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml",path):
            raise OwnerSchemaBlocked("unknown original owner worksheet file")
        result.append((name,path))
    return result


def _header_tokens(wb: ZipFile, sheet_path: str, shared: list[str]) -> dict:
    xml = eia._read_member(wb,sheet_path,MAX_SHEET_XML)
    seen_headers=set()
    rows_scanned=0
    candidate_header_rows=0
    for _event, elem in ET.iterparse(BytesIO(xml),events=("end",)):
        if elem.tag!="{%s}row" % eia.NS:
            continue
        rows_scanned+=1
        words=[]
        for cell in elem.findall("{%s}c" % eia.NS):
            text=eia._cell_text(cell,shared).strip()
            if text in HEADER_KEYS:
                seen_headers.add(text)
                words.append(text)
        if any(s in words for s in ("Plant Code","Plant ID")) and (
                any(s in words for s in ("Generator ID","Generator")) or
                any(s in words for s in ("Owner","Owner Name"))):
            candidate_header_rows+=1
        elem.clear()
        if rows_scanned>=MAX_FIRST_ROWS:
            break
    return {
        "rows_scanned_for_header_only":rows_scanned,
        "recognized_allowlisted_header_tokens":sorted(seen_headers),
        "candidate_plant_generator_or_owner_header_rows":candidate_header_rows,
        "arbitrary_source_rows_or_values_emitted":False,
    }


def inspect_owner_original_zip(original:bytes)->dict:
    try:
        outer=eia.check_original_archive(original,expected_sha256=eia.PINNED_ORIGINAL_SHA256)
        with ZipFile(BytesIO(original)) as archive:
            eia._safe_zip(archive)
            member=eia._read_member(archive,OWNER_MEMBER,MAX_OWNER_XLSX)
        with ZipFile(BytesIO(member)) as wb:
            eia._safe_zip(wb)
            sheets=_workbook_sheet_paths(wb)
            shared=eia._shared_strings(wb)
            sheet_receipts=[]
            for name,path in sheets:
                r=_header_tokens(wb,path,shared)
                sheet_receipts.append({"sheet_name":name,**r})
    except (BadZipFile,OSError,RuntimeError,ET.ParseError,eia.EIA860ProofBlocked) as exc:
        raise OwnerSchemaBlocked("unsupported or corrupt source-owner ZIP/XLSX") from exc
    return {
        "profile":"eia860-2025-generator-owner-native-header-v0",
        "source_url":eia.SOURCE_URL,
        "source_zip_sha256":eia.PINNED_ORIGINAL_SHA256,
        "source_original_bytes":len(original),
        "owner_workbook_name":OWNER_MEMBER,
        "owner_xlsx_sha256":sha256(member).hexdigest(),
        "owner_xlsx_bytes":len(member),
        "sheet_count":len(sheet_receipts),
        "sheets":sheet_receipts,
        "independent_plant_original_inventory_count":outer["original_2025_plant_inventory_records"],
        "epa_delaware_eia_2025_id_and_state_confirmation":outer["delaware_ids_present_in_eia_2025_with_state_DE"],
        "generator_ownership_fraction_verified":False,
        "missing_owner_row_proves_missing_legal_owner":False,
        "legal_owner_equals_insurance_group":False,
        "owner_names_or_addresses_exported":False,
        "license_or_scientific_model_admission_granted":False,
        "state":"ORIGINAL_OWNER_WORKBOOK_SCHEMA_RESEARCH_ONLY",
    }


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--live",action="store_true")
    g.add_argument("--original-zip",type=Path)
    args=parser.parse_args(argv)
    try:
        if args.live:
            original=eia.fetch_exact_official_source()
        else:
            p=args.original_zip
            if p.is_symlink() or not p.is_file() or p.stat().st_size>eia.MAX_ORIGINAL_BYTES:
                raise OwnerSchemaBlocked("expected bounded original local EIA ZIP")
            original=p.read_bytes()
        receipt=inspect_owner_original_zip(original)
        receipt["live_original_source_download"]=args.live
    except (OSError,OwnerSchemaBlocked,eia.EIA860ProofBlocked) as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc)}))
        return 2
    print(json.dumps(receipt,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
