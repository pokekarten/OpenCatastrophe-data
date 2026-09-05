# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted dispatcher extension for the fixed CEMS Europe RP10 receipt.

The existing country-risk-aware dispatcher remains authoritative for every
pre-existing action. This layer adds one closed Issue #793 network action to the
same request validation, complete issue-local ledger deduplication, serialized
workflow, and durable result contract.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_rp10_receipt as _cems
    from scripts import agent_action_protocol_cems_rp10 as _protocol
    from scripts import prepare_agent_action_result_country_risk as _country_prepare
    from scripts import validate_agent_action_request_cems_rp10 as _request
    from scripts import validate_agent_action_result_cems_rp10 as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_rp10_receipt as _cems
    import agent_action_protocol_cems_rp10 as _protocol
    import prepare_agent_action_result_country_risk as _country_prepare
    import validate_agent_action_request_cems_rp10 as _request
    import validate_agent_action_result_cems_rp10 as _result

for _name in dir(_country_prepare):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_country_prepare, _name)

_base = _country_prepare._legacy
CEMS_RP10_RECEIPT_ACTION = _request.CEMS_RP10_RECEIPT_ACTION
CEMS_RP10_RECEIPT_ISSUE = _request.CEMS_RP10_RECEIPT_ISSUE
CEMS_RP10_RECEIPT_DATASET_ID = _request.CEMS_RP10_RECEIPT_DATASET_ID
CEMS_RP10_RECEIPT_FIELD = _result._CEMS_FIELD


def _receipt_field(action: str) -> str:
    if action == CEMS_RP10_RECEIPT_ACTION:
        return CEMS_RP10_RECEIPT_FIELD
    return _country_prepare._receipt_field(action)


def prepare_completed_result(
    request: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    cems_acquirer: Callable[[], dict[str, Any]] = _cems.acquire_cems_rp10_receipt,
    **kwargs: Any,
) -> dict[str, Any]:
    """Deduplicate first, then run only the fixed CEMS worker for the CEMS action."""
    if request.get("action") != CEMS_RP10_RECEIPT_ACTION:
        return _country_prepare.prepare_completed_result(request, comments, **kwargs)

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
        raise _base.LedgerError(f"CEMS RP10 dispatcher inputs are incomplete: {sorted(missing)}")

    semantic_id = _protocol.semantic_request_id(
        request, kwargs["execution_sha"], kwargs["repository"]
    )
    duplicate_id = _base.find_existing_result(comments, semantic_id)
    if duplicate_id is not None:
        return _base.build_result(
            request,
            repository=kwargs["repository"],
            execution_sha=kwargs["execution_sha"],
            source_comment_id=kwargs["source_comment_id"],
            run_id=kwargs["run_id"],
            run_attempt=kwargs["run_attempt"],
            started_at=kwargs["started_at"],
            finished_at=_base.utc_now(),
            duplicate_result_comment_id=duplicate_id,
        )

    try:
        receipt = _result.validate_cems_rp10_receipt(cems_acquirer())
    except (_cems.CemsRp10ReceiptError, _result.ResultError):
        print("acquisition blocked: fixed CEMS RP10 receipt failed closed", file=sys.stderr)
        receipt = None

    return _base.build_acquisition_result(
        request,
        repository=kwargs["repository"],
        execution_sha=kwargs["execution_sha"],
        source_comment_id=kwargs["source_comment_id"],
        run_id=kwargs["run_id"],
        run_attempt=kwargs["run_attempt"],
        started_at=kwargs["started_at"],
        finished_at=_base.utc_now(),
        receipt=receipt,
    )


# Patch only the runtime extension points used by the existing dispatcher main().
_base.validate_request = _request.validate_request
_base.validate_result = _result.validate_result
_base.semantic_request_id = _protocol.semantic_request_id
_base.NETWORK_ACTIONS = _base.NETWORK_ACTIONS | {CEMS_RP10_RECEIPT_ACTION}
_base._receipt_field = _receipt_field
_base.prepare_completed_result = prepare_completed_result

NETWORK_ACTIONS = _base.NETWORK_ACTIONS
validate_request = _request.validate_request
validate_result = _result.validate_result
semantic_request_id = _protocol.semantic_request_id
ledger_issue_for_request = _base.ledger_issue_for_request
find_existing_result = _base.find_existing_result


def main(argv: list[str] | None = None) -> int:
    return _base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
