# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Prepare one durable action result with repository-wide deduplication.

Only closed, repository-owned acquisition actions execute provider network work,
and only after request validation plus a complete duplicate-result ledger scan.
Each worker owns its exact provider target and all transport/archive bounds;
requests cannot supply network targets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

try:
    from scripts.acquire_dwd_extreme_wind_receipt import AcquisitionError, acquire
    from scripts.acquire_dwd_metadata_receipt import acquire as acquire_dwd_metadata
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError, acquire_canary
    from scripts.agent_action_protocol import (
        ProtocolError,
        RESULT_SCHEMA_VERSION,
        TRUSTED_RESULT_LOGINS,
        extract_result_comment,
        semantic_request_id,
    )
    from scripts.validate_agent_action_request import (
        ACQUISITION_RECEIPT_ACTION,
        DWD_METADATA_RECEIPT_ACTION,
        EFEHR_README_RECEIPT_ACTION,
        RequestError,
        extract_request,
        validate_request,
    )
    from scripts.validate_agent_action_result import (
        ACQUISITION_FAILURE_CLASS,
        ResultError,
        validate_result,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_dwd_extreme_wind_receipt import AcquisitionError, acquire
    from acquire_dwd_metadata_receipt import acquire as acquire_dwd_metadata
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError, acquire_canary
    from agent_action_protocol import (
        ProtocolError,
        RESULT_SCHEMA_VERSION,
        TRUSTED_RESULT_LOGINS,
        extract_result_comment,
        semantic_request_id,
    )
    from validate_agent_action_request import (
        ACQUISITION_RECEIPT_ACTION,
        DWD_METADATA_RECEIPT_ACTION,
        EFEHR_README_RECEIPT_ACTION,
        RequestError,
        extract_request,
        validate_request,
    )
    from validate_agent_action_result import (
        ACQUISITION_FAILURE_CLASS,
        ResultError,
        validate_result,
    )

API_ROOT = "https://api.github.com"
PER_PAGE = 100
MAX_LEDGER_PAGES = 20
NETWORK_ACTIONS = frozenset(
    {ACQUISITION_RECEIPT_ACTION, DWD_METADATA_RECEIPT_ACTION, EFEHR_README_RECEIPT_ACTION}
)


class LedgerError(RuntimeError):
    """Raised when the durable GitHub result ledger cannot be read completely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_existing_result(comments: list[dict[str, Any]], semantic_id: str) -> int | None:
    """Return a matching completed result emitted by the trusted Actions reporter.

    Owner-authored comments are deliberately not trusted as execution receipts:
    authorization to request work is separate from provenance that the workflow ran.
    """

    for comment in comments:
        if type(comment) is not dict:
            raise LedgerError("repository comment ledger contains a non-object item")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login not in TRUSTED_RESULT_LOGINS:
            continue
        body = comment.get("body")
        if type(body) is not str:
            continue
        try:
            result = extract_result_comment(body)
        except ProtocolError as exc:
            raise LedgerError(f"trusted result comment is malformed: {exc}") from exc
        if result is None:
            continue
        try:
            validate_result(result)
        except ResultError as exc:
            raise LedgerError(f"trusted result comment fails result validation: {exc}") from exc
        if result["semantic_request_id"] != semantic_id:
            continue
        completed = result["status"] in {"pass", "duplicate"} or (
            result["action"] in NETWORK_ACTIONS
            and result["phase"] == "acquisition_receipt"
            and result["status"] == "blocked"
            and result["failure_class"] == ACQUISITION_FAILURE_CLASS
        )
        if not completed:
            continue
        comment_id = comment.get("id")
        if type(comment_id) is not int or comment_id < 1:
            raise LedgerError("trusted matching result comment lacks a positive integer id")
        return comment_id
    return None


def fetch_repository_comments(
    repository: str,
    token: str,
    *,
    opener: Any = urllib.request.urlopen,
    max_pages: int = MAX_LEDGER_PAGES,
) -> list[dict[str, Any]]:
    if type(repository) is not str or repository.count("/") != 1:
        raise LedgerError("repository must be owner/name")
    if type(token) is not str or not token:
        raise LedgerError("GitHub token is absent")
    if type(max_pages) is not int or max_pages < 1:
        raise LedgerError("max_pages must be a positive integer")

    comments: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        query = urllib.parse.urlencode(
            {"sort": "created", "direction": "desc", "per_page": PER_PAGE, "page": page}
        )
        request = urllib.request.Request(
            f"{API_ROOT}/repos/{repository}/issues/comments?{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "OpenCatastrophe-agent-action-ledger-v1",
            },
        )
        try:
            with opener(request, timeout=20) as response:
                raw = response.read()
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise LedgerError(f"cannot read GitHub result ledger: {type(exc).__name__}") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LedgerError("GitHub result ledger response is not valid UTF-8 JSON") from exc
        if type(payload) is not list or not all(type(item) is dict for item in payload):
            raise LedgerError("GitHub result ledger response must be an array of comment objects")
        comments.extend(payload)
        if len(payload) < PER_PAGE:
            return comments
    raise LedgerError(
        f"GitHub result ledger exceeds the fail-closed scan bound of {max_pages * PER_PAGE} comments"
    )


def build_result(
    request: dict[str, Any],
    *,
    repository: str,
    execution_sha: str,
    source_comment_id: int,
    run_id: int,
    run_attempt: int,
    started_at: str,
    finished_at: str,
    duplicate_result_comment_id: int | None = None,
    ledger_incomplete: bool = False,
) -> dict[str, Any]:
    """Build request-validation evidence, including dedup/ledger failure states."""
    semantic_id = semantic_request_id(request, execution_sha, repository)
    if ledger_incomplete:
        status, failure_class, duplicate_result_comment_id = "blocked", "ledger_incomplete", None
        ledger_scan_complete, prior_result_reused = False, False
    elif duplicate_result_comment_id is not None:
        status, failure_class = "duplicate", "duplicate_request"
        ledger_scan_complete, prior_result_reused = True, True
    else:
        status, failure_class = "pass", None
        ledger_scan_complete, prior_result_reused = True, False
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "semantic_request_id": semantic_id,
        "repository": repository,
        "action": request["action"],
        "source_issue": request["issue"],
        "source_comment_id": source_comment_id,
        "target_sha": request["target_sha"],
        "dataset_id": request["dataset_id"],
        "execution_sha": execution_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "started_at": started_at,
        "finished_at": finished_at,
        "phase": "request_validation",
        "status": status,
        "external_bytes_persisted": False,
        "evidence": {
            "request_validated": True,
            "ledger_scan_complete": ledger_scan_complete,
            "prior_result_reused": prior_result_reused,
        },
        "duplicate_result_comment_id": duplicate_result_comment_id,
        "failure_class": failure_class,
    }
    return validate_result(result)


def _receipt_field(action: str) -> str:
    if action == ACQUISITION_RECEIPT_ACTION:
        return "acquisition_receipt"
    if action == DWD_METADATA_RECEIPT_ACTION:
        return "dwd_metadata_receipt"
    if action == EFEHR_README_RECEIPT_ACTION:
        return "efehr_readme_receipt"
    raise LedgerError("unsupported closed acquisition action")


def build_acquisition_result(
    request: dict[str, Any],
    *,
    repository: str,
    execution_sha: str,
    source_comment_id: int,
    run_id: int,
    run_attempt: int,
    started_at: str,
    finished_at: str,
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    """Bind one successful or blocked closed acquisition attempt."""
    status = "pass" if receipt is not None else "blocked"
    receipt_field = _receipt_field(request["action"])
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "semantic_request_id": semantic_request_id(request, execution_sha, repository),
        "repository": repository,
        "action": request["action"],
        "source_issue": request["issue"],
        "source_comment_id": source_comment_id,
        "target_sha": request["target_sha"],
        "dataset_id": request["dataset_id"],
        "execution_sha": execution_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "started_at": started_at,
        "finished_at": finished_at,
        "phase": "acquisition_receipt",
        "status": status,
        "external_bytes_persisted": False,
        "evidence": {
            "request_validated": True,
            "ledger_scan_complete": True,
            "prior_result_reused": False,
            receipt_field: receipt,
        },
        "duplicate_result_comment_id": None,
        "failure_class": None if receipt is not None else ACQUISITION_FAILURE_CLASS,
    }
    return validate_result(result)


def prepare_completed_result(
    request: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    repository: str,
    execution_sha: str,
    source_comment_id: int,
    run_id: int,
    run_attempt: int,
    started_at: str,
    acquirer: Callable[[], dict[str, Any]] = acquire,
    metadata_acquirer: Callable[[], dict[str, Any]] = acquire_dwd_metadata,
    efehr_acquirer: Callable[[], dict[str, Any]] = acquire_canary,
) -> dict[str, Any]:
    """Deduplicate first, then execute only one closed allowlisted acquisition action."""
    semantic_id = semantic_request_id(request, execution_sha, repository)
    duplicate_id = find_existing_result(comments, semantic_id)
    if duplicate_id is not None:
        return build_result(
            request,
            repository=repository,
            execution_sha=execution_sha,
            source_comment_id=source_comment_id,
            run_id=run_id,
            run_attempt=run_attempt,
            started_at=started_at,
            finished_at=utc_now(),
            duplicate_result_comment_id=duplicate_id,
        )

    if request["action"] == ACQUISITION_RECEIPT_ACTION:
        selected_acquirer = acquirer
    elif request["action"] == DWD_METADATA_RECEIPT_ACTION:
        selected_acquirer = metadata_acquirer
    elif request["action"] == EFEHR_README_RECEIPT_ACTION:
        selected_acquirer = efehr_acquirer
    else:
        return build_result(
            request,
            repository=repository,
            execution_sha=execution_sha,
            source_comment_id=source_comment_id,
            run_id=run_id,
            run_attempt=run_attempt,
            started_at=started_at,
            finished_at=utc_now(),
        )

    try:
        receipt = selected_acquirer()
    except (AcquisitionError, EfehrAcquisitionError) as exc:
        # The durable result carries only a closed failure class. The trusted
        # workflow log receives the bounded worker diagnostic for operators.
        print(f"acquisition blocked: {exc}", file=sys.stderr)
        receipt = None
    return build_acquisition_result(
        request,
        repository=repository,
        execution_sha=execution_sha,
        source_comment_id=source_comment_id,
        run_id=run_id,
        run_attempt=run_attempt,
        started_at=started_at,
        finished_at=utc_now(),
        receipt=receipt,
    )


def positive_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LedgerError(f"{field} must be a positive integer") from exc
    if parsed < 1:
        raise LedgerError(f"{field} must be a positive integer")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True)
    parser.add_argument("--source-comment-id", required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--github-token-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started_at = utc_now()
    body = os.environ.get(args.comment_body_env)
    token = os.environ.get(args.github_token_env)
    if body is None or token is None:
        print("BLOCKED: required environment input is absent", file=sys.stderr)
        return 2
    try:
        issue = positive_int(args.expected_issue, "expected_issue")
        source_comment_id = positive_int(args.source_comment_id, "source_comment_id")
        run_id = positive_int(args.run_id, "run_id")
        run_attempt = positive_int(args.run_attempt, "run_attempt")
        request = validate_request(extract_request(body), expected_issue=issue)
        try:
            comments = fetch_repository_comments(args.repository, token)
            result = prepare_completed_result(
                request,
                comments,
                repository=args.repository,
                execution_sha=args.execution_sha,
                source_comment_id=source_comment_id,
                run_id=run_id,
                run_attempt=run_attempt,
                started_at=started_at,
            )
        except LedgerError:
            result = build_result(
                request,
                repository=args.repository,
                execution_sha=args.execution_sha,
                source_comment_id=source_comment_id,
                run_id=run_id,
                run_attempt=run_attempt,
                started_at=started_at,
                finished_at=utc_now(),
                ledger_incomplete=True,
            )
    except (RequestError, ResultError, ProtocolError, LedgerError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
