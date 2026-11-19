#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source EIA-860 annual 2025 generator/owner/utility key coverage audit.

For 15 independently cross-confirmed EPA↔EIA Delaware *plant codes* only.
Outputs aggregate counts, not generator IDs, company names, source rows, or
any inferred insured building, location, owner group or catastrophe loss.
"""
from __future__ import annotations

from collections import Counter, defaultdict
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
    from research_runners import eia860_2025_generator_utility_schema_v0 as schema
    from research_runners import eia860_2025_original_owner_schema_v0 as owner
    from research_runners import eia860_2025_owner_shares_cohort_v0 as shares
except ModuleNotFoundError as exc:
    if exc.name != "research_runners":
        raise
    import eia860_annual_2025_original_zip_v0 as eia
    import eia860_2025_generator_utility_schema_v0 as schema
    import eia860_2025_original_owner_schema_v0 as owner
    import eia860_2025_owner_shares_cohort_v0 as shares

GEN_SHA = "931e1ed0be2c6706794c196f158f779b5c8a32d08c61d748a823dfc25a3201a8"
UTIL_SHA = "aa82abf7ecab6d202d44952e7ada2586f8a053dead3956d3eaca756bc8232db9"
OWNER_SHA = shares.PINNED_OWNER_XLSX_SHA
COHORT = frozenset(eia.EPA_DE_CODES)
PLANT = re.compile(r"[0-9]{1,6}\Z")
GEN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.: -]{0,39}\Z")
CODE = re.compile(r"[0-9]{1,8}\Z")
MAX_SOURCE_ROWS = 120_000
MAX_WORKSHEET_BYTES = schema.MAX_XML_FILE
STATUS_CODES = frozenset(("CN","IP","L","OA","OP","OS","OT","P","RE","SB","T","TS","U","V"))


class GeneratorOperatorJoinBlocked(ValueError):
    """Source-native population, original-member identity or join not proven."""


def _row_records(zf: ZipFile, path: str, shared: list[str], required: tuple[str, ...]):
    """Yield only rows after a real exact header. No labels/rows ever logged."""
    try:
        info = zf.getinfo(path)
        if info.file_size > MAX_WORKSHEET_BYTES:
            raise GeneratorOperatorJoinBlocked("unbounded source worksheet XML")
        header = None
        row_n = 0
        with zf.open(info) as stream:
            for _, elem in ET.iterparse(stream, events=("end",)):
                if elem.tag != "{%s}row" % eia.NS:
                    continue
                row_n += 1
                if row_n > MAX_SOURCE_ROWS:
                    raise GeneratorOperatorJoinBlocked("unbounded source inventory rows")
                cells = {}
                for c in elem.findall("{%s}c" % eia.NS):
                    col = eia._col_number(c.get("r", ""))
                    if col in cells:
                        raise GeneratorOperatorJoinBlocked("source has duplicate XLSX column")
                    cells[col] = eia._cell_text(c, shared).strip()
                if header is None:
                    reverse = {value: col for col,value in cells.items() if value}
                    if all(x in reverse for x in required):
                        header = {k:reverse[k] for k in required}
                    elif row_n > schema.MAX_HEADER_ROWS:
                        raise GeneratorOperatorJoinBlocked("exact native reporting header not found")
                    elem.clear()
                    continue
                if any(cells.get(c) for c in header.values()):
                    yield {name:cells.get(index, "") for name,index in header.items()}
                elem.clear()
    except (BadZipFile, KeyError, OSError, RuntimeError, ET.ParseError,
            eia.EIA860ProofBlocked) as exc:
        raise GeneratorOperatorJoinBlocked("source native worksheet cannot be read") from exc
    if header is None:
        raise GeneratorOperatorJoinBlocked("source native header absent")


def _open_approved_workbook(raw:bytes, expected_sha:str, scope:str):
    if sha256(raw).hexdigest()!=expected_sha:
        raise GeneratorOperatorJoinBlocked("pinned original generator/utility/Owner SHA mismatch")
    # The native reader validates exact source tab list for generator scope.
    if scope in ("generator","utility"):
        schema.inspect_workbook(raw,scope=scope)
    try:
        sheets,ss,zf,buf=schema._sheets(raw)
    except schema.GeneratorRosterBlocked as exc:
        raise GeneratorOperatorJoinBlocked("original nested workbook invalid") from exc
    return sheets,ss,zf,buf


def inspect_members(gen_raw:bytes, util_raw:bytes, owner_raw:bytes, *,
                    require_pinned:bool=True) -> dict:
    if type(require_pinned) is not bool:
        raise GeneratorOperatorJoinBlocked("explicit original SHA enforcement boolean required")
    if require_pinned:
        for blob,digest in ((gen_raw,GEN_SHA),(util_raw,UTIL_SHA),(owner_raw,OWNER_SHA)):
            if sha256(blob).hexdigest()!=digest:
                raise GeneratorOperatorJoinBlocked("source workbook SHA not pinned")
    # Synthetic fixtures opt out of *identity pin*, never from structural gates.
    tab_counts=Counter()
    tab_statuses=defaultdict(Counter)
    memberships=defaultdict(set)
    operator_by_key=defaultdict(set)
    duplicated_in_tab=Counter()
    bad_key_rows=Counter()
    source_unkeyed_rows_without_generator=Counter()
    status_without_value=Counter()
    for sheets,shared,zf,buf in [_open_approved_workbook(
            gen_raw,GEN_SHA if require_pinned else sha256(gen_raw).hexdigest(),"generator")]:
        try:
            for tab,path in sheets:
                seen_this_tab=set()
                for r in _row_records(zf,path,shared,
                                      ("Plant Code","Generator ID","Status","Utility ID")):
                    plant,gen=r["Plant Code"],r["Generator ID"]
                    if not PLANT.fullmatch(plant) or int(plant)==0:
                        if not gen:
                            # Provider source footer/banner with no source
                            # plant or generator key is not a real generator;
                            # retain a count but never emit the text.
                            source_unkeyed_rows_without_generator[tab]+=1
                        else:
                            # A purported generator without an official
                            # numeric plant key needs human review.
                            bad_key_rows[tab]+=1
                        continue
                    p=str(int(plant))
                    if p not in COHORT:
                        continue
                    if not GEN_ID.fullmatch(gen):
                        bad_key_rows[tab]+=1
                        continue
                    key=(p,gen)
                    tab_counts[tab]+=1
                    if key in seen_this_tab:
                        duplicated_in_tab[tab]+=1
                    seen_this_tab.add(key)
                    memberships[key].add(tab)
                    status=r["Status"]
                    if status not in STATUS_CODES:
                        status_without_value[tab]+=1
                    else:
                        tab_statuses[tab][status]+=1
                    utility=r["Utility ID"]
                    if CODE.fullmatch(utility) and int(utility)>0:
                        operator_by_key[key].add(str(int(utility)))
        finally:
            zf.close()
            buf.close()
    utility_codes=set()
    utility_duplicates=0
    utility_empty_or_invalid=0
    sheets,shared,zf,buf=_open_approved_workbook(
        util_raw,UTIL_SHA if require_pinned else sha256(util_raw).hexdigest(),"utility")
    try:
        if len(sheets)!=1:
            raise GeneratorOperatorJoinBlocked("original utility reporting scope not singular")
        for r in _row_records(zf,sheets[0][1],shared,("Utility ID",)):
            uid=r["Utility ID"]
            if not CODE.fullmatch(uid) or int(uid)==0:
                utility_empty_or_invalid+=1
                continue
            norm=str(int(uid))
            if norm in utility_codes:
                utility_duplicates+=1
            utility_codes.add(norm)
    finally:
        zf.close()
        buf.close()
    owner_keys=set()
    owner_source_rows=0
    sheets,shared,zf,buf=_open_approved_workbook(
        owner_raw,OWNER_SHA if require_pinned else sha256(owner_raw).hexdigest(),"owner")
    try:
        matches=[path for name,path in sheets if name=="Ownership"]
        if len(matches)!=1:
            raise GeneratorOperatorJoinBlocked("original Owner exception schedule absent")
        for r in _row_records(zf,matches[0],shared,("Plant Code","Generator ID")):
            plant=r["Plant Code"]
            gen=r["Generator ID"]
            if not PLANT.fullmatch(plant) or int(plant)==0:
                continue
            p=str(int(plant))
            if p not in COHORT:
                continue
            if not GEN_ID.fullmatch(gen):
                raise GeneratorOperatorJoinBlocked("unresolved in-cohort original Owner generator key")
            owner_source_rows+=1
            owner_keys.add((p,gen))
    finally:
        zf.close()
        buf.close()
    if sum(tab_counts.values()) < len(memberships):
        raise GeneratorOperatorJoinBlocked("generator inventory conservation failure")
    utility_match=sum(any(uid in utility_codes for uid in operator_by_key[k])
                      for k in memberships)
    reporting_utilities_in_cohort=set()
    plant_utility_ids=defaultdict(set)
    for (plant, _gen), util_ids in operator_by_key.items():
        reporting_utilities_in_cohort.update(util_ids)
        plant_utility_ids[plant].update(util_ids)
    plants_with_multiple_reporting_utilities=sum(
        len(ids)>1 for ids in plant_utility_ids.values())
    operator_missing=sum(not operator_by_key[k] for k in memberships)
    operator_multiple=sum(len(operator_by_key[k])>1 for k in memberships)
    owner_with_roster=len(owner_keys & set(memberships))
    owner_without_roster=len(owner_keys - set(memberships))
    owner_by_tab={tab:sum(tab in memberships.get(k,set()) for k in owner_keys)
                  for tab in ("Operable","Proposed","Retired and Canceled")}
    tabs=("Operable","Proposed","Retired and Canceled")
    cross_tab=sum(len(m)>1 for m in memberships.values())
    state=("REVIEW_KEY_OR_SOURCE_STATUS" if owner_without_roster or cross_tab
           or operator_multiple or sum(duplicated_in_tab.values())
           or sum(bad_key_rows.values()) or sum(status_without_value.values()) else
           "GENERATOR_OPERATOR_KEYS_RESEARCH_ONLY")
    return {
        "profile":"eia860-2025-delaware-generator-utility-owner-key-coverage-v0",
        "reporting_year":2025,
        "epa_eia_delaware_source_proven_plant_code_count":len(COHORT),
        "generator_member_sha256":sha256(gen_raw).hexdigest(),
        "utility_member_sha256":sha256(util_raw).hexdigest(),
        "owner_member_sha256":sha256(owner_raw).hexdigest(),
        "original_member_hashes_verified":require_pinned,
        "in_cohort_generator_source_rows_by_sheet":{t:tab_counts[t] for t in tabs},
        "in_cohort_distinct_plant_generator_keys":len(memberships),
        "in_cohort_plant_ids_with_generator_rows":len({k[0] for k in memberships}),
        "in_cohort_generator_keys_in_multiple_sheets":cross_tab,
        "in_cohort_duplicate_keys_within_sheet":sum(duplicated_in_tab.values()),
        "source_rows_without_plant_and_generator_keys_by_sheet":dict(source_unkeyed_rows_without_generator),
        "original_source_rows_with_bad_plant_or_generator_key_by_sheet":dict(bad_key_rows),
        "source_generator_status_code_counts_by_sheet":{
            t:dict(sorted(tab_statuses[t].items())) for t in tabs},
        "source_generator_rows_with_missing_or_unknown_status_by_sheet":dict(status_without_value),
        "source_utility_distinct_ids_nationwide":len(utility_codes),
        "in_cohort_distinct_reporting_utility_ids":len(reporting_utilities_in_cohort),
        "in_cohort_plant_codes_with_multiple_reporting_utility_ids":plants_with_multiple_reporting_utilities,
        "source_utility_duplicate_id_rows":utility_duplicates,
        "source_utility_empty_or_invalid_id_rows":utility_empty_or_invalid,
        "generator_keys_with_at_least_one_source_utility_id":len(memberships)-operator_missing,
        "generator_keys_without_source_utility_id":operator_missing,
        "generator_keys_with_multiple_source_utility_ids":operator_multiple,
        "generator_keys_with_a_utility_id_in_original_utility_roster":utility_match,
        "owner_schedule_reported_rows_in_15_plants":owner_source_rows,
        "distinct_owner_schedule_generator_keys_in_15_plants":len(owner_keys),
        "owner_schedule_keys_present_in_original_generator_roster":owner_with_roster,
        "owner_schedule_keys_missing_from_generator_roster":owner_without_roster,
        "owner_schedule_generator_keys_by_original_tab":owner_by_tab,
        "generator_keys_without_schedule4_are_confirmed_operator_owned":False,
        "source_status_codes_equal_2026_operating_insurability":False,
        "utility_id_proves_ultimate_owner_or_insurer":False,
        "generator_nameplate_equals_insurable_tiv":False,
        "gem_project_identity_confirmed":False,
        "insured_portfolio_or_loss_model_admitted":False,
        "source_records_names_and_generator_ids_emitted":False,
        "state":state,
    }


def inspect_pinned_original_zip(original:bytes)->dict:
    try:
        eia.check_original_archive(original,expected_sha256=eia.PINNED_ORIGINAL_SHA256)
        with ZipFile(BytesIO(original)) as z:
            eia._safe_zip(z)
            g=eia._read_member(z,schema.GENERATOR_MEMBER,schema.MAX_GENERATOR_XLSX)
            u=eia._read_member(z,schema.UTILITY_MEMBER,schema.MAX_UTILITY_XLSX)
            o=eia._read_member(z,owner.OWNER_MEMBER,owner.MAX_OWNER_XLSX)
        report=inspect_members(g,u,o,require_pinned=True)
    except (BadZipFile,OSError,RuntimeError,eia.EIA860ProofBlocked) as exc:
        raise GeneratorOperatorJoinBlocked("original publisher 2025 ZIP pin rejected") from exc
    report["source_original_zip_sha256"]=eia.PINNED_ORIGINAL_SHA256
    return report


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    method=parser.add_mutually_exclusive_group(required=True)
    method.add_argument("--live",action="store_true")
    method.add_argument("--original-zip",type=Path)
    args=parser.parse_args(argv)
    try:
        if args.live:
            raw=eia.fetch_exact_official_source()
        else:
            p=args.original_zip
            if p.is_symlink() or not p.is_file() or p.stat().st_size>eia.MAX_ORIGINAL_BYTES:
                raise GeneratorOperatorJoinBlocked("original local EIA ZIP missing/oversized")
            raw=p.read_bytes()
        result=inspect_pinned_original_zip(raw)
        result["direct_pinned_publisher_download_in_this_run"]=args.live
    except (GeneratorOperatorJoinBlocked,OSError,eia.EIA860ProofBlocked) as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc)}))
        return 2
    print(json.dumps(result,sort_keys=True))
    return 1 if result["state"]=="REVIEW_KEY_OR_SOURCE_STATUS" else 0


if __name__=="__main__":
    raise SystemExit(main())
