# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import run_esrm20_athens_gmpe_profile_action as action


SHA = "a" * 40


def _trusted_comment(body: str) -> dict:
    return {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body}


def _valid_matching_terminal() -> str:
    result = action._base_result(execution_sha=SHA)
    result.update(
        {
            "status": "blocked",
            "failure_class": "acquisition_failure",
            "evidence": None,
            "provider_file_bytes_read": None,
        }
    )
    result = action._validate_terminal_result(result, execution_sha=SHA)
    return action.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))


class FullLedgerValidationTests(unittest.TestCase):
    def test_matching_terminal_does_not_hide_later_malformed_trusted_terminal(self):
        comments = [
            _trusted_comment(_valid_matching_terminal()),
            _trusted_comment(action.RESULT_MARKER + "\n{not-json}"),
        ]
        original = action.fetch_repository_comments
        action.fetch_repository_comments = lambda *args, **kwargs: comments
        try:
            with self.assertRaisesRegex(
                action.AthensGmpeProfileActionError,
                "trusted Athens GMPE result JSON is malformed",
            ):
                action.has_terminal_result(repository="pokekarten/OpenCatastrophe-data", token="test", execution_sha=SHA)
        finally:
            action.fetch_repository_comments = original

    def test_matching_terminal_is_returned_only_after_complete_trusted_ledger_validation(self):
        comments = [
            _trusted_comment(_valid_matching_terminal()),
            {"user": {"login": "pokekarten"}, "body": "owner note"},
            _trusted_comment("unrelated trusted bot comment"),
        ]
        original = action.fetch_repository_comments
        action.fetch_repository_comments = lambda *args, **kwargs: comments
        try:
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=SHA,
                )
            )
        finally:
            action.fetch_repository_comments = original


if __name__ == "__main__":
    unittest.main()
