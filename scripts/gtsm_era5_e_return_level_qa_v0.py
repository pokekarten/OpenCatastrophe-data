# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only quality audit of pinned GTSM original return-level statistics.

Never emits original water levels, station IDs, positions or source grids.
Do not interpret this evidence as flood depth, insurance loss or model admission.
"""
from __future__ import annotations

import math
from pathlib import Path

EXPECTED_STATIONS = 38_957
EXPECTED_PERIODS = 8
RETURN_PERIODS = (1, 2, 5, 10, 25, 50, 75, 100)
SOURCES = ("wl_extreme_bestfit", "wl_extreme_5perc", "wl_extreme_95perc")
FLOAT_TOLERANCE_METRES = 1e-9


class ReturnLevelAuditBlocked(ValueError):
    """Original release axes or native numeric matrix are not auditable."""


def audit_return_levels(
    bestfit: list[list[float]], lower: list[list[float]], upper: list[list[float]],
    *, expected_stations: int = EXPECTED_STATIONS,
    expected_periods: int = EXPECTED_PERIODS,
) -> dict[str, object]:
    """Count missing, uncertainty-order and within-row return-level anomalies.

    Synthetic tests may set small exact dimensions. Production caller always uses
    the pinned original's 38,957 x 8 native matrices.
    """
    if (type(expected_stations) is not int or type(expected_periods) is not int
            or not 1 <= expected_stations <= EXPECTED_STATIONS
            or not 1 <= expected_periods <= EXPECTED_PERIODS):
        raise ReturnLevelAuditBlocked("invalid declared bounded matrix dimensions")
    matrices = (bestfit, lower, upper)
    if any(type(matrix) is not list or len(matrix) != expected_stations for matrix in matrices):
        raise ReturnLevelAuditBlocked("native station dimension mismatch")

    valid_numeric_triplets = 0
    missing_or_nonfinite_triplets = 0
    inverted_uncertainty_interval = 0
    bestfit_below_lower = 0
    bestfit_above_upper = 0
    descending_bestfit_adjacent_periods = 0
    fully_clean_station_rows = 0
    rows_with_any_nonfinite = 0
    rows_with_any_interval_conflict = 0
    rows_with_any_nonmonotonic_bestfit = 0

    for station in range(expected_stations):
        rows = tuple(matrix[station] for matrix in matrices)
        if any(type(row) is not list or len(row) != expected_periods for row in rows):
            raise ReturnLevelAuditBlocked("return-period axis or station row malformed")
        converted = []
        for row in rows:
            if any(type(x) not in (float, int) for x in row):
                raise ReturnLevelAuditBlocked("non-numeric native return-level cell")
            converted.append([float(x) for x in row])
        best, low, high = converted
        bad_nonfinite = False
        bad_interval = False
        bad_monotonic = False

        for period_index in range(expected_periods):
            triple = (best[period_index], low[period_index], high[period_index])
            if not all(math.isfinite(x) for x in triple):
                missing_or_nonfinite_triplets += 1
                bad_nonfinite = True
                continue
            valid_numeric_triplets += 1
            if low[period_index] > high[period_index] + FLOAT_TOLERANCE_METRES:
                inverted_uncertainty_interval += 1
                bad_interval = True
            if best[period_index] + FLOAT_TOLERANCE_METRES < low[period_index]:
                bestfit_below_lower += 1
                bad_interval = True
            if best[period_index] > high[period_index] + FLOAT_TOLERANCE_METRES:
                bestfit_above_upper += 1
                bad_interval = True
        for period_index in range(1, expected_periods):
            prior, current = best[period_index-1:period_index+1]
            if (math.isfinite(prior) and math.isfinite(current)
                    and current + FLOAT_TOLERANCE_METRES < prior):
                descending_bestfit_adjacent_periods += 1
                bad_monotonic = True
        rows_with_any_nonfinite += int(bad_nonfinite)
        rows_with_any_interval_conflict += int(bad_interval)
        rows_with_any_nonmonotonic_bestfit += int(bad_monotonic)
        fully_clean_station_rows += int(not (bad_nonfinite or bad_interval or bad_monotonic))

    return {
        "schema_version": "gtsm-original-extreme-return-level-qa-v0",
        "original_station_rows": expected_stations,
        "original_return_period_slots": expected_periods,
        "return_period_years_source_checked_upstream": list(RETURN_PERIODS),
        "return_level_cells_per_variable": expected_stations * expected_periods,
        "numeric_finite_triplets": valid_numeric_triplets,
        "missing_or_nonfinite_triplets": missing_or_nonfinite_triplets,
        "inverted_uncertainty_interval_cells": inverted_uncertainty_interval,
        "bestfit_below_five_percent_bound_cells": bestfit_below_lower,
        "bestfit_above_ninetyfive_percent_bound_cells": bestfit_above_upper,
        "descending_bestfit_adjacent_period_pairs": descending_bestfit_adjacent_periods,
        "stations_with_missing_or_nonfinite_triplet": rows_with_any_nonfinite,
        "stations_with_uncertainty_interval_conflict": rows_with_any_interval_conflict,
        "stations_with_descending_bestfit_periods": rows_with_any_nonmonotonic_bestfit,
        "stations_without_any_these_quality_flags": fully_clean_station_rows,
        "comparison_tolerance_m": FLOAT_TOLERANCE_METRES,
        "per_station_values_emitted": False,
        "provider_sea_level_values_redistributed": False,
        "sea_level_to_inundation_transform_performed": False,
        "statistical_fit_validated": False,
        "vertical_datum_validated": False,
        "commercial_rights_approved": False,
        "cat_model_admitted": False,
    }


def audit_original_return_levels(path: Path) -> dict[str, object]:
    """Only after caller's SHA-256, native header and year-axis gates pass."""
    try:
        import numpy as np
        from netCDF4 import Dataset
    except ImportError as exc:
        raise ReturnLevelAuditBlocked("isolated pinned scientific netCDF4 environment required") from exc
    try:
        with Dataset(path.as_posix(), mode="r") as dataset:
            if (set(dataset.dimensions) != {"stations", "quantile", "return_period"}
                    or len(dataset.dimensions["stations"]) != EXPECTED_STATIONS
                    or len(dataset.dimensions["return_period"]) != EXPECTED_PERIODS):
                raise ReturnLevelAuditBlocked("native original GTSM matrix shape changed")
            matrices = []
            for name in SOURCES:
                var = dataset.variables[name]
                if (var.dimensions != ("stations", "return_period")
                        or str(var.dtype) != "float64"):
                    raise ReturnLevelAuditBlocked("original extreme-level schema changed")
                var.set_auto_maskandscale(False)
                values = np.asarray(var[:], dtype=np.float64)
                if values.shape != (EXPECTED_STATIONS, EXPECTED_PERIODS):
                    raise ReturnLevelAuditBlocked("source native return-level matrix dimensions changed")
                for attr in ("_FillValue", "missing_value"):
                    if attr in var.ncattrs():
                        marker = np.asarray(var.getncattr(attr))
                        if marker.ndim != 0 or not np.isfinite(marker).all():
                            raise ReturnLevelAuditBlocked("unsafe original missing-data marker")
                        values[values == float(marker)] = np.nan
                matrices.append(values.tolist())
    except ReturnLevelAuditBlocked:
        raise
    except Exception as exc:
        raise ReturnLevelAuditBlocked(
            "failed bounded read of original GTSM return-level matrices (error type: "
            + type(exc).__name__ + ")"
        ) from exc
    return audit_return_levels(*matrices)
