# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted in-memory bridge from the frozen ESRM20 mapping to its value-free profile.

The exact mapping object was already receipted by Issue #340. This worker adds
no provider-selection surface: it re-materializes only that immutable object,
uses the existing hardened EFEHR transport, then passes the bytes directly to
the reviewed value-free profiler merged by PR #407. Provider bytes are never
returned or persisted by this worker.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
    from scripts import profile_efehr_esrm20_mapping_structure as mapping_profile
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
    import profile_efehr_esrm20_mapping_structure as mapping_profile
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )

# Bridge-owned production authority. Dependency modules are cross-checked below;
# they do not define this worker's source identity at import time.
_CANONICAL_SCHEMA_VERSION = "oc-esrm20-mapping-structure-acquisition-v1"
_CANONICAL_OPERATION_ID = "esrm20-exposure-vulnerability-mapping-structure-profile-v1"
_CANONICAL_SOURCE_ISSUE = 283
_CANONICAL_PROFILE_ISSUE = 404
_CANONICAL_CONTROL_ISSUE = 411
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = (
    "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
)
_CANONICAL_RECEIPT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_RUN_ID = 31899242278
_CANONICAL_RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
_CANONICAL_PROFILER_SOURCE_COMMIT = "e172e5ad57d25fe43cb36810a6baa76e102a0187"
_CANONICAL_PROFILER_PATH = "scripts/profile_efehr_esrm20_mapping_structure.py"
_CANONICAL_PROFILER_FUNCTION = "profile_verified_mapping_bytes"
_CANONICAL_PROFILER_SCHEMA_VERSION = "oc-esrm20-mapping-structure-profile-v0"
# Git blob identity of the exact profiler source merged by #407 at e172e5ad....
# This makes the explanatory source-commit claim enforceable against the loaded
# source bytes instead of relying only on a Python function object's identity.
_CANONICAL_PROFILER_GIT_BLOB_SHA1 = "5d5aa5c9c48880022235e727c9ec4d5e73df46de"
_CANONICAL_PROFILER = mapping_profile.profile_verified_mapping_bytes

# Review/back-compat aliases only. Production authority is private and alias
# drift fails before provider work.
SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
PROFILE_ISSUE = _CANONICAL_PROFILE_ISSUE
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256
RECEIPT_COMMENT_ID = _CANONICAL_RECEIPT_COMMENT_ID
RECEIPT_RUN_ID = _CANONICAL_RECEIPT_RUN_ID
RECEIPT_EXECUTION_SHA = _CANONICAL_RECEIPT_EXECUTION_SHA
PROFILER_SOURCE_COMMIT = _CANONICAL_PROFILER_SOURCE_COMMIT
PROFILER_PATH = _CANONICAL_PROFILER_PATH
PROFILER_FUNCTION = _CANONICAL_PROFILER_FUNCTION
PROFILER_GIT_BLOB_SHA1 = _CANONICAL_PROFILER_GIT_BLOB_SHA1


class Esrm20MappingProfileAcquisitionError(RuntimeError):
    """Raised when the trusted mapping cannot yield a value-free profile."""


def _git_blob_sha1(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Esrm20MappingProfileAcquisitionError(
            "frozen ESRM20 mapping profiler source is unavailable"
        ) from exc
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def _require_canonical_aliases() -> None:
    exact_aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (PROFILE_ISSUE, _CANONICAL_PROFILE_ISSUE, "profile issue"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "expected byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "expected SHA-256"),
        (RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment id"),
        (RECEIPT_RUN_ID, _CANONICAL_RECEIPT_RUN_ID, "receipt run id"),
        (
            RECEIPT_EXECUTION_SHA,
            _CANONICAL_RECEIPT_EXECUTION_SHA,
            "receipt execution SHA",
        ),
        (
            PROFILER_SOURCE_COMMIT,
            _CANONICAL_PROFILER_SOURCE_COMMIT,
            "profiler source commit",
        ),
        (PROFILER_PATH, _CANONICAL_PROFILER_PATH, "profiler path"),
        (PROFILER_FUNCTION, _CANONICAL_PROFILER_FUNCTION, "profiler function"),
        (
            PROFILER_GIT_BLOB_SHA1,
            _CANONICAL_PROFILER_GIT_BLOB_SHA1,
            "profiler Git blob SHA-1",
        ),
    )
    for observed, expected, label in exact_aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingProfileAcquisitionError(
                f"frozen ESRM20 mapping profile {label} drifted"
            )

    dependency_exact = (
        (mapping_receipt.SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "receipt source issue"),
        (mapping_receipt.DATASET_ID, _CANONICAL_DATASET_ID, "receipt dataset id"),
        (mapping_receipt.PROJECT_ID, _CANONICAL_PROJECT_ID, "receipt project id"),
        (mapping_receipt.COMMIT_SHA, _CANONICAL_COMMIT_SHA, "receipt commit"),
        (
            mapping_receipt.REPOSITORY_PATH,
            _CANONICAL_REPOSITORY_PATH,
            "receipt repository path",
        ),
        (
            mapping_profile._CANONICAL_SOURCE_ISSUE,
            _CANONICAL_SOURCE_ISSUE,
            "profiler source issue",
        ),
        (
            mapping_profile._CANONICAL_PROFILE_ISSUE,
            _CANONICAL_PROFILE_ISSUE,
            "profiler profile issue",
        ),
        (
            mapping_profile._CANONICAL_DATASET_ID,
            _CANONICAL_DATASET_ID,
            "profiler dataset id",
        ),
        (
            mapping_profile._CANONICAL_PROJECT_ID,
            _CANONICAL_PROJECT_ID,
            "profiler project id",
        ),
        (
            mapping_profile._CANONICAL_PROJECT_PATH,
            _CANONICAL_PROJECT_PATH,
            "profiler project path",
        ),
        (
            mapping_profile._CANONICAL_COMMIT_SHA,
            _CANONICAL_COMMIT_SHA,
            "profiler commit",
        ),
        (
            mapping_profile._CANONICAL_REPOSITORY_PATH,
            _CANONICAL_REPOSITORY_PATH,
            "profiler repository path",
        ),
        (
            mapping_profile._CANONICAL_EXPECTED_BYTE_COUNT,
            _CANONICAL_EXPECTED_BYTE_COUNT,
            "profiler byte count",
        ),
        (
            mapping_profile._CANONICAL_EXPECTED_SHA256,
            _CANONICAL_EXPECTED_SHA256,
            "profiler SHA-256",
        ),
        (
            mapping_profile._CANONICAL_SCHEMA_VERSION,
            _CANONICAL_PROFILER_SCHEMA_VERSION,
            "profiler schema version",
        ),
    )
    for observed, expected, label in dependency_exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingProfileAcquisitionError(
                f"frozen ESRM20 mapping dependency {label} drifted"
            )

    if mapping_profile.profile_verified_mapping_bytes is not _CANONICAL_PROFILER:
        raise Esrm20MappingProfileAcquisitionError(
            "frozen ESRM20 mapping profiler function identity drifted"
        )
    source_path = Path(mapping_profile.__file__)
    if _git_blob_sha1(source_path) != _CANONICAL_PROFILER_GIT_BLOB_SHA1:
        raise Esrm20MappingProfileAcquisitionError(
            "frozen ESRM20 mapping profiler source blob drifted"
        )


def _profile_ceiling_is_closed(profile: object) -> dict[str, Any]:
    if type(profile) is not dict:
        raise Esrm20MappingProfileAcquisitionError(
            "mapping profiler returned an invalid result"
        )

    required_exact = (
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("profile_issue", _CANONICAL_PROFILE_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("repository_path", _CANONICAL_REPOSITORY_PATH),
        ("receipt_comment_id", _CANONICAL_RECEIPT_COMMENT_ID),
        ("receipt_run_id", _CANONICAL_RECEIPT_RUN_ID),
        ("receipt_execution_sha", _CANONICAL_RECEIPT_EXECUTION_SHA),
        ("byte_count", _CANONICAL_EXPECTED_BYTE_COUNT),
        ("sha256", _CANONICAL_EXPECTED_SHA256),
    )
    for field, expected in required_exact:
        observed = profile.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingProfileAcquisitionError(
                f"mapping profiler provenance drifted at {field}"
            )

    required_false = (
        "external_bytes_persisted",
        "derived_bytes_persisted",
        "publication_authorized",
        "mapping_interpretation_authorized",
        "vulnerability_selection_authorized",
        "model_use_authorized",
    )
    for field in required_false:
        if profile.get(field) is not False:
            raise Esrm20MappingProfileAcquisitionError(
                f"mapping profiler widened authority at {field}"
            )

    nested = profile.get("profile")
    if type(nested) is not dict:
        raise Esrm20MappingProfileAcquisitionError(
            "mapping profiler omitted its bounded profile"
        )
    nested_schema = nested.get("schema_version")
    if (
        type(nested_schema) is not type(_CANONICAL_PROFILER_SCHEMA_VERSION)
        or nested_schema != _CANONICAL_PROFILER_SCHEMA_VERSION
    ):
        raise Esrm20MappingProfileAcquisitionError(
            "mapping profiler nested schema version drifted"
        )
    nested_false = (
        "header_strings_returned",
        "cell_values_returned",
        "raw_rows_returned",
        "normalization_applied",
        "mapping_interpretation_authorized",
        "vulnerability_selection_authorized",
        "external_bytes_persisted",
        "derived_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    )
    for field in nested_false:
        if nested.get(field) is not False:
            raise Esrm20MappingProfileAcquisitionError(
                f"mapping profiler widened nested authority at {field}"
            )
    return profile


def _acquire_esrm20_mapping_structure_profile(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    """Private injectable helper used only for deterministic offline tests."""

    _require_canonical_aliases()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=_CANONICAL_SOURCE_ISSUE,
            dataset_id=_CANONICAL_DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=_CANONICAL_REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Esrm20MappingProfileAcquisitionError(
            "trusted mapping target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-ESRM20-mapping-profile-v1",
        },
        method="GET",
    )

    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            declared = _declared_length(response, _CANONICAL_EXPECTED_BYTE_COUNT)
            if declared is not None and declared != _CANONICAL_EXPECTED_BYTE_COUNT:
                raise EfehrAcquisitionError(
                    "mapping Content-Length does not match trusted receipt"
                )
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
            retrieved_at = now()
    except EfehrAcquisitionError as exc:
        raise Esrm20MappingProfileAcquisitionError(
            "mapping profile retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Esrm20MappingProfileAcquisitionError(
            f"mapping profile retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        profile = _profile_ceiling_is_closed(_CANONICAL_PROFILER(raw))
    except mapping_profile.MappingStructureProfileError as exc:
        raise Esrm20MappingProfileAcquisitionError(
            "trusted mapping structure profiling failed closed"
        ) from exc
    finally:
        raw = b""

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "operation_id": _CANONICAL_OPERATION_ID,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "profile_issue": _CANONICAL_PROFILE_ISSUE,
        "control_issue": _CANONICAL_CONTROL_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": _CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_run_id": _CANONICAL_RECEIPT_RUN_ID,
        "receipt_execution_sha": _CANONICAL_RECEIPT_EXECUTION_SHA,
        "profiler_source_commit": _CANONICAL_PROFILER_SOURCE_COMMIT,
        "profiler_path": _CANONICAL_PROFILER_PATH,
        "profiler_function": _CANONICAL_PROFILER_FUNCTION,
        "profiler_git_blob_sha1": _CANONICAL_PROFILER_GIT_BLOB_SHA1,
        "retrieved_at": retrieved_at,
        "profile": profile,
        "raw_bytes_returned": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }


def acquire_esrm20_mapping_structure_profile() -> dict[str, Any]:
    """Fetch the frozen mapping using code-owned transport/time authority only."""

    return _acquire_esrm20_mapping_structure_profile(
        opener=_open_fixed,
        now=utc_now,
        monotonic=time.monotonic,
    )
