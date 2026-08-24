# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import unittest
from typing import Any
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject

EXECUTION_SHA = "a" * 40


def _request(**updates: Any) -> str:
    payload: dict[str, Any] = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": EXECUTION_SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "TEST-SLOT3",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


def _adapter_document(*, status: str = "pass") -> dict[str, Any]:
    blocked = status == "blocked"
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


def _payload(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )


def _receipt(payload: bytes) -> dict[str, Any]:
    return {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _fake_execute(
    source_group1_config: bytes,
    *,
    runtime_identity: object,
    resolved_runtime: object,
) -> tuple[bytes, dict[str, Any]]:
    if source_group1_config != b"source":
        raise AssertionError("unexpected source config")
    if runtime_identity != {"runtime": "fixed"}:
        raise AssertionError("unexpected runtime identity")
    if resolved_runtime != {"resolved": "fixed"}:
        raise AssertionError("unexpected resolved runtime")
    payload = _payload(_adapter_document())
    return payload, _receipt(payload)


class KosovoResidentialOQ313ActionTests(unittest.TestCase):
    def test_validate_request_accepts_exact_closed_envelope(self) -> None:
        request = subject.validate_request(
            _request(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(request["target_sha"], EXECUTION_SHA)
        self.assertEqual(set(request), subject._REQUEST_FIELDS)

    def test_validate_request_rejects_authority_drift(self) -> None:
        cases = (
            ({"target_sha": "b" * 40}, "target_sha"),
            ({"issue": 287}, "issue"),
            ({"action": "other"}, "action"),
            ({"dataset_id": "other"}, "dataset_id"),
            ({"requester": " bad"}, "requester"),
        )
        for updates, message in cases:
            with self.subTest(updates=updates):
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313ActionError,
                    message,
                ):
                    subject.validate_request(
                        _request(**updates),
                        expected_issue=subject.CONTROL_ISSUE,
                        execution_sha=EXECUTION_SHA,
                    )

    def test_validate_request_rejects_caller_selected_target_fields(self) -> None:
        payload = json.loads(_request().split(subject.REQUEST_MARKER, 1)[1])
        payload["provider_path"] = "arbitrary"
        body = subject.REQUEST_MARKER + "\n" + json.dumps(payload)
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "fields drifted",
        ):
            subject.validate_request(
                body,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_validate_request_rejects_duplicate_json_keys(self) -> None:
        body = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + subject.ACTION
            + '","issue":609,"target_sha":"'
            + EXECUTION_SHA
            + '","dataset_id":"'
            + subject.DATASET_ID
            + '","requester":"one","requester":"two"}'
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "duplicate",
        ):
            subject.validate_request(
                body,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_run_action_wraps_exact_adapter_result_without_authority(self) -> None:
        result = subject.run_action(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={"runtime": "fixed"},
            resolved_runtime={"resolved": "fixed"},
            execute=_fake_execute,
        )
        self.assertEqual(result["schema_version"], subject.RESULT_SCHEMA_VERSION)
        self.assertEqual(result["execution_sha"], EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["adapter_result"]["status"], "pass")
        self.assertIs(result["external_provider_bytes_persisted"], False)
        self.assertIs(result["historical_reproduction_verified"], False)
        self.assertIs(result["scientific_validity_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_run_action_accepts_bounded_native_failure_as_blocked(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            payload = _payload(_adapter_document(status="blocked"))
            return payload, _receipt(payload)

        result = subject.run_action(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["adapter_result"]["failure_stage"], "openquake_run")

    def test_run_action_rejects_adapter_top_level_field_drift(self) -> None:
        cases = ("extra", "missing")
        for case in cases:
            with self.subTest(case=case):
                def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
                    del args, kwargs
                    document = _adapter_document()
                    if case == "extra":
                        document["unexpected_terminal_field"] = "must-not-cross"
                    else:
                        document.pop("issues")
                    payload = _payload(document)
                    return payload, _receipt(payload)

                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313ActionError,
                    "adapter result fields drifted",
                ):
                    subject.run_action(
                        execution_sha=EXECUTION_SHA,
                        source_group1_config=b"source",
                        runtime_identity={},
                        resolved_runtime={},
                        execute=execute,
                    )

    def test_run_action_rejects_adapter_authority_promotion(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            document = _adapter_document()
            document["model_use_authorized"] = True
            payload = _payload(document)
            return payload, _receipt(payload)

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "model_use_authorized",
        ):
            subject.run_action(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=execute,
            )

    def test_run_action_rejects_receipt_size_drift(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            payload = _payload(_adapter_document())
            receipt = _receipt(payload)
            receipt["byte_count"] = len(payload) + 1
            return payload, receipt

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "byte count",
        ):
            subject.run_action(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=execute,
            )

    def test_run_action_rejects_receipt_digest_drift(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            payload = _payload(_adapter_document())
            receipt = _receipt(payload)
            receipt["sha256"] = "0" * 64
            return payload, receipt

        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "digest drifted",
        ):
            subject.run_action(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=execute,
            )

    def test_validate_only_does_not_require_staged_execution_inputs(self) -> None:
        with mock.patch.dict(os.environ, {"REQUEST_BODY": _request()}, clear=False):
            result = subject.main(
                [
                    "--comment-body-env",
                    "REQUEST_BODY",
                    "--expected-issue",
                    "609",
                    "--execution-sha",
                    EXECUTION_SHA,
                    "--validate-request-only",
                ]
            )
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
