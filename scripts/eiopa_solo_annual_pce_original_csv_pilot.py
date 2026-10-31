#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""EIOPA solo annual S.05.01 source-byte pilot: exact CSV profile, CAT-only staging.

This stages original *aggregated* annual country statistics in an isolated
research SQLite database only. The public file is NOT admitted as commercial
CAT-model input, no units are guessed, and no provider rows are put in Git.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.request import Request, urlopen

try:
    from .export_cat_source_registry_sqlite import CAT_APP_ID, CAT_SCHEMA_VERSION
except ImportError:
    from export_cat_source_registry_sqlite import CAT_APP_ID, CAT_SCHEMA_VERSION

SOURCE_URL = "https://www.eiopa.europa.eu/assets/insurance-statistics/SA_Premiums_Claims_Expenses.csv"
SOURCE_PAGE = "https://www.eiopa.europa.eu/tools-and-data/insurance-statistics_en"
SOURCE_PROFILE = "eiopa-solo-annual-premiums-claims-expenses-research-v0"
MAX_BYTES = 30_000_000
MAX_ROWS = 240_000
HEADER = (
    "Reporting country", "Reference period", "Item", "Business type", "Item code",
    "Value", "Date of extraction (yyyymmdd)",
    "Number of submissions (per reporting country, reference date and undertaking type)",
)
NUMBER_RE = re.compile(r"-?(?:[0-9]+)(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]{1,3})?\Z", re.ASCII)
CODE_RE = re.compile(r"[A-Z][0-9]{4}\Z", re.ASCII)
PERIOD_RE = re.compile(r"Y20(?:1[6-9]|2[0-5])\Z", re.ASCII)


class EIOPACSVError(ValueError):
    """Reject unverified, ambiguous or corrupted market-statistic source rows."""


def _strict_rows(raw: bytes) -> tuple[list[tuple], dict]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise EIOPACSVError("missing or oversized original EIOPA CSV bytes")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise EIOPACSVError("source is not UTF-8") from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames is None or tuple(reader.fieldnames) != HEADER:
            raise EIOPACSVError("EIOPA S.05.01 CSV header/version changed")
        country_set, year_set, type_set, extraction_set = set(), set(), set(), set()
        nonlife_country_year = set()
        # Each selected source item has a *different* insurance accounting basis.
        # Count nonmissing observations; NEVER add or reclassify their values.
        selected_nonlife_codes = {
            "R0110": "direct_written_premium",
            "R0120": "proportional_reinsurance_accepted_written",
            "R0130": "nonproportional_reinsurance_accepted_written",
            "R0140": "reinsurers_share_written",
            "R0200": "net_written_premium",
            "R0310": "gross_direct_claims_incurred",
            "R0340": "reinsurers_share_claims_incurred",
            "R0400": "net_claims_incurred",
        }
        nonlife_present = {code: set() for code in selected_nonlife_codes}
        country_year_business = set()
        seen = set()
        rows = []
        counts = dict(numeric=0, missing=0, zero=0, negative=0)
        for n, row in enumerate(reader, start=1):
            if n > MAX_ROWS:
                raise EIOPACSVError("EIOPA row cap exceeded")
            if None in row or set(row) != set(HEADER) or any(v is None for v in row.values()):
                raise EIOPACSVError(f"invalid CSV column count at row {n}")
            country, period, item, business, code, value, extracted, submissions = (
                row[field].strip() for field in HEADER
            )
            if not (0 < len(country) <= 100 and 0 < len(item) <= 150
                    and 0 < len(business) <= 85 and not any("\n" in v or "\r" in v for v in row.values())):
                raise EIOPACSVError(f"invalid source text at row {n}")
            if not PERIOD_RE.fullmatch(period) or not CODE_RE.fullmatch(code):
                raise EIOPACSVError(f"unexpected period or EIOPA item code at row {n}")
            try:
                date.fromisoformat(f"{extracted[:4]}-{extracted[4:6]}-{extracted[6:8]}")
            except ValueError as exc:
                raise EIOPACSVError(f"invalid extraction date at row {n}") from exc
            if not re.fullmatch(r"20[0-9]{6}", extracted, re.ASCII):
                raise EIOPACSVError(f"unexpected extraction date at row {n}")
            if submissions and (not submissions.isascii() or not submissions.isdecimal()
                                or int(submissions) > 1_000_000):
                raise EIOPACSVError(f"invalid source submission count at row {n}")
            fact_key = (country, period, business, code)
            if fact_key in seen:
                raise EIOPACSVError(f"duplicate country/period/business/item-code at row {n}")
            seen.add(fact_key)
            is_missing = value == ""
            if is_missing:
                counts["missing"] += 1
                normalized = None
            else:
                if not NUMBER_RE.fullmatch(value):
                    raise EIOPACSVError(f"noncanonical numeric observation at row {n}")
                try:
                    d = Decimal(value)
                except InvalidOperation as exc:
                    raise EIOPACSVError(f"invalid numeric value at row {n}") from exc
                if not d.is_finite():
                    raise EIOPACSVError(f"nonfinite numeric value at row {n}")
                counts["numeric"] += 1
                counts["zero"] += (d == 0)
                counts["negative"] += (d < 0)
                normalized = value  # Decimal-as-text: no float rounding, NO unit inference.
            rows.append((n,country,period,item,business,code,normalized,extracted,
                         None if not submissions else int(submissions),int(is_missing)))
            country_set.add(country)
            year_set.add(period)
            type_set.add(business)
            country_year_business.add((country, period, business))
            if business == "Non-Life":
                nonlife_country_year.add((country, period))
                if code in nonlife_present and not is_missing:
                    nonlife_present[code].add((country, period))
            extraction_set.add(extracted)
    except csv.Error as exc:
        raise EIOPACSVError("malformed original EIOPA CSV syntax") from exc
    if not rows or not country_set or not year_set:
        raise EIOPACSVError("EIOPA CSV is empty or has no time/country observations")
    profile = {
        "profile": SOURCE_PROFILE, "source_url":SOURCE_URL,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_byte_count":len(raw), "source_row_count":len(rows),
        "country_count":len(country_set), "country_labels":sorted(country_set),
        "reference_periods":sorted(year_set),
        "business_types":sorted(type_set),
        "country_year_business_type_combinations":len(country_year_business),
        "nonlife_country_year_combinations":len(nonlife_country_year),
        "selected_nonlife_accounting_item_presence": {
            selected_nonlife_codes[code]:len(pairs)
            for code,pairs in sorted(nonlife_present.items())
        },
        "selected_nonlife_item_presence_rule":
            "count country-year observations with source value present, never sum measures",
        "extraction_dates":sorted(extraction_set), "value_state_counts":counts,
        "denominator":"country_year_business_type_item_code",
        "solo_annual_not_group_or_quarterly":True,
        "value_unit_verified":False, "value_unit":"NOT_VERIFIED_DO_NOT_CONVERT",
        "insured_cat_losses_created":False, "geocoded_risk_locations_created":False,
        "company_level_observations_created":False, "model_source_admitted":False,
        "data_rights_for_persistent_import_reviewed":False,
    }
    return rows, profile


def preflight(raw: bytes) -> dict:
    """Strictly inspect one source blob; return no provider rows or values."""
    return _strict_rows(raw)[1]


def stage_verified_csv(db_path: Path, raw: bytes) -> dict:
    """Atomic, versioned aggregation staging in a dedicated CAT-only DB."""
    rows, profile = _strict_rows(raw)  # Fail *before* opening target.
    output = Path(db_path).expanduser()
    if output.is_symlink() or not output.is_file():
        raise EIOPACSVError("an existing regular CAT-only research SQLite file is required")
    con = sqlite3.connect(output)
    try:
        if (con.execute("PRAGMA application_id").fetchone()[0] != CAT_APP_ID
                or con.execute("PRAGMA user_version").fetchone()[0] != CAT_SCHEMA_VERSION
                or not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='cat_source_candidate'").fetchone()):
            raise EIOPACSVError("refusing non-CAT database or missing registry seed")
        con.execute("""CREATE TABLE IF NOT EXISTS cat_eiopa_annual_market_stage (
          source_sha256 TEXT NOT NULL,
          source_row INTEGER NOT NULL,
          reporting_country_label TEXT NOT NULL,
          reference_period TEXT NOT NULL,
          source_item_label TEXT NOT NULL,
          source_business_type TEXT NOT NULL,
          source_item_code TEXT NOT NULL,
          source_decimal_text TEXT,
          extraction_date_yyyymmdd TEXT NOT NULL,
          number_of_submissions INTEGER,
          source_value_missing INTEGER NOT NULL CHECK(source_value_missing IN (0,1)),
          is_solo_annual INTEGER NOT NULL CHECK(is_solo_annual=1),
          unit_verified INTEGER NOT NULL CHECK(unit_verified=0),
          rights_reviewed INTEGER NOT NULL CHECK(rights_reviewed=0),
          model_admitted INTEGER NOT NULL CHECK(model_admitted=0),
          PRIMARY KEY (source_sha256,source_row),
          UNIQUE (source_sha256,reporting_country_label,reference_period,
                  source_business_type,source_item_code)
        )""")
        with con:
            con.executemany("""INSERT OR REPLACE INTO cat_eiopa_annual_market_stage VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(profile["source_sha256"],*row,1,0,0,0) for row in rows])
        observed = con.execute("""SELECT count(*) FROM cat_eiopa_annual_market_stage
               WHERE source_sha256=?""",(profile["source_sha256"],)).fetchone()[0]
        if observed != len(rows):
            raise EIOPACSVError("research-stage row-count mismatch")
    finally:
        con.close()
    return {**profile,"staged_into_isolated_cat_sqlite":True,
            "staged_observations":len(rows),"neon_modified":False,
            "third_party_rows_committed_to_git":False}


def fetch_source() -> bytes:
    req = Request(SOURCE_URL,headers={"User-Agent":"OpenCatastrophe-EIOPA-research-preflight/0.1",
                                       "Accept":"text/csv,text/plain"})
    with urlopen(req,timeout=60) as response:
        if response.status != 200 or response.geturl() != SOURCE_URL:
            raise EIOPACSVError("EIOPA source request redirected or unavailable")
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise EIOPACSVError("EIOPA source exceeds research byte cap")
    return raw


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch",action="store_true",help="fetch exact live EIOPA source CSV")
    mode.add_argument("--csv",type=Path,help="use offline original EIOPA CSV bytes")
    p.add_argument("--out",type=Path,help="existing CAT-only SQLite seed; omit for preflight only")
    p.add_argument("--result",type=Path,help="write metadata-only JSON result")
    a=p.parse_args(argv)
    try:
        raw=fetch_source() if a.fetch else a.csv.read_bytes()
        result=stage_verified_csv(a.out,raw) if a.out else preflight(raw)
        serial=json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False)
        if a.result:
            a.result.write_text(serial+"\n",encoding="utf-8")
        print(serial)
        return 0
    except (OSError,EIOPACSVError,sqlite3.DatabaseError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
