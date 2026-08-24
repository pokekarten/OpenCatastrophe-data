# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main profile for the exact ESRM20 Athens scenario-risk job config.

The operation is closed to one immutable EFEHR GitLab object. Provider bytes are
verified against immutable Git object identity before UTF-8 / INI interpretation,
profiled in memory, and never persisted or returned.

The output establishes only the exact OpenQuake config-key -> vulnerability-path
bindings needed by EQ1. It does not validate the vulnerability XML contents,
benchmark agreement, independent validation, publication rights, or model use.
"""

from __future__ import annotations

import argparse
import configparser
import hashlib
import http.client
import io
import json
import os
import posixpath
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
)
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
EVENT_ID = "Greece_07-9-1999"
REPOSITORY_PATH = "ruptures/OQ-engine_jobs/job_run_rupture_Greece_07-9-1999.ini"
GIT_BLOB_SHA1 = "dcef31c93ff73e055e32881cbb9d5c3f4967a191"
EXPECTED_BYTE_COUNT = 1_185
JOB_DIRECTORY = "ruptures/OQ-engine_jobs"
STRUCTURAL_TARGET = (
    "ruptures/vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml"
)
OCCUPANTS_TARGET = (
    "ruptures/vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM_day.xml"
)

REQUEST_MARKER = "<!-- oc-eq1-esrm20-athens-job-config-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-athens-job-config-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-athens-job-config-profile-request-v1"
PROFILE_SCHEMA_VERSION = "oc-esrm20-athens-job-config-binding-profile-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-athens-job-config-profile-result-v1"
ACTION = "esrm20_athens_job_config_vulnerability_binding_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_RESULT_UTF8_BYTES = 24_000
MAX_COMMENT_PAGES = 20

_CANONICAL_PROVIDER_HOST = "gitlab.seismo.ethz.ch"
_CANONICAL_PROVIDER_ROOT = "https://gitlab.seismo.ethz.ch"
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_ALLOWED_STRUCTURAL_KEYS = {"structural_vulnerability_file"}
_OCCUPANTS_KEY = "occupants_vulnerability_file"
_ALLOWED_VULNERABILITY_KEYS = _ALLOWED_STRUCTURAL_KEYS | {_OCCUPANTS_KEY}
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class AthensJobConfigError(RuntimeError):
    """Base fail-closed error for the exact Athens job-config profile."""


class AthensJobConfigAcquisitionError(AthensJobConfigError):
    """The exact provider object could not be acquired or identity-verified."""


class AthensJobConfigContentError(AthensJobConfigError):
    """The exact bytes failed the closed UTF-8 / INI binding profile."""


class AthensJobConfigContractError(AthensJobConfigError):
    """Frozen authority, request, ledger, or result contract drifted."""


def _require_contract() -> None:
    exact = (
        (PROVIDER_HOST, _CANONICAL_PROVIDER_HOST, "provider host"),
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (SOURCE_ISSUE, 285, "source issue"),
        (PARENT_CONSUMER_ISSUE, 287, "parent consumer issue"),
        (DATASET_ID, "efehr.esrm20.scenario-tests.v1.0", "dataset id"),
        (PROJECT_ID, 273, "project id"),
        (PROJECT_PATH, "efehr/esrm20_scenario_tests", "project path"),
        (RELEASE_TAG, "v1.0", "release tag"),
        (COMMIT_SHA, "041f90d950d6ff84180b2faa11319a42c66c74cc", "commit sha"),
        (EVENT_ID, "Greece_07-9-1999", "event id"),
        (
            REPOSITORY_PATH,
            "ruptures/OQ-engine_jobs/job_run_rupture_Greece_07-9-1999.ini",
            "repository path",
        ),
        (GIT_BLOB_SHA1, "dcef31c93ff73e055e32881cbb9d5c3f4967a191", "Git blob"),
        (EXPECTED_BYTE_COUNT, 1_185, "byte count"),
        (
            STRUCTURAL_TARGET,
            "ruptures/vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
            "structural target",
        ),
        (
            OCCUPANTS_TARGET,
            "ruptures/vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM_day.xml",
            "occupants target",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise AthensJobConfigContractError(
                f"Athens job-config {label} authority drifted"
            )


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise AthensJobConfigContractError(
            "Athens job-config transport identity drifted"
        )
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise AthensJobConfigContractError(
            "Athens job-config monotonic clock identity drifted"
        )


def raw_file_url() -> str:
    _require_contract()
    encoded_path = urllib.parse.quote(REPOSITORY_PATH, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def git_blob_sha1(data: bytes) -> str:
    if type(data) is not bytes:
        raise AthensJobConfigAcquisitionError("Athens job-config bytes are invalid")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git identity only


def verify_exact_identity(data: bytes) -> str:
    """Verify immutable length + Git blob identity before any content parsing."""
    _require_contract()
    if type(data) is not bytes:
        raise AthensJobConfigAcquisitionError("Athens job-config bytes are invalid")
    if len(data) != EXPECTED_BYTE_COUNT:
        raise AthensJobConfigAcquisitionError("Athens job-config byte count drifted")
    observed_blob = git_blob_sha1(data)
    if observed_blob != GIT_BLOB_SHA1:
        raise AthensJobConfigAcquisitionError("Athens job-config Git blob drifted")
    return hashlib.sha256(data).hexdigest()


def _normalize_target(value: str) -> str:
    if type(value) is not str:
        raise AthensJobConfigContentError("Athens job-config path is invalid")
    candidate = value.strip()
    if not candidate:
        raise AthensJobConfigContentError("Athens job-config path is invalid")
    if "\x00" in candidate or "\\" in candidate:
        raise AthensJobConfigContentError("Athens job-config path is unsafe")
    if candidate.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
        raise AthensJobConfigContentError("Athens job-config path is unsafe")
    normalized = posixpath.normpath(posixpath.join(JOB_DIRECTORY, candidate))
    if normalized.startswith("../") or normalized == ".." or normalized.startswith("/"):
        raise AthensJobConfigContentError("Athens job-config path escapes repository")
    return normalized


def _parse_ini(data: bytes) -> configparser.ConfigParser:
    if type(data) is not bytes:
        raise AthensJobConfigContentError("Athens job-config payload is invalid")
    if b"\x00" in data or data.startswith(b"\xef\xbb\xbf"):
        raise AthensJobConfigContentError("Athens job-config encoding is invalid")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AthensJobConfigContentError(
            "Athens job-config payload is not strict UTF-8"
        ) from exc
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
        allow_no_value=False,
    )
    parser.optionxform = str
    try:
        parser.read_file(io.StringIO(text))
    except (configparser.Error, ValueError) as exc:
        raise AthensJobConfigContentError("Athens job-config INI is malformed") from exc
    if not parser.sections():
        raise AthensJobConfigContentError("Athens job-config INI has no sections")
    return parser


def profile_bindings(data: bytes) -> dict[str, Any]:
    """Return only the closed vulnerability key/path binding surface."""
    parser = _parse_ini(data)
    observed: list[tuple[str, str]] = []
    for section in parser.sections():
        for key, value in parser.items(section, raw=True):
            if "vulnerability" not in key.lower():
                continue
            if key != key.lower() or key not in _ALLOWED_VULNERABILITY_KEYS:
                raise AthensJobConfigContentError(
                    "Athens job-config contains an unsupported vulnerability key"
                )
            observed.append((key, value))
    if len(observed) != 2:
        raise AthensJobConfigContentError(
            "Athens job-config vulnerability binding cardinality drifted"
        )
    keys = [key for key, _ in observed]
    if len(set(keys)) != len(keys):
        raise AthensJobConfigContentError(
            "Athens job-config repeats a vulnerability binding key"
        )
    structural_keys = [key for key in keys if key in _ALLOWED_STRUCTURAL_KEYS]
    if len(structural_keys) != 1 or keys.count(_OCCUPANTS_KEY) != 1:
        raise AthensJobConfigContentError(
            "Athens job-config vulnerability roles are incomplete or ambiguous"
        )

    by_key = {key: value for key, value in observed}
    structural_key = structural_keys[0]
    structural_path = _normalize_target(by_key[structural_key])
    occupants_path = _normalize_target(by_key[_OCCUPANTS_KEY])
    if structural_path != STRUCTURAL_TARGET:
        raise AthensJobConfigContentError(
            "Athens job-config structural vulnerability target drifted"
        )
    if occupants_path != OCCUPANTS_TARGET:
        raise AthensJobConfigContentError(
            "Athens job-config occupants vulnerability target drifted"
        )

    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "binding_count": 2,
        "bindings": [
            {
                "config_key": structural_key,
                "role": "structural",
                "repository_path": STRUCTURAL_TARGET,
            },
            {
                "config_key": _OCCUPANTS_KEY,
                "role": "occupants",
                "repository_path": OCCUPANTS_TARGET,
            },
        ],
        "raw_config_returned": False,
        "vulnerability_binding_verified": True,
        "vulnerability_model_content_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile(profile: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "binding_count",
        "bindings",
        "raw_config_returned",
        "vulnerability_binding_verified",
        "vulnerability_model_content_verified",
        "benchmark_agreement_inspected",
        "independent_validation_established",
        "holdout_status_established",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(profile) is not dict or set(profile) != fields:
        raise AthensJobConfigContractError("Athens job-config profile fields drifted")
    exact = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "binding_count": 2,
        "raw_config_returned": False,
        "vulnerability_binding_verified": True,
        "vulnerability_model_content_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(profile.get(field)) is not type(expected) or profile.get(field) != expected:
            raise AthensJobConfigContractError(
                f"Athens job-config profile drifted at {field}"
            )
    bindings = profile.get("bindings")
    if type(bindings) is not list or len(bindings) != 2:
        raise AthensJobConfigContractError("Athens job-config binding list drifted")
    allowed = {
        ("structural_vulnerability_file", "structural", STRUCTURAL_TARGET),
    }
    first = bindings[0]
    second = bindings[1]
    for item in bindings:
        if type(item) is not dict or set(item) != {
            "config_key",
            "role",
            "repository_path",
        }:
            raise AthensJobConfigContractError(
                "Athens job-config binding fields drifted"
            )
    structural = (
        first.get("config_key"),
        first.get("role"),
        first.get("repository_path"),
    )
    if structural not in allowed:
        raise AthensJobConfigContractError(
            "Athens job-config structural binding drifted"
        )
    if second != {
        "config_key": _OCCUPANTS_KEY,
        "role": "occupants",
        "repository_path": OCCUPANTS_TARGET,
    }:
        raise AthensJobConfigContractError(
            "Athens job-config occupants binding drifted"
        )
    return profile


def _acquire_and_profile_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    _require_contract()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    url = raw_file_url()
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,application/octet-stream;q=0.9",
            "User-Agent": "OpenCatastrophe-Athens-Job-Config-Profile-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            data = _read_bounded(
                response,
                deadline=deadline,
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except (
        EfehrAcquisitionError,
        http.client.HTTPException,
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ) as exc:
        raise AthensJobConfigAcquisitionError(
            "fixed Athens job-config acquisition failed"
        ) from exc

    sha256 = verify_exact_identity(data)
    try:
        profile = _validate_profile(profile_bindings(data))
    except AthensJobConfigContentError:
        raise
    return {
        "schema_version": "oc-esrm20-athens-job-config-profile-evidence-v1",
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "event_id": EVENT_ID,
        "repository_path": REPOSITORY_PATH,
        "git_blob_sha1": GIT_BLOB_SHA1,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": sha256,
        "profile": profile,
        "provider_file_bytes_read": True,
        "provider_file_content_profiled": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_and_profile() -> dict[str, Any]:
    _require_contract()
    _require_production_identity()
    return _acquire_and_profile_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )


_ACQUIRE = acquire_and_profile


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AthensJobConfigContractError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise AthensJobConfigContractError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    _require_contract()
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise AthensJobConfigContractError("wrong Athens job-config issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise AthensJobConfigContractError("invalid Athens job-config execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise AthensJobConfigContractError("invalid Athens job-config request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensJobConfigContractError(
            "Athens job-config request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except AthensJobConfigContractError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensJobConfigContractError(
            "invalid Athens job-config request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise AthensJobConfigContractError(
            "Athens job-config request fields drifted"
        )
    exact = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": DATASET_ID,
    }
    for field, expected in exact.items():
        if type(request.get(field)) is not type(expected) or request.get(field) != expected:
            raise AthensJobConfigContractError(
                f"Athens job-config request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise AthensJobConfigContractError("invalid requester identity")
    return request


def _identity() -> dict[str, Any]:
    return {
        "provider_host": PROVIDER_HOST,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "event_id": EVENT_ID,
        "repository_path": REPOSITORY_PATH,
        "git_blob_sha1": GIT_BLOB_SHA1,
        "byte_count": EXPECTED_BYTE_COUNT,
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "job_config_identity": _identity(),
        "external_bytes_persisted": False,
        "vulnerability_model_content_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_evidence(evidence: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "source_issue",
        "parent_consumer_issue",
        "dataset_id",
        "provider_host",
        "project_id",
        "project_path",
        "release_tag",
        "commit_sha",
        "event_id",
        "repository_path",
        "git_blob_sha1",
        "byte_count",
        "sha256",
        "profile",
        "provider_file_bytes_read",
        "provider_file_content_profiled",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(evidence) is not dict or set(evidence) != fields:
        raise AthensJobConfigContractError(
            "Athens job-config evidence fields drifted"
        )
    exact = {
        "schema_version": "oc-esrm20-athens-job-config-profile-evidence-v1",
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        **_identity(),
        "provider_file_bytes_read": True,
        "provider_file_content_profiled": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(evidence.get(field)) is not type(expected) or evidence.get(field) != expected:
            raise AthensJobConfigContractError(
                f"Athens job-config evidence drifted at {field}"
            )
    sha256 = evidence.get("sha256")
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise AthensJobConfigContractError("Athens job-config SHA-256 is invalid")
    _validate_profile(evidence.get("profile"))
    return evidence


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    fields = set(base) | {
        "status",
        "failure_class",
        "evidence",
        "provider_file_bytes_read",
        "provider_file_content_profiled",
    }
    if type(result) is not dict or set(result) != fields:
        raise AthensJobConfigContractError(
            "trusted Athens job-config result fields drifted"
        )
    for field, expected in base.items():
        if type(result.get(field)) is not type(expected) or result.get(field) != expected:
            raise AthensJobConfigContractError(
                f"trusted Athens job-config result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("provider_file_bytes_read") is not True
            or result.get("provider_file_content_profiled") is not True
        ):
            raise AthensJobConfigContractError(
                "Athens job-config PASS state drifted"
            )
        _validate_evidence(result.get("evidence"))
        return result
    if status == "blocked":
        failure = result.get("failure_class")
        if failure not in {"acquisition_failure", "profile_failure"}:
            raise AthensJobConfigContractError(
                "Athens job-config BLOCKED class drifted"
            )
        if result.get("evidence") is not None:
            raise AthensJobConfigContractError(
                "Athens job-config BLOCKED state leaked evidence"
            )
        if failure == "acquisition_failure":
            if (
                result.get("provider_file_bytes_read") is not None
                or result.get("provider_file_content_profiled") is not False
            ):
                raise AthensJobConfigContractError(
                    "Athens job-config acquisition failure overclaims state"
                )
        else:
            if (
                result.get("provider_file_bytes_read") is not True
                or result.get("provider_file_content_profiled") is not False
            ):
                raise AthensJobConfigContractError(
                    "Athens job-config profile failure state drifted"
                )
        return result
    raise AthensJobConfigContractError(
        "trusted Athens job-config result is not terminal"
    )


def _parse_terminal(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise AthensJobConfigContractError(
            "trusted Athens job-config result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensJobConfigContractError(
            "trusted Athens job-config result envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except AthensJobConfigContractError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensJobConfigContractError(
            "trusted Athens job-config result JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise AthensJobConfigContractError(
            "trusted Athens job-config result is not an object"
        )
    result_sha = result.get("execution_sha")
    if type(result_sha) is not str or _SHA1_RE.fullmatch(result_sha) is None:
        raise AthensJobConfigContractError(
            "trusted Athens job-config result SHA is invalid"
        )
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": MAX_COMMENT_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise AthensJobConfigContractError(
            "Athens job-config result ledger is incomplete"
        ) from exc
    matched = False
    for comment in comments:
        if type(comment) is not dict:
            raise AthensJobConfigContractError(
                "Athens job-config ledger contains non-object comment"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login == TRUSTED_RESULT_LOGIN:
            matched = (
                _parse_terminal(comment.get("body"), execution_sha=execution_sha)
                or matched
            )
    return matched


def _run(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        evidence = acquirer()
    except AthensJobConfigAcquisitionError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "evidence": None,
                "provider_file_bytes_read": None,
                "provider_file_content_profiled": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except AthensJobConfigContentError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "evidence": None,
                "provider_file_bytes_read": True,
                "provider_file_content_profiled": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)

    evidence = _validate_evidence(evidence)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "evidence": evidence,
            "provider_file_bytes_read": True,
            "provider_file_content_profiled": True,
        }
    )
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run(*, execution_sha: str) -> dict[str, Any]:
    return _run(execution_sha=execution_sha, acquirer=_ACQUIRE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")

    result = run(execution_sha=args.execution_sha)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_RESULT_UTF8_BYTES:
        raise AthensJobConfigContractError("Athens job-config result is too large")
    Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
