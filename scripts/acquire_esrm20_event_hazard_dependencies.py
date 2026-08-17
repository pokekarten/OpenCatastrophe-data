# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire and profile only the two frozen ESRM20 event-hazard root configs.

The canonical trusted-main receipts already bind the exact Group1/Group2 byte
identities. This worker re-materializes one fixed immutable root transiently,
then delegates byte verification and bounded interpretation to the reviewed
bridge. Provider bytes are never returned by any public worker.
"""

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
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    from scripts import verify_esrm20_event_hazard_dependencies as bridge
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    import verify_esrm20_event_hazard_dependencies as bridge


class EventHazardDependencyAcquisitionError(RuntimeError):
    """Raised when one fixed receipted root cannot be safely profiled."""


def _acquire_exact_root_payload(
    group: int,
    *,
    opener: Any | None,
    monotonic: Any,
) -> bytes:
    """Retrieve one internally selected frozen root and return memory-only bytes.

    This is an internal transport primitive. Public workers below immediately
    pass the bytes into a verifier/profiler and never return provider bytes.
    """

    try:
        spec = bridge._root_spec(group)
    except bridge.VerifiedEventHazardConfigError as exc:
        raise EventHazardDependencyAcquisitionError(
            "trusted ESRM20 event-hazard group is invalid"
        ) from exc

    try:
        target = validate_target(
            source_issue=bridge.SOURCE_ISSUE,
            dataset_id=bridge.DATASET_ID,
            project_id=bridge.PROJECT_ID,
            commit_sha=bridge.COMMIT_SHA,
            repository_path=spec.repository_path,
        )
    except EfehrReceiptError as exc:
        raise EventHazardDependencyAcquisitionError(
            "trusted ESRM20 event-hazard target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain,text/x-ini;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESRM20-dependency-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=spec.byte_count,
                monotonic=monotonic,
            )
    except EventHazardDependencyAcquisitionError:
        raise
    except EfehrAcquisitionError as exc:
        raise EventHazardDependencyAcquisitionError(
            "ESRM20 event-hazard dependency retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EventHazardDependencyAcquisitionError(
            f"ESRM20 event-hazard dependency retrieval failed: {type(exc).__name__}"
        ) from exc

    return raw


def _acquire_and_extract(
    group: int,
    *,
    opener: Any | None,
    monotonic: Any,
) -> dict[str, Any]:
    """Retrieve one internally selected root and return verified dependencies."""

    raw = _acquire_exact_root_payload(group, opener=opener, monotonic=monotonic)
    try:
        result = bridge.extract_verified_event_hazard_dependencies(group, raw)
    except bridge.VerifiedEventHazardConfigError as exc:
        raise EventHazardDependencyAcquisitionError(
            "ESRM20 event-hazard dependency verification failed closed"
        ) from exc

    if (
        result.get("dependency_inventory_authorized") is not False
        or result.get("external_bytes_persisted") is not False
        or result.get("publication_authorized") is not False
    ):
        raise EventHazardDependencyAcquisitionError(
            "verified ESRM20 dependency result widened its authority ceiling"
        )
    return result


def _acquire_and_profile_imts(
    group: int,
    *,
    opener: Any | None,
    monotonic: Any,
) -> dict[str, Any]:
    """Retrieve one fixed root and return only its verified IMT names."""

    raw = _acquire_exact_root_payload(group, opener=opener, monotonic=monotonic)
    try:
        result = bridge.extract_verified_event_hazard_imt_profile(group, raw)
    except bridge.VerifiedEventHazardConfigError as exc:
        raise EventHazardDependencyAcquisitionError(
            "ESRM20 event-hazard IMT verification failed closed"
        ) from exc
    if (
        result.get("levels_returned") is not False
        or result.get("raw_config_returned") is not False
        or result.get("component_semantics_verified") is not False
        or result.get("unit_semantics_verified") is not False
        or result.get("hazard_vulnerability_imt_compatibility_verified") is not False
        or result.get("external_bytes_persisted") is not False
        or result.get("publication_authorized") is not False
        or result.get("model_use_authorized") is not False
    ):
        raise EventHazardDependencyAcquisitionError(
            "verified ESRM20 IMT result widened its authority ceiling"
        )
    return result


def acquire_event_hazard_group1_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and profile only the frozen Group1 root."""

    return _acquire_and_extract(1, opener=opener, monotonic=monotonic)


def acquire_event_hazard_group2_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and profile only the frozen Group2 root."""

    return _acquire_and_extract(2, opener=opener, monotonic=monotonic)


def acquire_event_hazard_group1_imt_profile(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize Group1 and return only its verified canonical IMT names."""

    return _acquire_and_profile_imts(1, opener=opener, monotonic=monotonic)


def acquire_event_hazard_group2_imt_profile(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize Group2 and return only its verified canonical IMT names."""

    return _acquire_and_profile_imts(2, opener=opener, monotonic=monotonic)
