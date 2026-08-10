# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Authoritative executable contract for the public non-admission source landscape.

The JSON Schema is the portable structural profile. This module additionally
enforces repository policy and cross-shard invariants that are awkward or
unsafe to express as JSON Schema alone, including strict JSON parsing, public
URL safety, real calendar dates, global candidate-ID uniqueness and the
non-admission state boundary.
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LANDSCAPE_DIR = ROOT / "landscape"
SCHEMA_VERSION = "1.0.0"
CANDIDATE_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
HEADER_KEYS = {"schema_version", "purpose", "review_date", "entries"}
ENTRY_KEYS = {
    "candidate_id",
    "name",
    "provider",
    "categories",
    "spatial_scope",
    "temporal_scope",
    "resolution_or_granularity",
    "potential_roles",
    "authoritative_url",
    "access_class_hint",
    "candidate_status",
    "rights_review_status",
    "scientific_review_status",
    "admission_status",
    "note",
}
SENSITIVE_QUERY_KEYS = {
    "access_key",
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credential",
    "key",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-signature",
    "x-goog-credential",
    "x-goog-signature",
}
LOCAL_HOST_SUFFIXES = (".local", ".localhost", ".internal")


class LandscapeContractError(ValueError):
    """Raised when source-landscape bytes do not satisfy the public contract."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LandscapeContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise LandscapeContractError(f"non-finite JSON number is not allowed: {value}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LandscapeContractError(f"{path}: unable to read strict JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LandscapeContractError(f"{path}: landscape shard must be a JSON object")
    return payload


def _require_text(entry: dict[str, Any], key: str, *, path: Path) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LandscapeContractError(f"{path}: {key} must be a non-empty string")
    return value


def _require_string_list(entry: dict[str, Any], key: str, *, path: Path) -> tuple[str, ...]:
    value = entry.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise LandscapeContractError(f"{path}: {key} must be a non-empty array of strings")
    return tuple(value)


def _validate_authoritative_url(url: str, *, path: Path) -> None:
    if any(ch.isspace() for ch in url):
        raise LandscapeContractError(f"{path}: authoritative_url must not contain whitespace")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise LandscapeContractError(f"{path}: authoritative_url is malformed") from exc

    if parsed.scheme != "https" or not hostname:
        raise LandscapeContractError(f"{path}: authoritative_url must use HTTPS with a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise LandscapeContractError(f"{path}: authoritative_url must not embed credentials")

    host = hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(LOCAL_HOST_SUFFIXES):
        raise LandscapeContractError(f"{path}: authoritative_url must not reference a local/private host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise LandscapeContractError(f"{path}: authoritative_url must not reference a non-public IP address")

    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() in SENSITIVE_QUERY_KEYS:
            raise LandscapeContractError(
                f"{path}: authoritative_url must not contain credential or signature query parameters"
            )


def validate_landscape_shard(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one decoded shard without weakening the version-1 accepted domain."""

    if set(payload) != HEADER_KEYS:
        raise LandscapeContractError(f"{path}: unexpected landscape header fields")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise LandscapeContractError(f"{path}: unsupported schema_version")
    purpose = payload.get("purpose")
    if not isinstance(purpose, str) or "Non-admission" not in purpose:
        raise LandscapeContractError(f"{path}: purpose must explicitly declare Non-admission")
    review_date = payload.get("review_date")
    if not isinstance(review_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date):
        raise LandscapeContractError(f"{path}: review_date must be YYYY-MM-DD")
    try:
        date.fromisoformat(review_date)
    except ValueError as exc:
        raise LandscapeContractError(f"{path}: review_date must be a valid calendar date") from exc

    shard_entries = payload.get("entries")
    if not isinstance(shard_entries, list) or not shard_entries:
        raise LandscapeContractError(f"{path}: entries must be a non-empty array")

    for raw_entry in shard_entries:
        if not isinstance(raw_entry, dict) or set(raw_entry) != ENTRY_KEYS:
            raise LandscapeContractError(f"{path}: landscape entry fields do not match v1 contract")

        candidate_id = _require_text(raw_entry, "candidate_id", path=path)
        if not CANDIDATE_ID_RE.fullmatch(candidate_id):
            raise LandscapeContractError(f"{path}: invalid candidate_id: {candidate_id}")

        for key in (
            "name",
            "provider",
            "spatial_scope",
            "temporal_scope",
            "resolution_or_granularity",
            "access_class_hint",
            "note",
        ):
            _require_text(raw_entry, key, path=path)
        _require_string_list(raw_entry, "categories", path=path)
        _require_string_list(raw_entry, "potential_roles", path=path)

        url = _require_text(raw_entry, "authoritative_url", path=path)
        _validate_authoritative_url(url, path=path)
        if raw_entry.get("candidate_status") != "evidence_checked":
            raise LandscapeContractError(f"{path}: candidate_status must remain evidence_checked")
        if raw_entry.get("rights_review_status") != "not_reviewed":
            raise LandscapeContractError(f"{path}: rights_review_status must remain not_reviewed")
        if raw_entry.get("scientific_review_status") != "not_reviewed":
            raise LandscapeContractError(f"{path}: scientific_review_status must remain not_reviewed")
        if raw_entry.get("admission_status") != "not_admitted":
            raise LandscapeContractError(f"{path}: admission_status must remain not_admitted")

    return payload


def load_landscape_shard(path: Path) -> dict[str, Any]:
    """Strictly decode and validate one landscape shard."""

    return validate_landscape_shard(path, _load_json(path))


def load_landscape_shards(
    directory: Path = DEFAULT_LANDSCAPE_DIR,
) -> tuple[tuple[Path, dict[str, Any]], ...]:
    """Load all shards and enforce invariants that span shard boundaries."""

    paths = tuple(sorted(directory.glob("sources*.json")))
    if not paths:
        raise LandscapeContractError(f"{directory}: no source landscape shards found")

    shards: list[tuple[Path, dict[str, Any]]] = []
    seen_ids: set[str] = set()
    for path in paths:
        payload = load_landscape_shard(path)
        for raw_entry in payload["entries"]:
            candidate_id = str(raw_entry["candidate_id"])
            if candidate_id in seen_ids:
                raise LandscapeContractError(
                    f"duplicate candidate_id across landscape shards: {candidate_id}"
                )
            seen_ids.add(candidate_id)
        shards.append((path, payload))
    return tuple(shards)


def load_landscape(directory: Path = DEFAULT_LANDSCAPE_DIR) -> tuple[dict[str, Any], ...]:
    """Return all validated candidate entries in stable candidate-ID order."""

    entries = [
        entry
        for _path, payload in load_landscape_shards(directory)
        for entry in payload["entries"]
    ]
    return tuple(sorted(entries, key=lambda item: str(item["candidate_id"])))
