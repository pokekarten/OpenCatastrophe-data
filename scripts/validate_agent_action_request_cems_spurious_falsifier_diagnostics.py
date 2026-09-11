# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate the owner-only CEMS Issue #835 falsifier-diagnostic request."""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request_cems_spurious_support as _legacy
except ModuleNotFoundError:  # pragma: no cover
    import validate_agent_action_request_cems_spurious_support as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION = (
    "cems_europe_spurious_falsifier_diagnostics"
)
CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE = 835
CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID = (
    _legacy.CEMS_SPURIOUS_SUPPORT_DATASET_ID
)
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {
    CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION
}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    if (
        type(request) is not dict
        or request.get("action") != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION
    ):
        return _legacy.validate_request(request, expected_issue=expected_issue)

    issue = request.get("issue")
    if type(issue) is not int or issue != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE:
        raise RequestError(
            "cems_europe_spurious_falsifier_diagnostics is restricted to integer issue 835"
        )
    if request.get("dataset_id") != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID:
        raise RequestError(
            "cems_europe_spurious_falsifier_diagnostics is restricted to the frozen CEMS v3.1.1 dataset"
        )
    if expected_issue is not None and (
        type(expected_issue) is not int
        or expected_issue != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE
    ):
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    proxy = dict(request)
    proxy["action"] = _legacy.CEMS_SPURIOUS_SUPPORT_ACTION
    proxy["issue"] = _legacy.CEMS_SPURIOUS_SUPPORT_ISSUE
    proxy["dataset_id"] = _legacy.CEMS_SPURIOUS_SUPPORT_DATASET_ID
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
