# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire exact CEMS masks ephemerally, profile metadata, and compare to RP10."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import acquire_cems_europe_rp10_profile as _rp10_profile
    from scripts import profile_cems_europe_mask_geotiffs as _profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_mask_receipts as _masks
    import acquire_cems_europe_rp10_profile as _rp10_profile
    import profile_cems_europe_mask_geotiffs as _profile

SCHEMA_VERSION = "oc-cems-mask-geotiff-profiles-v1"
PROFILE_RECEIPT_SCHEMA_VERSION = "oc-cems-mask-geotiff-profile-receipt-v1"
SOURCE_ISSUE = 809
PROFILE_ISSUE = 816


class CemsMaskProfilesAcquisitionError(RuntimeError):
    """Raised when trusted acquisition cannot produce exact bounded mask profiles."""


class _TeeResponse:
    """Delegate a validated response while copying exactly returned bytes to a sink."""

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
        response = self._response
        if response is None:
            raise AttributeError(name)
        return getattr(response, name)

    def read(self, size: int = -1) -> Any:
        response = self._response
        if response is None:
            raise CemsMaskProfilesAcquisitionError("CEMS mask profile response is not open")
        chunk = response.read(size)
        if type(chunk) is bytes and chunk:
            try:
                self._sink.write(chunk)
            except OSError as exc:
                raise CemsMaskProfilesAcquisitionError(
                    "CEMS mask profile ephemeral byte sink failed"
                ) from exc
        return chunk


def _profile_one(
    kind: str,
    filename: str,
    directory: Path,
    *,
    opener: Callable[[Any, float], Any],
    clock: Callable[[], str],
    monotonic: Callable[[], float],
    profiler: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], Path]:
    path = directory / filename
    try:
        with path.open("xb") as sink:
            def tee_opener(request: Any, timeout: float) -> _TeeResponse:
                return _TeeResponse(opener(request, timeout), sink)

            receipt = _masks._acquire_one(
                kind,
                filename,
                opener=tee_opener,
                clock=clock,
                monotonic=monotonic,
            )
            sink.flush()

        expected = _profile.MASK_RECEIPTS[kind]
        if receipt["byte_count"] != expected["byte_count"]:
            raise CemsMaskProfilesAcquisitionError(
                "CEMS mask profile byte count differs from accepted #809 receipt"
            )
        if receipt["sha256"] != expected["sha256"]:
            raise CemsMaskProfilesAcquisitionError(
                "CEMS mask profile SHA-256 differs from accepted #809 receipt"
            )
        geotiff_profile = profiler(path, mask_kind=kind)
        return (
            {
                "schema_version": PROFILE_RECEIPT_SCHEMA_VERSION,
                "dataset_id": _masks.DATASET_ID,
                "source_issue": SOURCE_ISSUE,
                "profile_issue": PROFILE_ISSUE,
                "release": _masks.RELEASE,
                "mask_kind": kind,
                "filename": filename,
                "requested_url": receipt["requested_url"],
                "final_url": receipt["final_url"],
                "retrieved_at": receipt["retrieved_at"],
                "http_status": receipt["http_status"],
                "media_type": receipt["media_type"],
                "content_length_header": receipt["content_length_header"],
                "receipt_byte_count": receipt["byte_count"],
                "receipt_sha256": receipt["sha256"],
                "geotiff_profile": geotiff_profile,
                "external_bytes_persisted": False,
                "mask_values_inspected": False,
                "mask_value_semantics_verified": False,
                "benchmark_use_authorized": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            },
            path,
        )
    except (CemsMaskProfilesAcquisitionError, _masks.CemsMaskReceiptError):
        raise
    except _profile.CemsMaskGeoTiffProfileError as exc:
        raise CemsMaskProfilesAcquisitionError("CEMS mask GeoTIFF metadata profile failed") from exc
    except OSError as exc:
        raise CemsMaskProfilesAcquisitionError("CEMS mask profile ephemeral storage failed") from exc


def acquire_and_profile_cems_masks_against_rp10(
    *,
    opener: Callable[[Any, float], Any] = _masks._open_frozen_source,
    clock: Callable[[], str] = _masks._base.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    profiler: Callable[..., dict[str, Any]] = _profile.profile_cems_mask_geotiff,
    rp10_acquirer: Callable[[], dict[str, Any]] = _rp10_profile.acquire_and_profile_cems_rp10,
) -> dict[str, Any]:
    """Return same-runtime structural profiles while retaining no provider payload bytes."""
    try:
        rp10_receipt = rp10_acquirer()
        if rp10_receipt.get("external_bytes_persisted") is not False:
            raise CemsMaskProfilesAcquisitionError(
                "RP10 reference profile persisted external bytes"
            )
        rp10_geotiff = rp10_receipt.get("geotiff_profile")
        if type(rp10_geotiff) is not dict:
            raise CemsMaskProfilesAcquisitionError("RP10 reference GeoTIFF profile is absent")

        paths: list[Path] = []
        profile_receipts: list[dict[str, Any]] = []
        comparisons: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="oc-cems-mask-profiles-") as raw_directory:
            directory = Path(raw_directory)
            for kind, filename in _masks.ASSETS:
                profile_receipt, path = _profile_one(
                    kind,
                    filename,
                    directory,
                    opener=opener,
                    clock=clock,
                    monotonic=monotonic,
                    profiler=profiler,
                )
                paths.append(path)
                profile_receipts.append(profile_receipt)
                comparisons.append(
                    _profile.compare_mask_profile_to_rp10(
                        profile_receipt["geotiff_profile"],
                        rp10_geotiff,
                    )
                )

        if any(path.exists() for path in paths):  # pragma: no cover - defensive postcondition
            raise CemsMaskProfilesAcquisitionError(
                "CEMS mask profile ephemeral provider bytes were not removed"
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": _masks.DATASET_ID,
            "source_issue": SOURCE_ISSUE,
            "profile_issue": PROFILE_ISSUE,
            "release": _masks.RELEASE,
            "rp10_profile_receipt": rp10_receipt,
            "mask_profile_receipts": profile_receipts,
            "comparisons": comparisons,
            "external_bytes_persisted": False,
            "mask_values_inspected": False,
            "mask_value_semantics_verified": False,
            "benchmark_use_authorized": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
    except CemsMaskProfilesAcquisitionError:
        raise
    except Exception as exc:
        raise CemsMaskProfilesAcquisitionError(
            "CEMS mask profile acquisition/comparison failed"
        ) from exc
