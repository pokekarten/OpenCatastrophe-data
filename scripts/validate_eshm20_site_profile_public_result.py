# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate public ESHM20 site-profile terminal comments without value-set leaks.

The trusted worker/action may transiently compute exact value-set SHA-256 digests
as an internal structural check. Those deterministic digests are unsafe to
publish for singleton or otherwise low-entropy provider domains because they can
be inverted offline by dictionary enumeration.

This module is deliberately narrower than the worker. It validates only trusted
Issue #281 terminal comments and preserves dedup compatibility with the already
published legacy result shape. A public PASS may therefore be either:

* legacy: every column carries ``exact_value_set_sha256``; or
* redacted: no column carries ``exact_value_set_sha256``.

Mixed shapes fail closed. For redacted comments a private validation copy gets a
synthetic well-formed digest only so the existing strict action validator can
re-check every other field. The synthetic value is never returned or published.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

try:
    from scripts import run_eshm20_site_model_profile_action as action
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import run_eshm20_site_model_profile_action as action

VALUE_SET_DIGEST_FIELD = "exact_value_set_sha256"
_SYNTHETIC_VALIDATION_DIGEST = "0" * 64


class PublicSiteProfileResultError(RuntimeError):
    """Raised when a trusted public terminal comment is not safely bounded."""


def _column_list(result: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return PASS columns when structurally reachable, otherwise ``None``."""

    profile = result.get("profile")
    if type(profile) is not dict:
        return None
    csv_profile = profile.get("profile")
    if type(csv_profile) is not dict:
        return None
    columns = csv_profile.get("columns")
    if type(columns) is not list or any(type(column) is not dict for column in columns):
        return None
    return columns


def _strict_validate(value: dict[str, Any], *, execution_sha: str) -> None:
    try:
        action._validate_terminal_result(value, execution_sha=execution_sha)
    except action.SiteModelProfileActionError as exc:
        raise PublicSiteProfileResultError(
            "public ESHM20 site-profile terminal result failed the strict action contract"
        ) from exc


def validate_public_terminal_result(
    result: object,
    *,
    execution_sha: str,
) -> dict[str, Any]:
    """Validate legacy-hashed or fully-redacted public terminal evidence.

    Active worker output is *not* relaxed by this function. The normal action
    validator remains authoritative before publication. This validator is for
    already-public trusted bot comments and for dedup only.
    """

    if type(result) is not dict:
        raise PublicSiteProfileResultError("public terminal result must be an object")
    if type(execution_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", execution_sha):
        raise PublicSiteProfileResultError("invalid public terminal execution SHA")

    if result.get("status") != "pass":
        _strict_validate(result, execution_sha=execution_sha)
        return result

    columns = _column_list(result)
    if columns is None:
        _strict_validate(result, execution_sha=execution_sha)
        return result  # pragma: no cover - strict validator cannot accept this branch

    digest_presence = [VALUE_SET_DIGEST_FIELD in column for column in columns]
    if not digest_presence:
        raise PublicSiteProfileResultError("public PASS contains no columns")

    if all(digest_presence):
        # Backward compatibility for the one legacy trusted-main result already
        # present in Issue #281. New publication must use the redacted shape.
        _strict_validate(result, execution_sha=execution_sha)
        return result

    if any(digest_presence):
        raise PublicSiteProfileResultError(
            "public PASS mixes legacy hashed and redacted column shapes"
        )

    validation_copy = copy.deepcopy(result)
    validation_columns = _column_list(validation_copy)
    if validation_columns is None:  # pragma: no cover - copy preserves shape
        raise PublicSiteProfileResultError("public PASS column shape drifted")
    for column in validation_columns:
        column[VALUE_SET_DIGEST_FIELD] = _SYNTHETIC_VALIDATION_DIGEST

    _strict_validate(validation_copy, execution_sha=execution_sha)
    return result


def parse_trusted_public_terminal_result(
    body: object,
    *,
    execution_sha: str,
) -> bool:
    """Return whether a trusted comment is a valid terminal result for SHA."""

    if type(body) is not str or action.RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", execution_sha):
        raise PublicSiteProfileResultError("invalid requested execution SHA")
    if body.count(action.RESULT_MARKER) != 1:
        raise PublicSiteProfileResultError("public terminal result marker is malformed")
    before, after = body.split(action.RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise PublicSiteProfileResultError("public terminal result envelope is malformed")
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=action._pairs,
            parse_constant=action._reject_constant,
        )
    except (action.SiteModelProfileActionError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PublicSiteProfileResultError("public terminal result JSON is malformed") from exc
    if type(result) is not dict:
        raise PublicSiteProfileResultError("public terminal result fields drifted")
    result_execution_sha = result.get("execution_sha")
    if type(result_execution_sha) is not str or not re.fullmatch(
        r"[0-9a-f]{40}", result_execution_sha
    ):
        raise PublicSiteProfileResultError("public terminal result execution SHA is invalid")

    validate_public_terminal_result(result, execution_sha=result_execution_sha)
    return result_execution_sha == execution_sha


def has_terminal_site_profile_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded Issue #281 ledger is known."""

    if type(execution_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", execution_sha):
        raise PublicSiteProfileResultError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": action.CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = action.fetch_repository_comments(repository, token, **kwargs)
    except action.LedgerError as exc:
        raise PublicSiteProfileResultError("site-profile result ledger is incomplete") from exc

    for comment in comments:
        if type(comment) is not dict:
            raise PublicSiteProfileResultError("site-profile ledger contains a non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != action.TRUSTED_RESULT_LOGIN:
            continue
        if parse_trusted_public_terminal_result(
            comment.get("body"), execution_sha=execution_sha
        ):
            return True
    return False
