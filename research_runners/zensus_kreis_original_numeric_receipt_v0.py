# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-gated original Zensus 2022 county *building* values, not company sites.

This parser reads the previously SHA-pinned public official regional workbook,
and only its CSV-Gebäude sheet; it does not read GDV, insurer customer files,
individual building locations, or any 2025 R+V geographic exposures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from zensus_regional_original_receipt_v0 import (
    ORIGINAL_URL, OriginalReceiptError, download_original, inspect_original_package,
)
from zensus_regional_worksheet_schema_v0 import (
    _xlsx_target, _shared_strings, M,
)

ORIGINAL_SHA256 = "82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551"
HEADERS = ("Berichtszeitpunkt", "_RS", "Name", "Regionalebene",
           "GEBAEUDEART_SYS_1", "GEBAEUDEART_SYS_11",
           "GEBAEUDEART_SYS_111", "GEBAEUDEART_SYS_112",
           "GEBAEUDEART_SYS_12")
CODE = re.compile(r"(?:0[1-9]|1[0-6])[0-9]{3}\Z")
REF = re.compile(r"([A-Z]{1,3})[1-9][0-9]*\Z")
MAX_SHEET_BYTES = 500_000_000
MAX_ROWS = 35000
MAX_COLS = 9
MAX_COUNT = 10000000
MAX_KREISE = 450


def _column(ref: str) -> int:
    m = REF.fullmatch(ref)
    if not m:
        raise OriginalReceiptError("invalid original worksheet cell reference")
    x=0
    for ch in m.group(1):
        x=x*26+(ord(ch)-64)
    return x


def _cell_raw(cell: ET.Element) -> tuple[str,str]:
    t=cell.get("t", "")
    if t=="inlineStr":
        inline=cell.find(M+"is")
        return "inline", "".join(x.text or "" for x in inline.iter(M+"t")) if inline is not None else ""
    val=cell.find(M+"v")
    value=val.text if val is not None and val.text is not None else ""
    if t=="s":
        if not value.isdecimal() or int(value)>2000000:
            raise OriginalReceiptError("unbounded or invalid source shared string")
        return "shared", value
    if t in ("", "n", "str", "e"):
        return ("error" if t=="e" else "literal"), value
    raise OriginalReceiptError("unsupported original source cell type")


def _read_original_rows(archive: ZipFile, sheet: str) -> tuple[list[dict[str,tuple[str,str]]],set[int]]:
    if archive.getinfo(sheet).file_size>MAX_SHEET_BYTES:
        raise OriginalReceiptError("source worksheet too large")
    stored=[]
    wanted=set()
    seen=0
    try:
        with archive.open(sheet) as stream:
            for _,elem in ET.iterparse(stream,events=("end",)):
                if elem.tag!=M+"row":
                    continue
                seen+=1
                if seen>MAX_ROWS:
                    raise OriginalReceiptError("unexpected source regional worksheet row count")
                row={}
                for cell in elem.findall(M+"c"):
                    ix=_column(cell.get("r",""))
                    if ix>MAX_COLS:
                        continue
                    key=chr(64+ix)
                    if key in row:
                        raise OriginalReceiptError("duplicate original column in row")
                    raw=_cell_raw(cell)
                    row[key]=raw
                    if raw[0]=="shared":
                        wanted.add(int(raw[1]))
                stored.append(row)
                elem.clear()
    except (ET.ParseError, OSError, RuntimeError) as exc:
        raise OriginalReceiptError("original regional sheet XML could not be streamed") from exc
    if not 400<=len(stored)<=MAX_ROWS:
        raise OriginalReceiptError("original regional worksheet incomplete")
    return stored,wanted


def _value(v: tuple[str,str]|None, shared: dict[int,str]) -> str:
    if v is None:
        return ""
    kind,raw=v
    if kind=="shared":
        if int(raw) not in shared:
            raise OriginalReceiptError("unresolved source shared string")
        return shared[int(raw)].strip()
    if kind=="error":
        raise OriginalReceiptError("source Excel error in selected building cell")
    return raw.strip()


def inspect_original_kreis_building_counts(raw: bytes, *, require_original_sha=True) -> tuple[dict, list[dict]]:
    meta=inspect_original_package(raw)
    if require_original_sha and meta["original_file_sha256"]!=ORIGINAL_SHA256:
        raise OriginalReceiptError("original Zensus 2022 workbook SHA256 changed; refuse edition drift")
    with ZipFile(BytesIO(raw)) as archive:
        target=_xlsx_target(archive,"CSV-Gebäude")
        raw_rows,requested=_read_original_rows(archive,target)
        shared=_shared_strings(archive,requested)
    header=tuple(_value(raw_rows[0].get(chr(65+i)),shared) for i in range(len(HEADERS)))
    if header!=HEADERS:
        raise OriginalReceiptError("source column schema changed; no numeric admission")
    districts=[]
    already=set()
    levels=Counter()
    dates=Counter()
    skipped_bad=0
    for raw_row in raw_rows[1:]:
        code=_value(raw_row.get("B"),shared)
        region_type=_value(raw_row.get("D"),shared)
        # Non-Kreis administrative units coexist in this same worksheet.
        if not CODE.fullmatch(code):
            continue
        if "kreis" not in region_type.casefold():
            skipped_bad+=1
            continue
        if code in already:
            raise OriginalReceiptError("duplicated 2022 Landkreis identifier")
        already.add(code)
        date=_value(raw_row.get("A"),shared)
        name=_value(raw_row.get("C"),shared)
        if not name or len(name)>200:
            raise OriginalReceiptError("missing original Kreis name")
        levels[region_type]+=1
        dates[date]+=1
        nums=[]
        for col in ("E","F","G","H","I"):
            v=_value(raw_row.get(col),shared)
            if not re.fullmatch(r"(?:0|[1-9][0-9]*)",v):
                # Printed symbols and suppressed values cannot become zero.
                raise OriginalReceiptError("missing/suppressed/noninteger county building count: "+col+" for "+code)
            n=int(v)
            if n>MAX_COUNT:
                raise OriginalReceiptError("implausible county 2022 building count")
            nums.append(n)
        total,residential,non_dormitory,dormitory,other=nums
        if not (total>=residential>=non_dormitory and residential>=dormitory and total>=other):
            raise OriginalReceiptError("source building hierarchy impossible at Kreis "+code)
        districts.append({
            "kreis_ags_2022":code,
            "kreis_name_2022":name,
            "gebaeude_mit_wohnraum":total,
            "wohngebaeude":residential,
            "wohngebaeude_ohne_wohnheime":non_dormitory,
            "wohnheime":dormitory,
            "sonstiges_gebaeude_mit_wohnraum":other,
        })
        if len(districts)>MAX_KREISE:
            raise OriginalReceiptError("too many Kreis values; mixed geo hierarchy")
    if not 380<=len(districts)<=410 or len({r["kreis_ags_2022"][:2] for r in districts})!=16:
        raise OriginalReceiptError("missing Kreis rows or Länder; no partial geographic admission")
    if skipped_bad:
        raise OriginalReceiptError("five-digit Landkreis key has conflicting region type")
    districts.sort(key=lambda r:r["kreis_ags_2022"])
    valkeys=("gebaeude_mit_wohnraum","wohngebaeude","wohngebaeude_ohne_wohnheime","wohnheime","sonstiges_gebaeude_mit_wohnraum")
    sums={k:sum(d[k] for d in districts) for k in valkeys}
    hierarchy_nonadditivity = sum(abs(d["gebaeude_mit_wohnraum"] - d["wohngebaeude"] - d["sonstiges_gebaeude_mit_wohnraum"]) for d in districts)
    canonical=json.dumps(districts,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    receipt={
        "schema_version":"ZENSUS2022_ORIGINAL_KREIS_BUILDING_NUMERIC_RECEIPT_V0",
        "source_url":ORIGINAL_URL,
        "source_original_full_sha256":meta["original_file_sha256"],
        "original_edition_sha256_pinned": require_original_sha,
        "source_file_bytes":len(raw),
        "worksheet_exact_name":"CSV-Gebäude",
        "source_header_fields":list(header),
        "reporting_level_counts":dict(levels),
        "original_reported_dates":dict(dates),
        "kreis_count":len(districts),
        "land_codes_present":sorted({x["kreis_ags_2022"][:2] for x in districts}),
        "kreis_count_sum_by_field":sums,
        "kreis_numeric_mapping_sha256":hashlib.sha256(canonical).hexdigest(),
        "sum_count_nonadditivity_hierarchy_abs":hierarchy_nonadditivity,
        "original_geography_2022_05_15":True,
        "insurer_spatial_contracts_observed":False,
        "insurer_policy_to_building_1to1_proven":False,
        "real_tiv_or_claims_observed":False,
        "insurer_natural_peril_cover_observed":False,
        "oasis_model_input_admitted":False,
        "license":"German official census reuse attributed DL-DE-BY-2.0; verify final source-specific conditions",
        "warning":"Source Kreis buildings are physical opportunity by 2022 administrative units, NOT 2025 R+V insured assets. Source data not committed.",
    }
    return receipt,districts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--official-live",action="store_true",help="Download the exact official original once")
    group.add_argument("--original-xlsx",help="Locally supplied original publisher workbook")
    parser.add_argument("--emit-kreis-tsv",action="store_true",help="Print public Kreis aggregation rows for exact research reconciliation")
    args=parser.parse_args()
    raw=download_original() if args.official_live else open(args.original_xlsx,"rb").read()
    receipt,kreis=inspect_original_kreis_building_counts(raw)
    print(json.dumps(receipt,ensure_ascii=False,sort_keys=True))
    if args.emit_kreis_tsv:
        for r in kreis:
            print("ZENSUS2022_KREIS_RECORD\t"+r["kreis_ags_2022"]+"\t"+
                  str(r["gebaeude_mit_wohnraum"])+"\t"+str(r["wohngebaeude"])+"\t"+
                  str(r["wohngebaeude_ohne_wohnheime"])+"\t"+str(r["wohnheime"])+"\t"+
                  str(r["sonstiges_gebaeude_mit_wohnraum"]))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
