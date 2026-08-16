# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_hazard_logic_tree_profile_action as original
from scripts import run_esrm20_hazard_logic_tree_profile_action_receipt_fix as subject


class HazardCanonicalReceiptBindingTests(unittest.TestCase):
    def test_adapter_binds_exact_trusted_476_receipt_identity(self) -> None:
        subject.assert_canonical_receipt_binding()
        self.assertEqual(
            subject.GSIM_SHA256,
            "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4",
        )
        self.assertEqual(
            subject.SOURCE_SHA256,
            "caebf9142da6b4d6d1e970c3c008627d34943da83c977fb1da4d15d1e34d8a12",
        )
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5310057117)
        self.assertEqual(original.GSIM_SHA256, subject.GSIM_SHA256)
        self.assertEqual(original.SOURCE_SHA256, subject.SOURCE_SHA256)
        self.assertEqual(original.RECEIPT_COMMENT_ID, subject.RECEIPT_COMMENT_ID)

    def test_parser_and_action_contract_are_not_replaced(self) -> None:
        self.assertIs(subject.validate_request, original.validate_request)
        self.assertIs(subject.run_profile, original.run_profile)
        self.assertIs(subject._validate_profile, original._validate_profile)
        self.assertEqual(subject.ACTION, original.ACTION)
        self.assertEqual(subject.REQUEST_MARKER, original.REQUEST_MARKER)
        self.assertEqual(subject.RESULT_MARKER, original.RESULT_MARKER)

    @staticmethod
    def _blocked_result_body(sha: str) -> str:
        result = original._base_result(execution_sha=sha)
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "profile": None,
            }
        )
        return subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )

    def test_old_valid_terminal_result_does_not_block_new_execution_sha(self) -> None:
        old_sha = "1" * 40
        current_sha = "2" * 40
        comments = [
            {
                "user": {"login": original.TRUSTED_RESULT_LOGIN},
                "body": self._blocked_result_body(old_sha),
            }
        ]
        with mock.patch.object(
            original, "fetch_repository_comments", return_value=comments
        ):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=current_sha,
                )
            )

    def test_same_sha_terminal_result_still_deduplicates(self) -> None:
        old_sha = "1" * 40
        current_sha = "2" * 40
        comments = [
            {
                "user": {"login": original.TRUSTED_RESULT_LOGIN},
                "body": self._blocked_result_body(old_sha),
            },
            {
                "user": {"login": original.TRUSTED_RESULT_LOGIN},
                "body": self._blocked_result_body(current_sha),
            },
        ]
        with mock.patch.object(
            original, "fetch_repository_comments", return_value=comments
        ):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=current_sha,
                )
            )

    def test_historical_trusted_result_with_mismatched_own_shas_fails_closed(self) -> None:
        old_sha = "1" * 40
        current_sha = "2" * 40
        result = original._base_result(execution_sha=old_sha)
        result.update(
            {
                "execution_sha": "3" * 40,
                "status": "blocked",
                "failure_class": "profile_failure",
                "profile": None,
            }
        )
        comments = [
            {
                "user": {"login": original.TRUSTED_RESULT_LOGIN},
                "body": subject.RESULT_MARKER + "\n" + json.dumps(
                    result, sort_keys=True, separators=(",", ":")
                ),
            }
        ]
        with mock.patch.object(
            original, "fetch_repository_comments", return_value=comments
        ), self.assertRaisesRegex(
            original.HazardLogicTreeProfileActionError, "SHA binding"
        ):
            subject.has_terminal_result(
                repository="pokekarten/OpenCatastrophe-data",
                token="test",
                execution_sha=current_sha,
            )


if __name__ == "__main__":
    unittest.main()
