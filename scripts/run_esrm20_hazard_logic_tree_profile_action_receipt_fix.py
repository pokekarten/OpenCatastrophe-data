# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind #481 to canonical receipts and scope terminal dedup to one execution SHA.

This adapter changes no parser, provider target, request/result schema, or
authority semantics. It exists because two SHA-256 values were originally
transcribed incorrectly and because the original terminal-ledger scanner tried
to validate older trusted results against the current execution SHA. Older
well-formed results remain auditable history but cannot deduplicate a new head.
"""

from __future__ import annotations

import json
from typing import Any

from scripts import run_esrm20_hazard_logic_tree_profile_action as _subject

CANONICAL_GSIM_SHA256 = "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4"
CANONICAL_SOURCE_SHA256 = "caebf9142da6b4d6d1e970c3c008627d34943da83c977fb1da4d15d1e34d8a12"
CANONICAL_RECEIPT_COMMENT_ID = 5310057117

_subject.GSIM_SHA256 = CANONICAL_GSIM_SHA256
_subject.SOURCE_SHA256 = CANONICAL_SOURCE_SHA256
_subject.RECEIPT_COMMENT_ID = CANONICAL_RECEIPT_COMMENT_ID

REQUEST_MARKER = _subject.REQUEST_MARKER
RESULT_MARKER = _subject.RESULT_MARKER
REQUEST_SCHEMA_VERSION = _subject.REQUEST_SCHEMA_VERSION
RESULT_SCHEMA_VERSION = _subject.RESULT_SCHEMA_VERSION
ACTION = _subject.ACTION
CONTROL_ISSUE = _subject.CONTROL_ISSUE
SOURCE_SCIENCE_ISSUE = _subject.SOURCE_SCIENCE_ISSUE
DATASET_ID = _subject.DATASET_ID
GSIM_BYTE_COUNT = _subject.GSIM_BYTE_COUNT
GSIM_SHA256 = _subject.GSIM_SHA256
SOURCE_BYTE_COUNT = _subject.SOURCE_BYTE_COUNT
SOURCE_SHA256 = _subject.SOURCE_SHA256
RECEIPT_COMMENT_ID = _subject.RECEIPT_COMMENT_ID

validate_request = _subject.validate_request
_validate_profile = _subject._validate_profile
run_profile = _subject.run_profile
main = _subject.main


def assert_canonical_receipt_binding() -> None:
    if _subject.GSIM_SHA256 != CANONICAL_GSIM_SHA256:
        raise RuntimeError("GSIM receipt hash binding drifted")
    if _subject.SOURCE_SHA256 != CANONICAL_SOURCE_SHA256:
        raise RuntimeError("source receipt hash binding drifted")
    if _subject.RECEIPT_COMMENT_ID != CANONICAL_RECEIPT_COMMENT_ID:
        raise RuntimeError("canonical hazard receipt comment binding drifted")


def _result_execution_sha(body: object) -> str | None:
    """Return a trusted result's own SHA after envelope/JSON identity checks.

    This intentionally does not validate content fields for a *different* head:
    historical results can legitimately encode older receipt bindings. It does
    require a canonical envelope, duplicate-key-free JSON, matching target and
    execution SHAs, and the fixed action/issue/dataset identity before allowing
    the scanner to ignore that historical record.
    """
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise _subject.HazardLogicTreeProfileActionError(
            "trusted hazard profile marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise _subject.HazardLogicTreeProfileActionError(
            "trusted hazard profile envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_subject._pairs,
            parse_constant=_subject._reject_constant,
        )
    except _subject.HazardLogicTreeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise _subject.HazardLogicTreeProfileActionError(
            "trusted hazard profile JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise _subject.HazardLogicTreeProfileActionError(
            "trusted hazard profile result is not an object"
        )
    fixed = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", CONTROL_ISSUE),
        ("source_science_issue", SOURCE_SCIENCE_ISSUE),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in fixed:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise _subject.HazardLogicTreeProfileActionError(
                f"trusted hazard historical result drifted at {field}"
            )
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or _subject._SHA_RE.fullmatch(target_sha) is None
        or type(execution_sha) is not str
        or _subject._SHA_RE.fullmatch(execution_sha) is None
        or target_sha != execution_sha
    ):
        raise _subject.HazardLogicTreeProfileActionError(
            "trusted hazard historical result SHA binding is malformed"
        )
    return execution_sha


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Deduplicate only a fully validated terminal result for this exact head."""
    if type(execution_sha) is not str or _subject._SHA_RE.fullmatch(execution_sha) is None:
        raise _subject.HazardLogicTreeProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = _subject.fetch_repository_comments(repository, token, **kwargs)
    except _subject.LedgerError as exc:
        raise _subject.HazardLogicTreeProfileActionError(
            "result ledger is incomplete"
        ) from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != _subject.TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_sha = _result_execution_sha(body)
        if own_sha is None or own_sha != execution_sha:
            continue
        if _subject._parse_trusted_terminal_result(
            body, execution_sha=execution_sha
        ):
            return True
    return False


assert_canonical_receipt_binding()

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
