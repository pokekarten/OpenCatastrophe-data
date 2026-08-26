# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import tempfile
import unittest

from scripts import classify_oq313_native_stderr as classifier
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action


class OQ313NativeFailureExceptionClassWiringTests(unittest.TestCase):
    def _snapshot(self, payload: bytes) -> dict[str, object]:
        with tempfile.TemporaryFile(mode="w+b") as stderr_file:
            stderr_file.write(payload)
            stderr_file.flush()
            return runner._stderr_diagnostic_snapshot(stderr_file)

    def test_snapshot_adds_allowlisted_exception_class_without_exposing_content(self) -> None:
        payload = (
            b"Traceback (most recent call last):\n"
            b'  File "/private/provider/path.py", line 1, in <module>\n'
            b"ValueError: secret provider value\n"
        )
        diagnostic = self._snapshot(payload)
        self.assertEqual(
            diagnostic,
            {
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "content_exposed": False,
                "exception_class": "ValueError",
            },
        )
        self.assertNotIn("secret provider value", repr(diagnostic))
        self.assertNotIn("/private/provider/path.py", repr(diagnostic))

    def test_snapshot_uses_unclassified_for_non_utf8_tail(self) -> None:
        payload = (
            b"Traceback (most recent call last):\n"
            b'  File "x.py", line 1, in <module>\n'
            b"\xff\nValueError: hidden\n"
        )
        diagnostic = self._snapshot(payload)
        self.assertEqual(
            diagnostic["exception_class"],
            classifier.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(diagnostic["byte_count"], len(payload))
        self.assertEqual(diagnostic["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertIs(diagnostic["content_exposed"], False)

    def test_action_rejects_arbitrary_exception_class_token(self) -> None:
        document = {
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
            "native_failure_diagnostic": {
                "byte_count": 4,
                "sha256": hashlib.sha256(b"test").hexdigest(),
                "content_exposed": False,
                "exception_class": "SecretProviderException",
            },
        }
        with self.assertRaisesRegex(
            action.KosovoResidentialOQ313ActionError,
            "exception class drifted",
        ):
            action._validate_adapter_document(document)

    def test_action_accepts_only_public_classifier_token(self) -> None:
        document = {
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
            "native_failure_diagnostic": {
                "byte_count": 4,
                "sha256": hashlib.sha256(b"test").hexdigest(),
                "content_exposed": False,
                "exception_class": classifier.UNCLASSIFIED_EXCEPTION_CLASS,
            },
        }
        validated = action._validate_adapter_document(document)
        self.assertEqual(
            validated["native_failure_diagnostic"]["exception_class"],
            classifier.UNCLASSIFIED_EXCEPTION_CLASS,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
