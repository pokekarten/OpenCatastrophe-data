# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Materialize one already-acquired admitted artifact into a verified local cache.

This utility is deliberately offline. Provider/network acquisition remains owned by the
reviewed source-access and acquisition-receipt lanes. The caller supplies local bytes;
this module validates the existing model-input/manifest binding, verifies exact byte
size and SHA-256, and copies the bytes into a content-addressed cache outside Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

try:
    from scripts import validate_model_input
except ModuleNotFoundError:  # direct script execution
    import validate_model_input  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 1024 * 1024


class MaterializationError(ValueError):
    """Raised when local bytes cannot be safely materialized."""


def _resolved(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except OSError as exc:
        raise MaterializationError(f"cannot resolve path: {exc}") from exc


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_outside_repository(path: Path, *, root: Path, field: str) -> Path:
    resolved_path = _resolved(path)
    resolved_root = _resolved(root)
    if resolved_path == resolved_root or _is_within(resolved_path, resolved_root):
        raise MaterializationError(f"{field} must be outside the repository root")
    return resolved_path


def _require_regular_source(path: Path, *, root: Path) -> Path:
    if path.is_symlink():
        raise MaterializationError("source file must not be a symlink")
    resolved = _require_outside_repository(path, root=root, field="source file")
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise MaterializationError(f"source file is unavailable: {exc}") from exc
    if not stat.S_ISREG(mode):
        raise MaterializationError("source file must be a regular file")
    return resolved


def _prepare_cache_root(cache_root: Path, *, root: Path) -> Path:
    if cache_root.is_symlink():
        raise MaterializationError("cache root must not be a symlink")
    resolved = _require_outside_repository(cache_root, root=root, field="cache root")
    try:
        cache_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise MaterializationError(f"cannot create cache root: {exc}") from exc
    if cache_root.is_symlink() or not cache_root.is_dir():
        raise MaterializationError("cache root must be a real directory")
    if _resolved(cache_root) != resolved:
        raise MaterializationError("cache root changed while being prepared")
    return resolved


def _prepare_cache_parent(cache_root: Path, relative_parent: Path) -> Path:
    """Create a trusted relative directory chain without following cache-internal symlinks."""

    current = cache_root
    for segment in relative_parent.parts:
        if segment in {"", ".", ".."}:
            raise MaterializationError("cache key contains a noncanonical path segment")
        candidate = current / segment
        if candidate.exists() or candidate.is_symlink():
            if candidate.is_symlink():
                raise MaterializationError("cache directory chain must not contain symlinks")
            try:
                mode = candidate.lstat().st_mode
            except OSError as exc:
                raise MaterializationError(f"cannot inspect cache directory chain: {exc}") from exc
            if not stat.S_ISDIR(mode):
                raise MaterializationError("cache directory chain must contain only directories")
        else:
            try:
                candidate.mkdir()
            except OSError as exc:
                raise MaterializationError(f"cannot create cache directory: {exc}") from exc
            if candidate.is_symlink() or not candidate.is_dir():
                raise MaterializationError("created cache directory is not a real directory")
        current = candidate
    return current


def _hash_stream(stream: BinaryIO) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def _hash_file(path: Path) -> tuple[str, int]:
    try:
        with path.open("rb") as stream:
            return _hash_stream(stream)
    except OSError as exc:
        raise MaterializationError(f"cannot read file for verification: {exc}") from exc


def _load_expected_artifact(
    payload: dict[str, Any], *, root: Path
) -> tuple[dict[str, Any], int]:
    try:
        validate_model_input.validate_model_input(payload, root=root)
    except validate_model_input.ModelInputError as exc:
        raise MaterializationError(f"invalid model input: {exc}") from exc

    manifest_path = root / payload["manifest"]
    try:
        manifest = validate_model_input.validate_manifest.load_manifest(manifest_path)
    except validate_model_input.validate_manifest.ManifestError as exc:
        raise MaterializationError(f"referenced manifest is invalid: {exc}") from exc

    artifact = manifest.get(f"{payload['artifact']}_artifact")
    if not isinstance(artifact, dict):
        raise MaterializationError("selected manifest artifact is not identified")
    byte_size = artifact.get("byte_size")
    if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size < 0:
        raise MaterializationError("selected manifest artifact has invalid byte_size")
    return artifact, byte_size


def _existing_destination_matches(
    destination: Path, *, expected_sha256: str, expected_size: int
) -> bool:
    if destination.is_symlink():
        raise MaterializationError("cache destination must not be a symlink")
    try:
        mode = destination.lstat().st_mode
    except OSError as exc:
        raise MaterializationError(f"cannot inspect existing cache destination: {exc}") from exc
    if not stat.S_ISREG(mode):
        raise MaterializationError("cache destination must be a regular file")
    digest, size = _hash_file(destination)
    if digest != expected_sha256 or size != expected_size:
        raise MaterializationError("existing cache destination does not match admitted artifact")
    return True


def _publish_verified_temp(
    temp_path: Path,
    destination: Path,
    *,
    expected_sha256: str,
    expected_size: int,
) -> None:
    """Atomically publish a verified temp file without clobbering concurrent content."""

    try:
        os.link(temp_path, destination)
    except FileExistsError:
        _existing_destination_matches(
            destination,
            expected_sha256=expected_sha256,
            expected_size=expected_size,
        )
    except OSError as exc:
        raise MaterializationError(f"cannot publish verified cache destination: {exc}") from exc


def _copy_and_verify(
    source: Path,
    destination: Path,
    *,
    expected_sha256: str,
    expected_size: int,
) -> None:
    if destination.parent.is_symlink() or not destination.parent.is_dir():
        raise MaterializationError("cache destination parent must be a real directory")

    temp_path: Path | None = None
    try:
        with source.open("rb") as input_stream, tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=".oc-materialize-", delete=False
        ) as output_stream:
            temp_path = Path(output_stream.name)
            digest = hashlib.sha256()
            size = 0
            while True:
                chunk = input_stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                next_size = size + len(chunk)
                if next_size > expected_size:
                    raise MaterializationError(
                        f"source byte size mismatch: expected {expected_size}, got more than {expected_size}"
                    )
                output_stream.write(chunk)
                digest.update(chunk)
                size = next_size
            output_stream.flush()
            os.fsync(output_stream.fileno())

        if size != expected_size:
            raise MaterializationError(
                f"source byte size mismatch: expected {expected_size}, got {size}"
            )
        actual_sha256 = digest.hexdigest()
        if actual_sha256 != expected_sha256:
            raise MaterializationError("source SHA-256 does not match admitted artifact")

        _publish_verified_temp(
            temp_path,
            destination,
            expected_sha256=expected_sha256,
            expected_size=expected_size,
        )
        try:
            temp_path.unlink(missing_ok=True)
        except OSError as exc:
            raise MaterializationError(
                f"cannot remove verified cache temporary alias: {exc}"
            ) from exc
        temp_path = None
    except MaterializationError:
        raise
    except OSError as exc:
        raise MaterializationError(f"cannot materialize artifact: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def materialize(
    model_input_path: Path,
    source_path: Path,
    cache_root: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Validate and copy one exact admitted artifact into an external local cache."""

    try:
        payload = validate_model_input.load_strict_json(model_input_path)
    except validate_model_input.ModelInputError as exc:
        raise MaterializationError(f"invalid model input: {exc}") from exc

    artifact, expected_size = _load_expected_artifact(payload, root=root)
    expected_sha256 = artifact["sha256"]
    if expected_sha256 != payload["sha256"]:
        raise MaterializationError("model-input SHA-256 drifted from selected manifest artifact")

    source = _require_regular_source(source_path, root=root)
    resolved_cache_root = _prepare_cache_root(cache_root, root=root)

    cache_key = Path(payload["dataset_id"]) / payload["artifact"] / expected_sha256
    parent = _prepare_cache_parent(resolved_cache_root, cache_key.parent)
    destination = parent / cache_key.name
    if source == _resolved(destination):
        raise MaterializationError("source file must not already be the cache destination")

    reused = False
    if destination.exists() or destination.is_symlink():
        reused = _existing_destination_matches(
            destination,
            expected_sha256=expected_sha256,
            expected_size=expected_size,
        )
    else:
        _copy_and_verify(
            source,
            destination,
            expected_sha256=expected_sha256,
            expected_size=expected_size,
        )

    return {
        "dataset_id": payload["dataset_id"],
        "artifact": payload["artifact"],
        "storage_reference": payload["storage_reference"],
        "sha256": expected_sha256,
        "byte_size": expected_size,
        "cache_key": cache_key.as_posix(),
        "reused": reused,
        "repository_bytes_persisted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify already-acquired admitted bytes into an external local cache."
    )
    parser.add_argument("model_input", type=Path)
    parser.add_argument("source_file", type=Path)
    parser.add_argument("cache_root", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    try:
        receipt = materialize(
            args.model_input,
            args.source_file,
            args.cache_root,
            root=args.root,
        )
    except MaterializationError as exc:
        print(f"BLOCKED: {exc}")
        return 1

    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
