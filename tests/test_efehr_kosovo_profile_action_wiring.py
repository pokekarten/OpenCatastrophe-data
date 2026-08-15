# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from scripts import agent_action_protocol as protocol
from scripts import prepare_agent_action_result as prepare
from scripts import profile_efehr_kosovo_exposure as profile_worker
from scripts import validate_agent_action_request as request_validator
from scripts import validate_agent_action_result as result_validator

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "b" * 40
STARTED = "2026-08-15T08:10:00Z"
FINISHED = "2026-08-15T08:10:02Z"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_kosovo_exposure_profile",
    "issue": 351,
    "target_sha": EXECUTION_SHA,
    "dataset_id": profile_worker.DATASET_ID,
    "requester": "test-351-profile",
}


def profile_receipt(*, profiled_at: str | None = FINISHED) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": profile_worker.SCHEMA_VERSION,
        "source_issue": profile_worker.SOURCE_ISSUE,
        "dataset_id": profile_worker.DATASET_ID,
        "project_id": profile_worker.PROJECT_ID,
        "project_path": profile_worker.PROJECT_PATH,
        "commit_sha": profile_worker.COMMIT_SHA,
        "repository_path": profile_worker.REPOSITORY_PATH,
        "receipt_comment_id": profile_worker.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": profile_worker.RECEIPT_EXECUTION_SHA,
        "byte_count": profile_worker.EXPECTED_BYTE_COUNT,
        "sha256": profile_worker.EXPECTED_SHA256,
        "profile": {
            "schema_version": profile_worker.SCHEMA_VERSION,
            "parser": {
                "encoding": "utf-8",
                "bom_present": False,
                "delimiter": ",",
                "line_endings": {"crlf_count": 0, "lf_count": 3, "cr_count": 0},
            },
            "record_count": 2,
            "header": ["field_a", "field_b"],
            "columns": [
                {
                    "name": "field_a",
                    "record_count": 2,
                    "empty_count": 0,
                    "nonempty_count": 2,
                    "distinct_count": 2,
                    "exact_value_set_sha256": "1" * 64,
                    "decimal_summary": {
                        "all_nonempty_decimal": False,
                        "finite_decimal_count": 0,
                        "leading_or_trailing_whitespace_count": 0,
                    },
                },
                {
                    "name": "field_b",
                    "record_count": 2,
                    "empty_count": 1,
                    "nonempty_count": 1,
                    "distinct_count": 2,
                    "exact_value_set_sha256": "2" * 64,
                    "decimal_summary": {
                        "all_nonempty_decimal": True,
                        "finite_decimal_count": 1,
                        "leading_or_trailing_whitespace_count": 0,
                    },
                },
            ],
            "raw_rows_returned": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        },
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    if profiled_at is not None:
        receipt["profiled_at"] = profiled_at
    return receipt


def action_result(receipt: dict[str, object] | None) -> dict[str, object]:
    return prepare.build_acquisition_result(
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


class KosovoExposureProfileActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_has_no_provider_target_surface(self) -> None:
        self.assertEqual(request_validator.validate_request(dict(REQUEST), expected_issue=351), REQUEST)
        for field, value in (
            ("issue", 282),
            ("dataset_id", "other.dataset"),
            ("repository_path", profile_worker.REPOSITORY_PATH),
            ("project_id", profile_worker.PROJECT_ID),
            ("commit_sha", profile_worker.COMMIT_SHA),
            ("url", "https://example.invalid"),
            ("taxonomy", "field_a"),
        ):
            mutated = dict(REQUEST)
            mutated[field] = value
            with self.subTest(field=field), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(mutated, expected_issue=351)

    def test_network_semantic_identity_requires_trusted_execution_head(self) -> None:
        protocol.semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(protocol.ProtocolError, "target_sha"):
            protocol.semantic_request_id(REQUEST, "c" * 40, REPOSITORY)

    def test_dispatch_profiles_only_after_dedup_and_stamps_profile_completion(self) -> None:
        calls: list[str] = []
        with patch.object(prepare, "utc_now", return_value=FINISHED):
            result = prepare.prepare_completed_result(
                REQUEST,
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=100,
                run_id=200,
                run_attempt=1,
                started_at=STARTED,
                kosovo_profile_acquirer=lambda: calls.append("profile") or profile_receipt(profiled_at=None),
            )
        self.assertEqual(calls, ["profile"])
        self.assertEqual(result["status"], "pass")
        receipt = result["evidence"]["efehr_kosovo_exposure_profile"]
        self.assertEqual(receipt["profiled_at"], FINISHED)
        self.assertEqual(receipt["byte_count"], profile_worker.EXPECTED_BYTE_COUNT)
        self.assertEqual(receipt["sha256"], profile_worker.EXPECTED_SHA256)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

        comments = [{
            "id": 999,
            "body": protocol.canonical_result_comment(result),
            "user": {"login": "github-actions[bot]"},
        }]
        with patch.object(prepare, "utc_now", return_value=FINISHED):
            duplicate = prepare.prepare_completed_result(
                REQUEST,
                comments,
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=101,
                run_id=201,
                run_attempt=1,
                started_at=STARTED,
                kosovo_profile_acquirer=lambda: self.fail("dedup must precede provider/profile work"),
            )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)

    def test_profile_worker_failure_is_closed_without_payload(self) -> None:
        def blocked():
            raise profile_worker.ExposureProfileError("synthetic provider/profile failure")
        with patch.object(prepare, "utc_now", return_value=FINISHED):
            result = prepare.prepare_completed_result(
                REQUEST,
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=100,
                run_id=200,
                run_attempt=1,
                started_at=STARTED,
                kosovo_profile_acquirer=blocked,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertIsNone(result["evidence"]["efehr_kosovo_exposure_profile"])

    def test_result_rebinds_exact_receipt_profile_and_rejects_leakage(self) -> None:
        valid = profile_receipt()
        result = action_result(valid)
        self.assertEqual(result["source_issue"], 351)
        self.assertEqual(result["evidence"]["efehr_kosovo_exposure_profile"]["source_issue"], 282)

        top_mutations = (
            ("byte_count", profile_worker.EXPECTED_BYTE_COUNT + 1),
            ("sha256", "0" * 64),
            ("receipt_comment_id", profile_worker.RECEIPT_COMMENT_ID + 1),
            ("receipt_execution_sha", "0" * 40),
            ("publication_authorized", True),
        )
        for field, value in top_mutations:
            with self.subTest(top_field=field):
                mutated = copy.deepcopy(valid)
                mutated[field] = value
                with self.assertRaises(result_validator.ResultError):
                    action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["provider_body"] = "forbidden"
        with self.assertRaisesRegex(result_validator.ResultError, "fields mismatch"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["raw_rows_returned"] = True
        with self.assertRaisesRegex(result_validator.ResultError, "raw_rows_returned"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["header"] = ["field_a", "field_a"]
        with self.assertRaisesRegex(result_validator.ResultError, "unique"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["columns"][0]["name"] = "field_b"
        with self.assertRaisesRegex(result_validator.ResultError, "order/name"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["columns"][0]["empty_count"] = 1
        with self.assertRaisesRegex(result_validator.ResultError, "conserve"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["columns"][0]["exact_value_set_sha256"] = "ABC"
        with self.assertRaisesRegex(result_validator.ResultError, "SHA-256"):
            action_result(mutated)

    def test_result_rejects_worker_impossible_and_type_confused_profile_states(self) -> None:
        valid = profile_receipt()

        mutated = copy.deepcopy(valid)
        mutated["profile"]["parser"]["encoding"] = []
        with self.assertRaises(result_validator.ResultError):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["header"][0] = []
        with self.assertRaises(result_validator.ResultError):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        decimal = mutated["profile"]["columns"][1]["decimal_summary"]
        decimal["leading_or_trailing_whitespace_count"] = 1
        with self.assertRaisesRegex(result_validator.ResultError, "overlap"):
            action_result(mutated)

        mutated = copy.deepcopy(valid)
        mutated["profile"]["columns"][1]["decimal_summary"]["all_nonempty_decimal"] = False
        with self.assertRaisesRegex(result_validator.ResultError, "all_nonempty_decimal"):
            action_result(mutated)

    def test_profiled_at_must_be_inside_action_bounds(self) -> None:
        mutated = profile_receipt(profiled_at="2026-08-15T08:10:03Z")
        with self.assertRaisesRegex(result_validator.ResultError, "profiled_at"):
            action_result(mutated)


if __name__ == "__main__":
    unittest.main()
