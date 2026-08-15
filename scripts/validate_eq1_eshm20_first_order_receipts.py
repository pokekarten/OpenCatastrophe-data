# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Reduce the trusted #361 ESHM20 first-order PASS to consumer-safe identities.

This is an offline bridge over an already-trusted Agent Action result. It first
runs the merged canonical result validator and then binds the exact trusted
execution plus the three byte identities recorded by Issue #361 PASS comment
5301858821. The projection deliberately carries no provider URLs, payloads,
model semantics, dependency-closure authority, or model-use authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from scripts import acquire_eshm20_first_order_receipts as receipt_authority
    from scripts import validate_agent_action_result as canonical_result
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_eshm20_first_order_receipts as receipt_authority
    import validate_agent_action_result as canonical_result


SOURCE_ISSUE = 361
TRUSTED_RESULT_COMMENT_ID = 5301858821
TRUSTED_SOURCE_COMMENT_ID = 5301857400
TRUSTED_RUN_ID = 31880089623
TRUSTED_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
ACTION = "efehr_eshm20_first_order_receipts"
DATASET_ID = "efehr.eshm20"
PHASE = "acquisition_receipt"
STATUS = "pass"


@dataclass(frozen=True)
class _TrustedArtifact:
    role: str
    repository_path: str
    parent_section: str
    parent_option: str
    byte_count: int
    sha256: str


_TRUSTED_ARTIFACTS: tuple[_TrustedArtifact, ...] = (
    _TrustedArtifact(
        role="site_model",
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "eshm20_site_model_v06d.csv"
        ),
        parent_section="site_params",
        parent_option="site_model_file",
        byte_count=3_873_324,
        sha256="d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529",
    ),
    _TrustedArtifact(
        role="gmm_logic_tree",
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "gmpe_complete_logic_tree_5br.xml"
        ),
        parent_section="calculation",
        parent_option="gsim_logic_tree_file",
        byte_count=33_760,
        sha256="e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62",
    ),
    _TrustedArtifact(
        role="source_model_logic_tree",
        repository_path=(
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "source_model_logic_tree_eshm20_model_v12e.xml"
        ),
        parent_section="calculation",
        parent_option="source_model_logic_tree_file",
        byte_count=17_579,
        sha256="97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
    ),
)


class Eq1FirstOrderBridgeError(ValueError):
    """Raised when trusted first-order receipt evidence drifts or widens."""


def _exact(value: object, expected: object, field: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise Eq1FirstOrderBridgeError(f"{field} does not match trusted #361 evidence")


def validate_and_reduce(result: Any) -> dict[str, object]:
    """Validate one canonical #361 PASS and return a bounded identity projection."""

    try:
        validated = canonical_result.validate_result(result)
    except canonical_result.ResultError as exc:
        raise Eq1FirstOrderBridgeError("canonical Agent Action result validation failed") from exc

    _exact(validated["action"], ACTION, "action")
    _exact(validated["source_issue"], SOURCE_ISSUE, "source_issue")
    _exact(validated["source_comment_id"], TRUSTED_SOURCE_COMMENT_ID, "source_comment_id")
    _exact(validated["run_id"], TRUSTED_RUN_ID, "run_id")
    _exact(validated["execution_sha"], TRUSTED_EXECUTION_SHA, "execution_sha")
    _exact(validated["target_sha"], TRUSTED_EXECUTION_SHA, "target_sha")
    _exact(validated["dataset_id"], DATASET_ID, "dataset_id")
    _exact(validated["phase"], PHASE, "phase")
    _exact(validated["status"], STATUS, "status")
    _exact(validated["external_bytes_persisted"], False, "external_bytes_persisted")

    evidence = validated["evidence"]
    if type(evidence) is not dict:
        raise Eq1FirstOrderBridgeError("validated evidence is not an object")
    _exact(evidence["ledger_scan_complete"], True, "ledger_scan_complete")
    _exact(evidence["prior_result_reused"], False, "prior_result_reused")
    _exact(evidence["request_validated"], True, "request_validated")

    receipt_set = evidence[ACTION]
    if type(receipt_set) is not dict:
        raise Eq1FirstOrderBridgeError("first-order receipt set is not an object")
    exact_receipt_set_fields = {
        "schema_version": receipt_authority.SCHEMA_VERSION,
        "operation_id": receipt_authority.OPERATION_ID,
        "control_issue": receipt_authority.CONTROL_ISSUE,
        "source_issue": receipt_authority.SOURCE_ISSUE,
        "dataset_id": receipt_authority.DATASET_ID,
        "project_id": receipt_authority.PROJECT_ID,
        "project_path": receipt_authority.PROJECT_PATH,
        "commit_sha": receipt_authority.COMMIT_SHA,
        "selection_request_comment_id": receipt_authority.SELECTION_REQUEST_COMMENT_ID,
        "selection_result_comment_id": receipt_authority.SELECTION_RESULT_COMMENT_ID,
        "selection_run_id": receipt_authority.SELECTION_RUN_ID,
        "selection_execution_sha": receipt_authority.SELECTION_EXECUTION_SHA,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_receipt_set_fields.items():
        _exact(receipt_set[field], expected, f"receipt_set.{field}")

    receipts = receipt_set["receipts"]
    if type(receipts) is not list or len(receipts) != len(_TRUSTED_ARTIFACTS):
        raise Eq1FirstOrderBridgeError("trusted receipt set must contain exactly three artifacts")

    reduced_artifacts: list[dict[str, object]] = []
    for index, (receipt, expected) in enumerate(zip(receipts, _TRUSTED_ARTIFACTS, strict=True)):
        if type(receipt) is not dict:
            raise Eq1FirstOrderBridgeError(f"receipt[{index}] is not an object")
        exact_fields = {
            "source_issue": receipt_authority.SOURCE_ISSUE,
            "dataset_id": receipt_authority.DATASET_ID,
            "project_id": receipt_authority.PROJECT_ID,
            "project_path": receipt_authority.PROJECT_PATH,
            "commit_sha": receipt_authority.COMMIT_SHA,
            "repository_path": expected.repository_path,
            "parent_result_comment_id": receipt_authority.SELECTION_RESULT_COMMENT_ID,
            "parent_section": expected.parent_section,
            "parent_option": expected.parent_option,
            "byte_count": expected.byte_count,
            "sha256": expected.sha256,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }
        for field, value in exact_fields.items():
            _exact(receipt[field], value, f"receipt[{index}].{field}")
        reduced_artifacts.append(
            {
                "role": expected.role,
                "repository_path": expected.repository_path,
                "byte_count": expected.byte_count,
                "sha256": expected.sha256,
            }
        )

    return {
        "schema_version": "eq1-eshm20-first-order-receipt-bridge-v1",
        "authority": {
            "repository": "pokekarten/OpenCatastrophe-data",
            "result_comment_id": TRUSTED_RESULT_COMMENT_ID,
            "run_id": TRUSTED_RUN_ID,
            "execution_sha": TRUSTED_EXECUTION_SHA,
            "provider_commit": receipt_authority.COMMIT_SHA,
            "selection_result_comment_id": receipt_authority.SELECTION_RESULT_COMMENT_ID,
        },
        "artifacts": reduced_artifacts,
        "dependency_closure_authorized": False,
        "model_use_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
