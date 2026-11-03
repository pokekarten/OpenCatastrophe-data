# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Privacy-preserving, offline NYC PLUTO tax-lot vs LL84 campus linkage preflight.

Research only. A candidate is not a building identity, insured TIV or loss.
No source data, addresses, property IDs or BBLs are emitted in the output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BBL = re.compile(r"[1-5][0-9]{9}\Z")
BIN = re.compile(r"[1-5][0-9]{6}\Z")
MAX_ROWS = 10000


class LinkageError(ValueError):
    pass


def _tokens(value: object, field: str, pattern: re.Pattern[str]) -> tuple[str, ...]:
    if type(value) is not str:
        raise LinkageError(f"{field}: must be semicolon-delimited text")
    if not value:
        return ()
    parts = tuple(part.strip() for part in value.split(";"))
    if not all(pattern.fullmatch(part) for part in parts):
        raise LinkageError(f"{field}: expected strict 10-digit BBL or 7-digit BIN")
    if len(parts) != len(set(parts)):
        raise LinkageError(f"{field}: repeated identifier in one record")
    return parts


def _rows(obj: object, label: str) -> list[dict]:
    if type(obj) is not list or len(obj) > MAX_ROWS:
        raise LinkageError(f"{label}: expected at most {MAX_ROWS} rows")
    if any(type(row) is not dict for row in obj):
        raise LinkageError(f"{label}: every record must be an object")
    return obj


def analyze(payload: object) -> dict:
    if type(payload) is not dict or set(payload) != {"pluto_release", "pluto_rows", "ll84_rows"}:
        raise LinkageError("unexpected input schema")
    if payload["pluto_release"] != "26v2":
        raise LinkageError("only PLUTO 26v2 source identity accepted in this v0 diagnostic")

    pluto = {}
    for row in _rows(payload["pluto_rows"], "pluto_rows"):
        if set(row) != {"bbl", "num_buildings"}:
            raise LinkageError("PLUTO row has unexpected/missing fields")
        bbls = _tokens(row["bbl"], "pluto.bbl", BBL)
        count = row["num_buildings"]
        if len(bbls) != 1 or type(count) is not int or count < 0:
            raise LinkageError("PLUTO BBL must be unique and num_buildings nonnegative integer")
        if bbls[0] in pluto:
            raise LinkageError("duplicate PLUTO BBL; must not autoaggregate")
        pluto[bbls[0]] = count

    properties = []
    seen = set()
    year_bbl_count = Counter()
    for row in _rows(payload["ll84_rows"], "ll84_rows"):
        if set(row) != {"property_id", "calendar_year", "bbls", "bins"}:
            raise LinkageError("LL84 row has unexpected/missing fields")
        pid, year = row["property_id"], row["calendar_year"]
        if type(pid) is not str or not re.fullmatch(r"[0-9]+", pid):
            raise LinkageError("property_id must be numeric text")
        if type(year) is not int or not 2022 <= year <= 2026:
            raise LinkageError("calendar_year out of validated research range")
        if (pid, year) in seen:
            raise LinkageError("duplicate LL84 property-year; review revisions upstream")
        seen.add((pid, year))
        bbls = _tokens(row["bbls"], "ll84.bbls", BBL)
        bins = _tokens(row["bins"], "ll84.bins", BIN)
        properties.append((year, bbls, bins))
        for bbl in bbls:
            year_bbl_count[(year, bbl)] += 1

    reasons = Counter()
    candidates = Counter()
    for year, bbls, bins in properties:
        if not bbls:
            reason = "missing_bbl"
        elif len(bbls) != 1:
            reason = "multi_taxlot_campus"
        elif not bins:
            reason = "missing_bin"
        elif len(bins) != 1:
            reason = "multi_bin_campus"
        elif year_bbl_count[(year, bbls[0])] > 1:
            reason = "shared_bbl_same_year"
        elif bbls[0] not in pluto:
            reason = "bbl_absent_from_supplied_pluto"
        elif pluto[bbls[0]] != 1:
            reason = "pluto_multibuilding_or_unknown"
        else:
            reason = "unverified_single_bbl_bin_candidate"
            candidates[year] += 1
        reasons[reason] += 1

    return {
        "profile": "nyc-pluto-ll84-taxlot-linkage-research-v0",
        "admission": "not_admitted",
        "pluto_release": "26v2",
        "pluto_taxlot_rows": len(pluto),
        "ll84_property_year_rows": len(properties),
        "reason_counts": dict(sorted(reasons.items())),
        "candidate_property_years": {str(y): n for y, n in sorted(candidates.items())},
        "building_identity_proven": False,
        "insured_tiv_or_loss_calculated": False,
        "raw_identifiers_exported": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Pre-normalized local JSON only")
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > 2_000_000:
            raise LinkageError("input exceeds 2 MB preflight limit")
        content = json.loads(args.input.read_text(encoding="utf-8"))
        print(json.dumps(analyze(content), sort_keys=True, separators=(",", ":")))
        return 0
    except (LinkageError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
