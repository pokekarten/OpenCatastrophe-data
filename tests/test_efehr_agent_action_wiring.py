# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.acquire_efehr_gitlab_receipt import (
    DATASET_ID,
    EfehrAcquisitionError,
    MAX_CANARY_BYTES,
    OPERATION_ID,
    PROJECT_ID,
    RELEASE_TAG,
    REPOSITORY_PATH,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
    TAG_API_URL,
)
from scripts.agent_action_protocol import (
    ProtocolError,
    canonical_result_comment,
    semantic_request_id,
)
from scripts.efehr_gitlab_receipt import PROJECTS, PROVIDER_HOST, raw_file_api_url, validate_target
from scripts.prepare_agent_action_result import build_acquisition_result, prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "c" * 40
PROVIDER_COMMIT = "a" * 40
STARTED = "2026-08-13T11:00:00Z"
FINISHED = "2026-08-13T11:00:02Z"

REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_readme_receipt",
    "issue": 298,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot36-efehr-canary",
}

TARGET = validate_target(
    source_issue=SOURCE_ISSUE,
    dataset_id=DATASET_ID,
    project_id=PROJECT_ID,
    commit_sha=PROVIDER_COMMIT,
    repository_path=REPOSITORY_PATH,
)
RAW_URL = raw_file_api_url(TARGET)

RECEIPT = {
    "schema_version": SCHEMA_VERSION,
    "operation_id": OPERATION_ID,
    "release_tag": RELEASE_TAG,
    "tag_api_url": TAG_API_URL,
    "source_issue": SOURCE_ISSUE,
    "dataset_id": DATASET_ID,
    "provider_host": PROVIDER_HOST,
    "project_id": PROJECT_ID,
    "project_path": PROJECTS[PROJECT_ID]["project_path"],
    "commit_sha": PROVIDER_COMMIT,
    "repository_path": REPOSITORY_PATH,
    "requested_url": RAW_URL,
    "final_url": RAW_URL,
    "retrieved_at": "2026-08-13T11:00:01Z",
    "byte_count": 42,
    "sha256": "b" * 64,
    "content_type": "text/plain",
    "etag": '"synthetic-etag"',
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


def acquisition_result(receipt=RECEIPT):
    return build_acquisition_result(
        REQUEST,
        repository=REPOSITORY,
        execution_sha=EXECUTION_SHA,
        source_comment_id=100,
        run_id=200,
        run_attempt=1,
        started_at=STARTED,
        finished_at=FINISHED,
        receipt=receipt,
    )


class EfehrAgentActionWiringTests(unittest.TestCase):
    def test_request_accepts_only_frozen_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=298), REQUEST)

        with self.assertRaisesRegex(RequestError, "restricted to issue 298"):
            validate_request(dict(REQUEST, issue=282))
        with self.assertRaisesRegex(RequestError, "frozen ESRM20 exposure dataset"):
            validate_request(dict(REQUEST, dataset_id="efehr.other"))

    def test_request_rejects_caller_controlled_network_target_fields(self) -> None:
        for field, value in (
            ("repository_path", "_exposure_models/Exposure_Model_Kosovo_Res.csv"),
            ("project_id", 197),
            ("url", "https://example.invalid/data"),
        ):
            with self.subTest(field=field):
                mutated = dict(REQUEST)
                mutated[field] = value
                with self.assertRaisesRegex(RequestError, "unexpected"):
                    validate_request(mutated)

    def test_network_semantic_identity_requires_trusted_execution_head(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal trusted execution_sha"):
            semantic_request_id(REQUEST, "d" * 40, REPOSITORY)

    def test_pass_result_binds_exact_readme_receipt(self) -> None:
        result = acquisition_result()
        self.assertEqual(result["action"], "efehr_readme_receipt")
        self.assertEqual(result["source_issue"], 298)
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["evidence"]["efehr_readme_receipt"], RECEIPT)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["evidence"]["efehr_readme_receipt"]["publication_authorized"])

    def test_receipt_rejects_identity_and_publication_drift(self) -> None:
        mutations = (
            ("repository_path", "_exposure_models/Exposure_Model_Kosovo_Res.csv"),
            ("project_id", 197),
            ("release_tag", "latest"),
            ("commit_sha", "d" * 40),
            ("requested_url", "https://example.invalid/readme"),
            ("final_url", "https://example.invalid/readme"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = dict(RECEIPT)
                mutated[field] = value
                with self.assertRaises(ResultError):
                    acquisition_result(mutated)

    def test_receipt_rejects_unbounded_or_malformed_content(self) -> None:
        for field, value in (
            ("byte_count", MAX_CANARY_BYTES + 1),
            ("sha256", "not-a-sha"),
            ("etag", "ok\nforged"),
        ):
            with self.subTest(field=field):
                mutated = dict(RECEIPT)
                mutated[field] = value
                with self.assertRaises(ResultError):
                    acquisition_result(mutated)

    def test_blocked_worker_returns_closed_failure_without_receipt(self) -> None:
        def blocked_worker():
            raise EfehrAcquisitionError("synthetic provider failure")

        result = prepare_completed_result(
            REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            started_at="2020-01-01T00:00:00Z",
            efehr_acquirer=blocked_worker,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertIsNone(result["evidence"]["efehr_readme_receipt"])

    def test_existing_trusted_receipt_prevents_second_provider_call(self) -> None:
        prior = acquisition_result()
        comments = [
            {
                "id": 999,
                "body": canonical_result_comment(prior),
                "user": {"login": "github-actions[bot]"},
            }
        ]

        duplicate = prepare_completed_result(
            REQUEST,
            comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            started_at="2020-01-01T00:00:00Z",
            efehr_acquirer=lambda: self.fail("deduplicated action must not call EFEHR"),
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)
        self.assertEqual(duplicate["phase"], "request_validation")

    def test_result_validator_rejects_outer_issue_or_dataset_drift(self) -> None:
        result = acquisition_result()
        for field, value in (("source_issue", 282), ("dataset_id", "efehr.other")):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = value
                with self.assertRaises(ResultError):
                    validate_result(mutated)


if __name__ == "__main__":
    unittest.main()
