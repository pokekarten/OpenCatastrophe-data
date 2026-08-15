# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted metadata-only inventory for the ESRM20 v1.0 scenario-test release.

This operation is deliberately closed to EFEHR GitLab project 273 and release
``v1.0``. It resolves that tag to one full immutable commit SHA and lists only
bounded repository-tree metadata at that SHA. It never requests repository
file contents or the Zenodo/source archive.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _header_value,
        _open_fixed,
        _read_bounded,
        _remaining,
        _strict_json_object,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _header_value,
        _open_fixed,
        _read_bounded,
        _remaining,
        _strict_json_object,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT

# Production authority comes only from these private canonical bindings. Public
# aliases below remain reviewable/backwards-compatible, but a pre-network drift
# guard rejects any rebinding before an opener can receive a request.
_CANONICAL_SCHEMA_VERSION = "oc-efehr-esrm20-scenario-tree-metadata-v1"
_CANONICAL_OPERATION_ID = "esrm20-scenario-tests-v1-tree-metadata-v1"
_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_CANONICAL_PROVIDER_HOST = PROVIDER_HOST
_CANONICAL_PROVIDER_ROOT = PROVIDER_ROOT
_CANONICAL_PROJECT_ID = 273
_CANONICAL_PROJECT_PATH = "efehr/esrm20_scenario_tests"
_CANONICAL_RELEASE_TAG = "v1.0"
_CANONICAL_TAG_API_URL = (
    f"{_CANONICAL_PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/"
    f"repository/tags/{urllib.parse.quote(_CANONICAL_RELEASE_TAG, safe='')}"
)
_CANONICAL_TREE_API_URL = (
    f"{_CANONICAL_PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/"
    "repository/tree"
)
_CANONICAL_TREE_PER_PAGE = 100
_CANONICAL_MAX_TAG_RESPONSE_BYTES = 65_536
_CANONICAL_MAX_TREE_PAGE_BYTES = 1_048_576
_CANONICAL_MAX_TREE_PAGES = 50
_CANONICAL_MAX_TREE_ENTRIES = 5_000
_CANONICAL_MAX_TOTAL_METADATA_BYTES = 16_777_216
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
RELEASE_TAG = _CANONICAL_RELEASE_TAG
TAG_API_URL = _CANONICAL_TAG_API_URL
TREE_API_URL = _CANONICAL_TREE_API_URL
TREE_PER_PAGE = _CANONICAL_TREE_PER_PAGE
MAX_TAG_RESPONSE_BYTES = _CANONICAL_MAX_TAG_RESPONSE_BYTES
MAX_TREE_PAGE_BYTES = _CANONICAL_MAX_TREE_PAGE_BYTES
MAX_TREE_PAGES = _CANONICAL_MAX_TREE_PAGES
MAX_TREE_ENTRIES = _CANONICAL_MAX_TREE_ENTRIES
MAX_TOTAL_METADATA_BYTES = _CANONICAL_MAX_TOTAL_METADATA_BYTES

_GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
_TREE_TYPES = frozenset({"blob", "tree"})
_ALLOWED_MODES_BY_TYPE = {
    "blob": frozenset({"100644", "100755"}),
    "tree": frozenset({"040000"}),
}


def _require_canonical_target() -> None:
    """Fail before provider work if any published fixed authority drifts."""

    exact_aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROVIDER_HOST, _CANONICAL_PROVIDER_HOST, "provider host"),
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (TAG_API_URL, _CANONICAL_TAG_API_URL, "tag API URL"),
        (TREE_API_URL, _CANONICAL_TREE_API_URL, "tree API URL"),
    )
    for observed, expected, label in exact_aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise EfehrAcquisitionError(
                f"frozen ESRM20 scenario {label} authority drifted"
            )


def _strict_json_array(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EfehrAcquisitionError("EFEHR scenario tree response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EfehrAcquisitionError(
                    f"duplicate scenario-tree JSON key: {key}"
                )
            result[key] = value
        return result

    try:
        payload = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EfehrAcquisitionError(
                    f"non-finite scenario-tree JSON value: {token}"
                )
            ),
        )
    except json.JSONDecodeError as exc:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree response is not valid JSON"
        ) from exc
    if type(payload) is not list:
        raise EfehrAcquisitionError("EFEHR scenario tree response must be a JSON array")
    return payload


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or not _GIT_SHA_RE.fullmatch(commit_sha):
        raise EfehrAcquisitionError(
            "ESRM20 scenario tree ref must be a full lowercase commit SHA"
        )
    if type(page) is not int or not (1 <= page <= _CANONICAL_MAX_TREE_PAGES):
        raise EfehrAcquisitionError(
            "ESRM20 scenario tree page is outside the bounded policy"
        )
    query = urllib.parse.urlencode(
        {
            "ref": commit_sha,
            "recursive": "true",
            "per_page": _CANONICAL_TREE_PER_PAGE,
            "page": page,
        }
    )
    return f"{_CANONICAL_TREE_API_URL}?{query}"


def _resolve_v1_tag(
    *,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> tuple[str, int]:
    request = urllib.request.Request(
        _CANONICAL_TAG_API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-EFEHR-scenario-metadata-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, _CANONICAL_TAG_API_URL)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_MAX_TAG_RESPONSE_BYTES,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR scenario tag resolution failed: {type(exc).__name__}"
        ) from exc

    payload = _strict_json_object(raw)
    if payload.get("name") != _CANONICAL_RELEASE_TAG:
        raise EfehrAcquisitionError(
            "EFEHR scenario tag response does not match trusted v1.0 release"
        )
    commit = payload.get("commit")
    commit_sha = commit.get("id") if type(commit) is dict else None
    if type(commit_sha) is not str or not _GIT_SHA_RE.fullmatch(commit_sha):
        raise EfehrAcquisitionError(
            "EFEHR scenario tag response lacks a full lowercase commit SHA"
        )
    target = payload.get("target")
    if type(target) is not str or target != commit_sha:
        raise EfehrAcquisitionError(
            "EFEHR scenario tag target/commit identity drifted"
        )
    return commit_sha, len(raw)


def _canonical_tree_entry(item: Any) -> dict[str, str]:
    if type(item) is not dict:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree response contains a non-object entry"
        )
    required = {"id", "name", "type", "path", "mode"}
    if not required.issubset(item):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry lacks required metadata"
        )

    object_id = item["id"]
    entry_type = item["type"]
    path = item["path"]
    mode = item["mode"]
    name = item["name"]

    if type(object_id) is not str or not _GIT_SHA_RE.fullmatch(object_id):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry id is not a full lowercase Git SHA"
        )
    if type(entry_type) is not str or entry_type not in _TREE_TYPES:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry type is outside the bounded policy"
        )
    if type(path) is not str or not (1 <= len(path) <= 1024):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry path is not bounded text"
        )
    if (
        "\\" in path
        or "\x00" in path
        or path.startswith("/")
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
    ):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry path is not canonical POSIX text"
        )
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry path is not canonical POSIX text"
        )
    if type(name) is not str or name != parts[-1]:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry name/path identity drifted"
        )
    if type(mode) is not str or not re.fullmatch(r"[0-7]{6}", mode):
        raise EfehrAcquisitionError("EFEHR scenario tree entry mode is malformed")
    if mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree entry type/mode combination is not permitted"
        )
    return {"path": path, "type": entry_type, "id": object_id, "mode": mode}


def _next_page(response: Any, *, current_page: int) -> int | None:
    raw_next = _header_value(response, "X-Next-Page")
    raw_page = _header_value(response, "X-Page")
    raw_per_page = _header_value(response, "X-Per-Page")
    if raw_next is None or raw_page is None or raw_per_page is None:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree pagination headers are incomplete"
        )
    if raw_page != str(current_page):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree pagination current-page header drifted"
        )
    if raw_per_page != str(_CANONICAL_TREE_PER_PAGE):
        raise EfehrAcquisitionError(
            "EFEHR scenario tree pagination per-page header drifted"
        )
    if raw_next == "":
        return None
    if not raw_next.isdigit():
        raise EfehrAcquisitionError(
            "EFEHR scenario tree next-page header is malformed"
        )
    next_page = int(raw_next)
    if next_page != current_page + 1 or next_page > _CANONICAL_MAX_TREE_PAGES:
        raise EfehrAcquisitionError(
            "EFEHR scenario tree pagination left the contiguous bounded sequence"
        )
    return next_page


def _inventory_tree(
    commit_sha: str,
    *,
    tag_bytes: int,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> tuple[tuple[dict[str, str], ...], int, int]:
    entries: dict[str, dict[str, str]] = {}
    page = 1
    seen_pages: set[int] = set()
    tree_bytes = 0
    page_count = 0

    while True:
        if page in seen_pages:
            raise EfehrAcquisitionError(
                "EFEHR scenario tree pagination loop detected"
            )
        seen_pages.add(page)
        page_count += 1
        if page_count > _CANONICAL_MAX_TREE_PAGES:
            raise EfehrAcquisitionError(
                "EFEHR scenario tree exceeded the page bound"
            )

        url = _tree_url(commit_sha, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-EFEHR-scenario-metadata-v1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                raw = _read_bounded(
                    response,
                    deadline=deadline,
                    maximum=_CANONICAL_MAX_TREE_PAGE_BYTES,
                    monotonic=monotonic,
                )
                payload = _strict_json_array(raw)
                next_page = _next_page(response, current_page=page)
        except EfehrAcquisitionError:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise EfehrAcquisitionError(
                f"EFEHR scenario tree metadata retrieval failed: {type(exc).__name__}"
            ) from exc

        tree_bytes += len(raw)
        if tag_bytes + tree_bytes > _CANONICAL_MAX_TOTAL_METADATA_BYTES:
            raise EfehrAcquisitionError(
                "EFEHR scenario metadata exceeded the aggregate total byte bound"
            )
        for item in payload:
            entry = _canonical_tree_entry(item)
            path = entry["path"]
            if path in entries:
                raise EfehrAcquisitionError(
                    f"duplicate/conflicting EFEHR scenario tree path: {path}"
                )
            entries[path] = entry
            if len(entries) > _CANONICAL_MAX_TREE_ENTRIES:
                raise EfehrAcquisitionError(
                    "EFEHR scenario tree exceeded the entry bound"
                )

        if next_page is None:
            break
        page = next_page

    if not entries:
        raise EfehrAcquisitionError("EFEHR scenario repository tree is empty")
    return tuple(entries[path] for path in sorted(entries)), page_count, tree_bytes


def acquire_esrm20_scenario_tree_metadata(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Resolve fixed v1.0 and return only bounded immutable tree metadata."""

    _require_canonical_target()
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    commit_sha, tag_bytes = _resolve_v1_tag(
        opener=open_response,
        deadline=deadline,
        monotonic=monotonic,
    )
    entries, page_count, tree_bytes = _inventory_tree(
        commit_sha,
        tag_bytes=tag_bytes,
        opener=open_response,
        deadline=deadline,
        monotonic=monotonic,
    )
    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "operation_id": _CANONICAL_OPERATION_ID,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": _CANONICAL_PROVIDER_HOST,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "tag_api_url": _CANONICAL_TAG_API_URL,
        "resolved_commit_sha": commit_sha,
        "retrieved_at": now(),
        "tree_page_count": page_count,
        "tree_entry_count": len(entries),
        "metadata_byte_count": tag_bytes + tree_bytes,
        "entries": list(entries),
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
