# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read bounded commit metadata for one frozen ESRM20 runtime exposure path.

The operation is deliberately closed to EFEHR GitLab project 269, ESRM20 v1.0
commit ``05f83bbc...``, and ``Exposure/OQ_Exposure_Input_Kosovo_Res.csv``. It
uses the GitLab commits API with an exact path filter and returns commit metadata
only. Repository file payloads and commit diffs are never requested.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
    utc_now,
)
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-runtime-exposure-history-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-runtime-exposure-history-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-runtime-exposure-history-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-runtime-exposure-history-result-v1"
HISTORY_SCHEMA_VERSION = "oc-efehr-esrm20-kosovo-runtime-exposure-history-v1"
ACTION = "esrm20_kosovo_runtime_exposure_history"
CONTROL_ISSUE = 282
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
REF_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"
COMMITS_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/commits"
PER_PAGE = 100
MAX_PAGES = 10
MAX_COMMITS = 200
MAX_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 4_194_304
MAX_TITLE_CHARS = 300
MAX_TERMINAL_UTF8_BYTES = 60_000
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
_GENERATOR_PATH_HINT_RE = re.compile(
    r"(?:^|/)(?:scripts?|tools?|utils?|src)(?:/|$)|"
    r"(?:generat|format|convert|transform|exposure|openquake|oq_)",
    re.I,
)
_GENERATOR_EXTENSIONS = (".py", ".r", ".sh", ".ipynb", ".md", ".txt", ".yml", ".yaml")

_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "history",
    "external_file_bytes_accessed",
    "external_bytes_persisted",
    "transform_lineage_verified",
    "publication_authorized",
    "model_use_authorized",
}
_HISTORY_FIELDS = {
    "schema_version",
    "project_id",
    "project_path",
    "ref_sha",
    "repository_path",
    "retrieved_at_utc",
    "commit_count",
    "commits",
    "history_complete_within_ref",
    "diffs_requested",
    "file_payloads_requested",
}
_COMMIT_FIELDS = {
    "id",
    "parent_ids",
    "committed_date",
    "title",
    "title_generator_hint",
}


class KosovoRuntimeExposureHistoryError(RuntimeError):
    """Fail-closed metadata-history error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoRuntimeExposureHistoryError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise KosovoRuntimeExposureHistoryError(f"non-finite JSON constant: {token}")


def _load_json_array(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoRuntimeExposureHistoryError("commit metadata is not UTF-8") from exc
    try:
        payload = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureHistoryError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureHistoryError("commit metadata is invalid JSON") from exc
    if type(payload) is not list:
        raise KosovoRuntimeExposureHistoryError("commit metadata must be an array")
    return payload


def _canonical_url(page: int) -> str:
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_PAGES):
        raise KosovoRuntimeExposureHistoryError("history page outside bounded policy")
    query = urllib.parse.urlencode(
        {
            "ref_name": REF_SHA,
            "path": REPOSITORY_PATH,
            "follow": "false",
            "per_page": PER_PAGE,
            "page": page,
        }
    )
    return f"{COMMITS_API_URL}?{query}"


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise KosovoRuntimeExposureHistoryError("production transport authority drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise KosovoRuntimeExposureHistoryError("production clock authority drifted")
    exact = (
        (CONTROL_ISSUE, 282),
        (DATASET_ID, "efehr.esrm20.risk-inputs.v1.0"),
        (PROJECT_ID, 269),
        (PROJECT_PATH, "efehr/esrm20"),
        (REF_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783"),
        (REPOSITORY_PATH, "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoRuntimeExposureHistoryError("frozen runtime-exposure authority drifted")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise KosovoRuntimeExposureHistoryError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoRuntimeExposureHistoryError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoRuntimeExposureHistoryError("invalid history request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureHistoryError("history request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureHistoryError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureHistoryError("invalid history request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoRuntimeExposureHistoryError("history request fields drifted")
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
            raise KosovoRuntimeExposureHistoryError(f"history request {field} drifted")
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise KosovoRuntimeExposureHistoryError("invalid requester identity")
    return request


def _canonical_commit(item: Any) -> dict[str, Any]:
    if type(item) is not dict:
        raise KosovoRuntimeExposureHistoryError("commit entry is not an object")
    commit_id = item.get("id")
    parents = item.get("parent_ids")
    committed_date = item.get("committed_date")
    title = item.get("title")
    if type(commit_id) is not str or _SHA_RE.fullmatch(commit_id) is None:
        raise KosovoRuntimeExposureHistoryError("commit id is invalid")
    if (
        type(parents) is not list
        or len(parents) > 8
        or any(type(parent_id) is not str or _SHA_RE.fullmatch(parent_id) is None for parent_id in parents)
    ):
        raise KosovoRuntimeExposureHistoryError("commit parent ids are invalid")
    if type(committed_date) is not str or len(committed_date) > 80 or _ISO_DATE_RE.match(committed_date) is None:
        raise KosovoRuntimeExposureHistoryError("commit date is invalid")
    if (
        type(title) is not str
        or not title
        or title != title.strip()
        or len(title) > MAX_TITLE_CHARS
        or "\x00" in title
        or "\n" in title
        or "\r" in title
    ):
        raise KosovoRuntimeExposureHistoryError("commit title is invalid")
    generator_hint = bool(_GENERATOR_PATH_HINT_RE.search(title)) or title.casefold().endswith(
        tuple(extension.casefold() for extension in _GENERATOR_EXTENSIONS)
    )
    return {
        "id": commit_id,
        "parent_ids": parents,
        "committed_date": committed_date,
        "title": title,
        "title_generator_hint": generator_hint,
    }


def acquire_history_metadata_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    now: Callable[[], str],
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    commits: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    total_bytes = 0
    completed = False

    for page in range(1, MAX_PAGES + 1):
        url = _canonical_url(page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-EFEHR-Kosovo-runtime-exposure-history-v1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                raw = _read_bounded(
                    response,
                    deadline=deadline,
                    maximum=MAX_PAGE_BYTES,
                    monotonic=monotonic,
                )
        except EfehrAcquisitionError as exc:
            raise KosovoRuntimeExposureHistoryError("provider commit-history acquisition failed") from exc
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise KosovoRuntimeExposureHistoryError(
                f"provider commit-history acquisition failed: {type(exc).__name__}"
            ) from exc
        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_METADATA_BYTES:
            raise KosovoRuntimeExposureHistoryError("commit-history metadata exceeded total byte bound")
        page_items = _load_json_array(raw)
        if len(page_items) > PER_PAGE:
            raise KosovoRuntimeExposureHistoryError("commit-history page exceeded result bound")
        for item in page_items:
            commit = _canonical_commit(item)
            if commit["id"] in seen_ids:
                raise KosovoRuntimeExposureHistoryError("duplicate commit id in history")
            seen_ids.add(commit["id"])
            commits.append(commit)
            if len(commits) > MAX_COMMITS:
                raise KosovoRuntimeExposureHistoryError("commit-history result count exceeded bound")
        if len(page_items) < PER_PAGE:
            completed = True
            break

    if not completed:
        raise KosovoRuntimeExposureHistoryError("commit-history pagination did not terminate within bound")
    if not commits:
        raise KosovoRuntimeExposureHistoryError("exact runtime exposure path has no commit history")

    return {
        "schema_version": HISTORY_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "ref_sha": REF_SHA,
        "repository_path": REPOSITORY_PATH,
        "retrieved_at_utc": now(),
        "commit_count": len(commits),
        "commits": commits,
        "history_complete_within_ref": True,
        "diffs_requested": False,
        "file_payloads_requested": False,
    }


def acquire_history_metadata() -> dict[str, Any]:
    _require_production_identity()
    return acquire_history_metadata_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        now=utc_now,
    )


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_file_bytes_accessed": False,
        "external_bytes_persisted": False,
        "transform_lineage_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_history(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoRuntimeExposureHistoryError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        history = acquire_history_metadata()
    except KosovoRuntimeExposureHistoryError:
        result.update({"status": "blocked", "failure_class": "metadata_acquisition_failure", "history": None})
        return result
    result.update({"status": "pass", "failure_class": None, "history": history})
    return result


def _validate_history(history: object) -> None:
    if type(history) is not dict or set(history) != _HISTORY_FIELDS:
        raise KosovoRuntimeExposureHistoryError("trusted history fields drifted")
    exact = (
        ("schema_version", HISTORY_SCHEMA_VERSION),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("ref_sha", REF_SHA),
        ("repository_path", REPOSITORY_PATH),
        ("history_complete_within_ref", True),
        ("diffs_requested", False),
        ("file_payloads_requested", False),
    )
    for field, expected in exact:
        observed = history.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoRuntimeExposureHistoryError(f"trusted history drifted at {field}")
    retrieved = history.get("retrieved_at_utc")
    if type(retrieved) is not str or len(retrieved) > 80 or _ISO_DATE_RE.match(retrieved) is None:
        raise KosovoRuntimeExposureHistoryError("trusted history retrieval time is invalid")
    count = history.get("commit_count")
    commits = history.get("commits")
    if type(count) is not int or isinstance(count, bool) or not (1 <= count <= MAX_COMMITS):
        raise KosovoRuntimeExposureHistoryError("trusted history commit count is invalid")
    if type(commits) is not list or len(commits) != count:
        raise KosovoRuntimeExposureHistoryError("trusted history commit array is invalid")
    ids: set[str] = set()
    for commit in commits:
        if type(commit) is not dict or set(commit) != _COMMIT_FIELDS:
            raise KosovoRuntimeExposureHistoryError("trusted commit metadata fields drifted")
        canonical = _canonical_commit(commit)
        if canonical != commit:
            raise KosovoRuntimeExposureHistoryError("trusted commit metadata is not canonical")
        if commit["id"] in ids:
            raise KosovoRuntimeExposureHistoryError("trusted history contains duplicate commit")
        ids.add(commit["id"])


def _validate_terminal_payload(result: object, *, execution_sha: str) -> bool:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise KosovoRuntimeExposureHistoryError("trusted history result fields drifted")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", CONTROL_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
        ("external_file_bytes_accessed", False),
        ("external_bytes_persisted", False),
        ("transform_lineage_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoRuntimeExposureHistoryError(f"trusted history result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise KosovoRuntimeExposureHistoryError("trusted history PASS failure class drifted")
        _validate_history(result.get("history"))
        return True
    if status == "blocked":
        if result.get("failure_class") != "metadata_acquisition_failure" or result.get("history") is not None:
            raise KosovoRuntimeExposureHistoryError("trusted history BLOCKED state drifted")
        return True
    raise KosovoRuntimeExposureHistoryError("trusted history result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    encoded = body.encode("utf-8", errors="strict")
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise KosovoRuntimeExposureHistoryError("trusted history result envelope is invalid")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureHistoryError("trusted history result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureHistoryError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureHistoryError("trusted history result JSON is invalid") from exc
    return _validate_terminal_payload(result, execution_sha=execution_sha)


def has_terminal_history_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise KosovoRuntimeExposureHistoryError("history result ledger is incomplete") from exc
    seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            seen = True
    return seen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")
    result = run_history(execution_sha=args.execution_sha)
    _validate_terminal_payload(result, execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
