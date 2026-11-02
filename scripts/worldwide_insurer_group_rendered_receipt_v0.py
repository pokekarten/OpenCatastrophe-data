#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, fail-closed IAIS/NAIC group-register rendered-text receipt.

Input is a *locally obtained readable page rendering*, NEVER original provider
HTTP bytes or an authorised bulk ingestion. Does not fetch, store provider rows,
connect to Neon, map legal entities, or grant data/model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

URLS = {
    "iais": "https://www.iais.org/register-of-iaigs/",
    "naic": "https://isiteplus.naic.org/lead-state/publeadstate/pubLSHtml",
}
PROFILES = {
    "iais": {"count": 61, "jurisdictions": 19, "period": "2026-10-14"},
    "naic": {"count": 682, "jurisdictions": 52, "period": "2026-Q2"},
}
MAX_TEXT_BYTES = 1024 * 1024
IAIS_HEADER = re.compile(
    r"As of 14 October 2026, 61 IAIGs have been identified.*?from 19 jurisdictions",
    re.IGNORECASE | re.DOTALL,
)
NAIC_HEADER = re.compile(r"2026\s*-\s*Quarter\s*2", re.IGNORECASE)


class GroupRegisterError(ValueError):
    """The readable source document does not match the pinned source profile."""


def _name_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _fields(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [value.strip() for value in stripped.split("|")]


def _input(raw: bytes) -> str:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_TEXT_BYTES:
        raise GroupRegisterError("missing, oversized or invalid rendered text")
    try:
        value = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise GroupRegisterError("rendered text is not UTF-8") from exc
    if "\x00" in value or "\x1e" in value or "\x1f" in value:
        raise GroupRegisterError("rendered text contains reserved separators")
    return value


def _parse_iais(value: str, *, count: int, jurisdictions: int) -> list[tuple[str, ...]]:
    if not IAIS_HEADER.search(value):
        raise GroupRegisterError("IAIS dated group-count header missing")
    rows: list[tuple[str, ...]] = []
    for line in value.splitlines():
        f = _fields(line)
        if len(f) == 4 and f[0].isdigit():
            ordinal, name, supervisor, country = f
            if not name or not supervisor or not country or len(name) > 250:
                raise GroupRegisterError("empty or malformed IAIS group field")
            rows.append((ordinal, name, supervisor, country))
    if len(rows) != count or sorted(int(row[0]) for row in rows) != list(range(1, count + 1)):
        raise GroupRegisterError("incomplete, duplicated or nonsequential IAIS groups")
    if len({_name_key(row[1]) for row in rows}) != count:
        raise GroupRegisterError("duplicate IAIS group name")
    if len({row[3] for row in rows}) != jurisdictions:
        raise GroupRegisterError("IAIS supervisor jurisdiction tally mismatch")
    return rows


def _parse_naic(value: str, *, count: int, jurisdictions: int) -> list[tuple[str, ...]]:
    if not NAIC_HEADER.search(value) or "Group Code" not in value or "Lead State" not in value:
        raise GroupRegisterError("NAIC dated group-code register header missing")
    rows: list[tuple[str, ...]] = []
    for line in value.splitlines():
        f = _fields(line)
        if len(f) == 3 and f[1].isdigit():
            name, code, state = f
            if not 1 <= len(name) <= 250 or not re.fullmatch(r"[0-9]{1,5}", code):
                raise GroupRegisterError("invalid NAIC group name or code")
            if not re.fullmatch(r"[A-Z]{2}", state):
                raise GroupRegisterError("invalid NAIC lead jurisdiction")
            rows.append((name, code, state))
    if len(rows) != count or len({row[1] for row in rows}) != count:
        raise GroupRegisterError("NAIC missing or repeated group code")
    if len({row[2] for row in rows}) != jurisdictions:
        raise GroupRegisterError("NAIC lead jurisdiction tally mismatch")
    return rows


def audit_rendered_text(raw: bytes, register: str) -> dict:
    if register not in PROFILES:
        raise GroupRegisterError("unsupported register")
    value = _input(raw)
    profile = PROFILES[register]
    if register == "iais":
        rows = _parse_iais(value, count=profile["count"], jurisdictions=profile["jurisdictions"])
        keys = [row[0] for row in rows]
    else:
        rows = _parse_naic(value, count=profile["count"], jurisdictions=profile["jurisdictions"])
        keys = [row[1] for row in rows]
    # This hash identifies the local *rendering*, not the original HTTP response.
    # No row-level source bytes, names or identifiers are output.
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return {
        "schema": "oc-worldwide-insurer-group-rendered-receipt-v0",
        "register": register,
        "source_url": URLS[register],
        "source_period": profile["period"],
        "group_rows_read": len(rows),
        "distinct_group_identifiers": len(set(keys)),
        "distinct_supervisor_jurisdictions": profile["jurisdictions"],
        "rendered_text_sha256": digest,
        "original_http_bytes_verified": False,
        "rights_review_completed": False,
        "group_to_legal_entity_links_asserted": 0,
        "neon_updated": False,
        "model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, choices=sorted(PROFILES))
    parser.add_argument("--rendered-text", type=Path, required=True)
    args = parser.parse_args()
    path = args.rendered_text
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_TEXT_BYTES:
        raise GroupRegisterError("rendered-text path is not a bounded regular file")
    print(json.dumps(audit_rendered_text(path.read_bytes(), args.register), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GroupRegisterError, OSError, UnicodeError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
