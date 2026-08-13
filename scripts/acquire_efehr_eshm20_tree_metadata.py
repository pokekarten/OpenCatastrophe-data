# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted metadata-only ESHM20 GitLab branch/tree inventory worker.

The operation is intentionally closed to one public EFEHR project, one branch,
and one selected repository prefix. It returns repository metadata only and
never requests provider file contents.
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
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT

SCHEMA_VERSION = "oc-efehr-eshm20-tree-metadata-v1"
OPERATION_ID = "eshm20-master-tree-metadata-v1"
SOURCE_ISSUE = 320
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
BRANCH = "master"
TREE_PREFIX = "oq_computational/oq_configuration_eshm20_v12e_region_main/"
BRANCH_API_URL = (
    f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/branches/"
    f"{urllib.parse.quote(BRANCH, safe='')}"
)
TREE_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree"
TREE_PER_PAGE = 100
MAX_BRANCH_RESPONSE_BYTES = 65_536
MAX_TREE_PAGE_BYTES = 1_048_576
MAX_TREE_PAGES = 20
MAX_TREE_ENTRIES = 2_000
MAX_TOTAL_METADATA_BYTES = 8_388_608
_GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
_TREE_TYPES = frozenset({"blob", "tree"})


def _strict_json(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EfehrAcquisitionError(f"{label} response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EfehrAcquisitionError(f"duplicate {label}-response JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EfehrAcquisitionError(
                    f"non-finite {label}-response JSON value: {token}"
                )
            ),
        )
    except json.JSONDecodeError as exc:
        raise EfehrAcquisitionError(f"{label} response is not valid JSON") from exc


def _tree_url(commit_sha: str, page: int) -> str:
    if not _GIT_SHA_RE.fullmatch(commit_sha):
        raise EfehrAcquisitionError("ESHM20 tree ref must be a full lowercase commit SHA")
    if type(page) is not int or not (1 <= page <= MAX_TREE_PAGES):
        raise EfehrAcquisitionError("ESHM20 tree page is outside the bounded policy")
    query = urllib.parse.urlencode(
        {
            "ref": commit_sha,
            "path": TREE_PREFIX.rstrip("/"),
            "recursive": "true",
            "per_page": TREE_PER_PAGE,
            "page": page,
        }
    )
    return f"{TREE_API_URL}?{query}"


def _resolve_master(
    *,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> tuple[str, int]:
    request = urllib.request.Request(
        BRANCH_API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-EFEHR-metadata-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, BRANCH_API_URL)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=MAX_BRANCH_RESPONSE_BYTES,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR branch metadata retrieval failed: {type(exc).__name__}"
        ) from exc

    payload = _strict_json(raw, label="branch")
    if type(payload) is not dict or payload.get("name") != BRANCH:
        raise EfehrAcquisitionError("EFEHR branch response does not match trusted master")
    commit = payload.get("commit")
    commit_sha = commit.get("id") if type(commit) is dict else None
    if type(commit_sha) is not str or not _GIT_SHA_RE.fullmatch(commit_sha):
        raise EfehrAcquisitionError(
            "EFEHR branch response lacks a full lowercase commit SHA"
        )
    return commit_sha, len(raw)


def _canonical_tree_entry(item: Any) -> dict[str, str]:
    if type(item) is not dict:
        raise EfehrAcquisitionError("EFEHR tree response contains a non-object entry")
    required = {"id", "name", "type", "path", "mode"}
    if not required.issubset(item):
        raise EfehrAcquisitionError("EFEHR tree entry lacks required metadata")
    object_id = item["id"]
    entry_type = item["type"]
    path = item["path"]
    mode = item["mode"]
    name = item["name"]
    if type(object_id) is not str or not _GIT_SHA_RE.fullmatch(object_id):
        raise EfehrAcquisitionError("EFEHR tree entry id is not a full lowercase Git SHA")
    if type(entry_type) is not str or entry_type not in _TREE_TYPES:
        raise EfehrAcquisitionError("EFEHR tree entry type is outside the bounded policy")
    if type(path) is not str or not (1 <= len(path) <= 1024):
        raise EfehrAcquisitionError("EFEHR tree entry path is not bounded text")
    if (
        "\\" in path
        or "\x00" in path
        or path.startswith("/")
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
    ):
        raise EfehrAcquisitionError("EFEHR tree entry path is not canonical POSIX text")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise EfehrAcquisitionError("EFEHR tree entry path is not canonical POSIX text")
    if not path.startswith(TREE_PREFIX):
        raise EfehrAcquisitionError("EFEHR tree entry escaped the selected prefix")
    if type(name) is not str or name != parts[-1]:
        raise EfehrAcquisitionError("EFEHR tree entry name/path identity drifted")
    if type(mode) is not str or not re.fullmatch(r"[0-7]{6}", mode):
        raise EfehrAcquisitionError("EFEHR tree entry mode is malformed")
    return {"path": path, "type": entry_type, "id": object_id, "mode": mode}


def _next_page(response: Any, *, current_page: int, item_count: int) -> int | None:
    raw_next = _header_value(response, "X-Next-Page")
    raw_page = _header_value(response, "X-Page")
    raw_per_page = _header_value(response, "X-Per-Page")
    if raw_page is not None and raw_page != str(current_page):
        raise EfehrAcquisitionError("EFEHR tree pagination current-page header drifted")
    if raw_per_page is not None and raw_per_page != str(TREE_PER_PAGE):
        raise EfehrAcquisitionError("EFEHR tree pagination per-page header drifted")

    if raw_next is None or raw_next == "":
        if raw_next is None and item_count == TREE_PER_PAGE:
            raise EfehrAcquisitionError(
                "EFEHR tree pagination is ambiguous at a full page boundary"
            )
        return None
    if not raw_next.isdigit():
        raise EfehrAcquisitionError("EFEHR tree next-page header is malformed")
    next_page = int(raw_next)
    if next_page != current_page + 1 or next_page > MAX_TREE_PAGES:
        raise EfehrAcquisitionError("EFEHR tree pagination left the contiguous bounded sequence")
    return next_page


def _inventory_tree(
    commit_sha: str,
    *,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> tuple[tuple[dict[str, str], ...], int, int]:
    entries: dict[str, dict[str, str]] = {}
    page = 1
    seen_pages: set[int] = set()
    total_bytes = 0
    page_count = 0

    while True:
        if page in seen_pages:
            raise EfehrAcquisitionError("EFEHR tree pagination loop detected")
        seen_pages.add(page)
        page_count += 1
        if page_count > MAX_TREE_PAGES:
            raise EfehrAcquisitionError("EFEHR tree exceeded the page bound")

        url = _tree_url(commit_sha, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-EFEHR-metadata-v1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=_remaining(deadline, monotonic)) as response:
                _validate_exact_response(response, url)
                raw = _read_bounded(
                    response,
                    deadline=deadline,
                    maximum=MAX_TREE_PAGE_BYTES,
                    monotonic=monotonic,
                )
                payload = _strict_json(raw, label="tree")
                if type(payload) is not list:
                    raise EfehrAcquisitionError(
                        "EFEHR tree response must be a JSON array"
                    )
                next_page = _next_page(
                    response, current_page=page, item_count=len(payload)
                )
        except EfehrAcquisitionError:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise EfehrAcquisitionError(
                f"EFEHR tree metadata retrieval failed: {type(exc).__name__}"
            ) from exc

        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_METADATA_BYTES:
            raise EfehrAcquisitionError(
                "EFEHR tree metadata exceeded the total byte bound"
            )
        for item in payload:
            entry = _canonical_tree_entry(item)
            path = entry["path"]
            if path in entries:
                raise EfehrAcquisitionError(
                    f"duplicate/conflicting EFEHR tree path: {path}"
                )
            entries[path] = entry
            if len(entries) > MAX_TREE_ENTRIES:
                raise EfehrAcquisitionError("EFEHR tree exceeded the entry bound")

        if next_page is None:
            break
        page = next_page

    if not entries:
        raise EfehrAcquisitionError("EFEHR selected tree prefix is empty")
    return tuple(entries[path] for path in sorted(entries)), page_count, total_bytes


def acquire_eshm20_tree_metadata(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Resolve trusted master and return only a bounded metadata inventory."""

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    commit_sha, branch_bytes = _resolve_master(
        opener=open_response,
        deadline=deadline,
        monotonic=monotonic,
    )
    entries, page_count, tree_bytes = _inventory_tree(
        commit_sha,
        opener=open_response,
        deadline=deadline,
        monotonic=monotonic,
    )
    retrieved_at = now()
    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": OPERATION_ID,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "branch": BRANCH,
        "resolved_commit_sha": commit_sha,
        "tree_prefix": TREE_PREFIX,
        "retrieved_at": retrieved_at,
        "tree_page_count": page_count,
        "tree_entry_count": len(entries),
        "metadata_byte_count": branch_bytes + tree_bytes,
        "entries": list(entries),
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
