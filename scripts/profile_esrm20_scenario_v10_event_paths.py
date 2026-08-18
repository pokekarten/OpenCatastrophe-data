# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only resolver for one ESRM20 v1.0 scenario identifier.

The identifier is frozen from the trusted provider-authored v1.0 summary CSVs.
This profiler reuses the existing fixed project-273/v1.0 tree acquisition and
publishes only matching Git tree metadata below ``ruptures/`` and
``shakemaps/``. It never reads provider file payloads.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from typing import Any

from scripts import acquire_efehr_esrm20_scenario_tree_metadata as tree

SCHEMA_VERSION = "oc-esrm20-scenario-v10-event-paths-profile-v1"
SOURCE_ISSUE = 285
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
TARGET_EVENT_ID = "Greece_07-9-1999"
ALLOWED_ROOTS = ("ruptures", "shakemaps")
MAX_MATCHES = 128
MAX_PATH_UTF8_BYTES = 2048

_TREE_ACQUIRE = tree.acquire_esrm20_scenario_tree_metadata
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_MODES_BY_TYPE = {
    "blob": {"100644", "100755"},
    "tree": {"040000"},
}


class ScenarioEventPathProfileError(RuntimeError):
    """Raised when the fixed event-to-tree relation cannot be proven safely."""


def _bounded_path(value: object) -> str:
    if type(value) is not str or not value:
        raise ScenarioEventPathProfileError("scenario tree path is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioEventPathProfileError(
            "scenario tree path is not UTF-8 encodable"
        ) from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise ScenarioEventPathProfileError("scenario tree path exceeds policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ScenarioEventPathProfileError(
            "scenario tree path contains control characters"
        )
    if "\\" in value:
        raise ScenarioEventPathProfileError(
            "scenario tree path is not canonical relative POSIX"
        )
    parts = value.split("/")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or any(part in ("", ".", "..") for part in parts)
        or str(pure) != value
    ):
        raise ScenarioEventPathProfileError(
            "scenario tree path is not canonical relative POSIX"
        )
    return value


def _validated_inventory(value: object) -> list[dict[str, str]]:
    if type(value) is not dict:
        raise ScenarioEventPathProfileError("scenario tree receipt is not an object")
    exact = (
        ("schema_version", tree.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("release_tag", RELEASE_TAG),
        ("resolved_commit_sha", EXPECTED_COMMIT_SHA),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioEventPathProfileError(
                f"scenario tree receipt drifted at {field}"
            )

    entries = value.get("entries")
    if type(entries) is not list or not entries:
        raise ScenarioEventPathProfileError("scenario tree receipt has no entries")
    expected_count = value.get("tree_entry_count")
    if (
        type(expected_count) is not int
        or isinstance(expected_count, bool)
        or expected_count != len(entries)
    ):
        raise ScenarioEventPathProfileError(
            "scenario tree receipt entry count disagrees"
        )

    canonical: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for raw in entries:
        if type(raw) is not dict or set(raw) != {"path", "type", "id", "mode"}:
            raise ScenarioEventPathProfileError("scenario tree entry shape drifted")
        path = _bounded_path(raw["path"])
        if path in seen_paths:
            raise ScenarioEventPathProfileError("scenario tree paths are not unique")
        seen_paths.add(path)
        entry_type = raw["type"]
        object_id = raw["id"]
        mode = raw["mode"]
        if entry_type not in _ALLOWED_MODES_BY_TYPE:
            raise ScenarioEventPathProfileError("scenario tree entry type drifted")
        if type(object_id) is not str or _SHA1_RE.fullmatch(object_id) is None:
            raise ScenarioEventPathProfileError(
                "scenario tree object identity is invalid"
            )
        if type(mode) is not str or mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
            raise ScenarioEventPathProfileError(
                "scenario tree type/mode binding drifted"
            )
        canonical.append(
            {"path": path, "type": entry_type, "id": object_id, "mode": mode}
        )
    return canonical


def _tree_identity(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in sorted(
            entries, key=lambda item: (item["path"], item["type"], item["id"])
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _relation_identity(matches: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{item['root']}\t{item['object_sha1']}\t{item['path']}\n"
        for item in matches
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _event_matches(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    root_counts = {root: 0 for root in ALLOWED_ROOTS}
    for entry in entries:
        path = entry["path"]
        if TARGET_EVENT_ID not in path:
            continue
        root = path.split("/", 1)[0]
        if root not in ALLOWED_ROOTS:
            raise ScenarioEventPathProfileError(
                "event identifier appears outside fixed scenario roots"
            )
        if entry["type"] == "tree":
            continue
        if entry["type"] != "blob":
            raise ScenarioEventPathProfileError(
                "matched scenario dependency is not a blob"
            )
        matches.append(
            {
                "root": root,
                "path": path,
                "object_sha1": entry["id"],
            }
        )
        root_counts[root] += 1
        if len(matches) > MAX_MATCHES:
            raise ScenarioEventPathProfileError(
                "scenario event relation exceeds bounded policy"
            )

    matches.sort(key=lambda item: (item["root"], item["path"], item["object_sha1"]))
    identities = {(item["root"], item["path"], item["object_sha1"]) for item in matches}
    if len(identities) != len(matches):
        raise ScenarioEventPathProfileError(
            "scenario event relation contains duplicates"
        )
    if not matches or any(root_counts[root] < 1 for root in ALLOWED_ROOTS):
        raise ScenarioEventPathProfileError(
            "scenario event relation does not cover both fixed roots"
        )
    return matches


def profile_event_paths(*, acquire: Any | None = None) -> dict[str, Any]:
    """Resolve the fixed source-derived identifier to bounded tree metadata."""
    if tree.acquire_esrm20_scenario_tree_metadata is not _TREE_ACQUIRE:
        raise ScenarioEventPathProfileError(
            "trusted scenario tree acquisition authority drifted"
        )
    acquire_tree = acquire or _TREE_ACQUIRE
    try:
        receipt = acquire_tree()
    except tree.EfehrAcquisitionError as exc:
        raise ScenarioEventPathProfileError(
            "scenario tree acquisition failed closed"
        ) from exc

    entries = _validated_inventory(receipt)
    matches = _event_matches(entries)
    root_blob_counts = {
        root: sum(item["root"] == root for item in matches)
        for root in ALLOWED_ROOTS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": EXPECTED_COMMIT_SHA,
        "target_event_id": TARGET_EVENT_ID,
        "tree_entry_count": len(entries),
        "tree_identity_sha256": _tree_identity(entries),
        "matched_blob_count": len(matches),
        "root_blob_counts": root_blob_counts,
        "matches": matches,
        "relation_sha256": _relation_identity(matches),
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
