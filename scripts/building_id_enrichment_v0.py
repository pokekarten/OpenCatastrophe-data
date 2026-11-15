#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, diagnostic-only exact building-ID enrichment with fail-closed semantics.

Inputs are *local, user-supplied* CSV files; this script never fetches sources,
touches a database, exports per-building records, or admits data into a model.
It intentionally does not guess missing identities via addresses/geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

FIELDS = ("construction_year", "roof_type", "floors_above_ground")
BASE_REQUIRED = ("building_id", *FIELDS)
SUPPLEMENT_REQUIRED = (
    "source_record_id", "building_id", "record_kind",
    "observation_kind", *FIELDS,
)
RECORD_KINDS = frozenset(("building", "dwelling", "address", "parcel", "certificate"))
OBSERVATION_KINDS = frozenset(("measured", "official_record", "modelled", "statistical_estimate"))
# This pilot is a bounded *sample diagnostic*, not a national bulk ETL runner.
MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_INPUT_ROWS = 100_000


class BuildingEnrichmentError(ValueError):
    """Invalid or unsafe input; fail before computing an apparently valid report."""


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        if path.is_symlink() or not path.is_file():
            raise BuildingEnrichmentError("CSV source must be a regular, non-symlink file")
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise BuildingEnrichmentError("CSV input exceeds bounded sample byte limit")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, restkey="_unexpected")
            header = reader.fieldnames
            if not header or len(header) != len(set(header)):
                raise BuildingEnrichmentError("CSV requires unique nonempty column headers")
            if any(column not in header for column in required):
                raise BuildingEnrichmentError("CSV missing required building-enrichment columns")
            result = []
            for row_no, row in enumerate(reader, 2):
                if None in row or "_unexpected" in row:
                    raise BuildingEnrichmentError(f"CSV row {row_no}: malformed field count")
                if any(not isinstance(row[col], str) for col in required):
                    raise BuildingEnrichmentError(f"CSV row {row_no}: missing CSV value")
                if len(result) >= MAX_INPUT_ROWS:
                    raise BuildingEnrichmentError("CSV input exceeds bounded sample row limit")
                result.append(row)
            return result
    except (OSError, UnicodeError, csv.Error) as exc:
        raise BuildingEnrichmentError("Cannot read local UTF-8 CSV") from exc


def _validate_value(field: str, value: str, row_no: int) -> str:
    if value == "":
        return ""
    if field in ("construction_year", "floors_above_ground"):
        if not value.isascii() or not value.isdigit():
            raise BuildingEnrichmentError(f"CSV row {row_no}: invalid numeric {field}")
        number = int(value)
        if field == "construction_year" and not 1000 <= number <= 2100:
            raise BuildingEnrichmentError(f"CSV row {row_no}: implausible construction year")
        if field == "floors_above_ground" and not 1 <= number <= 300:
            raise BuildingEnrichmentError(f"CSV row {row_no}: implausible floor count")
        return str(number)
    if field == "roof_type":
        if value.strip() != value or len(value) > 120 or "\x00" in value:
            raise BuildingEnrichmentError(f"CSV row {row_no}: invalid roof type")
        return value.casefold()
    raise AssertionError(field)


def _normalise(rows: list[dict[str, str]], *, supplement: bool) -> list[dict[str, str]]:
    cleaned = []
    for row_no, row in enumerate(rows, 2):
        x = dict(row)
        x["building_id"] = x["building_id"].strip()
        if not x["building_id"] or len(x["building_id"]) > 256:
            raise BuildingEnrichmentError(f"CSV row {row_no}: missing/invalid building identity")
        if supplement:
            x["source_record_id"] = x["source_record_id"].strip()
            if not x["source_record_id"] or len(x["source_record_id"]) > 256:
                raise BuildingEnrichmentError(f"CSV row {row_no}: missing source record identity")
            if x["record_kind"] not in RECORD_KINDS:
                raise BuildingEnrichmentError(f"CSV row {row_no}: unsupported record kind")
            if x["observation_kind"] not in OBSERVATION_KINDS:
                raise BuildingEnrichmentError(f"CSV row {row_no}: unsupported observation kind")
        for field in FIELDS:
            x[field] = _validate_value(field, x[field], row_no)
        cleaned.append(x)
    return cleaned


def _unique(rows: list[dict[str, str]], field: str, kind: str) -> None:
    ids = [row[field] for row in rows]
    if len(set(ids)) != len(ids):
        raise BuildingEnrichmentError(f"Duplicate {kind} identity: cannot safely match")


def _sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def build_report(base_path: Path, supplement_path: Path, *, base_source_id: str,
                 supplement_source_id: str, rights_state: str = "not_reviewed") -> dict:
    """Return aggregate candidate diagnostics; never emit IDs or original values."""
    if not base_source_id or not supplement_source_id:
        raise BuildingEnrichmentError("Both source IDs are mandatory")
    if rights_state not in ("not_reviewed", "reviewed_for_local_analysis"):
        raise BuildingEnrichmentError("Invalid local-analysis rights state")

    base = _normalise(_read_csv(base_path, BASE_REQUIRED), supplement=False)
    supplementary = _normalise(_read_csv(supplement_path, SUPPLEMENT_REQUIRED), supplement=True)
    _unique(base, "building_id", "base building")
    _unique(supplementary, "source_record_id", "supplementary source record")
    if not base:
        raise BuildingEnrichmentError("Empty base: no buildings to compare")

    by_building: dict[str, list[dict[str, str]]] = defaultdict(list)
    other_entity_count = 0
    for row in supplementary:
        if row["record_kind"] != "building":
            other_entity_count += 1
            continue
        by_building[row["building_id"]].append(row)

    base_ids = {row["building_id"] for row in base}
    unmatched_supplementary = sum(
        len(rows) for key, rows in by_building.items() if key not in base_ids
    )
    ambiguous = {key for key, rows in by_building.items() if len(rows) != 1 and key in base_ids}
    matched = 0
    unmatched_base = 0
    fields: dict[str, Counter] = {field: Counter() for field in FIELDS}
    kinds: Counter = Counter()
    for row in base:
        b_id = row["building_id"]
        hits = by_building.get(b_id, [])
        if not hits:
            unmatched_base += 1
            continue
        if b_id in ambiguous:
            continue
        matched += 1
        supplement = hits[0]
        kinds[supplement["observation_kind"]] += 1
        for field in FIELDS:
            prior, candidate = row[field], supplement[field]
            if not candidate:
                continue
            if prior:
                fields[field]["agreement" if prior == candidate else "conflict"] += 1
            elif supplement["observation_kind"] in ("measured", "official_record"):
                fields[field]["proposed_observed_fill"] += 1
            elif supplement["observation_kind"] == "modelled":
                fields[field]["proposed_modelled_fill"] += 1
            else:
                fields[field]["blocked_aggregate_to_building_inference"] += 1

    assert matched + unmatched_base + len(ambiguous) == len(base)
    field_stats = {
        field: {
            key: fields[field][key] for key in (
                "agreement", "conflict", "proposed_observed_fill",
                "proposed_modelled_fill", "blocked_aggregate_to_building_inference",
            )
        }
        for field in FIELDS
    }
    return {
        "schema_version": "building-id-enrichment-diagnostic-v0",
        "base_source_id": base_source_id,
        "supplement_source_id": supplement_source_id,
        "base_sha256": _sha256(base_path),
        "supplement_sha256": _sha256(supplement_path),
        "rights_state_declared_by_caller": rights_state,
        "join_method": "strict_same_building_id_only",
        "rights_approved_for_model_input": False,
        "source_independence_established": False,
        "model_input_admitted": False,
        "provider_or_database_writes": False,
        "building_counts": {
            "base": len(base),
            "source_records": len(supplementary),
            "nonbuilding_records_skipped": other_entity_count,
            "exact_unique_matches": matched,
            "unmatched_base": unmatched_base,
            "ambiguous_base_buildings": len(ambiguous),
            "source_building_records_without_base_match": unmatched_supplementary,
        },
        "matching_observation_kind_counts": {
            key: kinds[key] for key in sorted(OBSERVATION_KINDS)
        },
        "attributes": field_stats,
        "warning": (
            "Aggregate diagnostic only; no record-level fill produced. "
            "IDs must be documented as the same BUILDING namespace and vintage externally; "
            "address, dwelling, parcel and certificate identifiers are not interchangeable. "
            "No spatial fallback, source rights or independent-observation validation."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--supplement", required=True, type=Path)
    parser.add_argument("--base-source-id", required=True)
    parser.add_argument("--supplement-source-id", required=True)
    parser.add_argument("--rights-state", choices=("not_reviewed", "reviewed_for_local_analysis"),
                        default="not_reviewed")
    parser.add_argument("--out", type=Path, help="Optional JSON diagnostics file (never raw rows)")
    args = parser.parse_args(argv)
    try:
        if args.out is not None:
            # Never overwrite source bytes, including a hardlink alias or output symlink.
            if args.out.is_symlink():
                raise BuildingEnrichmentError("Output symlinks are not permitted")
            if (args.out.resolve() in (args.base.resolve(), args.supplement.resolve())
                    or (args.out.exists() and (
                        args.out.samefile(args.base) or args.out.samefile(args.supplement)))):
                raise BuildingEnrichmentError("Output would overwrite an original CSV input")
        report = build_report(
            args.base, args.supplement,
            base_source_id=args.base_source_id,
            supplement_source_id=args.supplement_source_id,
            rights_state=args.rights_state,
        )
    except (BuildingEnrichmentError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False,
                          sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(rendered)
    else:
        args.out.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
