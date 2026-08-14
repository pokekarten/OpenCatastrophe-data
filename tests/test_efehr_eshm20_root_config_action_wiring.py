# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.acquire_efehr_eshm20_root_config_receipt import (
    COMMIT_SHA,
    DATASET_ID,
    MAX_ROOT_CONFIG_BYTES,
    OPERATION_ID,
    PROJECT_ID,
    REPOSITORY_PATH,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
)
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment, semantic_request_id
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, raw_file_api_url, validate_target
from scripts.prepare_agent_action_result import build_acquisition_result, prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

ACTION = "efehr_eshm20_root_config_receipt"
OUTER_ISSUE = 335
REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "a" * 40
STARTED = "2026-08-14T14:00:00Z"
FINISHED = "2026-08-14T14:00:02Z"
TARGET = validate_target(
    source_issue=SOURCE_ISSUE,
    dataset_id=DATASET_ID,
    project_id=PROJECT_ID,
    commit_sha=COMMIT_SHA,
    repository_path=REPOSITORY_PATH,
)
RAW_URL = raw_file_api_url(TARGET)
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": OUTER_ISSUE,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot12-root-config",
}
RECEIPT = {
    "schema_version": SCHEMA_VERSION,
    "operation_id": OPERATION_ID,
    "source_issue": SOURCE_ISSUE,
    "dataset_id": DATASET_ID,
    "provider_host": PROVIDER_HOST,
    "project_id": PROJECT_ID,
    "project_path": "efehr/eshm20",
    "commit_sha": COMMIT_SHA,
    "repository_path": REPOSITORY_PATH,
    "requested_url": RAW_URL,
    "final_url": RAW_URL,
    "retrieved_at": "2026-08-14T14:00:01Z",
    "byte_count": 12345,
    "sha256": "b" * 64,
    "content_type": "text/plain",
    "etag": None,
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


def result_for(receipt=RECEIPT, *, request=REQUEST):
    return build_acquisition_result(
        request,
        repository=REPOSITORY,
        execution_sha=EXECUTION_SHA,
        source_comment_id=400,
        run_id=500,
        run_attempt=1,
        started_at=STARTED,
        finished_at=FINISHED,
        receipt=receipt,
    )


class Eshm20RootConfigActionWiringTests(unittest.TestCase):
    def test_request_is_closed_to_outer_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=OUTER_ISSUE), REQUEST)
        for field, value in (("issue", 281), ("issue", 336), ("dataset_id", "efehr.other")):
            with self.subTest(field=field, value=value), self.assertRaises(RequestError):
                validate_request(dict(REQUEST, **{field: value}), expected_issue=OUTER_ISSUE)

    def test_request_rejects_caller_controlled_provider_target_fields(self) -> None:
        for field, value in (
            ("url", RAW_URL),
            ("provider_host", PROVIDER_HOST),
            ("project_id", PROJECT_ID),
            ("commit_sha", COMMIT_SHA),
            ("repository_path", REPOSITORY_PATH),
            ("branch", "master"),
            ("headers", "x"),
        ):
            with self.subTest(field=field), self.assertRaises(RequestError):
                validate_request(dict(REQUEST, **{field: value}), expected_issue=OUTER_ISSUE)

    def test_network_action_requires_trusted_execution_sha(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal trusted execution_sha"):
            semantic_request_id(REQUEST, "c" * 40, REPOSITORY)

    def test_dispatch_is_dedup_first_and_binds_outer_and_nested_identity(self) -> None:
        calls: list[str] = []

        def acquirer():
            calls.append("called")
            return dict(RECEIPT)

        result = prepare_completed_result(
            REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=400,
            run_id=500,
            run_attempt=1,
            started_at=STARTED,
            eshm20_root_config_acquirer=acquirer,
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["source_issue"], OUTER_ISSUE)
        self.assertEqual(result["dataset_id"], DATASET_ID)
        nested = result["evidence"]["efehr_eshm20_root_config_receipt"]
        self.assertEqual(nested["source_issue"], SOURCE_ISSUE)
        self.assertEqual(nested["project_id"], PROJECT_ID)
        self.assertEqual(nested["commit_sha"], COMMIT_SHA)
        self.assertEqual(nested["repository_path"], REPOSITORY_PATH)
        self.assertFalse(nested["external_bytes_persisted"])
        self.assertFalse(nested["publication_authorized"])

        comments = [{
            "id": 777,
            "body": canonical_result_comment(result),
            "user": {"login": "github-actions[bot]"},
        }]
        duplicate = prepare_completed_result(
            REQUEST,
            comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=401,
            run_id=501,
            run_attempt=1,
            started_at=STARTED,
            eshm20_root_config_acquirer=lambda: self.fail("duplicate must not invoke provider worker"),
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 777)
        self.assertEqual(duplicate["phase"], "request_validation")

    def test_nested_receipt_fails_closed_on_authority_or_payload_drift(self) -> None:
        mutations = (
            ("source_issue", 320),
            ("dataset_id", "efehr.other"),
            ("provider_host", "example.invalid"),
            ("project_id", 186),
            ("project_path", "efehr/other"),
            ("commit_sha", "c" * 40),
            ("repository_path", "other.ini"),
            ("requested_url", "https://example.invalid/root.ini"),
            ("final_url", "https://example.invalid/root.ini"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("byte_count", MAX_ROOT_CONFIG_BYTES + 1),
            ("sha256", "not-a-digest"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = dict(RECEIPT, **{field: value})
                with self.assertRaises(ResultError):
                    result_for(mutated)

    def test_outer_result_issue_and_dataset_cannot_drift(self) -> None:
        result = result_for()
        for field, value in (("source_issue", SOURCE_ISSUE), ("dataset_id", "efehr.other")):
            with self.subTest(field=field):
                mutated = dict(result, **{field: value})
                with self.assertRaises(ResultError):
                    validate_result(mutated)

    def test_blocked_receipt_is_closed_and_contains_no_provider_payload(self) -> None:
        blocked = result_for(None)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"]["efehr_eshm20_root_config_receipt"])
        self.assertFalse(blocked["external_bytes_persisted"])


if __name__ == "__main__":
    unittest.main()
