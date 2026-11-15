# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, non-admission preflight for the frozen 2026-11-15 Polisa all-markets CSV.

No HTTP, database writes, public data bytes, source rights or model approval.
An output SHA-256 identifies *local* bytes, not independent provider authenticity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

VERSION = "2026-11-15.792a4a"
EXPECTED_ROWS = 1772  # Provider-advertised, unverified count
MAX_BYTES = 2_000_000
MARKETS = frozenset({
    "Albania", "Bosnia and Herzegovina", "Bulgaria", "Croatia",
    "Czechia", "Estonia", "Hungary", "Kosovo*", "Latvia", "Lithuania",
    "Moldova", "Montenegro", "North Macedonia", "Poland", "Romania",
    "Serbia", "Slovakia", "Slovenia",
})
COLUMNS = tuple((
    "market,year,insurer,insurer_id,group,premium_eur_m,life_premium_eur_m,"
    "line_mtpl_eur_m,line_casco_eur_m,line_property_eur_m,line_health_eur_m,"
    "line_accident_eur_m,line_liability_eur_m,line_credit_eur_m,line_other_eur_m,"
    "line_life_eur_m,nonlife_earned_eur_m,nonlife_claims_eur_m,"
    "nonlife_expenses_eur_m,claims_ratio_gross_pct,claims_ratio_net_pct,"
    "combined_ratio_net_pct,own_funds_eur_m,scr_eur_m,mcr_eur_m,scr_ratio_pct,"
    "solvency_basis,net_profit_eur_m,equity_end_eur_m,roe_pct,data_note,"
    "source,quality_premium,quality_lines,quality_claims,quality_solvency,"
    "premium_written_abroad_eur_m,data_version,lei,annuity_claims_gross_eur_m,"
    "annuity_claims_net_eur_m,annuity_expenses_eur_m"
).split(","))
NUMERIC = tuple(c for c in COLUMNS if c.endswith(("_eur_m", "_pct")))
LEI = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")


class Blocked(ValueError):
    """Stop rather than silently accept changed or ambiguous provider data."""


def valid_lei(value: str) -> bool:
    """Check ISO 17442 shape and ISO/IEC 7064 MOD 97-10 digits, not registry status."""
    if not LEI.fullmatch(value):
        return False
    remainder = 0
    for ch in value:
        digits = str(ord(ch) - ord("A") + 10) if "A" <= ch <= "Z" else ch
        for digit in digits:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder == 1


def _source_ok(value: str) -> bool:
    if not value or any(c.isspace() for c in value):
        return False
    try:
        url = urlsplit(value)
        host = url.hostname
        _ = url.port
    except ValueError:
        return False
    if not (url.scheme == "https" and host and not url.username
            and not url.password and host.lower() != "localhost"
            and not host.lower().endswith((".localhost", ".local", ".internal"))):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True  # A domain is a provenance string, never fetched by this tool.


def inspect(raw: bytes, *, expected_rows: int = EXPECTED_ROWS,
            expected_markets: frozenset[str] = MARKETS) -> dict[str, object]:
    """Inspect local CSV bytes only; never return insurer names or raw values."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise Blocked("unbounded or empty CSV input")
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Blocked("not UTF-8") from exc
    if "\x00" in content:
        raise Blocked("NUL in input")
    reader = csv.reader(io.StringIO(content, newline=""), strict=True)
    try:
        header = tuple(next(reader))
    except (StopIteration, csv.Error) as exc:
        raise Blocked("missing/malformed header") from exc
    if header != COLUMNS:
        raise Blocked("frozen 42-column schema/order drift")
    keys: set[tuple[str, str, str]] = set()
    markets: Counter[str] = Counter()
    missing_property = 0
    for line, fields in enumerate(reader, 2):
        if len(fields) != len(COLUMNS):
            raise Blocked(f"row {line}: column count")
        row = dict(zip(COLUMNS, fields))
        market, year, insurer_id = row["market"], row["year"], row["insurer_id"]
        if market not in expected_markets or year not in {
            "2021", "2022", "2023", "2024", "2025"
        }:
            raise Blocked(f"row {line}: market/year outside frozen scope")
        if not row["insurer"].strip() or not insurer_id.strip():
            raise Blocked(f"row {line}: missing insurer identity")
        key = (market, year, insurer_id)
        if key in keys:
            raise Blocked(f"row {line}: duplicate insurer-year key")
        keys.add(key)
        if row["data_version"] != VERSION:
            raise Blocked(f"row {line}: mixed/stale data version")
        if not _source_ok(row["source"]):
            raise Blocked(f"row {line}: missing/unsafe upstream source")
        if row["lei"] and not valid_lei(row["lei"]):
            raise Blocked(f"row {line}: invalid LEI shape or check digits")
        for col in NUMERIC:
            cell = row[col]
            if cell == "":
                if col == "premium_eur_m":
                    raise Blocked(f"row {line}: missing premium")
                if col == "line_property_eur_m":
                    missing_property += 1
                continue
            try:
                value = Decimal(cell)
            except InvalidOperation as exc:
                raise Blocked(f"row {line}: invalid numeric value in {col}") from exc
            if not value.is_finite() or (col == "premium_eur_m" and value < 0):
                raise Blocked(f"row {line}: invalid numeric range in {col}")
        markets[market] += 1
    if len(keys) != expected_rows:
        raise Blocked(f"row count differs from provider's {expected_rows} claim")
    if frozenset(markets) != expected_markets:
        raise Blocked("18-market coverage incomplete")
    return {
        "profile": "polisa-local-csv-preflight-v0",
        "source_id": "polisa.cee18-insurer-market-compilation.20261109",
        "data_version": VERSION,
        "local_byte_count": len(raw),
        "local_sha256_not_provider_authentication": hashlib.sha256(raw).hexdigest(),
        "row_count": len(keys),
        "market_count": len(markets),
        "missing_property_premium_cells_not_zeros": missing_property,
        "provider_original_bytes_authenticated": False,
        "row_level_upstream_rights_reviewed": False,
        "commercial_reuse_approved": False,
        "cat_model_input_approved": False,
        "insurer_exposure_inferred": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True,
                        help="Already acquired, permitted CSV outside public Git")
    args = parser.parse_args(argv)
    try:
        with args.csv.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        result = inspect(raw)
    except (OSError, csv.Error, Blocked) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
