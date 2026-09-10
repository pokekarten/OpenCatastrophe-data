# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire exact CEMS RP10/spurious-depth bytes and run Issue #823 Stage D.

This worker composes only already frozen provider identities. It does not expose a
caller-selectable URL, filename, mask, threshold, distance model, or output path.
Provider bytes are copied into one private TemporaryDirectory only long enough to
bind their complete SHA-256 identities. The already-reviewed RP10 identity binder
copies those verified bytes into Rasterio MemoryFiles; path-addressable files are
then deleted before any raster value is read.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import acquire_cems_europe_rp10_receipt as _rp10_receipt
    from scripts import challenge_cems_spurious_depth_support as _challenge
    from scripts import profile_cems_europe_mask_geotiffs as _mask_metadata
    from scripts import profile_cems_europe_rp10_geotiff as _rp10_profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_mask_receipts as _masks
    import acquire_cems_europe_rp10_receipt as _rp10_receipt
    import challenge_cems_spurious_depth_support as _challenge
    import profile_cems_europe_mask_geotiffs as _mask_metadata
    import profile_cems_europe_rp10_geotiff as _rp10_profile

SCHEMA_VERSION = "oc-cems-spurious-support-challenge-receipt-v1"
SOURCE_ISSUE = 823
SPURIOUS_KIND = "spurious_depth"
SPURIOUS_FILENAME = "Europe_spurious_depth_areas.tif"
EXPECTED_CANDIDATE_SUPPORT_CELLS = 17_242_147


class CemsSpuriousSupportAcquisitionError(RuntimeError):
    """Raised when exact-byte Stage-D acquisition or evaluation fails closed."""


class _TeeResponse:
    """Delegate a fixed validated response while copying the exact stream to disk."""

    def __init__(self, response_cm: Any, sink: Any):
        self._response_cm = response_cm
        self._sink = sink
        self._response: Any | None = None

    def __enter__(self) -> "_TeeResponse":
        self._response = self._response_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return self._response_cm.__exit__(exc_type, exc, tb)

    def __getattr__(self, name: str) -> Any:
        if self._response is None:
            raise AttributeError(name)
        return getattr(self._response, name)

    def read(self, size: int = -1) -> Any:
        if self._response is None:
            raise CemsSpuriousSupportAcquisitionError("CEMS Stage-D response is not open")
        chunk = self._response.read(size)
        if type(chunk) is bytes and chunk:
            try:
                self._sink.write(chunk)
            except OSError as exc:
                raise CemsSpuriousSupportAcquisitionError(
                    "CEMS Stage-D ephemeral byte sink failed"
                ) from exc
        return chunk


def _materialize_rp10(
    path: Path,
    *,
    opener: Callable[[Any, float], Any],
    clock: Callable[[], str],
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    try:
        with path.open("xb") as sink:
            def tee_opener(request: Any, timeout: float) -> _TeeResponse:
                return _TeeResponse(opener(request, timeout), sink)

            receipt = _rp10_receipt.acquire_cems_rp10_receipt(
                opener=tee_opener,
                clock=clock,
                monotonic=monotonic,
            )
            sink.flush()
        if receipt.get("byte_count") != _rp10_profile.ACCEPTED_BYTE_COUNT:
            raise CemsSpuriousSupportAcquisitionError(
                "CEMS Stage-D RP10 receipt byte count differs from accepted #793 identity"
            )
        if receipt.get("sha256") != _rp10_profile.ACCEPTED_SHA256:
            raise CemsSpuriousSupportAcquisitionError(
                "CEMS Stage-D RP10 receipt SHA-256 differs from accepted #793 identity"
            )
        return receipt
    except (CemsSpuriousSupportAcquisitionError, _rp10_receipt.CemsRp10ReceiptError):
        raise
    except OSError as exc:
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D RP10 ephemeral materialization failed"
        ) from exc


def _materialize_spurious_mask(
    path: Path,
    *,
    opener: Callable[[Any, float], Any],
    clock: Callable[[], str],
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    accepted = _mask_metadata.MASK_RECEIPTS[SPURIOUS_KIND]
    if accepted.get("filename") != SPURIOUS_FILENAME:
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D accepted spurious-depth filename drifted"
        )
    try:
        with path.open("xb") as sink:
            def tee_opener(request: Any, timeout: float) -> _TeeResponse:
                return _TeeResponse(opener(request, timeout), sink)

            receipt = _masks._acquire_one(
                SPURIOUS_KIND,
                SPURIOUS_FILENAME,
                opener=tee_opener,
                clock=clock,
                monotonic=monotonic,
            )
            sink.flush()
        if receipt.get("byte_count") != accepted["byte_count"]:
            raise CemsSpuriousSupportAcquisitionError(
                "CEMS Stage-D mask receipt byte count differs from accepted #809 identity"
            )
        if receipt.get("sha256") != accepted["sha256"]:
            raise CemsSpuriousSupportAcquisitionError(
                "CEMS Stage-D mask receipt SHA-256 differs from accepted #809 identity"
            )
        return receipt
    except (CemsSpuriousSupportAcquisitionError, _masks.CemsMaskReceiptError):
        raise
    except OSError as exc:
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D mask ephemeral materialization failed"
        ) from exc


def _validate_challenge_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or result.get("schema_version") != _challenge.SCHEMA_VERSION:
        raise CemsSpuriousSupportAcquisitionError("CEMS Stage-D challenge result schema is invalid")
    if result.get("candidate_support_cells") != EXPECTED_CANDIDATE_SUPPORT_CELLS:
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D candidate support count differs from accepted Stage-B inventory"
        )
    if result.get("verdict") not in {
        "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION",
        "CURRENT_RP10_NECESSARY_CONDITION_FAIL",
    }:
        raise CemsSpuriousSupportAcquisitionError("CEMS Stage-D challenge verdict is invalid")
    for field in (
        "mask_value_semantics_verified",
        "per_cell_scientific_correctness_verified",
        "benchmark_use_authorized",
        "model_use_authorized",
        "publication_authorized",
        "external_bytes_persisted",
    ):
        if result.get(field) is not False:
            raise CemsSpuriousSupportAcquisitionError(
                f"CEMS Stage-D challenge exceeded authority ceiling: {field}"
            )
    if result.get("small_channel_filter_reconstructed") is not False:
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D challenge claimed unavailable small-channel reconstruction"
        )
    return result


def acquire_and_challenge_cems_spurious_support(
    *,
    rp10_opener: Callable[[Any, float], Any] = _rp10_receipt._open_frozen_source,
    mask_opener: Callable[[Any, float], Any] = _masks._open_frozen_source,
    clock: Callable[[], str] = _rp10_receipt.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    challenger: Callable[[Any, Any], dict[str, Any]] = _challenge.challenge_spurious_support,
) -> dict[str, Any]:
    """Run exact-byte Stage D and return bounded evidence after deleting provider files."""
    paths: list[Path] = []
    rp10_memory = None
    mask_memory = None
    try:
        with tempfile.TemporaryDirectory(prefix="oc-cems-spurious-stage-d-") as raw_directory:
            directory = Path(raw_directory)
            rp10_path = directory / _rp10_receipt.FILENAME
            mask_path = directory / SPURIOUS_FILENAME
            paths.extend((rp10_path, mask_path))

            rp10_receipt = _materialize_rp10(
                rp10_path,
                opener=rp10_opener,
                clock=clock,
                monotonic=monotonic,
            )
            mask_receipt = _materialize_spurious_mask(
                mask_path,
                opener=mask_opener,
                clock=clock,
                monotonic=monotonic,
            )

            accepted_mask = _mask_metadata.MASK_RECEIPTS[SPURIOUS_KIND]
            try:
                rp10_memory, _rp10_count, _rp10_sha = _rp10_profile._verify_file_identity(
                    rp10_path,
                    expected_byte_count=_rp10_profile.ACCEPTED_BYTE_COUNT,
                    expected_sha256=_rp10_profile.ACCEPTED_SHA256,
                )
                mask_memory, _mask_count, _mask_sha = _rp10_profile._verify_file_identity(
                    mask_path,
                    expected_byte_count=accepted_mask["byte_count"],
                    expected_sha256=accepted_mask["sha256"],
                )
            except _rp10_profile.CemsRp10GeoTiffProfileError as exc:
                raise CemsSpuriousSupportAcquisitionError(
                    "CEMS Stage-D receipt-bound MemoryFile identity failed"
                ) from exc

            # The verified MemoryFiles now own the exact reader bytes. Remove all
            # path-addressable provider payloads before opening either GDAL dataset.
            try:
                rp10_path.unlink()
                mask_path.unlink()
            except OSError as exc:
                raise CemsSpuriousSupportAcquisitionError(
                    "CEMS Stage-D verified provider files could not be removed before reading"
                ) from exc
            if rp10_path.exists() or mask_path.exists():  # pragma: no cover - defensive
                raise CemsSpuriousSupportAcquisitionError(
                    "CEMS Stage-D path-addressable provider bytes remain before reading"
                )

            try:
                with mask_memory, rp10_memory:
                    with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                        challenge_result = _validate_challenge_result(
                            challenger(mask_dataset, rp10_dataset)
                        )
            except CemsSpuriousSupportAcquisitionError:
                raise
            except Exception as exc:
                raise CemsSpuriousSupportAcquisitionError(
                    "CEMS Stage-D exact-byte raster challenge failed"
                ) from exc
            finally:
                # Close defensively even if a pre-context exception interrupted setup.
                if mask_memory is not None:
                    mask_memory.close()
                if rp10_memory is not None:
                    rp10_memory.close()

            result = {
                "schema_version": SCHEMA_VERSION,
                "dataset_id": _rp10_receipt.DATASET_ID,
                "source_issue": SOURCE_ISSUE,
                "release": _rp10_receipt.RELEASE,
                "rp10_receipt": rp10_receipt,
                "spurious_depth_receipt": mask_receipt,
                "challenge": challenge_result,
                "receipt_to_reader_binding": "verified_bytes_memoryfile",
                "external_bytes_persisted": False,
                "mask_value_semantics_verified": False,
                "per_cell_scientific_correctness_verified": False,
                "benchmark_use_authorized": False,
                "model_use_authorized": False,
                "publication_authorized": False,
            }

        if any(path.exists() for path in paths):  # pragma: no cover - defensive postcondition
            raise CemsSpuriousSupportAcquisitionError(
                "CEMS Stage-D provider bytes were not removed"
            )
        return result
    except CemsSpuriousSupportAcquisitionError:
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
        raise CemsSpuriousSupportAcquisitionError(
            "CEMS Stage-D acquisition/challenge failed"
        ) from exc
