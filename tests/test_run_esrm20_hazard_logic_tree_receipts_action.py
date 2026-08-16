# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import run_esrm20_hazard_logic_tree_receipts_action as subject

EXECUTION_SHA = "1" * 40
RETRIEVED_AT = "2026-08-16T22:45:00Z"


def request_body(*, sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


def receipt(*, path: str, operation: str, payload: bytes) -> dict[str, object]:
    return {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": operation,
        "source_issue": subject.SOURCE_SCIENCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": path,
        "requested_url": "https://example.invalid/fixed",
        "final_url": "https://example.invalid/fixed",
        "retrieved_at": RETRIEVED_AT,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": "application/xml",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


class HazardLogicTreeReceiptsActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=476, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in ("path", "url", "project_id", "group", "parser"):
            self.assertNotIn(forbidden, parsed)
        with self.assertRaisesRegex(subject.HazardLogicTreeReceiptsActionError, "target_sha"):
            subject.validate_request(
                request_body(sha="2" * 40), expected_issue=476, execution_sha=EXECUTION_SHA
            )

    def test_receipt_identity_is_exact_for_each_logic_tree(self) -> None:
        cases = (
            (
                subject.GSIM_LOGIC_TREE_REPOSITORY_PATH,
                subject.GSIM_LOGIC_TREE_OPERATION_ID,
            ),
            (
                subject.SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
                subject.SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
            ),
        )
        for path, operation in cases:
            with self.subTest(path=path):
                candidate = receipt(path=path, operation=operation, payload=path.encode())
                subject._validate_receipt(
                    candidate, repository_path=path, operation_id=operation
                )
                mutated = dict(candidate)
                mutated["repository_path"] = "Hazard/other.xml"
                with self.assertRaises(subject.HazardLogicTreeReceiptsActionError):
                    subject._validate_receipt(
                        mutated, repository_path=path, operation_id=operation
                    )

    def test_run_is_atomic_and_orders_two_fixed_receipts(self) -> None:
        gsim = receipt(
            path=subject.GSIM_LOGIC_TREE_REPOSITORY_PATH,
            operation=subject.GSIM_LOGIC_TREE_OPERATION_ID,
            payload=b"gsim",
        )
        source = receipt(
            path=subject.SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
            operation=subject.SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
            payload=b"source",
        )
        with mock.patch.object(
            subject, "acquire_event_hazard_gsim_logic_tree_receipt", return_value=gsim
        ), mock.patch.object(
            subject,
            "acquire_event_hazard_source_model_logic_tree_receipt",
            return_value=source,
        ):
            result = subject.run_receipts(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            [row["repository_path"] for row in result["receipts"]],
            [
                subject.GSIM_LOGIC_TREE_REPOSITORY_PATH,
                subject.SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
            ],
        )
        self.assertFalse(result["dependency_content_interpreted"])
        self.assertFalse(result["transitive_dependency_closure_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_second_failure_cannot_publish_partial_authoritative_receipt(self) -> None:
        gsim = receipt(
            path=subject.GSIM_LOGIC_TREE_REPOSITORY_PATH,
            operation=subject.GSIM_LOGIC_TREE_OPERATION_ID,
            payload=b"gsim",
        )
        with mock.patch.object(
            subject, "acquire_event_hazard_gsim_logic_tree_receipt", return_value=gsim
        ), mock.patch.object(
            subject,
            "acquire_event_hazard_source_model_logic_tree_receipt",
            side_effect=subject.EfehrAcquisitionError("secret provider detail"),
        ):
            result = subject.run_receipts(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipts"])
        self.assertNotIn("secret", json.dumps(result))

    def test_trusted_terminal_parser_requires_two_exact_rows(self) -> None:
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "receipts": [
                    {
                        "repository_path": subject.GSIM_LOGIC_TREE_REPOSITORY_PATH,
                        "operation_id": subject.GSIM_LOGIC_TREE_OPERATION_ID,
                        "retrieved_at": RETRIEVED_AT,
                        "byte_count": 10,
                        "sha256": "a" * 64,
                        "content_type": "application/xml",
                        "etag": None,
                    },
                    {
                        "repository_path": subject.SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
                        "operation_id": subject.SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
                        "retrieved_at": RETRIEVED_AT,
                        "byte_count": 20,
                        "sha256": "b" * 64,
                        "content_type": "application/xml",
                        "etag": None,
                    },
                ],
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["receipts"] = result["receipts"][:1]
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self.assertRaisesRegex(subject.HazardLogicTreeReceiptsActionError, "two receipts"):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
