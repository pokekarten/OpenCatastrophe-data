# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Stream bounded value inventories for the exact CEMS companion-mask GeoTIFFs.

This is the synthetic-first Issue #823 value-inspection layer. It deliberately
separates observed numeric encoding from semantic interpretation: values may be
inventoried, but no numeric class is silently declared to mean "masked".
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
except ImportError:  # Optional outside the reviewed GeoTIFF-profile environment.
    np = None

try:
    from scripts import profile_cems_europe_mask_geotiffs as _metadata
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_cems_europe_mask_geotiffs as _metadata

VALUE_PROFILE_ISSUE = 823
SCHEMA_VERSION = "oc-cems-mask-value-inventory-v1"
CARDINALITY_CAP = 32


class CemsMaskValueProfileError(RuntimeError):
    """Raised when exact identity or bounded value-inventory rules fail."""


def _require_numpy() -> None:
    if np is None:
        raise CemsMaskValueProfileError(
            "CEMS mask value profiling requires requirements-cems-geotiff-profile.txt"
        )


def _receipt(mask_kind: str) -> dict[str, Any]:
    if type(mask_kind) is not str or mask_kind not in _metadata.MASK_RECEIPTS:
        raise CemsMaskValueProfileError(
            "mask kind is outside the frozen #809/#816 receipt set"
        )
    return _metadata.MASK_RECEIPTS[mask_kind]


def _json_number(value: object) -> int | float | str | None:
    if value is None:
        return None
    if type(value) is bool:
        raise CemsMaskValueProfileError("numeric raster metadata cannot be boolean")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CemsMaskValueProfileError("raster metadata is not numeric") from exc
    if math.isnan(numeric):
        return "NaN"
    if math.isinf(numeric):
        return "Infinity" if numeric > 0 else "-Infinity"
    if numeric.is_integer() and abs(numeric) <= 2**53:
        return int(numeric)
    return numeric


def _nodata_mask(block: Any, nodata: object) -> Any:
    if nodata is None:
        return np.zeros(block.shape, dtype=bool)
    numeric = float(nodata)
    if math.isnan(numeric):
        return np.isnan(block)
    return block == numeric


def _inventory_windows(
    dataset: Any,
    windows: Iterable[Any],
    *,
    cardinality_cap: int,
) -> dict[str, Any]:
    """Aggregate supplied test/internal windows without full-raster materialisation."""
    _require_numpy()
    if type(cardinality_cap) is not int or not (1 <= cardinality_cap <= CARDINALITY_CAP):
        raise CemsMaskValueProfileError(
            "cardinality cap is outside the preregistered bound"
        )
    if dataset.count != 1:
        raise CemsMaskValueProfileError("value profiler requires exactly one raster band")

    total_cells = 0
    block_count = 0
    nodata_count = 0
    nan_non_nodata_count = 0
    positive_infinity_count = 0
    negative_infinity_count = 0
    finite_count = 0
    zero_count = 0
    nonzero_count = 0
    finite_min: float | None = None
    finite_max: float | None = None
    exact_counts: dict[float, int] = {}
    cardinality_cap_exceeded = False

    for window in windows:
        block = dataset.read(1, window=window, masked=False)
        if getattr(block, "ndim", None) != 2:
            raise CemsMaskValueProfileError("raster block is not two-dimensional")

        block_count += 1
        total_cells += int(block.size)

        nodata_mask = _nodata_mask(block, dataset.nodata)
        nodata_count += int(nodata_mask.sum())
        observed = block[~nodata_mask]
        if observed.size == 0:
            continue

        nan_mask = np.isnan(observed)
        posinf_mask = np.isposinf(observed)
        neginf_mask = np.isneginf(observed)
        nan_non_nodata_count += int(nan_mask.sum())
        positive_infinity_count += int(posinf_mask.sum())
        negative_infinity_count += int(neginf_mask.sum())

        finite = observed[np.isfinite(observed)]
        if finite.size == 0:
            continue

        finite_count += int(finite.size)
        zero_count += int((finite == 0).sum())
        nonzero_count += int((finite != 0).sum())

        block_min = float(finite.min())
        block_max = float(finite.max())
        finite_min = block_min if finite_min is None else min(finite_min, block_min)
        finite_max = block_max if finite_max is None else max(finite_max, block_max)

        if not cardinality_cap_exceeded:
            values, counts = np.unique(finite, return_counts=True)
            prospective = set(exact_counts)
            prospective.update(float(value) for value in values)
            if len(prospective) > cardinality_cap:
                cardinality_cap_exceeded = True
                exact_counts.clear()
            else:
                for value, count in zip(values, counts, strict=True):
                    key = float(value)
                    exact_counts[key] = exact_counts.get(key, 0) + int(count)

    expected_cells = int(dataset.width) * int(dataset.height)
    if total_cells != expected_cells:
        raise CemsMaskValueProfileError(
            f"window scan covered {total_cells} cells, expected {expected_cells}"
        )

    accounted_cells = (
        nodata_count
        + nan_non_nodata_count
        + positive_infinity_count
        + negative_infinity_count
        + finite_count
    )
    if accounted_cells != total_cells:
        raise CemsMaskValueProfileError(
            f"value accounting covered {accounted_cells} cells, expected {total_cells}"
        )

    if cardinality_cap_exceeded:
        finite_unique_value_count: int | None = None
        finite_value_counts: list[dict[str, Any]] | None = None
        encoding_observation = "cardinality_cap_exceeded"
    else:
        finite_unique_value_count = len(exact_counts)
        finite_value_counts = [
            {"value": _json_number(value), "count": exact_counts[value]}
            for value in sorted(exact_counts)
        ]
        if finite_count == 0:
            encoding_observation = "no_finite_non_nodata_values"
        elif finite_unique_value_count == 1:
            encoding_observation = "single_finite_value_candidate_support"
        else:
            encoding_observation = "multiple_finite_values_mapping_unresolved"

    result = {
        "total_cells": total_cells,
        "block_count": block_count,
        "nodata_value": _json_number(dataset.nodata),
        "nodata_count": nodata_count,
        "nan_non_nodata_count": nan_non_nodata_count,
        "positive_infinity_count": positive_infinity_count,
        "negative_infinity_count": negative_infinity_count,
        "finite_count": finite_count,
        "zero_count": zero_count,
        "nonzero_count": nonzero_count,
        "finite_min": _json_number(finite_min),
        "finite_max": _json_number(finite_max),
        "cardinality_cap": cardinality_cap,
        "cardinality_cap_exceeded": cardinality_cap_exceeded,
        "finite_unique_value_count": finite_unique_value_count,
        "finite_value_counts": finite_value_counts,
        "encoding_observation": encoding_observation,
    }
    canonical = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["inventory_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def inventory_dataset(
    dataset: Any,
    *,
    cardinality_cap: int = CARDINALITY_CAP,
) -> dict[str, Any]:
    """Inventory the complete single-band dataset through its own block windows."""
    windows = (window for _index, window in dataset.block_windows(1))
    return _inventory_windows(
        dataset,
        windows,
        cardinality_cap=cardinality_cap,
    )


def require_exact_grid_before_comparison(
    mask_profile: dict[str, Any],
    rp10_profile: dict[str, Any],
) -> dict[str, Any]:
    """Reuse the accepted #816 comparator and fail if exact grid equality is absent."""
    try:
        comparison = _metadata.compare_mask_profile_to_rp10(
            mask_profile,
            rp10_profile,
        )
    except _metadata.CemsMaskGeoTiffProfileError as exc:
        raise CemsMaskValueProfileError(str(exc)) from exc
    if comparison.get("grid_metadata_equal") is not True:
        raise CemsMaskValueProfileError(
            "cross-raster value comparison requires exact accepted grid metadata"
        )
    return comparison


def profile_cems_mask_value_inventory(
    path: str | Path,
    *,
    mask_kind: str,
) -> dict[str, Any]:
    """Inspect values only after binding the exact frozen mask bytes in memory."""
    _require_numpy()
    receipt = _receipt(mask_kind)
    source_path = Path(path)

    try:
        memory_file, byte_count, sha256 = _metadata._rp10._verify_file_identity(
            source_path,
            expected_byte_count=receipt["byte_count"],
            expected_sha256=receipt["sha256"],
        )
    except _metadata._rp10.CemsRp10GeoTiffProfileError as exc:
        raise CemsMaskValueProfileError(str(exc)) from exc

    try:
        with memory_file.open() as dataset:
            inventory = inventory_dataset(dataset)
            grid = {
                "width": int(dataset.width),
                "height": int(dataset.height),
                "crs": None if dataset.crs is None else dataset.crs.to_string(),
                "transform_gdal": [
                    float(value) for value in dataset.transform.to_gdal()
                ],
                "resolution": [float(abs(value)) for value in dataset.res],
                "bounds": [float(value) for value in dataset.bounds],
                "band_count": int(dataset.count),
                "dtype": str(dataset.dtypes[0]),
            }
    except CemsMaskValueProfileError:
        raise
    except Exception as exc:
        raise CemsMaskValueProfileError(
            "verified CEMS mask could not be scanned by block windows"
        ) from exc
    finally:
        memory_file.close()

    result = {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": _metadata.DATASET_ID,
        "release": _metadata.RELEASE,
        "source_issue": _metadata.SOURCE_ISSUE,
        "profile_issue": VALUE_PROFILE_ISSUE,
        "mask_kind": mask_kind,
        "filename": receipt["filename"],
        "receipt_byte_count": byte_count,
        "receipt_sha256": sha256,
        "receipt_identity_verified": True,
        "grid": grid,
        "inventory": inventory,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
    canonical = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["result_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
