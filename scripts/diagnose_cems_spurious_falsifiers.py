# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded diagnostics for the exact CEMS spurious-depth falsifier support.

Issue #835 is descriptive follow-up evidence only. It must not weaken or reopen
Issue #823, whose frozen result remains CURRENT_RP10_NECESSARY_CONDITION_FAIL
with MASK_VALUE_SEMANTICS_NOT_IDENTIFIED / NO_BENCHMARK.

This module is deliberately synthetic-first. It accepts already-established
falsifier records ``(row, column, nearest_distance_metres)`` and produces only
bounded derived summaries. It performs no provider acquisition and does not
change the Stage-D challenge implementation.
"""

from __future__ import annotations

import hashlib
import math
import statistics
import struct
from typing import Any, Iterable

try:
    from scripts import challenge_cems_spurious_depth_support as _stage_d
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import challenge_cems_spurious_depth_support as _stage_d

SCHEMA_VERSION = "oc-cems-spurious-falsifier-diagnostic-v1"
SOURCE_ISSUE = 835
STAGE_D_SOURCE_ISSUE = 823
STAGE_D_VERDICT = "CURRENT_RP10_NECESSARY_CONDITION_FAIL"
STAGE_D_DISPOSITION = "MASK_VALUE_SEMANTICS_NOT_IDENTIFIED / NO_BENCHMARK"
EXPECTED_REAL_FALSIFIER_CELLS = 19_797
EXPECTED_REAL_CANDIDATE_SUPPORT_CELLS = 17_242_147
DISTANCE_THRESHOLD_METRES = 2123.5739672579953
MAX_ROW_OFFSET = 23
MAX_COL_OFFSET = 71
_DIGEST_STRUCT = struct.Struct(">qqd")
_DIGEST_ENCODING = "big_endian_struct_>qqd_row_col_nearest_distance_metres"


class CemsSpuriousFalsifierDiagnosticError(RuntimeError):
    """Raised when bounded Phase-D diagnostic inputs violate the frozen contract."""


def _nearest_rank(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise CemsSpuriousFalsifierDiagnosticError(
            "nearest-rank summary requires at least one falsifier"
        )
    if not 0.0 < probability <= 1.0:
        raise CemsSpuriousFalsifierDiagnosticError("nearest-rank probability is invalid")
    index = max(0, math.ceil(probability * len(sorted_values)) - 1)
    return float(sorted_values[index])


def _component_summary(cells: set[tuple[int, int]], *, eight_neighbour: bool) -> dict[str, Any]:
    if not cells:
        return {
            "component_count": 0,
            "min_size": 0,
            "median_size": 0.0,
            "max_size": 0,
            "largest_10_sizes": [],
        }

    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if eight_neighbour:
        offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

    remaining = set(cells)
    sizes: list[int] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        size = 0
        while stack:
            row, column = stack.pop()
            size += 1
            for row_offset, column_offset in offsets:
                neighbour = (row + row_offset, column + column_offset)
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
        sizes.append(size)

    sizes.sort()
    return {
        "component_count": len(sizes),
        "min_size": sizes[0],
        "median_size": float(statistics.median(sizes)),
        "max_size": sizes[-1],
        "largest_10_sizes": sorted(sizes, reverse=True)[:10],
    }


def _normalize_records(
    records: Iterable[tuple[int, int, float]],
    *,
    raster_height: int,
    raster_width: int,
    distance_threshold_metres: float,
) -> list[tuple[int, int, float]]:
    if type(raster_height) is not int or raster_height <= 0:
        raise CemsSpuriousFalsifierDiagnosticError("raster_height must be a positive integer")
    if type(raster_width) is not int or raster_width <= 0:
        raise CemsSpuriousFalsifierDiagnosticError("raster_width must be a positive integer")
    if not math.isfinite(distance_threshold_metres) or distance_threshold_metres <= 0.0:
        raise CemsSpuriousFalsifierDiagnosticError("distance threshold must be finite and positive")

    normalized: list[tuple[int, int, float]] = []
    seen: set[tuple[int, int]] = set()
    for record in records:
        if type(record) not in (tuple, list) or len(record) != 3:
            raise CemsSpuriousFalsifierDiagnosticError(
                "each falsifier record must be (row, column, nearest_distance_metres)"
            )
        row, column, distance = record
        if type(row) is not int or isinstance(row, bool) or not 0 <= row < raster_height:
            raise CemsSpuriousFalsifierDiagnosticError("falsifier row is outside the raster")
        if (
            type(column) is not int
            or isinstance(column, bool)
            or not 0 <= column < raster_width
        ):
            raise CemsSpuriousFalsifierDiagnosticError("falsifier column is outside the raster")
        if type(distance) not in (int, float) or isinstance(distance, bool):
            raise CemsSpuriousFalsifierDiagnosticError("nearest distance must be numeric")
        numeric_distance = float(distance)
        if not math.isfinite(numeric_distance):
            raise CemsSpuriousFalsifierDiagnosticError("nearest distance must be finite")
        if numeric_distance <= distance_threshold_metres:
            raise CemsSpuriousFalsifierDiagnosticError(
                "falsifier nearest distance must remain beyond the frozen threshold"
            )
        cell = (row, column)
        if cell in seen:
            raise CemsSpuriousFalsifierDiagnosticError("duplicate falsifier cell")
        seen.add(cell)
        normalized.append((row, column, numeric_distance))

    normalized.sort(key=lambda value: (value[0], value[1]))
    return normalized


def _digest_records(records: list[tuple[int, int, float]]) -> str:
    digest = hashlib.sha256()
    for row, column, distance in records:
        digest.update(_DIGEST_STRUCT.pack(row, column, distance))
    return digest.hexdigest()


def characterize_falsifiers(
    records: Iterable[tuple[int, int, float]],
    *,
    transform: Any,
    raster_height: int,
    raster_width: int,
    distance_threshold_metres: float = DISTANCE_THRESHOLD_METRES,
    max_row_offset: int = MAX_ROW_OFFSET,
    max_col_offset: int = MAX_COL_OFFSET,
    expected_falsifier_count: int | None = None,
) -> dict[str, Any]:
    """Return bounded deterministic diagnostics for an exact falsifier record set."""
    if type(max_row_offset) is not int or max_row_offset < 0:
        raise CemsSpuriousFalsifierDiagnosticError("max_row_offset must be non-negative")
    if type(max_col_offset) is not int or max_col_offset < 0:
        raise CemsSpuriousFalsifierDiagnosticError("max_col_offset must be non-negative")

    normalized = _normalize_records(
        records,
        raster_height=raster_height,
        raster_width=raster_width,
        distance_threshold_metres=distance_threshold_metres,
    )
    if expected_falsifier_count is not None:
        if type(expected_falsifier_count) is not int or expected_falsifier_count < 0:
            raise CemsSpuriousFalsifierDiagnosticError(
                "expected_falsifier_count must be a non-negative integer"
            )
        if len(normalized) != expected_falsifier_count:
            raise CemsSpuriousFalsifierDiagnosticError(
                "falsifier count drifted from the preregistered expectation"
            )

    cells = {(row, column) for row, column, _distance in normalized}
    distances = sorted(distance for _row, _column, distance in normalized)
    audit_sample: list[dict[str, Any]] = []
    longitudes: list[float] = []
    latitudes: list[float] = []
    edge_count = 0

    for index, (row, column, distance) in enumerate(normalized):
        longitude, latitude = _stage_d._cell_centre(transform, row, column)
        longitude = float(longitude)
        latitude = float(latitude)
        if not math.isfinite(longitude) or not math.isfinite(latitude):
            raise CemsSpuriousFalsifierDiagnosticError("cell centre is not finite")
        longitudes.append(longitude)
        latitudes.append(latitude)
        if (
            row < max_row_offset
            or row >= raster_height - max_row_offset
            or column < max_col_offset
            or column >= raster_width - max_col_offset
        ):
            edge_count += 1
        if index < 16:
            audit_sample.append(
                {
                    "row": row,
                    "column": column,
                    "longitude": longitude,
                    "latitude": latitude,
                    "nearest_distance_metres": distance,
                }
            )

    if normalized:
        rows = [row for row, _column, _distance in normalized]
        columns = [column for _row, column, _distance in normalized]
        raster_bbox: dict[str, int] | None = {
            "min_row": min(rows),
            "max_row": max(rows),
            "min_column": min(columns),
            "max_column": max(columns),
        }
        centre_bounds: dict[str, float] | None = {
            "min_longitude": min(longitudes),
            "max_longitude": max(longitudes),
            "min_latitude": min(latitudes),
            "max_latitude": max(latitudes),
        }
        distance_summary: dict[str, float] | None = {
            "minimum": distances[0],
            "q25_nearest_rank": _nearest_rank(distances, 0.25),
            "median_nearest_rank": _nearest_rank(distances, 0.50),
            "q75_nearest_rank": _nearest_rank(distances, 0.75),
            "q95_nearest_rank": _nearest_rank(distances, 0.95),
            "q99_nearest_rank": _nearest_rank(distances, 0.99),
            "maximum": distances[-1],
        }
    else:
        raster_bbox = None
        centre_bounds = None
        distance_summary = None

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "stage_d_source_issue": STAGE_D_SOURCE_ISSUE,
        "stage_d_verdict": STAGE_D_VERDICT,
        "stage_d_disposition": STAGE_D_DISPOSITION,
        "falsifier_count": len(normalized),
        "distance_threshold_metres": float(distance_threshold_metres),
        "falsifier_digest_sha256": _digest_records(normalized),
        "falsifier_digest_encoding": _DIGEST_ENCODING,
        "raster_cell_bbox": raster_bbox,
        "cell_centre_bounds": centre_bounds,
        "nearest_distance_summary_metres": distance_summary,
        "first_16_falsifiers": audit_sample,
        "components_4_neighbour": _component_summary(cells, eight_neighbour=False),
        "components_8_neighbour": _component_summary(cells, eight_neighbour=True),
        "edge_envelope_falsifier_cells": edge_count,
        "interior_falsifier_cells": len(normalized) - edge_count,
        "max_row_offset": max_row_offset,
        "max_col_offset": max_col_offset,
        "diagnostic_only": True,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
