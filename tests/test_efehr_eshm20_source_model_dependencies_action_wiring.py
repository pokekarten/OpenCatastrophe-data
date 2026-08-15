# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stderr

from scripts import acquire_eshm20_source_model_dependencies as worker
from scripts import prepare_agent_action_result as prepare
from scripts import validate_agent_action_request as request_validator
from scripts import validate_agent_action_result as result_validator

ACTION = "efehr_eshm20_source_model_dependencies"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": 397,
    "target_sha": "a" * 40,
    "dataset_id": "efehr.eshm20",
    "requester": "issue397-builder",
}


def receipt() -> dict[str, object]:
    path = next(path for path in sorted(worker._CANONICAL_INVENTORY) if path.endswith(".xml") and path != worker._CANONICAL_REPOSITORY_PATH)
    return {
        "schema_version": worker._CANONICAL_SCHEMA_VERSION,
        "source_issue": worker._CANONICAL_SOURCE_ISSUE,
        "control_issue": worker._CANONICAL_CONTROL_ISSUE,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "project_id": worker._CANONICAL_PROJECT_ID,
        "project_path": worker._CANONICAL_PROJECT_PATH,
        "commit_sha": worker._CANONICAL_COMMIT_SHA,
        "repository_path": worker._CANONICAL_REPOSITORY_PATH,
        "byte_count": worker._CANONICAL_EXPECTED_BYTE_COUNT,
        "sha256": worker._CANONICAL_EXPECTED_SHA256,
        "parser": worker._CANONICAL_PARSER_ID,
        "inventory_receipt_comment_id": worker._CANONICAL_INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": worker._CANONICAL_ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": worker._CANONICAL_SOURCE_SPEC.parent_section,
        "root_dependency_option": worker._CANONICAL_SOURCE_SPEC.parent_option,
        "first_order_receipt_request_comment_id": worker._CANONICAL_FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_run_id": worker._CANONICAL_FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": worker._CANONICAL_FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "dependencies": [{
            "resolved_path": path,
            "origins": [{"uncertainty_type": "sourceModel", "branch_id": "b1"}],
            "is_hdf5_companion": False,
        }],
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class SourceTreeActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_six_fields(self) -> None:
        self.assertEqual(request_validator.validate_request(dict(REQUEST)), REQUEST)
        for field, value in (("issue", 398), ("dataset_id", "other.dataset")):
            mutated = dict(REQUEST, **{field: value})
            with self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(mutated)
        with self.assertRaises(request_validator.RequestError):
            request_validator.validate_request(dict(REQUEST, repository_path="attacker.xml"))

    def test_pass_receipt_is_derived_only_and_fail_closed(self) -> None:
        base = receipt()
        self.assertEqual(result_validator.validate_efehr_eshm20_source_model_dependencies(copy.deepcopy(base)), base)
        for field, value in (
            ("dependency_inventory_authorized", True),
            ("dependency_receipt_authorized", True),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("model_use_authorized", True),
        ):
            mutated = copy.deepcopy(base); mutated[field] = value
            with self.assertRaises(result_validator.ResultError):
                result_validator.validate_efehr_eshm20_source_model_dependencies(mutated)
        leaked = copy.deepcopy(base); leaked["provider_bytes"] = "PRIVATE"
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_dependencies(leaked)

    def test_child_path_origin_order_and_inventory_are_closed(self) -> None:
        base = receipt()
        outside = copy.deepcopy(base); outside["dependencies"][0]["resolved_path"] = "outside.xml"
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_dependencies(outside)
        hdf5 = copy.deepcopy(base); hdf5["dependencies"][0]["is_hdf5_companion"] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_dependencies(hdf5)
        bad_origin = copy.deepcopy(base); bad_origin["dependencies"][0]["origins"][0]["uncertainty_type"] = "gmpeModel"
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_dependencies(bad_origin)

    def test_dedup_precedes_worker_and_failure_log_is_sanitized(self) -> None:
        calls: list[str] = []
        def acquirer():
            calls.append("called")
            return receipt()
        result = prepare.prepare_completed_result(
            dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=1, run_id=2, run_attempt=1, started_at="2026-08-15T17:00:00Z",
            eshm20_source_model_dependencies_acquirer=acquirer,
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["status"], "pass")
        prior = [{"id": 9, "body": __import__("scripts.agent_action_protocol", fromlist=["canonical_result_comment"]).canonical_result_comment(result), "user": {"login": "github-actions[bot]"}}]
        duplicate = prepare.prepare_completed_result(
            dict(REQUEST), prior, repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=3, run_id=4, run_attempt=1, started_at="2026-08-15T17:00:00Z",
            eshm20_source_model_dependencies_acquirer=lambda: self.fail("worker ran on duplicate"),
        )
        self.assertEqual(duplicate["status"], "duplicate")

        def failed():
            raise worker.Eshm20SourceModelDependencyError("PRIVATE_PROVIDER_URL_AND_BODY")
        stream = io.StringIO()
        with redirect_stderr(stream):
            blocked = prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
                source_comment_id=5, run_id=6, run_attempt=1, started_at="2026-08-15T17:00:00Z",
                eshm20_source_model_dependencies_acquirer=failed,
            )
        self.assertEqual(blocked["status"], "blocked")
        self.assertNotIn("PRIVATE_PROVIDER", stream.getvalue())

    def test_target_execution_mismatch_fails_before_worker(self) -> None:
        with self.assertRaises(prepare.ProtocolError):
            prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="b" * 40,
                source_comment_id=1, run_id=2, run_attempt=1, started_at="2026-08-15T17:00:00Z",
                eshm20_source_model_dependencies_acquirer=lambda: self.fail("worker must not run"),
            )


if __name__ == "__main__":
    unittest.main()
