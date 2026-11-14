# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only Swiss crop-hail verification-support policies.

Portmann et al. (2024), NHESS 24, 2541-2558, sect. 2.4-2.5:
https://doi.org/10.5194/nhess-24-2541-2024

The published skill benchmark conditions the contingency table on grid cells
with nonzero crop exposure. Independently report positive observed damage
outside that support; never silently make those disappear from coverage
statistics. The "sensitivity" counts outside-support positives as misses
under the study's binary exposure-gated forecast, and is NOT a published
skill metric or an annual loss model.

No original confidential claims, raw coordinates, study code execution or
physical insured-loss amounts are used by this module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib


class Blocked(ValueError):
    """Invalid source proof or incompatible verification population."""


SOURCE_PROOF = (
    Path(__file__).resolve().parents[1]
    / "research/observations/swiss_crop_hail_original_24_crop_spatial_source_proof_v0.toml"
)
SCHEMA = "SWISS_CROP_HAIL_ORIGINAL_24_CROP_RESOLUTION_SPATIAL_SOURCE_PROOF_V0"
CROPS = {"barley", "field_crops", "grapevine", "maize", "rapeseed", "wheat"}
RESOLUTIONS_KM = {1, 2, 4, 8}


def _count(label: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise Blocked(f"{label} is not a nonnegative integer")
    return value


def _ratio(num: int, denom: int) -> float | None:
    return round(num / denom, 8) if denom else None


def contingency_metrics(tp: int, fp: int, fn: int, tn: int) -> dict[str, object]:
    """Return paper-style POD, FAR, FB, CSI, HSS without zero-denominator fiction."""
    a, b, c, d = (_count("tp", tp), _count("fp", fp),
                  _count("fn", fn), _count("tn", tn))
    hss_denom = (a + c) * (c + d) + (a + b) * (b + d)
    return {
        "hits": a, "false_alarms": b, "misses": c, "correct_negatives": d,
        "pod": _ratio(a, a + c),
        "far": _ratio(b, a + b),
        "frequency_bias": _ratio(a + b, a + c),
        "critical_success_index": _ratio(a, a + b + c),
        "heidke_skill_score": round(2 * (a * d - b * c) / hss_denom, 8)
        if hss_denom else None,
    }


def compare_verification_support(
    forecast: list[bool], observed: list[bool], has_exposure: list[bool]
) -> dict[str, object]:
    """Compare exact paper conditional support with a diagnostic observation union.

    Callers supply already aligned binary labels for identical event/grid
    coordinates. Predictions are restricted to nonzero-exposure cells.
    Out-of-exposure positive damage cannot be evaluated as a predicted hit
    under the source binary model; it appears as an additional miss in the
    *diagnostic*, which is not directly comparable to the paper's HSS.
    """
    if (not forecast or not (len(forecast) == len(observed) == len(has_exposure)) or
            any(type(x) is not bool for seq in (forecast, observed, has_exposure)
                for x in seq)):
        raise Blocked("requires nonempty equally sized boolean event/grid arrays")
    a = b = c = d = outside_positive = outside_negative = exposed_cells = 0
    for prediction, truth, exposure in zip(forecast, observed, has_exposure):
        if not exposure:
            if prediction:
                raise Blocked("binary crop forecast cannot predict outside crop exposure")
            if truth:
                outside_positive += 1
            else:
                outside_negative += 1
            continue
        exposed_cells += 1
        if prediction and truth:
            a += 1
        elif prediction and not truth:
            b += 1
        elif truth:
            c += 1
        else:
            d += 1
    if not exposed_cells:
        raise Blocked("no source crop exposure on verification population")
    reference = contingency_metrics(a, b, c, d)
    sensitivity = contingency_metrics(a, b, c + outside_positive, d)
    return {
        "policy_reference": "paper_nonzero_exposure_only",
        "paper_conditional_support": reference,
        "policy_diagnostic": "paper_support_plus_outside_exposure_positive_observations_only",
        "diagnostic_counts_missing_positives_as_misses": sensitivity,
        "outside_exposure_positive_observation_cells": outside_positive,
        "outside_exposure_negative_observation_cells_not_scored": outside_negative,
        "outside_observation_positive_cells_retained_in_audit": True,
        "reference_exposure_cell_count": exposed_cells,
        "diagnostic_population_is_not_fixed_full_geographic_extent": True,
        "model_annual_frequency_admitted": False,
        "model_insured_loss_severity_admitted": False,
    }


def source_proof_report(source: dict[str, object]) -> dict[str, object]:
    """Compute *coverage* only from original source receipt, not forecast skill."""
    if source.get("schema_version") != SCHEMA:
        raise Blocked("wrong pinned original-source evidence schema")
    for flag in ("raw_source_bytes_persisted", "raw_coordinates_published",
                 "rights_or_science_admitted", "yearly_oep_aep_ready"):
        if source.get(flag) is not False:
            raise Blocked("source evidence flags must be explicitly non-admission")
    rows = source.get("crop_resolution")
    if not isinstance(rows, list) or len(rows) != 24:
        raise Blocked("all 24 original crop/resolution source receipts required")
    actual_pairs = set()
    details = []
    sums = {
        "observed_positive_matrix_cells_across_pairs": 0,
        "outside_exposure_positive_matrix_cells_across_pairs": 0,
        "outside_exposure_positions_across_pairs": 0,
        "outside_exposure_positions_with_positive_impact_across_pairs": 0,
    }
    full = 0
    for row in rows:
        if not isinstance(row, dict):
            raise Blocked("invalid crop/resolution source receipt")
        crop, km = row.get("crop"), row.get("resolution_km")
        if crop not in CROPS or type(km) is not int or km not in RESOLUTIONS_KM:
            raise Blocked("unknown crop/resolution original source")
        if (crop, km) in actual_pairs:
            raise Blocked("duplicate crop/resolution original source")
        actual_pairs.add((crop, km))
        all_positive = _count("all positive", row.get("observed_impact_matrix_nonzero_cells"))
        outside = _count("outside positive", row.get("positive_impact_matrix_cells_on_unmatched_positions"))
        missing = _count("unmatched positions", row.get("unmatched_damage_positions"))
        missing_impacted = _count("unmatched impacted positions", row.get("unmatched_positions_with_positive_impact"))
        observed_events = _count("published selected event count", row.get("original_damage_event_count"))
        if (not (0 < observed_events <= 12) or outside > all_positive
                or missing_impacted > missing or
                (outside > observed_events * missing_impacted)
                or (missing_impacted > 0 and outside < missing_impacted)):
            raise Blocked("original sparse impact/coordinate conservation violated")
        is_full = row.get("full_spatial_key_coverage")
        if type(is_full) is not bool or is_full != (missing == 0):
            raise Blocked("original spatial support proof inconsistent")
        full += int(is_full)
        sums["observed_positive_matrix_cells_across_pairs"] += all_positive
        sums["outside_exposure_positive_matrix_cells_across_pairs"] += outside
        sums["outside_exposure_positions_across_pairs"] += missing
        sums["outside_exposure_positions_with_positive_impact_across_pairs"] += missing_impacted
        details.append({
            "crop": crop, "resolution_km": km,
            "selected_source_event_count": observed_events,
            "observed_positive_impact_matrix_cells": all_positive,
            "outside_2021_exposure_positive_impact_cells": outside,
            "outside_2021_exposure_positive_fraction_of_observations": _ratio(outside, all_positive),
            "within_2021_exposure_positive_fraction_of_observations": _ratio(all_positive - outside, all_positive),
            "source_position_coverage_complete": is_full,
        })
    if actual_pairs != {(crop, km) for crop in CROPS for km in RESOLUTIONS_KM}:
        raise Blocked("incomplete original source Cartesian crop/resolution set")
    for expected, given in (
        ("outside_exposure_positive_matrix_cells_across_pairs",
         "positive_impact_matrix_entries_on_unmatched_positions"),
        ("outside_exposure_positions_across_pairs",
         "unmatched_damage_raster_positions_across_pairs"),
        ("outside_exposure_positions_with_positive_impact_across_pairs",
         "unmatched_raster_positions_with_positive_observed_impact"),
    ):
        if sums[expected] != source.get(given):
            raise Blocked("aggregate totals differ from original source receipts")
    if full != source.get("full_damage_coordinate_coverage_pairs"):
        raise Blocked("source full join count inconsistent")
    details.sort(key=lambda x: (x["crop"], x["resolution_km"]))
    return {
        "schema_version": "oc-swiss-hail-paper-vs-full-coverage-v0",
        "original_workflow_run": source["workflow_run"],
        "original_source_scientific_status": "non_admitted",
        "paper_reference": "https://doi.org/10.5194/nhess-24-2541-2024",
        "crop_resolution_pairs": len(details),
        "fully_covered_pairs": full,
        "counts_are_grid_event_observations_not_unique_claims": True,
        **sums,
        "fraction_of_observed_positive_cells_outside_source_exposure": _ratio(
            sums["outside_exposure_positive_matrix_cells_across_pairs"],
            sums["observed_positive_matrix_cells_across_pairs"]
        ),
        "per_pair_coverage_only_not_skill": details,
        "paper_pod_far_hss_reproduced_from_original_hazard": False,
        "no_annual_event_probability_estimated": True,
        "no_insured_currency_loss_estimated": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-proof", type=Path, default=SOURCE_PROOF)
    args = parser.parse_args()
    try:
        with args.source_proof.open("rb") as handle:
            source = tomllib.load(handle)
        print(json.dumps(source_proof_report(source), sort_keys=True))
    except (OSError, ValueError, tomllib.TOMLDecodeError, KeyError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
