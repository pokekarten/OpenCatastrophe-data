# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Query the public non-admission source landscape without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .source_landscape_contract import (
        CANDIDATE_ID_RE,
        DEFAULT_LANDSCAPE_DIR,
        ENTRY_KEYS,
        HEADER_KEYS,
        LOCAL_HOST_SUFFIXES,
        SENSITIVE_QUERY_KEYS,
        LandscapeContractError,
        _validate_authoritative_url,
        load_landscape,
    )
else:
    from source_landscape_contract import (
        CANDIDATE_ID_RE,
        DEFAULT_LANDSCAPE_DIR,
        ENTRY_KEYS,
        HEADER_KEYS,
        LOCAL_HOST_SUFFIXES,
        SENSITIVE_QUERY_KEYS,
        LandscapeContractError,
        _validate_authoritative_url,
        load_landscape,
    )

LandscapeQueryError = LandscapeContractError


def _normalize_search_text(value: str) -> str:
    return " ".join(re.sub(r"[-_]+", " ", value.casefold()).split())


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
