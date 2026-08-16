# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from scripts import acquire_eshm20_source_model_child_receipts as worker
from scripts import agent_action_protocol as protocol
from scripts import prepare_agent_action_result as prepare
from scripts import validate_agent_action_request as request_validator
from scripts import validate_agent_action_result as result_validator

ACTION = "efehr_eshm20_source_model_child_receipts"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": 414,
    "target_sha": "a" * 40,
    "dataset_id": "efehr.eshm20",
    "requester": "issue414-builder",
}


def receipt() -> dict[str, object]:
    retrieved_at = "2026-08-16T08:00:01Z"
    children = [
        {
            "repository_path": spec.repository_path,
            "retrieved_at": retrieved_at,
            "byte_count": 24,
            "sha256": f"{index + 1:064x}",
            "project_id": worker._CANONICAL_PROJECT_ID,
            "project_path": worker._CANONICAL_PROJECT_PATH,
            "commit_sha": worker._CANONICAL_COMMIT_SHA,
            "parent_result_comment_id": worker._CANONICAL_PARENT_RESULT_COMMENT_ID,
            "dependency_inventory_authorized": False,
            "dependency_receipt_authorized": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
        for index, spec in enumerate(worker._CANONICAL_CHILDREN)
    ]
    return {
        "schema_version": worker._CANONICAL_SCHEMA_VERSION,
        "operation_id": worker._CANONICAL_OPERATION_ID,
        "control_issue": worker._CANONICAL_CONTROL_ISSUE,
        "source_issue": worker._CANONICAL_SOURCE_ISSUE,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "provider_host": worker._CANONICAL_PROVIDER_HOST,
        "project_id": worker._CANONICAL_PROJECT_ID,
        "project_path": worker._CANONICAL_PROJECT_PATH,
        "commit_sha": worker._CANONICAL_COMMIT_SHA,
        "parent_request_comment_id": worker._CANONICAL_PARENT_REQUEST_COMMENT_ID,
        "parent_result_comment_id": worker._CANONICAL_PARENT_RESULT_COMMENT_ID,
        "parent_run_id": worker._CANONICAL_PARENT_RUN_ID,
        "parent_execution_sha": worker._CANONICAL_PARENT_EXECUTION_SHA,
        "parent_semantic_request_id": worker._CANONICAL_PARENT_SEMANTIC_REQUEST_ID,
        "parent_source_tree_byte_count": worker._CANONICAL_PARENT_SOURCE_TREE_BYTE_COUNT,
        "parent_source_tree_sha256": worker._CANONICAL_PARENT_SOURCE_TREE_SHA256,
        "child_count": worker._CANONICAL_EXPECTED_CHILD_COUNT,
        "child_paths_sha256": worker._CANONICAL_EXPECTED_PATHS_SHA256,
        "retrieved_at": retrieved_at,
        "receipts": children,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class SourceModelChildReceiptActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_no_selectors(self) -> None:
        self.assertEqual(request_validator.validate_request(dict(REQUEST)), REQUEST)
        self.assertIn(ACTION, protocol.NETWORK_ACQUISITION_ACTIONS)
        for field, value in (("issue", 415), ("dataset_id", "other.dataset")):
            with self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(dict(REQUEST, **{field: value}))
        for selector in ("provider", "project_id", "commit_sha", "repository_path", "children"):
            with self.subTest(selector=selector), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(dict(REQUEST, **{selector: "attacker"}))

    def test_receipt_contract_is_closed_exact_and_strict(self) -> None:
        base = receipt()
        self.assertEqual(
            result_validator.validate_efehr_eshm20_source_model_child_receipts(copy.deepcopy(base)),
            base,
        )
        self.assertEqual(len(base["receipts"]), 51)
        self.assertEqual(
            [item["repository_path"] for item in base["receipts"]],
            [spec.repository_path for spec in worker._CANONICAL_CHILDREN],
        )
        mutations: list[dict[str, object]] = []
        widened = copy.deepcopy(base); widened["publication_authorized"] = True; mutations.append(widened)
        bool_count = copy.deepcopy(base); bool_count["receipts"][0]["byte_count"] = True; mutations.append(bool_count)
        reordered = copy.deepcopy(base); reordered["receipts"][0], reordered["receipts"][1] = reordered["receipts"][1], reordered["receipts"][0]; mutations.append(reordered)
        extra = copy.deepcopy(base); extra["receipts"][0]["requested_url"] = "https://example.invalid"; mutations.append(extra)
        widened_child = copy.deepcopy(base); widened_child["receipts"][0]["model_use_authorized"] = True; mutations.append(widened_child)
        for mutated in mutations:
            with self.assertRaises(result_validator.ResultError):
                result_validator.validate_efehr_eshm20_source_model_child_receipts(mutated)

    def test_dedup_precedes_worker_and_failure_is_sanitized(self) -> None:
        calls: list[str] = []
        result = prepare.prepare_completed_result(
            dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=1, run_id=2, run_attempt=1, started_at="2026-08-16T08:00:00Z",
            eshm20_source_model_child_receipts_acquirer=lambda: (calls.append("called") or receipt()),
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["evidence"][ACTION]["child_count"], 51)
        prior = [{
            "id": 9,
            "body": protocol.canonical_result_comment(result),
            "user": {"login": "github-actions[bot]"},
        }]
        duplicate = prepare.prepare_completed_result(
            dict(REQUEST), prior, repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=3, run_id=4, run_attempt=1, started_at="2026-08-16T08:00:00Z",
            eshm20_source_model_child_receipts_acquirer=lambda: self.fail("worker ran on duplicate"),
        )
        self.assertEqual(duplicate["status"], "duplicate")

        def failed():
            raise worker.Eshm20SourceModelChildReceiptError("PRIVATE_PROVIDER_URL_AND_BODY")
        stream = io.StringIO()
        with redirect_stderr(stream):
            blocked = prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
                source_comment_id=5, run_id=6, run_attempt=1, started_at="2026-08-16T08:00:00Z",
                eshm20_source_model_child_receipts_acquirer=failed,
            )
        self.assertEqual(blocked["status"], "blocked")
        self.assertNotIn("PRIVATE_PROVIDER", stream.getvalue())

    def test_target_execution_mismatch_fails_before_worker(self) -> None:
        with self.assertRaises(prepare.ProtocolError):
            prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="b" * 40,
                source_comment_id=1, run_id=2, run_attempt=1, started_at="2026-08-16T08:00:00Z",
                eshm20_source_model_child_receipts_acquirer=lambda: self.fail("worker must not run"),
            )

    def test_portable_schemas_close_issue_and_exact_cardinality(self) -> None:
        request_schema = json.loads(Path("schemas/agent-action-request-v1.schema.json").read_text(encoding="utf-8"))
        result_schema = json.loads(Path("schemas/agent-action-result-v1.schema.json").read_text(encoding="utf-8"))
        self.assertIn(ACTION, request_schema["properties"]["action"]["enum"])
        self.assertIn(ACTION, result_schema["properties"]["action"]["enum"])
        child_set = result_schema["$defs"]["efehrEshm20SourceModelChildReceiptSet"]
        self.assertEqual(child_set["properties"]["child_count"]["const"], 51)
        self.assertEqual(child_set["properties"]["receipts"]["minItems"], 51)
        self.assertEqual(child_set["properties"]["receipts"]["maxItems"], 51)
        self.assertFalse(child_set["additionalProperties"])
        child = result_schema["$defs"]["efehrEshm20SourceModelChildReceipt"]
        self.assertFalse(child["additionalProperties"])
        self.assertNotIn("requested_url", child["properties"])
        self.assertNotIn("final_url", child["properties"])


if __name__ == "__main__":
    unittest.main()
