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


_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_READ_BOUNDED = _read_bounded
_CANONICAL_REMAINING = _remaining
_CANONICAL_VALIDATE_EXACT_RESPONSE = _validate_exact_response
_CANONICAL_VALIDATE_TARGET = validate_target
_CANONICAL_RAW_FILE_API_URL = raw_file_api_url
_CANONICAL_REQUEST = urllib.request.Request
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS
_CANONICAL_CONFIG_SPEC = bridge.config_spec
_CANONICAL_EXTRACT_VERIFIED = bridge.extract_verified_ebrisk_dependencies
_CANONICAL_CONFIG_SPECS = bridge.CONFIG_SPECS
_CANONICAL_BRIDGE_FIXED_AUTHORITY = (
    bridge.SCHEMA_VERSION,
    bridge.SOURCE_ISSUE,
    bridge.DATASET_ID,
    bridge.PROJECT_ID,
    bridge.PROJECT_PATH,
    bridge.COMMIT_SHA,
    bridge.RECEIPT_COMMENT_ID,
    bridge.PARSER_ID,
    tuple(
        (spec.key, spec.operation_id, spec.repository_path, spec.byte_count, spec.sha256)
        for spec in bridge.CONFIG_SPECS
    ),
)


def _acquire_exact_payload(
    key: str, *, opener: Any, monotonic: Any
) -> bytes:
    """Private injectable byte acquisition helper for deterministic offline tests."""

    try:
        spec = _CANONICAL_CONFIG_SPEC(key)
        target = _CANONICAL_VALIDATE_TARGET(
            source_issue=_CANONICAL_BRIDGE_FIXED_AUTHORITY[1],
            dataset_id=_CANONICAL_BRIDGE_FIXED_AUTHORITY[2],
            project_id=_CANONICAL_BRIDGE_FIXED_AUTHORITY[3],
            commit_sha=_CANONICAL_BRIDGE_FIXED_AUTHORITY[5],
            repository_path=spec.repository_path,
        )
    except (bridge.VerifiedEbriskConfigError, EfehrReceiptError) as exc:
        raise EbriskDependencyAcquisitionError("trusted EBRISK target is invalid") from exc

    if target.project_path != _CANONICAL_BRIDGE_FIXED_AUTHORITY[4]:
        raise EbriskDependencyAcquisitionError("trusted EBRISK project path drifted")

    file_url = _CANONICAL_RAW_FILE_API_URL(target)
    request = _CANONICAL_REQUEST(
        file_url,
        headers={
            "Accept": "text/plain,text/x-ini;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESRM20-EBRISK-dependency-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    try:
        with opener(request, timeout=_CANONICAL_REMAINING(deadline, monotonic)) as response:
            _CANONICAL_VALIDATE_EXACT_RESPONSE(response, file_url)
            return _CANONICAL_READ_BOUNDED(
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
    key: str, *, opener: Any, monotonic: Any
) -> dict[str, Any]:
    """Private injectable acquisition/verification helper for tests."""

    raw = _CANONICAL_ACQUIRE_EXACT_PAYLOAD(key, opener=opener, monotonic=monotonic)
    try:
        result = _CANONICAL_EXTRACT_VERIFIED(key, raw)
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


_CANONICAL_ACQUIRE_EXACT_PAYLOAD = _acquire_exact_payload
_CANONICAL_ACQUIRE_AND_EXTRACT = _acquire_and_extract


def _require_production_identity() -> None:
    """Fail before provider I/O if any mutable production authority was rebound."""

    identity_checks = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
        (_read_bounded, _CANONICAL_READ_BOUNDED, "bounded reader"),
        (_remaining, _CANONICAL_REMAINING, "deadline helper"),
        (_validate_exact_response, _CANONICAL_VALIDATE_EXACT_RESPONSE, "response validator"),
        (validate_target, _CANONICAL_VALIDATE_TARGET, "target validator"),
        (raw_file_api_url, _CANONICAL_RAW_FILE_API_URL, "URL builder"),
        (urllib.request.Request, _CANONICAL_REQUEST, "request constructor"),
        (bridge.config_spec, _CANONICAL_CONFIG_SPEC, "config selector"),
        (bridge.extract_verified_ebrisk_dependencies, _CANONICAL_EXTRACT_VERIFIED, "verified parser"),
        (_acquire_exact_payload, _CANONICAL_ACQUIRE_EXACT_PAYLOAD, "private byte helper"),
        (_acquire_and_extract, _CANONICAL_ACQUIRE_AND_EXTRACT, "private verifier helper"),
    )
    for observed, expected, label in identity_checks:
        if observed is not expected:
            raise EbriskDependencyAcquisitionError(
                f"frozen EBRISK dependency {label} drifted"
            )

    if bridge.CONFIG_SPECS is not _CANONICAL_CONFIG_SPECS:
        raise EbriskDependencyAcquisitionError("frozen EBRISK dependency config specs drifted")
    observed_bridge = (
        bridge.SCHEMA_VERSION,
        bridge.SOURCE_ISSUE,
        bridge.DATASET_ID,
        bridge.PROJECT_ID,
        bridge.PROJECT_PATH,
        bridge.COMMIT_SHA,
        bridge.RECEIPT_COMMENT_ID,
        bridge.PARSER_ID,
        tuple(
            (spec.key, spec.operation_id, spec.repository_path, spec.byte_count, spec.sha256)
            for spec in bridge.CONFIG_SPECS
        ),
    )
    if observed_bridge != _CANONICAL_BRIDGE_FIXED_AUTHORITY:
        raise EbriskDependencyAcquisitionError("frozen EBRISK dependency bridge authority drifted")
    if TOTAL_DEADLINE_SECONDS != _CANONICAL_TOTAL_DEADLINE_SECONDS:
        raise EbriskDependencyAcquisitionError("frozen EBRISK dependency deadline drifted")


def acquire_group1_dependencies() -> dict[str, Any]:
    """Profile the fixed receipted Group1 config under code-owned production authority."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_AND_EXTRACT(
        "group1", opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC
    )


def acquire_group2_dependencies() -> dict[str, Any]:
    """Profile the fixed receipted Group2 config under code-owned production authority."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_AND_EXTRACT(
        "group2", opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC
    )


def acquire_iceland_dependencies() -> dict[str, Any]:
    """Profile the fixed receipted Iceland config under code-owned production authority."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_AND_EXTRACT(
        "iceland", opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC
    )
