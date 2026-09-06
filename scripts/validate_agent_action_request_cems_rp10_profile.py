# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend request validation for the trusted CEMS Europe RP10 metadata profile."""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request_cems_rp10 as _legacy
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import validate_agent_action_request_cems_rp10 as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_RP10_PROFILE_ACTION = "cems_europe_rp10_profile"
CEMS_RP10_PROFILE_ISSUE = 802
CEMS_RP10_PROFILE_DATASET_ID = _legacy.CEMS_RP10_RECEIPT_DATASET_ID
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_RP10_PROFILE_ACTION}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    """Validate the closed #802 profile action or delegate every earlier action."""
    if type(request) is not dict or request.get("action") != CEMS_RP10_PROFILE_ACTION:
        return _legacy.validate_request(request, expected_issue=expected_issue)

    issue = request.get("issue")
    if type(issue) is not int or issue != CEMS_RP10_PROFILE_ISSUE:
        raise RequestError("cems_europe_rp10_profile is restricted to integer issue 802")
    if request.get("dataset_id") != CEMS_RP10_PROFILE_DATASET_ID:
        raise RequestError(
            "cems_europe_rp10_profile is restricted to the frozen CEMS v3.1.1 dataset"
        )
    if expected_issue is not None and (
        type(expected_issue) is not int or expected_issue != CEMS_RP10_PROFILE_ISSUE
    ):
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    # Reuse the reviewed closed CEMS receipt request shape. Only internal fixed
    # values are substituted; the public request cannot select provider, URL,
    # filename, return period, reader, parser, or output scope.
    proxy = dict(request)
    proxy["action"] = _legacy.CEMS_RP10_RECEIPT_ACTION
    proxy["issue"] = _legacy.CEMS_RP10_RECEIPT_ISSUE
    proxy["dataset_id"] = _legacy.CEMS_RP10_RECEIPT_DATASET_ID
    _legacy.validate_request(proxy)
    return request


def main(argv: list[str] | None = None) -> int:
    original = _legacy.validate_request
    _legacy.validate_request = validate_request
    try:
        return _legacy.main(argv)
    finally:
        _legacy.validate_request = original


if __name__ == "__main__":
    raise SystemExit(main())
