# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only inventory of ESRM20 v1.0 configuration INI blobs.

The trusted wrapper reuses the already-reviewed fixed project-269/v1.0 tree
profiler and intercepts only its validated tree metadata immediately before the
legacy exact-basename resolver.  No provider file payload, archive, raw URL, or
caller-selected provider target is read.

The generic summarizer is deliberately provider-identity-neutral so synthetic
metadata used by tests cannot self-attest the real ESRM20 repository identity.
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Any

from scripts import profile_esrm20_ebrisk_v10_tree as tree_profile

SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-ini-inventory-profile-v1"
SOURCE_ISSUE = 281
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONFIGURATION_ROOT = "Configuration_files"
INI_SUFFIX = ".ini"
MAX_INI_BLOBS = 512
MAX_PATH_UTF8_BYTES = 2048

_PROFILE = tree_profile.profile_v10_tree
_TEMPLATE_RESOLVER = tree_profile._exact_template_paths
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}
_ALLOWED_MODES_BY_TYPE = {
    "blob": {"100644", "100755"},
    "tree": {"040000"},
}


class EbriskIniInventoryError(RuntimeError):
    """Raised when the fixed configuration metadata cannot be proven safely."""


class _InventoryComplete(RuntimeError):
    def __init__(self, entries: list[dict[str, str]]) -> None:
        super().__init__("bounded configuration INI inventory captured")
        self.entries = entries


def _canonical_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise EbriskIniInventoryError("configuration tree entry shape drifted")
    object_id = raw["id"]
    name = raw["name"]
    entry_type = raw["type"]
    path = raw["path"]
    mode = raw["mode"]
    if type(object_id) is not str or len(object_id) != 40:
        raise EbriskIniInventoryError("configuration tree object id is invalid")
    if any(character not in "0123456789abcdef" for character in object_id):
        raise EbriskIniInventoryError("configuration tree object id is invalid")
    if type(name) is not str or not name:
        raise EbriskIniInventoryError("configuration tree basename is invalid")
    if type(path) is not str or not path:
        raise EbriskIniInventoryError("configuration tree path is invalid")
    try:
        encoded = path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise EbriskIniInventoryError("configuration tree path is not UTF-8") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise EbriskIniInventoryError("configuration tree path exceeds policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise EbriskIniInventoryError("configuration tree path has control characters")
    if "\\" in path:
        raise EbriskIniInventoryError(
            "configuration tree path is not canonical relative POSIX"
        )
    parts = path.split("/")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or any(part in ("", ".", "..") for part in parts)
        or str(pure) != path
    ):
        raise EbriskIniInventoryError(
            "configuration tree path is not canonical relative POSIX"
        )
    if pure.name != name:
        raise EbriskIniInventoryError("configuration tree name/path identity drifted")
    if entry_type not in _ALLOWED_MODES_BY_TYPE:
        raise EbriskIniInventoryError("configuration tree entry type drifted")
    if type(mode) is not str or mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
        raise EbriskIniInventoryError("configuration tree type/mode binding drifted")
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


def _ini_identity(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['mode']}\t{entry['object_sha1']}\t{entry['path']}\n"
        for entry in entries
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def summarize_ini_inventory(entries: object) -> dict[str, Any]:
    """Summarize validated tree-like metadata without provider identity labels."""
    if type(entries) is not list or not entries:
        raise EbriskIniInventoryError("configuration tree inventory is empty")

    canonical: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for raw in entries:
        entry = _canonical_entry(raw)
        if entry["path"] in seen_paths:
            raise EbriskIniInventoryError("configuration tree paths are not unique")
        seen_paths.add(entry["path"])
        canonical.append(entry)

    root_entries = [entry for entry in canonical if entry["path"] == CONFIGURATION_ROOT]
    if len(root_entries) != 1:
        raise EbriskIniInventoryError(
            "exact Configuration_files root does not resolve to one tree entry"
        )
    root_entry = root_entries[0]
    if root_entry["type"] != "tree" or root_entry["mode"] != "040000":
        raise EbriskIniInventoryError("Configuration_files root is not a canonical tree")

    ini_entries: list[dict[str, str]] = []
    root_prefix = CONFIGURATION_ROOT + "/"
    for entry in canonical:
        path = entry["path"]
        if not path.startswith(root_prefix):
            continue
        if not entry["name"].endswith(INI_SUFFIX):
            continue
        if entry["type"] != "blob":
            raise EbriskIniInventoryError("configuration INI entry is not a blob")
        ini_entries.append(
            {
                "basename": entry["name"],
                "path": path,
                "mode": entry["mode"],
                "object_sha1": entry["id"],
            }
        )
        if len(ini_entries) > MAX_INI_BLOBS:
            raise EbriskIniInventoryError("configuration INI inventory exceeds policy")

    ini_entries.sort(
        key=lambda item: (item["path"], item["mode"], item["object_sha1"])
    )
    return {
        "configuration_root": CONFIGURATION_ROOT,
        "tree_entry_count": len(canonical),
        "source_tree_identity_sha256": _tree_identity(canonical),
        "ini_blob_count": len(ini_entries),
        "ini_inventory_sha256": _ini_identity(ini_entries),
        "ini_blobs": ini_entries,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _capture_inventory(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    raise _InventoryComplete(entries)


def profile_v10_ini_inventory() -> dict[str, Any]:
    """Run the fixed v1.0 tree acquisition and expose bounded INI metadata only."""
    if tree_profile.profile_v10_tree is not _PROFILE:
        raise EbriskIniInventoryError("trusted ebrisk tree profiler authority drifted")
    if tree_profile._exact_template_paths is not _TEMPLATE_RESOLVER:
        raise EbriskIniInventoryError("trusted ebrisk template resolver authority drifted")
    if (
        tree_profile.PROJECT_ID != PROJECT_ID
        or tree_profile.PROJECT_PATH != PROJECT_PATH
        or tree_profile.RELEASE_TAG != RELEASE_TAG
        or tree_profile.EXPECTED_COMMIT_SHA != EXPECTED_COMMIT_SHA
    ):
        raise EbriskIniInventoryError("fixed ebrisk v1.0 authority drifted")

    tree_profile._exact_template_paths = _capture_inventory
    try:
        try:
            _PROFILE()
        except _InventoryComplete as completed:
            summary = summarize_ini_inventory(completed.entries)
        except tree_profile.EbriskTreeProfileError as exc:
            raise EbriskIniInventoryError(
                "ebrisk tree metadata did not reach INI inventory projection"
            ) from exc
        else:
            raise EbriskIniInventoryError("INI inventory capture was bypassed")
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
