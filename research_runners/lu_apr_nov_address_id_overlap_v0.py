#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare exact Apr/Nov 2026 ACT *address* ID namespaces, aggregate-only.

Read only two SHA-pinned official originals. No raw identifiers, address
records, geometry, pair mappings or crosswalk may be emitted or persisted.
Text overlap is a hypothesis, not independently established building identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile

from research_runners.lu_bd_adresses_original_csv_quality_v0 import (
    EXPECTED_SHA256 as NOV_SHA,
    EXPECTED_SIZE as NOV_SIZE,
    HEADER as NOV_HEADER,
    verify_original_stream,
)
from research_runners.lu_geobase_addresses_20260401_original_v0 import (
    EXPECTED_GPKG_SHA256 as APR_GPKG_SHA,
    EXPECTED_ZIP_SHA256 as APR_ZIP_SHA,
    inspect as inspect_apr_original,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import _safe

APR_ROWS = 179024
NOV_ROWS = 179768
MAX_ORIGINAL_GPKG_BYTES = 400 * 1024 * 1024
MAX_IDENTIFIER_LENGTH = 256


class CrossReleaseAddressError(ValueError):
    """Invalid original input or non-admissible identity claim."""


def _key(value: object, role: str) -> str | None:
    if value is None or value == "":
        return None
    if type(value) is int:
        value = str(value)
    if not isinstance(value, str) or len(value) > MAX_IDENTIFIER_LENGTH:
        raise CrossReleaseAddressError(f"{role}: unsupported identifier type/size")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise CrossReleaseAddressError(f"{role}: invalid control character")
    return value if value.strip() else None


def _counts(values: list[str | None]) -> tuple[Counter[str], dict]:
    counter = Counter(x for x in values if x is not None)
    return counter, {
        "rows": len(values),
        "blank_rows": len(values) - sum(counter.values()),
        "distinct_nonblank": len(counter),
        "duplicate_excess_rows": sum(v-1 for v in counter.values()),
        "max_rows_per_exact_id": max(counter.values(), default=0),
    }


def _overlap(left: Counter[str], right: Counter[str]) -> dict:
    both = left.keys() & right.keys()
    return {
        "distinct_exact_shared_strings": len(both),
        "left_rows_with_shared_string": sum(left[k] for k in both),
        "right_rows_with_shared_string": sum(right[k] for k in both),
        "shared_strings_singleton_both_sides": sum(left[k] == 1 and right[k] == 1 for k in both),
        "shared_strings_multirow_either_side": sum(left[k] > 1 or right[k] > 1 for k in both),
        "left_only_distinct_strings": len(left)-len(both),
        "right_only_distinct_strings": len(right)-len(both),
    }


def compare(april: list[tuple[object, object]],
            november: list[tuple[object, object]]) -> dict:
    """Pure synthetic-test core, emits no ID strings or matching pairs."""
    if not isinstance(april, list) or not isinstance(november, list):
        raise CrossReleaseAddressError("original address populations must be lists")
    if not 1 <= len(april) <= 300000 or not 1 <= len(november) <= 300000:
        raise CrossReleaseAddressError("original address population budget exceeded")
    parsed = []
    for name, records in (("april", april), ("november", november)):
        a, b = [], []
        for row in records:
            if not isinstance(row, (list, tuple)) or len(row) != 2:
                raise CrossReleaseAddressError("invalid address ID pair width")
            a.append(_key(row[0], name))
            b.append(_key(row[1], name))
        counter_a, stats_a = _counts(a)
        counter_b, stats_b = _counts(b)
        pair_counter = Counter((x,y) for x,y in zip(a,b) if x is not None and y is not None)
        parsed.append((counter_a,counter_b,pair_counter,stats_a,stats_b))
    apr_a,apr_alt,apr_pairs,apr_a_stat,apr_alt_stat = parsed[0]
    nov_geo,nov_caclr,nov_pairs,nov_geo_stat,nov_caclr_stat = parsed[1]
    pair_both = apr_pairs.keys() & nov_pairs.keys()
    return {
        "source_populations": {"april_geo_base_address_rows": len(april),
                               "november_bd_adresses_rows": len(november)},
        "april_ad_addressid": apr_a_stat,
        "april_alternativeidentifier": apr_alt_stat,
        "november_id_geoportail": nov_geo_stat,
        "november_id_caclr_bat": nov_caclr_stat,
        "exact_string_id_evidence": {
            "april_AD_AddressID_vs_november_id_geoportail": _overlap(apr_a,nov_geo),
            "april_AlternativeIdentifier_vs_november_id_caclr_bat": _overlap(apr_alt,nov_caclr),
        },
        "exact_pair_evidence": {
            "april_complete_pairs": sum(apr_pairs.values()),
            "november_complete_pairs": sum(nov_pairs.values()),
            "distinct_exact_ordered_pairs_shared": len(pair_both),
            "april_rows_with_shared_ordered_pair": sum(apr_pairs[k] for k in pair_both),
            "november_rows_with_shared_ordered_pair": sum(nov_pairs[k] for k in pair_both),
            "shared_pairs_singleton_both_sides": sum(apr_pairs[k] == 1 and nov_pairs[k] == 1
                                                       for k in pair_both),
            "shared_pairs_multirow_either_side": sum(apr_pairs[k] > 1 or nov_pairs[k] > 1
                                                       for k in pair_both),
        },
        "same_source_organization_not_independent": True,
        "cross_vintage_unchanged_identity_proven": False,
        "literal_match_proves_same_real_address": False,
        "address_to_geobase_building_crosswalk_proven": False,
        "insurer_exposure_or_tiv_proven": False,
        "commercial_rights_review_approved": False,
        "scientific_cat_model_admitted": False,
        "row_level_ids_addresses_or_join_pairs_exported": False,
    }


def _november_pairs(path: Path) -> list[tuple[str,str]]:
    rows = []
    with path.open("r",encoding="utf-8-sig",newline="") as inp:
        reader=csv.reader(inp,delimiter=";",strict=True)
        if tuple(next(reader, ())) != NOV_HEADER:
            raise CrossReleaseAddressError("original Nov source CSV header drift")
        for row in reader:
            if len(row) != len(NOV_HEADER):
                raise CrossReleaseAddressError("original Nov CSV row width drift")
            rows.append((row[10],row[5]))
            if len(rows) > NOV_ROWS:
                raise CrossReleaseAddressError("original Nov address row budget exceeded")
    if len(rows) != NOV_ROWS:
        raise CrossReleaseAddressError("original Nov address population drift")
    return rows


def _april_pairs(path: Path, work: Path) -> list[tuple[object,object]]:
    preflight = inspect_apr_original(path)
    if (preflight["observed_original_zip_sha256"] != APR_ZIP_SHA
            or preflight["observed_original_gpkg_sha256"] != APR_GPKG_SHA):
        raise CrossReleaseAddressError("original Apr source digests drift")
    out = work / "april-original.gpkg"
    with zipfile.ZipFile(path) as arc:
        members = [x for x in arc.infolist()
                   if x.filename.lower().endswith(".gpkg") and not x.is_dir()]
        if len(members) != 1:
            raise CrossReleaseAddressError("original Apr GPKG archive shape drift")
        member=members[0]
        _safe(member)
        if not 0 < member.file_size <= MAX_ORIGINAL_GPKG_BYTES:
            raise CrossReleaseAddressError("original Apr GPKG size budget exceeded")
        total=0
        h=hashlib.sha256()
        with arc.open(member) as inp, out.open("xb") as dst:
            while chunk := inp.read(1024*1024):
                total += len(chunk)
                if total > member.file_size or total > MAX_ORIGINAL_GPKG_BYTES:
                    raise CrossReleaseAddressError("original Apr GPKG decompression budget exceeded")
                dst.write(chunk)
                h.update(chunk)
        if total != member.file_size or h.hexdigest() != APR_GPKG_SHA:
            raise CrossReleaseAddressError("original Apr GPKG SHA-256 verification failed")
    with closing(sqlite3.connect(out.resolve().as_uri()+"?mode=ro&immutable=1",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA application_id").fetchone()[0] not in (
            0x47504B47,0x47503130,0x47503131):
            raise CrossReleaseAddressError("original Apr file not GPKG")
        original = db.execute(
            "SELECT c.srs_id, g.geometry_type_name FROM gpkg_contents c "
            "JOIN gpkg_geometry_columns g ON g.table_name=c.table_name "
            "WHERE c.table_name='AD_Address' AND c.data_type='features'"
        ).fetchone()
        if not original or original[0]!=2169 or str(original[1]).upper()!="MULTIPOINT":
            raise CrossReleaseAddressError("original Apr address layer/CRS drift")
        names={r[1] for r in db.execute('PRAGMA table_info("AD_Address")')}
        if not {"AD_AddressID","AlternativeIdentifier"}.issubset(names):
            raise CrossReleaseAddressError("original Apr address ID columns missing")
        actual = db.execute('SELECT COUNT(*) FROM "AD_Address"').fetchone()[0]
        if actual!=APR_ROWS:
            raise CrossReleaseAddressError("original Apr address count drift")
        pairs = list(db.execute('SELECT "AD_AddressID","AlternativeIdentifier" FROM "AD_Address"'))
        if len(pairs)!=APR_ROWS:
            raise CrossReleaseAddressError("original Apr ID row count drift")
    return pairs


def inspect(april_zip: Path, november_csv: Path) -> dict:
    if any(p.is_symlink() or not p.is_file() for p in (april_zip,november_csv)):
        raise CrossReleaseAddressError("original inputs must be local regular files")
    if november_csv.stat().st_size != NOV_SIZE:
        raise CrossReleaseAddressError("original November source byte count drift")
    with november_csv.open("rb") as inp:
        receipt=verify_original_stream(inp)
    if receipt["original_sha256_computed"]!=NOV_SHA or receipt["row_count"]!=NOV_ROWS:
        raise CrossReleaseAddressError("original November source SHA/row drift")
    with tempfile.TemporaryDirectory(prefix="lu-address-namespace-") as d:
        april=_april_pairs(april_zip,Path(d))
        november=_november_pairs(november_csv)
        result=compare(april,november)
    if result["source_populations"]!={"april_geo_base_address_rows":APR_ROWS,
                                      "november_bd_adresses_rows":NOV_ROWS}:
        raise CrossReleaseAddressError("original source population conservation failed")
    return {
        "profile":"lu-geo-base-april-vs-bd-adresses-nov-original-id-qa-v0",
        "original_april_zip_sha256":APR_ZIP_SHA,
        "original_april_gpkg_sha256":APR_GPKG_SHA,
        "original_november_csv_sha256":NOV_SHA,
        "source_vintages":{"geo_base_addresses":"2026-04-01","bd_adresses":"2026-11-02"},
        **result,
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geobase-addresses-zip",type=Path,required=True)
    parser.add_argument("--bd-adresses-csv",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=inspect(args.geobase_addresses_zip,args.bd_adresses_csv)
    except (OSError,ValueError,UnicodeError,csv.Error,sqlite3.DatabaseError,
            zipfile.BadZipFile,EOFError):
        print("BLOCKED: cross-release original ACT address ID evidence is invalid",
              file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
