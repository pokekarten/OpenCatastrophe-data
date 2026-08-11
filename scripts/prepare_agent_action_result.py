# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Prepare one durable request-validation result with repository-wide deduplication."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from scripts.agent_action_protocol import ProtocolError, RESULT_SCHEMA_VERSION, TRUSTED_RESULT_LOGINS, extract_result_comment, semantic_request_id
    from scripts.validate_agent_action_request import RequestError, extract_request, validate_request
    from scripts.validate_agent_action_result import ResultError, validate_result
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from agent_action_protocol import ProtocolError, RESULT_SCHEMA_VERSION, TRUSTED_RESULT_LOGINS, extract_result_comment, semantic_request_id
    from validate_agent_action_request import RequestError, extract_request, validate_request
    from validate_agent_action_result import ResultError, validate_result

API_ROOT = "https://api.github.com"
PER_PAGE = 100
MAX_LEDGER_PAGES = 20


class LedgerError(RuntimeError):
    """Raised when the durable GitHub result ledger cannot be read completely."""


def find_existing_result(
    comments: list[dict[str, Any]], semantic_id: str, *, owner_login: str
) -> int | None:
    """Return a trusted completed result comment id for the same semantic request."""

    trusted_logins = set(TRUSTED_RESULT_LOGINS)
    trusted_logins.add(owner_login)
    for comment in comments:
        if type(comment) is not dict:
            raise LedgerError("repository comment ledger contains a non-object item")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login not in trusted_logins:
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
        if result["status"] not in {"pass", "duplicate"}:
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
    """Fetch the bounded repository-wide issue-comment ledger newest first."""

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
        url = f"{API_ROOT}/repos/{repository}/issues/comments?{query}"
        request = urllib.request.Request(
            url,
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
    execution_sha: str,
    source_comment_id: int,
    run_id: int,
    run_attempt: int,
    duplicate_result_comment_id: int | None = None,
    ledger_incomplete: bool = False,
) -> dict[str, Any]:
    semantic_id = semantic_request_id(request, execution_sha)
    if ledger_incomplete:
        status = "blocked"
        failure_class = "ledger_incomplete"
        duplicate_result_comment_id = None
    elif duplicate_result_comment_id is not None:
        status = "duplicate"
        failure_class = "duplicate_request"
    else:
        status = "pass"
        failure_class = None
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "semantic_request_id": semantic_id,
        "action": request["action"],
        "source_issue": request["issue"],
        "source_comment_id": source_comment_id,
        "target_sha": request["target_sha"],
        "dataset_id": request["dataset_id"],
        "execution_sha": execution_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "phase": "request_validation",
        "status": status,
        "external_bytes_persisted": False,
        "duplicate_result_comment_id": duplicate_result_comment_id,
        "failure_class": failure_class,
    }
    return validate_result(result)


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
    parser.add_argument("--owner-login", required=True)
    parser.add_argument("--github-token-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
        semantic_id = semantic_request_id(request, args.execution_sha)
        try:
            comments = fetch_repository_comments(args.repository, token)
            duplicate_id = find_existing_result(comments, semantic_id, owner_login=args.owner_login)
            result = build_result(
                request,
                execution_sha=args.execution_sha,
                source_comment_id=source_comment_id,
                run_id=run_id,
                run_attempt=run_attempt,
                duplicate_result_comment_id=duplicate_id,
            )
        except LedgerError:
            result = build_result(
                request,
                execution_sha=args.execution_sha,
                source_comment_id=source_comment_id,
                run_id=run_id,
                run_attempt=run_attempt,
                ledger_incomplete=True,
            )
    except (RequestError, ResultError, ProtocolError, LedgerError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
