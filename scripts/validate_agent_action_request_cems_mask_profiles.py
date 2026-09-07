# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend request validation for trusted CEMS companion-mask GeoTIFF profiles."""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request_cems_masks as _legacy
except ModuleNotFoundError:  # pragma: no cover
    import validate_agent_action_request_cems_masks as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_MASK_PROFILES_ACTION = "cems_europe_mask_profiles"
CEMS_MASK_PROFILES_ISSUE = 816
CEMS_MASK_PROFILES_DATASET_ID = _legacy.CEMS_MASK_RECEIPTS_DATASET_ID
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_MASK_PROFILES_ACTION}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    if type(request) is not dict or request.get("action") != CEMS_MASK_PROFILES_ACTION:
        return _legacy.validate_request(request, expected_issue=expected_issue)

    issue = request.get("issue")
    if type(issue) is not int or issue != CEMS_MASK_PROFILES_ISSUE:
        raise RequestError("cems_europe_mask_profiles is restricted to integer issue 816")
    if request.get("dataset_id") != CEMS_MASK_PROFILES_DATASET_ID:
        raise RequestError("cems_europe_mask_profiles is restricted to the frozen CEMS v3.1.1 dataset")
    if expected_issue is not None and (
        type(expected_issue) is not int or expected_issue != CEMS_MASK_PROFILES_ISSUE
    ):
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    proxy = dict(request)
    proxy["action"] = _legacy.CEMS_MASK_RECEIPTS_ACTION
    proxy["issue"] = _legacy.CEMS_MASK_RECEIPTS_ISSUE
    proxy["dataset_id"] = _legacy.CEMS_MASK_RECEIPTS_DATASET_ID
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
