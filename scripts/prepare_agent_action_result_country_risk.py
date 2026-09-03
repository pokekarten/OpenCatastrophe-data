# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted dispatcher layer for the fixed ESRM20 country-risk byte receipt.

The existing dispatcher remains authoritative for every pre-existing action.
This module monkey-patches only its extension points so Issue #778 can invoke
one already-reviewed fixed worker through the same request validation, complete
ledger deduplication, serialized workflow, and durable result contract.

The country-risk action first profiles the immutable ESRM20 v1.0 ``Risk`` tree
from trusted main. Provider file bytes are requested only when the exact frozen
``Risk/European_Risk_Country.csv`` path is proven to be a blob.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

try:
    from scripts import acquire_efehr_esrm20_country_risk_receipt as _country
    from scripts import agent_action_protocol_country_risk as _protocol
    from scripts import prepare_agent_action_result as _legacy
    from scripts import profile_esrm20_risk_v10_tree as _risk_tree
    from scripts import validate_agent_action_request_country_risk as _request
    from scripts import validate_agent_action_result_country_risk as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_country_risk_receipt as _country
    import agent_action_protocol_country_risk as _protocol
    import prepare_agent_action_result as _legacy
    import profile_esrm20_risk_v10_tree as _risk_tree
    import validate_agent_action_request_country_risk as _request
    import validate_agent_action_result_country_risk as _result

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

ESRM20_COUNTRY_RISK_RECEIPT_ACTION = _request.ESRM20_COUNTRY_RISK_RECEIPT_ACTION
ESRM20_COUNTRY_RISK_RECEIPT_ISSUE = _request.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE
ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID = _request.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID
COUNTRY_RISK_RECEIPT_FIELD = _result._COUNTRY_FIELD
RISK_TREE_PROFILE_FIELD = _result._TREE_FIELD

_ORIGINAL_PREPARE_COMPLETED_RESULT = _legacy.prepare_completed_result
_ORIGINAL_RECEIPT_FIELD = _legacy._receipt_field


def _receipt_field(action: str) -> str:
    if action == ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return COUNTRY_RISK_RECEIPT_FIELD
    return _ORIGINAL_RECEIPT_FIELD(action)


def _build_country_risk_acquisition_result(
    request: dict[str, Any],
    *,
    repository: str,
    execution_sha: str,
    source_comment_id: int,
    run_id: int,
    run_attempt: int,
    started_at: str,
    finished_at: str,
    tree_profile: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build one result retaining the metadata precondition even when blocked."""
    passed = (
        tree_profile is not None
        and tree_profile.get("country_risk_path_status") == "blob"
        and receipt is not None
    )
    result = {
        "schema_version": _legacy.RESULT_SCHEMA_VERSION,
        "semantic_request_id": _legacy.semantic_request_id(
            request, execution_sha, repository
        ),
        "repository": repository,
        "action": request["action"],
        "source_issue": request["issue"],
        "source_comment_id": source_comment_id,
        "target_sha": request["target_sha"],
        "dataset_id": request["dataset_id"],
        "execution_sha": execution_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "started_at": started_at,
        "finished_at": finished_at,
        "phase": "acquisition_receipt",
        "status": "pass" if passed else "blocked",
        "external_bytes_persisted": False,
        "evidence": {
            "request_validated": True,
            "ledger_scan_complete": True,
            "prior_result_reused": False,
            RISK_TREE_PROFILE_FIELD: tree_profile,
            COUNTRY_RISK_RECEIPT_FIELD: receipt,
        },
        "duplicate_result_comment_id": None,
        "failure_class": None if passed else _legacy.ACQUISITION_FAILURE_CLASS,
    }
    return _result.validate_result(result)


def prepare_completed_result(
    request: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    risk_tree_profiler: Callable[[], dict[str, Any]] = _risk_tree.profile_v10_tree,
    country_risk_acquirer: Callable[[], dict[str, Any]] = _country.acquire_country_risk_receipt,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run metadata precondition then fixed byte receipt, or delegate unchanged."""
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

    tree_profile: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    try:
        tree_profile = _result.validate_esrm20_risk_v10_tree_profile(
            risk_tree_profiler()
        )
    except (_risk_tree.RiskTreeProfileError, _result.ResultError):
        # Keep provider/network diagnostics out of the durable comment and log.
        print(
            "acquisition blocked: ESRM20 Risk tree metadata failed closed",
            file=sys.stderr,
        )
    else:
        if tree_profile["country_risk_path_status"] == "blob":
            try:
                receipt = country_risk_acquirer()
            except _country.Esrm20CountryRiskReceiptError:
                print(
                    "acquisition blocked: ESRM20 country-risk receipt acquisition failed closed",
                    file=sys.stderr,
                )
        else:
            print(
                "acquisition blocked: ESRM20 country-risk path is not a blob",
                file=sys.stderr,
            )

    return _build_country_risk_acquisition_result(
        request,
        repository=kwargs["repository"],
        execution_sha=kwargs["execution_sha"],
        source_comment_id=kwargs["source_comment_id"],
        run_id=kwargs["run_id"],
        run_attempt=kwargs["run_attempt"],
        started_at=kwargs["started_at"],
        finished_at=_legacy.utc_now(),
        tree_profile=tree_profile,
        receipt=receipt,
    )


# Patch only runtime extension points used by the existing dispatcher main().
_legacy.validate_request = _request.validate_request
_legacy.validate_result = _result.validate_result
_legacy.semantic_request_id = _protocol.semantic_request_id
_legacy.NETWORK_ACTIONS = _legacy.NETWORK_ACTIONS | {ESRM20_COUNTRY_RISK_RECEIPT_ACTION}
_legacy._receipt_field = _receipt_field
_legacy.prepare_completed_result = prepare_completed_result

NETWORK_ACTIONS = _legacy.NETWORK_ACTIONS
validate_request = _request.validate_request
validate_result = _result.validate_result
semantic_request_id = _protocol.semantic_request_id


def main(argv: list[str] | None = None) -> int:
    return _legacy.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
