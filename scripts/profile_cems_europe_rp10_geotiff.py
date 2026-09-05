# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile metadata of the exact receipt-bound CEMS Europe RP10 GeoTIFF.

This module never reads raster values. The public profiler first verifies the
complete local byte identity accepted by Issue #793 and only then opens the
file with Rasterio for bounded structural metadata.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import rasterio

SOURCE_ISSUE = 793
PROFILE_ISSUE = 802
DATASET_ID = "ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026"
RELEASE = "3.1.1"
FILENAME = "Europe_RP10_filled_depth.tif"
SOURCE_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/"
    + FILENAME
)
ACCEPTED_BYTE_COUNT = 272_286_610
ACCEPTED_SHA256 = "15f86b86c228a065250b05488548d7386ac8e33cec4cba6da93f712f7500f45b"
_HASH_CHUNK_SIZE = 1_048_576
_MAX_CRS_TEXT = 65_536
_MAX_UNIT_TEXT = 256
_UNIT_TAG_KEYS = frozenset({"UNIT", "UNITS", "UNITTYPE", "UNIT_TYPE"})


class CemsRp10GeoTiffProfileError(RuntimeError):
    """Raised when byte identity or bounded GeoTIFF metadata is invalid."""


def _bounded_text(value: str | None, *, field: str, limit: int) -> str | None:
    if value is None:
        return None
    if type(value) is not str or len(value) > limit:
        raise CemsRp10GeoTiffProfileError(f"{field} is outside the bounded metadata contract")
    return value


def _number(value: Any, *, field: str) -> int | float | str | None:
    if value is None:
        return None
    if type(value) is bool:
        raise CemsRp10GeoTiffProfileError(f"{field} is not numeric metadata")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CemsRp10GeoTiffProfileError(f"{field} is not numeric metadata") from exc
    return _number(numeric, field=field)


def _verify_file_identity(
    path: Path,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> tuple[int, str]:
    if type(expected_byte_count) is not int or expected_byte_count <= 0:
        raise CemsRp10GeoTiffProfileError("expected byte count is invalid")
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(ch not in "0123456789abcdef" for ch in expected_sha256)
    ):
        raise CemsRp10GeoTiffProfileError("expected SHA-256 is invalid")

    digest = hashlib.sha256()
    byte_count = 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_HASH_CHUNK_SIZE)
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    raise CemsRp10GeoTiffProfileError("local GeoTIFF stream returned non-byte content")
                byte_count += len(chunk)
                if byte_count > expected_byte_count:
                    raise CemsRp10GeoTiffProfileError("local GeoTIFF byte count exceeds accepted receipt")
                digest.update(chunk)
    except OSError as exc:
        raise CemsRp10GeoTiffProfileError("local GeoTIFF bytes could not be read") from exc

    sha256 = digest.hexdigest()
    if byte_count != expected_byte_count:
        raise CemsRp10GeoTiffProfileError("local GeoTIFF byte count differs from accepted receipt")
    if sha256 != expected_sha256:
        raise CemsRp10GeoTiffProfileError("local GeoTIFF SHA-256 differs from accepted receipt")
    return byte_count, sha256


def _filtered_unit_tags(dataset: Any) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for band in range(1, dataset.count + 1):
        raw = dataset.tags(band)
        selected: dict[str, str] = {}
        for key, value in raw.items():
            if type(key) is str and key.upper() in _UNIT_TAG_KEYS:
                bounded_key = _bounded_text(key, field="unit tag key", limit=_MAX_UNIT_TEXT)
                bounded_value = _bounded_text(value, field="unit tag value", limit=_MAX_UNIT_TEXT)
                assert bounded_key is not None and bounded_value is not None
                selected[bounded_key] = bounded_value
        result.append(dict(sorted(selected.items())))
    return result


def _profile_bound_geotiff(
    path: str | Path,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Internal testable profiler with caller-supplied byte identity."""
    local_path = Path(path)
    byte_count, sha256 = _verify_file_identity(
        local_path,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )

    try:
        with rasterio.open(local_path, "r") as dataset:
            if dataset.driver != "GTiff":
                raise CemsRp10GeoTiffProfileError("receipt-bound object is not a GDAL GeoTIFF dataset")
            if type(dataset.width) is not int or dataset.width <= 0:
                raise CemsRp10GeoTiffProfileError("GeoTIFF width is invalid")
            if type(dataset.height) is not int or dataset.height <= 0:
                raise CemsRp10GeoTiffProfileError("GeoTIFF height is invalid")
            if type(dataset.count) is not int or dataset.count <= 0:
                raise CemsRp10GeoTiffProfileError("GeoTIFF band count is invalid")

            crs = dataset.crs
            crs_string = _bounded_text(
                None if crs is None else str(crs),
                field="CRS string",
                limit=_MAX_CRS_TEXT,
            )
            crs_wkt = _bounded_text(
                None if crs is None else crs.to_wkt(),
                field="CRS WKT",
                limit=_MAX_CRS_TEXT,
            )
            crs_epsg = None if crs is None else crs.to_epsg()
            if crs_epsg is not None and (type(crs_epsg) is not int or crs_epsg <= 0):
                raise CemsRp10GeoTiffProfileError("CRS EPSG metadata is invalid")

            reader_units = [
                _bounded_text(unit, field="band unit", limit=_MAX_UNIT_TEXT)
                for unit in dataset.units
            ]
            unit_tags = _filtered_unit_tags(dataset)
            unit_metadata_present = any(unit is not None and unit != "" for unit in reader_units) or any(
                bool(tags) for tags in unit_tags
            )

            transform = [_number(value, field="affine transform") for value in dataset.transform.to_gdal()]
            resolution = [_number(value, field="pixel resolution") for value in dataset.res]
            bounds = [
                _number(value, field="raster bounds")
                for value in (dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top)
            ]
            nodata = [_number(value, field="band nodata") for value in dataset.nodatavals]
            scales = [_number(value, field="band scale") for value in dataset.scales]
            offsets = [_number(value, field="band offset") for value in dataset.offsets]
            descriptions = [
                _bounded_text(value, field="band description", limit=_MAX_UNIT_TEXT)
                for value in dataset.descriptions
            ]

            return {
                "schema_version": "oc-cems-rp10-geotiff-profile-v1",
                "dataset_id": DATASET_ID,
                "source_issue": SOURCE_ISSUE,
                "profile_issue": PROFILE_ISSUE,
                "release": RELEASE,
                "filename": FILENAME,
                "source_url": SOURCE_URL,
                "receipt_byte_count": byte_count,
                "receipt_sha256": sha256,
                "receipt_identity_verified": True,
                "driver": dataset.driver,
                "band_count": dataset.count,
                "dtypes": list(dataset.dtypes),
                "width": dataset.width,
                "height": dataset.height,
                "crs": {
                    "string": crs_string,
                    "epsg": crs_epsg,
                    "wkt": crs_wkt,
                },
                "transform_gdal": transform,
                "resolution": resolution,
                "bounds": bounds,
                "nodatavals": nodata,
                "scales": scales,
                "offsets": offsets,
                "descriptions": descriptions,
                "band_units": reader_units,
                "band_unit_tags": unit_tags,
                "unit_metadata_present": unit_metadata_present,
                "reader": {
                    "name": "rasterio",
                    "version": rasterio.__version__,
                    "gdal_version": getattr(rasterio, "__gdal_version__", None),
                    "proj_version": getattr(rasterio, "__proj_version__", None),
                },
                "raster_values_inspected": False,
                "external_bytes_persisted": False,
                "geotiff_metadata_verified": True,
                "benchmark_use_authorized": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            }
    except CemsRp10GeoTiffProfileError:
        raise
    except Exception as exc:
        raise CemsRp10GeoTiffProfileError("receipt-bound GeoTIFF metadata read failed") from exc


def profile_cems_rp10_geotiff(path: str | Path) -> dict[str, Any]:
    """Profile only the exact CEMS RP10 bytes accepted by trusted-main #793."""
    return _profile_bound_geotiff(
        path,
        expected_byte_count=ACCEPTED_BYTE_COUNT,
        expected_sha256=ACCEPTED_SHA256,
    )
