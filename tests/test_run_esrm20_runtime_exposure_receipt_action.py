# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_runtime_exposure_receipt_action as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError

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
        "retrieved_at": "2026-08-19T18:15:00Z",
        "byte_count": 1234,
        "sha256": "1" * 64,
        "content_type": "application/xml",
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
                "retrieved_at": "2026-08-19T18:15:00Z",
                "byte_count": 1234,
                "sha256": "1" * 64,
                "content_type": "application/xml",
                "etag": '"fixed"',
            },
        }
    )
    return result


def terminal_body(result: dict[str, object]) -> str:
    return subject.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class RuntimeExposureReceiptActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_rejects_widening(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=282, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)
        for body in (
            request_body(sha=OLD_SHA),
            request_body(repository_path="Exposure/other.xml"),
            subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}',
            subject.REQUEST_MARKER + '\n{"schema_version":NaN}',
        ):
            with self.subTest(body=body), self.assertRaises(subject.RuntimeExposureReceiptActionError):
                subject.validate_request(body, expected_issue=282, execution_sha=SHA)

    def test_pass_proves_only_bounded_byte_receipt(self) -> None:
        with mock.patch.object(
            subject, "acquire_runtime_exposure_receipt", return_value=worker_receipt()
        ):
            result = subject.run_receipt(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["receipt"]["byte_count"], 1234)
        self.assertEqual(result["receipt"]["sha256"], "1" * 64)
        for field in (
            "xml_content_interpreted",
            "exact_kosovo_exposure_selected",
            "value_structural_wiring_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[field])

    def test_acquisition_failure_is_bounded_blocked_result(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_runtime_exposure_receipt",
            side_effect=EfehrAcquisitionError("private transport detail"),
        ):
            result = subject.run_receipt(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipt"])

    def test_worker_identity_or_authority_drift_fails_closed(self) -> None:
        for forged in (
            worker_receipt(repository_path="Exposure/other.xml"),
            worker_receipt(publication_authorized=True),
            worker_receipt(byte_count=True),
            worker_receipt(sha256="0" * 63),
        ):
            with self.subTest(forged=forged), mock.patch.object(
                subject, "acquire_runtime_exposure_receipt", return_value=forged
            ):
                result = subject.run_receipt(execution_sha=SHA)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["receipt"])

    def test_historical_terminal_is_validated_under_own_sha_and_dedup_is_exact(self) -> None:
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

    def test_malformed_or_authority_widened_trusted_terminal_fails_closed(self) -> None:
        widened = pass_result(OLD_SHA)
        widened["model_use_authorized"] = True
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": terminal_body(widened),
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.RuntimeExposureReceiptActionError):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_terminal_publication_limit_is_enforced(self) -> None:
        result = pass_result(SHA)
        result["receipt"]["etag"] = "x" * subject.MAX_TERMINAL_UTF8_BYTES
        body = terminal_body(result)
        with self.assertRaisesRegex(subject.RuntimeExposureReceiptActionError, "exceeds limit"):
            subject.parse_terminal_result(body)


if __name__ == "__main__":
    unittest.main()
