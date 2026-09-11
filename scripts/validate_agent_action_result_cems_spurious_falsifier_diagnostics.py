# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for CEMS Issue #835 diagnostics."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_spurious_falsifier_diagnostics as _worker
    from scripts import agent_action_protocol_cems_spurious_falsifier_diagnostics as _protocol
    from scripts import validate_agent_action_result_cems_spurious_support as _legacy
    from scripts.validate_agent_action_request_cems_spurious_falsifier_diagnostics import (
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION,
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID,
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover
    import acquire_cems_spurious_falsifier_diagnostics as _worker
    import agent_action_protocol_cems_spurious_falsifier_diagnostics as _protocol
    import validate_agent_action_result_cems_spurious_support as _legacy
    from validate_agent_action_request_cems_spurious_falsifier_diagnostics import (
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION,
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID,
        CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
_common = _legacy._legacy
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {
    CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION
}
_CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_FIELD = (
    "cems_europe_spurious_falsifier_diagnostics"
)
_CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_EVIDENCE_FIELDS = (
    _legacy._CEMS_SPURIOUS_SUPPORT_EVIDENCE_FIELDS
    - {_legacy._CEMS_SPURIOUS_SUPPORT_FIELD}
    | {_CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_FIELD}
)

_DIAGNOSTIC_RECEIPT_FIELDS = {
    "schema_version",
    "dataset_id",
    "source_issue",
    "release",
    "pyproj_version",
    "rp10_receipt",
    "spurious_depth_receipt",
    "derivation",
    "receipt_to_reader_binding",
    "external_bytes_persisted",
    "diagnostic_only",
    "small_channel_filter_reconstructed",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "model_use_authorized",
    "publication_authorized",
}


def validate_cems_spurious_falsifier_diagnostics(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _DIAGNOSTIC_RECEIPT_FIELDS:
        raise ResultError("CEMS #835 diagnostic receipt fields drifted")

    exact = {
        "schema_version": _worker.SCHEMA_VERSION,
        "dataset_id": CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID,
        "source_issue": CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE,
        "release": _legacy._rp10_profile.RELEASE,
        "pyproj_version": _worker.EXPECTED_PYPROJ_VERSION,
        "receipt_to_reader_binding": "verified_bytes_memoryfile",
        "external_bytes_persisted": False,
        "diagnostic_only": True,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS #835 diagnostic aggregate {field} drifted")

    rp10_receipt = _legacy._rp10_result.validate_cems_rp10_receipt(
        receipt["rp10_receipt"]
    )
    if (
        rp10_receipt["byte_count"] != _legacy._rp10_profile.ACCEPTED_BYTE_COUNT
        or rp10_receipt["sha256"] != _legacy._rp10_profile.ACCEPTED_SHA256
    ):
        raise ResultError("CEMS #835 RP10 receipt drifted from accepted #793 identity")

    spurious_receipt = _legacy._mask_result._validate_one(
        receipt["spurious_depth_receipt"],
        kind=_worker._stage_d_worker.SPURIOUS_KIND,
        filename=_worker._stage_d_worker.SPURIOUS_FILENAME,
    )
    accepted_mask = _legacy._mask_metadata.MASK_RECEIPTS[
        _worker._stage_d_worker.SPURIOUS_KIND
    ]
    if (
        spurious_receipt["byte_count"] != accepted_mask["byte_count"]
        or spurious_receipt["sha256"] != accepted_mask["sha256"]
    ):
        raise ResultError("CEMS #835 mask receipt drifted from accepted #809 identity")

    try:
        _worker._validate_derivation_result(receipt["derivation"])
    except _worker.CemsSpuriousFalsifierDiagnosticAcquisitionError as exc:
        raise ResultError(f"CEMS #835 bounded derivation is invalid: {exc}") from exc
    return receipt


def _validate_phase_d_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _common.REQUIRED_FIELDS:
        raise ResultError("CEMS #835 result fields drifted")
    if result["schema_version"] != _common.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")

    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _common.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _common.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION:
        raise ResultError("unsupported CEMS #835 action")

    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _common.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS #835 network result requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ISSUE:
        raise ResultError("CEMS #835 result is outside control issue 835")
    if result["dataset_id"] != CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_DATASET_ID:
        raise ResultError("CEMS #835 result is outside frozen dataset")

    try:
        expected_id = _protocol.semantic_request_id_from_result(result)
    except _protocol.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if semantic_id != expected_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _base._utc_second(result["started_at"], "started_at")
    finished = _base._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")

    phase, status = result["phase"], result["status"]
    if phase not in _common.ALLOWED_PHASES or status not in _common.ALLOWED_STATUSES:
        raise ResultError("unsupported CEMS #835 result state")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")

    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (
        type(duplicate_id) is not int or isinstance(duplicate_id, bool) or duplicate_id < 1
    ):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        return _legacy._rp10_result._validate_request_validation_state(
            result,
            status=status,
            duplicate_id=duplicate_id,
            failure_class=failure_class,
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS #835 network result requires acquisition_receipt phase")

    evidence = result["evidence"]
    if (
        type(evidence) is not dict
        or set(evidence) != _CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_EVIDENCE_FIELDS
    ):
        raise ResultError("CEMS #835 evidence fields drifted")
    for field in _common.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS #835 acquisition requires complete non-reused ledger state")

    aggregate = evidence[_CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS #835 acquisition cannot carry failure_class")
        aggregate = validate_cems_spurious_falsifier_diagnostics(aggregate)
        for field in ("rp10_receipt", "spurious_depth_receipt"):
            retrieved = _base._utc_second(
                aggregate[field]["retrieved_at"],
                f"{_CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_FIELD}.{field}.retrieved_at",
            )
            if retrieved < started or retrieved > finished:
                raise ResultError("CEMS #835 retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _common.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS #835 failure class is invalid")
        if aggregate is not None:
            raise ResultError("blocked CEMS #835 acquisition cannot publish diagnostic evidence")
    else:
        raise ResultError("duplicate CEMS #835 result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if (
        type(result) is dict
        and result.get("action") == CEMS_SPURIOUS_FALSIFIER_DIAGNOSTICS_ACTION
    ):
        return _validate_phase_d_result(result)
    return _legacy.validate_result(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    args = parser.parse_args(argv)
    raw = os.environ.get(args.result_env)
    if raw is None:
        print(f"missing environment variable: {args.result_env}", file=sys.stderr)
        return 2
    try:
        parsed = json.loads(raw)
        validated = validate_result(parsed)
    except (json.JSONDecodeError, ResultError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(validated, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
