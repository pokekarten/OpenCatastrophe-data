# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Shared fail-closed primitives for the bounded agent-action control plane."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

RESULT_MARKER = "<!-- oc-action-result-v1 -->"
RESULT_SCHEMA_VERSION = "oc-action-result-v1"
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
TRUSTED_RESULT_LOGINS = {"github-actions[bot]"}


class ProtocolError(ValueError):
    """Raised when durable action protocol state is invalid."""


def semantic_request_id(request: dict[str, Any], execution_sha: str) -> str:
    """Return the cross-thread semantic identity of one trusted execution request.

    Transport-only fields such as source issue and requester are intentionally
    excluded. The trusted execution-code SHA is included so a post-merge protocol
    change starts a new semantic execution state instead of reusing stale evidence.
    """

    if type(execution_sha) is not str or not GIT_SHA_RE.fullmatch(execution_sha):
        raise ProtocolError("execution_sha must be a lowercase 40-character Git commit SHA")
    for field in ("schema_version", "action", "target_sha", "dataset_id"):
        if field not in request:
            raise ProtocolError(f"request missing semantic field: {field}")
    payload = {
        "schema_version": request["schema_version"],
        "action": request["action"],
        "dataset_id": request["dataset_id"],
        "target_sha": request["target_sha"],
        "execution_sha": execution_sha,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def extract_result_comment(body: str) -> dict[str, Any] | None:
    """Parse one canonical result comment; return None for unrelated comments."""

    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise ProtocolError("result comment must contain exactly one result marker")
    prefix, payload = body.split(RESULT_MARKER, 1)
    if prefix.strip():
        raise ProtocolError("result marker must be the first non-whitespace content")
    payload = payload.strip()
    if not payload:
        raise ProtocolError("result payload is missing")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProtocolError(f"duplicate result JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            payload,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ProtocolError(f"non-finite result JSON value: {token}")
            ),
        )
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid result JSON: {exc}") from exc
    if type(value) is not dict:
        raise ProtocolError("result payload must be a JSON object")
    return value


def canonical_result_comment(result: dict[str, Any]) -> str:
    return RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
