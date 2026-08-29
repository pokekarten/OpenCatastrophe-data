# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend Agent Action request validation for the fixed ESRM20 country-risk receipt.

All pre-existing requests delegate unchanged to the reviewed request validator.
This layer adds exactly one closed Issue #778 action. The request still cannot
select provider, project, commit, repository path, URL, parser, or output scope.
"""

from __future__ import annotations

from typing import Any

try:
    from scripts import validate_agent_action_request as _legacy
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import validate_agent_action_request as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

ESRM20_COUNTRY_RISK_RECEIPT_ACTION = "esrm20_country_risk_receipt"
ESRM20_COUNTRY_RISK_RECEIPT_ISSUE = 778
ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {ESRM20_COUNTRY_RISK_RECEIPT_ACTION}


def validate_request(
    request: dict[str, Any], *, expected_issue: int | None = None
) -> dict[str, Any]:
    """Validate the fixed country-risk action or delegate all legacy actions."""
    if type(request) is not dict or request.get("action") != ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return _legacy.validate_request(request, expected_issue=expected_issue)

    if request.get("issue") != ESRM20_COUNTRY_RISK_RECEIPT_ISSUE:
        raise RequestError("esrm20_country_risk_receipt is restricted to issue 778")
    if request.get("dataset_id") != ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID:
        raise RequestError(
            "esrm20_country_risk_receipt is restricted to the frozen ESRM20 risk-input dataset"
        )
    if expected_issue is not None and expected_issue != ESRM20_COUNTRY_RISK_RECEIPT_ISSUE:
        raise RequestError("request issue does not match triggering GitHub issue/PR")

    # Reuse the canonical common-field validation by validating an equivalent
    # already-reviewed fixed ESRM20 risk-input request. Only the closed action
    # and control issue differ; neither is caller-selectable after the checks above.
    proxy = dict(request)
    proxy["action"] = _legacy.ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION
    proxy["issue"] = _legacy.ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ISSUE
    _legacy.validate_request(proxy)
    return request


def main(argv: list[str] | None = None) -> int:
    # The trusted dispatcher imports this validator; direct CLI execution is not
    # needed for the workflow and would otherwise call the legacy module global.
    return _legacy.main(argv)
