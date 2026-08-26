# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from typing import Any

from scripts import classify_oq313_native_stderr as classifier
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject

EXECUTION_SHA = "a" * 40


def _blocked_adapter_document() -> dict[str, Any]:
    return {
        "schema_version": runner.SCHEMA_VERSION,
        "issues": {},
        "experiment_label": runner.EXPERIMENT_LABEL,
        "scope": runner.SCOPE,
        "openquake": {},
        "config": {},
        "loss_semantics": {},
        "source_runtime": {},
        "resolved_runtime": {},
        "execution": {
            "command": list(runner.COMMAND),
            "exit_code": 9,
            "numerical_execution_attempted": True,
        },
        "status": "blocked",
        "failure_stage": "openquake_run",
        "failure_code": "openquake_run_failed",
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
        "native_failure_diagnostic": None,
    }


def _payload_and_receipt(document: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    payload = (
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


class OQ313AdapterNativeFailureDiagnosticSchemaTests(unittest.TestCase):
    def test_present_null_native_failure_diagnostic_fails_closed(self) -> None:
        payload, receipt = _payload_and_receipt(_blocked_adapter_document())

        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            return payload, receipt

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "adapter native failure diagnostic fields drifted",
        ):
            subject.run_action(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=execute,
            )

    def test_unallowlisted_traceback_origin_fails_closed(self) -> None:
        document = _blocked_adapter_document()
        document["native_failure_diagnostic"] = {
            "byte_count": 4,
            "sha256": hashlib.sha256(b"boom").hexdigest(),
            "content_exposed": False,
            "exception_class": classifier.UNCLASSIFIED_EXCEPTION_CLASS,
            "traceback_origin": "openquake.not_allowed",
        }
        payload, receipt = _payload_and_receipt(document)

        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            return payload, receipt

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "adapter native failure diagnostic traceback origin drifted",
        ):
            subject.run_action(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=execute,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
