# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import check_esrm20_gsim_runtime_dedup as subject


EXECUTION_SHA = "1" * 40
OTHER_SHA = "2" * 40


def _trusted_comment(comment_id: int, body: str) -> dict[str, object]:
    return {
        "id": comment_id,
        "body": body,
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
    }


class Esrm20RuntimeDedupFullLedgerTests(unittest.TestCase):
    def test_matching_terminal_does_not_short_circuit_later_trusted_validation(
        self,
    ) -> None:
        comments = [
            _trusted_comment(1, "matching-terminal"),
            _trusted_comment(2, "later-malformed-terminal"),
        ]
        malformed = subject._error("trusted ESRM20 runtime result JSON is malformed")

        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ), mock.patch.object(
            subject,
            "_parse_terminal",
            side_effect=[EXECUTION_SHA, malformed],
        ) as parse_terminal:
            with self.assertRaisesRegex(
                subject._runtime.Esrm20GsimReferenceRuntimeError,
                "result JSON is malformed",
            ):
                subject.has_terminal_runtime_result(
                    repository="owner/repo",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )

        self.assertEqual(parse_terminal.call_count, 2)

    def test_match_is_returned_only_after_all_trusted_terminals_validate(self) -> None:
        comments = [
            _trusted_comment(1, "matching-terminal"),
            _trusted_comment(2, "different-valid-terminal"),
        ]

        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ), mock.patch.object(
            subject,
            "_parse_terminal",
            side_effect=[EXECUTION_SHA, OTHER_SHA],
        ) as parse_terminal:
            found = subject.has_terminal_runtime_result(
                repository="owner/repo",
                token="token",
                execution_sha=EXECUTION_SHA,
            )

        self.assertTrue(found)
        self.assertEqual(parse_terminal.call_count, 2)


if __name__ == "__main__":
    unittest.main()
