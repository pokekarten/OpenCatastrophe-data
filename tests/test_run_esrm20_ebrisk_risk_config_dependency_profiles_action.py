# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_ebrisk_risk_config_dependency_profiles_action as action
from scripts import verify_esrm20_ebrisk_risk_config_dependencies as bridge


SHA = "a" * 40
NOW = "2026-08-18T12:40:00Z"


def request_body(**extra: object) -> str:
    payload: dict[str, object] = {
        "schema_version": action.REQUEST_SCHEMA_VERSION,
        "action": action.ACTION,
        "issue": action.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": action.DATASET_ID,
        "requester": "test-agent",
    }
    payload.update(extra)
    return action.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True)


def profile_for(spec: bridge.ConfigSpec) -> dict[str, object]:
    return {
        "schema_version": bridge.SCHEMA_VERSION,
        "source_issue": bridge.SOURCE_ISSUE,
        "dataset_id": bridge.DATASET_ID,
        "project_id": bridge.PROJECT_ID,
        "project_path": bridge.PROJECT_PATH,
        "commit_sha": bridge.COMMIT_SHA,
        "candidate_key": spec.key,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": bridge.RECEIPT_COMMENT_ID,
        "parser": bridge.PARSER_ID,
        "dependencies": [
            {
                "section": "input",
                "option": "exposure_file",
                "raw_path": "../Exposure/exposure.xml",
                "resolved_path": "Exposure/exposure.xml",
            }
        ],
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "dependency_inventory_authorized": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class EbriskDependencyProfilesActionTests(unittest.TestCase):
    def test_request_is_closed_and_has_no_candidate_selector(self) -> None:
        parsed = action.validate_request(
            request_body(), expected_issue=281, execution_sha=SHA
        )
        self.assertEqual(parsed["action"], action.ACTION)
        with self.assertRaisesRegex(action.EbriskDependencyProfilesActionError, "fields drifted"):
            action.validate_request(
                request_body(candidate="group1"), expected_issue=281, execution_sha=SHA
            )

    def test_pass_requires_exact_three_ordered_profiles_and_preserves_ceilings(self) -> None:
        profiles = []
        for spec in bridge.CONFIG_SPECS:
            item = profile_for(spec)
            item["profiled_at"] = NOW
            profiles.append(item)
        result = {
            **action._base_result(execution_sha=SHA),
            "status": "pass",
            "failure_class": None,
            "profiles": profiles,
        }
        validated = action.validate_terminal_result(result, execution_sha=SHA)
        self.assertEqual([p["candidate_key"] for p in validated["profiles"]], ["group1", "group2", "iceland"])
        self.assertFalse(validated["historical_group_assignment_verified"])
        self.assertFalse(validated["dependency_inventory_authorized"])
        self.assertFalse(validated["runtime_compatibility_verified"])
        self.assertFalse(validated["model_use_authorized"])

    def test_swapped_profiles_fail_closed(self) -> None:
        profiles = []
        for spec in bridge.CONFIG_SPECS:
            item = profile_for(spec)
            item["profiled_at"] = NOW
            profiles.append(item)
        profiles[0], profiles[1] = profiles[1], profiles[0]
        result = {
            **action._base_result(execution_sha=SHA),
            "status": "pass",
            "failure_class": None,
            "profiles": profiles,
        }
        with self.assertRaises(action.EbriskDependencyProfilesActionError):
            action.validate_terminal_result(result, execution_sha=SHA)

    def test_extra_scientific_claim_is_rejected(self) -> None:
        result = {
            **action._base_result(execution_sha=SHA),
            "status": "blocked",
            "failure_class": "profile_failure",
            "profiles": None,
            "historical_group_assignment": "Group1",
        }
        with self.assertRaisesRegex(action.EbriskDependencyProfilesActionError, "fields drifted"):
            action.validate_terminal_result(result, execution_sha=SHA)

    def test_late_acquisition_failure_is_atomic(self) -> None:
        first = lambda: profile_for(bridge.CONFIG_SPECS[0])
        second = mock.Mock(side_effect=action.worker.EbriskDependencyAcquisitionError("boom"))
        third = lambda: profile_for(bridge.CONFIG_SPECS[2])
        fake_comments = lambda *args, **kwargs: []
        with (
            mock.patch.object(action, "_FETCH_COMMENTS", fake_comments),
            mock.patch.object(action, "fetch_repository_comments", fake_comments),
        ):
            result = action.execute_profiles(
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                execution_sha=SHA,
                acquirers=(first, second, third),
                now=lambda: NOW,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profiles"])
        self.assertFalse(third.__dict__ if hasattr(third, "__dict__") else False)

    def test_trusted_bot_result_is_deduplicated_by_exact_sha(self) -> None:
        result = {
            **action._base_result(execution_sha=SHA),
            "status": "blocked",
            "failure_class": "profile_failure",
            "profiles": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True)
        fake_comments = lambda *args, **kwargs: [
            {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body}
        ]
        with (
            mock.patch.object(action, "_FETCH_COMMENTS", fake_comments),
            mock.patch.object(action, "fetch_repository_comments", fake_comments),
        ):
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
