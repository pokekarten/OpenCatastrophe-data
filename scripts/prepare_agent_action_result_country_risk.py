# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted dispatcher layer for the fixed ESRM20 country-risk byte receipt.

The existing dispatcher remains authoritative for every pre-existing action.
This module monkey-patches only its extension points so Issue #778 can invoke
one already-reviewed fixed worker through the same request validation, complete
ledger deduplication, serialized workflow, and durable result contract.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

try:
    from scripts import acquire_efehr_esrm20_country_risk_receipt as _country
    from scripts import prepare_agent_action_result as _legacy
    from scripts import validate_agent_action_request_country_risk as _request
    from scripts import validate_agent_action_result_country_risk as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_country_risk_receipt as _country
    import prepare_agent_action_result as _legacy
    import validate_agent_action_request_country_risk as _request
    import validate_agent_action_result_country_risk as _result

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

ESRM20_COUNTRY_RISK_RECEIPT_ACTION = _request.ESRM20_COUNTRY_RISK_RECEIPT_ACTION
ESRM20_COUNTRY_RISK_RECEIPT_ISSUE = _request.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE
ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID = _request.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID
COUNTRY_RISK_RECEIPT_FIELD = _result._COUNTRY_FIELD

_ORIGINAL_PREPARE_COMPLETED_RESULT = _legacy.prepare_completed_result
_ORIGINAL_RECEIPT_FIELD = _legacy._receipt_field


def _receipt_field(action: str) -> str:
    if action == ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return COUNTRY_RISK_RECEIPT_FIELD
    return _ORIGINAL_RECEIPT_FIELD(action)


def prepare_completed_result(
    request: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    country_risk_acquirer: Callable[[], dict[str, Any]] = _country.acquire_country_risk_receipt,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the fixed country-risk worker or delegate all existing actions unchanged."""
    if request.get("action") != ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return _ORIGINAL_PREPARE_COMPLETED_RESULT(request, comments, **kwargs)

    required = {
        "repository",
        "execution_sha",
        "source_comment_id",
        "run_id",
        "run_attempt",
        "started_at",
    }
    missing = required - set(kwargs)
    if missing:
        raise _legacy.LedgerError(
            f"country-risk dispatcher inputs are incomplete: {sorted(missing)}"
        )

    semantic_id = _legacy.semantic_request_id(
        request, kwargs["execution_sha"], kwargs["repository"]
    )
    duplicate_id = _legacy.find_existing_result(comments, semantic_id)
    if duplicate_id is not None:
        return _legacy.build_result(
            request,
            repository=kwargs["repository"],
            execution_sha=kwargs["execution_sha"],
            source_comment_id=kwargs["source_comment_id"],
            run_id=kwargs["run_id"],
            run_attempt=kwargs["run_attempt"],
            started_at=kwargs["started_at"],
            finished_at=_legacy.utc_now(),
            duplicate_result_comment_id=duplicate_id,
        )

    try:
        receipt = country_risk_acquirer()
    except _country.Esrm20CountryRiskReceiptError:
        # Keep provider/network diagnostics out of the durable comment and log.
        print(
            "acquisition blocked: ESRM20 country-risk receipt acquisition failed closed",
            file=sys.stderr,
        )
        receipt = None

    return _legacy.build_acquisition_result(
        request,
        repository=kwargs["repository"],
        execution_sha=kwargs["execution_sha"],
        source_comment_id=kwargs["source_comment_id"],
        run_id=kwargs["run_id"],
        run_attempt=kwargs["run_attempt"],
        started_at=kwargs["started_at"],
        finished_at=_legacy.utc_now(),
        receipt=receipt,
    )


# Patch only runtime extension points used by the existing dispatcher main().
_legacy.validate_request = _request.validate_request
_legacy.validate_result = _result.validate_result
_legacy.NETWORK_ACTIONS = _legacy.NETWORK_ACTIONS | {ESRM20_COUNTRY_RISK_RECEIPT_ACTION}
_legacy._receipt_field = _receipt_field
_legacy.prepare_completed_result = prepare_completed_result

NETWORK_ACTIONS = _legacy.NETWORK_ACTIONS
validate_request = _request.validate_request
validate_result = _result.validate_result


def main(argv: list[str] | None = None) -> int:
    return _legacy.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
