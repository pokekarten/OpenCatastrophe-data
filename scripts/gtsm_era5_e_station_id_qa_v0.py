# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only original GTSM station-ID catalogue QA (no source IDs are emitted).

Original NetCDF is opened only by the already SHA-256-pinned receipt workflow.
The paper's 44,734 model output locations are not assumed to share this ID
index, so these are explicitly *candidate* indexing diagnostics, not joins.
"""
from __future__ import annotations

from pathlib import Path
from numbers import Integral

EXPECTED_SOURCE_ROWS = 38_957
PAPER_GTSM_OUTPUT_LOCATIONS = 44_734
MAX_UINT16 = 65_535


class StationIdAuditBlocked(ValueError):
    """Native station-ID data shape or encoding is not safe to inspect."""


def summarize_native_station_ids(
    station_ids: list[int], *,
    expected_rows: int = EXPECTED_SOURCE_ROWS,
    source_fill_value: int | None = None,
) -> dict[str, object]:
    """Report aggregate counts only; never publish original station IDs or a lookup table."""
    if type(expected_rows) is not int or not 1 <= expected_rows <= EXPECTED_SOURCE_ROWS:
        raise StationIdAuditBlocked("invalid bounded original station-row budget")
    if type(station_ids) is not list or len(station_ids) != expected_rows:
        raise StationIdAuditBlocked("original station-ID vector length or type drift")
    if source_fill_value is not None and (
        type(source_fill_value) is not int or
        not 0 <= source_fill_value <= MAX_UINT16
    ):
        raise StationIdAuditBlocked("native station-ID fill marker not representable as uint16")

    seen: set[int] = set()
    duplicates = 0
    native_fill_records = 0
    adjacent_non_increasing = 0
    outside_zero_based_parent = 0
    outside_one_based_parent = 0
    prev: int | None = None

    for value in station_ids:
        if type(value) is not int or not 0 <= value <= MAX_UINT16:
            raise StationIdAuditBlocked("native station identifier is not a uint16 integer")
        if source_fill_value is not None and value == source_fill_value:
            native_fill_records += 1
            continue
        if prev is not None and value <= prev:
            adjacent_non_increasing += 1
        prev = value
        if value in seen:
            duplicates += 1
        else:
            seen.add(value)
        if not 0 <= value < PAPER_GTSM_OUTPUT_LOCATIONS:
            outside_zero_based_parent += 1
        if not 1 <= value <= PAPER_GTSM_OUTPUT_LOCATIONS:
            outside_one_based_parent += 1

    distinct = len(seen)
    valid = expected_rows - native_fill_records
    if distinct + duplicates != valid:
        raise StationIdAuditBlocked("native source-ID totals cannot be reconciled")
    span = max(seen) - min(seen) + 1 if seen else 0
    holes = span - distinct if seen else 0
    sorted_ids = sorted(seen)
    missing_runs = [
        right - left - 1
        for left, right in zip(sorted_ids, sorted_ids[1:])
        if right - left > 1
    ]
    if sum(missing_runs) != holes:
        raise StationIdAuditBlocked("native ID gap-run totals do not reconcile")
    # Hypothetical arithmetic ONLY; source index range does not prove same-vintage
    # parent catalogue identity or a coast/ocean classification.
    zero_based_range_compatible = valid > 0 and outside_zero_based_parent == 0
    hypothetical_omissions = None
    if zero_based_range_compatible:
        before_span = min(seen)
        after_span = PAPER_GTSM_OUTPUT_LOCATIONS - max(seen) - 1
        total_unrepresented = PAPER_GTSM_OUTPUT_LOCATIONS - distinct
        if before_span + holes + after_span != total_unrepresented:
            raise StationIdAuditBlocked("candidate zero-based index counts do not reconcile")
        hypothetical_omissions = {
            "before_native_id_span": before_span,
            "inside_native_id_span": holes,
            "after_native_id_span": after_span,
            "total_if_same_parent_catalogue": total_unrepresented,
            "conditional_on_unproven_parent_index_identity": True,
        }
    return {
        "schema_version": "gtsm-native-station-id-catalogue-qa-v0",
        "source_statistical_rows": expected_rows,
        "paper_model_output_locations": PAPER_GTSM_OUTPUT_LOCATIONS,
        "paper_minus_source_rows_arithmetic_only": PAPER_GTSM_OUTPUT_LOCATIONS - expected_rows,
        "station_id_storage_type": "uint16",
        "native_station_id_records": valid,
        "native_station_id_fill_records": native_fill_records,
        "distinct_native_ids": distinct,
        "duplicate_native_id_records": duplicates,
        "nonincreasing_adjacent_id_pairs": adjacent_non_increasing,
        "native_id_span_width": span,
        "unrepresented_ids_inside_native_span": holes,
        "number_of_internal_gap_runs": len(missing_runs),
        "largest_internal_gap_run": max(missing_runs, default=0),
        "internal_gap_runs_of_at_least_1000_ids": sum(n >= 1000 for n in missing_runs),
        "zero_based_hypothetical_parent_omissions": hypothetical_omissions,
        "ids_outside_zero_based_paper_catalogue_range": outside_zero_based_parent,
        "ids_outside_one_based_paper_catalogue_range": outside_one_based_parent,
        "zero_based_catalogue_index_range_compatible": zero_based_range_compatible,
        "one_based_catalogue_index_range_compatible": (
            valid > 0 and outside_one_based_parent == 0
        ),
        "parent_catalogue_index_identity_proven": False,
        "paper_output_location_count_same_release_proven": False,
        "coastal_vs_ocean_station_membership_proven": False,
        "geolocation_or_site_join_authorized": False,
        "individual_station_ids_or_positions_emitted": False,
        "publisher_raw_data_persisted": False,
        "science_fitness_approved": False,
        "commercial_rights_approved": False,
        "cat_model_admitted": False,
    }


def inspect_original_station_ids(path: Path) -> dict[str, object]:
    """Bounded original `stations` uint16 vector; digest/header checked upstream."""
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise StationIdAuditBlocked("pinned netCDF4 reader unavailable") from exc
    try:
        with Dataset(path.as_posix(), "r") as dataset:
            if len(dataset.dimensions["stations"]) != EXPECTED_SOURCE_ROWS:
                raise StationIdAuditBlocked("original source station axis changed")
            station = dataset.variables["stations"]
            if station.dimensions != ("stations",) or str(station.dtype) != "uint16":
                raise StationIdAuditBlocked("native station-ID storage dimensions/type changed")
            source_fill = None
            if "_FillValue" in station.ncattrs():
                raw_fill = station.getncattr("_FillValue")
                if (getattr(raw_fill, "ndim", 0) != 0
                        or isinstance(raw_fill, bool)
                        or not isinstance(raw_fill, Integral)):
                    raise StationIdAuditBlocked("native station-ID fill marker has unexpected type")
                source_fill = int(raw_fill)
            station.set_auto_maskandscale(False)
            ids = station[:]
            if len(ids.shape) != 1 or ids.size != EXPECTED_SOURCE_ROWS:
                raise StationIdAuditBlocked("native station-ID values not one bounded axis")
            source_ids = ids.tolist()
    except StationIdAuditBlocked:
        raise
    except Exception as exc:
        raise StationIdAuditBlocked(
            "failed bounded native station-ID read (" + type(exc).__name__ + ")"
        ) from exc
    return summarize_native_station_ids(source_ids, source_fill_value=source_fill)
