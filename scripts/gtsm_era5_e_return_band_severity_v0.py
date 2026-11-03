# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only source return-band exceedance sizes by verified author prefix.

No station IDs, source coordinates, original water levels, or per-station
exception records are returned. Only after exact Zenodo and author Git blob
validation and full source ID+coordinate reconciliation in the caller.
"""
from __future__ import annotations

import math

if __package__:
    from .gtsm_era5_e_author_family_return_qa_v0 import (
        audit_return_levels_by_author_name_family, GtsmFamilyReturnAuditBlocked,
        FAMILIES, EXPECTED_SOURCE_ROWS, EXPECTED_PERIODS,
    )
    from .gtsm_era5_e_return_level_qa_v0 import FLOAT_TOLERANCE_METRES, RETURN_PERIODS
else:
    from gtsm_era5_e_author_family_return_qa_v0 import (
        audit_return_levels_by_author_name_family, GtsmFamilyReturnAuditBlocked,
        FAMILIES, EXPECTED_SOURCE_ROWS, EXPECTED_PERIODS,
    )
    from gtsm_era5_e_return_level_qa_v0 import FLOAT_TOLERANCE_METRES, RETURN_PERIODS


class OriginalBandSeverityBlocked(ValueError):
    """Publisher source/author pairing or band arithmetic invalid."""


BUCKETS = (
    "greater_than_0_to_0p01_m",
    "greater_than_0p01_to_0p1_m",
    "greater_than_0p1_to_1_m",
    "greater_than_1_m",
)


def bootstrap_percentiles_from_nominal_alpha(alpha: float) -> tuple[float, float]:
    """Mirror *historical source formula*, not a proof of producer runtime.

    pyextremes v2.3.1 model_mle.py uses np.quantile(rv_sample,
    [(1-alpha)/2, (1+alpha)/2]), with default n_samples=100 when the
    author's get_summary(..., alpha=0.95) call omits that argument.
    """
    if type(alpha) not in (float, int) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise OriginalBandSeverityBlocked("invalid nominal central CI alpha")
    return ((1 - alpha) * 50, (1 + alpha) * 50)


def _exceedance_bucket(metres: float) -> str:
    if not math.isfinite(metres) or metres <= FLOAT_TOLERANCE_METRES:
        raise OriginalBandSeverityBlocked("only strictly positive, finite exceedance accepted")
    if metres <= 0.01:
        return BUCKETS[0]
    if metres <= 0.1:
        return BUCKETS[1]
    if metres <= 1.0:
        return BUCKETS[2]
    return BUCKETS[3]


def audit_return_band_severity_by_family_and_year(
    station_ids: list[int],
    matrices: tuple[list[list[float]], list[list[float]], list[list[float]]],
    catalogue: dict[int, tuple[int, int, str]],
    *, expected_rows: int = EXPECTED_SOURCE_ROWS,
) -> dict[str, object]:
    """Classify native band crossings by author prefix, return year and size.

    The underlying original QA is executed again and reconciled per family;
    a best fit outside bootstrap percentile band is not automatically an error.
    """
    try:
        baseline = audit_return_levels_by_author_name_family(
            station_ids, matrices, catalogue, expected_rows=expected_rows
        )
    except GtsmFamilyReturnAuditBlocked as exc:
        raise OriginalBandSeverityBlocked("existing exact-family QA rejected source") from exc

    period_groups = {
        name: [
            {"return_period_years": RETURN_PERIODS[j],
             "above_reported_upper_cells": 0,
             "below_reported_lower_cells": 0,
             "missing_or_nonfinite_triplets": 0}
            for j in range(EXPECTED_PERIODS)
        ]
        for name in FAMILIES
    }
    severity_groups = {
        name: {direction: {bucket: 0 for bucket in BUCKETS}
               for direction in ("above_reported_upper", "below_reported_lower")}
        for name in FAMILIES
    }
    seen: set[int] = set()
    best, lower, upper = matrices
    for row_index, station_id in enumerate(station_ids):
        if type(station_id) is not int or station_id in seen:
            raise OriginalBandSeverityBlocked("original station IDs malformed")
        seen.add(station_id)
        row = catalogue.get(station_id)
        if type(row) is not tuple or len(row) != 3 or row[2] not in FAMILIES:
            raise OriginalBandSeverityBlocked("author station-name family unavailable")
        family = row[2]
        for j in range(EXPECTED_PERIODS):
            values = (best[row_index][j], lower[row_index][j], upper[row_index][j])
            if not all(math.isfinite(float(x)) for x in values):
                period_groups[family][j]["missing_or_nonfinite_triplets"] += 1
                continue
            center, lo, hi = map(float, values)
            if lo > hi + FLOAT_TOLERANCE_METRES:
                raise OriginalBandSeverityBlocked("inverted published interval needs separate review")
            if center > hi + FLOAT_TOLERANCE_METRES:
                period_groups[family][j]["above_reported_upper_cells"] += 1
                severity_groups[family]["above_reported_upper"][
                    _exceedance_bucket(center - hi)
                ] += 1
            if center + FLOAT_TOLERANCE_METRES < lo:
                period_groups[family][j]["below_reported_lower_cells"] += 1
                severity_groups[family]["below_reported_lower"][
                    _exceedance_bucket(lo - center)
                ] += 1

    by_family = baseline["station_family_quality_counts"]
    for family in FAMILIES:
        pairs = (
            ("above_reported_upper_cells", "bestfit_above_ninetyfive_percent_bound_cells",
             "above_reported_upper"),
            ("below_reported_lower_cells", "bestfit_below_five_percent_bound_cells",
             "below_reported_lower"),
        )
        for per_period_key, base_key, bucket_key in pairs:
            total = sum(p[per_period_key] for p in period_groups[family])
            if (total != by_family[family][base_key]
                    or sum(severity_groups[family][bucket_key].values()) != total):
                raise OriginalBandSeverityBlocked("source by-family crossing totals do not reconcile")
        if (sum(p["missing_or_nonfinite_triplets"] for p in period_groups[family])
                != by_family[family]["missing_or_nonfinite_triplets"]):
            raise OriginalBandSeverityBlocked("source family missingness totals do not reconcile")

    return {
        "schema_version": "gtsm-original-return-band-size-family-year-qa-v0",
        "native_return_period_years": list(RETURN_PERIODS),
        "original_station_rows": expected_rows,
        "by_author_name_family_and_return_year": period_groups,
        "band_exceedance_size_categories_m": severity_groups,
        "nominal_pyextremes_2p3p1_alpha_0p95_percentile_formula": [2.5, 97.5],
        "historical_model_mle_bootstrap_default_n_samples": 100,
        "historical_pyextremes_random_state_not_pinned_in_producer_script": True,
        "producer_exact_runtime_version_and_seeds_not_proven": True,
        "native_5perc_95perc_labels_not_reinterpreted": True,
        "author_family_name_not_physical_coast_validation": True,
        "individual_source_locations_or_levels_emitted": False,
        "original_provider_source_bytes_persisted": False,
        "commercial_rights_approved": False,
        "cat_model_admitted": False,
    }
