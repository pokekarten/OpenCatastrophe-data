# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_summaries_action as action


class ScenarioSummaryDedupTests(unittest.TestCase):
    @staticmethod
    def _blocked_result_body(sha: str) -> str:
        result = {
            **action._base_result(execution_sha=sha),
            "status": "blocked",
            "failure_class": "summary_acquisition_or_profile_failure",
            "profile": None,
        }
        return action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )

    @staticmethod
    def _trusted_comment(body: str) -> dict[str, object]:
        return {
            "user": {"login": action.TRUSTED_RESULT_LOGIN},
            "body": body,
        }

    def test_other_valid_execution_sha_is_ignored_for_current_dedup(self) -> None:
        historical_sha = "1" * 40
        current_sha = "2" * 40
        comments = [self._trusted_comment(self._blocked_result_body(historical_sha))]

        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=comments):
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=current_sha,
                )
            )

    def test_same_execution_sha_still_deduplicates(self) -> None:
        current_sha = "2" * 40
        comments = [self._trusted_comment(self._blocked_result_body(current_sha))]

        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=comments):
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=current_sha,
                )
            )

    def test_historical_result_with_mismatched_own_shas_fails_closed(self) -> None:
        historical_sha = "1" * 40
        current_sha = "2" * 40
        result = {
            **action._base_result(execution_sha=historical_sha),
            "execution_sha": "3" * 40,
            "status": "blocked",
            "failure_class": "summary_acquisition_or_profile_failure",
            "profile": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        comments = [self._trusted_comment(body)]

        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=comments), self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError,
            "target/execution SHA mismatch",
        ):
            action.has_terminal_result(
                repository="pokekarten/OpenCatastrophe-data",
                token="test-token",
                execution_sha=current_sha,
            )

    def test_other_sha_malformed_terminal_result_still_fails_closed(self) -> None:
        historical_sha = "1" * 40
        current_sha = "2" * 40
        result = {
            **action._base_result(execution_sha=historical_sha),
            "status": "pending",
            "failure_class": None,
            "profile": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        comments = [self._trusted_comment(body)]

        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=comments), self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError,
            "non-terminal status",
        ):
            action.has_terminal_result(
                repository="pokekarten/OpenCatastrophe-data",
                token="test-token",
                execution_sha=current_sha,
            )


if __name__ == "__main__":
    unittest.main()
