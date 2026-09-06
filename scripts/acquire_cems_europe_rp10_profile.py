# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire the frozen CEMS Europe RP10 asset ephemerally and profile exact bytes."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_rp10_receipt as _receipt
    from scripts import profile_cems_europe_rp10_geotiff as _profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_rp10_receipt as _receipt
    import profile_cems_europe_rp10_geotiff as _profile

SCHEMA_VERSION = "oc-cems-rp10-geotiff-profile-receipt-v1"
PROFILE_ISSUE = 802


class CemsRp10ProfileAcquisitionError(RuntimeError):
    """Raised when trusted acquisition cannot produce the exact bounded profile."""


class _TeeResponse:
    """Delegate the validated response while copying exactly returned bytes to a sink."""

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
            raise CemsRp10ProfileAcquisitionError("CEMS profile response is not open")
        chunk = response.read(size)
        if type(chunk) is bytes and chunk:
            try:
                self._sink.write(chunk)
            except OSError as exc:
                raise CemsRp10ProfileAcquisitionError(
                    "CEMS profile ephemeral byte sink failed"
                ) from exc
        return chunk


def acquire_and_profile_cems_rp10(
    *,
    opener: Callable[..., Any] = _receipt._open_frozen_source,
    clock: Callable[[], str] = _receipt.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    profiler: Callable[[str | Path], dict[str, Any]] = _profile.profile_cems_rp10_geotiff,
) -> dict[str, Any]:
    """Return metadata only after exact #793 bytes were acquired and reverified."""
    try:
        with tempfile.TemporaryDirectory(prefix="oc-cems-rp10-profile-") as directory:
            path = Path(directory) / _receipt.FILENAME
            with path.open("xb") as sink:
                def tee_opener(request: Any, timeout: float) -> _TeeResponse:
                    return _TeeResponse(opener(request, timeout), sink)

                receipt = _receipt.acquire_cems_rp10_receipt(
                    opener=tee_opener,
                    clock=clock,
                    monotonic=monotonic,
                )
                sink.flush()

            if receipt["byte_count"] != _profile.ACCEPTED_BYTE_COUNT:
                raise CemsRp10ProfileAcquisitionError(
                    "CEMS profile byte count differs from accepted #793 receipt"
                )
            if receipt["sha256"] != _profile.ACCEPTED_SHA256:
                raise CemsRp10ProfileAcquisitionError(
                    "CEMS profile SHA-256 differs from accepted #793 receipt"
                )

            geotiff_profile = profiler(path)
            result = {
                "schema_version": SCHEMA_VERSION,
                "dataset_id": _receipt.DATASET_ID,
                "source_issue": _receipt.SOURCE_ISSUE,
                "profile_issue": PROFILE_ISSUE,
                "release": _receipt.RELEASE,
                "filename": _receipt.FILENAME,
                "requested_url": _receipt.SOURCE_URL,
                "final_url": _receipt.SOURCE_URL,
                "retrieved_at": receipt["retrieved_at"],
                "http_status": receipt["http_status"],
                "media_type": receipt["media_type"],
                "content_length_header": receipt["content_length_header"],
                "receipt_byte_count": receipt["byte_count"],
                "receipt_sha256": receipt["sha256"],
                "geotiff_profile": geotiff_profile,
                "external_bytes_persisted": False,
                "benchmark_use_authorized": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            }
        # TemporaryDirectory has removed the provider bytes before authority escapes.
        if path.exists():  # pragma: no cover - defensive postcondition
            raise CemsRp10ProfileAcquisitionError(
                "CEMS profile ephemeral provider bytes were not removed"
            )
        return result
    except (CemsRp10ProfileAcquisitionError, _receipt.CemsRp10ReceiptError):
        raise
    except _profile.CemsRp10GeoTiffProfileError as exc:
        raise CemsRp10ProfileAcquisitionError("CEMS GeoTIFF metadata profile failed") from exc
    except OSError as exc:
        raise CemsRp10ProfileAcquisitionError("CEMS profile ephemeral storage failed") from exc
