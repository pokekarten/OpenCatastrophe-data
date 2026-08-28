# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compare the exact parent/introducing ESRM20 runtime-exposure trees.

This is the last bounded public-lineage probe for the frozen Kosovo residential
runtime exposure path. It reads repository-tree metadata only from EFEHR GitLab
project 269 for one exact parent/introducing commit pair. It never requests file
payloads or commit diffs.

The result inventories only blob paths whose object identity changed. It may
surface co-changed paths that look like generator/specification candidates, but
it does not claim that any candidate generated the runtime exposure.
"""

from __future__ import annotations

import argparse
import hashlib
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
    _header_value,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
    utc_now,
)
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-runtime-exposure-intro-tree-delta-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-runtime-exposure-intro-tree-delta-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-runtime-exposure-intro-tree-delta-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-runtime-exposure-intro-tree-delta-result-v1"
DELTA_SCHEMA_VERSION = "oc-efehr-esrm20-kosovo-runtime-exposure-intro-tree-delta-v1"
ACTION = "esrm20_kosovo_runtime_exposure_intro_tree_delta"
CONTROL_ISSUE = 282
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
INTRODUCING_SHA = "78e3f05af4fc3f285570172807c54774537ee309"
PARENT_SHA = "8d62f10c36ff58ea1ce88d156e315591e66aa0e6"
TARGET_PATH = "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"
TREE_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree"
PER_PAGE = 100
MAX_PAGES = 50
MAX_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 16_777_216
MAX_BLOBS = 10_000
MAX_CHANGED_PATHS = 1_000
MAX_TERMINAL_UTF8_BYTES = 60_000
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_CANDIDATE_RE = re.compile(
    r"(?:^|/)(?:[^/]*(?:generat|convert|transform|script|format|schema|spec|tool|readme|build)[^/]*)$",
    re.I,
)
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "delta",
    "external_file_bytes_accessed",
    "external_bytes_persisted",
    "transform_lineage_verified",
    "publication_authorized",
    "model_use_authorized",
}


class KosovoRuntimeExposureTreeDeltaError(RuntimeError):
    """Fail-closed tree-delta acquisition or validation error."""


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise KosovoRuntimeExposureTreeDeltaError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise KosovoRuntimeExposureTreeDeltaError(f"non-finite JSON constant: {token}")


def _load_json_array(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoRuntimeExposureTreeDeltaError("tree metadata is not UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureTreeDeltaError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureTreeDeltaError("tree metadata is invalid JSON") from exc
    if type(value) is not list:
        raise KosovoRuntimeExposureTreeDeltaError("tree metadata must be an array")
    return value


def _canonical_path(path: object) -> str:
    if type(path) is not str or not (1 <= len(path) <= 1024):
        raise KosovoRuntimeExposureTreeDeltaError("tree path is not bounded text")
    if (
        "\\" in path
        or "\x00" in path
        or path.startswith("/")
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise KosovoRuntimeExposureTreeDeltaError("tree path is not canonical POSIX text")
    return path


def _canonical_blob(item: object) -> dict[str, str] | None:
    if type(item) is not dict:
        raise KosovoRuntimeExposureTreeDeltaError("tree entry is not an object")
    entry_type = item.get("type")
    if entry_type == "tree":
        return None
    if entry_type != "blob":
        raise KosovoRuntimeExposureTreeDeltaError("tree entry type is outside bounded policy")
    object_id = item.get("id")
    mode = item.get("mode")
    path = _canonical_path(item.get("path"))
    if type(object_id) is not str or _SHA_RE.fullmatch(object_id) is None:
        raise KosovoRuntimeExposureTreeDeltaError("tree blob id is invalid")
    if type(mode) is not str or re.fullmatch(r"[0-7]{6}", mode) is None:
        raise KosovoRuntimeExposureTreeDeltaError("tree blob mode is invalid")
    return {"path": path, "id": object_id, "mode": mode}


def _tree_url(ref: str, page: int) -> str:
    if type(ref) is not str or _SHA_RE.fullmatch(ref) is None:
        raise KosovoRuntimeExposureTreeDeltaError("tree ref is invalid")
    if type(page) is not int or isinstance(page, bool) or not 1 <= page <= MAX_PAGES:
        raise KosovoRuntimeExposureTreeDeltaError("tree page is outside bounded policy")
    query = urllib.parse.urlencode(
        {"ref": ref, "recursive": "true", "per_page": PER_PAGE, "page": page}
    )
    return f"{TREE_API_URL}?{query}"


def _next_page(response: Any, *, current_page: int) -> int | None:
    raw_next = _header_value(response, "X-Next-Page")
    raw_page = _header_value(response, "X-Page")
    raw_per_page = _header_value(response, "X-Per-Page")
    if raw_next is None or raw_page is None or raw_per_page is None:
        raise KosovoRuntimeExposureTreeDeltaError("tree pagination headers are incomplete")
    if raw_page != str(current_page) or raw_per_page != str(PER_PAGE):
        raise KosovoRuntimeExposureTreeDeltaError("tree pagination headers drifted")
    if raw_next == "":
        return None
    if not raw_next.isdigit():
        raise KosovoRuntimeExposureTreeDeltaError("tree next-page header is malformed")
    next_page = int(raw_next)
    if next_page != current_page + 1 or next_page > MAX_PAGES:
        raise KosovoRuntimeExposureTreeDeltaError("tree pagination left bounded sequence")
    return next_page


def _inventory_tree_for_test(
    ref: str,
    *,
    opener: Any,
    monotonic: Callable[[], float],
    deadline: float,
    byte_budget: list[int],
) -> list[dict[str, str]]:
    blobs: dict[str, dict[str, str]] = {}
    page = 1
    while True:
        url = _tree_url(ref, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-EFEHR-Kosovo-intro-tree-delta-v1",
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
                next_page = _next_page(response, current_page=page)
        except EfehrAcquisitionError as exc:
            raise KosovoRuntimeExposureTreeDeltaError("provider tree metadata acquisition failed") from exc
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise KosovoRuntimeExposureTreeDeltaError(
                f"provider tree metadata acquisition failed: {type(exc).__name__}"
            ) from exc

        byte_budget[0] += len(raw)
        if byte_budget[0] > MAX_TOTAL_METADATA_BYTES:
            raise KosovoRuntimeExposureTreeDeltaError("tree metadata exceeded total byte bound")
        values = _load_json_array(raw)
        if len(values) > PER_PAGE:
            raise KosovoRuntimeExposureTreeDeltaError("tree page exceeded result bound")
        for value in values:
            blob = _canonical_blob(value)
            if blob is None:
                continue
            path = blob["path"]
            if path in blobs:
                raise KosovoRuntimeExposureTreeDeltaError("duplicate tree blob path")
            blobs[path] = blob
            if len(blobs) > MAX_BLOBS:
                raise KosovoRuntimeExposureTreeDeltaError("tree blob count exceeded bound")
        if next_page is None:
            break
        page = next_page

    return [blobs[path] for path in sorted(blobs)]


def _tree_identity(blobs: list[dict[str, str]]) -> dict[str, Any]:
    payload = json.dumps(
        blobs, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return {
        "blob_count": len(blobs),
        "metadata_sha256": hashlib.sha256(payload).hexdigest(),
    }


def compare_trees_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    now: Callable[[], str],
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    byte_budget = [0]
    parent = _inventory_tree_for_test(
        PARENT_SHA,
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        byte_budget=byte_budget,
    )
    introduced = _inventory_tree_for_test(
        INTRODUCING_SHA,
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        byte_budget=byte_budget,
    )
    parent_by_path = {item["path"]: item for item in parent}
    introduced_by_path = {item["path"]: item for item in introduced}

    changed: list[dict[str, str]] = []
    for path in sorted(set(parent_by_path) | set(introduced_by_path)):
        before = parent_by_path.get(path)
        after = introduced_by_path.get(path)
        if before == after:
            continue
        if before is None:
            status = "added"
        elif after is None:
            status = "deleted"
        else:
            status = "modified"
        changed.append({"path": path, "status": status})
        if len(changed) > MAX_CHANGED_PATHS:
            raise KosovoRuntimeExposureTreeDeltaError("changed path count exceeded bound")

    target = next((item for item in changed if item["path"] == TARGET_PATH), None)
    if target is None or target["status"] != "added":
        raise KosovoRuntimeExposureTreeDeltaError(
            "frozen runtime exposure target is not added by introducing commit"
        )

    candidates = [
        item["path"]
        for item in changed
        if item["path"] != TARGET_PATH and _CANDIDATE_RE.search(item["path"])
    ]
    return {
        "schema_version": DELTA_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "parent_sha": PARENT_SHA,
        "introducing_sha": INTRODUCING_SHA,
        "target_path": TARGET_PATH,
        "retrieved_at_utc": now(),
        "parent_tree": _tree_identity(parent),
        "introducing_tree": _tree_identity(introduced),
        "metadata_byte_count": byte_budget[0],
        "changed_path_count": len(changed),
        "changed_paths": changed,
        "target_change": "added",
        "plausible_generator_or_spec_paths": candidates,
        "plausible_generator_or_spec_path_count": len(candidates),
        "trees_complete": True,
        "diffs_requested": False,
        "file_payloads_requested": False,
    }


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise KosovoRuntimeExposureTreeDeltaError("production transport authority drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise KosovoRuntimeExposureTreeDeltaError("production clock authority drifted")
    exact = (
        (PROJECT_ID, 269),
        (PROJECT_PATH, "efehr/esrm20"),
        (INTRODUCING_SHA, "78e3f05af4fc3f285570172807c54774537ee309"),
        (PARENT_SHA, "8d62f10c36ff58ea1ce88d156e315591e66aa0e6"),
        (TARGET_PATH, "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoRuntimeExposureTreeDeltaError("frozen tree-delta authority drifted")


def acquire_delta() -> dict[str, Any]:
    _require_production_identity()
    return compare_trees_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        now=utc_now,
    )


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise KosovoRuntimeExposureTreeDeltaError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoRuntimeExposureTreeDeltaError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoRuntimeExposureTreeDeltaError("invalid tree-delta request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureTreeDeltaError("tree-delta request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureTreeDeltaError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureTreeDeltaError("invalid tree-delta request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoRuntimeExposureTreeDeltaError("tree-delta request fields drifted")
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
            raise KosovoRuntimeExposureTreeDeltaError(f"tree-delta request {field} drifted")
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise KosovoRuntimeExposureTreeDeltaError("invalid requester identity")
    return request


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


def run_delta(*, execution_sha: str) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        delta = acquire_delta()
    except KosovoRuntimeExposureTreeDeltaError:
        result.update({"status": "blocked", "failure_class": "metadata_acquisition_failure", "delta": None})
        return result
    result.update({"status": "pass", "failure_class": None, "delta": delta})
    return result


def _validate_terminal_payload(result: object, *, execution_sha: str) -> bool:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta result fields drifted")
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
        if result.get(field) != expected or type(result.get(field)) is not type(expected):
            raise KosovoRuntimeExposureTreeDeltaError(f"trusted tree-delta result drifted at {field}")
    status = result.get("status")
    if status == "blocked":
        if result.get("failure_class") != "metadata_acquisition_failure" or result.get("delta") is not None:
            raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta BLOCKED state drifted")
        return True
    if status != "pass" or result.get("failure_class") is not None:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta result has non-terminal status")
    delta = result.get("delta")
    if type(delta) is not dict:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta payload is missing")
    exact_delta = (
        ("schema_version", DELTA_SCHEMA_VERSION),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("parent_sha", PARENT_SHA),
        ("introducing_sha", INTRODUCING_SHA),
        ("target_path", TARGET_PATH),
        ("target_change", "added"),
        ("trees_complete", True),
        ("diffs_requested", False),
        ("file_payloads_requested", False),
    )
    for field, expected in exact_delta:
        if delta.get(field) != expected or type(delta.get(field)) is not type(expected):
            raise KosovoRuntimeExposureTreeDeltaError(f"trusted tree-delta payload drifted at {field}")
    changed = delta.get("changed_paths")
    count = delta.get("changed_path_count")
    candidates = delta.get("plausible_generator_or_spec_paths")
    candidate_count = delta.get("plausible_generator_or_spec_path_count")
    if type(changed) is not list or type(count) is not int or len(changed) != count:
        raise KosovoRuntimeExposureTreeDeltaError("trusted changed-path inventory drifted")
    if type(candidates) is not list or type(candidate_count) is not int or len(candidates) != candidate_count:
        raise KosovoRuntimeExposureTreeDeltaError("trusted candidate-path inventory drifted")
    if count < 1 or count > MAX_CHANGED_PATHS or candidate_count < 0 or candidate_count > count:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta counts are invalid")
    if not any(
        type(item) is dict and item.get("path") == TARGET_PATH and item.get("status") == "added"
        for item in changed
    ):
        raise KosovoRuntimeExposureTreeDeltaError("trusted target addition is missing")
    return True


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    encoded = body.encode("utf-8", errors="strict")
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta result envelope is invalid")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureTreeDeltaError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureTreeDeltaError("trusted tree-delta result JSON is invalid") from exc
    return _validate_terminal_payload(result, execution_sha=execution_sha)


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise KosovoRuntimeExposureTreeDeltaError("tree-delta result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


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
    result = run_delta(execution_sha=args.execution_sha)
    _validate_terminal_payload(result, execution_sha=args.execution_sha)
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise KosovoRuntimeExposureTreeDeltaError("tree-delta result exceeds terminal byte bound")
    Path(args.output).write_bytes(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
