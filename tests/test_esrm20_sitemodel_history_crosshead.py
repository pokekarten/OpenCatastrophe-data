# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import profile_esrm20_sitemodel_history as profile
from scripts import run_esrm20_sitemodel_history_action as action

CURRENT_SHA = "b" * 40
HISTORICAL_SHA = "a" * 40


def _valid_profile() -> dict:
    candidate = {
        "commit_sha": "c" * 40,
        "committed_at_utc": "2021-12-10T00:00:00Z",
        "parent_shas": ["d" * 40],
    }
    candidates = [candidate]
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": action.SOURCE_ISSUE,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "ref_name": profile.REF_NAME,
        "since_utc": profile.SINCE_UTC,
        "until_utc": profile.UNTIL_UTC,
        "pages_read": 1,
        "candidate_commit_count": 1,
        "history_identity_sha256": profile._history_sha256(candidates),
        "candidate_commits": candidates,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _terminal_result(execution_sha: str) -> dict:
    return {
        **action._base_result(execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "profile": _valid_profile(),
    }


def _body(result: dict) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class SiteModelHistoryCrossHeadTests(unittest.TestCase):
    def test_valid_historical_terminal_is_fully_validated_then_skipped(self) -> None:
        result = _terminal_result(HISTORICAL_SHA)
        self.assertFalse(action.parse_terminal_result(_body(result), execution_sha=CURRENT_SHA))
        self.assertTrue(action.parse_terminal_result(_body(result), execution_sha=HISTORICAL_SHA))

    def test_historical_widened_authority_fails_before_skip(self) -> None:
        result = _terminal_result(HISTORICAL_SHA)
        result["publication_authorized"] = True
        with self.assertRaisesRegex(
            action.SiteModelHistoryExecutionError,
            "result drifted at publication_authorized",
        ):
            action.parse_terminal_result(_body(result), execution_sha=CURRENT_SHA)

    def test_historical_corrupted_profile_fails_before_skip(self) -> None:
        result = _terminal_result(HISTORICAL_SHA)
        result["profile"]["candidate_commits"][0]["commit_sha"] = "e" * 40
        with self.assertRaisesRegex(
            action.SiteModelHistoryExecutionError,
            "identity does not match candidates",
        ):
            action.parse_terminal_result(_body(result), execution_sha=CURRENT_SHA)

    def test_historical_target_execution_mismatch_remains_fail_closed(self) -> None:
        result = _terminal_result(HISTORICAL_SHA)
        result["target_sha"] = "f" * 40
        with self.assertRaisesRegex(
            action.SiteModelHistoryExecutionError,
            "SHA binding is invalid",
        ):
            action.parse_terminal_result(_body(result), execution_sha=CURRENT_SHA)


if __name__ == "__main__":
    unittest.main()
