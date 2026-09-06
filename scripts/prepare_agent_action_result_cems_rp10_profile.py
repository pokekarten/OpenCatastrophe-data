# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted dispatcher extension for the receipt-bound CEMS Europe RP10 profile."""

from __future__ import annotations

import sys
from typing import Any, Callable

try:
    from scripts import agent_action_protocol_cems_rp10_profile as _protocol
    from scripts import prepare_agent_action_result_cems_rp10 as _legacy
    from scripts import validate_agent_action_request_cems_rp10_profile as _request
    from scripts import validate_agent_action_result_cems_rp10_profile as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import agent_action_protocol_cems_rp10_profile as _protocol
    import prepare_agent_action_result_cems_rp10 as _legacy
    import validate_agent_action_request_cems_rp10_profile as _request
    import validate_agent_action_result_cems_rp10_profile as _result

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
CEMS_RP10_PROFILE_ACTION = _request.CEMS_RP10_PROFILE_ACTION
CEMS_RP10_PROFILE_ISSUE = _request.CEMS_RP10_PROFILE_ISSUE
CEMS_RP10_PROFILE_DATASET_ID = _request.CEMS_RP10_PROFILE_DATASET_ID
CEMS_RP10_PROFILE_FIELD = _result._CEMS_PROFILE_FIELD


def _receipt_field(action: str) -> str:
    if action == CEMS_RP10_PROFILE_ACTION:
        return CEMS_RP10_PROFILE_FIELD
    return _legacy._receipt_field(action)


def _closed_profile_failure_stage(error: BaseException) -> str:
    message = str(error)
    if "accepted #793 receipt" in message:
        return "receipt_binding"
    if "GeoTIFF metadata profile failed" in message:
        return "geotiff_profile"
    if "ephemeral" in message:
        return "ephemeral_storage"
    if "deadline" in message:
        return "deadline"
    return "unknown"


def prepare_completed_result(
    request: dict[str, Any],
    comments: list[dict[str, Any]],
    *,
    profile_acquirer: Callable[[], dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Deduplicate first, then run only the closed #802 trusted profile worker."""
    if request.get("action") != CEMS_RP10_PROFILE_ACTION:
        return _legacy.prepare_completed_result(request, comments, **kwargs)

    required = {
        "repository", "execution_sha", "source_comment_id", "run_id",
        "run_attempt", "started_at",
    }
    missing = required - set(kwargs)
    if missing:
        raise _base.LedgerError(
            f"CEMS RP10 profile dispatcher inputs are incomplete: {sorted(missing)}"
        )

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
        if profile_acquirer is None:
            try:
                from scripts import acquire_cems_europe_rp10_profile as _worker
            except ModuleNotFoundError:  # pragma: no cover - direct script import path
                import acquire_cems_europe_rp10_profile as _worker
            profile_acquirer = _worker.acquire_and_profile_cems_rp10
        receipt = _result.validate_cems_rp10_profile_receipt(profile_acquirer())
    except _result.ResultError:
        print("CEMS_RP10_PROFILE_FAILURE_STAGE=result_validation", file=sys.stderr, flush=True)
        receipt = None
    except Exception as exc:
        # Provider/library details never enter the durable receipt or trusted log.
        # Expected worker failures are classified only into a small closed stage set.
        stage = _closed_profile_failure_stage(exc)
        print(f"CEMS_RP10_PROFILE_FAILURE_STAGE={stage}", file=sys.stderr, flush=True)
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


# Patch only the reviewed dispatcher extension points used by main().
_base.validate_request = _request.validate_request
_base.validate_result = _result.validate_result
_base.semantic_request_id = _protocol.semantic_request_id
_base.NETWORK_ACTIONS = _base.NETWORK_ACTIONS | {CEMS_RP10_PROFILE_ACTION}
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
