# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify the receipted ESHM20 root bytes before offline dependency parsing.

This module performs no network access and persists no provider payload. It is
an explicit bridge between the trusted byte receipt under #281 and the already
merged fail-closed OpenQuake configuration parser.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.openquake_config_dependencies import (
        OpenQuakeConfigError,
        extract_openquake_config_references,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from openquake_config_dependencies import (
        OpenQuakeConfigError,
        extract_openquake_config_references,
    )

SCHEMA_VERSION = "oc-eshm20-root-dependency-bridge-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "config_eshm20_v12e_main_region.ini"
)
EXPECTED_BYTE_COUNT = 2719
EXPECTED_SHA256 = "f1f4dabc48e1b8a478dbdb96b01c8f58cc68c98abd6f9004671c5fba9eb7e714"
PARSER_ID = "scripts.openquake_config_dependencies.extract_openquake_config_references"


class VerifiedRootConfigError(ValueError):
    """Raised when root bytes cannot be proven identical to the trusted receipt."""


def _verify_payload_identity(
    payload: bytes,
    *,
    expected_byte_count: int = EXPECTED_BYTE_COUNT,
    expected_sha256: str = EXPECTED_SHA256,
) -> str:
    """Recompute and verify byte identity before any decoding or parsing."""

    if type(payload) is not bytes:
        raise VerifiedRootConfigError("root payload must be immutable bytes")
    if type(expected_byte_count) is not int or expected_byte_count < 1:
        raise VerifiedRootConfigError("expected_byte_count must be a positive integer")
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(char not in "0123456789abcdef" for char in expected_sha256)
    ):
        raise VerifiedRootConfigError("expected_sha256 must be a lowercase SHA-256 digest")

    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if len(payload) != expected_byte_count:
        raise VerifiedRootConfigError(
            f"root byte count mismatch: observed {len(payload)}, expected {expected_byte_count}"
        )
    if observed_sha256 != expected_sha256:
        raise VerifiedRootConfigError(
            f"root SHA-256 mismatch: observed {observed_sha256}, expected {expected_sha256}"
        )
    return observed_sha256


def extract_verified_root_dependencies(
    payload: bytes,
    *,
    expected_byte_count: int = EXPECTED_BYTE_COUNT,
    expected_sha256: str = EXPECTED_SHA256,
) -> dict[str, Any]:
    """Return derived dependency metadata only after exact byte verification."""

    observed_sha256 = _verify_payload_identity(
        payload,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    try:
        config_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerifiedRootConfigError("verified root payload is not strict UTF-8") from exc

    try:
        references = extract_openquake_config_references(
            config_text,
            config_path=REPOSITORY_PATH,
        )
    except OpenQuakeConfigError as exc:
        raise VerifiedRootConfigError(f"verified root dependency parse failed: {exc}") from exc

    dependencies = [
        {
            "section": reference.section,
            "option": reference.option,
            "raw_path": reference.raw_path,
            "resolved_path": reference.resolved_path,
        }
        for reference in references
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "parser": PARSER_ID,
        "dependencies": dependencies,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _read_regular_file(path: Path) -> bytes:
    """Read one local regular file without following a symlink."""

    try:
        info = path.lstat()
    except OSError as exc:
        raise VerifiedRootConfigError(f"cannot stat root payload: {type(exc).__name__}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise VerifiedRootConfigError("root payload path must be a non-symlink regular file")
    if info.st_size != EXPECTED_BYTE_COUNT:
        raise VerifiedRootConfigError(
            f"root byte count mismatch: observed {info.st_size}, expected {EXPECTED_BYTE_COUNT}"
        )
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise VerifiedRootConfigError(f"cannot read root payload: {type(exc).__name__}") from exc
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Local materialized ESHM20 root INI")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = _read_regular_file(Path(args.input))
        result = extract_verified_root_dependencies(payload)
    except VerifiedRootConfigError as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
