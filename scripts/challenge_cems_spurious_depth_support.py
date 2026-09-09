# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Falsify the CEMS spurious-depth candidate support against current RP10.

Issue #823 Stage D is a necessary-condition challenge only. The Stage-B result
identified one finite candidate class (value 1) against a NaN background; this
module does not promote that candidate to verified mask semantics. It tests only
whether candidate cell centres have a current RP10 depth >10 m cell centre within
2 km plus one preregistered grid-cell diagonal tolerance, using WGS84 geodesics.
"""

from __future__ import annotations

import math
from typing import Any

try:
    import numpy as np
except ImportError:  # Optional outside the reviewed support-challenge runtime.
    np = None

try:
    import pyproj
    from pyproj import Geod
except ImportError:  # Optional outside the reviewed support-challenge runtime.
    pyproj = None
    Geod = None

try:
    from rasterio.windows import Window
except ImportError:  # Optional outside the reviewed support-challenge runtime.
    Window = None

SCHEMA_VERSION = "oc-cems-spurious-rp10-necessary-condition-v1"
BASE_DISTANCE_METRES = 2_000.0
CANDIDATE_VALUE = 1.0
RP10_SEED_THRESHOLD_METRES = 10.0
EXPECTED_CRS = "EPSG:4326"


class CemsSpuriousSupportChallengeError(RuntimeError):
    """Raised when the preregistered Stage-D contract cannot be evaluated exactly."""


def _require_dependencies() -> None:
    if np is None or Geod is None or Window is None:
        raise CemsSpuriousSupportChallengeError(
            "CEMS support challenge requires requirements-cems-mask-support-challenge.txt"
        )


def _crs_string(dataset: Any) -> str | None:
    crs = getattr(dataset, "crs", None)
    if crs is None:
        return None
    method = getattr(crs, "to_string", None)
    return method() if callable(method) else str(crs)


def _cell_centre(transform: Any, row: int, column: int) -> tuple[float, float]:
    x = (
        float(transform.c)
        + (float(column) + 0.5) * float(transform.a)
        + (float(row) + 0.5) * float(transform.b)
    )
    y = (
        float(transform.f)
        + (float(column) + 0.5) * float(transform.d)
        + (float(row) + 0.5) * float(transform.e)
    )
    return x, y


def _validate_common_grid(mask_dataset: Any, rp10_dataset: Any) -> Any:
    for label, dataset in (("mask", mask_dataset), ("RP10", rp10_dataset)):
        if getattr(dataset, "count", None) != 1:
            raise CemsSpuriousSupportChallengeError(
                f"{label} raster must contain exactly one band"
            )
        if type(getattr(dataset, "width", None)) is not int or dataset.width < 2:
            raise CemsSpuriousSupportChallengeError(f"{label} raster width is invalid")
        if type(getattr(dataset, "height", None)) is not int or dataset.height < 2:
            raise CemsSpuriousSupportChallengeError(f"{label} raster height is invalid")
        if _crs_string(dataset) != EXPECTED_CRS:
            raise CemsSpuriousSupportChallengeError(
                f"{label} raster CRS must be exact EPSG:4326"
            )

    if mask_dataset.width != rp10_dataset.width or mask_dataset.height != rp10_dataset.height:
        raise CemsSpuriousSupportChallengeError("mask/RP10 raster dimensions differ")
    if mask_dataset.transform != rp10_dataset.transform:
        raise CemsSpuriousSupportChallengeError("mask/RP10 affine transforms differ")

    transform = mask_dataset.transform
    if (
        float(transform.b) != 0.0
        or float(transform.d) != 0.0
        or float(transform.a) <= 0.0
        or float(transform.e) >= 0.0
    ):
        raise CemsSpuriousSupportChallengeError(
            "Stage D requires the accepted north-up unrotated geographic grid"
        )
    return transform


def _distance_metres(
    geod: Any,
    lon1: Any,
    lat1: Any,
    lon2: Any,
    lat2: Any,
) -> Any:
    _az1, _az2, distance = geod.inv(lon1, lat1, lon2, lat2)
    return distance


def _distance_contract(dataset: Any, transform: Any, geod: Any) -> dict[str, Any]:
    """Freeze one-cell tolerance plus conservative exact-geodesic search envelope."""
    north_00 = _cell_centre(transform, 0, 0)
    north_11 = _cell_centre(transform, 1, 1)
    south_00 = _cell_centre(transform, dataset.height - 1, 0)
    south_11 = _cell_centre(transform, dataset.height - 2, 1)

    north_diagonal = float(
        _distance_metres(geod, north_00[0], north_00[1], north_11[0], north_11[1])
    )
    south_diagonal = float(
        _distance_metres(geod, south_00[0], south_00[1], south_11[0], south_11[1])
    )
    tolerance = max(north_diagonal, south_diagonal)
    threshold = BASE_DISTANCE_METRES + tolerance

    # A same-row pair at the north/south boundary gives a conservative longitude
    # envelope. We include the first column offset already beyond the threshold,
    # so the envelope can only over-include neighbours; exact Geod.inv decides.
    max_col_offset = 0
    for row in (0, dataset.height - 1):
        lon0, lat0 = _cell_centre(transform, row, 0)
        first_beyond = dataset.width - 1
        for offset in range(1, dataset.width):
            lon2 = lon0 + offset * float(transform.a)
            distance = float(_distance_metres(geod, lon0, lat0, lon2, lat0))
            if distance > threshold:
                first_beyond = offset
                break
        max_col_offset = max(max_col_offset, first_beyond)

    # Likewise include the first same-column row offset beyond the threshold at
    # both meridional boundaries. Exact geodesics still decide every candidate.
    max_row_offset = 0
    for start_row, direction in ((0, 1), (dataset.height - 1, -1)):
        lon0, lat0 = _cell_centre(transform, start_row, 0)
        first_beyond = dataset.height - 1
        for offset in range(1, dataset.height):
            _lon2, lat2 = _cell_centre(
                transform,
                start_row + direction * offset,
                0,
            )
            distance = float(_distance_metres(geod, lon0, lat0, lon0, lat2))
            if distance > threshold:
                first_beyond = offset
                break
        max_row_offset = max(max_row_offset, first_beyond)

    if max_col_offset < 1 or max_row_offset < 1:
        raise CemsSpuriousSupportChallengeError("geodesic search envelope is invalid")

    return {
        "distance_model": "WGS84_GEOD",
        "base_distance_metres": BASE_DISTANCE_METRES,
        "north_cell_diagonal_metres": north_diagonal,
        "south_cell_diagonal_metres": south_diagonal,
        "cell_diagonal_tolerance_metres": tolerance,
        "distance_threshold_metres": threshold,
        "max_row_offset": max_row_offset,
        "max_col_offset": max_col_offset,
    }


def _read_row(dataset: Any, row: int) -> Any:
    try:
        values = dataset.read(
            1,
            window=Window(0, row, dataset.width, 1),
            masked=False,
        ).reshape(-1)
    except Exception as exc:
        raise CemsSpuriousSupportChallengeError("raster row could not be read") from exc
    if values.size != dataset.width:
        raise CemsSpuriousSupportChallengeError("raster row width drifted")
    return values


def _candidate_columns(mask_row: Any) -> Any:
    if bool(np.isinf(mask_row).any()):
        raise CemsSpuriousSupportChallengeError(
            "spurious-depth candidate raster contains infinity"
        )
    finite = np.isfinite(mask_row)
    if bool(finite.any()) and bool((mask_row[finite] != CANDIDATE_VALUE).any()):
        raise CemsSpuriousSupportChallengeError(
            "spurious-depth finite class drifted from Stage-B value 1"
        )
    return np.flatnonzero(finite)


def _seed_columns(rp10_row: Any) -> Any:
    if bool(np.isinf(rp10_row).any()):
        raise CemsSpuriousSupportChallengeError("RP10 raster contains infinity")
    return np.flatnonzero(
        np.isfinite(rp10_row) & (rp10_row > RP10_SEED_THRESHOLD_METRES)
    )


def _same_row_membership(candidate_columns: Any, seed_columns: Any) -> Any:
    membership = np.zeros(candidate_columns.size, dtype=bool)
    if candidate_columns.size == 0 or seed_columns.size == 0:
        return membership
    positions = np.searchsorted(seed_columns, candidate_columns)
    valid = positions < seed_columns.size
    valid_indices = np.flatnonzero(valid)
    if valid_indices.size:
        membership[valid_indices] = (
            seed_columns[positions[valid_indices]] == candidate_columns[valid_indices]
        )
    return membership


def _mark_exactly_covered(
    candidate_columns: Any,
    candidate_row: int,
    seed_rows: dict[int, Any],
    *,
    transform: Any,
    geod: Any,
    distance_threshold_metres: float,
    max_col_offset: int,
    initial_covered: Any,
) -> Any:
    covered = initial_covered.copy()
    if candidate_columns.size == 0:
        return covered

    candidate_latitude = _cell_centre(transform, candidate_row, 0)[1]
    ordered_rows = sorted(seed_rows, key=lambda row: (abs(row - candidate_row), row))

    for seed_row in ordered_rows:
        remaining = np.flatnonzero(~covered)
        if remaining.size == 0:
            break
        seeds = seed_rows[seed_row]
        if seeds.size == 0:
            continue

        candidates = candidate_columns[remaining]
        insertions = np.searchsorted(seeds, candidates)
        seed_latitude = _cell_centre(transform, seed_row, 0)[1]

        for side in ("left", "right"):
            if side == "left":
                seed_indices = insertions - 1
                valid = seed_indices >= 0
            else:
                seed_indices = insertions
                valid = seed_indices < seeds.size
            if not bool(valid.any()):
                continue

            remaining_indices = remaining[valid]
            candidate_subset = candidate_columns[remaining_indices]
            seed_subset = seeds[seed_indices[valid]]
            envelope = np.abs(seed_subset - candidate_subset) <= max_col_offset
            if not bool(envelope.any()):
                continue

            remaining_indices = remaining_indices[envelope]
            candidate_subset = candidate_subset[envelope]
            seed_subset = seed_subset[envelope]

            candidate_longitudes = (
                float(transform.c)
                + (candidate_subset.astype(float) + 0.5) * float(transform.a)
            )
            seed_longitudes = (
                float(transform.c)
                + (seed_subset.astype(float) + 0.5) * float(transform.a)
            )
            candidate_latitudes = np.full(
                candidate_longitudes.shape,
                candidate_latitude,
                dtype=float,
            )
            seed_latitudes = np.full(
                seed_longitudes.shape,
                seed_latitude,
                dtype=float,
            )
            distances = np.asarray(
                _distance_metres(
                    geod,
                    candidate_longitudes,
                    candidate_latitudes,
                    seed_longitudes,
                    seed_latitudes,
                ),
                dtype=float,
            )
            within = distances <= distance_threshold_metres
            if bool(within.any()):
                covered[remaining_indices[within]] = True

    return covered


def challenge_spurious_support(mask_dataset: Any, rp10_dataset: Any) -> dict[str, Any]:
    """Run the preregistered necessary-condition challenge on already-bound rasters."""
    _require_dependencies()
    transform = _validate_common_grid(mask_dataset, rp10_dataset)
    geod = Geod(ellps="WGS84")
    contract = _distance_contract(mask_dataset, transform, geod)
    max_row_offset = contract["max_row_offset"]

    seed_rows: dict[int, Any] = {}
    next_seed_row = 0
    rp10_seed_cells = 0
    candidate_cells = 0
    same_cell_overlap_cells = 0
    farther_cells = 0

    for candidate_row in range(mask_dataset.height):
        target_seed_row = min(
            rp10_dataset.height - 1,
            candidate_row + max_row_offset,
        )
        while next_seed_row <= target_seed_row:
            seeds = _seed_columns(_read_row(rp10_dataset, next_seed_row))
            seed_rows[next_seed_row] = seeds
            rp10_seed_cells += int(seeds.size)
            next_seed_row += 1

        oldest_allowed = candidate_row - max_row_offset
        for old_row in tuple(seed_rows):
            if old_row < oldest_allowed:
                del seed_rows[old_row]

        candidates = _candidate_columns(_read_row(mask_dataset, candidate_row))
        candidate_cells += int(candidates.size)
        same_row = _same_row_membership(
            candidates,
            seed_rows.get(candidate_row, np.empty(0, dtype=np.int64)),
        )
        same_cell_overlap_cells += int(same_row.sum())

        covered = _mark_exactly_covered(
            candidates,
            candidate_row,
            seed_rows,
            transform=transform,
            geod=geod,
            distance_threshold_metres=contract["distance_threshold_metres"],
            max_col_offset=contract["max_col_offset"],
            initial_covered=same_row,
        )
        farther_cells += int((~covered).sum())

    within_cells = candidate_cells - farther_cells
    if not (
        0 <= same_cell_overlap_cells <= within_cells <= candidate_cells
        and rp10_seed_cells >= same_cell_overlap_cells
    ):
        raise CemsSpuriousSupportChallengeError(
            "Stage-D aggregate counts failed internal reconciliation"
        )

    verdict = (
        "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION"
        if farther_cells == 0
        else "CURRENT_RP10_NECESSARY_CONDITION_FAIL"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_support_rule": "finite_value_exactly_1",
        "rp10_seed_rule": "finite_depth_strictly_gt_10_m",
        "candidate_support_cells": candidate_cells,
        "rp10_seed_cells": rp10_seed_cells,
        "same_cell_candidate_seed_overlap_cells": same_cell_overlap_cells,
        "candidate_with_seed_within_threshold_cells": within_cells,
        "candidate_farther_than_threshold_cells": farther_cells,
        "verdict": verdict,
        **contract,
        "pyproj_version": pyproj.__version__,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
