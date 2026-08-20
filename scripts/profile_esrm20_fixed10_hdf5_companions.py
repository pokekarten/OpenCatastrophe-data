# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Reconcile fixed ESRM20 source-model XML paths with same-stem HDF5 tree metadata.

This module reuses the already-reviewed fixed project-269/v1.0 tree profiler and
captures its validated metadata immediately before the legacy template projection.
It never reads provider file payloads. The ten XML paths are imported from the
trusted receipt set; callers cannot select project, ref, root, or paths.

A present GitLab tree object proves only repository-tree existence/identity. It is
not a byte receipt, publication permission, runtime validation, or model-use
authorization.
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Any

from scripts import profile_esrm20_ebrisk_v10_tree as tree_profile
from scripts import profile_esrm20_source_model_children as source_models

SCHEMA_VERSION = "oc-esrm20-fixed10-hdf5-companion-profile-v1"
SOURCE_ISSUE = 281
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
SOURCE_XML_PATHS = tuple(source_models.RECEIPTS)
EXPECTED_SOURCE_COUNT = 10
MAX_TREE_ENTRIES = tree_profile.MAX_ENTRIES
MAX_PATH_UTF8_BYTES = tree_profile.MAX_PATH_UTF8_BYTES

_PROFILE = tree_profile.profile_v10_tree
_TEMPLATE_RESOLVER = tree_profile._exact_template_paths
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}
_ALLOWED_MODES_BY_TYPE = {
    "blob": {"100644", "100755"},
    "tree": {"040000"},
}


class Hdf5CompanionProfileError(RuntimeError):
    """Raised when fixed source-model companion metadata cannot be proven safely."""


class _InventoryComplete(RuntimeError):
    def __init__(self, entries: list[dict[str, str]]) -> None:
        super().__init__("bounded source-model companion inventory captured")
        self.entries = entries


def _canonical_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise Hdf5CompanionProfileError("source-tree entry shape drifted")
    object_id = raw["id"]
    name = raw["name"]
    entry_type = raw["type"]
    path = raw["path"]
    mode = raw["mode"]

    if type(object_id) is not str or len(object_id) != 40:
        raise Hdf5CompanionProfileError("source-tree object id is invalid")
    if any(character not in "0123456789abcdef" for character in object_id):
        raise Hdf5CompanionProfileError("source-tree object id is invalid")
    if type(path) is not str or not path:
        raise Hdf5CompanionProfileError("source-tree path is invalid")
    try:
        encoded = path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Hdf5CompanionProfileError("source-tree path is not UTF-8") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise Hdf5CompanionProfileError("source-tree path exceeds policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise Hdf5CompanionProfileError("source-tree path has control characters")
    if "\\" in path:
        raise Hdf5CompanionProfileError("source-tree path is not canonical relative POSIX")

    parts = path.split("/")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or any(part in ("", ".", "..") for part in parts)
        or str(pure) != path
    ):
        raise Hdf5CompanionProfileError("source-tree path is not canonical relative POSIX")
    if type(name) is not str or not name or pure.name != name:
        raise Hdf5CompanionProfileError("source-tree name/path identity drifted")
    if entry_type not in _ALLOWED_MODES_BY_TYPE:
        raise Hdf5CompanionProfileError("source-tree entry type drifted")
    if type(mode) is not str or mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
        raise Hdf5CompanionProfileError("source-tree type/mode binding drifted")

    return {
        "id": object_id,
        "name": name,
        "type": entry_type,
        "path": path,
        "mode": mode,
    }


def _tree_identity(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in sorted(
            entries,
            key=lambda item: (item["path"], item["type"], item["id"]),
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _companion_identity(entries: list[dict[str, Any]]) -> str:
    canonical = "".join(
        "\t".join(
            (
                item["source_xml_path"],
                item["candidate_hdf5_path"],
                "present" if item["present"] else "absent",
                item["mode"] or "-",
                item["object_sha1"] or "-",
            )
        )
        + "\n"
        for item in entries
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _candidate_path(source_xml_path: str) -> str:
    pure = PurePosixPath(source_xml_path)
    if pure.suffix != ".xml":
        raise Hdf5CompanionProfileError("fixed source-model path is not lowercase XML")
    candidate = str(pure.with_suffix(".hdf5"))
    if candidate == source_xml_path:
        raise Hdf5CompanionProfileError("HDF5 companion derivation did not change suffix")
    return candidate


def summarize_hdf5_companions(entries: object) -> dict[str, Any]:
    """Project validated tree-like metadata onto the ten fixed HDF5 candidates."""
    if type(entries) is not list or not entries:
        raise Hdf5CompanionProfileError("source-tree inventory is empty")
    if len(entries) > MAX_TREE_ENTRIES:
        raise Hdf5CompanionProfileError("source-tree inventory exceeds policy")
    if (
        len(SOURCE_XML_PATHS) != EXPECTED_SOURCE_COUNT
        or len(set(SOURCE_XML_PATHS)) != EXPECTED_SOURCE_COUNT
    ):
        raise Hdf5CompanionProfileError("fixed source-model receipt set drifted")

    canonical: list[dict[str, str]] = []
    by_path: dict[str, dict[str, str]] = {}
    for raw in entries:
        entry = _canonical_entry(raw)
        if entry["path"] in by_path:
            raise Hdf5CompanionProfileError("source-tree paths are not unique")
        by_path[entry["path"]] = entry
        canonical.append(entry)

    companions: list[dict[str, Any]] = []
    present_count = 0
    for source_path in SOURCE_XML_PATHS:
        source_entry = by_path.get(source_path)
        if source_entry is None:
            raise Hdf5CompanionProfileError("fixed source-model XML is absent from source tree")
        if source_entry["type"] != "blob":
            raise Hdf5CompanionProfileError("fixed source-model XML is not a blob")

        candidate = _candidate_path(source_path)
        companion = by_path.get(candidate)
        if companion is not None and companion["type"] != "blob":
            raise Hdf5CompanionProfileError("same-stem HDF5 companion is not a blob")

        present = companion is not None
        present_count += int(present)
        companions.append(
            {
                "source_xml_path": source_path,
                "candidate_hdf5_path": candidate,
                "present": present,
                "mode": companion["mode"] if companion is not None else None,
                "object_sha1": companion["id"] if companion is not None else None,
            }
        )

    return {
        "source_tree_entry_count": len(canonical),
        "source_tree_identity_sha256": _tree_identity(canonical),
        "source_xml_count": EXPECTED_SOURCE_COUNT,
        "candidate_hdf5_count": EXPECTED_SOURCE_COUNT,
        "present_hdf5_count": present_count,
        "absent_hdf5_count": EXPECTED_SOURCE_COUNT - present_count,
        "companion_inventory_sha256": _companion_identity(companions),
        "companions": companions,
        "provider_file_bytes_read": False,
        "hdf5_byte_identity_verified": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _capture_inventory(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    raise _InventoryComplete(entries)


def profile_fixed10_hdf5_companions() -> dict[str, Any]:
    """Run the fixed v1.0 tree acquisition and expose only companion metadata."""
    if tree_profile.profile_v10_tree is not _PROFILE:
        raise Hdf5CompanionProfileError("trusted ebrisk tree profiler authority drifted")
    if tree_profile._exact_template_paths is not _TEMPLATE_RESOLVER:
        raise Hdf5CompanionProfileError("trusted ebrisk template resolver authority drifted")
    if (
        tree_profile.PROJECT_ID != PROJECT_ID
        or tree_profile.PROJECT_PATH != PROJECT_PATH
        or tree_profile.RELEASE_TAG != RELEASE_TAG
        or tree_profile.EXPECTED_COMMIT_SHA != EXPECTED_COMMIT_SHA
        or source_models.PROJECT_ID != PROJECT_ID
        or source_models.PROJECT_PATH != PROJECT_PATH
        or source_models.COMMIT_SHA != EXPECTED_COMMIT_SHA
        or tuple(source_models.RECEIPTS) != SOURCE_XML_PATHS
    ):
        raise Hdf5CompanionProfileError("fixed ESRM20 v1.0 authority drifted")

    tree_profile._exact_template_paths = _capture_inventory
    try:
        try:
            _PROFILE()
        except _InventoryComplete as completed:
            summary = summarize_hdf5_companions(completed.entries)
        except tree_profile.EbriskTreeProfileError as exc:
            raise Hdf5CompanionProfileError(
                "ebrisk tree metadata did not reach HDF5 companion projection"
            ) from exc
        else:
            raise Hdf5CompanionProfileError("HDF5 companion inventory capture was bypassed")
    finally:
        tree_profile._exact_template_paths = _TEMPLATE_RESOLVER

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": EXPECTED_COMMIT_SHA,
        **summary,
    }
