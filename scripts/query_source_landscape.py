# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Query the public non-admission source landscape without external dependencies."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LANDSCAPE_DIR = ROOT / "landscape"
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


class LandscapeQueryError(ValueError):
    """Raised when the landscape cannot be read without ambiguous semantics."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LandscapeQueryError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise LandscapeQueryError(f"non-finite JSON number is not allowed: {value}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LandscapeQueryError(f"{path}: unable to read strict JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LandscapeQueryError(f"{path}: landscape shard must be a JSON object")
    return payload


def _require_text(entry: dict[str, Any], key: str, *, path: Path) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LandscapeQueryError(f"{path}: {key} must be a non-empty string")
    return value


def _require_string_list(entry: dict[str, Any], key: str, *, path: Path) -> tuple[str, ...]:
    value = entry.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise LandscapeQueryError(f"{path}: {key} must be a non-empty array of strings")
    return tuple(value)


def _validate_authoritative_url(url: str, *, path: Path) -> None:
    if any(ch.isspace() for ch in url):
        raise LandscapeQueryError(f"{path}: authoritative_url must not contain whitespace")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise LandscapeQueryError(f"{path}: authoritative_url is malformed") from exc

    if parsed.scheme != "https" or not hostname:
        raise LandscapeQueryError(f"{path}: authoritative_url must use HTTPS with a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise LandscapeQueryError(f"{path}: authoritative_url must not embed credentials")

    host = hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(LOCAL_HOST_SUFFIXES):
        raise LandscapeQueryError(f"{path}: authoritative_url must not reference a local/private host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise LandscapeQueryError(f"{path}: authoritative_url must not reference a non-public IP address")

    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() in SENSITIVE_QUERY_KEYS:
            raise LandscapeQueryError(f"{path}: authoritative_url must not contain credential or signature query parameters")


def _normalize_search_text(value: str) -> str:
    return " ".join(re.sub(r"[-_]+", " ", value.casefold()).split())


def load_landscape(directory: Path = DEFAULT_LANDSCAPE_DIR) -> tuple[dict[str, Any], ...]:
    """Load all landscape shards and enforce the public non-admission boundary."""

    paths = tuple(sorted(directory.glob("sources*.json")))
    if not paths:
        raise LandscapeQueryError(f"{directory}: no source landscape shards found")

    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for path in paths:
        payload = _load_json(path)
        if set(payload) != HEADER_KEYS:
            raise LandscapeQueryError(f"{path}: unexpected landscape header fields")
        if payload.get("schema_version") != "1.0.0":
            raise LandscapeQueryError(f"{path}: unsupported schema_version")
        purpose = payload.get("purpose")
        if not isinstance(purpose, str) or "Non-admission" not in purpose:
            raise LandscapeQueryError(f"{path}: purpose must explicitly declare Non-admission")
        review_date = payload.get("review_date")
        if not isinstance(review_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date):
            raise LandscapeQueryError(f"{path}: review_date must be YYYY-MM-DD")
        shard_entries = payload.get("entries")
        if not isinstance(shard_entries, list) or not shard_entries:
            raise LandscapeQueryError(f"{path}: entries must be a non-empty array")

        for raw_entry in shard_entries:
            if not isinstance(raw_entry, dict) or set(raw_entry) != ENTRY_KEYS:
                raise LandscapeQueryError(f"{path}: landscape entry fields do not match v1 contract")

            candidate_id = _require_text(raw_entry, "candidate_id", path=path)
            if not CANDIDATE_ID_RE.fullmatch(candidate_id):
                raise LandscapeQueryError(f"{path}: invalid candidate_id: {candidate_id}")
            if candidate_id in seen_ids:
                raise LandscapeQueryError(f"duplicate candidate_id across landscape shards: {candidate_id}")
            seen_ids.add(candidate_id)

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
                raise LandscapeQueryError(f"{path}: candidate_status must remain evidence_checked")
            if raw_entry.get("rights_review_status") != "not_reviewed":
                raise LandscapeQueryError(f"{path}: rights_review_status must remain not_reviewed")
            if raw_entry.get("scientific_review_status") != "not_reviewed":
                raise LandscapeQueryError(f"{path}: scientific_review_status must remain not_reviewed")
            if raw_entry.get("admission_status") != "not_admitted":
                raise LandscapeQueryError(f"{path}: admission_status must remain not_admitted")

            entries.append(raw_entry)

    return tuple(sorted(entries, key=lambda item: str(item["candidate_id"])))


def query_entries(
    entries: tuple[dict[str, Any], ...],
    *,
    candidate_id: str | None = None,
    categories: tuple[str, ...] = (),
    roles: tuple[str, ...] = (),
    provider: str | None = None,
    text: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return deterministic matches; all supplied filters use AND semantics."""

    category_filters = tuple(value.casefold() for value in categories)
    role_filters = tuple(value.casefold() for value in roles)
    provider_filter = provider.casefold() if provider else None
    text_filter = _normalize_search_text(text) if text else None

    matches: list[dict[str, Any]] = []
    for entry in entries:
        if candidate_id is not None and entry["candidate_id"] != candidate_id:
            continue
        entry_categories = {value.casefold() for value in entry["categories"]}
        if any(value not in entry_categories for value in category_filters):
            continue
        entry_roles = {value.casefold() for value in entry["potential_roles"]}
        if any(value not in entry_roles for value in role_filters):
            continue
        if provider_filter is not None and provider_filter not in entry["provider"].casefold():
            continue
        if text_filter is not None:
            searchable = _normalize_search_text(
                " ".join(
                    [
                        entry["candidate_id"],
                        entry["name"],
                        entry["provider"],
                        entry["spatial_scope"],
                        entry["temporal_scope"],
                        entry["resolution_or_granularity"],
                        *entry["categories"],
                        *entry["potential_roles"],
                        entry["note"],
                    ]
                )
            )
            if text_filter not in searchable:
                continue
        matches.append(entry)

    return tuple(matches)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", dest="candidate_id", help="Exact candidate_id")
    parser.add_argument("--category", action="append", default=[], help="Required exact category; repeatable")
    parser.add_argument("--role", action="append", default=[], help="Required exact potential role; repeatable")
    parser.add_argument("--provider", help="Case-insensitive provider substring")
    parser.add_argument("--text", help="Case-insensitive substring across searchable candidate metadata")
    args = parser.parse_args(argv)

    try:
        entries = load_landscape()
        matches = query_entries(
            entries,
            candidate_id=args.candidate_id,
            categories=tuple(args.category),
            roles=tuple(args.role),
            provider=args.provider,
            text=args.text,
        )
    except LandscapeQueryError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    payload = {
        "profile": "opencatastrophe-source-landscape-query-v1",
        "scope": "non_admission_discovery_only",
        "count": len(matches),
        "results": matches,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
