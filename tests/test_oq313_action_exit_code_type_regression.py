# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from typing import Any

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject


def _adapter_document() -> dict[str, Any]:
    return {
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
        "resolved_runtime": {},
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


def _adapter_payload_and_receipt() -> tuple[bytes, dict[str, Any]]:
    payload = (
        json.dumps(
            _adapter_document(),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


class OQ313ActionExitCodeTypeRegressionTests(unittest.TestCase):
    def test_pass_rejects_zero_like_non_integer_exit_codes(self) -> None:
        for exit_code in (False, 0.0):
            with self.subTest(exit_code=exit_code):
                document = _adapter_document()
                document["execution"]["exit_code"] = exit_code
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313ActionError,
                    "PASS exit code type drifted",
                ):
                    subject._validate_adapter_document(document)

    def test_pass_preserves_exact_integer_zero(self) -> None:
        document = _adapter_document()
        validated = subject._validate_adapter_document(document)
        self.assertIs(type(validated["execution"]["exit_code"]), int)
        self.assertEqual(validated["execution"]["exit_code"], 0)

    def test_adapter_receipt_rejects_float_byte_count_equal_to_payload_length(
        self,
    ) -> None:
        payload, receipt = _adapter_payload_and_receipt()
        receipt["byte_count"] = float(receipt["byte_count"])

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "adapter receipt byte count drifted",
        ):
            subject._canonical_result(
                execution_sha="a" * 40,
                adapter_payload=payload,
                adapter_receipt=receipt,
            )

    def test_adapter_receipt_preserves_exact_integer_byte_count(self) -> None:
        payload, receipt = _adapter_payload_and_receipt()
        result = subject._canonical_result(
            execution_sha="a" * 40,
            adapter_payload=payload,
            adapter_receipt=receipt,
        )

        self.assertIs(type(result["adapter_receipt"]["byte_count"]), int)
        self.assertEqual(result["adapter_receipt"]["byte_count"], len(payload))


if __name__ == "__main__":
    unittest.main()
