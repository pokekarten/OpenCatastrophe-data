# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Return-level original-data QA stratified by the pinned author station-name family.

Original NetCDF / author TSV must be independently hash-verified upstream.
The station-name prefix is a producer convention, not independent coastline
geolocation or inundation validation. Never emit station IDs, coordinates,
original levels, positions or station-level exception records.
"""
from __future__ import annotations

from pathlib import Path

if __package__:
    from .gtsm_era5_e_return_level_qa_v0 import (
        audit_return_levels, ReturnLevelAuditBlocked, SOURCES, RETURN_PERIODS,
    )
else:
    from gtsm_era5_e_return_level_qa_v0 import (
        audit_return_levels, ReturnLevelAuditBlocked, SOURCES, RETURN_PERIODS,
    )

EXPECTED_SOURCE_ROWS = 38_957
EXPECTED_PERIODS = 8
FAMILIES = (
    "coast_name_prefix",
    "regular_grid_name_prefix",
    "observation_name_prefix",
    "other_name_prefix",
)

COUNTER_FIELDS = (
    "original_station_rows",
    "numeric_finite_triplets",
    "missing_or_nonfinite_triplets",
    "inverted_uncertainty_interval_cells",
    "bestfit_below_five_percent_bound_cells",
    "bestfit_above_ninetyfive_percent_bound_cells",
    "descending_bestfit_adjacent_period_pairs",
    "stations_with_missing_or_nonfinite_triplet",
    "stations_with_uncertainty_interval_conflict",
    "stations_with_descending_bestfit_periods",
    "stations_without_any_these_quality_flags",
)


class GtsmFamilyReturnAuditBlocked(ValueError):
    """Source-native matrices or published author family labels are inconsistent."""


def audit_return_levels_by_author_name_family(
    source_station_ids: list[int],
    matrices: tuple[list[list[float]], list[list[float]], list[list[float]]],
    author_catalogue: dict[int, tuple[int, int, str]],
    *, expected_rows: int = EXPECTED_SOURCE_ROWS,
) -> dict[str, object]:
    """Cross-tab four producer station-name families with existing full QA.

    Zero station-ID/key/value disclosures. Original 38,957x8 schema pinned in
    the caller; tests pass bounded synthetic dimensions.
    """
    if (type(expected_rows) is not int or not 1 <= expected_rows <= EXPECTED_SOURCE_ROWS
            or type(source_station_ids) is not list
            or len(source_station_ids) != expected_rows
            or type(matrices) is not tuple or len(matrices) != len(SOURCES)
            or type(author_catalogue) is not dict or not author_catalogue):
        raise GtsmFamilyReturnAuditBlocked("source/author original family QA dimensions invalid")
    if any(type(matrix) is not list or len(matrix) != expected_rows for matrix in matrices):
        raise GtsmFamilyReturnAuditBlocked("native source return-level matrix rows changed")
    try:
        whole = audit_return_levels(*matrices, expected_stations=expected_rows)
    except ReturnLevelAuditBlocked as exc:
        raise GtsmFamilyReturnAuditBlocked("source-native return-level QA rejected") from exc

    grouped = {family: ([], [], []) for family in FAMILIES}
    seen_ids: set[int] = set()
    for row_idx, identifier in enumerate(source_station_ids):
        if type(identifier) is not int or not 0 <= identifier <= 65_535:
            raise GtsmFamilyReturnAuditBlocked("invalid original source native station ID")
        if identifier in seen_ids:
            raise GtsmFamilyReturnAuditBlocked("duplicate original source native station ID")
        seen_ids.add(identifier)
        author_row = author_catalogue.get(identifier)
        if (type(author_row) is not tuple or len(author_row) != 3
                or author_row[2] not in FAMILIES):
            raise GtsmFamilyReturnAuditBlocked("verified producer station-name family unavailable")
        category = grouped[author_row[2]]
        for source_index, matrix in enumerate(matrices):
            category[source_index].append(matrix[row_idx])

    by_family: dict[str, dict[str, object]] = {}
    for family in FAMILIES:
        groups = grouped[family]
        count = len(groups[0])
        if any(len(part) != count for part in groups):
            raise GtsmFamilyReturnAuditBlocked("cross-family source matrix row reconciliation failed")
        if not count:
            by_family[family] = {key: 0 for key in COUNTER_FIELDS}
            continue
        try:
            result = audit_return_levels(
                *groups, expected_stations=count, expected_periods=EXPECTED_PERIODS,
            )
        except ReturnLevelAuditBlocked as exc:
            raise GtsmFamilyReturnAuditBlocked("producer family return-level QA rejected") from exc
        by_family[family] = {key: result[key] for key in COUNTER_FIELDS}

    for key in COUNTER_FIELDS:
        if sum(int(category[key]) for category in by_family.values()) != whole[key]:
            raise GtsmFamilyReturnAuditBlocked("producer-family QA counts differ from native global QA")

    return {
        "schema_version": "gtsm-source-return-quality-by-author-family-v0",
        "original_source_station_rows": expected_rows,
        "native_return_period_years": list(RETURN_PERIODS),
        "source_global_quality_counts": {key: whole[key] for key in COUNTER_FIELDS},
        "station_family_quality_counts": by_family,
        "native_2p5_97p5_versus_named_5_95_confidence_semantics_unresolved": True,
        "producer_station_prefix_is_not_geographic_coast_or_flood_footprint_proof": True,
        "bestfit_outside_reported_interval_not_necessarily_source_error": True,
        "full_source_levels_station_ids_and_coordinates_emitted": False,
        "raw_provider_bytes_persisted": False,
        "physical_coastal_cat_model_validated": False,
        "source_commercial_rights_approved": False,
        "cat_model_admitted": False,
    }


def read_pinned_original_return_matrices(
    path: Path,
) -> tuple[list[list[float]], list[list[float]], list[list[float]]]:
    """Only called after independent full-file SHA-256 and native-header checks."""
    try:
        import numpy as np
        from netCDF4 import Dataset
        with Dataset(path.as_posix(), "r") as ds:
            if (set(ds.dimensions) != {"stations", "quantile", "return_period"}
                    or len(ds.dimensions["stations"]) != EXPECTED_SOURCE_ROWS
                    or len(ds.dimensions["return_period"]) != EXPECTED_PERIODS):
                raise GtsmFamilyReturnAuditBlocked("original source dimensions changed")
            original = []
            for name in SOURCES:
                var = ds.variables[name]
                if (var.dimensions != ("stations", "return_period")
                        or str(var.dtype) != "float64"):
                    raise GtsmFamilyReturnAuditBlocked("native return-level variable schema changed")
                var.set_auto_maskandscale(False)
                values = np.asarray(var[:], dtype=np.float64)
                if values.shape != (EXPECTED_SOURCE_ROWS, EXPECTED_PERIODS):
                    raise GtsmFamilyReturnAuditBlocked("native original return-level matrix changed")
                for key in ("_FillValue", "missing_value"):
                    if key in var.ncattrs():
                        marker = np.asarray(var.getncattr(key))
                        if marker.ndim != 0 or not np.issubdtype(marker.dtype, np.number):
                            raise GtsmFamilyReturnAuditBlocked("native missing-value marker invalid")
                        fill = float(marker)
                        if np.isfinite(fill):
                            values[values == fill] = np.nan
                original.append(values.tolist())
    except GtsmFamilyReturnAuditBlocked:
        raise
    except Exception as exc:
        raise GtsmFamilyReturnAuditBlocked(
            "failed bounded fixed original-source matrix read (" + type(exc).__name__ + ")"
        ) from exc
    return tuple(original)  # type: ignore[return-value]
