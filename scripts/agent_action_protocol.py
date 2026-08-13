# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Shared fail-closed primitives for the bounded agent-action control plane."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

REQUEST_SCHEMA_VERSION = "oc-action-request-v1"
RESULT_MARKER = "<!-- oc-action-result-v1 -->"
RESULT_SCHEMA_VERSION = "oc-action-result-v1"
ACQUISITION_RECEIPT_ACTION = "acquisition_receipt"
DWD_METADATA_RECEIPT_ACTION = "dwd_metadata_receipt"
EFEHR_README_RECEIPT_ACTION = "efehr_readme_receipt"
NETWORK_ACQUISITION_ACTIONS = frozenset(
    {ACQUISITION_RECEIPT_ACTION, DWD_METADATA_RECEIPT_ACTION, EFEHR_README_RECEIPT_ACTION}
)
GIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
TRUSTED_RESULT_LOGINS = {"github-actions[bot]"}


class ProtocolError(ValueError):
    """Raised when durable action protocol state is invalid."""


def semantic_request_id(request: dict[str, Any], execution_sha: str, repository: str) -> str:
    """Return the cross-thread semantic identity of one trusted execution request.

    Transport-only fields such as source issue and requester are intentionally
    excluded. Repository and trusted execution-code SHA are included so receipts
    cannot be reused across repositories or materially different protocol code.
    Each closed network acquisition action also requires its semantic target to
    equal the trusted execution commit. The action itself participates in the
    identity, keeping measurement, station-metadata and EFEHR README receipts
    distinct without introducing a caller-controlled network target.
    """

    if type(execution_sha) is not str or not GIT_SHA_RE.fullmatch(execution_sha):
        raise ProtocolError("execution_sha must be a lowercase 40-character Git commit SHA")
    if type(repository) is not str or not REPOSITORY_RE.fullmatch(repository):
        raise ProtocolError("repository must be canonical owner/name")
    for field in ("schema_version", "action", "target_sha", "dataset_id"):
        if field not in request:
            raise ProtocolError(f"request missing semantic field: {field}")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ProtocolError("unsupported request schema_version for semantic identity")
    if request["action"] in NETWORK_ACQUISITION_ACTIONS and request["target_sha"] != execution_sha:
        raise ProtocolError("network acquisition target_sha must equal trusted execution_sha")
    payload = {
        "schema_version": request["schema_version"],
        "action": request["action"],
        "dataset_id": request["dataset_id"],
        "target_sha": request["target_sha"],
        "execution_sha": execution_sha,
        "repository": repository,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def semantic_request_id_from_result(result: dict[str, Any]) -> str:
    """Recompute a result receipt's semantic identity from its bound fields."""

    required = ("action", "dataset_id", "target_sha", "execution_sha", "repository")
    for field in required:
        if field not in result:
            raise ProtocolError(f"result missing semantic field: {field}")
    request_view = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": result["action"],
        "dataset_id": result["dataset_id"],
        "target_sha": result["target_sha"],
    }
    return semantic_request_id(request_view, result["execution_sha"], result["repository"])


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
