# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_esrm20_event_hazard_receipts import (
    COMMIT_SHA,
    DATASET_ID,
    GROUP1_OPERATION_ID,
    GROUP1_REPOSITORY_PATH,
    GROUP2_OPERATION_ID,
    GROUP2_REPOSITORY_PATH,
    MAX_CONFIG_BYTES,
    PROJECT_ID,
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
STARTED = "2026-08-15T06:00:00Z"
FINISHED = "2026-08-15T06:00:02Z"


def request(group: int) -> dict[str, object]:
    return {
        "schema_version": "oc-action-request-v1",
        "action": f"esrm20_event_hazard_group{group}_receipt",
        "issue": 346,
        "target_sha": EXECUTION_SHA,
        "dataset_id": DATASET_ID,
        "requester": f"eq1-event-hazard-group{group}",
    }


def receipt(group: int) -> dict[str, object]:
    if group == 1:
        operation_id = GROUP1_OPERATION_ID
        repository_path = GROUP1_REPOSITORY_PATH
    elif group == 2:
        operation_id = GROUP2_OPERATION_ID
        repository_path = GROUP2_REPOSITORY_PATH
    else:  # pragma: no cover - test helper guard
        raise AssertionError("unsupported test group")
    target = validate_target(
        source_issue=SOURCE_ISSUE,
        dataset_id=DATASET_ID,
        project_id=PROJECT_ID,
        commit_sha=COMMIT_SHA,
        repository_path=repository_path,
    )
    raw_url = raw_file_api_url(target)
    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": operation_id,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": PROJECT_ID,
        "project_path": PROJECTS[PROJECT_ID]["project_path"],
        "commit_sha": COMMIT_SHA,
        "repository_path": repository_path,
        "requested_url": raw_url,
        "final_url": raw_url,
        "retrieved_at": "2026-08-15T06:00:01Z",
        "byte_count": 42,
        "sha256": "b" * 64,
        "content_type": "text/plain; charset=utf-8",
        "etag": "\"synthetic-etag\"",
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquisition_result(group: int, nested_receipt: dict[str, object] | None = None):
    return build_acquisition_result(
        request(group),
        repository=REPOSITORY,
        execution_sha=EXECUTION_SHA,
        source_comment_id=100 + group,
        run_id=200 + group,
        run_attempt=1,
        started_at=STARTED,
        finished_at=FINISHED,
        receipt=receipt(group) if nested_receipt is None else nested_receipt,
    )


class Esrm20EventHazardActionWiringTests(unittest.TestCase):
    def test_requests_are_closed_to_issue_346_and_frozen_dataset(self) -> None:
        for group in (1, 2):
            candidate = request(group)
            self.assertEqual(validate_request(dict(candidate), expected_issue=346), candidate)
            with self.assertRaisesRegex(RequestError, "restricted to issue 346"):
                validate_request(dict(candidate, issue=281))
            with self.assertRaisesRegex(RequestError, "frozen ESRM20 risk-input dataset"):
                validate_request(dict(candidate, dataset_id="efehr.other"))
        with self.assertRaisesRegex(RequestError, "unsupported action"):
            validate_request(dict(request(1), action="esrm20_event_hazard_group3_receipt"))

    def test_requests_reject_caller_controlled_group_or_provider_targets(self) -> None:
        mutations = (
            ("group", 2),
            ("repository_path", GROUP2_REPOSITORY_PATH),
            ("project_id", 269),
            ("commit_sha", "d" * 40),
            ("ref", "main"),
            ("url", "https://example.invalid/config.ini"),
            ("headers", {"Accept": "text/plain"}),
            ("parser", "ini"),
            ("content_selector", "GMPE"),
        )
        for group in (1, 2):
            for field, value in mutations:
                with self.subTest(group=group, field=field):
                    with self.assertRaisesRegex(RequestError, "unexpected"):
                        validate_request(dict(request(group), **{field: value}))

    def test_both_actions_require_trusted_execution_head_and_issue_local_ledger(self) -> None:
        for group in (1, 2):
            candidate = request(group)
            semantic_request_id(candidate, EXECUTION_SHA, REPOSITORY)
            with self.assertRaisesRegex(ProtocolError, "target_sha must equal trusted execution_sha"):
                semantic_request_id(candidate, "d" * 40, REPOSITORY)
            self.assertEqual(ledger_issue_for_request(candidate), 346)

    def test_each_outer_action_dispatches_only_its_matching_worker(self) -> None:
        for group in (1, 2):
            calls = {1: 0, 2: 0}

            def group1_worker():
                calls[1] += 1
                if group != 1:
                    self.fail("Group2 action reached Group1 worker")
                return receipt(1)

            def group2_worker():
                calls[2] += 1
                if group != 2:
                    self.fail("Group1 action reached Group2 worker")
                return receipt(2)

            result = prepare_completed_result(
                request(group),
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=300 + group,
                run_id=400 + group,
                run_attempt=1,
                started_at=STARTED,
                event_hazard_group1_acquirer=group1_worker,
                event_hazard_group2_acquirer=group2_worker,
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual(calls[group], 1)
            self.assertEqual(calls[3 - group], 0)

    def test_pass_results_keep_outer_issue_346_and_nested_science_issue_281_distinct(self) -> None:
        for group in (1, 2):
            result = acquisition_result(group)
            field = f"esrm20_event_hazard_group{group}_receipt"
            self.assertEqual(result["source_issue"], 346)
            self.assertEqual(result["dataset_id"], DATASET_ID)
            self.assertEqual(result["phase"], "acquisition_receipt")
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["evidence"][field]["source_issue"], 281)
            self.assertFalse(result["evidence"][field]["external_bytes_persisted"])
            self.assertFalse(result["evidence"][field]["publication_authorized"])

    def test_cross_group_receipt_substitution_fails_closed(self) -> None:
        with self.assertRaises(ResultError):
            acquisition_result(1, receipt(2))
        with self.assertRaises(ResultError):
            acquisition_result(2, receipt(1))

    def test_receipts_reject_identity_payload_and_bounds_drift(self) -> None:
        for group in (1, 2):
            base = receipt(group)
            other_path = GROUP2_REPOSITORY_PATH if group == 1 else GROUP1_REPOSITORY_PATH
            mutations = (
                ("operation_id", GROUP2_OPERATION_ID if group == 1 else GROUP1_OPERATION_ID),
                ("source_issue", 346),
                ("project_id", 197),
                ("commit_sha", "d" * 40),
                ("repository_path", other_path),
                ("requested_url", "https://example.invalid/config.ini"),
                ("final_url", "https://example.invalid/config.ini"),
                ("byte_count", MAX_CONFIG_BYTES + 1),
                ("sha256", "not-a-sha"),
                ("etag", "ok\nforged"),
                ("external_bytes_persisted", True),
                ("publication_authorized", True),
            )
            for field, value in mutations:
                with self.subTest(group=group, field=field):
                    with self.assertRaises(ResultError):
                        acquisition_result(group, dict(base, **{field: value}))
            with self.assertRaisesRegex(ResultError, "unexpected=.*provider_body"):
                acquisition_result(group, dict(base, provider_body="secret bytes"))

    def test_blocked_worker_is_closed_without_receipt(self) -> None:
        for group in (1, 2):
            calls = 0

            def blocked_worker():
                nonlocal calls
                calls += 1
                raise EfehrAcquisitionError("synthetic provider failure")

            kwargs = (
                {"event_hazard_group1_acquirer": blocked_worker}
                if group == 1
                else {"event_hazard_group2_acquirer": blocked_worker}
            )
            result = prepare_completed_result(
                request(group),
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=500 + group,
                run_id=600 + group,
                run_attempt=1,
                started_at=STARTED,
                **kwargs,
            )
            field = f"esrm20_event_hazard_group{group}_receipt"
            self.assertEqual(calls, 1)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["failure_class"], "acquisition_failed")
            self.assertIsNone(result["evidence"][field])

    def test_existing_trusted_result_prevents_second_provider_call(self) -> None:
        for group in (1, 2):
            prior = acquisition_result(group)
            calls = 0

            def forbidden_worker():
                nonlocal calls
                calls += 1
                self.fail("deduplicated event-hazard action must not call provider")

            kwargs = (
                {"event_hazard_group1_acquirer": forbidden_worker}
                if group == 1
                else {"event_hazard_group2_acquirer": forbidden_worker}
            )
            duplicate = prepare_completed_result(
                request(group),
                [{"id": 900 + group, "body": canonical_result_comment(prior), "user": {"login": "github-actions[bot]"}}],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=700 + group,
                run_id=800 + group,
                run_attempt=1,
                started_at=STARTED,
                **kwargs,
            )
            self.assertEqual(calls, 0)
            self.assertEqual(duplicate["status"], "duplicate")
            self.assertEqual(duplicate["phase"], "request_validation")
            self.assertEqual(duplicate["duplicate_result_comment_id"], 900 + group)

    def test_outer_result_rejects_issue_or_dataset_drift(self) -> None:
        for group in (1, 2):
            result = acquisition_result(group)
            for field, value in (("source_issue", 281), ("dataset_id", "efehr.other")):
                with self.subTest(group=group, field=field):
                    with self.assertRaises(ResultError):
                        validate_result(dict(result, **{field: value}))


if __name__ == "__main__":
    unittest.main()
