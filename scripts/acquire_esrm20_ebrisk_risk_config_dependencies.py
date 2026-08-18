# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Transiently re-materialize fixed receipted EBRISK configs for dependency profiling."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from scripts import verify_esrm20_ebrisk_risk_config_dependencies as bridge
except ModuleNotFoundError:  # pragma: no cover
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    import verify_esrm20_ebrisk_risk_config_dependencies as bridge


class EbriskDependencyAcquisitionError(RuntimeError):
    """Raised when an exact receipted EBRISK candidate cannot be safely profiled."""


def _acquire_exact_payload(
    key: str, *, opener: Any | None, monotonic: Any
) -> bytes:
    try:
        spec = bridge.config_spec(key)
        target = validate_target(
            source_issue=bridge.SOURCE_ISSUE,
            dataset_id=bridge.DATASET_ID,
            project_id=bridge.PROJECT_ID,
            commit_sha=bridge.COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except (bridge.VerifiedEbriskConfigError, EfehrReceiptError) as exc:
        raise EbriskDependencyAcquisitionError("trusted EBRISK target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain,text/x-ini;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESRM20-EBRISK-dependency-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            return _read_bounded(
                response,
                deadline=deadline,
                maximum=spec.byte_count,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise EbriskDependencyAcquisitionError(
            "EBRISK dependency retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EbriskDependencyAcquisitionError(
            f"EBRISK dependency retrieval failed: {type(exc).__name__}"
        ) from exc


def _acquire_and_extract(
    key: str, *, opener: Any | None, monotonic: Any
) -> dict[str, Any]:
    raw = _acquire_exact_payload(key, opener=opener, monotonic=monotonic)
    try:
        result = bridge.extract_verified_ebrisk_dependencies(key, raw)
    except bridge.VerifiedEbriskConfigError as exc:
        raise EbriskDependencyAcquisitionError(
            "EBRISK dependency verification failed closed"
        ) from exc
    ceilings = (
        "raw_config_returned",
        "historical_group_assignment_verified",
        "dependency_inventory_authorized",
        "runtime_compatibility_verified",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    )
    if any(result.get(field) is not False for field in ceilings):
        raise EbriskDependencyAcquisitionError(
            "verified EBRISK dependency result widened its authority ceiling"
        )
    return result


def acquire_group1_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    return _acquire_and_extract("group1", opener=opener, monotonic=monotonic)


def acquire_group2_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    return _acquire_and_extract("group2", opener=opener, monotonic=monotonic)


def acquire_iceland_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    return _acquire_and_extract("iceland", opener=opener, monotonic=monotonic)
