#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned EIA-860 annual 2025 capacity + ownership status on 15 Delaware plants.

Research only. Preserve Operable / Proposed / Retired and source OP vs SB.
Nameplate MW is equipment rated generation capability, NOT a replacement value,
sum insured, commercial policy, location geometry, or insurable asset count.
No name/plant/generator/company/owner IDs exported to stdout or version control.
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
from zipfile import BadZipFile, ZipFile

try:
    from research_runners import eia860_annual_2025_original_zip_v0 as eia
    from research_runners import eia860_2025_generator_utility_schema_v0 as schema
    from research_runners import eia860_2025_generator_utility_owner_join_v0 as keyjoin
    from research_runners import eia860_2025_original_owner_schema_v0 as owner
except ModuleNotFoundError as exc:
    if exc.name != "research_runners":
        raise
    import eia860_annual_2025_original_zip_v0 as eia
    import eia860_2025_generator_utility_schema_v0 as schema
    import eia860_2025_generator_utility_owner_join_v0 as keyjoin
    import eia860_2025_original_owner_schema_v0 as owner

GEN_SHA = keyjoin.GEN_SHA
OWNER_SHA = keyjoin.OWNER_SHA
MAX_CAPACITY_MW = Decimal("50000")
MAX_SUM_MW = Decimal("1000000")
CAPACITY = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,8})?\Z")
SOURCE_CODES = frozenset(("S", "J", "W"))
# EIA ownership codes in the federal survey instructions: single ownership
# by respondent / jointly owned / wholly owned by another entity.
# Source equipment type is classified only from the exact prime mover code.
# Unknown/blank prime movers are *not* automatically categorized.
PRIME_FAMILY = {
    "PV":"solar_pv", "WT":"wind", "WS":"wind", "BA":"battery",
    "HY":"hydro", "PS":"pumped_storage", "GT":"gas_turbine",
    "CT":"combined_cycle_turbine", "CA":"combined_cycle_steam",
    "CS":"combined_cycle_shared_shaft", "CC":"combined_cycle_total_unit",
    "ST":"steam_turbine", "IC":"internal_combustion",
    "FC":"fuel_cell", "CE":"compressed_air", "ES":"other_storage",
    "CP":"concentrated_solar_storage", "FW":"flywheel",
    "OT":"other_prime_mover", "BT":"binary_cycle",
    "HA":"hydrokinetic", "HB":"hydrokinetic", "HK":"hydrokinetic",
}
FAMILY_KEYS = tuple(sorted(set(PRIME_FAMILY.values())))
KEYS = ("Plant Code", "Generator ID", "Status", "Utility ID",
        "Nameplate Capacity (MW)", "Prime Mover", "Energy Source 1",
        "Ownership")


class NativeCapacityBlocked(ValueError):
    """Pinned original source, units or keyed generator evidence unproven."""


def _frozen_mw(value: str) -> Decimal | None:
    """Parse only native Excel numeric MW (no unit conversion, no imputation)."""
    if not value:
        return None
    if not CAPACITY.fullmatch(value):
        return None
    try:
        v = Decimal(value)
    except InvalidOperation:
        return None
    if not v.is_finite() or v < 0 or v > MAX_CAPACITY_MW:
        return None
    return v


def _fmt_mw(x:Decimal)->str:
    return format(x.quantize(Decimal("0.001")), "f")


def inspect_original_members(generator_xlsx: bytes, owner_xlsx: bytes, *,
                             require_pinned: bool = True) -> dict:
    if type(require_pinned) is not bool:
        raise NativeCapacityBlocked("explicit provenance requirement must be boolean")
    if require_pinned and (
        sha256(generator_xlsx).hexdigest()!=GEN_SHA or
        sha256(owner_xlsx).hexdigest()!=OWNER_SHA
    ):
        raise NativeCapacityBlocked("original EIA 2025 generator/Owner member hash mismatch")
    try:
        schema.inspect_workbook(generator_xlsx,scope="generator")
        tabs,strings,wb,memory = schema._sheets(generator_xlsx)
    except (schema.GeneratorRosterBlocked, BadZipFile, OSError) as exc:
        raise NativeCapacityBlocked("invalid generator source workbook") from exc
    cohort = keyjoin.COHORT
    rows = Counter()
    seen = set()
    by_status = Counter()
    by_ownership = defaultdict(Counter)
    by_family = defaultdict(Counter)
    capacity_sums = defaultdict(lambda:Decimal(0))
    missing_capacity = Counter()
    zero_capacity = Counter()
    unknown_owner_code = Counter()
    unknown_prime_mover = Counter()
    bad_key = Counter()
    excluded_nonrecords = Counter()
    source_utilities = set()
    reporting_generator_owner_code = {}
    tab_of_key = {}
    try:
        for tab,path in tabs:
            for r in keyjoin._row_records(wb,path,strings,KEYS):
                plant, gen = r["Plant Code"],r["Generator ID"]
                if not keyjoin.PLANT.fullmatch(plant) or int(plant)==0:
                    if not gen:
                        excluded_nonrecords[tab]+=1
                    else:
                        bad_key[tab]+=1
                    continue
                plant = str(int(plant))
                if plant not in cohort:
                    continue
                if not keyjoin.GEN_ID.fullmatch(gen):
                    bad_key[tab]+=1
                    continue
                key = (plant,gen)
                if key in seen:
                    raise NativeCapacityBlocked("duplicate generator key in original source tabs")
                seen.add(key)
                tab_of_key[key] = tab
                rows[tab]+=1
                status=r["Status"]
                if status not in keyjoin.STATUS_CODES:
                    raise NativeCapacityBlocked("unknown in-cohort source generator status")
                by_status[status]+=1
                ownership=r["Ownership"]
                reporting_generator_owner_code[key]=ownership
                if ownership in SOURCE_CODES:
                    by_ownership[tab][ownership]+=1
                else:
                    unknown_owner_code[tab]+=1
                uid=r["Utility ID"]
                if uid and keyjoin.CODE.fullmatch(uid) and int(uid)>0:
                    source_utilities.add(str(int(uid)))
                prime=r["Prime Mover"]
                if prime in PRIME_FAMILY:
                    by_family[tab][PRIME_FAMILY[prime]]+=1
                else:
                    unknown_prime_mover[tab]+=1
                mw=_frozen_mw(r["Nameplate Capacity (MW)"])
                if mw is None:
                    missing_capacity[tab]+=1
                else:
                    if mw==0:
                        zero_capacity[tab]+=1
                    capacity_sums[tab]+=mw
                    if capacity_sums[tab]>MAX_SUM_MW:
                        raise NativeCapacityBlocked("implausible total in bounded source cohort")
    except (keyjoin.GeneratorOperatorJoinBlocked, eia.EIA860ProofBlocked) as exc:
        raise NativeCapacityBlocked("could not inspect approved source generator rows") from exc
    finally:
        wb.close()
        memory.close()
    # Owner exception schedule; key only. Do not use names or percentage cells in
    # this adapter; those shares were checked in PR #1299.
    try:
        tabs,ss,wb,memory = schema._sheets(owner_xlsx)
        owner_paths=[path for title,path in tabs if title=="Ownership"]
        if len(owner_paths)!=1:
            raise NativeCapacityBlocked("missing original Owner schedule")
        owner_keys = set()
        for r in keyjoin._row_records(wb,owner_paths[0],ss,("Plant Code","Generator ID")):
            plant,gen=r["Plant Code"],r["Generator ID"]
            if not keyjoin.PLANT.fullmatch(plant) or int(plant)==0:
                continue
            plant=str(int(plant))
            if plant not in cohort:
                continue
            if not keyjoin.GEN_ID.fullmatch(gen):
                raise NativeCapacityBlocked("invalid original in-cohort Owner generator key")
            owner_keys.add((plant,gen))
    except (keyjoin.GeneratorOperatorJoinBlocked, schema.GeneratorRosterBlocked,
            eia.EIA860ProofBlocked, BadZipFile, OSError) as exc:
        raise NativeCapacityBlocked("cannot inspect original Owner source rows") from exc
    finally:
        if "wb" in locals():
            wb.close()
            memory.close()
    owner_missing_roster = len(owner_keys-seen)
    owner_by_ownership = Counter(reporting_generator_owner_code[k]
                                 for k in owner_keys if k in reporting_generator_owner_code)
    exceptional_without_schedule = sum(
        code in ("J","W") and k not in owner_keys
        for k,code in reporting_generator_owner_code.items())
    single_with_schedule=sum(
        reporting_generator_owner_code.get(k)=="S" for k in owner_keys)
    capacity_rows = sum(rows.values())
    if capacity_rows!=len(seen) or len(cohort)!=15:
        raise NativeCapacityBlocked("15-plant cohort/source-key conservation failure")
    by_tab=("Operable","Proposed","Retired and Canceled")
    # 'Unknown' is a useful research quality state, not permission to impute.
    need_review = (owner_missing_roster or exceptional_without_schedule or
                   single_with_schedule or sum(bad_key.values()) or
                   sum(missing_capacity.values()) or
                   sum(unknown_owner_code.values()) or
                   sum(unknown_prime_mover.values()))
    return {
        "profile":"eia860-annual-2025-delaware-generator-nameplate-ownership-v0",
        "report_year":2025,
        "delaware_plant_id_cohort":len(cohort),
        "generator_original_member_sha256":sha256(generator_xlsx).hexdigest(),
        "owner_original_member_sha256":sha256(owner_xlsx).hexdigest(),
        "pinned_native_original_members_verified":require_pinned,
        "original_gen_keys":len(seen),
        "by_reporting_tab_rows":{t:rows[t] for t in by_tab},
        "source_generator_status_counts":dict(sorted(by_status.items())),
        "by_reporting_tab_nameplate_mw_not_tiv":{
            t:_fmt_mw(capacity_sums[t]) for t in by_tab},
        "by_reporting_tab_nameplate_missing_or_invalid":{
            t:missing_capacity[t] for t in by_tab},
        "by_reporting_tab_zero_nameplate_mw":{t:zero_capacity[t] for t in by_tab},
        "by_reporting_tab_ownership_code_S_J_W":{
            t:{v:by_ownership[t][v] for v in ("S","J","W")} for t in by_tab},
        "ownership_code_missing_or_unknown_by_tab":{
            t:unknown_owner_code[t] for t in by_tab},
        "by_reporting_tab_prime_mover_equipment_families":{
            t:{fam:by_family[t][fam] for fam in FAMILY_KEYS if by_family[t][fam]}
            for t in by_tab},
        "unmapped_prime_mover_by_tab":{t:unknown_prime_mover[t] for t in by_tab},
        "excluded_source_unkeyed_rows_by_tab":dict(excluded_nonrecords),
        "malformed_in_cohort_key_rows_by_tab":dict(bad_key),
        "distinct_reporting_utility_ids_in_cohort":len(source_utilities),
        "owner_schedule_generator_keys":len(owner_keys),
        "owner_schedule_keys_without_generator_record":owner_missing_roster,
        "owner_schedule_gen_keys_by_original_ownership_code":{
            k:owner_by_ownership[k] for k in ("S","J","W")},
        "original_generators_J_or_W_without_owner_schedule":exceptional_without_schedule,
        "original_generators_S_with_owner_schedule":single_with_schedule,
        "generator_capacity_is_replacement_cost_tiv":False,
        "generator_equals_one_insured_asset":False,
        "generator_id_proves_insurer_or_parent_entity":False,
        "source_2025_status_equals_2026_operational_status":False,
        "reported_ownership_code_is_ultimate_beneficial_owner":False,
        "gem_source_crosswalk_confirmed":False,
        "insurer_portfolio_or_treaty_admitted":False,
        "raw_generator_owner_ids_and_names_emitted":False,
        "state":"REVIEW_SOURCE_OWNERSHIP_CAPACITY" if need_review
                else "SOURCE_CAPACITY_OWNERSHIP_RESEARCH_ONLY",
    }


def inspect_pinned_original_zip(data:bytes) -> dict:
    try:
        eia.check_original_archive(data,expected_sha256=eia.PINNED_ORIGINAL_SHA256)
        with ZipFile(BytesIO(data)) as zipfile:
            eia._safe_zip(zipfile)
            g=eia._read_member(zipfile,schema.GENERATOR_MEMBER,schema.MAX_GENERATOR_XLSX)
            o=eia._read_member(zipfile,owner.OWNER_MEMBER,owner.MAX_OWNER_XLSX)
        result=inspect_original_members(g,o,require_pinned=True)
        result["official_full_original_zip_sha256"]=eia.PINNED_ORIGINAL_SHA256
        return result
    except (BadZipFile,OSError,RuntimeError,eia.EIA860ProofBlocked) as exc:
        raise NativeCapacityBlocked("official original annual ZIP is not pinned or parseable") from exc


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live",action="store_true")
    mode.add_argument("--original-zip",type=Path)
    a=p.parse_args(argv)
    try:
        if a.live:
            data=eia.fetch_exact_official_source()
        else:
            path=a.original_zip
            if path.is_symlink() or not path.is_file() or path.stat().st_size>eia.MAX_ORIGINAL_BYTES:
                raise NativeCapacityBlocked("expected original local EIA 2025 ZIP")
            data=path.read_bytes()
        report=inspect_pinned_original_zip(data)
        report["original_official_https_requested_in_this_run"]=a.live
    except (OSError,eia.EIA860ProofBlocked,NativeCapacityBlocked) as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc)}))
        return 2
    print(json.dumps(report,sort_keys=True))
    # A research exception is not a failed parser or false 2026 model admission.
    return 1 if report["state"].startswith("REVIEW") else 0


if __name__=="__main__":
    raise SystemExit(main())
