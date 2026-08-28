# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path
from typing import Any

from scripts import project_oq313_risk_by_event_receipt as numerical_contract
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action
from scripts import validate_eq1_oq313_run_result as terminal_validator

EXECUTION_SHA = "a" * 40


def _adapter_payload() -> tuple[bytes, dict[str, Any]]:
    document = {
        "schema_version": runner.SCHEMA_VERSION,
        "issues": {
            "control": runner.CONTROL_ISSUE,
            "parent_consumer": runner.PARENT_CONSUMER_ISSUE,
        },
        "experiment_label": runner.EXPERIMENT_LABEL,
        "scope": runner.SCOPE,
        "openquake": {
            "repository": runner.OPENQUAKE_REPOSITORY,
            "version": runner.OPENQUAKE_VERSION,
            "source_version": runner.OPENQUAKE_SOURCE_VERSION,
            "commit_sha": runner.OPENQUAKE_COMMIT_SHA,
        },
        "config": {
            "logical_path": runner.CONFIG_LOGICAL_PATH,
            "byte_count": 1,
            "sha256": "b" * 64,
            "staged_byte_identity_verified": True,
        },
        "loss_semantics": {},
        "source_runtime": {},
        "resolved_runtime": {"concurrent_tasks": 0},
        "execution": {
            "command": list(runner.COMMAND),
            "exit_code": 0,
            "numerical_execution_attempted": True,
        },
        "status": "pass",
        "failure_stage": None,
        "failure_code": None,
        "external_provider_bytes_persisted": False,
        "risk_by_event_receipt_emitted": False,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "historical_group_assignment_verified": False,
        "vulnerability_horizontal_component_verified": False,
        "horizontal_component_conversion_authorized": False,
        "project186_value_structural_equivalence_verified": False,
        "numerical_reference_loss_verified": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    payload = (
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _large_numerical_payload() -> tuple[bytes, dict[str, Any]]:
    rows = [
        {
            "event_id": index,
            "rup_id": index + 10_000,
            "rlz_id": index % 2,
            "loss_f32_be_hex": "3f800000",
            "variance_f32_be_hex": "00000000",
        }
        for index in range(1_000)
    ]
    payload, identity = numerical_contract.project_oq313_risk_by_event_receipt(
        rows,
        portfolio_agg_id=3,
        structural_loss_id=0,
        concurrent_tasks=0,
    )
    if len(payload) <= action.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES:
        raise AssertionError("large numerical fixture must exceed publication budget")
    return payload, identity


def _run_with_projector(project_datastore: Any) -> dict[str, Any]:
    def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
        del args, kwargs
        datadir = Path(os.environ[action.OQ_DATADIR_ENV])
        (datadir / "calc_1.hdf5").write_bytes(b"fixture")
        return _adapter_payload()

    return action.run_action_with_numerical_receipt(
        execution_sha=EXECUTION_SHA,
        source_group1_config=b"source",
        runtime_identity={},
        resolved_runtime={},
        execute=execute,
        project_datastore=project_datastore,
    )


class OQ313BoundedNumericalReceiptTests(unittest.TestCase):
    def test_valid_oversized_receipt_emits_compact_commitment(self) -> None:
        payload, identity = _large_numerical_payload()

        result = _run_with_projector(lambda path: (payload, dict(identity)))

        self.assertEqual(result["status"], "pass")
        self.assertIs(result["numerical_receipt_emitted"], True)
        self.assertIsNone(result["numerical_receipt_failure_stage"])
        self.assertIsNone(result["numerical_receipt_failure_code"])
        self.assertEqual(result["numerical_receipt_identity"], identity)
        self.assertNotIn("numerical_receipt", result)

        commitment = result["numerical_receipt_commitment"]
        self.assertEqual(
            commitment["schema_version"],
            action.NUMERICAL_RECEIPT_COMMITMENT_SCHEMA_VERSION,
        )
        self.assertEqual(
            commitment["source_schema_version"],
            numerical_contract.SCHEMA_VERSION,
        )
        self.assertEqual(commitment["row_count"], 1_000)
        self.assertIs(commitment["full_receipt_published"], False)
        self.assertEqual(
            identity["sha256"],
            hashlib.sha256(payload).hexdigest(),
        )

        public_payload = (
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        self.assertLess(
            len(public_payload),
            action.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES,
        )
        self.assertIs(result["scientific_validity_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_oversized_receipt_is_validated_before_compaction(self) -> None:
        payload, identity = _large_numerical_payload()
        bad_identity = dict(identity)
        bad_identity["sha256"] = "0" * 64

        result = _run_with_projector(lambda path: (payload, bad_identity))

        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "numerical_receipt_validation_failed",
        )
        self.assertNotIn("numerical_receipt_commitment", result)

    def test_terminal_validator_accepts_exact_compact_commitment(self) -> None:
        payload, identity = _large_numerical_payload()
        result = _run_with_projector(lambda path: (payload, dict(identity)))
        body = (
            action.RESULT_MARKER
            + "\n"
            + json.dumps(result, sort_keys=True, separators=(",", ":"))
        )

        summary = terminal_validator.validate_terminal_body(
            body,
            expected_execution_sha=EXECUTION_SHA,
        )

        self.assertIs(summary["body_contract_validated"], True)
        self.assertEqual(summary["declared_terminal_status"], "pass")
        self.assertEqual(summary["numerical_receipt_identity"], identity)
        self.assertEqual(summary["row_count"], 1_000)
        self.assertIs(summary["scientific_validity_verified"], False)
        self.assertIs(summary["publication_authorized"], False)
        self.assertIs(summary["model_use_authorized"], False)

    def test_terminal_validator_rejects_commitment_tampering(self) -> None:
        payload, identity = _large_numerical_payload()
        result = _run_with_projector(lambda path: (payload, dict(identity)))
        result["numerical_receipt_commitment"]["row_count"] = 0
        body = (
            action.RESULT_MARKER
            + "\n"
            + json.dumps(result, sort_keys=True, separators=(",", ":"))
        )

        with self.assertRaisesRegex(
            terminal_validator.EQ1OQ313TerminalValidationError,
            "commitment row count drifted",
        ):
            terminal_validator.validate_terminal_body(
                body,
                expected_execution_sha=EXECUTION_SHA,
            )


if __name__ == "__main__":
    unittest.main()
