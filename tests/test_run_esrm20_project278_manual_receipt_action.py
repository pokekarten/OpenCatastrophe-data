# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_project278_manual_receipt_action as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError

EXECUTION_SHA = "a" * 40


def _request(**overrides):
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": EXECUTION_SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "slot2",
    }
    value.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, sort_keys=True, separators=(",", ":"))


def _receipt(**overrides):
    value = {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": subject.WORKER_OPERATION_ID,
        "source_issue": subject.CONTROL_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "requested_url": "https://gitlab.seismo.ethz.ch/example",
        "final_url": "https://gitlab.seismo.ethz.ch/example",
        "retrieved_at": "2026-08-26T06:00:00Z",
        "byte_count": 1234,
        "sha256": "b" * 64,
        "content_type": "application/pdf",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    value.update(overrides)
    return value


def _terminal(result):
    return subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))


class RequestTests(unittest.TestCase):
    def test_accepts_exact_request(self):
        result = subject.validate_request(_request(), expected_issue=291, execution_sha=EXECUTION_SHA)
        self.assertEqual(result["target_sha"], EXECUTION_SHA)

    def test_rejects_wrong_dataset_and_float_issue(self):
        with self.assertRaises(subject.Project278ManualReceiptActionError):
            subject.validate_request(_request(dataset_id="wrong"), expected_issue=291, execution_sha=EXECUTION_SHA)
        with self.assertRaises(subject.Project278ManualReceiptActionError):
            subject.validate_request(_request(issue=291.0), expected_issue=291, execution_sha=EXECUTION_SHA)


class ExecutionTests(unittest.TestCase):
    def test_pass_projects_only_bounded_receipt_identity(self):
        with mock.patch.object(subject, "acquire_project278_manual_receipt", return_value=_receipt()):
            result = subject.run_manual_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["receipt"]["byte_count"], 1234)
        self.assertEqual(result["receipt"]["sha256"], "b" * 64)
        for field in subject._AUTHORITY_FALSE_FIELDS:
            self.assertIs(result[field], False)
        serialized = json.dumps(result)
        self.assertNotIn("requested_url", serialized)
        self.assertNotIn("final_url", serialized)

    def test_acquisition_failure_is_bounded(self):
        with mock.patch.object(
            subject,
            "acquire_project278_manual_receipt",
            side_effect=EfehrAcquisitionError("secret provider failure"),
        ):
            result = subject.run_manual_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipt"])
        self.assertNotIn("secret provider failure", json.dumps(result))

    def test_rejects_widened_worker_authority_and_float_byte_count(self):
        with mock.patch.object(
            subject,
            "acquire_project278_manual_receipt",
            return_value=_receipt(publication_authorized=True),
        ):
            result = subject.run_manual_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")
        with mock.patch.object(
            subject,
            "acquire_project278_manual_receipt",
            return_value=_receipt(byte_count=1234.0),
        ):
            result = subject.run_manual_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")


class LedgerTests(unittest.TestCase):
    def _pass_result(self):
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "receipt": {
                    "retrieved_at": "2026-08-26T06:00:00Z",
                    "byte_count": 1234,
                    "sha256": "b" * 64,
                    "content_type": "application/pdf",
                    "etag": None,
                },
            }
        )
        return result

    def test_complete_ledger_detects_terminal(self):
        comments = [
            {"user": {"login": "someone"}, "body": _terminal(self._pass_result())},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": _terminal(self._pass_result())},
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_manual_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
            )

    def test_later_malformed_trusted_terminal_fails_closed(self):
        comments = [
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": _terminal(self._pass_result())},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": subject.RESULT_MARKER + "\n{"},
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.Project278ManualReceiptActionError):
                subject.has_terminal_manual_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )

    def test_terminal_byte_bound_precedes_json_parse(self):
        body = subject.RESULT_MARKER + "\n" + (" " * subject.MAX_TERMINAL_UTF8_BYTES) + "{}"
        with self.assertRaisesRegex(subject.Project278ManualReceiptActionError, "byte bound"):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
