# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import run_efehr_esrm20_athens_local_receipts_action as subject


class AthensLocalActionTests(unittest.TestCase):
    def test_ledger_failure_becomes_bounded_blocked_terminal(self):
        original = subject.worker.prepare_result

        def fail(*args, **kwargs):
            raise subject.worker.AthensLocalReceiptError(
                "cannot read complete Athens-local result ledger"
            )

        subject.worker.prepare_result = fail
        try:
            result = subject.prepare_action_result(
                "ignored",
                expected_issue=658,
                execution_sha="a" * 40,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
            )
        finally:
            subject.worker.prepare_result = original

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "ledger_incomplete")
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_unrelated_worker_error_is_not_terminalized(self):
        original = subject.worker.prepare_result

        def fail(*args, **kwargs):
            raise subject.worker.AthensLocalReceiptError("different failure")

        subject.worker.prepare_result = fail
        try:
            with self.assertRaisesRegex(
                subject.worker.AthensLocalReceiptError, "different failure"
            ):
                subject.prepare_action_result(
                    "ignored",
                    expected_issue=658,
                    execution_sha="a" * 40,
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                )
        finally:
            subject.worker.prepare_result = original


if __name__ == "__main__":
    unittest.main()
