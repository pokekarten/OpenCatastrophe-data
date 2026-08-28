# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Metadata-only tree delta around the Kosovo OQ exposure introduction commit."""

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
from collections import Counter
from pathlib import Path, PurePosixPath
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
from scripts.acquire_efehr_esrm20_scenario_tree_metadata import (
    _canonical_tree_entry,
    _next_page,
    _strict_json_array,
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
INTRO_COMMIT = "78e3f05af4fc3f285570172807c54774537ee309"
PARENT_COMMIT = "8d62f10c36ff58ea1ce88d156e315591e66aa0e6"
TARGET_PATH = "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"
TREE_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree"
PER_PAGE = 100
MAX_TREE_PAGES = 50
MAX_TREE_ENTRIES = 5_000
MAX_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 24_000_000
MAX_CHANGED_BLOBS = 2_500
MAX_CANDIDATES = 100
MAX_TERMINAL_UTF8_BYTES = 60_000
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_CODE_DOC_EXTENSIONS = frozenset(
    {".py", ".r", ".sh", ".ipynb", ".m", ".jl", ".js", ".ts", ".md", ".rst", ".txt"}
)
_CONFIG_EXTENSIONS = frozenset({".ini", ".cfg", ".toml", ".yml", ".yaml", ".json", ".xml"})
_NAME_HINT = re.compile(r"readme|script|tool|generat|format|convert|transform|spec|method|workflow", re.I)
_CONFIG_HINT = re.compile(r"config|configuration|job|openquake|(?:^|[_-])oq(?:[_-]|$)", re.I)
_CHANGE_KINDS = ("added", "deleted", "modified", "mode_changed")


class KosovoRuntimeExposureIntroTreeDeltaError(RuntimeError):
    """Fail-closed metadata-only tree comparison error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoRuntimeExposureIntroTreeDeltaError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise KosovoRuntimeExposureIntroTreeDeltaError(f"non-finite JSON constant: {token}")


def _load_object(text: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except KosovoRuntimeExposureIntroTreeDeltaError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoRuntimeExposureIntroTreeDeltaError(f"invalid {label} JSON") from exc
    if type(value) is not dict:
        raise KosovoRuntimeExposureIntroTreeDeltaError(f"{label} must be an object")
    return value


def _tree_url(ref_sha: str, page: int) -> str:
    if ref_sha not in {INTRO_COMMIT, PARENT_COMMIT}:
        raise KosovoRuntimeExposureIntroTreeDeltaError("tree ref left frozen two-commit boundary")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_TREE_PAGES):
        raise KosovoRuntimeExposureIntroTreeDeltaError("tree page left bounded policy")
    query = urllib.parse.urlencode(
        {"ref": ref_sha, "recursive": "true", "per_page": PER_PAGE, "page": page}
    )
    return f"{TREE_API_URL}?{query}"


def _fingerprint(entries: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(
            (f'{entry["path"]}\0{entry["type"]}\0{entry["id"]}\0{entry["mode"]}\n').encode("utf-8")
        )
    return digest.hexdigest()


def _inventory(
    ref_sha: str,
    *,
    opener: Any,
    deadline: float,
    monotonic: Callable[[], float],
    byte_budget: list[int],
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    entries: dict[str, dict[str, str]] = {}
    page = 1
    while True:
        url = _tree_url(ref_sha, page)
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-EFEHR-Kosovo-tree-delta-v1"},
            method="GET",
        )
        try:
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                raw = _read_bounded(
                    response, deadline=deadline, maximum=MAX_PAGE_BYTES, monotonic=monotonic
                )
                payload = _strict_json_array(raw)
                next_page = _next_page(response, current_page=page)
        except EfehrAcquisitionError as exc:
            raise KosovoRuntimeExposureIntroTreeDeltaError("provider tree metadata acquisition failed") from exc
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise KosovoRuntimeExposureIntroTreeDeltaError(
                f"provider tree metadata acquisition failed: {type(exc).__name__}"
            ) from exc
        byte_budget[0] += len(raw)
        if byte_budget[0] > MAX_TOTAL_METADATA_BYTES:
            raise KosovoRuntimeExposureIntroTreeDeltaError("combined tree metadata exceeded byte bound")
        if len(payload) > PER_PAGE:
            raise KosovoRuntimeExposureIntroTreeDeltaError("tree page exceeded entry bound")
        for item in payload:
            try:
                entry = _canonical_tree_entry(item)
            except EfehrAcquisitionError as exc:
                raise KosovoRuntimeExposureIntroTreeDeltaError("tree entry failed canonical validation") from exc
            if entry["path"] in entries:
                raise KosovoRuntimeExposureIntroTreeDeltaError("duplicate path in recursive tree")
            entries[entry["path"]] = entry
            if len(entries) > MAX_TREE_ENTRIES:
                raise KosovoRuntimeExposureIntroTreeDeltaError("tree exceeded entry bound")
        if next_page is None:
            break
        page = next_page
    values = list(entries.values())
    return entries, {
        "ref_sha": ref_sha,
        "entry_count": len(values),
        "blob_count": sum(item["type"] == "blob" for item in values),
        "tree_count": sum(item["type"] == "tree" for item in values),
        "metadata_sha256": _fingerprint(values),
    }


def _change_kind(parent: dict[str, str] | None, intro: dict[str, str] | None) -> str | None:
    if parent is None:
        return "added"
    if intro is None:
        return "deleted"
    if parent["id"] == intro["id"] and parent["mode"] == intro["mode"]:
        return None
    if parent["id"] == intro["id"]:
        return "mode_changed"
    return "modified"


def _candidate_class(path: str) -> str | None:
    if path == TARGET_PATH:
        return None
    pure = PurePosixPath(path.casefold())
    if pure.suffix in _CODE_DOC_EXTENSIONS or _NAME_HINT.search(path):
        return "code_doc"
    if pure.suffix in _CONFIG_EXTENSIONS and (pure.suffix != ".xml" or _CONFIG_HINT.search(path)):
        return "config"
    return None


def _changed_fingerprint(changed: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in changed:
        digest.update(json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def compare_tree_metadata_for_test(
    *, opener: Any, monotonic: Callable[[], float], now: Callable[[], str]
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    budget = [0]
    parent, parent_identity = _inventory(
        PARENT_COMMIT, opener=opener, deadline=deadline, monotonic=monotonic, byte_budget=budget
    )
    intro, intro_identity = _inventory(
        INTRO_COMMIT, opener=opener, deadline=deadline, monotonic=monotonic, byte_budget=budget
    )
    parent_blobs = {path: item for path, item in parent.items() if item["type"] == "blob"}
    intro_blobs = {path: item for path, item in intro.items() if item["type"] == "blob"}
    changed: list[dict[str, Any]] = []
    kinds: Counter[str] = Counter()
    top: Counter[str] = Counter()
    code_doc: list[str] = []
    config: list[str] = []
    target_kind: str | None = None
    for path in sorted(set(parent_blobs) | set(intro_blobs)):
        before = parent_blobs.get(path)
        after = intro_blobs.get(path)
        kind = _change_kind(before, after)
        if kind is None:
            continue
        item = {
            "path": path,
            "kind": kind,
            "parent_id": before["id"] if before else None,
            "parent_mode": before["mode"] if before else None,
            "introducing_id": after["id"] if after else None,
            "introducing_mode": after["mode"] if after else None,
        }
        changed.append(item)
        if len(changed) > MAX_CHANGED_BLOBS:
            raise KosovoRuntimeExposureIntroTreeDeltaError("changed blob count exceeded bound")
        kinds[kind] += 1
        top[path.split("/", 1)[0]] += 1
        if path == TARGET_PATH:
            target_kind = kind
        candidate = _candidate_class(path)
        if candidate == "code_doc":
            code_doc.append(path)
        elif candidate == "config":
            config.append(path)
    if target_kind not in {"added", "modified", "mode_changed"}:
        raise KosovoRuntimeExposureIntroTreeDeltaError("target did not change at frozen introducing commit")
    if len(code_doc) > MAX_CANDIDATES or len(config) > MAX_CANDIDATES:
        raise KosovoRuntimeExposureIntroTreeDeltaError("candidate sibling count exceeded bound")
    return {
        "schema_version": DELTA_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "introducing_commit": INTRO_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "target_path": TARGET_PATH,
        "retrieved_at_utc": now(),
        "parent_tree": parent_identity,
        "introducing_tree": intro_identity,
        "changed_blob_count": len(changed),
        "change_kind_counts": {kind: kinds[kind] for kind in _CHANGE_KINDS},
        "changed_blob_metadata_sha256": _changed_fingerprint(changed),
        "target_change_kind": target_kind,
        "changed_top_level_counts": [
            {"top_level": key, "changed_blob_count": top[key]} for key in sorted(top)
        ],
        "code_doc_candidate_count": len(code_doc),
        "code_doc_candidate_paths": sorted(code_doc),
        "config_candidate_count": len(config),
        "config_candidate_paths": sorted(config),
        "candidate_paths_complete": True,
        "file_payloads_requested": False,
        "commit_diffs_requested": False,
    }


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise KosovoRuntimeExposureIntroTreeDeltaError("production authority drifted")
    fixed = (
        (PROJECT_ID, 269),
        (INTRO_COMMIT, "78e3f05af4fc3f285570172807c54774537ee309"),
        (PARENT_COMMIT, "8d62f10c36ff58ea1ce88d156e315591e66aa0e6"),
        (TARGET_PATH, "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"),
    )
    if any(observed != expected for observed, expected in fixed):
        raise KosovoRuntimeExposureIntroTreeDeltaError("frozen tree-delta target drifted")


def compare_tree_metadata() -> dict[str, Any]:
    _require_production_identity()
    return compare_tree_metadata_for_test(
        opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC, now=utc_now
    )


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if expected_issue != CONTROL_ISSUE or type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid request execution fence")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureIntroTreeDeltaError("request envelope is not canonical")
    request = _load_object(after.strip(), "request")
    expected = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": CONTROL_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": DATASET_ID,
    }
    if set(request) != set(expected) | {"requester"}:
        raise KosovoRuntimeExposureIntroTreeDeltaError("request fields drifted")
    if any(type(request.get(key)) is not type(value) or request.get(key) != value for key, value in expected.items()):
        raise KosovoRuntimeExposureIntroTreeDeltaError("request identity drifted")
    requester = request.get("requester")
    if type(requester) is not str or requester != requester.strip() or _SAFE_REQUESTER_RE.fullmatch(requester) is None:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid requester")
    return request


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_file_bytes_accessed": False,
        "commit_diffs_requested": False,
        "external_bytes_persisted": False,
        "transform_lineage_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_tree_delta(*, execution_sha: str) -> dict[str, Any]:
    result = _base_result(execution_sha)
    try:
        delta = compare_tree_metadata()
    except KosovoRuntimeExposureIntroTreeDeltaError:
        result.update({"status": "blocked", "failure_class": "metadata_acquisition_failure", "tree_delta": None})
        return result
    result.update({"status": "pass", "failure_class": None, "tree_delta": delta})
    return result


def _validate_delta(delta: object) -> None:
    if type(delta) is not dict:
        raise KosovoRuntimeExposureIntroTreeDeltaError("tree delta is not an object")
    required = {
        "schema_version", "project_id", "project_path", "introducing_commit", "parent_commit",
        "target_path", "retrieved_at_utc", "parent_tree", "introducing_tree", "changed_blob_count",
        "change_kind_counts", "changed_blob_metadata_sha256", "target_change_kind",
        "changed_top_level_counts", "code_doc_candidate_count", "code_doc_candidate_paths",
        "config_candidate_count", "config_candidate_paths", "candidate_paths_complete",
        "file_payloads_requested", "commit_diffs_requested",
    }
    if set(delta) != required:
        raise KosovoRuntimeExposureIntroTreeDeltaError("tree-delta fields drifted")
    fixed = {
        "schema_version": DELTA_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "introducing_commit": INTRO_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "target_path": TARGET_PATH,
        "candidate_paths_complete": True,
        "file_payloads_requested": False,
        "commit_diffs_requested": False,
    }
    if any(delta.get(key) != value for key, value in fixed.items()):
        raise KosovoRuntimeExposureIntroTreeDeltaError("tree-delta identity drifted")
    changed = delta.get("changed_blob_count")
    counts = delta.get("change_kind_counts")
    if type(changed) is not int or not (1 <= changed <= MAX_CHANGED_BLOBS):
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid changed blob count")
    if type(counts) is not dict or set(counts) != set(_CHANGE_KINDS) or sum(counts.values()) != changed:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid change-kind counts")
    if delta.get("target_change_kind") not in {"added", "modified", "mode_changed"}:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid target change kind")
    for prefix in ("code_doc", "config"):
        count = delta.get(f"{prefix}_candidate_count")
        paths = delta.get(f"{prefix}_candidate_paths")
        if type(count) is not int or not (0 <= count <= MAX_CANDIDATES):
            raise KosovoRuntimeExposureIntroTreeDeltaError("invalid candidate count")
        if type(paths) is not list or len(paths) != count or paths != sorted(set(paths)) or TARGET_PATH in paths:
            raise KosovoRuntimeExposureIntroTreeDeltaError("invalid candidate paths")
    for tree_key, ref in (("parent_tree", PARENT_COMMIT), ("introducing_tree", INTRO_COMMIT)):
        tree = delta.get(tree_key)
        if type(tree) is not dict or tree.get("ref_sha") != ref:
            raise KosovoRuntimeExposureIntroTreeDeltaError("invalid tree identity")
        if re.fullmatch(r"[0-9a-f]{64}", str(tree.get("metadata_sha256"))) is None:
            raise KosovoRuntimeExposureIntroTreeDeltaError("invalid tree fingerprint")
    if re.fullmatch(r"[0-9a-f]{64}", str(delta.get("changed_blob_metadata_sha256"))) is None:
        raise KosovoRuntimeExposureIntroTreeDeltaError("invalid delta fingerprint")


def _validate_terminal_payload(result: object, *, execution_sha: str) -> bool:
    if type(result) is not dict:
        raise KosovoRuntimeExposureIntroTreeDeltaError("result is not an object")
    base = _base_result(execution_sha)
    if set(result) != set(base) | {"status", "failure_class", "tree_delta"}:
        raise KosovoRuntimeExposureIntroTreeDeltaError("result fields drifted")
    if any(result.get(key) != value for key, value in base.items()):
        raise KosovoRuntimeExposureIntroTreeDeltaError("result identity drifted")
    if result.get("status") == "pass":
        if result.get("failure_class") is not None:
            raise KosovoRuntimeExposureIntroTreeDeltaError("PASS failure class drifted")
        _validate_delta(result.get("tree_delta"))
        return True
    if result.get("status") == "blocked":
        if result.get("failure_class") != "metadata_acquisition_failure" or result.get("tree_delta") is not None:
            raise KosovoRuntimeExposureIntroTreeDeltaError("BLOCKED state drifted")
        return True
    raise KosovoRuntimeExposureIntroTreeDeltaError("non-terminal result")


def _parse_terminal(body: object, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if len(body.encode("utf-8")) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise KosovoRuntimeExposureIntroTreeDeltaError("terminal envelope is invalid")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoRuntimeExposureIntroTreeDeltaError("terminal envelope is malformed")
    return _validate_terminal_payload(_load_object(after.strip(), "result"), execution_sha=execution_sha)


def has_terminal_tree_delta_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise KosovoRuntimeExposureIntroTreeDeltaError("result ledger is incomplete") from exc
    return any(
        type(comment.get("user")) is dict
        and comment["user"].get("login") == TRUSTED_RESULT_LOGIN
        and _parse_terminal(comment.get("body"), execution_sha)
        for comment in comments
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required")
    result = run_tree_delta(execution_sha=args.execution_sha)
    _validate_terminal_payload(result, execution_sha=args.execution_sha)
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise KosovoRuntimeExposureIntroTreeDeltaError("result exceeds terminal bound")
    Path(args.output).write_bytes(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
