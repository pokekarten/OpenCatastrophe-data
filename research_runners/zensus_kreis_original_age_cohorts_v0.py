# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Destatis Zensus 2022 400-Kreis building age cohorts, source-gated.

Age band counts are *published physical buildings with residential use*, NOT
2025 R+V insured positions, policy age, roof type, restoration, TIV or losses.
Official Cell-Key disclosure control may make totals nonadditive.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import tomllib
from zipfile import ZipFile

from zensus_regional_original_receipt_v0 import OriginalReceiptError, inspect_original_package, download_original
from zensus_regional_worksheet_schema_v0 import _xlsx_target, _shared_strings
from zensus_kreis_original_numeric_receipt_v0 import (
    _read_original_rows, _value, CODE, ORIGINAL_SHA256,
)

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
FIRST=("Berichtszeitpunkt","_RS","Name","Regionalebene","GEBAEUDEART_SYS_1",
       "GEBAEUDEART_SYS_11","GEBAEUDEART_SYS_111",
       "GEBAEUDEART_SYS_112","GEBAEUDEART_SYS_12")
CODES=tuple(f"BAUJAHR_10JA__{i:02d}" for i in range(1,11))
# Grounded at official Zensus 2022 table 3000G-1002, not simply inferred from suffix.
BANDS=("Vor 1919","1919 - 1949","1950 - 1959","1960 - 1969",
       "1970 - 1979","1980 - 1989","1990 - 1999","2000 - 2009",
       "2010 - 2015","2016 und später")
OFFICIAL_CATEGORY_PAGE="https://ergebnisse.zensus2022.de/datenbank/online/statistic/3000G/table/3000G-1002"
MAX_AGE_FIELD=10000000
CENSUS_DATE="20220515"


def read_pinned_baseline(raw: bytes) -> dict[str,int]:
    c=tomllib.loads(raw.decode("utf-8"))
    if (c.get("schema_version")!="ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGGREGATES_V0"
        or c.get("original_full_file_sha256")!=ORIGINAL_SHA256
        or c.get("region_rows")!=400
        or c.get("original_printed_kreis_total_buildings_with_residential_use")!=19957288):
        raise OriginalReceiptError("original county buildings baseline metadata changed")
    items=c.get("kreise",[])
    if len(items)!=400:
        raise OriginalReceiptError("400 county baseline rows not present")
    mapped={}
    for r in items:
        code,buildings=r["ags"],r["geb_mit_wohnraum"]
        if not CODE.fullmatch(code) or code in mapped or type(buildings) is not int or buildings<1:
            raise OriginalReceiptError("original county baseline code/count invalid")
        mapped[code]=buildings
    if len(mapped)!=400 or sum(mapped.values())!=19957288:
        raise OriginalReceiptError("original county baseline national total is not pinned")
    return mapped


def inspect_original_age_cohorts(raw: bytes, baseline: dict[str,int], *, require_original_sha: bool=True) -> tuple[dict,list[dict]]:
    meta=inspect_original_package(raw)
    if require_original_sha and meta["original_file_sha256"]!=ORIGINAL_SHA256:
        raise OriginalReceiptError("original Destatis age XLSX edition changed")
    if len(baseline)!=400 or sum(baseline.values())!=19957288:
        # synthetic tests pass a fully hypothetical 400-row baseline with
        # require_original_sha=False; avoid an accidental real-admission claim.
        if require_original_sha:
            raise OriginalReceiptError("actual published county baseline mismatched")
    with ZipFile(BytesIO(raw)) as z:
        sheet=_xlsx_target(z,"CSV-Gebäude")
        raw_rows,keys=_read_original_rows(z,sheet,max_columns=19)
        strings=_shared_strings(z,keys)
    headers=tuple(_value(raw_rows[0].get(chr(65+i)),strings) for i in range(19))
    if headers!=FIRST+CODES:
        raise OriginalReceiptError("original Zensus age bands/source columns changed")
    result={}
    missing=Counter()
    dates=Counter()
    diffs=[]
    for r in raw_rows[1:]:
        ags=_value(r.get("B"),strings)
        if not CODE.fullmatch(ags):
            continue
        level=_value(r.get("D"),strings)
        if level!="Stadtkreis/kreisfreie Stadt/Landkreis":
            raise OriginalReceiptError("five-digit AGS has unexpected administrative level")
        if ags in result or ags not in baseline:
            raise OriginalReceiptError("duplicate or unfamiliar 2022 Kreis for age")
        date=_value(r.get("A"),strings)
        if date!=CENSUS_DATE:
            raise OriginalReceiptError("original age measurement date is not 20220515")
        dates[date]+=1
        n=_value(r.get("E"),strings)
        if not re.fullmatch(r"(0|[1-9][0-9]*)",n) or int(n)!=baseline[ags]:
            raise OriginalReceiptError("age row physical building total not equal original exact Kreis baseline "+ags)
        bands=[]
        for i,code in enumerate(CODES):
            col=chr(74+i)
            value=_value(r.get(col),strings)
            if not re.fullmatch(r"(0|[1-9][0-9]*)",value):
                # Official missing / suppressed / not released original cell.
                bands.append(None)
                missing[code]+=1
                continue
            x=int(value)
            if x>MAX_AGE_FIELD or x>baseline[ags]+10:
                raise OriginalReceiptError("source age-band cell outside physical count/Cell-Key bound for "+ags)
            bands.append(x)
        delta=sum(x for x in bands if x is not None)-baseline[ags] if all(x is not None for x in bands) else None
        if delta is not None:
            diffs.append(delta)
        result[ags]={"ags":ags,"buildings_2022":baseline[ags],"age_bands_2022":bands,
                     "all_age_bands_numeric":all(x is not None for x in bands),
                     "complete_age_band_sum_minus_buildings":delta}
    if set(result)!=set(baseline) or len(result)!=400 or len(dates)!=1:
        raise OriginalReceiptError("county age rows incomplete/duplicate/not at original vintage")
    rows=[result[k] for k in sorted(result)]
    canonical=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    total_by_band=[sum(r["age_bands_2022"][i] for r in rows if r["age_bands_2022"][i] is not None)
                   for i in range(len(CODES))]
    observed_by_band=[sum(r["age_bands_2022"][i] is not None for r in rows)
                      for i in range(len(CODES))]
    receipt={
      "schema_version":"ZENSUS2022_400_KREIS_ORIGINAL_AGE_BANDS_RECEIPT_V0",
      "publisher":"Statistisches Bundesamt (Destatis) / Statistische Ämter des Bundes und der Länder",
      "original_workbook_sha256":meta["original_file_sha256"],
      "original_workbook_edition_pinned":require_original_sha,
      "worksheet":"CSV-Gebäude",
      "source_age_columns":list(CODES),
      "age_band_labels_official_order":list(BANDS),
      "age_band_source_definitions":OFFICIAL_CATEGORY_PAGE,
      "county_count":len(rows),"building_total_original":sum(baseline.values()),
      "age_numeric_coverage_by_column":dict(zip(CODES,observed_by_band)),
      "age_numeric_sum_available_only_by_column":dict(zip(CODES,total_by_band)),
      "age_unavailable_count_by_column":dict(missing),
      "counties_all_ten_age_bands_numeric":len(diffs),
      "complete_county_max_abs_age_sum_minus_total":max(map(abs,diffs),default=None),
      "complete_county_age_sum_delta_total":sum(diffs),
      "source_400_county_age_canonical_sha256":hashlib.sha256(canonical).hexdigest(),
      "original_date_verified":"20220515",
      "source_physical_age_bands_are_insurer_2025_policy_age":False,
      "source_physical_age_bands_are_roof_condition_or_wind_fragility":False,
      "insurer_risk_locations_or_values_observed":False,
      "rva_2025_age_book_admitted":False,
      "licensed_reuse_pending_final_source_specific_review":True,
      "notes":"Official rounded/CKM published regional columns may not be additive. Missing categories remain null. No 2025 insurer geographic exposure inferred."
    }
    return receipt,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    x=p.add_mutually_exclusive_group(required=True)
    x.add_argument("--official-live",action="store_true")
    x.add_argument("--original-xlsx",type=Path)
    p.add_argument("--baseline",type=Path,default=BASELINE)
    p.add_argument("--emit-age-tsv",action="store_true",
                   help="Print original public county aggregates, no building addresses")
    args=p.parse_args()
    raw=download_original() if args.official_live else args.original_xlsx.read_bytes()
    baseline=read_pinned_baseline(args.baseline.read_bytes())
    receipt,rows=inspect_original_age_cohorts(raw,baseline)
    print("ZENSUS_ORIGINAL_AGE_RECEIPT\t"+json.dumps(receipt,sort_keys=True,ensure_ascii=False))
    if args.emit_age_tsv:
        for row in rows:
            print("ZENSUS_AGE_KREIS_RECORD\t"+row["ags"]+"\t"+
                  "\t".join("None" if x is None else str(x) for x in row["age_bands_2022"]))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
