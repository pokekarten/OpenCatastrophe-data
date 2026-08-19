# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_runtime_exposure_receipt_action as subject

SHA = "a" * 40


def worker_receipt(byte_count: int) -> dict[str, object]:
    return {
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
        "retrieved_at": "2026-08-19T18:30:00Z",
        "byte_count": byte_count,
        "sha256": "1" * 64,
        "content_type": "application/xml",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def pass_result(byte_count: int) -> dict[str, object]:
    result = subject._base_result(execution_sha=SHA)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipt": {
                "retrieved_at": "2026-08-19T18:30:00Z",
                "byte_count": byte_count,
                "sha256": "1" * 64,
                "content_type": "application/xml",
                "etag": None,
            },
        }
    )
    return result


class RuntimeExposureReceiptByteBoundRegressionTests(unittest.TestCase):
    def test_worker_receipt_accepts_exact_limit_and_rejects_limit_plus_one(self) -> None:
        validated = subject._validate_receipt(worker_receipt(subject.MAX_RECEIPT_BYTES))
        self.assertEqual(validated["byte_count"], subject.MAX_RECEIPT_BYTES)

        with self.assertRaisesRegex(
            subject.RuntimeExposureReceiptActionError, "byte count is invalid"
        ):
            subject._validate_receipt(worker_receipt(subject.MAX_RECEIPT_BYTES + 1))

    def test_oversized_worker_receipt_becomes_bounded_blocked_result(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_runtime_exposure_receipt",
            return_value=worker_receipt(subject.MAX_RECEIPT_BYTES + 1),
        ):
            result = subject.run_receipt(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipt"])

    def test_terminal_accepts_exact_limit_and_rejects_limit_plus_one(self) -> None:
        self.assertEqual(subject._validate_terminal_result(pass_result(subject.MAX_RECEIPT_BYTES)), SHA)
        with self.assertRaisesRegex(
            subject.RuntimeExposureReceiptActionError, "trusted PASS receipt is invalid"
        ):
            subject._validate_terminal_result(pass_result(subject.MAX_RECEIPT_BYTES + 1))

    def test_oversized_historical_trusted_terminal_fails_before_dedup(self) -> None:
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            pass_result(subject.MAX_RECEIPT_BYTES + 1),
            sort_keys=True,
            separators=(",", ":"),
        )
        comments = [
            {
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": body,
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaisesRegex(
                subject.RuntimeExposureReceiptActionError, "trusted PASS receipt is invalid"
            ):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )


if __name__ == "__main__":
    unittest.main()
