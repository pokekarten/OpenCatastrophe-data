# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main diagnostic for fixed ESRM20 ebrisk template cardinality.

This action reuses the already-bounded ESRM20 v1.0 metadata profiler. It exposes
only one closed state for each of the three provider-predeclared template
basenames; no provider file bytes, tree paths, object IDs, or unrelated tree
inventory are published.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-template-cardinality-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-ebrisk-template-cardinality-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-ebrisk-template-cardinality-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-ebrisk-template-cardinality-result-v1"
SOURCE_ISSUE = 281
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 16_000

STATES = frozenset({"missing", "single_blob", "single_non_blob", "multiple"})
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_RESULT_FIELDS = {
    "schema_version",
    "source_issue",
    "target_sha",
    "execution_sha",
    "status",
    "template_resolution",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "historical_group_assignment_authorized",
    "publication_authorized",
    "model_use_authorized",
}
_ITEM_FIELDS = {"basename", "state"}

_PROFILE = profile.profile_v10_tree
_TEMPLATE_RESOLVER = profile._exact_template_paths
_FETCH_COMMENTS = fetch_repository_comments


class EbriskTemplateDiagnosticError(RuntimeError):
    """Fail-closed error for the bounded template-cardinality diagnostic."""


class _DiagnosticComplete(RuntimeError):
    def __init__(self, summary: list[dict[str, str]]) -> None:
        super().__init__("bounded ebrisk template diagnostic complete")
        self.summary = summary


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EbriskTemplateDiagnosticError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise EbriskTemplateDiagnosticError(f"non-finite JSON constant: {value}")


def _load_json(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskTemplateDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskTemplateDiagnosticError("invalid diagnostic JSON") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise EbriskTemplateDiagnosticError("wrong diagnostic issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskTemplateDiagnosticError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EbriskTemplateDiagnosticError("invalid diagnostic request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskTemplateDiagnosticError("diagnostic request envelope is not canonical")
    request = _load_json(after.strip())
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EbriskTemplateDiagnosticError("diagnostic request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise EbriskTemplateDiagnosticError("diagnostic request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise EbriskTemplateDiagnosticError("diagnostic request issue drifted")
    if request["target_sha"] != execution_sha:
        raise EbriskTemplateDiagnosticError("diagnostic request target is not trusted main")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise EbriskTemplateDiagnosticError("invalid diagnostic requester")
    return request


def summarize_template_resolution(entries: object) -> list[dict[str, str]]:
    if type(entries) is not list:
        raise EbriskTemplateDiagnosticError("diagnostic entries are not a list")
    summary: list[dict[str, str]] = []
    for basename in profile.TEMPLATE_BASENAMES:
        matches = [
            entry
            for entry in entries
            if type(entry) is dict and entry.get("name") == basename
        ]
        if not matches:
            state = "missing"
        elif len(matches) > 1:
            state = "multiple"
        else:
            state = "single_blob" if matches[0].get("type") == "blob" else "single_non_blob"
        summary.append({"basename": basename, "state": state})
    return summary


def _diagnostic_template_resolver(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    raise _DiagnosticComplete(summarize_template_resolution(entries))


def run_template_diagnostic() -> list[dict[str, str]]:
    if profile.profile_v10_tree is not _PROFILE:
        raise EbriskTemplateDiagnosticError("trusted ebrisk profiler authority drifted")
    if profile._exact_template_paths is not _TEMPLATE_RESOLVER:
        raise EbriskTemplateDiagnosticError("trusted template resolver authority drifted")

    profile._exact_template_paths = _diagnostic_template_resolver
    try:
        try:
            _PROFILE()
        except _DiagnosticComplete as completed:
            return validate_template_resolution(completed.summary)
        except profile.EbriskTreeProfileError as exc:
            raise EbriskTemplateDiagnosticError(
                "ebrisk metadata did not reach template resolution"
            ) from exc
        raise EbriskTemplateDiagnosticError("diagnostic resolver was bypassed")
    finally:
        profile._exact_template_paths = _TEMPLATE_RESOLVER


def validate_template_resolution(value: object) -> list[dict[str, str]]:
    if type(value) is not list or len(value) != len(profile.TEMPLATE_BASENAMES):
        raise EbriskTemplateDiagnosticError("template diagnostic set is incomplete")
    expected = list(profile.TEMPLATE_BASENAMES)
    observed: list[str] = []
    for item in value:
        if type(item) is not dict or set(item) != _ITEM_FIELDS:
            raise EbriskTemplateDiagnosticError("template diagnostic shape drifted")
        basename = item["basename"]
        state = item["state"]
        if type(basename) is not str or basename not in profile.TEMPLATE_BASENAMES:
            raise EbriskTemplateDiagnosticError("template diagnostic basename drifted")
        if type(state) is not str or state not in STATES:
            raise EbriskTemplateDiagnosticError("template diagnostic state drifted")
        observed.append(basename)
    if observed != expected:
        raise EbriskTemplateDiagnosticError("template diagnostics are not in canonical order")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise EbriskTemplateDiagnosticError("diagnostic result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskTemplateDiagnosticError("diagnostic result envelope is malformed")
    result = _load_json(after.strip())
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskTemplateDiagnosticError("diagnostic result fields drifted")
    own_sha = result.get("execution_sha")
    target_sha = result.get("target_sha")
    if type(own_sha) is not str or _SHA_RE.fullmatch(own_sha) is None:
        raise EbriskTemplateDiagnosticError("diagnostic execution SHA is invalid")
    if type(target_sha) is not str or target_sha != own_sha:
        raise EbriskTemplateDiagnosticError("diagnostic target/execution SHA mismatch")
    for field, expected in _base_result(execution_sha=own_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskTemplateDiagnosticError(f"diagnostic result drifted at {field}")
    if result["status"] == "pass":
        validate_template_resolution(result["template_resolution"])
    elif result["status"] == "duplicate":
        if result["template_resolution"] is not None:
            raise EbriskTemplateDiagnosticError("duplicate diagnostic carries evidence")
    else:
        raise EbriskTemplateDiagnosticError("diagnostic result has invalid status")
    return own_sha == execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskTemplateDiagnosticError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise EbriskTemplateDiagnosticError("diagnostic result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise EbriskTemplateDiagnosticError("diagnostic ledger contains non-object")
        user = comment.get("user")
        if type(user) is not dict or user.get("login") != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        if parse_terminal_result(body, execution_sha=execution_sha):
            return True
    return False


def execute_diagnostic(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if fetch_repository_comments is not _FETCH_COMMENTS:
        raise EbriskTemplateDiagnosticError("trusted diagnostic ledger authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "template_resolution": None,
        }
    else:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "template_resolution": run_template_diagnostic(),
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise EbriskTemplateDiagnosticError("diagnostic result exceeds publication limit")
    parse_terminal_result(RESULT_MARKER + "\n" + encoded.decode("utf-8"), execution_sha=execution_sha)
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

    validate_request(
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
        raise EbriskTemplateDiagnosticError("GitHub ledger token is absent")
    result = execute_diagnostic(
        repository=args.repository,
        token=token,
        execution_sha=args.execution_sha,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
