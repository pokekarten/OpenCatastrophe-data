#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-original EIA-860 2025 generator Owner-row aggregate, Delaware pilot.

Generator-keyed ownership rows in Schedule 4 exist for jointly or third-party
owned generators; an absent row is not a proven 0% owner or an absent asset.
No names, addresses, source rows or insurer TIV are printed or persisted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import argparse
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

try:
    from research_runners import eia860_annual_2025_original_zip_v0 as eia
    from research_runners import eia860_2025_original_owner_schema_v0 as owner
except ModuleNotFoundError as exc:
    if exc.name != "research_runners":
        raise
    import eia860_annual_2025_original_zip_v0 as eia
    import eia860_2025_original_owner_schema_v0 as owner

PINNED_OWNER_XLSX_SHA = "f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383"
REQUIRED_HEADERS = ("Plant Code", "Generator ID", "Owner Name", "Percent Owned")
MAX_ROWS = 75_000
ID = re.compile(r"[0-9]{1,6}\Z")
GENERATOR = re.compile(r"[A-Za-z0-9_.:-]{1,30}\Z")
SHARE = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,8})?\Z")
TOL = Decimal("0.05")


class OwnerShareBlocked(ValueError):
    """Source-native ownership shares cannot be safely interpreted."""


def inspect_owner_worksheet(owner_xlsx:bytes, *,
                            require_original_member_sha:bool=False)->dict:
    if not isinstance(require_original_member_sha,bool):
        raise OwnerShareBlocked("explicit native-member approval must be a boolean")
    if require_original_member_sha and sha256(owner_xlsx).hexdigest()!=PINNED_OWNER_XLSX_SHA:
        raise OwnerShareBlocked("original Owner XLSX checksum differs from pinned source")
    try:
        with ZipFile(BytesIO(owner_xlsx)) as wb:
            eia._safe_zip(wb)
            matches=[path for name,path in owner._workbook_sheet_paths(wb) if name=="Ownership"]
            if len(matches)!=1:
                raise OwnerShareBlocked("expected exactly one EIA annual Ownership worksheet")
            shared=eia._shared_strings(wb)
            raw=eia._read_member(wb,matches[0],owner.MAX_SHEET_XML)
            style_xml=(eia._read_member(wb,"xl/styles.xml",2_000_000)
                       if "xl/styles.xml" in wb.namelist() else None)
    except (BadZipFile,OSError,RuntimeError,eia.EIA860ProofBlocked,owner.OwnerSchemaBlocked) as exc:
        raise OwnerShareBlocked("invalid original annual generator Owner workbook") from exc
    style_root=eia._xml(style_xml) if style_xml is not None else None
    cell_xfs=(style_root.find("{%s}cellXfs" % eia.NS)
              if style_root is not None else None)
    styles=[] if cell_xfs is None else [x.get("numFmtId","0") for x in cell_xfs]
    percent_styles=Counter()
    raw_le_one=raw_gt_one=0
    native_percent_style_rows=unresolved_percent_style_rows=0
    hdr=None
    row_n=0
    source_rows=0
    cohort_rows=0
    unparsed_shares=0
    invalid_owner_identity=0
    repeated_plant_generator_owner=0
    cohorts=set(eia.EPA_DE_CODES)
    groups:dict[tuple[str,str],dict]=defaultdict(lambda:{"total":Decimal(0),"incomplete":False,"owners":set()})
    try:
        for _event, elem in ET.iterparse(BytesIO(raw),events=("end",)):
            if elem.tag!="{%s}row" % eia.NS:
                continue
            row_n+=1
            if row_n>MAX_ROWS:
                raise OwnerShareBlocked("Owner sheet row limit exceeded")
            cells={}
            cell_styles={}
            for cell in elem.findall("{%s}c" % eia.NS):
                c=eia._col_number(cell.get("r",""))
                if c in cells:
                    raise OwnerShareBlocked("duplicated original Owner worksheet column")
                cells[c]=eia._cell_text(cell,shared).strip()
                cell_styles[c]=cell.get("s","0")
            if hdr is None:
                inverse={value:col for col,value in cells.items() if value}
                if all(field in inverse for field in REQUIRED_HEADERS):
                    hdr=tuple(inverse[k] for k in REQUIRED_HEADERS)
                elif row_n>35:
                    raise OwnerShareBlocked("original EIA Owner worksheet exact headers not established")
                elem.clear()
                continue
            src_plant=cells.get(hdr[0],"")
            generator=cells.get(hdr[1],"")
            if not src_plant or not generator:
                elem.clear()
                continue
            source_rows+=1
            if not ID.fullmatch(src_plant) or int(src_plant)==0:
                # Unparseable source row cannot be assigned to any plant.
                raise OwnerShareBlocked("bad source Owner Plant Code")
            plant=str(int(src_plant))
            if plant not in cohorts:
                elem.clear()
                continue
            cohort_rows+=1
            if not GENERATOR.fullmatch(generator):
                raise OwnerShareBlocked("invalid in-cohort generator ID")
            owner_name=cells.get(hdr[2],"")
            pct=cells.get(hdr[3],"")
            style_index=cell_styles.get(hdr[3],"0")
            percent_styles[style_index]+=1
            style_numfmt=(styles[int(style_index)]
                          if style_index.isdigit() and int(style_index)<len(styles)
                          else "UNRESOLVED")
            uses_native_percent_style=style_numfmt in ("9","10")
            if uses_native_percent_style:
                native_percent_style_rows+=1
            elif require_original_member_sha:
                unresolved_percent_style_rows+=1
            group=groups[(plant,generator)]
            if not owner_name or len(owner_name)>180:
                invalid_owner_identity+=1
                group["incomplete"]=True
            elif owner_name in group["owners"]:
                repeated_plant_generator_owner+=1
                group["incomplete"]=True
            else:
                group["owners"].add(owner_name)
            if not SHARE.fullmatch(pct):
                unparsed_shares+=1
                group["incomplete"]=True
            else:
                try:
                    share=Decimal(pct)
                except InvalidOperation:
                    unparsed_shares+=1
                    group["incomplete"]=True
                else:
                    if Decimal("0")<=share<=Decimal("1"):
                        raw_le_one+=1
                    elif share>Decimal("1"):
                        raw_gt_one+=1
                    if require_original_member_sha and not uses_native_percent_style:
                        # For a verified original workbook, absent/unknown format
                        # must not be silently interpreted as percentage points.
                        unparsed_shares+=1
                        group["incomplete"]=True
                    else:
                        # OOXML stores percent-formatted cells as fractions:
                        # 0.40 with built-in numFmtId 10 is 40 percent points.
                        percent_points=share*Decimal("100") if uses_native_percent_style else share
                        if not Decimal("0")<=percent_points<=Decimal("100"):
                            unparsed_shares+=1
                            group["incomplete"]=True
                        else:
                            group["total"]+=percent_points
            elem.clear()
    except (ET.ParseError,eia.EIA860ProofBlocked) as exc:
        raise OwnerShareBlocked("malformed original owner XLSX row XML") from exc
    if hdr is None:
        raise OwnerShareBlocked("no complete original Owner worksheet header")
    good=low=high=incomplete=0
    for g in groups.values():
        if g["incomplete"]:
            incomplete+=1
        elif abs(g["total"]-Decimal("100"))<=TOL:
            good+=1
        elif g["total"]<Decimal("100")-TOL:
            low+=1
        else:
            high+=1
    if good+low+high+incomplete!=len(groups):
        raise OwnerShareBlocked("generator ownership aggregate failed conservation")
    return {
        "profile":"eia860-2025-annual-owner-generator-share-cohort-v0",
        "owner_worksheet":"Ownership",
        "owner_workbook_sha256":sha256(owner_xlsx).hexdigest(),
        "original_owner_member_sha_pinned":require_original_member_sha,
        "delaware_epa_eia_plant_cohort":len(cohorts),
        "source_rows_with_plant_and_generator_fields":source_rows,
        "delaware_owner_schedule_rows":cohort_rows,
        "delaware_owner_raw_percentage_cells_between_0_and_1":raw_le_one,
        "delaware_owner_raw_percentage_cells_greater_than_1":raw_gt_one,
        "delaware_percent_owned_source_cell_style_counts":dict(sorted(percent_styles.items())),
        "delaware_percent_owned_style_number_format_ids":{
            st:(styles[int(st)] if st.isdigit() and int(st)<len(styles) else "UNRESOLVED")
            for st in sorted(percent_styles)
        },
        "delaware_owner_rows_with_native_percent_format":native_percent_style_rows,
        "delaware_owner_rows_with_unresolved_original_percent_format":unresolved_percent_style_rows,
        "percent_units_interpreted_using_original_xlsx_style":(
            require_original_member_sha and cohort_rows>0 and
            native_percent_style_rows==cohort_rows and unresolved_percent_style_rows==0),
        "delaware_plant_ids_with_explicit_owner_schedule_rows":len({x[0] for x in groups}),
        "delaware_distinct_generators_with_owner_schedule_rows":len(groups),
        "delaware_generators_owner_sum_100_within_0_05_percentage_points":good,
        "delaware_generators_owner_sum_below_99_95_pct":low,
        "delaware_generators_owner_sum_above_100_05_pct":high,
        "delaware_generators_ownership_unverifiable_due_to_bad_rows":incomplete,
        "delaware_owner_rows_with_unparsed_share":unparsed_shares,
        "delaware_owner_rows_with_empty_or_invalid_owner_name":invalid_owner_identity,
        "delaware_repeated_generator_owner_name_rows":repeated_plant_generator_owner,
        "cohort_generator_group_count_conserved":True,
        "source_owner_name_or_address_emitted":False,
        "unreported_generators_are_operator_owned_proven":False,
        "generator_owner_share_proves_company_group_legal_share":False,
        "eia_utility_id_equals_insurer_lei":False,
        "insurer_policies_or_tiv_inferred":False,
        "gem_owner_id_or_location_join_confirmed":False,
        "source_scientific_or_insurance_model_admission_granted":False,
        "state":"REVIEW_OWNER_SHARE_ANOMALIES" if low or high or incomplete
                else "EIA_OWNER_GENERATOR_SHARES_RESEARCH_ONLY",
    }


def inspect_pinned_archive(original:bytes)->dict:
    try:
        original_meta=eia.check_original_archive(original,expected_sha256=eia.PINNED_ORIGINAL_SHA256)
        with ZipFile(BytesIO(original)) as outer:
            eia._safe_zip(outer)
            member=eia._read_member(outer,owner.OWNER_MEMBER,owner.MAX_OWNER_XLSX)
        r=inspect_owner_worksheet(member,require_original_member_sha=True)
    except (BadZipFile,OSError,RuntimeError,eia.EIA860ProofBlocked) as exc:
        raise OwnerShareBlocked("source original EIA annual ZIP identity mismatch") from exc
    r["source_original_zip_sha256"]=eia.PINNED_ORIGINAL_SHA256
    r["eia_annual_plant_inventory_rows"]=original_meta["original_2025_plant_inventory_records"]
    return r


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--live",action="store_true")
    g.add_argument("--original-zip",type=Path)
    a=p.parse_args(argv)
    try:
        if a.live:
            data=eia.fetch_exact_official_source()
        else:
            if (a.original_zip.is_symlink() or not a.original_zip.is_file() or
                    a.original_zip.stat().st_size>eia.MAX_ORIGINAL_BYTES):
                raise OwnerShareBlocked("expected local bounded original EIA ZIP")
            data=a.original_zip.read_bytes()
        report=inspect_pinned_archive(data)
        report["live_source_acquisition"]=a.live
    except (OSError,OwnerShareBlocked,eia.EIA860ProofBlocked) as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc)}))
        return 2
    print(json.dumps(report,sort_keys=True))
    return 1 if report["state"]=="REVIEW_OWNER_SHARE_ANOMALIES" else 0


if __name__=="__main__":
    raise SystemExit(main())
