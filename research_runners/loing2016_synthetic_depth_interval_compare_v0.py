#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only interval consistency diagnostic for DDT45 2021 Loing atlas.

This is NOT independent validation or observed 2016 source data. It imports
the canonical source edition/class bounds; no depth midpoints, geospatial
interpolation, claims or CAT model admissions are generated.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

from research_runners.loing2016_azi_depth_class_semantics_v0 import (
    AtlasClassBlocked, review_azi_class,
)


class IntervalComparisonBlocked(ValueError):
    """Missing or scientifically inadmissible comparison input."""


_EXPECTED_EXPERIMENT = "SYNTHETIC_ONLY_NO_OBSERVED_PROVIDER_BYTES"
_EXPECTED_VERSION = "DDT45_LOING_AVAL_AZI_2021"
_EXPECTED_EVENT = "LOING_MAY_JUNE_2016"
_PREDICTION = re.compile(r"(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,3})?")
_CELL_ID = re.compile(r"SYN_[A-Z0-9_]{1,45}")


def _unique_keys(pairs):
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise IntervalComparisonBlocked("duplicate metadata key")
        obj[name] = value
    return obj


def _reject_nonfinite(_value):
    raise IntervalComparisonBlocked("nonfinite JSON number")


def _synthetic_prediction(value):
    # Strings preserve decimal precision and reject booleans, NaN and floats.
    if not isinstance(value, str) or not _PREDICTION.fullmatch(value):
        raise IntervalComparisonBlocked("finite nonnegative decimal metres string required")
    try:
        depth = Decimal(value)
    except InvalidOperation as exc:
        raise IntervalComparisonBlocked("invalid predicted depth") from exc
    if depth > Decimal("50"):
        raise IntervalComparisonBlocked("synthetic prediction exceeds bounded scope")
    return depth


def compare_synthetic_intervals(envelope):
    if not isinstance(envelope, dict) or set(envelope) != {
        "experiment", "atlas_version", "event_id", "synthetic_rows"
    }:
        raise IntervalComparisonBlocked("required experiment/version/event/rows only")
    if envelope["experiment"] != _EXPECTED_EXPERIMENT:
        raise IntervalComparisonBlocked("real source arrays or model claims not admitted")
    if envelope["atlas_version"] != _EXPECTED_VERSION or envelope["event_id"] != _EXPECTED_EVENT:
        raise IntervalComparisonBlocked("wrong edition or historical event")
    rows = envelope["synthetic_rows"]
    if not isinstance(rows, list) or not (1 <= len(rows) <= 100):
        raise IntervalComparisonBlocked("bounded synthetic rows required")
    seen = set()
    output = []
    distances = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "synthetic_cell_id", "depth_class", "predicted_depth_m"
        }:
            raise IntervalComparisonBlocked("unreviewed/missing synthetic row fields")
        cell_id = row["synthetic_cell_id"]
        if not isinstance(cell_id, str) or not _CELL_ID.fullmatch(cell_id):
            raise IntervalComparisonBlocked("only synthetic anonymized cell identifiers permitted")
        if cell_id in seen:
            raise IntervalComparisonBlocked("duplicate synthetic cell")
        seen.add(cell_id)
        depth = _synthetic_prediction(row["predicted_depth_m"])
        try:
            category = review_azi_class({
                "atlas_version": _EXPECTED_VERSION,
                "event_id": _EXPECTED_EVENT,
                "depth_class": row["depth_class"],
            })
        except AtlasClassBlocked as exc:
            raise IntervalComparisonBlocked("unknown or ambiguous provider depth class") from exc
        lower = Decimal(category["lower_depth_class_boundary_m"])
        upper_label = category["upper_depth_class_boundary_m"]
        upper = Decimal(upper_label) if upper_label is not None else None
        if depth < lower:
            relation = "below_interval"
            gap = lower - depth
        elif upper is not None and depth > upper:
            relation = "above_interval"
            gap = depth - upper
        elif depth == lower or (upper is not None and depth == upper):
            # The original legend's endpoint inclusion has not been proven.
            relation = "on_boundary_inclusion_unresolved"
            gap = Decimal(0)
        else:
            relation = "within_interval_not_verified_observation"
            gap = Decimal(0)
        distances.append(gap)
        output.append({
            "synthetic_cell_id": cell_id,
            "source_depth_class": row["depth_class"],
            "predicted_depth_m": str(depth),
            "class_lower_boundary_m": str(lower),
            "class_upper_boundary_m": str(upper) if upper is not None else None,
            "interval_relation": relation,
            "distance_outside_interval_m": str(gap),
            "is_independent_flood_validation": False,
            "is_precise_observed_building_depth": False,
        })
    distance_sum = sum(distances, Decimal(0))
    return {
        "profile": "loing2016-ddt2021-interval-consistency-synthetic-v0",
        "experiment": _EXPECTED_EXPERIMENT,
        "atlas_version": _EXPECTED_VERSION,
        "synthetic_cells_checked": len(output),
        "synthetic_cells_outside_intervals": sum(x > 0 for x in distances),
        "sum_distance_outside_intervals_m": str(distance_sum),
        "max_distance_outside_intervals_m": str(max(distances)),
        "per_cell": output,
        "independent_observed_flood_holdout_verified": False,
        "original_atlas_geometry_or_depth_bytes_authenticated": False,
        "source_rights_and_calibration_lineage_established": False,
        "terrain_or_building_depth_inferred": False,
        "probabilistic_hazard_or_flood_return_period_validated": False,
        "insured_loss_or_gross_net_curve_permitted": False,
        "interpretation": "synthetic_software_regression_only_no_real_model_skill_inference",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-json", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = args.synthetic_json
        if not path.is_file() or path.stat().st_size > 16384:
            raise IntervalComparisonBlocked("local synthetic input missing or oversized")
        body = json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_keys,
                          parse_constant=_reject_nonfinite)
        result = compare_synthetic_intervals(body)
    except (IntervalComparisonBlocked, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
