# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_runtime_residential_csv_receipt_action as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.prepare_agent_action_result import LedgerError

SHA = "a" * 40
OLD_SHA = "b" * 40


def request_body(*, sha: str = SHA, **overrides: object) -> str:
    payload: dict[str, object] = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "test-agent",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def worker_receipt(**overrides: object) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": subject.WORKER_OPERATION_ID,
        "source_issue": subject.SOURCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "requested_url": "https://gitlab.seismo.ethz.ch/fixed",
        "final_url": "https://gitlab.seismo.ethz.ch/fixed",
        "retrieved_at": "2026-08-20T23:40:00Z",
        "byte_count": 1234,
        "sha256": "1" * 64,
        "content_type": "text/csv; charset=utf-8",
        "etag": '"fixed"',
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    receipt.update(overrides)
    return receipt


def pass_result(sha: str) -> dict[str, object]:
    result = subject._base_result(execution_sha=sha)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipt": {
                "retrieved_at": "2026-08-20T23:40:00Z",
                "byte_count": 1234,
                "sha256": "1" * 64,
                "content_type": "text/csv; charset=utf-8",
                "etag": '"fixed"',
            },
        }
    )
    return result


def terminal_body(result: dict[str, object]) -> str:
    return subject.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class RuntimeResidentialCsvReceiptActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_rejects_target_widening(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=282, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)
        for body in (
            request_body(sha=OLD_SHA),
            request_body(repository_path="Exposure/OQ_Exposure_Input_Kosovo_Com.csv"),
            subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}',
            subject.REQUEST_MARKER + '\n{"schema_version":NaN}',
        ):
            with self.subTest(body=body), self.assertRaises(
                subject.RuntimeResidentialCsvReceiptActionError
            ):
                subject.validate_request(body, expected_issue=282, execution_sha=SHA)

    def test_pass_proves_only_fixed_byte_receipt(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_runtime_residential_csv_receipt",
            return_value=worker_receipt(),
        ):
            result = subject.run_receipt(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["receipt"]["byte_count"], 1234)
        self.assertEqual(result["receipt"]["sha256"], "1" * 64)
        for field in (
            "content_interpreted",
            "taxonomy_semantics_verified",
            "crs_semantics_verified",
            "value_semantics_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_acquisition_failure_is_sanitized_bounded_result(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_runtime_residential_csv_receipt",
            side_effect=EfehrAcquisitionError("private transport detail"),
        ):
            result = subject.run_receipt(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipt"])
        self.assertNotIn("private transport detail", json.dumps(result))

    def test_ledger_incomplete_is_bounded_preprovider_terminal(self) -> None:
        result = subject.ledger_incomplete_result(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "ledger_incomplete")
        self.assertIsNone(result["receipt"])
        self.assertEqual(subject.parse_terminal_result(terminal_body(result)), SHA)
        for field in (
            "content_interpreted",
            "taxonomy_semantics_verified",
            "crs_semantics_verified",
            "value_semantics_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_ledger_read_failure_still_fails_closed_before_provider(self) -> None:
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=LedgerError("private ledger detail"),
        ):
            with self.assertRaisesRegex(
                subject.RuntimeResidentialCsvReceiptActionError,
                "ledger is incomplete",
            ):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_worker_identity_and_authority_drift_fail_closed(self) -> None:
        for forged in (
            worker_receipt(repository_path="Exposure/OQ_Exposure_Input_Kosovo_Com.csv"),
            worker_receipt(operation_id="other"),
            worker_receipt(publication_authorized=True),
            worker_receipt(byte_count=True),
            worker_receipt(sha256="0" * 63),
        ):
            with self.subTest(forged=forged), mock.patch.object(
                subject,
                "acquire_runtime_residential_csv_receipt",
                return_value=forged,
            ):
                result = subject.run_receipt(execution_sha=SHA)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["receipt"])

    def test_historical_terminal_validated_under_own_sha_and_dedup_exact(self) -> None:
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": terminal_body(pass_result(OLD_SHA)),
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=OLD_SHA,
                )
            )

    def test_complete_ledger_is_validated_even_after_matching_terminal(self) -> None:
        malformed = pass_result(OLD_SHA)
        malformed["publication_authorized"] = True
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": terminal_body(pass_result(SHA)),
            },
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": terminal_body(malformed),
            },
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.RuntimeResidentialCsvReceiptActionError):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_non_bot_matching_marker_never_deduplicates(self) -> None:
        comments = [
            {"user": {"login": "pokekarten"}, "body": terminal_body(pass_result(SHA))}
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_terminal_publication_limit_is_enforced(self) -> None:
        result = pass_result(SHA)
        result["receipt"]["etag"] = "x" * subject.MAX_TERMINAL_UTF8_BYTES
        with self.assertRaisesRegex(
            subject.RuntimeResidentialCsvReceiptActionError, "exceeds limit"
        ):
            subject.parse_terminal_result(terminal_body(result))


if __name__ == "__main__":
    unittest.main()
