# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest

from scripts.acquire_efehr_esrm20_mapping_receipt import (
    COMMIT_SHA, DATASET_ID, MAX_FILE_BYTES, OPERATION_ID, PROJECT_ID,
    REPOSITORY_PATH, SCHEMA_VERSION, SOURCE_ISSUE,
)
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment, semantic_request_id
from scripts.efehr_gitlab_receipt import PROJECTS, PROVIDER_HOST, raw_file_api_url, validate_target
from scripts.prepare_agent_action_result import build_acquisition_result, ledger_issue_for_request, prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "c" * 40
ACTION = "esrm20_exposure_vulnerability_mapping_receipt"
CONTROL_ISSUE = 340
STARTED = "2026-08-15T12:00:00Z"
FINISHED = "2026-08-15T12:00:02Z"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": CONTROL_ISSUE,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DATASET_ID,
    "requester": "slot-eq1-mapping-receipt",
}
TARGET = validate_target(
    source_issue=SOURCE_ISSUE, dataset_id=DATASET_ID, project_id=PROJECT_ID,
    commit_sha=COMMIT_SHA, repository_path=REPOSITORY_PATH,
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
    "retrieved_at": "2026-08-15T12:00:01Z",
    "byte_count": 42,
    "sha256": "b" * 64,
    "content_type": "text/csv",
    "etag": "\"synthetic-etag\"",
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


def acquisition_result(receipt=RECEIPT):
    return build_acquisition_result(
        REQUEST, repository=REPOSITORY, execution_sha=EXECUTION_SHA,
        source_comment_id=100, run_id=200, run_attempt=1,
        started_at=STARTED, finished_at=FINISHED, receipt=receipt,
    )


class Esrm20MappingActionWiringTests(unittest.TestCase):
    def test_request_is_closed_to_control_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=CONTROL_ISSUE), REQUEST)
        for change in ({"issue": 283}, {"dataset_id": "efehr.other"}):
            with self.subTest(change=change), self.assertRaises(RequestError):
                validate_request(dict(REQUEST, **change))

    def test_request_rejects_caller_target_and_interpretation_selectors(self) -> None:
        for key, value in (
            ("url", "https://example.invalid"), ("repository_path", "other.csv"),
            ("project_id", 1), ("commit_sha", "d" * 40), ("ref", "main"),
            ("taxonomy", "secret"), ("vulnerability_file", "secret.xml"),
            ("parser", "csv"), ("headers", {"Accept": "text/csv"}),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(RequestError, "unexpected"):
                validate_request(dict(REQUEST, **{key: value}))

    def test_network_identity_and_ledger_are_bound_to_trusted_head_and_issue(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal"):
            build_acquisition_result(
                REQUEST, repository=REPOSITORY, execution_sha="d" * 40,
                source_comment_id=99, run_id=199, run_attempt=1,
                started_at=STARTED, finished_at=FINISHED, receipt=RECEIPT,
            )
        self.assertEqual(ledger_issue_for_request(REQUEST), CONTROL_ISSUE)

    def test_pass_result_separates_control_issue_from_scientific_source(self) -> None:
        result = acquisition_result()
        self.assertEqual(validate_result(result), result)
        self.assertEqual(result["source_issue"], CONTROL_ISSUE)
        receipt = result["evidence"][ACTION]
        self.assertEqual(receipt["source_issue"], 283)
        self.assertEqual(receipt["repository_path"], REPOSITORY_PATH)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_receipt_rejects_drift_leakage_and_malformed_metadata(self) -> None:
        mutations = (
            ("operation_id", "other"), ("source_issue", 340), ("project_id", 1),
            ("commit_sha", "d" * 40), ("repository_path", "other.csv"),
            ("requested_url", "https://example.invalid"), ("final_url", "https://example.invalid"),
            ("external_bytes_persisted", True), ("publication_authorized", True),
            ("byte_count", MAX_FILE_BYTES + 1), ("byte_count", True),
            ("sha256", "not-a-sha"), ("etag", "ok\nforged"),
        )
        for key, value in mutations:
            with self.subTest(key=key), self.assertRaises(ResultError):
                acquisition_result(dict(RECEIPT, **{key: value}))
        with self.assertRaisesRegex(ResultError, "fields mismatch"):
            acquisition_result(dict(RECEIPT, provider_body="secret bytes"))

    def test_blocked_failure_is_value_free_and_dedup_prevents_provider_call(self) -> None:
        def blocked_worker():
            raise EfehrAcquisitionError("synthetic provider detail")

        stderr = StringIO()
        with redirect_stderr(stderr):
            blocked = prepare_completed_result(
                REQUEST, [], repository=REPOSITORY, execution_sha=EXECUTION_SHA,
                source_comment_id=101, run_id=201, run_attempt=1, started_at=STARTED,
                esrm20_mapping_acquirer=blocked_worker,
            )
        self.assertNotIn("synthetic provider detail", stderr.getvalue())
        self.assertIn("mapping receipt acquisition failed closed", stderr.getvalue())
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"][ACTION])
        self.assertNotIn("synthetic provider detail", json.dumps(blocked, sort_keys=True))

        prior = acquisition_result()
        calls = 0
        def forbidden_worker():
            nonlocal calls
            calls += 1
            self.fail("deduplicated action must not call EFEHR")

        duplicate = prepare_completed_result(
            REQUEST,
            [{"id": 999, "body": canonical_result_comment(prior), "user": {"login": "github-actions[bot]"}}],
            repository=REPOSITORY, execution_sha=EXECUTION_SHA,
            source_comment_id=102, run_id=202, run_attempt=1, started_at=STARTED,
            esrm20_mapping_acquirer=forbidden_worker,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)

    def test_portable_schemas_cover_request_and_successful_result(self) -> None:
        root = Path(__file__).resolve().parents[1]
        request_schema = json.loads((root / "schemas/agent-action-request-v1.schema.json").read_text())
        result_schema = json.loads((root / "schemas/agent-action-result-v1.schema.json").read_text())
        self.assertIn(ACTION, request_schema["properties"]["action"]["enum"])
        self.assertIn(ACTION, result_schema["properties"]["action"]["enum"])
        self.assertIn("esrm20ExposureVulnerabilityMappingReceipt", result_schema["$defs"])
        serialized = json.dumps(result_schema, sort_keys=True)
        self.assertIn(ACTION, serialized)
        self.assertIn(REPOSITORY_PATH, serialized)


if __name__ == "__main__":
    unittest.main()
