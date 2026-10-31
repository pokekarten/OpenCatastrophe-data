#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded GLEIF Level-2 relationship/exception pilot; NEVER infer ownership.

Checks original official JSON:API bytes and records source-versioned, historical
accounting-consolidation observations in a CAT-only SQLite research DB.
No Neon write, no inferred claims/portfolio, no copied provider response in Git.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.request import Request, urlopen

try:
    from .gleif_level1_insurer_identity_pilot import (
        API_BASE, CAT_APP_ID, CAT_SCHEMA_VERSION, GLEIFPilotError, valid_lei,
    )
except ImportError:
    from gleif_level1_insurer_identity_pilot import (
        API_BASE, CAT_APP_ID, CAT_SCHEMA_VERSION, GLEIFPilotError, valid_lei,
    )

MAX_BYTES = 500_000
# The exact relations and exceptions were observed in the 2026-10-30 FFBK
# source receipt (GLEIF CC0 API), not inferred from company-name similarity.
# If a live source has changed, fail rather than force a historical assertion.
PILOT = (
    ("5299006ZIILJ6VJVSJ32", "direct-parent-relationship", "529900F2F9VZ5FRROH89"),
    ("529900KIN5BE45V5KB18", "direct-parent-relationship", "5299006ZIILJ6VJVSJ32"),
    ("529900KIN5BE45V5KB18", "ultimate-parent-relationship", "529900F2F9VZ5FRROH89"),
    ("529900UCN37OZCXGVW88", "direct-parent-relationship", "529900KIN5BE45V5KB18"),
    ("529900UCN37OZCXGVW88", "ultimate-parent-relationship", "529900F2F9VZ5FRROH89"),
    ("549300KCPG3666EE4546", "direct-parent-reporting-exception", "NON_CONSOLIDATING"),
    ("529900MUF4C20K50JS49", "direct-parent-reporting-exception", "NO_KNOWN_PERSON"),
)
REQUIRED_TYPES = {
    "direct-parent-relationship": "IS_DIRECTLY_CONSOLIDATED_BY",
    "ultimate-parent-relationship": "IS_ULTIMATELY_CONSOLIDATED_BY",
}
EXCEPTION_CATEGORIES = {
    "direct-parent-reporting-exception": "DIRECT_ACCOUNTING_CONSOLIDATION_PARENT",
}
REASON_RE = re.compile(r"[A-Z_]{2,80}\Z", re.ASCII)


def source_url(lei: str, suffix: str) -> str:
    if not any((a,b)==(lei,suffix) for a,b,_ in PILOT) or not valid_lei(lei):
        raise GLEIFPilotError("unapproved exact GLEIF Level-2 pilot endpoint")
    return API_BASE + lei + "/" + suffix


def _unique_pairs(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise GLEIFPilotError("duplicate JSON key in GLEIF Level-2 response")
        data[key] = value
    return data


def _json(blob: bytes) -> dict:
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise GLEIFPilotError("invalid GLEIF source response size")
    try:
        value = json.loads(blob.decode("utf-8-sig"), object_pairs_hook=_unique_pairs,
            parse_constant=lambda x: (_ for _ in ()).throw(GLEIFPilotError("nonfinite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GLEIFPilotError("invalid GLEIF source JSON") from exc
    if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
        raise GLEIFPilotError("expected one JSON:API data record")
    return value["data"]


def _extract_node(node) -> str:
    # GLEIF RR-CDF uses the token "LEI" for node types. The JSON:API
    # representation can preserve that uppercase spelling.
    if not isinstance(node, dict) or node.get("type") not in (None, "lei", "LEI") or not valid_lei(node.get("id")):
        raise GLEIFPilotError("invalid child/parent LEI endpoint")
    return node["id"]


def parse_level2(blob: bytes, child: str, suffix: str, expected: str) -> dict:
    url = source_url(child, suffix)
    if (child,suffix,expected) not in PILOT:
        raise GLEIFPilotError("unapproved Level-2 relationship or exception")
    data = _json(blob)
    attrs = data.get("attributes")
    if not isinstance(attrs, dict):
        raise GLEIFPilotError("missing Level-2 attributes")
    actual_parent = None
    reason = None
    periods = []
    if suffix in REQUIRED_TYPES:
        relation = attrs.get("relationship")
        registration = attrs.get("registration")
        if not isinstance(relation, dict) or not isinstance(registration, dict):
            raise GLEIFPilotError("missing GLEIF relationship or registration")
        if (_extract_node(relation.get("startNode")) != child
            or _extract_node(relation.get("endNode")) != expected):
            raise GLEIFPilotError("GLEIF parent/child identity mismatch")
        if relation.get("type") != REQUIRED_TYPES[suffix]:
            raise GLEIFPilotError("unexpected GLEIF consolidation relationship class")
        if relation.get("status") != "ACTIVE" or registration.get("status") != "PUBLISHED":
            raise GLEIFPilotError("relationship not currently ACTIVE/PUBLISHED")
        periods = relation.get("periods", [])
        if not isinstance(periods, list) or len(periods) > 20:
            raise GLEIFPilotError("invalid relationship periods")
        for period in periods:
            if not isinstance(period, dict) or period.get("type") not in (
                "ACCOUNTING_PERIOD","RELATIONSHIP_PERIOD","DOCUMENT_FILING_PERIOD"):
                raise GLEIFPilotError("unrecognized period type")
            for date_key in ("startDate", "endDate"):
                raw = period.get(date_key)
                if raw is not None and (not isinstance(raw, str) or len(raw) > 40):
                    raise GLEIFPilotError("invalid source period date")
        actual_parent = expected
        kind = REQUIRED_TYPES[suffix]
    else:
        ex = attrs.get("exception")
        if not isinstance(ex, dict):
            raise GLEIFPilotError("missing exception detail")
        if ex.get("lei") != child or ex.get("category") != EXCEPTION_CATEGORIES[suffix]:
            raise GLEIFPilotError("GLEIF exception LEI/category mismatch")
        reason = ex.get("reason")
        if reason != expected or not REASON_RE.fullmatch(reason):
            raise GLEIFPilotError("GLEIF exception reason mismatch")
        kind = "PARENT_REPORTING_EXCEPTION"
    return {
        "child_lei": child, "parent_lei": actual_parent,
        "relation_kind": kind, "reporting_exception_reason": reason,
        "periods": periods, "source_url": url,
        "original_sha256": hashlib.sha256(blob).hexdigest(),
        "evidence_class": "GLEIF_LEVEL2_ACCOUNTING_CONSOLIDATION_OR_EXPLICIT_EXCEPTION",
        "insurance_exposure_observed": False,
        "treaty_relationship_observed": False,
        "beneficial_ownership_observed": False,
    }


def fetch_level2(lei: str, suffix: str) -> bytes:
    url = source_url(lei, suffix)
    request = Request(url, headers={
        "Accept": "application/vnd.api+json",
        "User-Agent": "OpenCatastrophe research GLEIF CC0 source verifier",
    })
    with urlopen(request, timeout=25) as res:
        if res.status != 200 or res.geturl() != url:
            raise GLEIFPilotError("unexpected redirect or GLEIF response status")
        blob = res.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise GLEIFPilotError("GLEIF Level-2 source too large")
    return blob


def store_level2(db_path: Path, sources: dict[tuple[str, str],bytes], captured_at: str) -> dict:
    if set(sources) != {(x,y) for x,y,_ in PILOT}:
        raise GLEIFPilotError("require all seven exact Level-2 API responses")
    rows = [parse_level2(sources[(lei,suffix)],lei,suffix,expected)
            for lei,suffix,expected in PILOT]
    if not isinstance(captured_at,str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\+00:00",captured_at):
        raise GLEIFPilotError("require precise UTC capture time")
    db_path = Path(db_path).expanduser()
    if db_path.is_symlink() or not db_path.is_file():
        raise GLEIFPilotError("refuse absent or nonregular CAT database")
    with sqlite3.connect(db_path) as con:
        if (con.execute("PRAGMA application_id").fetchone()[0] != CAT_APP_ID
            or con.execute("PRAGMA user_version").fetchone()[0] != CAT_SCHEMA_VERSION):
            raise GLEIFPilotError("refuse unrelated database")
        if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cat_gleif_legal_entity'").fetchone() is None:
            raise GLEIFPilotError("GLEIF Level-1 identity pilot must run first")
        con.execute("""CREATE TABLE IF NOT EXISTS cat_gleif_level2_observation (
          child_lei TEXT NOT NULL,
          endpoint_suffix TEXT NOT NULL,
          parent_lei TEXT,
          relation_kind TEXT NOT NULL,
          exception_reason TEXT,
          periods_json TEXT NOT NULL,
          source_url TEXT NOT NULL,
          original_sha256 TEXT NOT NULL,
          observed_at_utc TEXT NOT NULL,
          insurance_exposure_observed INTEGER NOT NULL CHECK(insurance_exposure_observed=0),
          treaty_relationship_observed INTEGER NOT NULL CHECK(treaty_relationship_observed=0),
          beneficial_ownership_observed INTEGER NOT NULL CHECK(beneficial_ownership_observed=0),
          PRIMARY KEY(child_lei,endpoint_suffix)
        )""")
        with con:
            for (child,suffix,_), row in zip(PILOT, rows):
                con.execute("""INSERT INTO cat_gleif_level2_observation VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(child_lei,endpoint_suffix) DO UPDATE SET
                  parent_lei=excluded.parent_lei,
                  relation_kind=excluded.relation_kind,
                  exception_reason=excluded.exception_reason,
                  periods_json=excluded.periods_json, source_url=excluded.source_url,
                  original_sha256=excluded.original_sha256, observed_at_utc=excluded.observed_at_utc""",
                  (child,suffix,row["parent_lei"],row["relation_kind"],
                   row["reporting_exception_reason"],json.dumps(row["periods"],sort_keys=True),
                   row["source_url"],row["original_sha256"],captured_at,0,0,0))
        return {
            "evidence_class": "GLEIF_LEVEL2_RESEARCH_ONLY",
            "records_verified": len(rows),
            "consolidation_links": sum(x["parent_lei"] is not None for x in rows),
            "reporting_exceptions": sum(x["parent_lei"] is None for x in rows),
            "original_sha256_by_endpoint": {
                r["source_url"]:r["original_sha256"] for r in rows},
            "source_bytes_committed":False,
            "ownership_percentage_estimated":False,
            "insured_portfolios_created":False,
            "neon_modified":False,
        }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fetch", action="store_true", help="download exact official GLEIF source endpoints")
    p.add_argument("--out", required=True, type=Path, help="existing CAT-only SQLite DB with Level 1 rows")
    args = p.parse_args()
    if not args.fetch:
        p.error("CLI only supports --fetch; tests may provide synthetic bytes directly")
    raw = {(lei,suffix):fetch_level2(lei,suffix) for lei,suffix,_ in PILOT}
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(store_level2(args.out,raw,observed),sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (GLEIFPilotError,OSError,sqlite3.DatabaseError) as exc:
        print(f"BLOCKED: {exc}",file=sys.stderr)
        raise SystemExit(1)
