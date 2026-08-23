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
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject

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


class OQ313NumericalReceiptPublicationBudgetTests(unittest.TestCase):
    def test_oversized_receipt_terminalizes_without_embedding_rows(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"fixture")
            return _adapter_payload()

        rows = [
            {
                "event_id": index + 1,
                "rup_id": index + 1,
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
        self.assertGreater(len(payload), subject.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES)

        result = subject.run_action_with_numerical_receipt(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
            project_datastore=lambda path: (payload, identity),
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_stage"],
            "risk_by_event_receipt",
        )
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "numerical_receipt_publication_budget_exceeded",
        )
        self.assertNotIn("numerical_receipt", result)
        self.assertNotIn("numerical_receipt_identity", result)
        self.assertLess(
            len(json.dumps(result, sort_keys=True, separators=(",", ":"))),
            subject.MAX_PUBLIC_NUMERICAL_RECEIPT_BYTES,
        )


if __name__ == "__main__":
    unittest.main()
