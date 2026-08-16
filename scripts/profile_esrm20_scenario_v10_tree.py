# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only profile of the frozen ESRM20 scenario-test v1.0 tree.

The profiler resolves only the fixed public project/tag to an immutable commit
and inventories repository-tree metadata at that commit. It never requests raw
repository file contents or the published archive. Event-name matches are
predeclared discovery evidence only, not scenario selection or model-use
approval.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-scenario-v10-tree-profile-v1"
SOURCE_ISSUE = 285
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
PER_PAGE = 100
MAX_PAGES = 200
MAX_PAGE_BYTES = 524_288
MAX_TAG_BYTES = 131_072
MAX_ENTRIES = PER_PAGE * MAX_PAGES
MAX_PATH_UTF8_BYTES = 2048
MAX_EVENT_CANDIDATES = 256
TOTAL_DEADLINE_SECONDS = 180.0
EVENT_LITERALS = ("athens", "thessaloniki")

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}


class ScenarioTreeProfileError(RuntimeError):
    """Raised when fixed scenario metadata cannot be proven safely."""


def _strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScenarioTreeProfileError("scenario metadata response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise ScenarioTreeProfileError(f"duplicate scenario metadata JSON key: {key}")
            obj[key] = value
        return obj

    def reject_nonfinite(token: str) -> Any:
        raise ScenarioTreeProfileError(f"non-finite scenario metadata JSON value: {token}")

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except ScenarioTreeProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise ScenarioTreeProfileError("scenario metadata response is not valid JSON") from exc


def _bounded_text(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        raise ScenarioTreeProfileError(f"scenario {label} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioTreeProfileError(f"scenario {label} is not UTF-8 encodable") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise ScenarioTreeProfileError(f"scenario {label} exceeds policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ScenarioTreeProfileError(f"scenario {label} contains control characters")
    return value


def _tag_url() -> str:
    encoded = urllib.parse.quote(RELEASE_TAG, safe="")
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/{encoded}"


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise ScenarioTreeProfileError("scenario commit SHA is invalid")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_PAGES):
        raise ScenarioTreeProfileError("scenario tree page is outside policy")
    query = urllib.parse.urlencode(
        {
            "page": page,
            "per_page": PER_PAGE,
            "recursive": "true",
            "ref": commit_sha,
        }
    )
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree?{query}"


def _resolve_tag_commit(*, opener: Any, deadline: float, monotonic: Any) -> str:
    url = _tag_url()
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-ESRM20-scenario-v10-tree-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            raw = _READ_BOUNDED(
                response,
                deadline=deadline,
                maximum=MAX_TAG_BYTES,
                monotonic=monotonic,
            )
    except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
        raise ScenarioTreeProfileError("scenario v1.0 tag acquisition failed closed") from exc

    value = _strict_json(raw)
    if type(value) is not dict:
        raise ScenarioTreeProfileError("scenario tag response is not an object")
    if value.get("name") != RELEASE_TAG:
        raise ScenarioTreeProfileError("scenario tag identity drifted")
    commit = value.get("commit")
    if type(commit) is not dict:
        raise ScenarioTreeProfileError("scenario tag commit object is absent")
    commit_sha = commit.get("id")
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise ScenarioTreeProfileError("scenario tag commit SHA is invalid")
    return commit_sha


def _optional_bounded_header_int(
    headers: object, name: str, *, minimum: int, maximum: int
) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise ScenarioTreeProfileError("scenario tree pagination headers are unavailable")
    raw = getter(name)
    if raw is None:
        return None
    if type(raw) is not str or not raw or not raw.isascii() or not raw.isdigit():
        raise ScenarioTreeProfileError(f"scenario tree {name} is invalid")
    value = int(raw)
    if not (minimum <= value <= maximum):
        raise ScenarioTreeProfileError(f"scenario tree {name} exceeds bounded policy")
    return value


def _pagination_next(headers: object, *, expected_page: int) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise ScenarioTreeProfileError("scenario tree pagination headers are unavailable")
    observed_page = getter("X-Page")
    observed_per_page = getter("X-Per-Page")
    observed_next = getter("X-Next-Page")
    if not all(type(value) is str for value in (observed_page, observed_per_page, observed_next)):
        raise ScenarioTreeProfileError("scenario tree pagination headers are incomplete")
    if observed_page != str(expected_page):
        raise ScenarioTreeProfileError("scenario tree X-Page drifted")
    if observed_per_page != str(PER_PAGE):
        raise ScenarioTreeProfileError("scenario tree X-Per-Page drifted")

    total_pages = _optional_bounded_header_int(
        headers, "X-Total-Pages", minimum=1, maximum=MAX_PAGES
    )
    total_entries = _optional_bounded_header_int(
        headers, "X-Total", minimum=1, maximum=MAX_ENTRIES
    )
    if total_pages is not None and total_pages < expected_page:
        raise ScenarioTreeProfileError("scenario tree total pages precede current page")
    if total_pages is not None and total_entries is not None:
        expected_total_pages = (total_entries + PER_PAGE - 1) // PER_PAGE
        if expected_total_pages != total_pages:
            raise ScenarioTreeProfileError("scenario tree total pagination metadata disagrees")

    if observed_next == "":
        if total_pages is not None and total_pages != expected_page:
            raise ScenarioTreeProfileError("scenario terminal page disagrees with total pages")
        return None
    expected_next = expected_page + 1
    if observed_next != str(expected_next):
        raise ScenarioTreeProfileError("scenario X-Next-Page is not contiguous")
    if expected_next > MAX_PAGES:
        raise ScenarioTreeProfileError("scenario tree pagination exceeds page policy")
    if total_pages is not None and expected_next > total_pages:
        raise ScenarioTreeProfileError("scenario X-Next-Page exceeds total pages")
    return expected_next


def _validate_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise ScenarioTreeProfileError("scenario tree entry shape drifted")
    object_id = raw["id"]
    if type(object_id) is not str or _SHA1_RE.fullmatch(object_id) is None:
        raise ScenarioTreeProfileError("scenario tree entry id is not a Git SHA-1")
    name = _bounded_text(raw["name"], label="name")
    path = _bounded_text(raw["path"], label="path")
    entry_type = raw["type"]
    mode = raw["mode"]
    if entry_type not in ("blob", "tree"):
        raise ScenarioTreeProfileError("scenario tree entry type is unsupported")
    if type(mode) is not str or re.fullmatch(r"[0-7]{6}", mode) is None:
        raise ScenarioTreeProfileError("scenario tree entry mode is invalid")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ScenarioTreeProfileError("scenario tree path is not canonical relative POSIX")
    if pure.name != name:
        raise ScenarioTreeProfileError("scenario tree name/path identity drifted")
    return {
        "id": object_id,
        "name": name,
        "type": entry_type,
        "path": path,
        "mode": mode,
    }


def _inventory_sha256(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in sorted(entries, key=lambda item: (item["path"], item["type"], item["id"]))
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _event_candidates(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for entry in entries:
        folded = entry["path"].casefold()
        for literal in EVENT_LITERALS:
            if literal in folded:
                candidates.append(
                    {
                        "event_literal": literal,
                        "path": entry["path"],
                        "type": entry["type"],
                        "object_sha1": entry["id"],
                    }
                )
    candidates.sort(key=lambda item: (item["event_literal"], item["path"], item["type"]))
    if len(candidates) > MAX_EVENT_CANDIDATES:
        raise ScenarioTreeProfileError("scenario event candidate set exceeds bounded policy")
    identities = {(item["event_literal"], item["path"], item["type"]) for item in candidates}
    if len(identities) != len(candidates):
        raise ScenarioTreeProfileError("scenario event candidate set contains duplicates")
    return candidates


def profile_v10_tree(*, opener: Any | None = None, monotonic: Any | None = None) -> dict[str, Any]:
    """Resolve the fixed v1.0 tag and profile only bounded tree metadata."""
    if transport._open_fixed is not _OPEN_FIXED or transport._read_bounded is not _READ_BOUNDED:
        raise ScenarioTreeProfileError("trusted EFEHR transport authority drifted")
    if transport._validate_exact_response is not _VALIDATE_RESPONSE:
        raise ScenarioTreeProfileError("trusted EFEHR response authority drifted")
    if transport._remaining is not _REMAINING or time.monotonic is not _MONOTONIC:
        raise ScenarioTreeProfileError("trusted deadline authority drifted")

    clock = monotonic or _MONOTONIC
    open_response = opener or _OPEN_FIXED
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    commit_sha = _resolve_tag_commit(opener=open_response, deadline=deadline, monotonic=clock)

    entries: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    page = 1
    pages_read = 0
    while True:
        url = _tree_url(commit_sha, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-ESRM20-scenario-v10-tree-v1",
            },
            method="GET",
        )
        try:
            with open_response(request, timeout=_REMAINING(deadline, clock)) as response:
                _VALIDATE_RESPONSE(response, url)
                raw = _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=MAX_PAGE_BYTES,
                    monotonic=clock,
                )
                raw_page = _strict_json(raw)
                if type(raw_page) is not list:
                    raise ScenarioTreeProfileError("scenario tree response is not an array")
                for raw_entry in raw_page:
                    entry = _validate_entry(raw_entry)
                    if entry["path"] in seen_paths:
                        raise ScenarioTreeProfileError("scenario tree contains duplicate paths")
                    seen_paths.add(entry["path"])
                    entries.append(entry)
                    if len(entries) > MAX_ENTRIES:
                        raise ScenarioTreeProfileError("scenario tree exceeds entry policy")
                next_page = _pagination_next(response.headers, expected_page=page)
        except ScenarioTreeProfileError:
            raise
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise ScenarioTreeProfileError("scenario tree metadata acquisition failed closed") from exc
        pages_read += 1
        if next_page is None:
            break
        page = next_page

    if not entries or pages_read < 1:
        raise ScenarioTreeProfileError("scenario tree inventory is empty")
    blob_count = sum(entry["type"] == "blob" for entry in entries)
    tree_count = sum(entry["type"] == "tree" for entry in entries)
    top_level_counts = Counter(entry["path"].split("/", 1)[0] for entry in entries)
    candidates = _event_candidates(entries)
    present = {literal: any(item["event_literal"] == literal for item in candidates) for literal in EVENT_LITERALS}

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": commit_sha,
        "pages_read": pages_read,
        "entry_count": len(entries),
        "blob_count": blob_count,
        "tree_count": tree_count,
        "tree_identity_sha256": _inventory_sha256(entries),
        "top_level_entry_counts": dict(sorted(top_level_counts.items())),
        "event_literal_candidates": candidates,
        "athens_present": present["athens"],
        "thessaloniki_present": present["thessaloniki"],
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "scenario_selection_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
