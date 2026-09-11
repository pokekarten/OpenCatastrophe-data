# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Derive Issue #835 falsifier records from already-open receipt-bound rasters.

This is a synthetic-first computational layer. It reuses the frozen Issue #823
Stage-D decision contract to identify falsifiers, then computes each falsifier's
global nearest current RP10 seed distance. It performs no acquisition and does
not alter the completed #823 verdict or authority ceiling.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
import math
from typing import Any

try:
    import numpy as np
except ImportError:  # Optional outside the reviewed CEMS support runtime.
    np = None

try:
    from pyproj import Geod
except ImportError:  # Optional outside the reviewed CEMS support runtime.
    Geod = None

try:
    from scripts import challenge_cems_spurious_depth_support as _stage_d
    from scripts import diagnose_cems_spurious_falsifiers as _diagnostic
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import challenge_cems_spurious_depth_support as _stage_d
    import diagnose_cems_spurious_falsifiers as _diagnostic

SCHEMA_VERSION = "oc-cems-spurious-falsifier-derivation-v1"
SOURCE_ISSUE = 835
STAGE_D_SOURCE_ISSUE = 823
EXPECTED_REAL_CANDIDATE_SUPPORT_CELLS = 17_242_147
EXPECTED_REAL_RP10_SEED_CELLS = 716_876
EXPECTED_REAL_FALSIFIER_CELLS = 19_797

# Deliberately below the minimum WGS84 meridional radius of curvature
# (~6.335e6 m). For the ellipsoidal surface metric, path length is at least
# M_min * absolute geodetic-latitude change. This conservative constant can
# therefore prune rows only when they provably cannot improve the exact best.
CONSERVATIVE_MERIDIONAL_METRES_PER_RADIAN = 6_300_000.0


class CemsSpuriousFalsifierDerivationError(RuntimeError):
    """Raised when Phase-D falsifier derivation cannot preserve frozen semantics."""


def _require_dependencies() -> None:
    if np is None or Geod is None:
        raise CemsSpuriousFalsifierDerivationError(
            "CEMS falsifier derivation requires requirements-cems-mask-support-challenge.txt"
        )


def _build_seed_index(rp10_dataset: Any) -> tuple[dict[int, Any], tuple[int, ...], int]:
    seed_rows: dict[int, Any] = {}
    seed_count = 0
    for row in range(rp10_dataset.height):
        seeds = _stage_d._seed_columns(_stage_d._read_row(rp10_dataset, row))
        seed_count += int(seeds.size)
        if seeds.size:
            seed_rows[row] = seeds.astype(np.int64, copy=False)
    if seed_count == 0:
        raise CemsSpuriousFalsifierDerivationError(
            "RP10 contains no current >10 m seed cells"
        )
    return seed_rows, tuple(seed_rows), seed_count


def _row_latitude(transform: Any, row: int) -> float:
    _longitude, latitude = _stage_d._cell_centre(transform, row, 0)
    latitude = float(latitude)
    if not math.isfinite(latitude):
        raise CemsSpuriousFalsifierDerivationError("seed-row latitude is not finite")
    return latitude


def _latitude_lower_bound_metres(candidate_latitude: float, seed_latitude: float) -> float:
    delta_radians = abs(math.radians(seed_latitude - candidate_latitude))
    return CONSERVATIVE_MERIDIONAL_METRES_PER_RADIAN * delta_radians


def _exact_minimum_distance_to_seed_row(
    candidate_row: int,
    candidate_column: int,
    seed_row: int,
    seed_columns: Any,
    *,
    transform: Any,
    geod: Any,
) -> float:
    """Evaluate every seed in one row with exact WGS84 Geod.inv."""
    if seed_columns.size == 0:
        return math.inf

    candidate_longitude, candidate_latitude = _stage_d._cell_centre(
        transform, candidate_row, candidate_column
    )
    candidate_longitudes = np.full(seed_columns.shape, candidate_longitude, dtype=float)
    candidate_latitudes = np.full(seed_columns.shape, candidate_latitude, dtype=float)
    seed_longitudes = (
        float(transform.c)
        + (seed_columns.astype(float) + 0.5) * float(transform.a)
        + (float(seed_row) + 0.5) * float(transform.b)
    )
    seed_latitude = _row_latitude(transform, seed_row)
    seed_latitudes = np.full(seed_columns.shape, seed_latitude, dtype=float)
    distances = np.asarray(
        _stage_d._distance_metres(
            geod,
            candidate_longitudes,
            candidate_latitudes,
            seed_longitudes,
            seed_latitudes,
        ),
        dtype=float,
    )
    if distances.size != seed_columns.size or not bool(np.isfinite(distances).all()):
        raise CemsSpuriousFalsifierDerivationError(
            "exact seed-row geodesic evaluation returned invalid distances"
        )
    return float(distances.min())


def _global_nearest_seed_distance(
    candidate_row: int,
    candidate_column: int,
    seed_rows: dict[int, Any],
    seed_row_numbers: tuple[int, ...],
    *,
    transform: Any,
    geod: Any,
) -> float:
    """Return the global exact nearest RP10-seed distance with safe row pruning."""
    if not seed_row_numbers:
        raise CemsSpuriousFalsifierDerivationError("seed-row index is empty")

    _candidate_longitude, candidate_latitude = _stage_d._cell_centre(
        transform, candidate_row, candidate_column
    )
    candidate_latitude = float(candidate_latitude)
    if not math.isfinite(candidate_latitude):
        raise CemsSpuriousFalsifierDerivationError("candidate latitude is not finite")

    insertion = bisect_left(seed_row_numbers, candidate_row)
    left = insertion - 1
    right = insertion
    best = math.inf

    while left >= 0 or right < len(seed_row_numbers):
        left_bound = math.inf
        right_bound = math.inf
        if left >= 0:
            left_row = seed_row_numbers[left]
            left_bound = _latitude_lower_bound_metres(
                candidate_latitude,
                _row_latitude(transform, left_row),
            )
            if left_bound > best:
                left = -1
                left_bound = math.inf
        if right < len(seed_row_numbers):
            right_row = seed_row_numbers[right]
            right_bound = _latitude_lower_bound_metres(
                candidate_latitude,
                _row_latitude(transform, right_row),
            )
            if right_bound > best:
                right = len(seed_row_numbers)
                right_bound = math.inf

        if left_bound == math.inf and right_bound == math.inf:
            break

        if left_bound <= right_bound:
            seed_row = seed_row_numbers[left]
            left -= 1
        else:
            seed_row = seed_row_numbers[right]
            right += 1

        distance = _exact_minimum_distance_to_seed_row(
            candidate_row,
            candidate_column,
            seed_row,
            seed_rows[seed_row],
            transform=transform,
            geod=geod,
        )
        if distance < best:
            best = distance

    if not math.isfinite(best):
        raise CemsSpuriousFalsifierDerivationError(
            "global nearest RP10-seed distance could not be established"
        )
    return best


def _seed_window(
    seed_rows: dict[int, Any],
    seed_row_numbers: tuple[int, ...],
    *,
    candidate_row: int,
    max_row_offset: int,
) -> dict[int, Any]:
    first = bisect_left(seed_row_numbers, candidate_row - max_row_offset)
    last = bisect_right(seed_row_numbers, candidate_row + max_row_offset)
    return {row: seed_rows[row] for row in seed_row_numbers[first:last]}


def _derive_records(
    mask_dataset: Any,
    rp10_dataset: Any,
) -> tuple[list[tuple[int, int, float]], dict[str, Any], Any, int, int]:
    """Return exact falsifier records plus frozen Stage-D reconciliation metadata."""
    _require_dependencies()
    try:
        transform = _stage_d._validate_common_grid(mask_dataset, rp10_dataset)
        geod = Geod(ellps="WGS84")
        contract = _stage_d._distance_contract(mask_dataset, transform, geod)
        seed_rows, seed_row_numbers, rp10_seed_cells = _build_seed_index(rp10_dataset)
    except (_stage_d.CemsSpuriousSupportChallengeError, CemsSpuriousFalsifierDerivationError):
        raise
    except Exception as exc:
        raise CemsSpuriousFalsifierDerivationError(
            "Stage-D grid/seed preparation failed"
        ) from exc

    candidate_cells = 0
    records: list[tuple[int, int, float]] = []
    for candidate_row in range(mask_dataset.height):
        try:
            candidates = _stage_d._candidate_columns(
                _stage_d._read_row(mask_dataset, candidate_row)
            )
        except _stage_d.CemsSpuriousSupportChallengeError:
            raise
        candidate_cells += int(candidates.size)
        if candidates.size == 0:
            continue

        window = _seed_window(
            seed_rows,
            seed_row_numbers,
            candidate_row=candidate_row,
            max_row_offset=contract["max_row_offset"],
        )
        same_row = _stage_d._same_row_membership(
            candidates,
            seed_rows.get(candidate_row, np.empty(0, dtype=np.int64)),
        )
        covered = _stage_d._mark_exactly_covered(
            candidates,
            candidate_row,
            window,
            transform=transform,
            geod=geod,
            distance_threshold_metres=contract["distance_threshold_metres"],
            max_col_offset=contract["max_col_offset"],
            initial_covered=same_row,
        )
        falsifier_columns = candidates[~covered]
        for column_value in falsifier_columns:
            column = int(column_value)
            nearest = _global_nearest_seed_distance(
                candidate_row,
                column,
                seed_rows,
                seed_row_numbers,
                transform=transform,
                geod=geod,
            )
            if nearest <= float(contract["distance_threshold_metres"]):
                raise CemsSpuriousFalsifierDerivationError(
                    "global nearest distance contradicts frozen Stage-D falsifier decision"
                )
            records.append((candidate_row, column, nearest))

    if candidate_cells == 0:
        raise CemsSpuriousFalsifierDerivationError("candidate support is empty")
    return records, contract, transform, candidate_cells, rp10_seed_cells


def derive_and_characterize_falsifiers(
    mask_dataset: Any,
    rp10_dataset: Any,
    *,
    expected_candidate_support_cells: int | None = None,
    expected_rp10_seed_cells: int | None = None,
    expected_falsifier_cells: int | None = None,
) -> dict[str, Any]:
    """Derive exact records and return only bounded #835 characterization evidence."""
    records, contract, transform, candidate_cells, rp10_seed_cells = _derive_records(
        mask_dataset, rp10_dataset
    )
    falsifier_cells = len(records)

    expectations = (
        ("candidate support", candidate_cells, expected_candidate_support_cells),
        ("RP10 seed", rp10_seed_cells, expected_rp10_seed_cells),
        ("falsifier", falsifier_cells, expected_falsifier_cells),
    )
    for label, observed, expected in expectations:
        if expected is None:
            continue
        if type(expected) is not int or expected < 0:
            raise CemsSpuriousFalsifierDerivationError(
                f"expected {label} count must be a non-negative integer"
            )
        if observed != expected:
            raise CemsSpuriousFalsifierDerivationError(
                f"{label} count drifted from preregistered expectation"
            )

    diagnostic = _diagnostic.characterize_falsifiers(
        records,
        transform=transform,
        raster_height=mask_dataset.height,
        raster_width=mask_dataset.width,
        distance_threshold_metres=float(contract["distance_threshold_metres"]),
        max_row_offset=int(contract["max_row_offset"]),
        max_col_offset=int(contract["max_col_offset"]),
        expected_falsifier_count=expected_falsifier_cells,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "stage_d_source_issue": STAGE_D_SOURCE_ISSUE,
        "candidate_support_cells": candidate_cells,
        "rp10_seed_cells": rp10_seed_cells,
        "candidate_farther_than_threshold_cells": falsifier_cells,
        "distance_threshold_metres": float(contract["distance_threshold_metres"]),
        "max_row_offset": int(contract["max_row_offset"]),
        "max_col_offset": int(contract["max_col_offset"]),
        "global_nearest_row_pruning_lower_bound_metres_per_radian": (
            CONSERVATIVE_MERIDIONAL_METRES_PER_RADIAN
        ),
        "diagnostic": diagnostic,
        "diagnostic_only": True,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
