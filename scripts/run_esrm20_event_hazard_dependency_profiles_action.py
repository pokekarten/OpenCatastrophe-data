# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Dedicated trusted-main dispatcher for the two frozen ESRM20 hazard roots."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_esrm20_event_hazard_dependencies as worker
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
from scripts.esrm20_event_hazard_dependency_profile_contract import (
    ACTION_GROUP1, ACTION_GROUP2, ACTION_TO_GROUP, CONTROL_ISSUE, DATASET_ID,
    EventHazardDependencyActionError, MAX_LEDGER_PAGES, MAX_RESULT_UTF8_BYTES,
    REQUEST_MARKER, REQUEST_SCHEMA_VERSION, RESULT_MARKER, RESULT_SCHEMA_VERSION,
    TRUSTED_RESULT_LOGIN, _UTC_NOW, _base_result, _peek_terminal_identity,
    validate_profile, validate_request, validate_terminal_result,
)

_FETCH_COMMENTS = fetch_repository_comments
_ACQUIRE_GROUP1 = worker.acquire_event_hazard_group1_dependencies
_ACQUIRE_GROUP2 = worker.acquire_event_hazard_group2_dependencies

def has_terminal_result(*, repository: str, token: str, action: str, execution_sha: str) -> bool:
    if fetch_repository_comments is not _FETCH_COMMENTS:
        raise EventHazardDependencyActionError("trusted ledger authority drifted")
    try:
        comments = _FETCH_COMMENTS(repository, token, issue=CONTROL_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise EventHazardDependencyActionError("result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise EventHazardDependencyActionError("result ledger contains non-object")
        user = comment.get("user")
        if type(user) is not dict or user.get("login") != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        identity = _peek_terminal_identity(body)
        if identity is None or identity != (action, execution_sha):
            continue
        if validate_terminal_result(body, action=action, execution_sha=execution_sha):
            return True
    return False


def execute_profile(
    *,
    repository: str,
    token: str,
    action: str,
    execution_sha: str,
    group1_acquirer: Callable[[], dict[str, Any]] | None = None,
    group2_acquirer: Callable[[], dict[str, Any]] | None = None,
    now: Callable[[], str] = _UTC_NOW,
) -> dict[str, Any]:
    if action not in ACTION_TO_GROUP:
        raise EventHazardDependencyActionError("execution action is outside closed operations")
    if (
        worker.acquire_event_hazard_group1_dependencies is not _ACQUIRE_GROUP1
        or worker.acquire_event_hazard_group2_dependencies is not _ACQUIRE_GROUP2
    ):
        raise EventHazardDependencyActionError("trusted dependency-profile authority drifted")
    if has_terminal_result(repository=repository, token=token, action=action, execution_sha=execution_sha):
        return {
            **_base_result(action=action, execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }

    group1 = group1_acquirer or _ACQUIRE_GROUP1
    group2 = group2_acquirer or _ACQUIRE_GROUP2
    selected = group1 if action == ACTION_GROUP1 else group2
    try:
        profile = dict(selected())
    except worker.EventHazardDependencyAcquisitionError:
        return {
            **_base_result(action=action, execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "acquisition_failure",
            "profile": None,
        }
    profile["profiled_at"] = now()
    validate_profile(profile, action=action)
    result = {
        **_base_result(action=action, execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "profile": profile,
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise EventHazardDependencyActionError("dependency result exceeds publication limit")
    validate_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"),
        action=action,
        execution_sha=execution_sha,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--token-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    request = validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise EventHazardDependencyActionError("GitHub ledger token is absent")
    result = execute_profile(
        repository=args.repository,
        token=token,
        action=request["action"],
        execution_sha=args.execution_sha,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
