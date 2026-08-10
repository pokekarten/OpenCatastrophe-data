# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Strict validation and identity for external acquisition receipts.

Receipts bind frozen acquisition intent and an admitted manifest to one exact
external request and one exact byte artifact. They do not admit the bytes for
Git publication; storage remains external unless the dataset manifest is
separately promoted through the repository admission process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qsl, urlparse

SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
EXTERNAL_RE = re.compile(r"^external://[A-Za-z0-9][A-Za-z0-9._/-]*$")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")

TOP_KEYS = {"schema_version", "acquisition_intent_sha256", "manifest", "request", "artifact"}
MANIFEST_KEYS = {"path", "sha256"}
REQUEST_KEYS = {"exact_request", "retrieved_at"}
ARTIFACT_KEYS = {"logical_identity", "byte_size", "sha256", "storage_reference"}

SENSITIVE_NAMES = {
    "access_key", "access_token", "api_key", "apikey", "auth", "authorization",
    "cookie", "credential", "credentials", "key", "password", "private_key",
    "secret", "session", "sig", "signature", "signed_url", "token",
    "x_amz_credential", "x_amz_signature", "x_goog_credential", "x_goog_signature",
}


class ReceiptError(ValueError):
    """Raised when an external acquisition receipt fails closed."""


def _reject_constant(value: str) -> None:
    raise ReceiptError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(str(exc)) from exc
    if type(payload) is not dict:
        raise ReceiptError("receipt root must be an object")
    return payload


def _closed(obj: dict[str, Any], allowed: set[str], required: set[str], field: str) -> None:
    unknown = sorted(set(obj) - allowed)
    missing = sorted(required - set(obj))
    if unknown:
        raise ReceiptError(f"{field} contains unexpected fields: {', '.join(unknown)}")
    if missing:
        raise ReceiptError(f"{field} is missing fields: {', '.join(missing)}")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ReceiptError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ReceiptError(f"{field} must be a non-empty trimmed string")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise ReceiptError(f"{field} must not contain control characters")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ReceiptError(f"{field} must be valid UTF-8") from exc
    return value


def _sha256(value: Any, field: str) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ReceiptError(f"{field} must be a lowercase SHA-256")
    return value


def _timestamp(value: Any, field: str) -> str:
    text = _string(value, field)
    if not RFC3339_RE.fullmatch(text):
        raise ReceiptError(f"{field} must be RFC-3339 with an explicit timezone")
    normalized = text[:-1] + "+00:00" if text[-1:] in {"Z", "z"} else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ReceiptError(f"{field} is not a valid date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReceiptError(f"{field} must include a timezone")
    return text


def _manifest_path(value: Any) -> str:
    text = _string(value, "manifest.path")
    if "\\" in text or text.startswith("/"):
        raise ReceiptError("manifest.path must be a relative canonical POSIX path")
    path = PurePosixPath(text)
    if path.as_posix() != text or path.parts[:1] != ("manifests",) or path.suffix != ".json":
        raise ReceiptError("manifest.path must be a canonical manifests/*.json path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ReceiptError("manifest.path must not contain empty, dot, or parent segments")
    return text


def _external_reference(value: Any) -> str:
    text = _string(value, "artifact.storage_reference")
    if not EXTERNAL_RE.fullmatch(text):
        raise ReceiptError("artifact.storage_reference must be a canonical external:// reference")
    segments = text[len("external://"):].split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ReceiptError("artifact.storage_reference must not contain empty, dot, or parent path segments")
    return text


def _normalized_sensitive_name(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _check_url_for_secrets(value: str, field: str) -> None:
    if not value.lower().startswith(("http://", "https://")):
        return
    try:
        parsed = urlparse(value)
        parsed.port
    except ValueError as exc:
        raise ReceiptError(f"{field} contains a malformed URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ReceiptError(f"{field} contains a malformed HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ReceiptError(f"{field} must not contain URL credentials")
    sensitive = [
        name
        for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
        if _normalized_sensitive_name(name) in SENSITIVE_NAMES
        or _normalized_sensitive_name(name).startswith("x_amz_")
        or _normalized_sensitive_name(name).startswith("x_goog_")
    ]
    if sensitive:
        raise ReceiptError(f"{field} must not contain credential/signature query parameters")


def _safe_json(value: Any, field: str) -> None:
    if value is None or type(value) in {bool, int, str}:
        if type(value) is str:
            _string(value, field)
            _check_url_for_secrets(value, field)
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ReceiptError(f"{field} must not contain non-finite numbers")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _safe_json(item, f"{field}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ReceiptError(f"{field} keys must be strings")
            _string(key, f"{field} key")
            normalized = _normalized_sensitive_name(key)
            if normalized in SENSITIVE_NAMES or normalized.startswith("x_amz_") or normalized.startswith("x_goog_"):
                raise ReceiptError(f"{field} contains forbidden credential/signature field: {key}")
            _safe_json(item, f"{field}.{key}")
        return
    raise ReceiptError(f"{field} contains unsupported JSON value type")


def validate_receipt(
    receipt: dict[str, Any],
    *,
    expected_intent_sha256: str | None = None,
    expected_manifest: str | None = None,
) -> None:
    """Validate one closed, secret-safe external acquisition receipt."""

    if type(receipt) is not dict:
        raise ReceiptError("receipt root must be an object")
    _closed(receipt, TOP_KEYS, TOP_KEYS, "receipt")
    if receipt["schema_version"] != SCHEMA_VERSION:
        raise ReceiptError(f"schema_version must be {SCHEMA_VERSION}")

    intent_digest = _sha256(receipt["acquisition_intent_sha256"], "acquisition_intent_sha256")
    if expected_intent_sha256 is not None:
        _sha256(expected_intent_sha256, "expected_intent_sha256")
        if intent_digest != expected_intent_sha256:
            raise ReceiptError("acquisition_intent_sha256 does not match expected frozen intent")

    manifest = _mapping(receipt["manifest"], "manifest")
    _closed(manifest, MANIFEST_KEYS, MANIFEST_KEYS, "manifest")
    manifest_path = _manifest_path(manifest["path"])
    _sha256(manifest["sha256"], "manifest.sha256")
    if expected_manifest is not None:
        expected_path = _manifest_path(expected_manifest)
        if manifest_path != expected_path:
            raise ReceiptError("manifest.path does not match expected admitted manifest")

    request = _mapping(receipt["request"], "request")
    _closed(request, REQUEST_KEYS, REQUEST_KEYS, "request")
    exact_request = _mapping(request["exact_request"], "request.exact_request")
    if not exact_request:
        raise ReceiptError("request.exact_request must not be empty")
    _safe_json(exact_request, "request.exact_request")
    _timestamp(request["retrieved_at"], "request.retrieved_at")

    artifact = _mapping(receipt["artifact"], "artifact")
    _closed(artifact, ARTIFACT_KEYS, ARTIFACT_KEYS, "artifact")
    _string(artifact["logical_identity"], "artifact.logical_identity")
    byte_size = artifact["byte_size"]
    if type(byte_size) is not int or byte_size <= 0:
        raise ReceiptError("artifact.byte_size must be a positive integer")
    _sha256(artifact["sha256"], "artifact.sha256")
    _external_reference(artifact["storage_reference"])


def canonical_receipt_bytes(receipt: dict[str, Any]) -> bytes:
    validate_receipt(receipt)
    return json.dumps(
        receipt,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def receipt_sha256(receipt: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_receipt_bytes(receipt)).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-intent-sha256")
    parser.add_argument("--expected-manifest")
    parser.add_argument("--print-sha256", action="store_true")
    args = parser.parse_args()

    try:
        receipt = load_receipt(args.receipt)
        validate_receipt(
            receipt,
            expected_intent_sha256=args.expected_intent_sha256,
            expected_manifest=args.expected_manifest,
        )
        digest = receipt_sha256(receipt) if args.print_sha256 else None
    except ReceiptError as exc:
        print(f"BLOCKED: {exc}")
        return 1

    print(f"PASS: {args.receipt}")
    if digest is not None:
        print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
