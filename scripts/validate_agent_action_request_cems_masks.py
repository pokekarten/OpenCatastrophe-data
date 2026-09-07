# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend request validation for the two fixed CEMS v3.1.1 companion masks."""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request_cems_rp10_profile as _legacy
except ModuleNotFoundError:  # pragma: no cover
    import validate_agent_action_request_cems_rp10_profile as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_MASK_RECEIPTS_ACTION = "cems_europe_mask_receipts"
CEMS_MASK_RECEIPTS_ISSUE = 809
CEMS_MASK_RECEIPTS_DATASET_ID = _legacy.CEMS_RP10_PROFILE_DATASET_ID
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_MASK_RECEIPTS_ACTION}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    if type(request) is not dict or request.get("action") != CEMS_MASK_RECEIPTS_ACTION:
        return _legacy.validate_request(request, expected_issue=expected_issue)

    issue = request.get("issue")
    if type(issue) is not int or issue != CEMS_MASK_RECEIPTS_ISSUE:
        raise RequestError("cems_europe_mask_receipts is restricted to integer issue 809")
    if request.get("dataset_id") != CEMS_MASK_RECEIPTS_DATASET_ID:
        raise RequestError("cems_europe_mask_receipts is restricted to the frozen CEMS v3.1.1 dataset")
    if expected_issue is not None and (
        type(expected_issue) is not int or expected_issue != CEMS_MASK_RECEIPTS_ISSUE
    ):
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    # Reuse the already-closed profile request shape. Public requests therefore
    # cannot select either mask filename, URL, provider, parser, reader or output.
    proxy = dict(request)
    proxy["action"] = _legacy.CEMS_RP10_PROFILE_ACTION
    proxy["issue"] = _legacy.CEMS_RP10_PROFILE_ISSUE
    proxy["dataset_id"] = _legacy.CEMS_RP10_PROFILE_DATASET_ID
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
