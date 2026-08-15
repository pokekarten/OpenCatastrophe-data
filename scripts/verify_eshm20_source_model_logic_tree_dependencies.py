# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify receipted ESHM20 source-model logic-tree bytes before parsing.

The canonical trusted-main receipt already binds the exact source-model logic-tree
byte identity. This bridge verifies those bytes before UTF-8 decoding, delegates
source-file discovery to the existing reviewed OpenQuake logic-tree parser, and
emits only bounded derived dependency metadata. Inventory membership is metadata
authority only and never substitutes for a byte receipt of a referenced file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.openquake_source_model_logic_tree_dependencies import (
        OpenQuakeLogicTreeError,
        extract_source_model_logic_tree_dependencies,
    )
    from scripts.verify_eshm20_root_config_dependencies import (
        FROZEN_INVENTORY_PATHS,
        INVENTORY_RECEIPT_COMMENT_ID,
        PREFIX,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from openquake_source_model_logic_tree_dependencies import (  # type: ignore[no-redef]
        OpenQuakeLogicTreeError,
        extract_source_model_logic_tree_dependencies,
    )
    from verify_eshm20_root_config_dependencies import (  # type: ignore[no-redef]
        FROZEN_INVENTORY_PATHS,
        INVENTORY_RECEIPT_COMMENT_ID,
        PREFIX,
    )

SCHEMA_VERSION = "oc-eshm20-source-model-dependency-bridge-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 361
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = PREFIX + "source_model_logic_tree_eshm20_model_v12e.xml"
EXPECTED_BYTE_COUNT = 17579
EXPECTED_SHA256 = "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867"
RECEIPT_COMMENT_ID = 5301858821
RECEIPT_RUN_ID = 31880089623
RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
SELECTION_RESULT_COMMENT_ID = 5301726249
PARSER_ID = (
    "scripts.openquake_source_model_logic_tree_dependencies."
    "extract_source_model_logic_tree_dependencies"
)
FROZEN_INVENTORY_COUNT = 62


class VerifiedSourceModelLogicTreeError(ValueError):
    """Raised when source-model logic-tree bytes or dependencies violate evidence."""


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise VerifiedSourceModelLogicTreeError(
            "source-model logic-tree payload must be immutable bytes"
        )
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise VerifiedSourceModelLogicTreeError(
            "source-model logic-tree byte count mismatch: "
            f"observed {len(payload)}, expected {EXPECTED_BYTE_COUNT}"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != EXPECTED_SHA256:
        raise VerifiedSourceModelLogicTreeError("source-model logic-tree SHA-256 mismatch")
    return observed_sha256


def extract_verified_source_model_dependencies(payload: bytes) -> dict[str, Any]:
    """Verify the frozen logic-tree bytes and emit only source-derived paths."""

    observed_sha256 = _verify_payload_identity(payload)
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerifiedSourceModelLogicTreeError(
            "verified source-model logic-tree payload is not strict UTF-8"
        ) from exc

    if len(FROZEN_INVENTORY_PATHS) != FROZEN_INVENTORY_COUNT:
        raise VerifiedSourceModelLogicTreeError(
            "frozen ESHM20 inventory identity is invalid"
        )

    try:
        references = extract_source_model_logic_tree_dependencies(
            xml_text,
            logic_tree_path=REPOSITORY_PATH,
            repository_inventory=FROZEN_INVENTORY_PATHS,
        )
    except OpenQuakeLogicTreeError as exc:
        raise VerifiedSourceModelLogicTreeError(
            f"verified source-model logic-tree dependency parse failed: {exc}"
        ) from exc

    if any(reference.resolved_path not in FROZEN_INVENTORY_PATHS for reference in references):
        raise VerifiedSourceModelLogicTreeError(
            "verified source-model dependency is absent from frozen inventory"
        )

    dependencies = [
        {
            "resolved_path": reference.resolved_path,
            "is_hdf5_companion": reference.is_hdf5_companion,
            "origins": [
                {
                    "uncertainty_type": origin.uncertainty_type,
                    "branch_id": origin.branch_id,
                }
                for origin in reference.origins
            ],
        }
        for reference in references
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_run_id": RECEIPT_RUN_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "selection_result_comment_id": SELECTION_RESULT_COMMENT_ID,
        "inventory_receipt_comment_id": INVENTORY_RECEIPT_COMMENT_ID,
        "parser": PARSER_ID,
        "dependencies": dependencies,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _file_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _read_regular_file(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise VerifiedSourceModelLogicTreeError(
            f"cannot stat source-model logic-tree payload: {type(exc).__name__}"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise VerifiedSourceModelLogicTreeError(
            "source-model logic-tree payload path must be a non-symlink regular file"
        )
    if before.st_size != EXPECTED_BYTE_COUNT:
        raise VerifiedSourceModelLogicTreeError(
            "source-model logic-tree byte count mismatch: "
            f"observed {before.st_size}, expected {EXPECTED_BYTE_COUNT}"
        )

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise VerifiedSourceModelLogicTreeError(
            f"cannot open source-model logic-tree payload: {type(exc).__name__}"
        ) from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _file_identity(opened) != _file_identity(before):
            raise VerifiedSourceModelLogicTreeError(
                "source-model logic-tree payload identity changed before read"
            )
        chunks: list[bytes] = []
        remaining = EXPECTED_BYTE_COUNT + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if _file_identity(after) != _file_identity(opened):
            raise VerifiedSourceModelLogicTreeError(
                "source-model logic-tree payload identity changed during read"
            )
    except OSError as exc:
        raise VerifiedSourceModelLogicTreeError(
            f"cannot read source-model logic-tree payload: {type(exc).__name__}"
        ) from exc
    finally:
        os.close(fd)

    payload = b"".join(chunks)
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise VerifiedSourceModelLogicTreeError(
            "source-model logic-tree byte count mismatch: "
            f"observed {len(payload)}, expected {EXPECTED_BYTE_COUNT}"
        )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Local materialized ESHM20 source-model logic-tree XML",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = extract_verified_source_model_dependencies(
            _read_regular_file(Path(args.input))
        )
    except VerifiedSourceModelLogicTreeError as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())