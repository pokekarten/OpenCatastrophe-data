# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compute a deterministic SHA-256 identity for a validated manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from validate_manifest import ManifestError, load_manifest, validate_structure


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    validate_structure(manifest)
    return json.dumps(
        manifest,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def manifest_sha256(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
        digest = manifest_sha256(manifest)
    except (ManifestError, ValueError) as exc:
        print(f"BLOCKED: {exc}")
        return 1

    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
