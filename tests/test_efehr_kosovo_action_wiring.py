# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_kosovo_receipt import (
    COMMIT_SHA,
    DATASET_ID,
    MAX_FILE_BYTES,
    OPERATION_ID,
    PROJECT_ID,
    REPOSITORY_PATH,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
)
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment, semantic_request_id
from scripts.efehr_gitlab_receipt import PROJECTS, PROVIDER_HOST, raw_file_api_url, validate_target
from scripts.prepare_agent_action_result import (
    build_acquisition_result,
    ledger_issue_for_request,
    prepare_completed_result,
)
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "c" * 40
STARTED = "2026-08-14T11:00:00Z"
FINISHED = "2026-08-14T11:00:02Z"

REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_kosovo_exposure_receipt",
    "issue": 328,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot12-kosovo-exposure",
}

TARGET = validate_target(
    source_issue=SOURCE_ISSUE,
    dataset_id=DATASET_ID,
    project_id=PROJECT_ID,
    commit_sha=COMMIT_SHA,
    repository_path=REPOSITORY_PATH,
)
RAW_URL = raw_file_api_url(TARGET)

RECEIPT = {
    "schema_version": SCHEMA_VERSION,
    "operation_id": OPERATION_ID,
    "source_issue": SOURCE_ISSUE,
    "dataset_id": DATASET_ID,
    "provider_host": PROVIDER_HOST,
    "project_id": PROJECT_ID,
    "project_path": PROJECTS[PROJECT_ID]["project_path"],
    "commit_sha": COMMIT_SHA,
    "repository_path": REPOSITORY_PATH,
    "requested_url": RAW_URL,
    "final_url": RAW_URL,
    "retrieved_at": "2026-08-14T11:00:01Z",
    "byte_count": 42,
    "sha256": "b" * 64,
    "content_type": "text/csv",
    "etag": "\"synthetic-etag\"",
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


class EfehrKosovoActionWiringTests(unittest.TestCase):
    def test_request_accepts_only_dispatch_issue_and_frozen_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=328), REQUEST)
        with self.assertRaisesRegex(RequestError, "restricted to issue 328"):
            validate_request(dict(REQUEST, issue=282))
        with self.assertRaisesRegex(RequestError, "frozen ESRM20 exposure dataset"):
            validate_request(dict(REQUEST, dataset_id="efehr.other"))

    def test_request_rejects_every_caller_controlled_target_variant(self) -> None:
        mutations = (
            ("repository_path", "_exposure_models/ReadMe_Exposure_Model_Format.txt"),
            ("project_id", 197),
            ("commit_sha", "d" * 40),
            ("ref", "main"),
            ("url", "https://example.invalid/data"),
            ("country", "Albania"),
            ("occupancy", "Com"),
            ("parser", "csv"),
            ("headers", {"Accept": "text/csv"}),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                with self.assertRaisesRegex(RequestError, "unexpected"):
                    validate_request(dict(REQUEST, **{field: value}))

    def test_network_semantic_identity_requires_trusted_execution_head(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal trusted execution_sha"):
            semantic_request_id(REQUEST, "d" * 40, REPOSITORY)

    def test_network_ledger_scope_is_exact_dispatch_issue(self) -> None:
        self.assertEqual(ledger_issue_for_request(REQUEST), 328)

    def test_pass_result_separates_dispatch_issue_from_scientific_receipt_issue(self) -> None:
        result = acquisition_result()
        self.assertEqual(result["action"], "efehr_kosovo_exposure_receipt")
        self.assertEqual(result["source_issue"], 328)
        self.assertEqual(result["dataset_id"], DATASET_ID)
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(result["status"], "pass")
        receipt = result["evidence"]["efehr_kosovo_exposure_receipt"]
        self.assertEqual(receipt, RECEIPT)
        self.assertEqual(receipt["source_issue"], 282)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_receipt_rejects_target_operation_and_body_leakage_drift(self) -> None:
        mutations = (
            ("operation_id", "esrm20-exposure-format-readme-v1"),
            ("source_issue", 328),
            ("project_id", 197),
            ("commit_sha", "d" * 40),
            ("repository_path", "_exposure_models/ReadMe_Exposure_Model_Format.txt"),
            ("repository_path", "_exposure_models/Exposure_Model_Kosovo_Com.csv"),
            ("requested_url", "https://example.invalid/kosovo.csv"),
            ("final_url", "https://example.invalid/kosovo.csv"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                with self.assertRaises(ResultError):
                    acquisition_result(dict(RECEIPT, **{field: value}))
        with self.assertRaisesRegex(ResultError, "unexpected=.*provider_body"):
            acquisition_result(dict(RECEIPT, provider_body="secret bytes"))

    def test_receipt_rejects_unbounded_or_malformed_content(self) -> None:
        for field, value in (
            ("byte_count", MAX_FILE_BYTES + 1),
            ("sha256", "not-a-sha"),
            ("etag", "ok\nforged"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ResultError):
                    acquisition_result(dict(RECEIPT, **{field: value}))

    def test_blocked_worker_returns_closed_failure_without_receipt(self) -> None:
        calls = 0

        def blocked_worker():
            nonlocal calls
            calls += 1
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
            kosovo_exposure_acquirer=blocked_worker,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertIsNone(result["evidence"]["efehr_kosovo_exposure_receipt"])

    def test_existing_trusted_receipt_prevents_second_provider_call(self) -> None:
        prior = acquisition_result()
        calls = 0

        def forbidden_worker():
            nonlocal calls
            calls += 1
            self.fail("deduplicated action must not call EFEHR")

        duplicate = prepare_completed_result(
            REQUEST,
            [{"id": 999, "body": canonical_result_comment(prior), "user": {"login": "github-actions[bot]"}}],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            started_at="2020-01-01T00:00:00Z",
            kosovo_exposure_acquirer=forbidden_worker,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)
        self.assertEqual(duplicate["phase"], "request_validation")

    def test_outer_result_rejects_issue_or_dataset_drift(self) -> None:
        result = acquisition_result()
        for field, value in (("source_issue", 282), ("dataset_id", "efehr.other")):
            with self.subTest(field=field):
                with self.assertRaises(ResultError):
                    validate_result(dict(result, **{field: value}))


if __name__ == "__main__":
    unittest.main()
