# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire frozen CEMS bytes and derive bounded Issue #835 diagnostics.

This trusted worker composes the already-reviewed #831 exact-byte acquisition
with the merged #835 derivation layer. It exposes no caller-selectable provider,
URL, filename, threshold, count, geometry, output path, or authority setting.
Provider bytes are verified into Rasterio MemoryFiles and path-addressable copies
are removed before any GDAL dataset is opened.
"""

from __future__ import annotations

import math
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_cems_spurious_support_challenge as _stage_d_worker
    from scripts import derive_cems_spurious_falsifiers as _derive
    from scripts import diagnose_cems_spurious_falsifiers as _diagnostic
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_spurious_support_challenge as _stage_d_worker
    import derive_cems_spurious_falsifiers as _derive
    import diagnose_cems_spurious_falsifiers as _diagnostic

SCHEMA_VERSION = "oc-cems-spurious-falsifier-diagnostic-receipt-v1"
SOURCE_ISSUE = 835
EXPECTED_CANDIDATE_SUPPORT_CELLS = 17_242_147
EXPECTED_RP10_SEED_CELLS = 716_876
EXPECTED_FALSIFIER_CELLS = 19_797
EXPECTED_DISTANCE_THRESHOLD_METRES = 2123.5739672579953
EXPECTED_MAX_ROW_OFFSET = 23
EXPECTED_MAX_COL_OFFSET = 71
EXPECTED_LOWER_BOUND_METRES_PER_RADIAN = 6_300_000.0
EXPECTED_PYPROJ_VERSION = "3.7.2"


class CemsSpuriousFalsifierDiagnosticAcquisitionError(RuntimeError):
    """Raised when exact-byte #835 acquisition/diagnostics fail closed."""


def _require_false(mapping: dict[str, Any], field: str, *, label: str) -> None:
    if mapping.get(field) is not False:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"{label} exceeded authority ceiling: {field}"
        )


def _validate_digest(value: Any) -> None:
    if type(value) is not str or len(value) != 64:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 falsifier digest is invalid"
        )
    if any(character not in "0123456789abcdef" for character in value):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 falsifier digest is not lowercase hexadecimal"
        )


def _validate_distance_summary(summary: Any) -> None:
    if type(summary) is not dict:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 nearest-distance summary is invalid"
        )
    fields = (
        "minimum",
        "q25_nearest_rank",
        "median_nearest_rank",
        "q75_nearest_rank",
        "q95_nearest_rank",
        "q99_nearest_rank",
        "maximum",
    )
    values: list[float] = []
    for field in fields:
        value = summary.get(field)
        if type(value) not in (int, float) or isinstance(value, bool):
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                f"CEMS #835 distance summary field is invalid: {field}"
            )
        numeric = float(value)
        if not math.isfinite(numeric):
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                f"CEMS #835 distance summary field is non-finite: {field}"
            )
        values.append(numeric)
    if values != sorted(values):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 nearest-distance ranks are not monotone"
        )
    if values[0] <= EXPECTED_DISTANCE_THRESHOLD_METRES:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 diagnostic includes a non-falsifier distance"
        )


def _validate_components(summary: Any, *, label: str) -> None:
    if type(summary) is not dict:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} component summary is invalid"
        )
    component_count = summary.get("component_count")
    minimum = summary.get("min_size")
    median = summary.get("median_size")
    maximum = summary.get("max_size")
    largest = summary.get("largest_10_sizes")
    if type(component_count) is not int or component_count <= 0:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} component count is invalid"
        )
    if type(minimum) is not int or minimum <= 0:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} minimum component size is invalid"
        )
    if type(maximum) is not int or maximum < minimum:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} maximum component size is invalid"
        )
    if type(median) not in (int, float) or isinstance(median, bool):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} median component size is invalid"
        )
    if not minimum <= float(median) <= maximum:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} median component size is outside bounds"
        )
    if type(largest) is not list or not 1 <= len(largest) <= 10:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} largest-component list is invalid"
        )
    if any(type(size) is not int or size <= 0 for size in largest):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} largest-component size is invalid"
        )
    if largest != sorted(largest, reverse=True) or largest[0] != maximum:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            f"CEMS #835 {label} largest-component ordering is invalid"
        )


def _validate_derivation_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or result.get("schema_version") != _derive.SCHEMA_VERSION:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 derivation result schema is invalid"
        )
    exact_fields = {
        "source_issue": SOURCE_ISSUE,
        "stage_d_source_issue": 823,
        "candidate_support_cells": EXPECTED_CANDIDATE_SUPPORT_CELLS,
        "rp10_seed_cells": EXPECTED_RP10_SEED_CELLS,
        "candidate_farther_than_threshold_cells": EXPECTED_FALSIFIER_CELLS,
        "distance_threshold_metres": EXPECTED_DISTANCE_THRESHOLD_METRES,
        "max_row_offset": EXPECTED_MAX_ROW_OFFSET,
        "max_col_offset": EXPECTED_MAX_COL_OFFSET,
        "global_nearest_row_pruning_lower_bound_metres_per_radian": (
            EXPECTED_LOWER_BOUND_METRES_PER_RADIAN
        ),
    }
    for field, expected in exact_fields.items():
        if result.get(field) != expected:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                f"CEMS #835 derivation contract drifted: {field}"
            )

    diagnostic = result.get("diagnostic")
    if type(diagnostic) is not dict or diagnostic.get("schema_version") != _diagnostic.SCHEMA_VERSION:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded diagnostic schema is invalid"
        )
    if diagnostic.get("source_issue") != SOURCE_ISSUE:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded diagnostic issue binding drifted"
        )
    if diagnostic.get("stage_d_source_issue") != 823:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 Stage-D source binding drifted"
        )
    if diagnostic.get("stage_d_verdict") != _diagnostic.STAGE_D_VERDICT:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 changed the frozen #823 verdict"
        )
    if diagnostic.get("stage_d_disposition") != _diagnostic.STAGE_D_DISPOSITION:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 changed the frozen #823 disposition"
        )
    if diagnostic.get("falsifier_count") != EXPECTED_FALSIFIER_CELLS:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded falsifier count drifted"
        )
    if diagnostic.get("distance_threshold_metres") != EXPECTED_DISTANCE_THRESHOLD_METRES:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded diagnostic threshold drifted"
        )
    if diagnostic.get("max_row_offset") != EXPECTED_MAX_ROW_OFFSET:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded diagnostic row envelope drifted"
        )
    if diagnostic.get("max_col_offset") != EXPECTED_MAX_COL_OFFSET:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 bounded diagnostic column envelope drifted"
        )

    _validate_digest(diagnostic.get("falsifier_digest_sha256"))
    if diagnostic.get("falsifier_digest_encoding") != (
        "big_endian_struct_>qqd_row_col_nearest_distance_metres"
    ):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 falsifier digest encoding drifted"
        )
    _validate_distance_summary(diagnostic.get("nearest_distance_summary_metres"))

    sample = diagnostic.get("first_16_falsifiers")
    if type(sample) is not list or len(sample) != min(16, EXPECTED_FALSIFIER_CELLS):
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 audit sample size is invalid"
        )
    previous_cell: tuple[int, int] | None = None
    for item in sample:
        if type(item) is not dict:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                "CEMS #835 audit sample item is invalid"
            )
        row = item.get("row")
        column = item.get("column")
        if type(row) is not int or type(column) is not int:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                "CEMS #835 audit sample cell index is invalid"
            )
        current_cell = (row, column)
        if previous_cell is not None and current_cell <= previous_cell:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                "CEMS #835 audit sample is not strict row-major order"
            )
        previous_cell = current_cell
        for field in ("longitude", "latitude", "nearest_distance_metres"):
            value = item.get(field)
            if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    f"CEMS #835 audit sample field is invalid: {field}"
                )
        if float(item["nearest_distance_metres"]) <= EXPECTED_DISTANCE_THRESHOLD_METRES:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                "CEMS #835 audit sample contains a non-falsifier distance"
            )

    _validate_components(diagnostic.get("components_4_neighbour"), label="4-neighbour")
    _validate_components(diagnostic.get("components_8_neighbour"), label="8-neighbour")
    edge = diagnostic.get("edge_envelope_falsifier_cells")
    interior = diagnostic.get("interior_falsifier_cells")
    if type(edge) is not int or type(interior) is not int or edge < 0 or interior < 0:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 edge/interior counts are invalid"
        )
    if edge + interior != EXPECTED_FALSIFIER_CELLS:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 edge/interior counts do not reconcile"
        )

    for label, mapping in (("derivation", result), ("diagnostic", diagnostic)):
        if mapping.get("diagnostic_only") is not True:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                f"CEMS #835 {label} lost diagnostic-only boundary"
            )
        if mapping.get("small_channel_filter_reconstructed") is not False:
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                f"CEMS #835 {label} claimed unavailable small-channel reconstruction"
            )
        for field in (
            "mask_value_semantics_verified",
            "per_cell_scientific_correctness_verified",
            "benchmark_use_authorized",
            "model_use_authorized",
            "publication_authorized",
            "external_bytes_persisted",
        ):
            _require_false(mapping, field, label=label)
    return result


def acquire_and_diagnose_cems_spurious_falsifiers(
    *,
    rp10_opener: Callable[[Any, float], Any] = _stage_d_worker._rp10_receipt._open_frozen_source,
    mask_opener: Callable[[Any, float], Any] = _stage_d_worker._masks._open_frozen_source,
    clock: Callable[[], str] = _stage_d_worker._rp10_receipt.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    deriver: Callable[..., dict[str, Any]] = _derive.derive_and_characterize_falsifiers,
) -> dict[str, Any]:
    """Reacquire exact frozen bytes and return only validated bounded #835 evidence."""
    runtime_version = getattr(_stage_d_worker._challenge.pyproj, "__version__", None)
    if runtime_version != EXPECTED_PYPROJ_VERSION:
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 pyproj runtime differs from frozen 3.7.2 contract"
        )

    paths: list[Path] = []
    rp10_memory = None
    mask_memory = None
    try:
        with tempfile.TemporaryDirectory(prefix="oc-cems-spurious-phase-d-") as raw_directory:
            directory = Path(raw_directory)
            rp10_path = directory / _stage_d_worker._rp10_receipt.FILENAME
            mask_path = directory / _stage_d_worker.SPURIOUS_FILENAME
            paths.extend((rp10_path, mask_path))

            try:
                rp10_receipt = _stage_d_worker._materialize_rp10(
                    rp10_path,
                    opener=rp10_opener,
                    clock=clock,
                    monotonic=monotonic,
                )
                mask_receipt = _stage_d_worker._materialize_spurious_mask(
                    mask_path,
                    opener=mask_opener,
                    clock=clock,
                    monotonic=monotonic,
                )
            except _stage_d_worker.CemsSpuriousSupportAcquisitionError as exc:
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    "CEMS #835 exact receipt acquisition failed"
                ) from exc

            accepted_mask = _stage_d_worker._mask_metadata.MASK_RECEIPTS[
                _stage_d_worker.SPURIOUS_KIND
            ]
            try:
                rp10_memory, _rp10_count, _rp10_sha = (
                    _stage_d_worker._rp10_profile._verify_file_identity(
                        rp10_path,
                        expected_byte_count=_stage_d_worker._rp10_profile.ACCEPTED_BYTE_COUNT,
                        expected_sha256=_stage_d_worker._rp10_profile.ACCEPTED_SHA256,
                    )
                )
                mask_memory, _mask_count, _mask_sha = (
                    _stage_d_worker._rp10_profile._verify_file_identity(
                        mask_path,
                        expected_byte_count=accepted_mask["byte_count"],
                        expected_sha256=accepted_mask["sha256"],
                    )
                )
            except _stage_d_worker._rp10_profile.CemsRp10GeoTiffProfileError as exc:
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    "CEMS #835 receipt-bound MemoryFile identity failed"
                ) from exc

            try:
                rp10_path.unlink()
                mask_path.unlink()
            except OSError as exc:
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    "CEMS #835 verified provider files could not be removed before reading"
                ) from exc
            if rp10_path.exists() or mask_path.exists():  # pragma: no cover - defensive
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    "CEMS #835 path-addressable provider bytes remain before reading"
                )

            try:
                with mask_memory, rp10_memory:
                    with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                        derivation = _validate_derivation_result(
                            deriver(
                                mask_dataset,
                                rp10_dataset,
                                expected_candidate_support_cells=(
                                    EXPECTED_CANDIDATE_SUPPORT_CELLS
                                ),
                                expected_rp10_seed_cells=EXPECTED_RP10_SEED_CELLS,
                                expected_falsifier_cells=EXPECTED_FALSIFIER_CELLS,
                            )
                        )
            except CemsSpuriousFalsifierDiagnosticAcquisitionError:
                raise
            except Exception as exc:
                raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                    "CEMS #835 exact-byte falsifier derivation failed"
                ) from exc
            finally:
                if mask_memory is not None:
                    mask_memory.close()
                if rp10_memory is not None:
                    rp10_memory.close()

            result = {
                "schema_version": SCHEMA_VERSION,
                "dataset_id": _stage_d_worker._rp10_receipt.DATASET_ID,
                "source_issue": SOURCE_ISSUE,
                "release": _stage_d_worker._rp10_receipt.RELEASE,
                "pyproj_version": runtime_version,
                "rp10_receipt": rp10_receipt,
                "spurious_depth_receipt": mask_receipt,
                "derivation": derivation,
                "receipt_to_reader_binding": "verified_bytes_memoryfile",
                "external_bytes_persisted": False,
                "diagnostic_only": True,
                "small_channel_filter_reconstructed": False,
                "mask_value_semantics_verified": False,
                "per_cell_scientific_correctness_verified": False,
                "benchmark_use_authorized": False,
                "model_use_authorized": False,
                "publication_authorized": False,
            }

        if any(path.exists() for path in paths):  # pragma: no cover - defensive
            raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
                "CEMS #835 provider bytes were not removed"
            )
        return result
    except CemsSpuriousFalsifierDiagnosticAcquisitionError:
        if mask_memory is not None:
            mask_memory.close()
        if rp10_memory is not None:
            rp10_memory.close()
        raise
    except Exception as exc:
        if mask_memory is not None:
            mask_memory.close()
        if rp10_memory is not None:
            rp10_memory.close()
        raise CemsSpuriousFalsifierDiagnosticAcquisitionError(
            "CEMS #835 acquisition/diagnostic worker failed"
        ) from exc
