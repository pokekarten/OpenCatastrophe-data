# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read the frozen Dresden GloFAS v4 upstream-area candidates from exact NetCDF4 bytes.

This acquisition-only adapter is the byte-grounded bridge between the pre-target
46-cell geometry frozen in :mod:`scripts.hydrology_grid_matching` and the
existing drainage-area selector. It never downloads data and never reads river
discharge or PEGELONLINE measurements.

The external file is read once through a descriptor-bound regular-file check.
The same immutable byte string is both SHA-256 fingerprinted and opened by
Unidata ``netCDF4`` in memory, so the scientific values cannot come from a
second path lookup that differs from the recorded artifact identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path
from typing import Any, NamedTuple

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.dresden_acquisition_evidence import validate_artifact_descriptor
from scripts.hydrology_grid_matching import (
    GLOFAS_V4_GRID_RESOLUTION_DEGREES,
    GLOFAS_V4_LATITUDE_COUNT,
    GLOFAS_V4_LONGITUDE_COUNT,
    GLOFAS_V4_MAX_LATITUDE_CENTER,
    GLOFAS_V4_MAX_LONGITUDE_CENTER,
    GLOFAS_V4_MIN_LATITUDE_CENTER,
    GLOFAS_V4_MIN_LONGITUDE_CENTER,
    GLOFAS_V4_UPSTREAM_AREA_FILENAME,
    GLOFAS_V4_UPSTREAM_AREA_UNIT,
    GLOFAS_V4_UPSTREAM_AREA_VARIABLE,
    GlofasGridCell,
    glofas_v4_candidate_grid_points,
)

PROFILE_VERSION = "1.0.0"
DRESDEN_STATION_LATITUDE_WGS84 = 51.054460
DRESDEN_STATION_LONGITUDE_WGS84 = 13.738832
EXPECTED_CANDIDATE_COUNT = 46
M2_PER_KM2 = 1_000_000.0
COORDINATE_ABS_TOLERANCE = 1e-10
OFFICIAL_FILL_VALUE = -3.402823e38


class GlofasUpareaError(ValueError):
    """Raised when exact GloFAS v4 ancillary bytes fail the frozen contract."""


class GlofasUpareaReadResult(NamedTuple):
    """Canonical external evidence plus defined cells ready for the frozen selector."""

    evidence: dict[str, Any]
    grid_cells: tuple[GlofasGridCell, ...]


def _stable_external_bytes(path: Path, storage_reference: str) -> tuple[dict[str, Any], bytes]:
    if not isinstance(path, Path):
        raise GlofasUpareaError("path must be a pathlib.Path")
    try:
        before = path.lstat()
    except OSError as exc:
        raise GlofasUpareaError(f"cannot stat GloFAS ancillary: {exc}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise GlofasUpareaError("GloFAS ancillary must be a regular non-symlink file")
    if before.st_size <= 0:
        raise GlofasUpareaError("GloFAS ancillary must not be empty")

    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            identity_opened = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
            if not stat.S_ISREG(opened.st_mode) or identity_opened != identity_before:
                raise GlofasUpareaError("GloFAS ancillary changed before it could be opened safely")
            payload = handle.read()
    except GlofasUpareaError:
        raise
    except OSError as exc:
        raise GlofasUpareaError(f"cannot read GloFAS ancillary: {exc}") from exc

    try:
        after = path.lstat()
    except OSError as exc:
        raise GlofasUpareaError(f"cannot restat GloFAS ancillary: {exc}") from exc
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_after != identity_before or len(payload) != after.st_size:
        raise GlofasUpareaError("GloFAS ancillary changed while being read")

    descriptor = {
        "byte_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "storage_reference": storage_reference,
    }
    try:
        validate_artifact_descriptor(descriptor, "glofas_uparea_artifact")
    except ValueError as exc:
        raise GlofasUpareaError(str(exc)) from exc
    return descriptor, payload


def _netcdf4_module() -> Any:
    try:
        import netCDF4  # type: ignore[import-not-found]
    except ImportError as exc:
        raise GlofasUpareaError(
            "GloFAS NetCDF4 acquisition requires requirements-glofas-acquisition.txt"
        ) from exc
    return netCDF4


def _attribute_text(variable: Any, name: str, expected: str, where: str) -> None:
    actual = getattr(variable, name, None)
    if actual != expected:
        raise GlofasUpareaError(f"{where}.{name} must equal {expected!r}, got {actual!r}")


def _float_attribute(variable: Any, name: str, where: str) -> float:
    if name not in variable.ncattrs():
        raise GlofasUpareaError(f"{where}.{name} is required")
    try:
        value = float(variable.getncattr(name))
    except (TypeError, ValueError, OverflowError) as exc:
        raise GlofasUpareaError(f"{where}.{name} must be a finite numeric value") from exc
    if not math.isfinite(value):
        raise GlofasUpareaError(f"{where}.{name} must be finite")
    return value


def _expected_latitude(index: int) -> float:
    return round(
        GLOFAS_V4_MAX_LATITUDE_CENTER - GLOFAS_V4_GRID_RESOLUTION_DEGREES * index,
        12,
    )


def _expected_longitude(index: int) -> float:
    return round(
        GLOFAS_V4_MIN_LONGITUDE_CENTER + GLOFAS_V4_GRID_RESOLUTION_DEGREES * index,
        12,
    )


def _validate_coordinate_axis(variable: Any, *, axis: str) -> None:
    if axis == "latitude":
        count = GLOFAS_V4_LATITUDE_COUNT
        expected = _expected_latitude
        units = "degrees_north"
        axis_letter = "Y"
    elif axis == "longitude":
        count = GLOFAS_V4_LONGITUDE_COUNT
        expected = _expected_longitude
        units = "degrees_east"
        axis_letter = "X"
    else:  # pragma: no cover - internal programming error
        raise AssertionError(axis)

    if tuple(variable.dimensions) != (axis,) or tuple(variable.shape) != (count,):
        raise GlofasUpareaError(f"{axis} coordinate dimensions/shape do not match the frozen v4 grid")
    _attribute_text(variable, "standard_name", axis, axis)
    _attribute_text(variable, "units", units, axis)
    _attribute_text(variable, "axis", axis_letter, axis)

    values = variable[:]
    if len(values) != count:
        raise GlofasUpareaError(f"{axis} coordinate length changed while reading")
    for index, raw in enumerate(values):
        try:
            value = float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise GlofasUpareaError(f"{axis}[{index}] must be finite numeric data") from exc
        if not math.isfinite(value) or not math.isclose(
            value,
            expected(index),
            rel_tol=0.0,
            abs_tol=COORDINATE_ABS_TOLERANCE,
        ):
            raise GlofasUpareaError(
                f"{axis}[{index}] does not match the frozen GloFAS v4 coordinate grid"
            )


def _software_receipt(netCDF4: Any) -> dict[str, str]:
    return {
        "netcdf4_python": str(getattr(netCDF4, "__version__", "unknown")),
        "netcdf_c": str(getattr(netCDF4, "__netcdf4libversion__", "unknown")),
        "hdf5": str(getattr(netCDF4, "__hdf5libversion__", "unknown")),
    }


def read_dresden_glofas_v4_uparea(
    path: Path,
    *,
    storage_reference: str,
) -> GlofasUpareaReadResult:
    """Read only the 46 frozen Dresden candidate cells from exact v4 ancillary bytes."""

    artifact, payload = _stable_external_bytes(path, storage_reference)
    netCDF4 = _netcdf4_module()
    try:
        dataset = netCDF4.Dataset(GLOFAS_V4_UPSTREAM_AREA_FILENAME, mode="r", memory=payload)
    except Exception as exc:
        raise GlofasUpareaError(f"exact ancillary bytes are not a readable NetCDF4 dataset: {exc}") from exc

    try:
        if dataset.data_model not in {"NETCDF4", "NETCDF4_CLASSIC"}:
            raise GlofasUpareaError(
                f"ancillary data model must be NetCDF4, got {dataset.data_model!r}"
            )
        required_dimensions = {
            "latitude": GLOFAS_V4_LATITUDE_COUNT,
            "longitude": GLOFAS_V4_LONGITUDE_COUNT,
        }
        for name, expected_count in required_dimensions.items():
            dimension = dataset.dimensions.get(name)
            if dimension is None or len(dimension) != expected_count:
                raise GlofasUpareaError(
                    f"dimension {name!r} must contain exactly {expected_count} values"
                )

        latitude = dataset.variables.get("latitude")
        longitude = dataset.variables.get("longitude")
        uparea = dataset.variables.get(GLOFAS_V4_UPSTREAM_AREA_VARIABLE)
        if latitude is None or longitude is None or uparea is None:
            raise GlofasUpareaError("ancillary must contain latitude, longitude and uparea variables")

        _validate_coordinate_axis(latitude, axis="latitude")
        _validate_coordinate_axis(longitude, axis="longitude")

        if tuple(uparea.dimensions) != ("latitude", "longitude") or tuple(uparea.shape) != (
            GLOFAS_V4_LATITUDE_COUNT,
            GLOFAS_V4_LONGITUDE_COUNT,
        ):
            raise GlofasUpareaError("uparea dimensions/shape do not match the frozen v4 grid")
        _attribute_text(uparea, "units", GLOFAS_V4_UPSTREAM_AREA_UNIT, "uparea")
        _attribute_text(uparea, "long_name", "Upstream area of each river pixel", "uparea")
        if getattr(uparea.dtype, "kind", None) != "f" or getattr(uparea.dtype, "itemsize", None) != 4:
            raise GlofasUpareaError("uparea must be the documented 32-bit floating-point variable")

        fill_value = _float_attribute(uparea, "_FillValue", "uparea")
        missing_value = _float_attribute(uparea, "missing_value", "uparea")
        if not math.isclose(fill_value, OFFICIAL_FILL_VALUE, rel_tol=1e-7, abs_tol=0.0):
            raise GlofasUpareaError("uparea._FillValue differs from the documented v4 sentinel")
        if not math.isclose(missing_value, OFFICIAL_FILL_VALUE, rel_tol=1e-7, abs_tol=0.0):
            raise GlofasUpareaError("uparea.missing_value differs from the documented v4 sentinel")

        uparea.set_auto_maskandscale(False)
        points = glofas_v4_candidate_grid_points(
            station_latitude=DRESDEN_STATION_LATITUDE_WGS84,
            station_longitude=DRESDEN_STATION_LONGITUDE_WGS84,
        )
        if len(points) != EXPECTED_CANDIDATE_COUNT:
            raise GlofasUpareaError("frozen Dresden candidate count drifted from 46")

        records: list[dict[str, Any]] = []
        grid_cells: list[GlofasGridCell] = []
        for point in points:
            try:
                area_m2 = float(uparea[point.latitude_index, point.longitude_index])
            except (TypeError, ValueError, OverflowError, IndexError) as exc:
                raise GlofasUpareaError(
                    f"cannot read uparea at native index ({point.latitude_index}, {point.longitude_index})"
                ) from exc

            if area_m2 == fill_value or area_m2 == missing_value:
                records.append(
                    {
                        "latitude_index": point.latitude_index,
                        "longitude_index": point.longitude_index,
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "status": "missing",
                        "upstream_area_m2": None,
                        "upstream_area_km2": None,
                    }
                )
                continue
            if not math.isfinite(area_m2) or area_m2 <= 0.0:
                raise GlofasUpareaError(
                    f"defined uparea at native index ({point.latitude_index}, {point.longitude_index}) "
                    "must be finite and positive"
                )
            area_km2 = area_m2 / M2_PER_KM2
            if not math.isfinite(area_km2) or area_km2 <= 0.0:
                raise GlofasUpareaError("m2-to-km2 conversion must remain finite and positive")
            records.append(
                {
                    "latitude_index": point.latitude_index,
                    "longitude_index": point.longitude_index,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "status": "defined",
                    "upstream_area_m2": area_m2,
                    "upstream_area_km2": area_km2,
                }
            )
            grid_cells.append(GlofasGridCell(point.latitude, point.longitude, area_km2))

        if not grid_cells:
            raise GlofasUpareaError("all 46 frozen Dresden candidate cells are missing")

        evidence = {
            "profile_version": PROFILE_VERSION,
            "evidence_type": "dresden_glofas_v4_uparea_extraction",
            "artifact": artifact,
            "software": _software_receipt(netCDF4),
            "source_contract": {
                "filename": GLOFAS_V4_UPSTREAM_AREA_FILENAME,
                "variable": GLOFAS_V4_UPSTREAM_AREA_VARIABLE,
                "unit": GLOFAS_V4_UPSTREAM_AREA_UNIT,
                "latitude_count": GLOFAS_V4_LATITUDE_COUNT,
                "longitude_count": GLOFAS_V4_LONGITUDE_COUNT,
                "grid_resolution_degrees": GLOFAS_V4_GRID_RESOLUTION_DEGREES,
                "latitude_first": GLOFAS_V4_MAX_LATITUDE_CENTER,
                "latitude_last": GLOFAS_V4_MIN_LATITUDE_CENTER,
                "longitude_first": GLOFAS_V4_MIN_LONGITUDE_CENTER,
                "longitude_last": GLOFAS_V4_MAX_LONGITUDE_CENTER,
            },
            "station_coordinate_wgs84": {
                "latitude": DRESDEN_STATION_LATITUDE_WGS84,
                "longitude": DRESDEN_STATION_LONGITUDE_WGS84,
            },
            "candidate_count": len(records),
            "defined_candidate_count": len(grid_cells),
            "candidates": records,
        }
        return GlofasUpareaReadResult(evidence=evidence, grid_cells=tuple(grid_cells))
    finally:
        dataset.close()


def canonical_extraction_bytes(evidence: dict[str, Any]) -> bytes:
    if type(evidence) is not dict:
        raise GlofasUpareaError("extraction evidence must be an object")
    try:
        return json.dumps(
            evidence,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GlofasUpareaError(f"extraction evidence is not canonical JSON data: {exc}") from exc


def extraction_sha256(evidence: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_extraction_bytes(evidence)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read the frozen Dresden candidate cells from an exact GloFAS v4 upstream-area NetCDF4 file."
    )
    parser.add_argument("path", type=Path, help="External uparea_glofas_v4_0.nc file; never copied into Git")
    parser.add_argument(
        "--storage-reference",
        required=True,
        help="Canonical external:// logical identity for the exact file",
    )
    args = parser.parse_args(argv)
    try:
        result = read_dresden_glofas_v4_uparea(
            args.path,
            storage_reference=args.storage_reference,
        )
    except (OSError, GlofasUpareaError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_extraction_bytes(result.evidence) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
