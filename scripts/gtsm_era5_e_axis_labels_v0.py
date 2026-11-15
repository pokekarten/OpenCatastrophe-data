# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded native probability/return-period axis labels from a prevalidated GTSM source.

This script reads two tiny coordinate axes only, not sea-level measurement grids.
"""
from __future__ import annotations

import math
from pathlib import Path

SOURCE_QUANTILE_COUNT = 7
SOURCE_RETURN_COUNT = 8
PAPER_PERCENTILE_LEVELS = (1, 5, 10, 25, 50, 75, 90, 95, 99)
PAPER_RETURN_YEARS = (1, 2, 5, 10, 25, 50, 75, 100)


class NativeAxesBlocked(ValueError):
    """Source axis content, order or release-specific coordinate labels invalid."""


def inspect_level_labels(quantiles: list[float], return_years: list[int]) -> dict[str, object]:
    """Only metadata coordinates; never infer missing percentiles or water levels."""
    if type(quantiles) is not list or type(return_years) is not list:
        raise NativeAxesBlocked("axis labels must be concrete native scalar lists")
    if len(quantiles) != SOURCE_QUANTILE_COUNT or len(return_years) != SOURCE_RETURN_COUNT:
        raise NativeAxesBlocked("GTSM published statistical axis lengths drifted")
    if any(type(x) not in (float, int) or not math.isfinite(x) for x in quantiles):
        raise NativeAxesBlocked("quantile coordinate contains malformed/non-finite scalars")
    if any(type(x) is not int for x in return_years):
        raise NativeAxesBlocked("return-period axis must contain native integer years")
    if any(a >= b for a, b in zip(quantiles, quantiles[1:])):
        raise NativeAxesBlocked("quantile labels must be strictly ascending")
    if any(a >= b for a, b in zip(return_years, return_years[1:])):
        raise NativeAxesBlocked("return-period labels must be strictly ascending")
    if tuple(return_years) != PAPER_RETURN_YEARS:
        raise NativeAxesBlocked("native return-period labels conflict with exact public paper")
    if all(0 < v < 1 for v in quantiles):
        inferred_encoding = "unit_fraction_candidate"
        percent_labels = [round(v * 100, 6) for v in quantiles]
    elif all(0 < v < 100 for v in quantiles):
        inferred_encoding = "percentage_candidate"
        percent_labels = [round(v, 6) for v in quantiles]
    else:
        inferred_encoding = "unknown"
        percent_labels = []
    paper_set = set(PAPER_PERCENTILE_LEVELS)
    probable_missing = (
        [v for v in PAPER_PERCENTILE_LEVELS if v not in percent_labels] if percent_labels else []
    )
    probable_extra = (
        [v for v in percent_labels if v not in paper_set] if percent_labels else []
    )
    return {
        "schema_version": "gtsm-statistics-axis-label-audit-v0",
        "observed_quantile_labels_native": [float(v) for v in quantiles],
        "observed_return_period_years": list(return_years),
        "paper_declared_percentiles": list(PAPER_PERCENTILE_LEVELS),
        "native_quantile_count": SOURCE_QUANTILE_COUNT,
        "paper_quantile_count": len(PAPER_PERCENTILE_LEVELS),
        "quantile_encoding_hypothesis": inferred_encoding,
        "candidate_missing_paper_percentiles": probable_missing,
        "candidate_additional_native_percentiles": probable_extra,
        "quantile_semantics_reviewed": False,
        "raw_hazard_grids_read": False,
        "raw_coastal_position_records_read": False,
        "data_rights_approved": False,
        "cat_model_admitted": False,
    }


def inspect_original_level_labels(path: Path) -> dict[str, object]:
    """Read 15 axis labels after full original hash+schema verification upstream."""
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise NativeAxesBlocked("pinned NetCDF acquisition dependency missing") from exc
    try:
        with Dataset(path.as_posix(), mode="r") as ds:
            q_var = ds.variables["quantile"]
            r_var = ds.variables["return_period"]
            if (q_var.dimensions != ("quantile",) or str(q_var.dtype) != "float64"
                    or r_var.dimensions != ("return_period",) or str(r_var.dtype) != "int64"):
                raise NativeAxesBlocked("GTSM original scalar statistical axes differ from expected")
            if (len(ds.dimensions["quantile"]) != SOURCE_QUANTILE_COUNT
                    or len(ds.dimensions["return_period"]) != SOURCE_RETURN_COUNT):
                raise NativeAxesBlocked("source scalar statistical axis lengths drifted")
            q_var.set_auto_maskandscale(False)
            r_var.set_auto_maskandscale(False)
            quantiles = q_var[:].tolist()
            periods = r_var[:].tolist()
    except NativeAxesBlocked:
        raise
    except Exception as exc:
        raise NativeAxesBlocked("unable to inspect original statistical axis labels") from exc
    return inspect_level_labels(quantiles, periods)
