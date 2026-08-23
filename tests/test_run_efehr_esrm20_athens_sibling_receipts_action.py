# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
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


def _blocked_result(failure_class: str) -> dict[str, object]:
    return {
        **worker._base_result(execution_sha=EXECUTION_SHA),
        "status": "blocked",
        "failure_class": failure_class,
        "receipts": None,
        "provider_file_bytes_read": None,
    }


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
        self.assertEqual(result["failure_class"], "ledger_incomplete")
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["content_semantics_verified"], False)
        self.assertIs(result["benchmark_agreement_inspected"], False)
        self.assertIs(result["independent_validation_established"], False)
        self.assertIs(result["holdout_status_established"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertEqual(worker.validate_result(result), result)

    def test_acquisition_failure_keeps_distinct_failure_class(self) -> None:
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=worker.AthensSiblingReceiptError("synthetic provider failure"),
        ):
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[],
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "athens_sibling_receipt_failure")
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])

    def test_ledger_incomplete_terminal_deduplicates_without_provider(self) -> None:
        terminal = worker.validate_result(_blocked_result("ledger_incomplete"))
        comment = {
            "id": 901,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER
            + "\n"
            + json.dumps(terminal, separators=(",", ":")),
        }
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=AssertionError("provider must not run after terminal dedup"),
        ) as acquire:
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[comment],
            )

        acquire.assert_not_called()
        self.assertEqual(
            result, {"status": "duplicate", "duplicate_result_comment_id": 901}
        )

    def test_unknown_blocked_failure_class_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            worker.AthensSiblingReceiptError, "blocked result failure class drifted"
        ):
            worker.validate_result(_blocked_result("unexpected_failure"))

    def test_publisher_accepts_only_known_blocked_failure_classes(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/esrm20-athens-sibling-receipts.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '              (\n'
            '                .failure_class == "athens_sibling_receipt_failure" or\n'
            '                .failure_class == "ledger_incomplete"\n'
            '              ) and\n'
            '              .receipts == null and .provider_file_bytes_read == null',
            workflow,
        )

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
