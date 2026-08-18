# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile only immutable ESRM20 v1.0 ``Exposure_30arcsec`` tree metadata.

This module is deliberately closed to EFEHR GitLab project 269, release v1.0,
the already frozen commit, and one fixed repository subtree.  It never requests
repository file contents or archives.  Provider paths containing the exact
source spelling ``Kosovo`` and ending in ``.xml`` are reported only as named
metadata candidates; no candidate is selected for execution or scientific use.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-exposure-v10-tree-profile-v1"
SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
SUBTREE_PATH = "Exposure_30arcsec"
PROVIDER_KOSOVO_TOKEN = "Kosovo"
TREE_PER_PAGE = 100
MAX_TREE_PAGES = 30
MAX_TREE_ENTRIES = 3_000
MAX_TAG_BYTES = 131_072
MAX_TREE_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 12_582_912
MAX_PATH_UTF8_BYTES = 2_048
MAX_KOSOVO_XML_CANDIDATES = 16
TOTAL_DEADLINE_SECONDS = 180.0

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}
_ALLOWED_MODES_BY_TYPE = {
    "blob": frozenset({"100644", "100755"}),
    "tree": frozenset({"040000"}),
}

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_HEADER_VALUE = transport._header_value
_STRICT_JSON_OBJECT = transport._strict_json_object
_MONOTONIC = time.monotonic
_REQUEST = urllib.request.Request
_PROVIDER_ROOT = PROVIDER_ROOT

FAILURE_CLASSES = frozenset(
    {
        "tag_metadata_acquisition_failure",
        "tag_metadata_validation_failure",
        "tree_metadata_acquisition_failure",
        "tree_metadata_validation_failure",
        "candidate_resolution_failure",
    }
)


class ExposureTreeProfileError(RuntimeError):
    """Fail-closed error for the fixed exposure tree metadata profile."""

    def __init__(self, message: str, *, failure_class: str | None = None) -> None:
        super().__init__(message)
        if failure_class is not None and failure_class not in FAILURE_CLASSES:
            raise ValueError("invalid exposure-tree failure class")
        self.failure_class = failure_class


def _tag_url() -> str:
    tag = urllib.parse.quote(RELEASE_TAG, safe="")
    return f"{_PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/{tag}"


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _GIT_SHA_RE.fullmatch(commit_sha) is None:
        raise ExposureTreeProfileError("exposure tree commit SHA is invalid")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_TREE_PAGES):
        raise ExposureTreeProfileError("exposure tree page is outside policy")
    query = urllib.parse.urlencode(
        {
            "page": page,
            "path": SUBTREE_PATH,
            "per_page": TREE_PER_PAGE,
            "recursive": "true",
            "ref": commit_sha,
        }
    )
    return f"{_PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree?{query}"


def _strict_json_array(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ExposureTreeProfileError("exposure tree response is not UTF-8") from exc

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ExposureTreeProfileError(
                    f"duplicate exposure-tree JSON key: {key}"
                )
            result[key] = value
        return result

    def reject_constant(token: str) -> Any:
        raise ExposureTreeProfileError(
            f"non-finite exposure-tree JSON value: {token}"
        )

    def finite_float(token: str) -> float:
        try:
            value = float(token)
        except ValueError as exc:
            raise ExposureTreeProfileError(
                f"invalid exposure-tree JSON float: {token}"
            ) from exc
        if not math.isfinite(value):
            raise ExposureTreeProfileError(
                f"non-finite exposure-tree JSON value: {token}"
            )
        return value

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except ExposureTreeProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise ExposureTreeProfileError("exposure tree response is not valid JSON") from exc
    if type(value) is not list:
        raise ExposureTreeProfileError("exposure tree response is not an array")
    return value


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value:
        raise ExposureTreeProfileError(f"exposure {field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ExposureTreeProfileError(f"exposure {field} is not UTF-8") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise ExposureTreeProfileError(f"exposure {field} exceeds policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ExposureTreeProfileError(f"exposure {field} contains control characters")
    return value


def _canonical_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise ExposureTreeProfileError("exposure tree entry shape drifted")
    object_id = raw["id"]
    if type(object_id) is not str or _GIT_SHA_RE.fullmatch(object_id) is None:
        raise ExposureTreeProfileError("exposure tree object id is invalid")
    entry_type = raw["type"]
    if entry_type not in _ALLOWED_MODES_BY_TYPE:
        raise ExposureTreeProfileError("exposure tree object type is unsupported")
    mode = raw["mode"]
    if type(mode) is not str or mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
        raise ExposureTreeProfileError("exposure tree type/mode identity drifted")
    path = _bounded_text(raw["path"], field="tree path")
    name = _bounded_text(raw["name"], field="tree name")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in ("", ".", "..") for part in pure.parts)
        or "\\" in path
    ):
        raise ExposureTreeProfileError("exposure tree path is not canonical relative POSIX")
    if pure.name != name:
        raise ExposureTreeProfileError("exposure tree path/name identity drifted")
    prefix = SUBTREE_PATH + "/"
    if not path.startswith(prefix):
        raise ExposureTreeProfileError("exposure tree entry escaped fixed subtree")
    return {
        "id": object_id,
        "mode": mode,
        "name": name,
        "path": path,
        "type": entry_type,
    }


def _pagination_next(headers: object, *, page: int) -> int | None:
    raw_page = _HEADER_VALUE(headers, "X-Page")
    raw_per_page = _HEADER_VALUE(headers, "X-Per-Page")
    raw_next = _HEADER_VALUE(headers, "X-Next-Page")
    if raw_page != str(page) or raw_per_page != str(TREE_PER_PAGE):
        raise ExposureTreeProfileError("exposure tree pagination identity drifted")
    if raw_next == "":
        return None
    if type(raw_next) is not str or not raw_next.isascii() or not raw_next.isdigit():
        raise ExposureTreeProfileError("exposure tree next-page header is invalid")
    next_page = int(raw_next)
    if next_page != page + 1 or next_page > MAX_TREE_PAGES:
        raise ExposureTreeProfileError("exposure tree pagination is not contiguous")
    return next_page


def _resolve_tag_commit(*, opener: Any, monotonic: Any, deadline: float) -> tuple[str, int]:
    url = _tag_url()
    request = _REQUEST(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-ESRM20-exposure-v10-tree-v1",
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
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError, transport.EfehrAcquisitionError) as exc:
        raise ExposureTreeProfileError(
            "exposure v1.0 tag acquisition failed closed",
            failure_class="tag_metadata_acquisition_failure",
        ) from exc

    try:
        value = _STRICT_JSON_OBJECT(raw)
        if value.get("name") != RELEASE_TAG:
            raise ExposureTreeProfileError("exposure release-tag identity drifted")
        commit = value.get("commit")
        commit_sha = commit.get("id") if type(commit) is dict else None
        if type(commit_sha) is not str or _GIT_SHA_RE.fullmatch(commit_sha) is None:
            raise ExposureTreeProfileError("exposure release tag lacks immutable commit")
        target = value.get("target")
        if type(target) is not str or target != commit_sha:
            raise ExposureTreeProfileError("exposure tag target/commit identity drifted")
        if commit_sha != EXPECTED_COMMIT_SHA:
            raise ExposureTreeProfileError("exposure v1.0 tag moved from frozen commit")
        return commit_sha, len(raw)
    except ExposureTreeProfileError as exc:
        if exc.failure_class is not None:
            raise
        raise ExposureTreeProfileError(
            str(exc), failure_class="tag_metadata_validation_failure"
        ) from exc
    except transport.EfehrAcquisitionError as exc:
        raise ExposureTreeProfileError(
            "exposure v1.0 tag metadata failed validation",
            failure_class="tag_metadata_validation_failure",
        ) from exc


def _inventory_tree(
    commit_sha: str,
    *,
    opener: Any,
    monotonic: Any,
    deadline: float,
    tag_bytes: int,
) -> tuple[list[dict[str, str]], int]:
    entries: dict[str, dict[str, str]] = {}
    total_bytes = tag_bytes
    page = 1
    pages_read = 0
    try:
        while True:
            pages_read += 1
            if pages_read > MAX_TREE_PAGES:
                raise ExposureTreeProfileError("exposure tree page bound exceeded")
            url = _tree_url(commit_sha, page)
            request = _REQUEST(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "OpenCatastrophe-ESRM20-exposure-v10-tree-v1",
                },
                method="GET",
            )
            try:
                with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
                    _VALIDATE_RESPONSE(response, url)
                    raw = _READ_BOUNDED(
                        response,
                        deadline=deadline,
                        maximum=MAX_TREE_PAGE_BYTES,
                        monotonic=monotonic,
                    )
                    values = _strict_json_array(raw)
                    next_page = _pagination_next(response.headers, page=page)
            except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError, transport.EfehrAcquisitionError) as exc:
                raise ExposureTreeProfileError(
                    "exposure subtree acquisition failed closed",
                    failure_class="tree_metadata_acquisition_failure",
                ) from exc

            total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_METADATA_BYTES:
                raise ExposureTreeProfileError("exposure metadata byte bound exceeded")
            for value in values:
                entry = _canonical_entry(value)
                path = entry["path"]
                if path in entries:
                    raise ExposureTreeProfileError("duplicate exposure tree path")
                entries[path] = entry
                if len(entries) > MAX_TREE_ENTRIES:
                    raise ExposureTreeProfileError("exposure tree entry bound exceeded")
            if next_page is None:
                break
            page = next_page
    except ExposureTreeProfileError as exc:
        if exc.failure_class is not None:
            raise
        raise ExposureTreeProfileError(
            str(exc), failure_class="tree_metadata_validation_failure"
        ) from exc

    if not entries:
        raise ExposureTreeProfileError(
            "fixed exposure subtree is empty",
            failure_class="tree_metadata_validation_failure",
        )
    return [entries[path] for path in sorted(entries)], pages_read


def _tree_identity_sha256(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in entries
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _kosovo_named_xml_candidates(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for entry in entries:
        name = entry["name"]
        if (
            entry["type"] == "blob"
            and PROVIDER_KOSOVO_TOKEN in name
            and name.endswith(".xml")
        ):
            candidates.append(
                {
                    "mode": entry["mode"],
                    "object_sha1": entry["id"],
                    "path": entry["path"],
                    "type": "blob",
                }
            )
    candidates.sort(key=lambda item: (item["path"], item["object_sha1"]))
    if not candidates or len(candidates) > MAX_KOSOVO_XML_CANDIDATES:
        raise ExposureTreeProfileError(
            "Kosovo-named exposure XML candidate cardinality is outside policy",
            failure_class="candidate_resolution_failure",
        )
    return candidates


def _profile_v10_tree_for_test(*, opener: Any, monotonic: Any) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    commit_sha, tag_bytes = _resolve_tag_commit(
        opener=opener, monotonic=monotonic, deadline=deadline
    )
    entries, pages_read = _inventory_tree(
        commit_sha,
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        tag_bytes=tag_bytes,
    )
    candidates = _kosovo_named_xml_candidates(entries)
    blob_count = sum(entry["type"] == "blob" for entry in entries)
    tree_count = sum(entry["type"] == "tree" for entry in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": EXPECTED_COMMIT_SHA,
        "subtree_path": SUBTREE_PATH,
        "pages_read": pages_read,
        "entry_count": len(entries),
        "blob_count": blob_count,
        "tree_count": tree_count,
        "tree_identity_sha256": _tree_identity_sha256(entries),
        "kosovo_named_xml_candidates": candidates,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


_RESOLVE_TAG_COMMIT = _resolve_tag_commit
_INVENTORY_TREE = _inventory_tree
_KOSOVO_CANDIDATES = _kosovo_named_xml_candidates
_PROFILE_FOR_TEST = _profile_v10_tree_for_test


def _require_production_authority() -> None:
    exact = (
        (SCHEMA_VERSION, "oc-esrm20-exposure-v10-tree-profile-v1"),
        (SOURCE_ISSUE, 282),
        (DATASET_ID, "efehr.esrm20.risk-inputs.v1.0"),
        (PROJECT_ID, 269),
        (PROJECT_PATH, "efehr/esrm20"),
        (RELEASE_TAG, "v1.0"),
        (EXPECTED_COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783"),
        (SUBTREE_PATH, "Exposure_30arcsec"),
        (PROVIDER_KOSOVO_TOKEN, "Kosovo"),
        (PROVIDER_ROOT, _PROVIDER_ROOT),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ExposureTreeProfileError("trusted exposure-tree target authority drifted")
    authority = (
        (transport._open_fixed, _OPEN_FIXED),
        (transport._read_bounded, _READ_BOUNDED),
        (transport._validate_exact_response, _VALIDATE_RESPONSE),
        (transport._remaining, _REMAINING),
        (transport._header_value, _HEADER_VALUE),
        (transport._strict_json_object, _STRICT_JSON_OBJECT),
        (time.monotonic, _MONOTONIC),
        (urllib.request.Request, _REQUEST),
        (_resolve_tag_commit, _RESOLVE_TAG_COMMIT),
        (_inventory_tree, _INVENTORY_TREE),
        (_kosovo_named_xml_candidates, _KOSOVO_CANDIDATES),
        (_profile_v10_tree_for_test, _PROFILE_FOR_TEST),
    )
    if any(observed is not expected for observed, expected in authority):
        raise ExposureTreeProfileError("trusted exposure-tree execution authority drifted")


def profile_v10_tree() -> dict[str, Any]:
    """Run the zero-argument production profile against the fixed provider target."""
    _require_production_authority()
    return _PROFILE_FOR_TEST(opener=_OPEN_FIXED, monotonic=_MONOTONIC)
