# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted dispatcher layer for the fixed ESRM20 country-risk evidence chain.

The existing dispatcher remains authoritative for every pre-existing action.
This module monkey-patches only its extension points so Issue #778 can invoke
one closed action through the same request validation, complete ledger
deduplication, serialized workflow, and durable result contract.

The action first profiles immutable ESRM20 v1.0 ``Risk`` tree metadata. Provider
file bytes are requested only when the exact frozen country-risk path is a blob.
The same bounded in-process bytes are then bound to that exact Git blob, fed to
the already-reviewed offline schema profiler, and discarded; raw rows and
numeric values never enter the durable result.
"""

from __future__ import annotations

import hashlib
import sys
from typing import Any, Callable

try:
    from scripts import acquire_efehr_esrm20_country_risk_receipt as _country
    from scripts import agent_action_protocol_country_risk as _protocol
    from scripts import prepare_agent_action_result as _legacy
    from scripts import profile_esrm20_country_risk_schema as _schema
    from scripts import profile_esrm20_risk_v10_tree as _risk_tree
    from scripts import validate_agent_action_request_country_risk as _request
    from scripts import validate_agent_action_result_country_risk as _result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_country_risk_receipt as _country
    import agent_action_protocol_country_risk as _protocol
    import prepare_agent_action_result as _legacy
    import profile_esrm20_country_risk_schema as _schema
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
COUNTRY_RISK_SCHEMA_PROFILE_FIELD = _result._SCHEMA_FIELD
COUNTRY_RISK_GIT_BLOB_BINDING_FIELD = _result._BINDING_FIELD

_ORIGINAL_PREPARE_COMPLETED_RESULT = _legacy.prepare_completed_result
_ORIGINAL_RECEIPT_FIELD = _legacy._receipt_field


def _receipt_field(action: str) -> str:
    if action == ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return COUNTRY_RISK_RECEIPT_FIELD
    return _ORIGINAL_RECEIPT_FIELD(action)


def _git_blob_sha1(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise _result.ResultError("country-risk Git blob payload must be bytes")
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


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
    blob_binding: dict[str, Any] | None,
    schema_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build one result retaining every completed bounded evidence stage."""
    passed = (
        tree_profile is not None
        and tree_profile.get("country_risk_path_status") == "blob"
        and receipt is not None
        and blob_binding is not None
        and blob_binding.get("verified") is True
        and schema_profile is not None
        and schema_profile.get("trusted_source_receipt_bound") is True
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
            COUNTRY_RISK_GIT_BLOB_BINDING_FIELD: blob_binding,
            COUNTRY_RISK_SCHEMA_PROFILE_FIELD: schema_profile,
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
    country_risk_acquirer: Callable[[], tuple[dict[str, Any], bytes]] = (
        _country.acquire_country_risk_receipt_with_payload
    ),
    schema_profiler: Callable[..., dict[str, Any]] = (
        _schema.profile_country_risk_schema_bytes
    ),
    **kwargs: Any,
) -> dict[str, Any]:
    """Run tree gate, fixed byte receipt, Git-blob binding and schema profile."""
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
    blob_binding: dict[str, Any] | None = None
    schema_profile: dict[str, Any] | None = None
    try:
        tree_profile = _result.validate_esrm20_risk_v10_tree_profile(
            risk_tree_profiler()
        )
    except (_risk_tree.RiskTreeProfileError, _result.ResultError):
        print(
            "acquisition blocked: ESRM20 Risk tree metadata failed closed",
            file=sys.stderr,
        )
    else:
        if tree_profile["country_risk_path_status"] == "blob":
            payload: bytes | None = None
            try:
                acquired = country_risk_acquirer()
                if (
                    type(acquired) is not tuple
                    or len(acquired) != 2
                    or type(acquired[0]) is not dict
                    or type(acquired[1]) is not bytes
                ):
                    raise _country.Esrm20CountryRiskReceiptError(
                        "country-risk in-process acquisition shape drifted"
                    )
                receipt = _result.validate_esrm20_country_risk_receipt(acquired[0])
                payload = acquired[1]
                if (
                    len(payload) != receipt["byte_count"]
                    or hashlib.sha256(payload).hexdigest() != receipt["sha256"]
                ):
                    raise _result.ResultError(
                        "country-risk captured payload is not bound to receipt identity"
                    )
                country_entry = tree_profile["country_risk_path_entry"]
                payload_git_blob_sha1 = _git_blob_sha1(payload)
                if (
                    type(country_entry) is not dict
                    or payload_git_blob_sha1 != country_entry["object_sha1"]
                ):
                    raise _result.ResultError(
                        "country-risk captured payload does not match immutable Git blob"
                    )
                blob_binding = {
                    "schema_version": _result.COUNTRY_RISK_GIT_BLOB_BINDING_SCHEMA_VERSION,
                    "repository_path": receipt["repository_path"],
                    "tree_object_sha1": country_entry["object_sha1"],
                    "payload_git_blob_sha1": payload_git_blob_sha1,
                    "payload_byte_count": len(payload),
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                    "verified": True,
                }
                _result.validate_country_risk_git_blob_binding(
                    blob_binding, tree_profile, receipt
                )
                pure_schema_profile = _result.validate_esrm20_country_risk_schema_profile(
                    schema_profiler(
                        payload,
                        expected_sha256=receipt["sha256"],
                        expected_byte_count=receipt["byte_count"],
                    )
                )
                if pure_schema_profile["trusted_source_receipt_bound"] is not False:
                    raise _result.ResultError(
                        "pure country-risk schema profiler promoted source authority"
                    )
                _result.validate_schema_receipt_binding(pure_schema_profile, receipt)
                schema_profile = dict(pure_schema_profile)
                schema_profile["trusted_source_receipt_bound"] = True
            except (
                _country.Esrm20CountryRiskReceiptError,
                _schema.CountryRiskSchemaProfileError,
                _result.ResultError,
            ):
                blob_binding = None
                schema_profile = None
                print(
                    "acquisition blocked: ESRM20 country-risk byte/schema chain failed closed",
                    file=sys.stderr,
                )
            finally:
                payload = None
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
        blob_binding=blob_binding,
        schema_profile=schema_profile,
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
