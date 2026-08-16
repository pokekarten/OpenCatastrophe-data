# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stderr
from unittest import mock

from scripts import acquire_eshm20_source_model_child_receipts as worker
from scripts import agent_action_protocol as protocol
from scripts import efehr_gitlab_receipt as efehr
from scripts import prepare_agent_action_result as prepare
from scripts import validate_agent_action_request as request_validator
from scripts import validate_agent_action_result as result_validator

ACTION = "efehr_eshm20_source_model_child_receipts"
EXECUTION_SHA = "a" * 40
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": 414,
    "target_sha": EXECUTION_SHA,
    "dataset_id": "efehr.eshm20",
    "requester": "issue414-builder",
}
RETRIEVED_AT = "2026-08-16T08:00:00Z"
FINISHED_AT = "2026-08-16T09:00:00Z"


def child_receipt(repository_path: str, index: int) -> dict[str, object]:
    target = efehr.validate_target(
        source_issue=worker.SOURCE_ISSUE,
        dataset_id=worker.DATASET_ID,
        project_id=worker.PROJECT_ID,
        commit_sha=worker.COMMIT_SHA,
        repository_path=repository_path,
    )
    url = efehr.raw_file_api_url(target)
    return {
        "schema_version": efehr.SCHEMA_VERSION,
        "source_issue": worker.SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "provider_host": efehr.PROVIDER_HOST,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": repository_path,
        "requested_url": url,
        "final_url": url,
        "retrieved_at": RETRIEVED_AT,
        "byte_count": index + 1,
        "sha256": f"{index + 1:064x}",
        "content_type": "application/xml",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "parent_result_comment_id": worker.PARENT_RESULT_COMMENT_ID,
    }


def receipt_set() -> dict[str, object]:
    receipts = [
        child_receipt(spec.repository_path, index)
        for index, spec in enumerate(worker.CHILDREN)
    ]
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "provider_host": efehr.PROVIDER_HOST,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "parent_request_comment_id": worker.PARENT_REQUEST_COMMENT_ID,
        "parent_result_comment_id": worker.PARENT_RESULT_COMMENT_ID,
        "parent_run_id": worker.PARENT_RUN_ID,
        "parent_execution_sha": worker.PARENT_EXECUTION_SHA,
        "parent_semantic_request_id": worker.PARENT_SEMANTIC_REQUEST_ID,
        "parent_source_tree_byte_count": worker.PARENT_SOURCE_TREE_BYTE_COUNT,
        "parent_source_tree_sha256": worker.PARENT_SOURCE_TREE_SHA256,
        "child_count": worker.EXPECTED_CHILD_COUNT,
        "child_paths_sha256": worker.EXPECTED_PATHS_SHA256,
        "retrieved_at": RETRIEVED_AT,
        "receipts": receipts,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class SourceModelChildReceiptActionTests(unittest.TestCase):
    def test_request_and_network_semantics_are_closed(self) -> None:
        self.assertEqual(request_validator.validate_request(dict(REQUEST)), REQUEST)
        self.assertIn(ACTION, prepare.NETWORK_ACTIONS)
        self.assertIn(ACTION, protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(dict(REQUEST)), 414)

        for field, value in (("issue", 397), ("dataset_id", "other.dataset")):
            with self.subTest(field=field):
                with self.assertRaises(request_validator.RequestError):
                    request_validator.validate_request(dict(REQUEST, **{field: value}))

        for selector in ("provider", "project_id", "commit_sha", "repository_path", "paths", "parser", "url"):
            with self.subTest(selector=selector):
                with self.assertRaises(request_validator.RequestError):
                    request_validator.validate_request(dict(REQUEST, **{selector: "attacker"}))

    def test_exact_51_receipt_contract_and_authority_ceilings(self) -> None:
        base = receipt_set()
        self.assertEqual(
            result_validator.validate_efehr_eshm20_source_model_child_receipts(
                copy.deepcopy(base)
            ),
            base,
        )

        for field in (
            "dependency_inventory_authorized",
            "dependency_receipt_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(base)
                mutated[field] = True
                with self.assertRaises(result_validator.ResultError):
                    result_validator.validate_efehr_eshm20_source_model_child_receipts(mutated)

        widened = copy.deepcopy(base)
        widened["transitive_closure_authorized"] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_child_receipts(widened)

    def test_cardinality_order_parent_and_scalar_mutations_fail_closed(self) -> None:
        base = receipt_set()

        short = copy.deepcopy(base)
        short["receipts"] = short["receipts"][:-1]
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_child_receipts(short)

        reordered = copy.deepcopy(base)
        reordered["receipts"][0], reordered["receipts"][1] = (
            reordered["receipts"][1], reordered["receipts"][0]
        )
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_efehr_eshm20_source_model_child_receipts(reordered)

        mutations = (
            (0, "parent_result_comment_id", 1),
            (0, "project_id", 999),
            (0, "commit_sha", "b" * 40),
            (0, "byte_count", True),
            (0, "sha256", "A" * 64),
            (0, "external_bytes_persisted", True),
            (0, "publication_authorized", True),
        )
        for index, field, value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(base)
                mutated["receipts"][index][field] = value
                with self.assertRaises(result_validator.ResultError):
                    result_validator.validate_efehr_eshm20_source_model_child_receipts(mutated)

    def test_dispatch_dedup_and_failure_are_fail_closed(self) -> None:
        calls: list[str] = []

        def acquirer():
            calls.append("called")
            return receipt_set()

        with mock.patch.object(prepare, "utc_now", return_value=FINISHED_AT):
            result = prepare.prepare_completed_result(
                dict(REQUEST),
                [],
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha=EXECUTION_SHA,
                source_comment_id=1,
                run_id=2,
                run_attempt=1,
                started_at="2026-08-16T07:00:00Z",
                eshm20_source_model_child_receipts_acquirer=acquirer,
            )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["evidence"][ACTION]["child_count"], 51)

        prior = [{
            "id": 9,
            "body": protocol.canonical_result_comment(result),
            "user": {"login": "github-actions[bot]"},
        }]
        with mock.patch.object(prepare, "utc_now", return_value=FINISHED_AT):
            duplicate = prepare.prepare_completed_result(
                dict(REQUEST),
                prior,
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha=EXECUTION_SHA,
                source_comment_id=3,
                run_id=4,
                run_attempt=1,
                started_at="2026-08-16T07:00:00Z",
                eshm20_source_model_child_receipts_acquirer=lambda: self.fail(
                    "worker ran on duplicate"
                ),
            )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 9)

        def failed():
            raise worker.Eshm20SourceModelChildReceiptError(
                "PRIVATE_PROVIDER_URL_AND_BODY"
            )

        stream = io.StringIO()
        with (
            redirect_stderr(stream),
            mock.patch.object(prepare, "utc_now", return_value=FINISHED_AT),
        ):
            blocked = prepare.prepare_completed_result(
                dict(REQUEST),
                [],
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha=EXECUTION_SHA,
                source_comment_id=5,
                run_id=6,
                run_attempt=1,
                started_at="2026-08-16T07:00:00Z",
                eshm20_source_model_child_receipts_acquirer=failed,
            )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"][ACTION])
        self.assertNotIn("PRIVATE_PROVIDER", stream.getvalue())

    def test_target_execution_mismatch_fails_before_worker(self) -> None:
        with self.assertRaises(prepare.ProtocolError):
            prepare.prepare_completed_result(
                dict(REQUEST),
                [],
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha="b" * 40,
                source_comment_id=1,
                run_id=2,
                run_attempt=1,
                started_at="2026-08-16T07:00:00Z",
                eshm20_source_model_child_receipts_acquirer=lambda: self.fail(
                    "worker must not run"
                ),
            )


if __name__ == "__main__":
    unittest.main()
