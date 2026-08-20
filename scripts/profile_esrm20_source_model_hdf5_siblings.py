# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Metadata-only sibling predicates for the ten frozen ESRM20 source-model XML files.

OpenQuake can resolve a same-stem ``.hdf5`` companion for some source-model XML
inputs.  This profiler answers only that fixed question for the ten exact #481
source-model receipts.  It reuses the immutable ESRM20-v1.0 GitLab tree-metadata
transport/validation primitive and never requests provider file payload bytes.

A complete tree scan can prove whether each exact same-stem path is present or
absent at the frozen commit.  It does not prove transitive dependency closure,
runtime compatibility, publication authority, model-use fitness, or that any
present HDF5 object is scientifically suitable for a particular calculation.
"""

from __future__ import annotations

import time
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from scripts import profile_esrm20_ebrisk_v10_tree as tree
from scripts import profile_esrm20_source_model_children as source_models
from scripts import acquire_efehr_gitlab_receipt as transport

SCHEMA_VERSION = "oc-esrm20-source-model-hdf5-siblings-v1"
SOURCE_ISSUE = 281
CONSUMER_ISSUE = 287
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
SOURCE_RECEIPT_SET_SHA256 = "621d16b35166cb66c86079106f1a7fd717ff07ef155184c5eed5a028292e4eb8"
EXPECTED_SOURCE_COUNT = 10
TOTAL_DEADLINE_SECONDS = tree.TOTAL_DEADLINE_SECONDS

_FIXED_RECEIPTS = dict(source_models.RECEIPTS)
_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic


class SourceModelHdf5SiblingProfileError(RuntimeError):
    """Fail-closed error for fixed source-model HDF5 sibling metadata."""

    def __init__(self, message: str, *, failure_class: str | None = None) -> None:
        super().__init__(message)
        if failure_class is not None and failure_class not in tree.FAILURE_CLASSES:
            raise ValueError("invalid HDF5 sibling failure class")
        self.failure_class = failure_class


def _assert_fixed_contract() -> None:
    exact = (
        ("source project id", source_models.PROJECT_ID, PROJECT_ID),
        ("source project path", source_models.PROJECT_PATH, PROJECT_PATH),
        ("source commit", source_models.COMMIT_SHA, COMMIT_SHA),
        ("tree project id", tree.PROJECT_ID, PROJECT_ID),
        ("tree project path", tree.PROJECT_PATH, PROJECT_PATH),
        ("tree commit", tree.EXPECTED_COMMIT_SHA, COMMIT_SHA),
    )
    for label, observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelHdf5SiblingProfileError(f"{label} drifted")
    if source_models.RECEIPTS != _FIXED_RECEIPTS:
        raise SourceModelHdf5SiblingProfileError("fixed source-model receipt set drifted")
    if len(_FIXED_RECEIPTS) != EXPECTED_SOURCE_COUNT:
        raise SourceModelHdf5SiblingProfileError("fixed source-model receipt count drifted")


def _fixed_targets() -> tuple[tuple[str, str], ...]:
    targets: list[tuple[str, str]] = []
    seen: set[str] = set()
    for source_path in _FIXED_RECEIPTS:
        pure = PurePosixPath(source_path)
        if pure.suffix != ".xml":
            raise SourceModelHdf5SiblingProfileError("fixed source-model path is not XML")
        sibling = str(pure.with_suffix(".hdf5"))
        if sibling in seen:
            raise SourceModelHdf5SiblingProfileError("fixed HDF5 sibling targets are not unique")
        seen.add(sibling)
        targets.append((source_path, sibling))
    if len(targets) != EXPECTED_SOURCE_COUNT:
        raise SourceModelHdf5SiblingProfileError("fixed HDF5 sibling target count drifted")
    return tuple(targets)


def _profile_from_inventory(
    entries: list[dict[str, str]], *, pages_read: int, commit_sha: str
) -> dict[str, Any]:
    if commit_sha != COMMIT_SHA:
        raise SourceModelHdf5SiblingProfileError("HDF5 sibling inventory commit drifted")
    if type(pages_read) is not int or isinstance(pages_read, bool) or not (1 <= pages_read <= tree.MAX_PAGES):
        raise SourceModelHdf5SiblingProfileError("HDF5 sibling page count is invalid")
    if not entries or len(entries) > tree.MAX_ENTRIES:
        raise SourceModelHdf5SiblingProfileError("HDF5 sibling inventory size is invalid")

    targets = _fixed_targets()
    target_paths = {sibling for _, sibling in targets}
    matched: dict[str, dict[str, str]] = {}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"id", "name", "type", "path", "mode"}:
            raise SourceModelHdf5SiblingProfileError("HDF5 sibling inventory entry shape drifted")
        path = entry["path"]
        if path not in target_paths:
            continue
        if path in matched:
            raise SourceModelHdf5SiblingProfileError("HDF5 sibling path resolved more than once")
        if entry["type"] != "blob":
            raise SourceModelHdf5SiblingProfileError("HDF5 sibling path is not a blob")
        matched[path] = entry

    predicates: list[dict[str, Any]] = []
    for source_path, sibling_path in targets:
        entry = matched.get(sibling_path)
        predicates.append(
            {
                "source_xml_path": source_path,
                "hdf5_sibling_path": sibling_path,
                "present": entry is not None,
                "object_sha1": entry["id"] if entry is not None else None,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "consumer_issue": CONSUMER_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "source_receipt_set_sha256": SOURCE_RECEIPT_SET_SHA256,
        "source_model_count": EXPECTED_SOURCE_COUNT,
        "pages_read": pages_read,
        "entry_count": len(entries),
        "tree_identity_sha256": tree._inventory_sha256(entries),
        "hdf5_sibling_predicates": predicates,
        "hdf5_sibling_metadata_verified": True,
        "all_hdf5_siblings_present": all(item["present"] for item in predicates),
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_fixed_hdf5_siblings(
    *, opener: Any | None = None, monotonic: Any | None = None
) -> dict[str, Any]:
    """Scan frozen project-269 tree metadata and resolve only the ten fixed siblings."""
    _assert_fixed_contract()
    if transport._open_fixed is not _OPEN_FIXED or transport._read_bounded is not _READ_BOUNDED:
        raise SourceModelHdf5SiblingProfileError("trusted EFEHR transport authority drifted")
    if transport._validate_exact_response is not _VALIDATE_RESPONSE:
        raise SourceModelHdf5SiblingProfileError("trusted EFEHR response authority drifted")
    if transport._remaining is not _REMAINING or time.monotonic is not _MONOTONIC:
        raise SourceModelHdf5SiblingProfileError("trusted deadline authority drifted")

    clock = monotonic or _MONOTONIC
    open_response = opener or _OPEN_FIXED
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    try:
        commit_sha = tree._resolve_tag_commit(
            opener=open_response, deadline=deadline, monotonic=clock
        )
    except tree.EbriskTreeProfileError as exc:
        raise SourceModelHdf5SiblingProfileError(
            str(exc), failure_class=exc.failure_class
        ) from exc

    entries: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    page = 1
    pages_read = 0
    while True:
        url = tree._tree_url(commit_sha, page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-ESRM20-fixed10-HDF5-siblings-v1",
            },
            method="GET",
        )
        try:
            with open_response(request, timeout=_REMAINING(deadline, clock)) as response:
                _VALIDATE_RESPONSE(response, url)
                raw = _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=tree.MAX_PAGE_BYTES,
                    monotonic=clock,
                )
                raw_page = tree._strict_json(raw)
                if type(raw_page) is not list:
                    raise tree.EbriskTreeProfileError("HDF5 sibling tree response is not an array")
                for raw_entry in raw_page:
                    entry = tree._validate_entry(raw_entry)
                    if entry["path"] in seen_paths:
                        raise tree.EbriskTreeProfileError("HDF5 sibling tree contains duplicate paths")
                    seen_paths.add(entry["path"])
                    entries.append(entry)
                    if len(entries) > tree.MAX_ENTRIES:
                        raise tree.EbriskTreeProfileError("HDF5 sibling tree exceeds entry policy")
                next_page = tree._pagination_next(response.headers, expected_page=page)
        except tree.EbriskTreeProfileError as exc:
            failure_class = exc.failure_class or "tree_metadata_validation_failure"
            raise SourceModelHdf5SiblingProfileError(
                str(exc), failure_class=failure_class
            ) from exc
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise SourceModelHdf5SiblingProfileError(
                "HDF5 sibling tree metadata acquisition failed closed",
                failure_class="tree_metadata_acquisition_failure",
            ) from exc
        pages_read += 1
        if next_page is None:
            break
        page = next_page

    return _profile_from_inventory(entries, pages_read=pages_read, commit_sha=commit_sha)
