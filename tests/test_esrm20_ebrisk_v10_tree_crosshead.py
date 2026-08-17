# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts import run_esrm20_ebrisk_v10_tree_action as action

CURRENT_SHA = "b" * 40
HISTORICAL_SHA = "a" * 40


def _valid_profile() -> dict:
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": action.SOURCE_ISSUE,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.EXPECTED_COMMIT_SHA,
        "pages_read": 1,
        "entry_count": 4,
        "blob_count": 3,
        "tree_count": 1,
        "tree_identity_sha256": "f" * 64,
        "top_level_entry_counts": {"Configuration_Files": 4},
        "ebrisk_templates": [
            {
                "basename": "config_ebrisk_group1.ini",
                "path": "Configuration_Files/config_ebrisk_group1.ini",
                "type": "blob",
                "object_sha1": "1" * 40,
            },
            {
                "basename": "config_ebrisk_group2.ini",
                "path": "Configuration_Files/config_ebrisk_group2.ini",
                "type": "blob",
                "object_sha1": "2" * 40,
            },
            {
                "basename": "conif_ebrisk_group3.ini",
                "path": "Configuration_Files/conif_ebrisk_group3.ini",
                "type": "blob",
                "object_sha1": "3" * 40,
            },
        ],
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _terminal_comment(execution_sha: str, *, profile_value: dict | None = None) -> dict:
    result = {
        **action._base_result(execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "profile": profile_value if profile_value is not None else _valid_profile(),
    }
    return {
        "user": {"login": action.TRUSTED_RESULT_LOGIN},
        "body": action.RESULT_MARKER
        + "\n"
        + json.dumps(result, sort_keys=True, separators=(",", ":")),
    }


class EbriskCrossHeadTerminalTests(unittest.TestCase):
    def test_valid_historical_terminal_is_fully_validated_then_skipped(self) -> None:
        with mock.patch.object(
            action,
            "_FETCH_COMMENTS",
            return_value=[_terminal_comment(HISTORICAL_SHA)],
        ):
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=CURRENT_SHA,
                )
            )

    def test_exact_sha_terminal_still_deduplicates(self) -> None:
        with mock.patch.object(
            action,
            "_FETCH_COMMENTS",
            return_value=[_terminal_comment(CURRENT_SHA)],
        ):
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=CURRENT_SHA,
                )
            )

    def test_historical_target_execution_mismatch_fails_closed(self) -> None:
        comment = _terminal_comment(HISTORICAL_SHA)
        marker, raw = comment["body"].split("\n", 1)
        result = json.loads(raw)
        result["target_sha"] = "c" * 40
        comment["body"] = marker + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=[comment]):
            with self.assertRaisesRegex(
                action.EbriskTreeExecutionError,
                "target/execution SHA mismatch",
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=CURRENT_SHA,
                )

    def test_historical_nested_profile_identity_mutation_fails_before_skip(self) -> None:
        changed = _valid_profile()
        changed["commit_sha"] = "9" * 40
        with mock.patch.object(
            action,
            "_FETCH_COMMENTS",
            return_value=[_terminal_comment(HISTORICAL_SHA, profile_value=changed)],
        ):
            with self.assertRaisesRegex(
                action.EbriskTreeExecutionError,
                "profile drifted at commit_sha",
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=CURRENT_SHA,
                )

    def test_historical_normalized_path_mutation_fails_before_skip(self) -> None:
        changed = _valid_profile()
        changed["ebrisk_templates"] = [
            dict(item) for item in changed["ebrisk_templates"]
        ]
        changed["ebrisk_templates"][0]["path"] = (
            "./Configuration_Files/config_ebrisk_group1.ini"
        )
        with mock.patch.object(
            action,
            "_FETCH_COMMENTS",
            return_value=[_terminal_comment(HISTORICAL_SHA, profile_value=changed)],
        ):
            with self.assertRaisesRegex(
                action.EbriskTreeExecutionError,
                "not canonical relative POSIX",
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=CURRENT_SHA,
                )


if __name__ == "__main__":
    unittest.main()
