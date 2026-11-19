# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two *fictional* sub-county TWIA allocation priors, not insured locations.

Consumes only locally normalized Q4-2025 carrier county/class marginals that pass
TWIA's existing research reconciler. The three zones are invented labels, not
GIS cells, coast-distance bands, OED locations, or real insured buildings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCENARIOS = {"distributed": (1, 1, 1), "concentrated": (8, 2, 1)}
ZONE_IDS = ("fictional-zone-1", "fictional-zone-2", "fictional-zone-3")
MEASURES = (
    "policies_in_force", "risks_in_force", "direct_liability_usd",
    "indirect_liability_usd", "ytd_written_premium_usd",
)


class SyntheticAllocationError(ValueError):
    """Inputs or derived zones cannot support the claimed aggregate constraints."""


def apportion_integer(amount: int, weights: tuple[int, ...]) -> list[int]:
    """Conservative largest remainder integer split; leftmost tie-break."""
    if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
        raise SyntheticAllocationError("nonnegative integer amount required")
    if not weights or any(isinstance(w, bool) or not isinstance(w, int) or w < 0 for w in weights):
        raise SyntheticAllocationError("nonnegative integer weight vector required")
    total_weight = sum(weights)
    if not total_weight:
        if amount:
            raise SyntheticAllocationError("cannot allocate positive amount with no weights")
        return [0] * len(weights)
    q = [amount * w // total_weight for w in weights]
    residual = amount - sum(q)
    rank = sorted(range(len(weights)), key=lambda i: (-(amount * weights[i] % total_weight), i))
    for i in rank[:residual]:
        q[i] += 1
    assert sum(q) == amount
    return q


def _validate_rows(rows: list[dict[str, Any]]) -> None:
    # Always recheck the essential invariants even if this function is called
    # directly rather than through the existing source-format reconciler.
    from twia_liability_2025_reconciliation_v0 import COUNTIES, CLASSES
    keys = set()
    for row in rows:
        key = (row.get("county"), row.get("policy_class"))
        if key in keys or key[0] not in COUNTIES or key[1] not in CLASSES:
            raise SyntheticAllocationError("invalid or duplicate county/class")
        keys.add(key)
        if any(isinstance(row.get(m), bool) or not isinstance(row.get(m), int) or row[m] < 0 for m in MEASURES):
            raise SyntheticAllocationError("only nonnegative integer reporting metrics")
        if row["risks_in_force"] < row["policies_in_force"]:
            raise SyntheticAllocationError("risks in force smaller than policies")
        if row["direct_liability_usd"] and row["risks_in_force"] == 0:
            raise SyntheticAllocationError("positive direct liability with zero reported risks")
    if len(keys) != len(COUNTIES) * len(CLASSES):
        raise SyntheticAllocationError("require all 45 county/class source cells")


def allocate_two_priors(
    rows: list[dict[str, Any]],
    *,
    source_audit: dict[str, Any],
) -> dict[str, Any]:
    """Return two alternative self-consistent hypothetical allocations.

    The same observed marginals are respected separately in each world;
    different worlds must never be aggregated together.
    """
    _validate_rows(rows)
    if source_audit.get("reconciled_at_normalized_grain") is not True:
        raise SyntheticAllocationError("source marginals did not reconcile")
    if source_audit.get("report_as_of") != "2025-12-31":
        raise SyntheticAllocationError("wrong source vintage")
    for key in ("normalization_county_sha256", "normalization_class_sha256"):
        digest = source_audit.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise SyntheticAllocationError("missing exact normalized-source digest")
    output_scenarios = []
    ordered_rows = sorted(rows, key=lambda r: (r["county"], r["policy_class"]))
    for scenario, weights in SCENARIOS.items():
        cells = []
        for source in ordered_rows:
            p = apportion_integer(source["policies_in_force"], weights)
            extra = apportion_integer(source["risks_in_force"] - source["policies_in_force"], weights)
            risks = [p[i] + extra[i] for i in range(3)]
            # Direct liability is a reported insurance limit, not physical building TIV.
            # It can be apportioned by hypothetical risk-unit counts, not a location claim.
            direct = apportion_integer(source["direct_liability_usd"], tuple(risks))
            # YTD premiums are historical financial flows, not the in-force risk book;
            # avoid falsely making them zero merely because risk count became zero.
            indirect = apportion_integer(source["indirect_liability_usd"], weights)
            premium = apportion_integer(source["ytd_written_premium_usd"], weights)
            for i, zone_id in enumerate(ZONE_IDS):
                cells.append({
                    "county": source["county"],
                    "policy_class": source["policy_class"],
                    "hypothetical_zone": zone_id,
                    "policies_in_force": p[i],
                    "risks_in_force": risks[i],
                    "direct_liability_usd": direct[i],
                    "indirect_liability_usd": indirect[i],
                    "ytd_written_premium_usd": premium[i],
                })
            subset = cells[-3:]
            if any(sum(cell[m] for cell in subset) != source[m] for m in MEASURES):
                raise SyntheticAllocationError("county/class total is not conserved")
            if any(c["risks_in_force"] < c["policies_in_force"] for c in subset):
                raise SyntheticAllocationError("risk-policy constraint broken")
            if any(c["risks_in_force"] == 0 and c["direct_liability_usd"] > 0 for c in subset):
                raise SyntheticAllocationError("direct limit assigned without reported risk")
        for measure in MEASURES:
            if sum(c[measure] for c in cells) != sum(r[measure] for r in rows):
                raise SyntheticAllocationError("scenario grand totals drifted")
        output_scenarios.append({
            "scenario": scenario,
            "hypothetical_weights": list(weights),
            "cells": cells,
        })
    different = any(a != b for a, b in zip(
        output_scenarios[0]["cells"], output_scenarios[1]["cells"]
    ))
    return {
        "profile": "twia-2025-12-31-two-fictional-microzone-priors-v0",
        "insurer": "Texas Windstorm Insurance Association",
        "source_report_as_of": "2025-12-31",
        "source_normalized_sha256": {
            "county": source_audit["normalization_county_sha256"],
            "county_class": source_audit["normalization_class_sha256"],
        },
        "source_control_mode": source_audit["mode"],
        "geography": "15 TWIA-covered county names; Harris is eligible subset only",
        "peril_scope": "TWIA property wind/hail (not flood or surge)",
        "scenario_count": 2,
        "zone_count_per_county_class": 3,
        "scenarios_are_distinct": different,
        "worlds_are_mutually_exclusive": True,
        "source_marginals_conserved": True,
        "all_buildings_have_observed_coordinates": False,
        "synthetic_zones_are_geospatial": False,
        "exposure_is_observed_insured_tiv": False,
        "scenario_is_insurer_real_portfolio": False,
        "original_provider_bytes_verified": False,
        "commercial_data_rights_approved": False,
        "model_input_approved": False,
        "oasis_oed_ready": False,
        "cat_hazard_vulnerability_calibrated": False,
        "actual_reinsurance_terms_verified": False,
        "note": "Synthetic alternative marginals only. Zone labels have no geometry, boundary or geographic direction; no asset coordinates, OED location mapping or insured building population inferred.",
        "scenarios": output_scenarios,
    }


def allocate_from_csv(county_csv: Path, class_csv: Path, *, mode: str) -> dict[str, Any]:
    from twia_liability_2025_reconciliation_v0 import (
        _read_csv, CLASS_FIELDS, reconcile,
    )
    audit = reconcile(county_csv, class_csv, mode=mode)
    if not audit["reconciled_at_normalized_grain"]:
        raise SyntheticAllocationError("reconciliation failed: no synthetic allocation allowed")
    rows, digest = _read_csv(class_csv, CLASS_FIELDS, "county_class")
    if digest != audit["normalization_class_sha256"]:
        raise SyntheticAllocationError("source changed after reconciliation")
    return allocate_two_priors(rows, source_audit=audit)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--county-csv", type=Path, required=True)
    parser.add_argument("--county-class-csv", type=Path, required=True)
    parser.add_argument("--mode", choices=("synthetic", "published-2025"), default="synthetic")
    parser.add_argument("--output-json", type=Path, required=True,
                        help="Create-only absolute file outside repository; never commit")
    args = parser.parse_args()
    if not args.output_json.is_absolute():
        parser.error("output must be an absolute path outside the repository")
    repo_root = Path(__file__).resolve().parents[1]
    resolved_output = args.output_json.parent.resolve(strict=True) / args.output_json.name
    if repo_root == resolved_output.parent or repo_root in resolved_output.parents:
        parser.error("output must be outside Git checkout")
    package = allocate_from_csv(args.county_csv, args.county_class_csv, mode=args.mode)
    with resolved_output.open("x", encoding="utf-8") as stream:
        json.dump(package, stream, sort_keys=True, indent=2)
        stream.write("\n")
    # No company source records or synthetic subcounty allocations in stdout.
    print(json.dumps({
        "output_sha256": hashlib.sha256(resolved_output.read_bytes()).hexdigest(),
        "scenario_count": len(package["scenarios"]),
        "cells_per_scenario": len(package["scenarios"][0]["cells"]),
        "distinct_scenarios": package["scenarios_are_distinct"],
        "model_input_approved": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
