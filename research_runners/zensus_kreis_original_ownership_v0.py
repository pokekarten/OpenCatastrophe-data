# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read 2022 original Kreis building ownership T:AA, not actual insurer owner mix.

Original Destatis workbook edition and 400 original Kreis total building
counts must match exactly. Null/suppressed ownership categories remain null.
Building ownership is NOT policyholder status or owner-occupied tenancy.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
import re
from pathlib import Path
from zipfile import ZipFile

from zensus_regional_original_receipt_v0 import OriginalReceiptError,download_original,inspect_original_package
from zensus_regional_worksheet_schema_v0 import _xlsx_target,_shared_strings
from zensus_kreis_original_numeric_receipt_v0 import (
    _read_original_rows,_value,CODE,ORIGINAL_SHA256
)
from zensus_kreis_original_age_cohorts_v0 import BASELINE,FIRST,read_pinned_baseline

OWNER_CODES=tuple(f"EIGENTUM__{i}" for i in range(1,9))
# These are SOURCE COLUMN CODES, not validated semantic names. The original
# aggregate code order is not the order of the questionnaire; e.g. code 2
# carries ~16.94m buildings and matches the national private-person category,
# while code 1 carries ~1.77m and matches WEG. Group comparisons are NOT
# sufficient to certify all eight individual code labels.
OWNER_LABELS=tuple(f"Publisher ownership column EIGENTUM__{i}; exact name unverified" for i in range(1,9))
SOURCE_DEFINITION="https://ergebnisse.zensus2022.de/datenbank/online/variables"
MAX_OWNER_CELL=10_000_000


def extract_original_kreis_ownership(raw: bytes, baseline: dict[str,int],
                                     *, require_original_sha: bool=True) -> tuple[dict,list[dict]]:
    meta=inspect_original_package(raw)
    if require_original_sha and meta["original_file_sha256"]!=ORIGINAL_SHA256:
        raise OriginalReceiptError("original Zensus official source edition SHA mismatch")
    if require_original_sha and (len(baseline)!=400 or sum(baseline.values())!=19957288):
        raise OriginalReceiptError("official 400-Kreis original building baseline invalid")
    with ZipFile(BytesIO(raw)) as z:
        target=_xlsx_target(z,"CSV-Gebäude")
        raw_rows,indices=_read_original_rows(z,target,max_columns=27)
        strings=_shared_strings(z,indices)
    expected=FIRST+tuple(f"BAUJAHR_10JA__{i:02}" for i in range(1,11))+OWNER_CODES
    source_columns=[chr(65+i) for i in range(26)]+["AA"]
    actual=tuple(_value(raw_rows[0].get(col),strings) for col in source_columns)
    if actual!=expected:
        raise OriginalReceiptError("original 2022 ownership sheet header/column order mismatched")
    out={}
    source_dates=Counter()
    incomplete=Counter()
    nonadditive=[]
    for r in raw_rows[1:]:
        ags=_value(r.get("B"),strings)
        if not CODE.fullmatch(ags):continue
        if _value(r.get("D"),strings)!="Stadtkreis/kreisfreie Stadt/Landkreis":
            raise OriginalReceiptError("unexpected 5-digit Kreis administrative level")
        if ags in out or ags not in baseline:
            raise OriginalReceiptError("duplicate/unknown original Kreis code for ownership")
        dt=_value(r.get("A"),strings)
        if dt!="20220515":
            raise OriginalReceiptError("original ownership census-date mismatch")
        source_dates[dt]+=1
        num=_value(r.get("E"),strings)
        if not re.fullmatch(r"(0|[1-9][0-9]*)",num) or int(num)!=baseline[ags]:
            raise OriginalReceiptError("original ownership Kreis total not same as published original buildings")
        owners=[]
        for i in range(8):
            col=chr(84+i) if i<7 else "AA"
            v=_value(r.get(col),strings)
            if not re.fullmatch(r"(0|[1-9][0-9]*)",v):
                owners.append(None)
                incomplete[OWNER_CODES[i]]+=1
                continue
            n=int(v)
            if n>MAX_OWNER_CELL or n>baseline[ags]+10:
                raise OriginalReceiptError("published 2022 ownership count exceeds valid total outside Cell-Key tolerance")
            owners.append(n)
        delta=sum(owners)-baseline[ags] if all(x is not None for x in owners) else None
        if delta is not None:nonadditive.append(delta)
        out[ags]={
            "ags":ags,
            "buildings_with_residential_use_2022":baseline[ags],
            "ownership_categories_2022":owners,
            "ownership_fully_numeric":delta is not None,
            "original_owner_category_sum_minus_total":delta,
        }
    if len(out)!=400 or set(out)!=set(baseline) or len(source_dates)!=1:
        raise OriginalReceiptError("missing 400 original Kreis ownership rows")
    ordered=[out[k] for k in sorted(out)]
    sums=[sum(x["ownership_categories_2022"][i] for x in ordered
              if x["ownership_categories_2022"][i] is not None) for i in range(8)]
    cov=[sum(x["ownership_categories_2022"][i] is not None for x in ordered)
         for i in range(8)]
    canonical=json.dumps(ordered,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    receipt={
        "schema_version":"ZENSUS2022_ORIGINAL_400_KREIS_BUILDING_OWNERSHIP_V0",
        "official_original_sha256":meta["original_file_sha256"],
        "original_source_sha_pinned":require_original_sha,
        "original_source_sheet":"CSV-Gebäude",
        "source_ownership_codes":list(OWNER_CODES),
        "source_ownership_labels":list(OWNER_LABELS),
        "official_category_definitions_url":SOURCE_DEFINITION,
        "county_count":len(ordered),
        "source_date":"20220515",
        "available_owner_category_2022_counts":dict(zip(OWNER_CODES,sums)),
        "numeric_counties_per_ownership_category":dict(zip(OWNER_CODES,cov)),
        "unavailable_counties_per_category":dict(incomplete),
        "complete_counties_all_8_ownership_categories":len(nonadditive),
        "max_abs_county_ownership_sum_minus_total":max(map(abs,nonadditive),default=None),
        "signed_county_ownership_sum_minus_total":sum(nonadditive),
        "source_values_canonical_sha256":hashlib.sha256(canonical).hexdigest(),
        "buildings_with_residential_use_2022_count":sum(baseline.values()),
        "rva_2025_company_ownership_distribution_observed":False,
        "census_building_owner_equals_insurer_policyholder":False,
        "eight_exact_owner_column_labels_source_verified":False,
        "source_group_to_code_mapping_requires_independent_table_check":True,
        "owner_type_equals_self_occupied_household":False,
        "insurer_2025_covered_properties_or_tiv_observed":False,
        "geographic_loss_model_admitted":False,
    }
    return receipt,ordered


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--official-live",action="store_true")
    g.add_argument("--original-xlsx",type=Path)
    p.add_argument("--baseline",type=Path,default=BASELINE)
    p.add_argument("--emit-ownership-tsv",action="store_true")
    a=p.parse_args()
    original=download_original() if a.official_live else a.original_xlsx.read_bytes()
    stock=read_pinned_baseline(a.baseline.read_bytes())
    audit,rows=extract_original_kreis_ownership(original,stock)
    print("ZENSUS_OWNERSHIP_RECEIPT\t"+json.dumps(audit,ensure_ascii=False,sort_keys=True))
    if a.emit_ownership_tsv:
        for r in rows:
            print("ZENSUS_OWNERSHIP_KREIS_RECORD\t"+r["ags"]+"\t"+
                  "\t".join("None" if v is None else str(v) for v in r["ownership_categories_2022"]))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
