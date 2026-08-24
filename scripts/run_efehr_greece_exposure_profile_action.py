# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact ESRM20 Greece exposure wrapper profile."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_efehr_greece_exposure_profile as worker
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_efehr_greece_exposure_profile as worker
    from prepare_agent_action_result import LedgerError, fetch_repository_comments


REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-result-v1"
ACTION = "esrm20_greece_exposure_wrapper_profile"
CONTROL_ISSUE = 285
CONTENT_ISSUE = 662
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class GreeceExposureProfileActionError(RuntimeError):
    """Fail-closed trusted Greece exposure-profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise GreeceExposureProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise GreeceExposureProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise GreeceExposureProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise GreeceExposureProfileActionError("invalid Greece exposure-profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError(
            "invalid Greece exposure-profile request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile request fields drifted"
        )
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureProfileActionError(
                f"Greece exposure-profile request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise GreeceExposureProfileActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "content_issue": CONTENT_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile_payload(payload: object) -> dict[str, Any]:
    try:
        return worker._validate_profile_result(payload)
    except worker.GreeceExposureContractError as exc:
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile payload violates reviewed worker contract"
        ) from exc


def _validate_terminal_result(
    result: object, *, execution_sha: str
) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "profile"}
    if type(result) is not dict or set(result) != expected_fields:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result fields drifted"
        )
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureProfileActionError(
                f"trusted Greece exposure-profile result drifted at {field}"
            )

    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise GreeceExposureProfileActionError(
                "Greece exposure-profile PASS cannot carry failure_class"
            )
        _validate_profile_payload(result.get("profile"))
        return result
    if status == "blocked":
        if (
            result.get("failure_class")
            not in {"acquisition_failure", "profile_failure"}
            or result.get("profile") is not None
        ):
            raise GreeceExposureProfileActionError(
                "blocked Greece exposure-profile result is not safely bounded"
            )
        return result
    raise GreeceExposureProfileActionError(
        "trusted Greece exposure-profile result has non-terminal status"
    )


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    if body.count(RESULT_MARKER) != 1:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result fields drifted"
        )
    result_execution_sha = result.get("execution_sha")
    if (
        type(result_execution_sha) is not str
        or not _SHA_RE.fullmatch(result_execution_sha)
    ):
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result execution SHA is invalid"
        )
    _validate_terminal_result(result, execution_sha=result_execution_sha)
    return result_execution_sha == execution_sha


def has_terminal_greece_exposure_profile_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded Issue #285 ledger is known."""

    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile result ledger is incomplete"
        ) from exc
    for comment in comments:
        if type(comment) is not dict:
            raise GreeceExposureProfileActionError(
                "Greece exposure-profile ledger contains a non-object comment"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(
            comment.get("body"),
            execution_sha=execution_sha,
        ):
            return True
    return False


def _run_greece_exposure_profile(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquirer()
    except worker.GreeceExposureAcquisitionError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "profile": None,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except worker.GreeceExposureContentError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "profile": None,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)

    payload = _validate_profile_payload(payload)
    result.update({"status": "pass", "failure_class": None, "profile": payload})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_greece_exposure_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_greece_exposure_profile(
        execution_sha=execution_sha,
        acquirer=worker.acquire_and_profile_greece_exposure,
    )


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
    result = run_greece_exposure_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
