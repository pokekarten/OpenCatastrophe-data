# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Post one already prepared and validated Agent Action Dispatch result comment."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

try:
    from scripts.agent_action_protocol import canonical_result_comment
    from scripts.validate_agent_action_result import ResultError, _strict_json, validate_result
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from agent_action_protocol import canonical_result_comment
    from validate_agent_action_result import ResultError, _strict_json, validate_result

API_ROOT = "https://api.github.com"


class PostError(RuntimeError):
    """Raised when a validated result cannot be posted safely."""


def post_result(result: dict, *, repository: str, expected_issue: int, token: str, opener=urllib.request.urlopen) -> int:
    result = validate_result(result)
    if result["source_issue"] != expected_issue:
        raise PostError("result source_issue does not match triggering issue")
    if result["repository"] != repository:
        raise PostError("result repository does not match workflow repository")
    if type(repository) is not str or repository.count("/") != 1:
        raise PostError("repository must be owner/name")
    if type(token) is not str or not token:
        raise PostError("GitHub token is absent")

    url = f"{API_ROOT}/repos/{repository}/issues/{expected_issue}/comments"
    payload = json.dumps({"body": canonical_result_comment(result)}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OpenCatastrophe-agent-action-result-v1",
        },
    )
    try:
        with opener(request, timeout=20) as response:
            raw = response.read()
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise PostError(f"cannot post result comment: {type(exc).__name__}") from exc
    try:
        posted = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PostError("result-comment response is not valid UTF-8 JSON") from exc
    comment_id = posted.get("id") if type(posted) is dict else None
    if type(comment_id) is not int or comment_id < 1:
        raise PostError("result-comment response lacks a positive comment id")
    return comment_id


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise PostError("expected issue must be a positive integer") from exc
    if parsed < 1:
        raise PostError("expected issue must be a positive integer")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--expected-issue", required=True)
    parser.add_argument("--github-token-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result_text = os.environ.get(args.result_env)
    token = os.environ.get(args.github_token_env)
    if result_text is None or token is None:
        print("BLOCKED: required result/token environment input is absent", file=sys.stderr)
        return 2
    try:
        result = validate_result(_strict_json(result_text))
        comment_id = post_result(
            result,
            repository=args.repository,
            expected_issue=positive_int(args.expected_issue),
            token=token,
        )
    except (ResultError, PostError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"posted_result_comment_id={comment_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
