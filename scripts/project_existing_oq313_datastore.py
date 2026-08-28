# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Project an existing completed OpenQuake 3.13 datastore without rerunning it.

This is a local/offline recovery path for an already-computed ``calc_*.hdf5``.
It never starts OpenQuake and never acquires provider bytes. The existing reviewed
EQ1 datastore selector remains the numerical authority.

The public summary binds the datastore bytes and either embeds the validated
canonical numerical receipt or, when that receipt exceeds the repository's
publication budget, emits the same bounded commitment used by the trusted action.
The full canonical receipt may optionally be written to a new local file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action

SCHEMA_VERSION = "oc-oq313-existing-datastore-projection-v1"
_CALC_DATASTORE_RE = re.compile(r"^calc_[0-9]+\.hdf5$")
_BUFFER_SIZE = 1024 * 1024


class ExistingOQ313DatastoreProjectionError(RuntimeError):
    """The supplied existing datastore cannot produce a bounded EQ1 receipt."""


def _stable_stat(path: Path) -> tuple[int, int]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ExistingOQ313DatastoreProjectionError("cannot stat datastore") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ExistingOQ313DatastoreProjectionError(
            "datastore must be one regular non-symlink file"
        )
    if _CALC_DATASTORE_RE.fullmatch(path.name) is None:
        raise ExistingOQ313DatastoreProjectionError(
            "datastore filename must match calc_<integer>.hdf5"
        )
    if info.st_size <= 0:
        raise ExistingOQ313DatastoreProjectionError("datastore must be non-empty")
    return info.st_size, info.st_mtime_ns


def _hash_file(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_BUFFER_SIZE)
                if not chunk:
                    break
                byte_count += len(chunk)
                digest.update(chunk)
    except OSError as exc:
        raise ExistingOQ313DatastoreProjectionError("cannot hash datastore") from exc
    return {"byte_count": byte_count, "sha256": digest.hexdigest()}


def _write_new_file(path: Path, payload: bytes) -> None:
    if type(payload) is not bytes or not payload:
        raise ExistingOQ313DatastoreProjectionError(
            "full numerical receipt must be non-empty bytes"
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise ExistingOQ313DatastoreProjectionError(
            "cannot create full numerical receipt output"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise ExistingOQ313DatastoreProjectionError(
            "cannot write full numerical receipt output"
        ) from exc


def _validate_projected_receipt(
    payload: object,
    identity: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(payload) is not bytes or not payload:
        raise ExistingOQ313DatastoreProjectionError(
            "datastore projector returned invalid payload"
        )
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt is not UTF-8"
        ) from exc
    try:
        document = action._load_json_text(text, label="projected numerical receipt")
    except action.KosovoResidentialOQ313ActionError as exc:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt JSON is invalid"
        ) from exc
    if type(document) is not dict:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt must be an object"
        )
    runtime = document.get("runtime")
    if type(runtime) is not dict:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt runtime is missing"
        )
    concurrent_tasks = runtime.get("concurrent_tasks")
    if type(concurrent_tasks) is not int or concurrent_tasks < 0:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt concurrent_tasks drifted"
        )
    try:
        return action._validate_numerical_receipt(
            payload,
            identity,
            expected_concurrent_tasks=concurrent_tasks,
        )
    except action.KosovoResidentialOQ313ActionError as exc:
        raise ExistingOQ313DatastoreProjectionError(
            "projected numerical receipt failed current validation"
        ) from exc


def project_existing_datastore(
    path: Path,
    *,
    full_receipt_out: Path | None = None,
    project_datastore: Callable[[Path], tuple[bytes, dict[str, Any]]] = action._project_exact_datastore,
) -> dict[str, Any]:
    """Return a bounded identity/receipt summary for one completed local datastore."""

    if not isinstance(path, Path):
        raise ExistingOQ313DatastoreProjectionError("datastore path must be a Path")
    before = _stable_stat(path)
    try:
        payload, identity = project_datastore(path)
    except action.KosovoResidentialOQ313ActionError as exc:
        raise ExistingOQ313DatastoreProjectionError(
            "existing datastore failed current EQ1 projection"
        ) from exc
    after_projection = _stable_stat(path)
    if after_projection != before:
        raise ExistingOQ313DatastoreProjectionError(
            "datastore changed while numerical receipt was projected"
        )

    document, validated_identity = _validate_projected_receipt(payload, identity)
    datastore_identity = _hash_file(path)
    after_hash = _stable_stat(path)
    if after_hash != before or datastore_identity["byte_count"] != before[0]:
        raise ExistingOQ313DatastoreProjectionError(
            "datastore changed while byte identity was computed"
        )

    full_receipt_written = False
    if full_receipt_out is not None:
        if not isinstance(full_receipt_out, Path):
            raise ExistingOQ313DatastoreProjectionError(
                "full receipt output path must be a Path"
            )
        _write_new_file(full_receipt_out, payload)
        full_receipt_written = True

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_kind": "existing_openquake_datastore",
        "datastore": {
            "filename": path.name,
            **datastore_identity,
        },
        "numerical_receipt_identity": validated_identity,
        "full_receipt_written": full_receipt_written,
        "historical_reproduction_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    if len(payload) > action.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES:
        result["projection_mode"] = "commitment"
        result["numerical_receipt_commitment"] = action._numerical_receipt_commitment(
            document,
            validated_identity,
        )
    else:
        result["projection_mode"] = "full_receipt"
        result["numerical_receipt"] = document
    return result


def _canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Project a completed local OpenQuake 3.13 calc_*.hdf5 into the current "
            "bounded EQ1 risk_by_event receipt without rerunning OpenQuake."
        )
    )
    parser.add_argument("datastore", type=Path)
    parser.add_argument(
        "--full-receipt-out",
        type=Path,
        help=(
            "Optional new local file for the full canonical receipt. The path must "
            "not already exist; provider/datastore bytes are never copied there."
        ),
    )
    args = parser.parse_args(argv)
    try:
        result = project_existing_datastore(
            args.datastore,
            full_receipt_out=args.full_receipt_out,
        )
    except ExistingOQ313DatastoreProjectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(_canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
