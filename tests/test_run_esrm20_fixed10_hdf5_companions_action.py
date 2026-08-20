# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import profile_esrm20_fixed10_hdf5_companions as profile
from scripts import run_esrm20_fixed10_hdf5_companions_action as action

EXECUTION_SHA = "b" * 40


def _valid_profile() -> dict:
    companions = []
    for index, source_path in enumerate(profile.SOURCE_XML_PATHS):
        present = index == 0
        companions.append(
            {
                "source_xml_path": source_path,
                "candidate_hdf5_path": source_path[:-4] + ".hdf5",
                "present": present,
                "mode": "100644" if present else None,
                "object_sha1": "3" * 40 if present else None,
            }
        )
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": 281,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.EXPECTED_COMMIT_SHA,
        "source_tree_entry_count": 100,
        "source_tree_identity_sha256": "1" * 64,
        "source_xml_count": 10,
        "candidate_hdf5_count": 10,
        "present_hdf5_count": 1,
        "absent_hdf5_count": 9,
        "companion_inventory_sha256": profile._companion_identity(companions),
        "companions": companions,
        "provider_file_bytes_read": False,
        "hdf5_byte_identity_verified": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class Fixed10Hdf5CompanionActionTests(unittest.TestCase):
    def test_request_is_exact_issue_and_trusted_main_sha_bound(self) -> None:
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
        with self.assertRaises(action.Hdf5CompanionExecutionError):
            action.validate_request(
                body, expected_issue=281, execution_sha="c" * 40
            )

    def test_request_rejects_duplicate_key_and_nonfinite_constant(self) -> None:
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
            action.Hdf5CompanionExecutionError, "duplicate JSON key"
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
        with self.assertRaisesRegex(action.Hdf5CompanionExecutionError, "non-finite"):
            action.validate_request(
                nonfinite, expected_issue=281, execution_sha=EXECUTION_SHA
            )

    def test_profile_accepts_exact_fixed10_projection(self) -> None:
        value = _valid_profile()
        self.assertEqual(action.validate_profile(value), value)

    def test_profile_rejects_widened_authority_and_fake_absence_metadata(self) -> None:
        widened = _valid_profile()
        widened["model_use_authorized"] = True
        with self.assertRaisesRegex(
            action.Hdf5CompanionExecutionError, "model_use_authorized"
        ):
            action.validate_profile(widened)

        fake_absent = _valid_profile()
        fake_absent["companions"] = [dict(item) for item in fake_absent["companions"]]
        fake_absent["companions"][1]["object_sha1"] = "4" * 40
        with self.assertRaisesRegex(
            action.Hdf5CompanionExecutionError,
            "absent HDF5 companion carries object metadata",
        ):
            action.validate_profile(fake_absent)

    def test_profile_rejects_candidate_derivation_and_count_drift(self) -> None:
        wrong_candidate = _valid_profile()
        wrong_candidate["companions"] = [
            dict(item) for item in wrong_candidate["companions"]
        ]
        wrong_candidate["companions"][0]["candidate_hdf5_path"] += ".other"
        with self.assertRaisesRegex(
            action.Hdf5CompanionExecutionError,
            "same-stem HDF5 derivation drifted",
        ):
            action.validate_profile(wrong_candidate)

        wrong_count = _valid_profile()
        wrong_count["present_hdf5_count"] = 2
        wrong_count["absent_hdf5_count"] = 8
        with self.assertRaisesRegex(
            action.Hdf5CompanionExecutionError,
            "presence count disagrees",
        ):
            action.validate_profile(wrong_count)

    def test_pass_and_blocked_results_remain_fail_closed(self) -> None:
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
            action.Hdf5CompanionExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(widened_body, execution_sha=EXECUTION_SHA)

    def test_workflow_runs_provider_code_only_from_trusted_default_branch(self) -> None:
        workflow = Path(
            ".github/workflows/esrm20-fixed10-hdf5-companions.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("issue_comment:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("github.event.issue.number == 281", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn(action.REQUEST_MARKER, workflow)


if __name__ == "__main__":
    unittest.main()
