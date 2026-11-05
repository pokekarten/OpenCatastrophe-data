# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline aggregate-only cardinality QA for a bounded LINZ property-to-building pilot.

Inputs are local, rights-cleared CSV extracts selected outside the repository.
Only public source join keys are read; no row values or individual identifiers
are emitted, no data is downloaded, and no source/model admission is inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


class NZJoinPreflightError(ValueError):
    """Fail closed on unusable input format or unjustified join assumptions."""


def _id(value: object) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    if cleaned.casefold() in {"", "null", "none", "nan", "n/a"}:
        return ""
    return cleaned


def _read_bounded_csv(path: Path, fields: tuple[str, ...], max_rows: int) -> list[dict[str, str]]:
    if max_rows < 1 or max_rows > 100_000:
        raise NZJoinPreflightError("max_rows must be in range 1..100000")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            if not headers or len(headers) != len(set(headers)) or not set(fields).issubset(headers):
                raise NZJoinPreflightError("missing or duplicate required CSV header")
            records: list[dict[str, str]] = []
            for record in reader:
                if len(records) >= max_rows:
                    raise NZJoinPreflightError("CSV exceeds bounded pilot row limit")
                if None in record:
                    raise NZJoinPreflightError("CSV row has excess columns")
                records.append({field: _id(record.get(field)) for field in fields})
    except (OSError, UnicodeError, csv.Error) as exc:
        raise NZJoinPreflightError("unreadable CSV input") from exc
    return records


def evaluate(
    valuations: Iterable[dict[str, str]],
    boundaries: Iterable[dict[str, str]],
    property_building_refs: Iterable[dict[str, str]],
    current_outlines: Iterable[dict[str, str]],
) -> dict[str, object]:
    """Compute ID-only join diagnostics, never geocode or replicate valuations."""
    v_rows = tuple(valuations)
    b_rows = tuple(boundaries)
    r_rows = tuple(property_building_refs)
    o_rows = tuple(current_outlines)

    val_ids = [_id(row.get("unit_of_property_id")) for row in v_rows]
    val_nonempty = [value for value in val_ids if value]
    unique_val = set(val_nonempty)
    boundary_ids = {_id(row.get("unit_of_property_id")) for row in b_rows}
    boundary_ids.discard("")
    refs: dict[str, set[str]] = defaultdict(set)
    ref_pairs: set[tuple[str, str]] = set()
    invalid_refs = 0
    duplicate_ref_pairs = 0
    for row in r_rows:
        uid, bid = _id(row.get("unit_of_property_id")), _id(row.get("building_id"))
        if not uid or not bid:
            invalid_refs += 1
            continue
        pair = (uid, bid)
        if pair in ref_pairs:
            duplicate_ref_pairs += 1
        ref_pairs.add(pair)
        refs[uid].add(bid)
    outline_ids = [_id(row.get("building_id")) for row in o_rows]
    outlined = set(outline_ids)
    outlined.discard("")

    with_ref = {uid for uid in unique_val if refs.get(uid)}
    with_outline = {uid for uid in with_ref if refs[uid] & outlined}
    confirmed_outline_keys = set().union(*(refs[uid] & outlined for uid in with_outline)) if with_outline else set()
    multi_roof = {uid for uid in with_ref if len(refs[uid]) > 1}

    return {
        "profile": "nz-linz-property-building-join-aggregate-preflight-v0",
        "evidence": "bounded_local_csv_key_join_only",
        "counts": {
            "valuation_rows": len(v_rows),
            "valuation_distinct_nonnull_units": len(unique_val),
            "valuation_missing_id_rows": len(v_rows) - len(val_nonempty),
            "valuation_duplicate_id_rows": len(val_nonempty) - len(unique_val),
            "boundary_rows": len(b_rows),
            "boundary_rows_with_unit_id": sum(bool(_id(row.get("unit_of_property_id"))) for row in b_rows),
            "valuation_units_with_boundary_in_sample": len(unique_val & boundary_ids),
            "reference_rows": len(r_rows),
            "reference_invalid_key_rows": invalid_refs,
            "reference_duplicate_pairs": duplicate_ref_pairs,
            "valuation_units_with_building_reference_in_sample": len(with_ref),
            "valuation_units_with_multiple_linked_buildings": len(multi_roof),
            "current_outline_rows": len(o_rows),
            "current_outline_duplicate_building_ids": len(outline_ids) - len(outlined) - outline_ids.count(""),
            "valuation_units_with_linked_current_outline_in_sample": len(with_outline),
            "distinct_matched_current_outline_ids_in_sample": len(confirmed_outline_keys),
        },
        "cautions": {
            "inputs_may_be_unaligned_subsets": True,
            "source_release_or_vintage_alignment_verified": False,
            "links_do_not_prove_single_building_per_property": True,
            "valuation_is_not_replacement_cost_or_insured_tiv": True,
            "insured_exposure_admitted": False,
            "cat_model_input_admitted": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--valuations", type=Path, required=True)
    parser.add_argument("--boundaries", type=Path, required=True)
    parser.add_argument("--property-building-refs", type=Path, required=True)
    parser.add_argument("--outlines", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=25_000)
    args = parser.parse_args(argv)

    try:
        output = evaluate(
            _read_bounded_csv(args.valuations, ("unit_of_property_id",), args.max_rows),
            _read_bounded_csv(args.boundaries, ("source", "unit_of_property_id"), args.max_rows),
            _read_bounded_csv(args.property_building_refs, ("unit_of_property_id", "building_id"), args.max_rows),
            _read_bounded_csv(args.outlines, ("building_id",), args.max_rows),
        )
    except NZJoinPreflightError:
        print("BLOCKED: bounded LINZ CSV input did not satisfy required field/row contract", file=sys.stderr)
        return 2

    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
