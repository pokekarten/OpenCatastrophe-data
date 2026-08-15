# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import acquire_eshm20_first_order_receipts as worker
from scripts.agent_action_protocol import semantic_request_id
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target
from scripts.prepare_agent_action_result import prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

ACTION = "efehr_eshm20_first_order_receipts"
DATASET = "efehr.eshm20"
ISSUE = 361
EXECUTION_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"


def request(**changes):
    value = {
        "schema_version": "oc-action-request-v1",
        "action": ACTION,
        "issue": ISSUE,
        "target_sha": EXECUTION_SHA,
        "dataset_id": DATASET,
        "requester": "synthetic-361-test",
    }
    value.update(changes)
    return value


def receipt_set():
    items = []
    for index, spec in enumerate(worker.DEPENDENCIES, start=1):
        target = validate_target(
            source_issue=worker.SOURCE_ISSUE,
            dataset_id=worker.DATASET_ID,
            project_id=worker.PROJECT_ID,
            commit_sha=worker.COMMIT_SHA,
            repository_path=spec.repository_path,
        )
        url = raw_file_api_url(target)
        items.append(
            {
                "schema_version": "oc-efehr-gitlab-artifact-receipt-v1",
                "source_issue": worker.SOURCE_ISSUE,
                "dataset_id": worker.DATASET_ID,
                "provider_host": worker.PROVIDER_HOST,
                "project_id": worker.PROJECT_ID,
                "project_path": worker.PROJECT_PATH,
                "commit_sha": worker.COMMIT_SHA,
                "repository_path": spec.repository_path,
                "requested_url": url,
                "final_url": url,
                "retrieved_at": f"2026-08-15T10:10:0{index}Z",
                "byte_count": 100 + index,
                "sha256": f"{index}" * 64,
                "content_type": "application/octet-stream",
                "etag": f'"synthetic-{index}"',
                "external_bytes_persisted": False,
                "publication_authorized": False,
                "parent_result_comment_id": worker.SELECTION_RESULT_COMMENT_ID,
                "parent_section": spec.parent_section,
                "parent_option": spec.parent_option,
            }
        )
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "provider_host": worker.PROVIDER_HOST,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "selection_request_comment_id": worker.SELECTION_REQUEST_COMMENT_ID,
        "selection_result_comment_id": worker.SELECTION_RESULT_COMMENT_ID,
        "selection_run_id": worker.SELECTION_RUN_ID,
        "selection_execution_sha": worker.SELECTION_EXECUTION_SHA,
        "retrieved_at": "2026-08-15T10:10:03Z",
        "receipts": items,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def pass_result(receipt=None):
    evidence_receipt = receipt_set() if receipt is None else receipt
    return {
        "schema_version": "oc-action-result-v1",
        "semantic_request_id": semantic_request_id(request(), EXECUTION_SHA, REPOSITORY),
        "repository": REPOSITORY,
        "action": ACTION,
        "source_issue": ISSUE,
        "source_comment_id": 123,
        "target_sha": EXECUTION_SHA,
        "dataset_id": DATASET,
        "execution_sha": EXECUTION_SHA,
        "run_id": 456,
        "run_attempt": 1,
        "started_at": "2026-08-15T10:10:00Z",
        "finished_at": "2026-08-15T10:10:04Z",
        "phase": "acquisition_receipt",
        "status": "pass",
        "external_bytes_persisted": False,
        "evidence": {
            "request_validated": True,
            "ledger_scan_complete": True,
            "prior_result_reused": False,
            ACTION: evidence_receipt,
        },
        "duplicate_result_comment_id": None,
        "failure_class": None,
    }


class Eshm20FirstOrderActionWiringTests(unittest.TestCase):
    def test_request_is_closed_to_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(request(), expected_issue=ISSUE), request())
        for mutation in (
            {"issue": ISSUE + 1},
            {"dataset_id": "other.dataset"},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(RequestError):
                    validate_request(request(**mutation), expected_issue=mutation.get("issue", ISSUE))

    def test_target_sha_must_equal_trusted_execution_sha(self) -> None:
        with self.assertRaisesRegex(Exception, "target_sha"):
            prepare_completed_result(
                request(target_sha="b" * 40),
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=123,
                run_id=456,
                run_attempt=1,
                started_at="2026-08-15T10:10:00Z",
                eshm20_first_order_acquirer=mock.Mock(return_value=receipt_set()),
            )

    def test_dedup_happens_before_provider_work(self) -> None:
        prior = pass_result()
        comments = [
            {
                "id": 999,
                "user": {"login": "github-actions[bot]"},
                "body": "<!-- oc-action-result-v1 -->\n"
                + json.dumps(prior, sort_keys=True, separators=(",", ":")),
            }
        ]
        acquirer = mock.Mock(side_effect=AssertionError("must not run"))
        result = prepare_completed_result(
            request(),
            comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=124,
            run_id=457,
            run_attempt=1,
            started_at="2026-08-15T10:10:05Z",
            eshm20_first_order_acquirer=acquirer,
        )
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["duplicate_result_comment_id"], 999)
        acquirer.assert_not_called()

    def test_result_rebinds_exact_three_receipts_and_parent_selection(self) -> None:
        result = pass_result()
        self.assertEqual(validate_result(result), result)

        mutations = []
        for field, value in (
            ("selection_result_comment_id", 1),
            ("selection_run_id", 1),
            ("selection_execution_sha", "b" * 40),
            ("dependency_inventory_authorized", True),
            ("publication_authorized", True),
        ):
            mutated = copy.deepcopy(receipt_set())
            mutated[field] = value
            mutations.append(mutated)

        missing = copy.deepcopy(receipt_set())
        missing["receipts"].pop()
        mutations.append(missing)
        extra = copy.deepcopy(receipt_set())
        extra["receipts"].append(copy.deepcopy(extra["receipts"][-1]))
        mutations.append(extra)
        reordered = copy.deepcopy(receipt_set())
        reordered["receipts"][0], reordered["receipts"][1] = (
            reordered["receipts"][1],
            reordered["receipts"][0],
        )
        mutations.append(reordered)

        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ResultError):
                    validate_result(pass_result(mutated))

    def test_nested_path_parent_digest_type_and_authority_drift_fail_closed(self) -> None:
        cases = []
        for field, value in (
            ("repository_path", worker.DEPENDENCIES[1].repository_path),
            ("parent_section", "wrong"),
            ("parent_option", "wrong"),
            ("parent_result_comment_id", 1),
            ("sha256", "A" * 64),
            ("byte_count", True),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
        ):
            mutated = copy.deepcopy(receipt_set())
            mutated["receipts"][0][field] = value
            cases.append(mutated)
        for mutated in cases:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ResultError):
                    validate_result(pass_result(mutated))

    def test_receipt_times_are_ordered_and_outer_time_is_final_member(self) -> None:
        reversed_time = copy.deepcopy(receipt_set())
        reversed_time["receipts"][1]["retrieved_at"] = "2026-08-15T10:10:00Z"
        with self.assertRaises(ResultError):
            validate_result(pass_result(reversed_time))

        wrong_outer = copy.deepcopy(receipt_set())
        wrong_outer["retrieved_at"] = "2026-08-15T10:10:02Z"
        with self.assertRaises(ResultError):
            validate_result(pass_result(wrong_outer))

    def test_action_time_bounds_apply_to_final_retrieval(self) -> None:
        result = pass_result()
        result["finished_at"] = "2026-08-15T10:10:02Z"
        with self.assertRaisesRegex(ResultError, "start/finish"):
            validate_result(result)

    def test_every_member_retrieval_is_inside_action_bounds(self) -> None:
        mutated = receipt_set()
        mutated["receipts"][0]["retrieved_at"] = "2026-08-15T10:09:59Z"
        with self.assertRaisesRegex(ResultError, r"receipts\[0\].*start/finish"):
            validate_result(pass_result(mutated))

    def test_worker_failure_is_closed_and_carries_no_payload(self) -> None:
        from scripts.acquire_eshm20_first_order_receipts import Eshm20FirstOrderReceiptError

        result = prepare_completed_result(
            request(),
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=123,
            run_id=456,
            run_attempt=1,
            started_at="2026-08-15T10:10:00Z",
            eshm20_first_order_acquirer=mock.Mock(
                side_effect=Eshm20FirstOrderReceiptError("bounded failure")
            ),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertIsNone(result["evidence"][ACTION])

    def test_portable_result_schema_has_closed_361_phase_contract(self) -> None:
        schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn(ACTION, schema["properties"]["action"]["enum"])
        evidence = schema["properties"]["evidence"]["oneOf"]
        self.assertTrue(any(ACTION in branch.get("required", []) for branch in evidence))
        guards = schema["allOf"]
        phase_guard = next(
            branch
            for branch in guards
            if branch.get("if", {}).get("properties")
            == {"phase": {"const": "acquisition_receipt"}}
        )
        self.assertIn(ACTION, phase_guard["then"]["properties"]["action"]["enum"])

        def guard_for(status=None):
            expected = {
                "phase": {"const": "acquisition_receipt"},
                "action": {"const": ACTION},
            }
            if status is not None:
                expected["status"] = {"const": status}
            return next(
                branch
                for branch in guards
                if branch.get("if", {}).get("properties") == expected
            )

        binding = guard_for()
        self.assertEqual(binding["then"]["properties"]["source_issue"], {"const": ISSUE})
        self.assertEqual(binding["then"]["properties"]["dataset_id"], {"const": DATASET})
        self.assertEqual(binding["then"]["properties"]["evidence"], {"required": [ACTION]})
        self.assertEqual(
            guard_for("pass")["then"]["properties"]["evidence"]["properties"][ACTION],
            {"$ref": "#/$defs/efehrEshm20FirstOrderReceiptSet"},
        )
        self.assertEqual(
            guard_for("blocked")["then"]["properties"]["evidence"]["properties"][ACTION],
            {"type": "null"},
        )


if __name__ == "__main__":
    unittest.main()
