# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend Agent Action request validation for the fixed CEMS Europe RP10 receipt.

All pre-existing requests delegate unchanged to the reviewed country-risk-aware
validator. This layer adds exactly one closed Issue #793 action. The request
cannot select provider, URL, filename, return period, parser, or output scope.
"""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request_country_risk as _legacy
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import validate_agent_action_request_country_risk as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_RP10_RECEIPT_ACTION = "cems_europe_rp10_receipt"
CEMS_RP10_RECEIPT_ISSUE = 793
CEMS_RP10_RECEIPT_DATASET_ID = (
    "ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026"
)
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_RP10_RECEIPT_ACTION}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    """Validate the fixed CEMS action or delegate every earlier action."""
    if type(request) is not dict or request.get("action") != CEMS_RP10_RECEIPT_ACTION:
        return _legacy.validate_request(request, expected_issue=expected_issue)

    if request.get("issue") != CEMS_RP10_RECEIPT_ISSUE:
        raise RequestError("cems_europe_rp10_receipt is restricted to issue 793")
    if request.get("dataset_id") != CEMS_RP10_RECEIPT_DATASET_ID:
        raise RequestError(
            "cems_europe_rp10_receipt is restricted to the frozen CEMS v3.1.1 dataset"
        )
    if expected_issue is not None and expected_issue != CEMS_RP10_RECEIPT_ISSUE:
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    # Reuse the already-reviewed common request shape. The proxy values are
    # internal constants only; no provider or network selector is accepted.
    proxy = dict(request)
    proxy["action"] = _legacy.ESRM20_COUNTRY_RISK_RECEIPT_ACTION
    proxy["issue"] = _legacy.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE
    proxy["dataset_id"] = _legacy.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID
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
