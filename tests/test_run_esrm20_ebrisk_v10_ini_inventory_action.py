# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import profile_esrm20_ebrisk_v10_ini_inventory as profile
from scripts import run_esrm20_ebrisk_v10_ini_inventory_action as action

EXECUTION_SHA = "b" * 40


def _valid_profile() -> dict:
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": 281,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.EXPECTED_COMMIT_SHA,
        "configuration_root": profile.CONFIGURATION_ROOT,
        "tree_entry_count": 4,
        "source_tree_identity_sha256": "1" * 64,
        "ini_blob_count": 3,
        "ini_inventory_sha256": "2" * 64,
        "ini_blobs": [
            {
                "basename": "config_ebrisk_group1.ini",
                "path": "Configuration_files/config_ebrisk_group1.ini",
                "mode": "100644",
                "object_sha1": "3" * 40,
            },
            {
                "basename": "config_event_hazard_Group1.ini",
                "path": "Configuration_files/config_event_hazard_Group1.ini",
                "mode": "100644",
                "object_sha1": "4" * 40,
            },
            {
                "basename": "other.ini",
                "path": "Configuration_files/subdir/other.ini",
                "mode": "100755",
                "object_sha1": "5" * 40,
            },
        ],
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class EbriskV10IniInventoryActionTests(unittest.TestCase):
    def test_request_is_exact_issue_and_execution_sha_bound(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 281,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(
            body, expected_issue=281, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.EbriskIniInventoryExecutionError):
            action.validate_request(
                body, expected_issue=281, execution_sha="c" * 40
            )

    def test_request_rejects_duplicate_json_key_and_nonfinite_constant(self) -> None:
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":281,"target_sha":"'
            + EXECUTION_SHA
            + '","target_sha":"'
            + EXECUTION_SHA
            + '","requester":"x"}'
        )
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "duplicate JSON key"
        ):
            action.validate_request(
                duplicate, expected_issue=281, execution_sha=EXECUTION_SHA
            )
        nonfinite = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":281,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":NaN}'
        )
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "non-finite"
        ):
            action.validate_request(
                nonfinite, expected_issue=281, execution_sha=EXECUTION_SHA
            )

    def test_profile_accepts_exact_case_preserving_inventory(self) -> None:
        self.assertEqual(action.validate_profile(_valid_profile()), _valid_profile())

    def test_profile_rejects_path_case_suffix_or_authority_widening(self) -> None:
        cases: list[tuple[str, dict]] = []

        escaped = _valid_profile()
        escaped["ini_blobs"] = [dict(item) for item in escaped["ini_blobs"]]
        escaped["ini_blobs"][0]["path"] = "Other/config_ebrisk_group1.ini"
        escaped["ini_blobs"].sort(
            key=lambda item: (item["path"], item["mode"], item["object_sha1"])
        )
        cases.append(("exact configuration root", escaped))

        upper_suffix = _valid_profile()
        upper_suffix["ini_blobs"] = [dict(item) for item in upper_suffix["ini_blobs"]]
        upper_suffix["ini_blobs"][0]["basename"] = "config_ebrisk_group1.INI"
        upper_suffix["ini_blobs"][0]["path"] = (
            "Configuration_files/config_ebrisk_group1.INI"
        )
        cases.append(("lowercase INI", upper_suffix))

        widened = _valid_profile()
        widened["historical_group_assignment_authorized"] = True
        cases.append(("historical_group_assignment_authorized", widened))

        for message, value in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(
                    action.EbriskIniInventoryExecutionError, message
                ):
                    action.validate_profile(value)

    def test_profile_rejects_noncanonical_order_duplicate_path_and_count_drift(self) -> None:
        reordered = _valid_profile()
        reordered["ini_blobs"] = list(reversed(reordered["ini_blobs"]))
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "not canonical"
        ):
            action.validate_profile(reordered)

        duplicated = _valid_profile()
        duplicated["ini_blobs"] = [dict(item) for item in duplicated["ini_blobs"]]
        duplicated["ini_blobs"][1]["path"] = duplicated["ini_blobs"][0]["path"]
        duplicated["ini_blobs"][1]["basename"] = duplicated["ini_blobs"][0]["basename"]
        duplicated["ini_blobs"].sort(
            key=lambda item: (item["path"], item["mode"], item["object_sha1"])
        )
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "not unique"
        ):
            action.validate_profile(duplicated)

        count = _valid_profile()
        count["ini_blob_count"] = 2
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "count disagrees"
        ):
            action.validate_profile(count)

    def test_pass_and_blocked_results_are_fail_closed(self) -> None:
        passed = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            passed, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))

        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": action.BLOCKED_FAILURE_CLASS,
            "profile": None,
        }
        blocked_body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(
            action.parse_terminal_result(blocked_body, execution_sha=EXECUTION_SHA)
        )
        blocked["profile"] = _valid_profile()
        widened_body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(
            action.EbriskIniInventoryExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(widened_body, execution_sha=EXECUTION_SHA)

    def test_dedup_scans_only_trusted_bot_terminal_results(self) -> None:
        terminal = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            terminal, sort_keys=True, separators=(",", ":")
        )
        original_fetch = action.fetch_repository_comments
        original_authority = action._FETCH_COMMENTS
        try:
            def fake_fetch(repository, token, *, issue, max_pages):
                self.assertEqual(issue, 281)
                return [
                    {"user": {"login": "someone"}, "body": body},
                    {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body},
                ]

            action.fetch_repository_comments = fake_fetch
            action._FETCH_COMMENTS = fake_fetch
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )
            )
        finally:
            action.fetch_repository_comments = original_fetch
            action._FETCH_COMMENTS = original_authority

    def test_execute_deduplicates_before_profile_execution(self) -> None:
        terminal = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _valid_profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            terminal, sort_keys=True, separators=(",", ":")
        )
        original_fetch = action.fetch_repository_comments
        original_fetch_authority = action._FETCH_COMMENTS
        original_profile = profile.profile_v10_ini_inventory
        original_profile_authority = action._PROFILE
        calls = 0
        try:
            def fake_fetch(repository, token, *, issue, max_pages):
                return [
                    {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body}
                ]

            def forbidden_profile():
                nonlocal calls
                calls += 1
                raise AssertionError(
                    "provider metadata profiler must not run after dedup"
                )

            action.fetch_repository_comments = fake_fetch
            action._FETCH_COMMENTS = fake_fetch
            profile.profile_v10_ini_inventory = forbidden_profile
            action._PROFILE = forbidden_profile
            result = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="x",
                execution_sha=EXECUTION_SHA,
            )
            self.assertEqual(result["status"], "duplicate")
            self.assertEqual(calls, 0)
        finally:
            action.fetch_repository_comments = original_fetch
            action._FETCH_COMMENTS = original_fetch_authority
            profile.profile_v10_ini_inventory = original_profile
            action._PROFILE = original_profile_authority


if __name__ == "__main__":
    unittest.main()
