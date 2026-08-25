# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action


def _blocked_document(*, failure_code: str, exit_code: int) -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": runner.SCHEMA_VERSION,
        "issues": {
            "control": runner.CONTROL_ISSUE,
            "parent_consumer": runner.PARENT_CONSUMER_ISSUE,
        },
        "experiment_label": runner.EXPERIMENT_LABEL,
        "scope": runner.SCOPE,
        "openquake": {},
        "config": {},
        "loss_semantics": {},
        "source_runtime": {},
        "resolved_runtime": {},
        "execution": {
            "command": list(runner.COMMAND),
            "exit_code": exit_code,
            "numerical_execution_attempted": True,
        },
        "status": "blocked",
        "failure_stage": "openquake_run",
        "failure_code": failure_code,
        "external_provider_bytes_persisted": False,
        "risk_by_event_receipt_emitted": False,
        "native_failure_diagnostic": {
            "byte_count": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
            "content_exposed": False,
        },
    }
    for field in action._AUTHORITY_FALSE_FIELDS:
        document[field] = False
    return document


class OQ313TimeoutProvenanceTests(unittest.TestCase):
    def test_action_accepts_controller_timeout_as_distinct_blocked_terminal(self) -> None:
        document = _blocked_document(
            failure_code="openquake_run_timeout",
            exit_code=runner.NATIVE_TIMEOUT_EXIT_CODE,
        )

        validated = action._validate_adapter_document(document)

        self.assertEqual(validated["failure_code"], "openquake_run_timeout")
        self.assertEqual(validated["execution"]["exit_code"], 124)
        self.assertIs(validated["native_failure_diagnostic"]["content_exposed"], False)
        for field in action._AUTHORITY_FALSE_FIELDS:
            self.assertIs(validated[field], False)

    def test_action_treats_genuine_native_exit_124_as_ordinary_native_failure(self) -> None:
        document = _blocked_document(
            failure_code="openquake_run_failed",
            exit_code=runner.NATIVE_TIMEOUT_EXIT_CODE,
        )

        validated = action._validate_adapter_document(document)

        self.assertEqual(validated["failure_code"], "openquake_run_failed")
        self.assertEqual(validated["execution"]["exit_code"], 124)

    def test_action_rejects_timeout_classification_with_non_timeout_exit(self) -> None:
        document = _blocked_document(
            failure_code="openquake_run_timeout",
            exit_code=9,
        )

        with self.assertRaisesRegex(
            action.KosovoResidentialOQ313ActionError,
            "timeout exit code drifted",
        ):
            action._validate_adapter_document(document)

    def test_action_rejects_timeout_without_opaque_diagnostic(self) -> None:
        document = _blocked_document(
            failure_code="openquake_run_timeout",
            exit_code=runner.NATIVE_TIMEOUT_EXIT_CODE,
        )
        document.pop("native_failure_diagnostic")

        with self.assertRaisesRegex(
            action.KosovoResidentialOQ313ActionError,
            "timeout diagnostic missing",
        ):
            action._validate_adapter_document(document)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
