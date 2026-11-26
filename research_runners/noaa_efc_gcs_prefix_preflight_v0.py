# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only, bounded NOAA EFC Google Cloud Storage object-metadata preflight.

Does NOT access the network, authorize bucket listing, fetch any object,
validate hail/tornado event data, or admit inputs to a catastrophe model.
Operator input must be a separately rights-reviewed original JSON list body.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

SOURCE_ID = "noaa.ncei.event-footprint-catalog.2026"
BUCKET = "noaa-ncei-ipg"
PREFIX = "datasets/event-catalog/"
MAX_BYTES = 65_536
MAX_ENTRIES = 10
MAX_LOCAL_FILE = 65_536
SAFE_OBJECT_NAME = re.compile(r"^[A-Za-z0-9_./ -]+$")
DIGITS = re.compile(r"^[0-9]{1,20}$")


class EfcGcsPreflightError(ValueError):
    """Untrusted GCS response violates bounded original metadata contract."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise EfcGcsPreflightError("duplicate JSON key")
        result[name] = value
    return result


def _reject_constant(_value: str) -> None:
    raise EfcGcsPreflightError("nonfinite JSON numeric value")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise EfcGcsPreflightError("nonfinite JSON float")
    return number


def _safe_name(value: Any, *, is_prefix: bool = False) -> str:
    if type(value) is not str or len(value) > 2048:
        raise EfcGcsPreflightError("invalid object/prefix name")
    if not value.startswith(PREFIX) or not SAFE_OBJECT_NAME.fullmatch(value):
        raise EfcGcsPreflightError("unexpected GCS object-name prefix or syntax")
    if value.startswith("/") or value.endswith("/.") or "//" in value:
        raise EfcGcsPreflightError("ambiguous object path")
    if any(part in {"", ".", ".."} for part in value.split("/")[:-1]):
        raise EfcGcsPreflightError("empty or traversal object-name segment")
    if is_prefix:
        if not value.endswith("/"):
            raise EfcGcsPreflightError("GCS prefix must end in slash")
    elif value.endswith("/"):
        raise EfcGcsPreflightError("folder is not an individual object")
    return value


def _decimal(value: Any, name: str) -> int:
    if type(value) is not str or not DIGITS.fullmatch(value):
        raise EfcGcsPreflightError(f"invalid {name}")
    number = int(value)
    if number <= 0 and name == "generation":
        raise EfcGcsPreflightError("GCS generation must be positive")
    return number


def inspect_original_metadata(raw: bytes) -> dict[str, Any]:
    """Inspect one externally acquired small original listing; no URLs are followed."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise EfcGcsPreflightError("empty or oversized original response")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object,
                         parse_constant=_reject_constant, parse_float=_finite_float)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EfcGcsPreflightError("invalid UTF-8 JSON response") from exc
    if type(obj) is not dict or obj.get("kind") != "storage#objects":
        raise EfcGcsPreflightError("response is not a GCS objects listing")
    items = obj.get("items", [])
    prefixes = obj.get("prefixes", [])
    if type(items) is not list or type(prefixes) is not list:
        raise EfcGcsPreflightError("GCS items/prefixes must be arrays")
    if not 0 < len(items) + len(prefixes) <= MAX_ENTRIES:
        raise EfcGcsPreflightError("empty or unbounded GCS listing")
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not dict or item.get("kind") != "storage#object":
            raise EfcGcsPreflightError("invalid GCS item kind")
        name = _safe_name(item.get("name"))
        if name in seen or item.get("bucket") != BUCKET:
            raise EfcGcsPreflightError("duplicate name or foreign GCS bucket")
        seen.add(name)
        generation = _decimal(item.get("generation"), "generation")
        size = _decimal(item.get("size"), "size")
        content_type = item.get("contentType")
        if content_type is not None and (type(content_type) is not str
                                         or len(content_type) > 128
                                         or "/" not in content_type):
            raise EfcGcsPreflightError("malformed GCS content type")
        discovered.append({"name": name, "generation": str(generation),
                           "size_bytes": size, "content_type": content_type})
    safe_prefixes: list[str] = []
    for value in prefixes:
        prefix = _safe_name(value, is_prefix=True)
        if prefix in seen:
            raise EfcGcsPreflightError("duplicate GCS prefix")
        seen.add(prefix)
        safe_prefixes.append(prefix)
    if [row["name"] for row in discovered] != sorted(row["name"] for row in discovered):
        raise EfcGcsPreflightError("objects not ordered by provider lexicographic name")
    if safe_prefixes != sorted(safe_prefixes):
        raise EfcGcsPreflightError("GCS prefixes not sorted")
    continuation = obj.get("nextPageToken")
    if continuation is not None and (type(continuation) is not str
                                     or not 0 < len(continuation) <= 2048):
        raise EfcGcsPreflightError("invalid GCS continuation marker")
    return {
        "profile": "oc-noaa-efc-gcs-prefix-metadata-v0",
        "source_id": SOURCE_ID,
        "bucket_from_catalogue": BUCKET,
        "catalogue_prefix": PREFIX,
        "original_response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "object_count": len(discovered),
        "prefix_count": len(safe_prefixes),
        "objects_metadata_only": discovered,
        "prefixes_metadata_only": safe_prefixes,
        "more_pages_indicated_but_not_followed": continuation is not None,
        "source_byte_persistence_authorized": False,
        "original_event_geojson_acquired": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-metadata-json", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        path = args.original_metadata_json
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_LOCAL_FILE:
            raise EfcGcsPreflightError("expected bounded regular non-symlink local file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        print(json.dumps(inspect_original_metadata(raw), sort_keys=True, indent=2,
                         allow_nan=False))
    except (EfcGcsPreflightError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
