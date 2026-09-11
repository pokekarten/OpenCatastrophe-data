# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for CEMS Issue #823 Stage D."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_spurious_support_challenge as _worker
    from scripts import agent_action_protocol_cems_spurious_support as _protocol
    from scripts import challenge_cems_spurious_depth_support as _challenge
    from scripts import profile_cems_europe_mask_geotiffs as _mask_metadata
    from scripts import profile_cems_europe_rp10_geotiff as _rp10_profile
    from scripts import validate_agent_action_result_cems_mask_values as _legacy
    from scripts import validate_agent_action_result_cems_masks as _mask_result
    from scripts import validate_agent_action_result_cems_rp10 as _rp10_result
    from scripts.validate_agent_action_request_cems_spurious_support import (
        CEMS_SPURIOUS_SUPPORT_ACTION,
        CEMS_SPURIOUS_SUPPORT_DATASET_ID,
        CEMS_SPURIOUS_SUPPORT_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover
    import acquire_cems_spurious_support_challenge as _worker
    import agent_action_protocol_cems_spurious_support as _protocol
    import challenge_cems_spurious_depth_support as _challenge
    import profile_cems_europe_mask_geotiffs as _mask_metadata
    import profile_cems_europe_rp10_geotiff as _rp10_profile
    import validate_agent_action_result_cems_mask_values as _legacy
    import validate_agent_action_result_cems_masks as _mask_result
    import validate_agent_action_result_cems_rp10 as _rp10_result
    from validate_agent_action_request_cems_spurious_support import (
        CEMS_SPURIOUS_SUPPORT_ACTION,
        CEMS_SPURIOUS_SUPPORT_DATASET_ID,
        CEMS_SPURIOUS_SUPPORT_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_SPURIOUS_SUPPORT_ACTION}
_CEMS_SPURIOUS_SUPPORT_FIELD = "cems_europe_spurious_support_challenge"
_CEMS_SPURIOUS_SUPPORT_EVIDENCE_FIELDS = (
    _legacy._CEMS_MASK_VALUE_INVENTORIES_EVIDENCE_FIELDS
    - {_legacy._CEMS_MASK_VALUE_INVENTORIES_FIELD}
    | {_CEMS_SPURIOUS_SUPPORT_FIELD}
)

_STAGE_D_FIELDS = {
    "schema_version",
    "dataset_id",
    "source_issue",
    "release",
    "rp10_receipt",
    "spurious_depth_receipt",
    "challenge",
    "receipt_to_reader_binding",
    "external_bytes_persisted",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "model_use_authorized",
    "publication_authorized",
}
_CHALLENGE_FIELDS = {
    "schema_version",
    "candidate_support_rule",
    "rp10_seed_rule",
    "candidate_support_cells",
    "rp10_seed_cells",
    "same_cell_candidate_seed_overlap_cells",
    "candidate_with_seed_within_threshold_cells",
    "candidate_farther_than_threshold_cells",
    "verdict",
    "distance_model",
    "base_distance_metres",
    "north_cell_diagonal_metres",
    "south_cell_diagonal_metres",
    "cell_diagonal_tolerance_metres",
    "distance_threshold_metres",
    "max_row_offset",
    "max_col_offset",
    "pyproj_version",
    "small_channel_filter_reconstructed",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "model_use_authorized",
    "publication_authorized",
    "external_bytes_persisted",
}

# Frozen from the exact #816 grid and pyproj 3.7.2 / WGS84 Geod before Stage-D
# provider execution. These are geometry-derived, not outcome-derived tolerances.
_EXPECTED_NORTH_DIAGONAL_METRES = 97.7271662395491
_EXPECTED_SOUTH_DIAGONAL_METRES = 123.57396725799528
_EXPECTED_TOLERANCE_METRES = 123.57396725799528
_EXPECTED_DISTANCE_THRESHOLD_METRES = 2123.5739672579953
_EXPECTED_MAX_ROW_OFFSET = 23
_EXPECTED_MAX_COL_OFFSET = 71
_EXPECTED_PYPROJ_VERSION = "3.7.2"
_FLOAT_ABS_TOL = 1e-9


def _nonnegative_int(value: Any, field: str) -> int:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise ResultError(f"{field} must be a non-negative integer")
    return value


def _finite_float(value: Any, field: str) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ResultError(f"{field} must be finite numeric metadata")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ResultError(f"{field} must be finite numeric metadata")
    return numeric


def _require_close(value: Any, expected: float, field: str) -> None:
    numeric = _finite_float(value, field)
    if not math.isclose(numeric, expected, rel_tol=0.0, abs_tol=_FLOAT_ABS_TOL):
        raise ResultError(f"{field} drifted from preregistered Stage-D geometry")


def validate_cems_spurious_support_challenge(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _STAGE_D_FIELDS:
        raise ResultError("CEMS Stage-D aggregate fields drifted")

    exact = {
        "schema_version": _worker.SCHEMA_VERSION,
        "dataset_id": CEMS_SPURIOUS_SUPPORT_DATASET_ID,
        "source_issue": CEMS_SPURIOUS_SUPPORT_ISSUE,
        "release": _rp10_profile.RELEASE,
        "receipt_to_reader_binding": "verified_bytes_memoryfile",
        "external_bytes_persisted": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS Stage-D aggregate {field} drifted from frozen authority")

    rp10_receipt = _rp10_result.validate_cems_rp10_receipt(receipt["rp10_receipt"])
    if (
        rp10_receipt["byte_count"] != _rp10_profile.ACCEPTED_BYTE_COUNT
        or rp10_receipt["sha256"] != _rp10_profile.ACCEPTED_SHA256
    ):
        raise ResultError("CEMS Stage-D RP10 receipt drifted from accepted #793 identity")

    spurious_receipt = _mask_result._validate_one(
        receipt["spurious_depth_receipt"],
        kind=_worker.SPURIOUS_KIND,
        filename=_worker.SPURIOUS_FILENAME,
    )
    accepted_mask = _mask_metadata.MASK_RECEIPTS[_worker.SPURIOUS_KIND]
    if (
        spurious_receipt["byte_count"] != accepted_mask["byte_count"]
        or spurious_receipt["sha256"] != accepted_mask["sha256"]
    ):
        raise ResultError("CEMS Stage-D mask receipt drifted from accepted #809 identity")

    challenge = receipt["challenge"]
    if type(challenge) is not dict or set(challenge) != _CHALLENGE_FIELDS:
        raise ResultError("CEMS Stage-D challenge fields drifted")

    challenge_exact = {
        "schema_version": _challenge.SCHEMA_VERSION,
        "candidate_support_rule": "finite_value_exactly_1",
        "rp10_seed_rule": "finite_depth_strictly_gt_10_m",
        "candidate_support_cells": _worker.EXPECTED_CANDIDATE_SUPPORT_CELLS,
        "distance_model": "WGS84_GEOD",
        "base_distance_metres": 2000.0,
        "max_row_offset": _EXPECTED_MAX_ROW_OFFSET,
        "max_col_offset": _EXPECTED_MAX_COL_OFFSET,
        "pyproj_version": _EXPECTED_PYPROJ_VERSION,
        "small_channel_filter_reconstructed": False,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
    for field, expected in challenge_exact.items():
        if type(challenge[field]) is not type(expected) or challenge[field] != expected:
            raise ResultError(f"CEMS Stage-D challenge {field} drifted from frozen contract")

    _require_close(
        challenge["north_cell_diagonal_metres"],
        _EXPECTED_NORTH_DIAGONAL_METRES,
        "challenge.north_cell_diagonal_metres",
    )
    _require_close(
        challenge["south_cell_diagonal_metres"],
        _EXPECTED_SOUTH_DIAGONAL_METRES,
        "challenge.south_cell_diagonal_metres",
    )
    _require_close(
        challenge["cell_diagonal_tolerance_metres"],
        _EXPECTED_TOLERANCE_METRES,
        "challenge.cell_diagonal_tolerance_metres",
    )
    _require_close(
        challenge["distance_threshold_metres"],
        _EXPECTED_DISTANCE_THRESHOLD_METRES,
        "challenge.distance_threshold_metres",
    )

    candidate = _worker.EXPECTED_CANDIDATE_SUPPORT_CELLS
    seeds = _nonnegative_int(challenge["rp10_seed_cells"], "challenge.rp10_seed_cells")
    same = _nonnegative_int(
        challenge["same_cell_candidate_seed_overlap_cells"],
        "challenge.same_cell_candidate_seed_overlap_cells",
    )
    within = _nonnegative_int(
        challenge["candidate_with_seed_within_threshold_cells"],
        "challenge.candidate_with_seed_within_threshold_cells",
    )
    farther = _nonnegative_int(
        challenge["candidate_farther_than_threshold_cells"],
        "challenge.candidate_farther_than_threshold_cells",
    )
    if not (0 <= same <= within <= candidate and seeds >= same):
        raise ResultError("CEMS Stage-D aggregate counts do not reconcile")
    if within + farther != candidate:
        raise ResultError("CEMS Stage-D covered/farther counts do not reconcile")

    expected_verdict = (
        "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION"
        if farther == 0
        else "CURRENT_RP10_NECESSARY_CONDITION_FAIL"
    )
    if challenge["verdict"] != expected_verdict:
        raise ResultError("CEMS Stage-D verdict violates zero-tolerance preregistration")
    return receipt


def _validate_stage_d_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS Stage-D result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")

    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_SPURIOUS_SUPPORT_ACTION:
        raise ResultError("unsupported CEMS Stage-D action")

    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS Stage-D network result requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_SPURIOUS_SUPPORT_ISSUE:
        raise ResultError("CEMS Stage-D result is outside control issue 823")
    if result["dataset_id"] != CEMS_SPURIOUS_SUPPORT_DATASET_ID:
        raise ResultError("CEMS Stage-D result is outside frozen dataset")

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
    if phase not in _legacy.ALLOWED_PHASES or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported CEMS Stage-D result state")
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
        return _rp10_result._validate_request_validation_state(
            result,
            status=status,
            duplicate_id=duplicate_id,
            failure_class=failure_class,
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS Stage-D network result requires acquisition_receipt phase")

    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CEMS_SPURIOUS_SUPPORT_EVIDENCE_FIELDS:
        raise ResultError("CEMS Stage-D evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS Stage-D acquisition requires complete non-reused ledger state")

    aggregate = evidence[_CEMS_SPURIOUS_SUPPORT_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS Stage-D acquisition cannot carry failure_class")
        aggregate = validate_cems_spurious_support_challenge(aggregate)
        for field in ("rp10_receipt", "spurious_depth_receipt"):
            retrieved = _base._utc_second(
                aggregate[field]["retrieved_at"],
                f"{_CEMS_SPURIOUS_SUPPORT_FIELD}.{field}.retrieved_at",
            )
            if retrieved < started or retrieved > finished:
                raise ResultError("CEMS Stage-D retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS Stage-D failure class is invalid")
        if aggregate is not None:
            raise ResultError("blocked CEMS Stage-D acquisition cannot publish challenge evidence")
    else:
        raise ResultError("duplicate CEMS Stage-D result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == CEMS_SPURIOUS_SUPPORT_ACTION:
        return _validate_stage_d_result(result)
    return _legacy.validate_result(result)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.result_env not in os.environ:
        print("BLOCKED: result environment variable is absent", file=sys.stderr)
        return 2
    try:
        result = validate_result(_base._strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
