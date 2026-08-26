# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_greece_source_csv_receipts_action as subject


class GreeceSourceCsvReceiptActionTests(unittest.TestCase):
    SHA = "a" * 40

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
            subject._parse_trusted_terminal_result(body, execution_sha=self.SHA)


if __name__ == "__main__":
    unittest.main()
