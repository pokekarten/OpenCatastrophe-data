# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import profile_esrm20_exposure_v10_tree as profile
from scripts import run_esrm20_exposure_v10_tree_action as action

EXECUTION_SHA = "b" * 40


def _profile() -> dict:
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": 282,
        "dataset_id": profile.DATASET_ID,
        "project_id": 269,
        "project_path": "efehr/esrm20",
        "release_tag": "v1.0",
        "commit_sha": profile.EXPECTED_COMMIT_SHA,
        "subtree_path": "Exposure",
        "pages_read": 2,
        "entry_count": 4,
        "blob_count": 3,
        "tree_count": 1,
        "tree_identity_sha256": "c" * 64,
        "kosovo_named_xml_candidates": [
            {
                "mode": "100644",
                "object_sha1": "d" * 40,
                "path": "Exposure/OQ_Exposure_Input_Kosovo.xml",
                "type": "blob",
            }
        ],
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _body(result: dict) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class ExposureTreeActionTests(unittest.TestCase):
    def test_request_is_selector_free_and_sha_bound(self) -> None:
        request = {
            "schema_version": action.REQUEST_SCHEMA_VERSION,
            "issue": 282,
            "target_sha": EXECUTION_SHA,
            "requester": "test-runner",
        }
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            request, separators=(",", ":")
        )
        parsed = action.validate_request(
            body, expected_issue=282, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed, request)
        for extra in ("path", "ref", "candidate", "country"):
            widened = dict(request)
            widened[extra] = "forbidden"
            widened_body = action.REQUEST_MARKER + "\n" + json.dumps(widened)
            with self.assertRaisesRegex(action.ExposureTreeExecutionError, "fields drifted"):
                action.validate_request(
                    widened_body, expected_issue=282, execution_sha=EXECUTION_SHA
                )
        with self.assertRaisesRegex(action.ExposureTreeExecutionError, "trusted main"):
            action.validate_request(
                body, expected_issue=282, execution_sha="e" * 40
            )

    def test_profile_validator_rejects_authority_widening(self) -> None:
        valid = _profile()
        self.assertIs(action.validate_profile(valid), valid)
        for field in (
            "provider_file_bytes_read",
            "external_bytes_persisted",
            "exact_kosovo_exposure_selected",
            "value_structural_wiring_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                changed = dict(valid)
                changed[field] = True
                with self.assertRaisesRegex(action.ExposureTreeExecutionError, field):
                    action.validate_profile(changed)

    def test_candidate_paths_fail_closed_on_traversal_case_or_duplicates(self) -> None:
        valid = _profile()
        bad_paths = (
            "Exposure/../Kosovo.xml",
            "Exposure/KOSOVO.xml",
            "/Exposure/Kosovo.xml",
            "Exposure\\Kosovo.xml",
            "Exposure/Kosovo.csv",
        )
        for path in bad_paths:
            with self.subTest(path=path):
                changed = dict(valid)
                changed["kosovo_named_xml_candidates"] = [
                    {**valid["kosovo_named_xml_candidates"][0], "path": path}
                ]
                with self.assertRaises(action.ExposureTreeExecutionError):
                    action.validate_profile(changed)
        duplicate = dict(valid)
        duplicate["kosovo_named_xml_candidates"] = [
            dict(valid["kosovo_named_xml_candidates"][0]),
            dict(valid["kosovo_named_xml_candidates"][0]),
        ]
        with self.assertRaisesRegex(action.ExposureTreeExecutionError, "not unique"):
            action.validate_profile(duplicate)

    def test_terminal_pass_blocked_and_duplicate_are_closed(self) -> None:
        passed = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _profile(),
        }
        self.assertTrue(action.parse_terminal_result(_body(passed), execution_sha=EXECUTION_SHA))
        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "candidate_resolution_failure",
            "profile": None,
        }
        self.assertTrue(action.parse_terminal_result(_body(blocked), execution_sha=EXECUTION_SHA))
        blocked["profile"] = _profile()
        with self.assertRaisesRegex(action.ExposureTreeExecutionError, "widened evidence"):
            action.parse_terminal_result(_body(blocked), execution_sha=EXECUTION_SHA)
        duplicate = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
        self.assertTrue(
            action.parse_terminal_result(_body(duplicate), execution_sha=EXECUTION_SHA)
        )

    def test_private_test_seams_do_not_widen_production_authority(self) -> None:
        result = action._execute_for_test(
            repository="pokekarten/OpenCatastrophe-data",
            token="x",
            execution_sha=EXECUTION_SHA,
            profile_fn=_profile,
            terminal_fn=lambda **kwargs: False,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["profile"], _profile())
        duplicate = action._execute_for_test(
            repository="pokekarten/OpenCatastrophe-data",
            token="x",
            execution_sha=EXECUTION_SHA,
            profile_fn=lambda: (_ for _ in ()).throw(AssertionError("must not run")),
            terminal_fn=lambda **kwargs: True,
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertIsNone(duplicate["profile"])

    def test_production_action_rejects_rebound_profile_before_execution(self) -> None:
        with mock.patch.object(profile, "profile_v10_tree", lambda: _profile()):
            with self.assertRaisesRegex(
                action.ExposureTreeExecutionError, "profile authority drifted"
            ):
                action.execute_profile(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )

    def test_production_action_rejects_rebound_inner_validator(self) -> None:
        with mock.patch.object(action, "validate_profile", lambda value: value):
            with self.assertRaisesRegex(
                action.ExposureTreeExecutionError, "action authority drifted"
            ):
                action.execute_profile(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )

    def test_trusted_bot_result_self_validates_before_dedup_sha_match(self) -> None:
        foreign_sha = "f" * 40
        malformed_foreign = {
            **action._base_result(execution_sha=foreign_sha),
            "status": "pass",
            "failure_class": None,
            "profile": {**_profile(), "publication_authorized": True},
        }
        comments = [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": _body(malformed_foreign),
            }
        ]
        with mock.patch.object(action, "_FETCH_COMMENTS", lambda *args, **kwargs: comments):
            with self.assertRaises(action.ExposureTreeExecutionError):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=EXECUTION_SHA,
                )


if __name__ == "__main__":
    unittest.main()
