#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed MTBS/FPA FOD identity audit on caller-prepared, bounded CSV projections.

No publisher network requests, native GPKG parsing, peril-frequency calibration,
source admission, loss estimates or identification of contractual occurrences.
Projection columns are local research interfaces, NOT published provider schemas.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

MAX_BYTES = 2_000_000
MAX_ROWS = 20_000
FPA_COLUMNS = ("fpa_record_id", "mtbs_id", "fire_year")
MTBS_COLUMNS = ("mtbs_component_id", "mtbs_id", "fire_year", "event_kind")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MTBS_VINTAGE = re.compile(r"MTBS[-_][A-Za-z0-9][A-Za-z0-9._-]{7,79}\Z")
YEAR = re.compile(r"[0-9]{4}\Z")


class WildfireAuditBlocked(ValueError):
    """An exact source, schema or join-identity proof is missing or invalid."""


def _read_projection(blob: bytes, expected_sha: str, columns: tuple[str, ...], label: str) -> list[dict[str, str]]:
    if type(expected_sha) is not str or not SHA256.fullmatch(expected_sha):
        raise WildfireAuditBlocked(label + ": expected lowercase SHA-256 required")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise WildfireAuditBlocked(label + ": empty or oversized projection bytes")
    if hashlib.sha256(blob).hexdigest() != expected_sha:
        raise WildfireAuditBlocked(label + ": source projection SHA-256 mismatch")
    try:
        text = blob.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != columns:
            raise WildfireAuditBlocked(label + ": expected exact normalized CSV column order")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise WildfireAuditBlocked(label + ": bounded row limit exceeded")
            if None in row or any(v is None for v in row.values()):
                raise WildfireAuditBlocked(label + ": malformed field count")
            if any(v != v.strip() for v in row.values()):
                raise WildfireAuditBlocked(label + ": unnormalized leading/trailing whitespace")
            rows.append(row)
        if not rows:
            raise WildfireAuditBlocked(label + ": at least one actual row required")
        return rows
    except (UnicodeError, csv.Error) as exc:
        raise WildfireAuditBlocked(label + ": malformed UTF-8 or CSV") from exc


def _id(value: str, label: str, *, optional: bool = False) -> str:
    if value == "" and optional:
        return value
    if not SAFE_ID.fullmatch(value):
        raise WildfireAuditBlocked(label + ": invalid source identifier")
    return value


def _year(value: str, label: str, low: int, high: int) -> int:
    if not YEAR.fullmatch(value):
        raise WildfireAuditBlocked(label + ": invalid calendar year")
    year = int(value)
    if not low <= year <= high:
        raise WildfireAuditBlocked(label + ": outside selected source temporal scope")
    return year


def audit_crosswalk(fpa_blob: bytes, fpa_sha256: str, mtbs_blob: bytes, mtbs_sha256: str,
                    *, fpa_release: str, mtbs_release: str) -> dict:
    """Return aggregate diagnostics only; never emit or persist actual source IDs."""
    if fpa_release != "FPA_FOD_20260615":
        raise WildfireAuditBlocked("FPA FOD original seventh-edition release must be fixed")
    if type(mtbs_release) is not str or not MTBS_VINTAGE.fullmatch(mtbs_release) or any(
        x in mtbs_release.lower() for x in ("latest", "current", "unknown")
    ):
        raise WildfireAuditBlocked("MTBS exact publisher product/reprocessing vintage required")

    fpa_rows = _read_projection(fpa_blob, fpa_sha256, FPA_COLUMNS, "FPA FOD")
    mtbs_rows = _read_projection(mtbs_blob, mtbs_sha256, MTBS_COLUMNS, "MTBS")
    fpa_by_mtbs = Counter()
    mtbs_by_id = Counter()
    mtbs_row = {}
    seen_fpa = set()
    seen_mtbs = set()

    for row in fpa_rows:
        fid = _id(row["fpa_record_id"], "FPA FOD primary key")
        if fid in seen_fpa:
            raise WildfireAuditBlocked("duplicate FPA FOD record ID")
        seen_fpa.add(fid)
        mtbs_id = _id(row["mtbs_id"], "FPA FOD MTBS_ID", optional=True)
        _year(row["fire_year"], "FPA FOD", 1992, 2024)
        if mtbs_id:
            fpa_by_mtbs[mtbs_id] += 1

    for row in mtbs_rows:
        component = _id(row["mtbs_component_id"], "MTBS projection component key")
        if component in seen_mtbs:
            raise WildfireAuditBlocked("duplicate MTBS projection component key")
        seen_mtbs.add(component)
        mtbs_id = _id(row["mtbs_id"], "MTBS source ID")
        _year(row["fire_year"], "MTBS", 1984, 2026)
        if row["event_kind"] not in ("wildfire", "prescribed", "unknown"):
            raise WildfireAuditBlocked("MTBS event_kind requires an audited explicit mapping")
        mtbs_by_id[mtbs_id] += 1
        mtbs_row[mtbs_id] = row

    disposition = Counter()
    for row in fpa_rows:
        key = row["mtbs_id"]
        if not key:
            kind = "no_mtbs_id_recorded"
        elif key not in mtbs_by_id:
            kind = "mtbs_id_not_in_supplied_perimeter_subset"
        elif fpa_by_mtbs[key] != 1 or mtbs_by_id[key] != 1:
            kind = "ambiguous_one_to_many_or_many_to_one"
        elif row["fire_year"] != mtbs_row[key]["fire_year"]:
            kind = "source_fire_year_disagreement"
        elif mtbs_row[key]["event_kind"] == "prescribed":
            kind = "prescribed_fire_not_wildfire"
        elif mtbs_row[key]["event_kind"] == "unknown":
            kind = "unknown_mtbs_event_kind"
        else:
            kind = "unique_mtbs_id_research_candidate"
        disposition[kind] += 1

    names = (
        "no_mtbs_id_recorded", "mtbs_id_not_in_supplied_perimeter_subset",
        "ambiguous_one_to_many_or_many_to_one", "source_fire_year_disagreement",
        "prescribed_fire_not_wildfire", "unknown_mtbs_event_kind",
        "unique_mtbs_id_research_candidate",
    )
    counts = {name: disposition[name] for name in names}
    if sum(counts.values()) != len(fpa_rows):
        raise WildfireAuditBlocked("audit failed row conservation")
    problems = sum(counts[k] for k in (
        "ambiguous_one_to_many_or_many_to_one", "source_fire_year_disagreement",
        "unknown_mtbs_event_kind",
    ))
    unique = counts["unique_mtbs_id_research_candidate"]
    return {
        "audit": "us-wildfire-mtbs-fpa-fod-crosswalk-v0",
        "fpa_release": fpa_release,
        "mtbs_release": mtbs_release,
        "fpa_projection_sha256": fpa_sha256,
        "mtbs_projection_sha256": mtbs_sha256,
        "fpa_rows": len(fpa_rows),
        "mtbs_component_rows": len(mtbs_rows),
        "mtbs_components_without_fpa_reference": sum(
            count for key, count in mtbs_by_id.items() if key not in fpa_by_mtbs
        ),
        "fpa_row_disposition": counts,
        "fpa_rows_conserved": True,
        "state": "REVIEW_NEEDED" if problems else (
            "RESEARCH_ID_CANDIDATES_ONLY" if unique else "NO_UNAMBIGUOUS_ID_CANDIDATE"
        ),
        "mapped_components_are_independent_observations": False,
        "full_national_wildfire_census_proven": False,
        "physical_event_identity_approved": False,
        "contractual_occurrence_approved": False,
        "building_damage_or_insured_losses_derived": False,
        "scientific_fitness_established": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fpa-projection", type=Path, required=True)
    parser.add_argument("--fpa-sha256", required=True)
    parser.add_argument("--mtbs-projection", type=Path, required=True)
    parser.add_argument("--mtbs-sha256", required=True)
    parser.add_argument("--fpa-release", required=True)
    parser.add_argument("--mtbs-release", required=True)
    args = parser.parse_args(argv)
    try:
        for path in (args.fpa_projection, args.mtbs_projection):
            if not path.is_file() or path.stat().st_size > MAX_BYTES:
                raise WildfireAuditBlocked("missing or oversized local projection file")
        report = audit_crosswalk(
            args.fpa_projection.read_bytes(), args.fpa_sha256,
            args.mtbs_projection.read_bytes(), args.mtbs_sha256,
            fpa_release=args.fpa_release, mtbs_release=args.mtbs_release)
    except (OSError, WildfireAuditBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_NEEDED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
