# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_athens_sibling_receipts as worker
from scripts import run_efehr_esrm20_athens_sibling_receipts_action as action
from scripts.prepare_agent_action_result import LedgerError

EXECUTION_SHA = "a" * 40


def _request_body() -> str:
    payload = {
        "schema_version": worker.REQUEST_SCHEMA_VERSION,
        "issue": 285,
        "target_sha": EXECUTION_SHA,
        "requester": "TEST-AGENT",
    }
    return worker.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


class AthensSiblingActionTests(unittest.TestCase):
    def test_ledger_failure_terminalizes_without_provider_acquisition(self) -> None:
        with (
            mock.patch.object(
                worker,
                "_FETCH_COMMENTS",
                side_effect=LedgerError("synthetic incomplete ledger"),
            ),
            mock.patch.object(
                worker,
                "_ACQUIRE",
                side_effect=AssertionError("provider acquisition must not run"),
            ) as acquire,
        ):
            result = action.prepare_action_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
            )

        acquire.assert_not_called()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "athens_sibling_receipt_failure")
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["content_semantics_verified"], False)
        self.assertIs(result["benchmark_agreement_inspected"], False)
        self.assertIs(result["independent_validation_established"], False)
        self.assertIs(result["holdout_status_established"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertEqual(worker.validate_result(result), result)

    def test_nonledger_worker_error_is_not_reclassified(self) -> None:
        with mock.patch.object(
            worker,
            "prepare_result",
            side_effect=worker.AthensSiblingReceiptError("different failure"),
        ):
            with self.assertRaisesRegex(
                worker.AthensSiblingReceiptError, "different failure"
            ):
                action.prepare_action_result(
                    _request_body(),
                    expected_issue=285,
                    execution_sha=EXECUTION_SHA,
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                )


if __name__ == "__main__":
    unittest.main()
