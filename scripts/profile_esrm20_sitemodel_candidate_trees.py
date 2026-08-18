# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded tree-metadata comparison for ESRM20 Exposure-to-Site candidates.

The trusted #291 history receipt narrowed the historical Exposure-to-Site
repository to exactly three candidate commits around the ESRM20 v1.0 release.
This profiler inventories GitLab repository-tree metadata at only those immutable
candidate SHAs and compares blob object identities. It never requests repository
file contents, commit diffs, archives, raw URLs, or caller-selected refs/paths.

Changed paths/object IDs are provenance evidence only. They do not identify the
exact commit or invocation that generated the frozen Kosovo site model and do
not establish CRS, missing-value, publication, or model-use semantics.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-sitemodel-candidate-tree-profile-v1"
SOURCE_ISSUE = 291
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
HISTORY_IDENTITY_SHA256 = (
    "368858a0bce6ddb7fbc42adf1c520d23c7bf0102c533f6d9501a2b933170235d"
)
CANDIDATE_HISTORY = (
    {
        "commit_sha": "038c91d2bf5a07f6b54ff51639aad874d6837ea9",
        "committed_at_utc": "2021-12-10T09:20:39Z",
        "parent_shas": (
            "e8eddb6d9357419c74775ef5887a4b50f442778e",
            "cf7a026746bd411d4b80414611b97401a3aed41e",
        ),
    },
    {
        "commit_sha": "cf7a026746bd411d4b80414611b97401a3aed41e",
        "committed_at_utc": "2021-12-09T18:08:30Z",
        "parent_shas": ("e8eddb6d9357419c74775ef5887a4b50f442778e",),
    },
    {
        "commit_sha": "e8eddb6d9357419c74775ef5887a4b50f442778e",
        "committed_at_utc": "2021-12-06T09:28:07Z",
        "parent_shas": (),
    },
)
PER_PAGE = 100
MAX_PAGES_PER_COMMIT = 50
MAX_PAGE_BYTES = 524_288
MAX_ENTRIES_PER_COMMIT = PER_PAGE * MAX_PAGES_PER_COMMIT
MAX_CHANGED_BLOBS = 256
MAX_PATH_UTF8_BYTES = 2048
TOTAL_DEADLINE_SECONDS = 180.0

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}


class SiteModelCandidateTreeError(RuntimeError):
    """Raised when fixed candidate tree metadata cannot be proven safely."""


def _strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SiteModelCandidateTreeError(
            "site-tool tree metadata response is not UTF-8"
        ) from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise SiteModelCandidateTreeError(
                    f"duplicate site-tool tree metadata JSON key: {key}"
                )
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> Any:
        raise SiteModelCandidateTreeError(
            f"non-finite site-tool tree metadata JSON value: {token}"
        )

    def reject_float_overflow(token: str) -> float:
        try:
            value = float(token)
        except ValueError as exc:
            raise SiteModelCandidateTreeError(
                f"invalid site-tool tree metadata JSON float: {token}"
            ) from exc
        if not math.isfinite(value):
            raise SiteModelCandidateTreeError(
                f"non-finite site-tool tree metadata JSON value: {token}"
            )
        return value

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
            parse_float=reject_float_overflow,
        )
    except SiteModelCandidateTreeError:
        raise
    except json.JSONDecodeError as exc:
        raise SiteModelCandidateTreeError(
            "site-tool tree metadata response is not valid JSON"
        ) from exc


def _bounded_text(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        raise SiteModelCandidateTreeError(f"site-tool tree {label} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise SiteModelCandidateTreeError(
            f"site-tool tree {label} is not UTF-8 encodable"
        ) from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise SiteModelCandidateTreeError(f"site-tool tree {label} exceeds policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise SiteModelCandidateTreeError(
            f"site-tool tree {label} contains control characters"
        )
    return value


def _history_identity_sha256() -> str:
    canonical = "".join(
        (
            f"{item['commit_sha']}\t{item['committed_at_utc']}\t"
            f"{','.join(item['parent_shas'])}\n"
        )
        for item in CANDIDATE_HISTORY
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise SiteModelCandidateTreeError("candidate commit SHA is invalid")
    if (
        type(page) is not int
        or isinstance(page, bool)
        or not (1 <= page <= MAX_PAGES_PER_COMMIT)
    ):
        raise SiteModelCandidateTreeError("candidate tree page is outside policy")
    query = urllib.parse.urlencode(
        {
            "page": page,
            "per_page": PER_PAGE,
            "recursive": "true",
            "ref": commit_sha,
        }
    )
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree?{query}"


def _pagination_next(headers: object, *, expected_page: int) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise SiteModelCandidateTreeError("candidate tree pagination headers unavailable")
    observed_page = getter("X-Page")
    observed_per_page = getter("X-Per-Page")
    observed_next = getter("X-Next-Page")
    if not all(
        type(value) is str
        for value in (observed_page, observed_per_page, observed_next)
    ):
        raise SiteModelCandidateTreeError(
            "candidate tree pagination headers are incomplete"
        )
    if observed_page != str(expected_page):
        raise SiteModelCandidateTreeError("candidate tree X-Page drifted")
    if observed_per_page != str(PER_PAGE):
        raise SiteModelCandidateTreeError("candidate tree X-Per-Page drifted")
    if observed_next == "":
        return None
    expected_next = expected_page + 1
    if observed_next != str(expected_next):
        raise SiteModelCandidateTreeError(
            "candidate tree X-Next-Page is not contiguous"
        )
    if expected_next > MAX_PAGES_PER_COMMIT:
        raise SiteModelCandidateTreeError("candidate tree pagination exceeds policy")
    return expected_next


def _validate_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise SiteModelCandidateTreeError("candidate tree entry shape drifted")
    object_id = raw["id"]
    if type(object_id) is not str or _SHA1_RE.fullmatch(object_id) is None:
        raise SiteModelCandidateTreeError("candidate tree object id is not Git SHA-1")
    name = _bounded_text(raw["name"], label="name")
    path = _bounded_text(raw["path"], label="path")
    entry_type = raw["type"]
    mode = raw["mode"]
    if entry_type not in ("blob", "tree"):
        raise SiteModelCandidateTreeError("candidate tree entry type is unsupported")
    if type(mode) is not str or re.fullmatch(r"[0-7]{6}", mode) is None:
        raise SiteModelCandidateTreeError("candidate tree entry mode is invalid")
    valid_modes = {"tree": {"040000"}, "blob": {"100644", "100755", "120000"}}
    if mode not in valid_modes[entry_type]:
        raise SiteModelCandidateTreeError(
            "candidate tree entry type/mode pair is not canonical Git metadata"
        )
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise SiteModelCandidateTreeError(
            "candidate tree path is not canonical relative POSIX"
        )
    if pure.name != name:
        raise SiteModelCandidateTreeError("candidate tree name/path identity drifted")
    return {
        "id": object_id,
        "name": name,
        "type": entry_type,
        "path": path,
        "mode": mode,
    }


def _tree_identity_sha256(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in sorted(
            entries,
            key=lambda item: (item["path"], item["type"], item["id"]),
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_tree(
    commit_sha: str,
    *,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> tuple[list[dict[str, str]], int]:
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
                "User-Agent": "OpenCatastrophe-ESRM20-sitemodel-candidate-tree-v1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
                _VALIDATE_RESPONSE(response, url)
                raw = _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=MAX_PAGE_BYTES,
                    monotonic=monotonic,
                )
                raw_page = _strict_json(raw)
                if type(raw_page) is not list:
                    raise SiteModelCandidateTreeError(
                        "candidate tree response is not an array"
                    )
                for raw_entry in raw_page:
                    entry = _validate_entry(raw_entry)
                    if entry["path"] in seen_paths:
                        raise SiteModelCandidateTreeError(
                            "candidate tree contains duplicate path"
                        )
                    seen_paths.add(entry["path"])
                    entries.append(entry)
                    if len(entries) > MAX_ENTRIES_PER_COMMIT:
                        raise SiteModelCandidateTreeError(
                            "candidate tree exceeds entry policy"
                        )
                next_page = _pagination_next(
                    response.headers,
                    expected_page=page,
                )
        except SiteModelCandidateTreeError:
            raise
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise SiteModelCandidateTreeError(
                "candidate tree metadata acquisition failed closed"
            ) from exc
        pages_read += 1
        if next_page is None:
            break
        page = next_page

    if pages_read < 1 or not entries:
        raise SiteModelCandidateTreeError("candidate tree is empty")
    return entries, pages_read


def _blob_state(entries: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    return {
        entry["path"]: (entry["mode"], entry["id"])
        for entry in entries
        if entry["type"] == "blob"
    }


def _changed_blobs(
    trees: list[tuple[str, list[dict[str, str]]]],
) -> list[dict[str, Any]]:
    blob_maps = [(commit_sha, _blob_state(entries)) for commit_sha, entries in trees]
    paths = sorted({path for _, blob_map in blob_maps for path in blob_map})
    changed: list[dict[str, Any]] = []
    for path in paths:
        states = [blob_map.get(path) for _, blob_map in blob_maps]
        if len(set(states)) == 1:
            continue
        if len(changed) >= MAX_CHANGED_BLOBS:
            raise SiteModelCandidateTreeError(
                "candidate tree changed-blob set exceeds policy"
            )
        changed.append(
            {
                "path": path,
                "states": [
                    {
                        "commit_sha": commit_sha,
                        "present": state is not None,
                        "mode": state[0] if state is not None else None,
                        "object_sha1": state[1] if state is not None else None,
                    }
                    for (commit_sha, _), state in zip(blob_maps, states, strict=True)
                ],
            }
        )
    return changed


def _changed_blob_identity_sha256(changed: list[dict[str, Any]]) -> str:
    canonical_parts: list[str] = []
    for item in changed:
        canonical_parts.append(f"{item['path']}\n")
        for state in item["states"]:
            canonical_parts.append(
                (
                    f"{state['commit_sha']}\t{int(state['present'])}\t"
                    f"{state['mode'] or '-'}\t{state['object_sha1'] or '-'}\n"
                )
            )
    return hashlib.sha256("".join(canonical_parts).encode("utf-8")).hexdigest()


# Canonical production authority is captured only after every evidence-defining
# helper exists. The public production entry point validates this complete
# closure before any provider I/O. Synthetic seams remain private for tests.
_CANONICAL_CANDIDATE_HISTORY_OBJECT = CANDIDATE_HISTORY
_CANONICAL_CANDIDATE_HISTORY = tuple(
    (
        item["commit_sha"],
        item["committed_at_utc"],
        tuple(item["parent_shas"]),
    )
    for item in CANDIDATE_HISTORY
)
_CANONICAL_ALLOWED_ENTRY_FIELDS_OBJECT = _ALLOWED_ENTRY_FIELDS
_CANONICAL_ALLOWED_ENTRY_FIELDS = frozenset(_ALLOWED_ENTRY_FIELDS)
_CANONICAL_SHA1_RE = _SHA1_RE
_CANONICAL_PROVIDER_ROOT = PROVIDER_ROOT
_CANONICAL_POLICY = (
    SCHEMA_VERSION,
    SOURCE_ISSUE,
    PROJECT_ID,
    PROJECT_PATH,
    HISTORY_IDENTITY_SHA256,
    PER_PAGE,
    MAX_PAGES_PER_COMMIT,
    MAX_PAGE_BYTES,
    MAX_ENTRIES_PER_COMMIT,
    MAX_CHANGED_BLOBS,
    MAX_PATH_UTF8_BYTES,
    TOTAL_DEADLINE_SECONDS,
)
_SHA256 = hashlib.sha256
_URLENCODE = urllib.parse.urlencode
_REQUEST = urllib.request.Request
_RE_FULLMATCH = re.fullmatch
_STRICT_JSON = _strict_json
_BOUNDED_TEXT = _bounded_text
_HISTORY_IDENTITY = _history_identity_sha256
_TREE_URL = _tree_url
_PAGINATION_NEXT = _pagination_next
_VALIDATE_ENTRY = _validate_entry
_TREE_IDENTITY = _tree_identity_sha256
_READ_TREE = _read_tree
_BLOB_STATE = _blob_state
_CHANGED_BLOBS = _changed_blobs
_CHANGED_BLOB_IDENTITY = _changed_blob_identity_sha256


def _candidate_history_rows() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    try:
        return tuple(
            (
                item["commit_sha"],
                item["committed_at_utc"],
                tuple(item["parent_shas"]),
            )
            for item in CANDIDATE_HISTORY
        )
    except (KeyError, TypeError) as exc:
        raise SiteModelCandidateTreeError(
            "candidate-tree history production authority drifted"
        ) from exc


def _require_production_authority() -> None:
    current_policy = (
        SCHEMA_VERSION,
        SOURCE_ISSUE,
        PROJECT_ID,
        PROJECT_PATH,
        HISTORY_IDENTITY_SHA256,
        PER_PAGE,
        MAX_PAGES_PER_COMMIT,
        MAX_PAGE_BYTES,
        MAX_ENTRIES_PER_COMMIT,
        MAX_CHANGED_BLOBS,
        MAX_PATH_UTF8_BYTES,
        TOTAL_DEADLINE_SECONDS,
    )
    if current_policy != _CANONICAL_POLICY or PROVIDER_ROOT != _CANONICAL_PROVIDER_ROOT:
        raise SiteModelCandidateTreeError(
            "candidate-tree fixed production policy drifted"
        )
    if (
        CANDIDATE_HISTORY is not _CANONICAL_CANDIDATE_HISTORY_OBJECT
        or _candidate_history_rows() != _CANONICAL_CANDIDATE_HISTORY
    ):
        raise SiteModelCandidateTreeError(
            "candidate-tree history production authority drifted"
        )
    if (
        _ALLOWED_ENTRY_FIELDS is not _CANONICAL_ALLOWED_ENTRY_FIELDS_OBJECT
        or frozenset(_ALLOWED_ENTRY_FIELDS) != _CANONICAL_ALLOWED_ENTRY_FIELDS
        or _SHA1_RE is not _CANONICAL_SHA1_RE
        or _SHA1_RE.pattern != r"^[0-9a-f]{40}$"
        or _SHA1_RE.flags != re.UNICODE
    ):
        raise SiteModelCandidateTreeError(
            "candidate-tree entry policy production authority drifted"
        )
    if (
        hashlib.sha256 is not _SHA256
        or urllib.parse.urlencode is not _URLENCODE
        or urllib.request.Request is not _REQUEST
        or re.fullmatch is not _RE_FULLMATCH
    ):
        raise SiteModelCandidateTreeError(
            "candidate-tree primitive production authority drifted"
        )
    if (
        _strict_json is not _STRICT_JSON
        or _bounded_text is not _BOUNDED_TEXT
        or _history_identity_sha256 is not _HISTORY_IDENTITY
        or _tree_url is not _TREE_URL
        or _pagination_next is not _PAGINATION_NEXT
        or _validate_entry is not _VALIDATE_ENTRY
        or _tree_identity_sha256 is not _TREE_IDENTITY
        or _read_tree is not _READ_TREE
        or _blob_state is not _BLOB_STATE
        or _changed_blobs is not _CHANGED_BLOBS
        or _changed_blob_identity_sha256 is not _CHANGED_BLOB_IDENTITY
    ):
        raise SiteModelCandidateTreeError(
            "candidate-tree evidence production authority drifted"
        )
    if (
        transport._open_fixed is not _OPEN_FIXED
        or transport._read_bounded is not _READ_BOUNDED
        or transport._validate_exact_response is not _VALIDATE_RESPONSE
        or transport._remaining is not _REMAINING
        or time.monotonic is not _MONOTONIC
    ):
        raise SiteModelCandidateTreeError(
            "trusted EFEHR candidate-tree transport authority drifted"
        )
    if _history_identity_sha256() != HISTORY_IDENTITY_SHA256:
        raise SiteModelCandidateTreeError(
            "trusted site-tool history candidate identity drifted"
        )


def _profile_candidate_trees_for_test(
    *,
    opener: Any,
    monotonic: Any,
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    trees: list[tuple[str, list[dict[str, str]]]] = []
    profiles: list[dict[str, Any]] = []

    for history_item in CANDIDATE_HISTORY:
        commit_sha = history_item["commit_sha"]
        entries, pages_read = _read_tree(
            commit_sha,
            opener=opener,
            deadline=deadline,
            monotonic=monotonic,
        )
        trees.append((commit_sha, entries))
        profiles.append(
            {
                "commit_sha": commit_sha,
                "pages_read": pages_read,
                "entry_count": len(entries),
                "blob_count": sum(entry["type"] == "blob" for entry in entries),
                "tree_identity_sha256": _tree_identity_sha256(entries),
            }
        )

    changed = _changed_blobs(trees)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "history_identity_sha256": HISTORY_IDENTITY_SHA256,
        "candidate_tree_profiles": profiles,
        "changed_blob_count": len(changed),
        "changed_blob_identity_sha256": _changed_blob_identity_sha256(changed),
        "changed_blobs": changed,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_candidate_trees() -> dict[str, Any]:
    """Return bounded changed-blob metadata using only canonical production authority."""
    _require_production_authority()
    return _profile_candidate_trees_for_test(
        opener=_OPEN_FIXED,
        monotonic=_MONOTONIC,
    )
