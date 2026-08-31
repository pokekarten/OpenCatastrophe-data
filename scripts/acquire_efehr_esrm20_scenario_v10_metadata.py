# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only resolver for ESRM20 scenario-tests v1.0.

The operation is deliberately closed to public EFEHR GitLab project 273,
``efehr/esrm20_scenario_tests``, and release tag ``v1.0``. It resolves that
tag to a full immutable commit and inventories recursive repository-tree
metadata only. It never requests repository file payloads, archive bytes,
commit diffs, model outputs, or observed-damage values.

A successful result proves only provider metadata identity and inventory
structure. It does not prove scientific validity, untouched holdout status,
publication authority, or model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Iterable

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

SCHEMA_VERSION = "oc-efehr-esrm20-scenario-v10-metadata-v1"
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
TAG_API_URL = (
    f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/"
    f"{urllib.parse.quote(RELEASE_TAG, safe='')}"
)
TREE_API_URL = f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree"
PER_PAGE = 100
MAX_PAGES = 200
MAX_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 32 * 1024 * 1024
MAX_ENTRIES = 20_000
MAX_EVENT_CANDIDATES = 256
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MODE_RE = re.compile(r"^[0-7]{6}$")
_EVENT_HINT_RE = re.compile(r"(?:thessalon|athens|1978|1999)", re.I)

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class ScenarioV10MetadataError(RuntimeError):
    """Fail-closed project-273 v1.0 metadata error."""


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ScenarioV10MetadataError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise ScenarioV10MetadataError(f"non-finite JSON constant: {token}")


def _load_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScenarioV10MetadataError("provider metadata is not UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except ScenarioV10MetadataError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioV10MetadataError("provider metadata is invalid JSON") from exc


def _canonical_path(value: object) -> str:
    if type(value) is not str or not (1 <= len(value.encode("utf-8")) <= 1024):
        raise ScenarioV10MetadataError("tree path is outside bounded text policy")
    if (
        value.startswith("/")
        or value.endswith("/")
        or "\\" in value
        or "\x00" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ScenarioV10MetadataError("tree path is not canonical repository-relative POSIX text")
    return value


def _canonical_commit(payload: object) -> str:
    if type(payload) is not dict:
        raise ScenarioV10MetadataError("tag metadata must be an object")
    if payload.get("name") != RELEASE_TAG:
        raise ScenarioV10MetadataError("tag metadata does not match fixed v1.0 release")
    commit = payload.get("commit")
    commit_sha = commit.get("id") if type(commit) is dict else None
    if type(commit_sha) is not str or _SHA_RE.fullmatch(commit_sha) is None:
        raise ScenarioV10MetadataError("tag metadata lacks a full lowercase commit SHA")
    return commit_sha


def _canonical_entry(value: object) -> dict[str, str]:
    if type(value) is not dict:
        raise ScenarioV10MetadataError("tree entry is not an object")
    entry_type = value.get("type")
    if entry_type not in {"blob", "tree"}:
        raise ScenarioV10MetadataError("tree entry type is outside bounded policy")
    object_id = value.get("id")
    mode = value.get("mode")
    path = _canonical_path(value.get("path"))
    if type(object_id) is not str or _SHA_RE.fullmatch(object_id) is None:
        raise ScenarioV10MetadataError("tree object id is invalid")
    if type(mode) is not str or _MODE_RE.fullmatch(mode) is None:
        raise ScenarioV10MetadataError("tree object mode is invalid")
    return {"path": path, "type": entry_type, "id": object_id, "mode": mode}


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _SHA_RE.fullmatch(commit_sha) is None:
        raise ScenarioV10MetadataError("tree ref is not a full immutable commit SHA")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_PAGES):
        raise ScenarioV10MetadataError("tree page is outside bounded policy")
    query = urllib.parse.urlencode(
        {
            "ref": commit_sha,
            "recursive": "true",
            "per_page": PER_PAGE,
            "page": page,
        }
    )
    return f"{TREE_API_URL}?{query}"


def _next_page(response: Any, *, current_page: int) -> int | None:
    raw_next = _header_value(response, "X-Next-Page")
    raw_page = _header_value(response, "X-Page")
    raw_per_page = _header_value(response, "X-Per-Page")
    if raw_next is None or raw_page is None or raw_per_page is None:
        raise ScenarioV10MetadataError("tree pagination headers are incomplete")
    if raw_page != str(current_page) or raw_per_page != str(PER_PAGE):
        raise ScenarioV10MetadataError("tree pagination headers drifted")
    if raw_next == "":
        return None
    if not raw_next.isdigit():
        raise ScenarioV10MetadataError("tree next-page header is malformed")
    next_page = int(raw_next)
    if next_page != current_page + 1 or next_page > MAX_PAGES:
        raise ScenarioV10MetadataError("tree pagination left bounded sequence")
    return next_page


def _resolve_tag_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    deadline: float,
    byte_budget: list[int],
) -> str:
    request = urllib.request.Request(
        TAG_API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-EFEHR-scenario-v10-metadata-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, TAG_API_URL)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=MAX_PAGE_BYTES,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise ScenarioV10MetadataError("provider tag metadata acquisition failed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise ScenarioV10MetadataError(
            f"provider tag metadata acquisition failed: {type(exc).__name__}"
        ) from exc
    byte_budget[0] += len(raw)
    if byte_budget[0] > MAX_TOTAL_METADATA_BYTES:
        raise ScenarioV10MetadataError("provider metadata exceeded total byte bound")
    return _canonical_commit(_load_json(raw))


def _inventory_tree_for_test(
    commit_sha: str,
    *,
    opener: Any,
    monotonic: Callable[[], float],
    deadline: float,
    byte_budget: list[int],
) -> list[dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    page = 1
    while True:
        url = _tree_url(commit_sha, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-EFEHR-scenario-v10-metadata-v1",
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
            raise ScenarioV10MetadataError("provider tree metadata acquisition failed") from exc
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise ScenarioV10MetadataError(
                f"provider tree metadata acquisition failed: {type(exc).__name__}"
            ) from exc

        byte_budget[0] += len(raw)
        if byte_budget[0] > MAX_TOTAL_METADATA_BYTES:
            raise ScenarioV10MetadataError("provider metadata exceeded total byte bound")
        payload = _load_json(raw)
        if type(payload) is not list or len(payload) > PER_PAGE:
            raise ScenarioV10MetadataError("tree metadata page is outside bounded array policy")
        for raw_entry in payload:
            entry = _canonical_entry(raw_entry)
            path = entry["path"]
            if path in entries:
                raise ScenarioV10MetadataError("duplicate tree path in recursive inventory")
            entries[path] = entry
            if len(entries) > MAX_ENTRIES:
                raise ScenarioV10MetadataError("tree entry count exceeded bounded policy")

        if next_page is None:
            break
        page = next_page

    if not entries:
        raise ScenarioV10MetadataError("resolved v1.0 tree inventory is empty")
    return [entries[path] for path in sorted(entries)]


def _inventory_identity(entries: list[dict[str, str]]) -> str:
    payload = json.dumps(
        entries,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def acquire_metadata_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    now: Callable[[], str],
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    byte_budget = [0]
    commit_sha = _resolve_tag_for_test(
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        byte_budget=byte_budget,
    )
    entries = _inventory_tree_for_test(
        commit_sha,
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        byte_budget=byte_budget,
    )
    event_candidates = [
        entry["path"]
        for entry in entries
        if _EVENT_HINT_RE.search(entry["path"]) is not None
    ]
    if len(event_candidates) > MAX_EVENT_CANDIDATES:
        raise ScenarioV10MetadataError("event-hint candidate count exceeded bounded policy")

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": commit_sha,
        "retrieved_at_utc": now(),
        "metadata_byte_count": byte_budget[0],
        "entry_count": len(entries),
        "inventory_metadata_sha256": _inventory_identity(entries),
        "entries": entries,
        "event_hint_regex": _EVENT_HINT_RE.pattern,
        "event_candidate_path_count": len(event_candidates),
        "event_candidate_paths": event_candidates,
        "recursive_tree_complete_within_bounds": True,
        "file_payloads_requested": False,
        "archive_bytes_requested": False,
        "commit_diffs_requested": False,
        "scientific_validation_verified": False,
        "untouched_holdout_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise ScenarioV10MetadataError("production transport authority drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise ScenarioV10MetadataError("production clock authority drifted")
    exact = (
        (PROJECT_ID, 273),
        (PROJECT_PATH, "efehr/esrm20_scenario_tests"),
        (RELEASE_TAG, "v1.0"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioV10MetadataError("frozen project-273 v1.0 authority drifted")


def acquire_metadata() -> dict[str, Any]:
    """Resolve the fixed release and inventory metadata only."""
    _require_production_identity()
    return acquire_metadata_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        now=utc_now,
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve fixed ESRM20 scenario-tests v1.0 and inventory tree metadata."
    )
    parser.parse_args(list(argv) if argv is not None else None)
    payload = acquire_metadata()
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
