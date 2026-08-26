# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_greece_source_csv_receipts_action as subject


class GreeceSourceCsvReceiptActionTests(unittest.TestCase):
    SHA = "a" * 40
    PRIOR_SHA = "b" * 40

    def request_body(self) -> str:
        payload = {
            "schema_version": subject.REQUEST_SCHEMA_VERSION,
            "action": subject.ACTION,
            "issue": subject.CONTROL_ISSUE,
            "target_sha": self.SHA,
            "dataset_id": subject.DATASET_ID,
            "requester": "unit-test",
        }
        return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def terminal_body(self, sha: str, *, status: str) -> str:
        payload = subject._base_result(execution_sha=sha)
        if status == "pass":
            payload.update({"status": "pass", "failure_class": None, "receipts": []})
        elif status == "blocked":
            payload.update({"status": "blocked", "failure_class": "acquisition_failure", "receipts": None})
        else:
            raise AssertionError(status)
        return subject.RESULT_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def trusted_comment(self, body: str) -> dict[str, object]:
        return {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body}

    def test_validate_request_binds_execution_sha(self):
        result = subject.validate_request(
            self.request_body(), expected_issue=subject.CONTROL_ISSUE, execution_sha=self.SHA
        )
        self.assertEqual(result["target_sha"], self.SHA)

    def test_validate_request_rejects_float_issue(self):
        body = self.request_body().replace('"issue":285', '"issue":285.0')
        with self.assertRaises(subject.GreeceSourceCsvReceiptsActionError):
            subject.validate_request(body, expected_issue=subject.CONTROL_ISSUE, execution_sha=self.SHA)

    def test_acquisition_failure_is_bounded(self):
        with mock.patch.object(subject, "acquire_receipts", side_effect=subject.EfehrAcquisitionError("boom")):
            result = subject.run_receipts(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipts"])
        for field in subject._FALSE_FIELDS:
            self.assertIs(result[field], False)

    def test_terminal_result_is_bounded_before_json(self):
        body = subject.RESULT_MARKER + "\n" + ("é" * 30_000)
        with self.assertRaisesRegex(subject.GreeceSourceCsvReceiptsActionError, "byte bound"):
            subject._parse_trusted_terminal_result(body)

    def test_prior_sha_blocked_terminal_is_valid_non_match(self):
        comments = [self.trusted_comment(self.terminal_body(self.PRIOR_SHA, status="blocked"))]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertFalse(subject.has_terminal_result(repository="owner/repo", token="token", execution_sha=self.SHA))

    def test_prior_sha_pass_terminal_is_valid_non_match(self):
        comments = [self.trusted_comment(self.terminal_body(self.PRIOR_SHA, status="pass"))]
        with (
            mock.patch.object(subject, "fetch_repository_comments", return_value=comments),
            mock.patch.object(subject, "_validate_terminal_receipts", return_value=[]),
        ):
            self.assertFalse(subject.has_terminal_result(repository="owner/repo", token="token", execution_sha=self.SHA))

    def test_later_malformed_prior_sha_terminal_fails_closed_after_current_match(self):
        current = self.terminal_body(self.SHA, status="blocked")
        malformed_payload = subject._base_result(execution_sha=self.PRIOR_SHA)
        malformed_payload.update(
            {
                "target_sha": "c" * 40,
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipts": None,
            }
        )
        malformed = subject.RESULT_MARKER + "\n" + json.dumps(malformed_payload, separators=(",", ":"))
        comments = [self.trusted_comment(current), self.trusted_comment(malformed)]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaisesRegex(subject.GreeceSourceCsvReceiptsActionError, "target_sha"):
                subject.has_terminal_result(repository="owner/repo", token="token", execution_sha=self.SHA)

    def test_terminal_execution_sha_must_be_canonical(self):
        payload = subject._base_result(execution_sha=self.SHA)
        payload.update(
            {
                "target_sha": "A" * 40,
                "execution_sha": "A" * 40,
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipts": None,
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))
        with self.assertRaisesRegex(subject.GreeceSourceCsvReceiptsActionError, "execution SHA"):
            subject._parse_trusted_terminal_result(body)


if __name__ == "__main__":
    unittest.main()
