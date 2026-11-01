# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, fail-closed CAL FIRE DINS event-year inspection-count QA.

Consumes only an independently prepared *aggregate*, never feature rows.
Does not fetch provider records, reconstruct addresses, calculate financial loss,
estimate the number of exposed buildings, or authorize use as a model input.

A privacy threshold reduces direct small-cell publication; it is not a guarantee
against attacks by differencing multiple releases or auxiliary information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SOURCE_ID = "us.calfire.dins.structure-damage"
FRAME = "calfire_dins_inspected_structures"
DAMAGE_STATES = frozenset({
    "Destroyed (>50%)",
    "Major (25-50%)",
    "Minor (10-25%)",
    "Affected (>0-10%)",
    "Inaccessible",
    "No Damage",
})
TOP_KEYS = frozenset({
    "schema_version", "source_id", "event_year", "origin",
    "source_snapshot_sha256", "inspection_frame", "damage_counts",
    "contains_feature_rows",
})
MAX_BYTES = 16384
MIN_PUBLIC_NONZERO_CELL = 10
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class DinsAggregateError(ValueError):
    """Malformed, identifying, untraceable, or scientifically unsafe aggregate."""


def _unique_object(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise DinsAggregateError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise DinsAggregateError("nonfinite JSON constant forbidden")


def evaluate_aggregate(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise DinsAggregateError("aggregate input byte size out of bounds")
    try:
        obj = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DinsAggregateError("invalid UTF-8 JSON aggregate") from exc
    if type(obj) is not dict or set(obj) != TOP_KEYS:
        raise DinsAggregateError("unexpected top-level fields or source feature rows")
    if obj["schema_version"] != "1.0.0" or obj["source_id"] != SOURCE_ID:
        raise DinsAggregateError("source contract identity mismatch")
    year = obj["event_year"]
    if type(year) is not int or not 2013 <= year <= 2100:
        raise DinsAggregateError("invalid event year")
    if obj["inspection_frame"] != FRAME or obj["contains_feature_rows"] is not False:
        raise DinsAggregateError("unreviewed inspection frame or feature rows included")
    origin = obj["origin"]
    digest = obj["source_snapshot_sha256"]
    if origin == "synthetic":
        if digest is not None:
            raise DinsAggregateError("synthetic records must not claim original source hash")
    elif origin == "externally_prepared_aggregate":
        if type(digest) is not str or not SHA256_RE.fullmatch(digest):
            raise DinsAggregateError("external aggregate requires syntactically valid source SHA")
    else:
        raise DinsAggregateError("unrecognized aggregate provenance")
    counts = obj["damage_counts"]
    if type(counts) is not dict or set(counts) != DAMAGE_STATES:
        raise DinsAggregateError("unexpected or missing DINS damage states")
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise DinsAggregateError("counts must be nonnegative integers, not booleans")
    count = sum(counts.values())
    if count == 0:
        raise DinsAggregateError("empty inspected sample")
    if year < 2018 and counts["No Damage"] != 0:
        raise DinsAggregateError("pre-2018 no-damage cohort is not comparable")
    # If any nonzero published category would be individually identifying,
    # suppress the entire distribution (and total) to prevent subtraction.
    small_cell = any(0 < value < MIN_PUBLIC_NONZERO_CELL for value in counts.values())
    suppressed = count < MIN_PUBLIC_NONZERO_CELL or small_cell
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_id": SOURCE_ID,
        "event_year": year,
        "origin": origin,
        "inspection_frame": FRAME,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "source_snapshot_hash_supplied_but_not_verified": origin != "synthetic",
        "counts_suppressed": suppressed,
        "pre_2018_non_damage_records_not_collected": year < 2018,
        "selection_bias_unresolved": True,
        "exposure_population_denominator_available": False,
        "financial_loss_inferred": False,
        "vulnerability_probability_inferred": False,
        "model_data_admitted": False,
    }
    if not suppressed:
        result["inspected_record_count_not_exposure_denominator"] = count
        result["damage_counts_within_inspected_frame"] = {
            key: counts[key] for key in sorted(DAMAGE_STATES)
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        result = evaluate_aggregate(raw)
    except (OSError, DinsAggregateError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
