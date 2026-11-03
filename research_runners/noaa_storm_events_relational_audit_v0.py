#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, hash-bound relational audit; never publish provider records.

Exit 0: selected checks consistent; 1: relational contradictions; 2: invalid
input. None of these outcomes establishes rights, admission or model fitness.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zlib

MAX_COMPRESSED = 30_000_000
MAX_DECODED = 80_000_000
HEADERS = {
    "details": tuple((
        "BEGIN_YEARMONTH BEGIN_DAY BEGIN_TIME END_YEARMONTH END_DAY END_TIME "
        "EPISODE_ID EVENT_ID STATE STATE_FIPS YEAR MONTH_NAME EVENT_TYPE CZ_TYPE "
        "CZ_FIPS CZ_NAME WFO BEGIN_DATE_TIME CZ_TIMEZONE END_DATE_TIME "
        "INJURIES_DIRECT INJURIES_INDIRECT DEATHS_DIRECT DEATHS_INDIRECT "
        "DAMAGE_PROPERTY DAMAGE_CROPS SOURCE MAGNITUDE MAGNITUDE_TYPE FLOOD_CAUSE "
        "CATEGORY TOR_F_SCALE TOR_LENGTH TOR_WIDTH TOR_OTHER_WFO "
        "TOR_OTHER_CZ_STATE TOR_OTHER_CZ_FIPS TOR_OTHER_CZ_NAME BEGIN_RANGE "
        "BEGIN_AZIMUTH BEGIN_LOCATION END_RANGE END_AZIMUTH END_LOCATION "
        "BEGIN_LAT BEGIN_LON END_LAT END_LON EPISODE_NARRATIVE EVENT_NARRATIVE "
        "DATA_SOURCE").split()),
    "fatalities": tuple((
        "FAT_YEARMONTH FAT_DAY FAT_TIME FATALITY_ID EVENT_ID FATALITY_TYPE "
        "FATALITY_DATE FATALITY_AGE FATALITY_SEX FATALITY_LOCATION").split()),
    "locations": tuple((
        "YEARMONTH EPISODE_ID EVENT_ID LOCATION_INDEX RANGE AZIMUTH LOCATION "
        "LATITUDE LONGITUDE LAT2 LON2").split()),
}
KEEP = {
    "details": ("EVENT_ID", "EPISODE_ID", "DEATHS_DIRECT", "DEATHS_INDIRECT",
                "DAMAGE_PROPERTY", "DAMAGE_CROPS", "EVENT_TYPE", "MAGNITUDE_TYPE"),
    "fatalities": ("EVENT_ID", "FATALITY_ID", "FATALITY_TYPE"),
    "locations": ("EVENT_ID", "EPISODE_ID", "LOCATION_INDEX"),
}


class StormAuditError(ValueError):
    """Input identity, format or key semantics cannot be trusted."""


def _table(kind: str, blob: bytes, expected: str) -> list[dict]:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise StormAuditError(kind + ": expected SHA256 must be lower-case hex")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_COMPRESSED:
        raise StormAuditError(kind + ": compressed byte bound exceeded or empty")
    if hashlib.sha256(blob).hexdigest() != expected:
        raise StormAuditError(kind + ": original compressed SHA256 mismatch")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as source:
            raw = source.read(MAX_DECODED + 1)
        if len(raw) > MAX_DECODED:
            raise StormAuditError(kind + ": decoded byte bound exceeded")
        text = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != HEADERS[kind]:
            raise StormAuditError(kind + ": unexpected complete CSV header")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise StormAuditError(kind + ": malformed column count")
            # Narratives and individual fatality attributes are discarded.
            rows.append({key: row[key].strip() for key in KEEP[kind]})
        return rows
    except (OSError, EOFError, UnicodeError, csv.Error, zlib.error) as exc:
        raise StormAuditError(kind + ": invalid gzip/CRC/UTF-8/CSV") from exc


def _id(raw: str) -> str:
    if len(raw) > 20 or not re.fullmatch(r"[1-9][0-9]*", raw):
        raise StormAuditError("invalid positive integer source key")
    return raw


def _count(raw: str) -> int:
    if len(raw) > 12 or not re.fullmatch(r"[0-9]+", raw):
        raise StormAuditError("invalid nonnegative reported count")
    return int(raw)


def damage_status(raw: str) -> str:
    """Distinguish unknown, reported zero and reported positive damage."""
    if not raw:
        return "missing"
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMB]?)", raw)
    if len(raw) > 40 or not match:
        raise StormAuditError("unrecognized reported damage encoding")
    amount = Decimal(match[1]) * {"": 1, "K": 1000, "M": 1000000,
                                "B": 1000000000}[match[2]]
    return "reported_zero" if amount == 0 else "reported_positive"


def _subset_summary(ids, events, fatality_counts, location_counts):
    # Summarize parents once, independently of child join multiplicity.
    damage = {field: Counter(missing=0, reported_zero=0, reported_positive=0)
              for field in ("DAMAGE_PROPERTY", "DAMAGE_CROPS")}
    for key in ids:
        for field in damage:
            damage[field][damage_status(events[key][field])] += 1
    return {
        "parent_rows": len(ids),
        "matched_location_rows": sum(location_counts[key] for key in ids),
        "reported_fatalities": {
            kind: sum(events[key][field] for key in ids)
            for kind, field in (("D", "DEATHS_DIRECT"), ("I", "DEATHS_INDIRECT"))},
        "matched_fatality_rows": {
            kind: sum(fatality_counts[key, kind] for key in ids) for kind in ("D", "I")},
        "damage_field_status": {field: dict(value) for field, value in damage.items()},
    }


def _review_partition(events, fatality_counts, location_counts, flagged, problems):
    # This proposes a review subset; it never drops or repairs source records.
    orphan_rows = {key: problems[key] for key in
                   ("fatality_orphan_rows", "location_orphan_rows")}
    blocked = any(orphan_rows.values())
    eligible = set() if blocked else set(events) - flagged
    quarantined = set(events) - eligible
    summaries = {
        label: _subset_summary(ids, events, fatality_counts, location_counts)
        for label, ids in (("eligible_for_selected_checks", eligible),
                           ("quarantined_for_review", quarantined))}
    total = _subset_summary(set(events), events, fatality_counts, location_counts)
    conserved = all(
        sum(group["reported_fatalities"][kind] for group in summaries.values())
        == total["reported_fatalities"][kind] for kind in ("D", "I"))
    conserved = conserved and sum(group["parent_rows"] for group in summaries.values()) == len(events)
    if not conserved or eligible.intersection(quarantined):
        raise StormAuditError("review partition does not conserve parent totals")
    eligible_counts_agree = all(
        summaries["eligible_for_selected_checks"]["reported_fatalities"][kind]
        == summaries["eligible_for_selected_checks"]["matched_fatality_rows"][kind]
        for kind in ("D", "I"))
    if not eligible_counts_agree:
        raise StormAuditError("eligible review subset still has count contradictions")
    return {
        "scope": "selected cross-table consistency only; no automatic model-input exclusion",
        "state": "blocked_by_orphan_children" if blocked else "review_partition_available",
        "distinct_parents_with_known_contradiction": len(flagged),
        "unassigned_orphan_child_rows": orphan_rows,
        "parent_and_reported_fatality_totals_conserved": conserved,
        "nonempty_eligible_subset_checks_passed": bool(eligible) and eligible_counts_agree,
        **summaries,
    }


def audit_tables(blobs: dict[str, bytes], expected_sha256: dict[str, str]) -> dict:
    """Audit three pinned tables, returning only aggregate diagnostics."""
    if set(blobs) != set(HEADERS) or set(expected_sha256) != set(HEADERS):
        raise StormAuditError("exactly details, fatalities and locations required")
    tables = {kind: _table(kind, blobs[kind], expected_sha256[kind]) for kind in HEADERS}
    if not tables["details"]:
        raise StormAuditError("empty details table is not a validated event set")
    events = {}
    damage = {key: Counter(missing=0, reported_zero=0, reported_positive=0)
              for key in ("DAMAGE_PROPERTY", "DAMAGE_CROPS")}
    wind_types = Counter()
    for row in tables["details"]:
        key = _id(row["EVENT_ID"])
        _id(row["EPISODE_ID"])
        if key in events:
            raise StormAuditError("duplicate parent EVENT_ID")
        events[key] = row
        for field in ("DEATHS_DIRECT", "DEATHS_INDIRECT"):
            row[field] = _count(row[field])
        for field in damage:
            damage[field][damage_status(row[field])] += 1
        if row["EVENT_TYPE"] == "Thunderstorm Wind":
            if row["MAGNITUDE_TYPE"] not in ("", "MG", "EG", "MS", "ES"):
                raise StormAuditError("unknown thunderstorm wind magnitude type")
            wind_types[row["MAGNITUDE_TYPE"] or "(missing)"] += 1
    fatality_counts = Counter()
    fatality_keys = set()
    location_keys = set()
    location_counts = Counter()
    flagged_parents = set()
    problems = Counter(fatality_orphan_rows=0, location_orphan_rows=0,
                       location_episode_mismatch_rows=0)
    for row in tables["fatalities"]:
        key = _id(row["FATALITY_ID"])
        event_id = _id(row["EVENT_ID"])
        if key in fatality_keys:
            raise StormAuditError("duplicate FATALITY_ID")
        fatality_keys.add(key)
        kind = row["FATALITY_TYPE"]
        if kind not in ("D", "I"):
            raise StormAuditError("unknown FATALITY_TYPE")
        problems["fatality_orphan_rows"] += event_id not in events
        fatality_counts[event_id, kind] += 1
    for row in tables["locations"]:
        event_id = _id(row["EVENT_ID"])
        _id(row["EPISODE_ID"])
        key = (event_id, _id(row["LOCATION_INDEX"]))
        if key in location_keys:
            raise StormAuditError("duplicate EVENT_ID/LOCATION_INDEX")
        location_keys.add(key)
        location_counts[event_id] += 1
        if event_id not in events:
            problems["location_orphan_rows"] += 1
        elif row["EPISODE_ID"] != events[event_id]["EPISODE_ID"]:
            problems["location_episode_mismatch_rows"] += 1
            flagged_parents.add(event_id)
    reconciliation = {}
    for kind, field in (("D", "DEATHS_DIRECT"), ("I", "DEATHS_INDIRECT")):
        residuals = []
        for key, row in events.items():
            residual = fatality_counts[key, kind] - row[field]
            residuals.append(residual)
            if residual:
                flagged_parents.add(key)
        reconciliation[kind] = {
            "reported_in_details": sum(row[field] for row in events.values()),
            "matched_child_rows": sum(fatality_counts[key, kind] for key in events),
            "mismatched_events": sum(value != 0 for value in residuals),
            "max_abs_event_residual": max(map(abs, residuals)),
        }
    multiplicities = [max(1, location_counts[key]) * max(
        1, fatality_counts[key, "D"] + fatality_counts[key, "I"]) for key in events]
    consistent = not any(problems.values()) and not any(
        value["mismatched_events"] for value in reconciliation.values())
    return {
        "audit": "noaa-storm-events-relational-v0",
        "status": "consistent" if consistent else "inconsistent",
        "selected_checks_passed": consistent,
        "source_compressed_sha256": dict(expected_sha256),
        "rows": {kind: len(rows) for kind, rows in tables.items()},
        "problems": dict(problems), "fatality_reconciliation": reconciliation,
        "review_partition": _review_partition(
            events, fatality_counts, location_counts, flagged_parents, problems),
        "damage_field_status": {key: dict(value) for key, value in damage.items()},
        "thunderstorm_wind_magnitude_types": dict(wind_types),
        "join_cardinality": {
            "parent_rows": len(events), "naive_left_join_rows": sum(multiplicities),
            "duplicated_parents": sum(value > 1 for value in multiplicities),
            "max_parent_multiplicity": max(multiplicities),
        },
        "source_admission_granted": False, "scientific_fitness_established": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in HEADERS:
        parser.add_argument("--" + kind, type=Path, required=True)
        parser.add_argument("--" + kind + "-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        blobs = {}
        for kind in HEADERS:
            with getattr(args, kind).open("rb") as source:
                blobs[kind] = source.read(MAX_COMPRESSED + 1)
        report = audit_tables(blobs, {kind: getattr(args, kind + "_sha256")
                                     for kind in HEADERS})
    except (StormAuditError, OSError) as exc:
        print(json.dumps({"status": "invalid_input", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["selected_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
