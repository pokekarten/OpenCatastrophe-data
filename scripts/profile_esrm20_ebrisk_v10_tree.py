# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only profile of frozen ESRM20 ebrisk v1.0 tree paths.

The profiler resolves only the fixed public ESRM20 project/tag, requires the tag
to resolve to the already frozen immutable commit, and inventories repository
tree metadata at that commit. It never requests raw repository file contents or
an archive. Exact provider-predeclared ebrisk basenames are matched
case-sensitively and must each resolve to exactly one blob.

The resulting paths/object IDs prove repository-tree identity only. They do not
select a historical ebrisk group, authorize model execution, or authorize
publication/reuse of provider payload bytes.
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

SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-tree-profile-v1"
SOURCE_ISSUE = 281
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
TEMPLATE_BASENAMES = (
    "config_ebrisk_group1.ini",
    "config_ebrisk_group2.ini",
    "conif_ebrisk_group3.ini",
)
PER_PAGE = 100
MAX_PAGES = 200
MAX_PAGE_BYTES = 524_288
MAX_TAG_BYTES = 131_072
MAX_ENTRIES = PER_PAGE * MAX_PAGES
MAX_PATH_UTF8_BYTES = 2048
TOTAL_DEADLINE_SECONDS = 180.0

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}


class EbriskTreeProfileError(RuntimeError):
    """Raised when fixed ebrisk repository-tree metadata cannot be proven safely."""


def _strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EbriskTreeProfileError("ebrisk metadata response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise EbriskTreeProfileError(f"duplicate ebrisk metadata JSON key: {key}")
            obj[key] = value
        return obj

    def reject_nonfinite(token: str) -> Any:
        raise EbriskTreeProfileError(f"non-finite ebrisk metadata JSON value: {token}")

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except EbriskTreeProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise EbriskTreeProfileError("ebrisk metadata response is not valid JSON") from exc


def _bounded_text(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        raise EbriskTreeProfileError(f"ebrisk {label} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise EbriskTreeProfileError(f"ebrisk {label} is not UTF-8 encodable") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise EbriskTreeProfileError(f"ebrisk {label} exceeds policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise EbriskTreeProfileError(f"ebrisk {label} contains control characters")
    return value


def _tag_url() -> str:
    encoded = urllib.parse.quote(RELEASE_TAG, safe="")
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/{encoded}"


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise EbriskTreeProfileError("ebrisk commit SHA is invalid")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_PAGES):
        raise EbriskTreeProfileError("ebrisk tree page is outside policy")
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
            "User-Agent": "OpenCatastrophe-ESRM20-ebrisk-v10-tree-v1",
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
        raise EbriskTreeProfileError("ebrisk v1.0 tag acquisition failed closed") from exc

    value = _strict_json(raw)
    if type(value) is not dict:
        raise EbriskTreeProfileError("ebrisk tag response is not an object")
    if value.get("name") != RELEASE_TAG:
        raise EbriskTreeProfileError("ebrisk tag identity drifted")
    commit = value.get("commit")
    if type(commit) is not dict:
        raise EbriskTreeProfileError("ebrisk tag commit object is absent")
    commit_sha = commit.get("id")
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise EbriskTreeProfileError("ebrisk tag commit SHA is invalid")
    if commit_sha != EXPECTED_COMMIT_SHA:
        raise EbriskTreeProfileError("ebrisk v1.0 tag no longer resolves to frozen commit")
    return commit_sha


def _optional_bounded_header_int(
    headers: object, name: str, *, minimum: int, maximum: int
) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise EbriskTreeProfileError("ebrisk tree pagination headers are unavailable")
    raw = getter(name)
    if raw is None:
        return None
    if type(raw) is not str or not raw or not raw.isascii() or not raw.isdigit():
        raise EbriskTreeProfileError(f"ebrisk tree {name} is invalid")
    value = int(raw)
    if not (minimum <= value <= maximum):
        raise EbriskTreeProfileError(f"ebrisk tree {name} exceeds bounded policy")
    return value


def _pagination_next(headers: object, *, expected_page: int) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise EbriskTreeProfileError("ebrisk tree pagination headers are unavailable")
    observed_page = getter("X-Page")
    observed_per_page = getter("X-Per-Page")
    observed_next = getter("X-Next-Page")
    if not all(type(value) is str for value in (observed_page, observed_per_page, observed_next)):
        raise EbriskTreeProfileError("ebrisk tree pagination headers are incomplete")
    if observed_page != str(expected_page):
        raise EbriskTreeProfileError("ebrisk tree X-Page drifted")
    if observed_per_page != str(PER_PAGE):
        raise EbriskTreeProfileError("ebrisk tree X-Per-Page drifted")

    total_pages = _optional_bounded_header_int(
        headers, "X-Total-Pages", minimum=1, maximum=MAX_PAGES
    )
    total_entries = _optional_bounded_header_int(
        headers, "X-Total", minimum=1, maximum=MAX_ENTRIES
    )
    if total_pages is not None and total_pages < expected_page:
        raise EbriskTreeProfileError("ebrisk tree total pages precede current page")
    if total_pages is not None and total_entries is not None:
        expected_total_pages = (total_entries + PER_PAGE - 1) // PER_PAGE
        if expected_total_pages != total_pages:
            raise EbriskTreeProfileError("ebrisk tree total pagination metadata disagrees")

    if observed_next == "":
        if total_pages is not None and total_pages != expected_page:
            raise EbriskTreeProfileError("ebrisk terminal page disagrees with total pages")
        return None
    expected_next = expected_page + 1
    if observed_next != str(expected_next):
        raise EbriskTreeProfileError("ebrisk X-Next-Page is not contiguous")
    if expected_next > MAX_PAGES:
        raise EbriskTreeProfileError("ebrisk tree pagination exceeds page policy")
    if total_pages is not None and expected_next > total_pages:
        raise EbriskTreeProfileError("ebrisk X-Next-Page exceeds total pages")
    return expected_next


def _validate_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise EbriskTreeProfileError("ebrisk tree entry shape drifted")
    object_id = raw["id"]
    if type(object_id) is not str or _SHA1_RE.fullmatch(object_id) is None:
        raise EbriskTreeProfileError("ebrisk tree entry id is not a Git SHA-1")
    name = _bounded_text(raw["name"], label="name")
    path = _bounded_text(raw["path"], label="path")
    entry_type = raw["type"]
    mode = raw["mode"]
    if entry_type not in ("blob", "tree"):
        raise EbriskTreeProfileError("ebrisk tree entry type is unsupported")
    if type(mode) is not str or re.fullmatch(r"[0-7]{6}", mode) is None:
        raise EbriskTreeProfileError("ebrisk tree entry mode is invalid")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise EbriskTreeProfileError("ebrisk tree path is not canonical relative POSIX")
    if pure.name != name:
        raise EbriskTreeProfileError("ebrisk tree name/path identity drifted")
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


def _exact_template_paths(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    by_basename: dict[str, list[dict[str, str]]] = {name: [] for name in TEMPLATE_BASENAMES}
    for entry in entries:
        if entry["name"] in by_basename:
            by_basename[entry["name"]].append(entry)

    result: list[dict[str, str]] = []
    for basename in TEMPLATE_BASENAMES:
        matches = by_basename[basename]
        if len(matches) != 1:
            raise EbriskTreeProfileError(
                f"ebrisk template {basename} does not resolve to exactly one tree entry"
            )
        match = matches[0]
        if match["type"] != "blob":
            raise EbriskTreeProfileError(f"ebrisk template {basename} is not a blob")
        result.append(
            {
                "basename": basename,
                "path": match["path"],
                "type": match["type"],
                "object_sha1": match["id"],
            }
        )
    return result


def profile_v10_tree(*, opener: Any | None = None, monotonic: Any | None = None) -> dict[str, Any]:
    """Profile fixed ESRM20 v1.0 tree metadata and exact ebrisk template paths."""
    if transport._open_fixed is not _OPEN_FIXED or transport._read_bounded is not _READ_BOUNDED:
        raise EbriskTreeProfileError("trusted EFEHR transport authority drifted")
    if transport._validate_exact_response is not _VALIDATE_RESPONSE:
        raise EbriskTreeProfileError("trusted EFEHR response authority drifted")
    if transport._remaining is not _REMAINING or time.monotonic is not _MONOTONIC:
        raise EbriskTreeProfileError("trusted deadline authority drifted")

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
                "User-Agent": "OpenCatastrophe-ESRM20-ebrisk-v10-tree-v1",
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
                    raise EbriskTreeProfileError("ebrisk tree response is not an array")
                for raw_entry in raw_page:
                    entry = _validate_entry(raw_entry)
                    if entry["path"] in seen_paths:
                        raise EbriskTreeProfileError("ebrisk tree contains duplicate paths")
                    seen_paths.add(entry["path"])
                    entries.append(entry)
                    if len(entries) > MAX_ENTRIES:
                        raise EbriskTreeProfileError("ebrisk tree exceeds entry policy")
                next_page = _pagination_next(response.headers, expected_page=page)
        except EbriskTreeProfileError:
            raise
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise EbriskTreeProfileError("ebrisk tree metadata acquisition failed closed") from exc
        pages_read += 1
        if next_page is None:
            break
        page = next_page

    if not entries or pages_read < 1:
        raise EbriskTreeProfileError("ebrisk tree inventory is empty")
    blob_count = sum(entry["type"] == "blob" for entry in entries)
    tree_count = sum(entry["type"] == "tree" for entry in entries)
    top_level_counts = Counter(entry["path"].split("/", 1)[0] for entry in entries)
    exact_templates = _exact_template_paths(entries)

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
        "ebrisk_templates": exact_templates,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
