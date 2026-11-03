# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only GTSM native-coordinate QA; output aggregated counts, never point records.

This module is deliberately not a geospatial join or coastal-hazard model.
Call only after separately validating the exact original SHA-256 and NetCDF schema.
"""
from __future__ import annotations

from pathlib import Path

EXPECTED_STATIONS = 38_957
MISSING_RAW = -999
MAX_LON_RAW = 180_000
MAX_LAT_RAW = 90_000


class CoordinateAuditBlocked(ValueError):
    """Exact original coordinate vector shape or type failed."""


def count_native_positions(raw_lons: list[int], raw_lats: list[int],
                           *, expected: int = EXPECTED_STATIONS) -> dict[str, object]:
    """QA raw packed int32 codes before applying the known 0.001 degree scale.

    Counts cannot establish physical proximity to shore, source model datum,
    valid water-level results or commercial data reuse.
    """
    if type(expected) is not int or not 1 <= expected <= 50_000:
        raise CoordinateAuditBlocked("invalid predeclared original station budget")
    if type(raw_lons) is not list or type(raw_lats) is not list:
        raise CoordinateAuditBlocked("expected two materialized original native coordinate vectors")
    if len(raw_lons) != expected or len(raw_lats) != expected:
        raise CoordinateAuditBlocked("GTSM original station vector length differs from exact source dimension")

    missing_both = 0
    missing_single = 0
    out_of_geographic_bounds = 0
    zero_zero_position_records = 0
    in_range = 0
    repeated_positions = 0
    observed: set[tuple[int, int]] = set()
    for lon, lat in zip(raw_lons, raw_lats):
        if type(lon) is not int or type(lat) is not int:
            raise CoordinateAuditBlocked("native coordinate vector must contain only raw integer codes")
        if lon == MISSING_RAW and lat == MISSING_RAW:
            missing_both += 1
            continue
        if lon == MISSING_RAW or lat == MISSING_RAW:
            missing_single += 1
            continue
        if abs(lon) > MAX_LON_RAW or abs(lat) > MAX_LAT_RAW:
            out_of_geographic_bounds += 1
            continue
        in_range += 1
        if lon == 0 and lat == 0:
            zero_zero_position_records += 1
        pair = (lon, lat)
        if pair in observed:
            repeated_positions += 1
        else:
            observed.add(pair)
    if in_range + missing_both + missing_single + out_of_geographic_bounds != expected:
        raise CoordinateAuditBlocked("original coordinate QA totals do not reconcile")
    return {
        "schema_version": "gtsm-native-positions-aggregate-qa-v0",
        "source_dimension_rows": expected,
        "valid_range_position_records": in_range,
        "missing_both_coordinates": missing_both,
        "missing_single_coordinate": missing_single,
        "out_of_geographic_bounds": out_of_geographic_bounds,
        "repeated_position_records": repeated_positions,
        "distinct_valid_positions": len(observed),
        "records_at_zero_zero": zero_zero_position_records,
        "input_native_scale_factor": "0.001",
        "input_missing_raw_code": MISSING_RAW,
        "longitude_degree_bounds": [-180, 180],
        "latitude_degree_bounds": [-90, 90],
        "original_coordinate_values_read_only": True,
        "raw_coordinate_values_redistributed": False,
        "near_coast_or_ocean_classification_done": False,
        "vertical_datum_validated": False,
        "exposure_linkage_authorized": False,
        "cat_model_admitted": False,
    }


def audit_original_coordinates(path: Path) -> dict[str, object]:
    """Read lon/lat only from already SHA-256-verified, schema-pinned NetCDF."""
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise CoordinateAuditBlocked("netCDF4 pinned acquisition environment required") from exc
    try:
        with Dataset(path.as_posix(), mode="r") as ds:
            if set(ds.dimensions) != {"stations", "quantile", "return_period"}:
                raise CoordinateAuditBlocked("GTSM original axis inventory differs from expected release")
            if len(ds.dimensions["stations"]) != EXPECTED_STATIONS:
                raise CoordinateAuditBlocked("original location dimension drifted")
            columns = []
            for name in ("lon", "lat"):
                variable = ds.variables[name]
                if variable.dimensions != ("stations",) or str(variable.dtype) != "int32":
                    raise CoordinateAuditBlocked("native coordinate variable schema drift")
                variable.set_auto_maskandscale(False)
                values = variable[:]
                if values.ndim != 1 or values.size != EXPECTED_STATIONS:
                    raise CoordinateAuditBlocked("original coordinate array shape drift")
                columns.append(values.tolist())
    except CoordinateAuditBlocked:
        raise
    except Exception as exc:
        raise CoordinateAuditBlocked("failed bounded read of GTSM original coordinate variables") from exc
    return count_native_positions(columns[0], columns[1])
