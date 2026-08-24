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
from scripts import validate_eq1_oq313_run_result as subject

EXECUTION_SHA = "a" * 40


def _adapter_payload(*, status: str = "pass") -> tuple[bytes, dict[str, Any]]:
    blocked = status == "blocked"
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
            "exit_code": 9 if blocked else 0,
            "numerical_execution_attempted": True,
        },
        "status": status,
        "failure_stage": "openquake_run" if blocked else None,
        "failure_code": "openquake_run_failed" if blocked else None,
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


def _numerical_payload() -> tuple[bytes, dict[str, Any]]:
    return numerical_contract.project_oq313_risk_by_event_receipt(
        [
            {
                "event_id": 1,
                "rup_id": 2,
                "rlz_id": 3,
                "loss_f32_be_hex": "3f800000",
                "variance_f32_be_hex": "00000000",
            }
        ],
        portfolio_agg_id=4,
        structural_loss_id=0,
        concurrent_tasks=0,
    )


def _result(*, blocked_adapter: bool = False) -> dict[str, Any]:
    def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
        del args, kwargs
        datadir = Path(os.environ[action.OQ_DATADIR_ENV])
        (datadir / "calc_1.hdf5").write_bytes(b"fixture")
        return _adapter_payload(status="blocked" if blocked_adapter else "pass")

    return action.run_action_with_numerical_receipt(
        execution_sha=EXECUTION_SHA,
        source_group1_config=b"source",
        runtime_identity={},
        resolved_runtime={},
        execute=execute,
        project_datastore=lambda path: _numerical_payload(),
    )


def _body(result: dict[str, Any]) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class EQ1OQ313TerminalValidatorTests(unittest.TestCase):
    def test_accepts_canonical_pass_and_reports_receipt_identity(self) -> None:
        result = _result()
        summary = subject.validate_terminal_body(
            _body(result), expected_execution_sha=EXECUTION_SHA
        )
        self.assertEqual(summary["status"], "pass")
        self.assertIs(summary["numerical_receipt_emitted"], True)
        self.assertEqual(summary["row_count"], 1)
        self.assertEqual(
            summary["numerical_receipt_identity"],
            result["numerical_receipt_identity"],
        )

    def test_accepts_canonical_native_block_without_projecting_partial_data(self) -> None:
        result = _result(blocked_adapter=True)
        summary = subject.validate_terminal_body(
            _body(result), expected_execution_sha=EXECUTION_SHA
        )
        self.assertEqual(summary["status"], "blocked")
        self.assertIs(summary["numerical_receipt_emitted"], False)

    def test_rejects_execution_sha_drift(self) -> None:
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "execution_sha"
        ):
            subject.validate_terminal_body(
                _body(_result()), expected_execution_sha="c" * 40
            )

    def test_rejects_outer_authority_promotion(self) -> None:
        result = _result()
        result["model_use_authorized"] = True
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "authority boundary"
        ):
            subject.validate_terminal_body(
                _body(result), expected_execution_sha=EXECUTION_SHA
            )

    def test_rejects_adapter_receipt_drift(self) -> None:
        result = _result()
        result["adapter_receipt"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "adapter receipt digest"
        ):
            subject.validate_terminal_body(
                _body(result), expected_execution_sha=EXECUTION_SHA
            )

    def test_rejects_numerical_receipt_content_drift(self) -> None:
        result = _result()
        result["numerical_receipt"]["rows"][0]["loss_f32_be_hex"] = "40000000"
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "numerical receipt contract"
        ):
            subject.validate_terminal_body(
                _body(result), expected_execution_sha=EXECUTION_SHA
            )

    def test_rejects_extra_public_field(self) -> None:
        result = _result()
        result["unexpected"] = "drift"
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "PASS terminal fields"
        ):
            subject.validate_terminal_body(
                _body(result), expected_execution_sha=EXECUTION_SHA
            )

    def test_accepts_bounded_numerical_failure_code(self) -> None:
        result = _result()
        result.pop("numerical_receipt")
        result.pop("numerical_receipt_identity")
        result["status"] = "blocked"
        result["numerical_receipt_emitted"] = False
        result["numerical_receipt_failure_stage"] = "risk_by_event_receipt"
        result["numerical_receipt_failure_code"] = "risk_by_event_selection_failed"
        summary = subject.validate_terminal_body(
            _body(result), expected_execution_sha=EXECUTION_SHA
        )
        self.assertEqual(summary["status"], "blocked")

    def test_rejects_unbounded_numerical_failure_code(self) -> None:
        result = _result()
        result.pop("numerical_receipt")
        result.pop("numerical_receipt_identity")
        result["status"] = "blocked"
        result["numerical_receipt_emitted"] = False
        result["numerical_receipt_failure_stage"] = "risk_by_event_receipt"
        result["numerical_receipt_failure_code"] = "invented"
        with self.assertRaisesRegex(
            subject.EQ1OQ313TerminalValidationError, "failure code"
        ):
            subject.validate_terminal_body(
                _body(result), expected_execution_sha=EXECUTION_SHA
            )


if __name__ == "__main__":
    unittest.main()
