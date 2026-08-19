# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from scripts import profile_esrm20_sitemodel_candidate_trees as profile
from scripts import run_esrm20_sitemodel_candidate_tree_action as action

EXECUTION_SHA = "e" * 40
OLD_SHA = "d" * 40
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "esrm20-sitemodel-candidate-trees.yml"
)


def _candidate_profile() -> dict:
    candidates = []
    for item in profile.CANDIDATE_HISTORY:
        commit_sha = item["commit_sha"]
        candidates.append(
            {
                "commit_sha": commit_sha,
                "pages_read": 1,
                "entry_count": 4,
                "blob_count": 3,
                "tree_identity_sha256": hashlib.sha256(commit_sha.encode("ascii")).hexdigest(),
            }
        )
    commits = [item["commit_sha"] for item in profile.CANDIDATE_HISTORY]
    changed = [
        {
            "path": "src/exposure2site.py",
            "states": [
                {
                    "commit_sha": commits[0],
                    "present": True,
                    "mode": "100644",
                    "object_sha1": "a" * 40,
                },
                {
                    "commit_sha": commits[1],
                    "present": True,
                    "mode": "100644",
                    "object_sha1": "b" * 40,
                },
                {
                    "commit_sha": commits[2],
                    "present": False,
                    "mode": None,
                    "object_sha1": None,
                },
            ],
        }
    ]
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": profile.SOURCE_ISSUE,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "history_identity_sha256": profile.HISTORY_IDENTITY_SHA256,
        "candidate_tree_profiles": candidates,
        "changed_blob_count": len(changed),
        "changed_blob_identity_sha256": profile._changed_blob_identity_sha256(changed),
        "changed_blobs": changed,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _request_body(*, target_sha: str = EXECUTION_SHA) -> str:
    return action.REQUEST_MARKER + "\n" + json.dumps(
        {
            "schema_version": action.REQUEST_SCHEMA_VERSION,
            "issue": 291,
            "target_sha": target_sha,
            "requester": "test-runner",
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _result_body(result: dict) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class SiteModelCandidateTreeActionTests(unittest.TestCase):
    def test_request_is_exact_trusted_head_bound_and_strict(self) -> None:
        parsed = action.validate_request(
            _request_body(), expected_issue=291, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)

        with self.assertRaises(action.SiteModelCandidateTreeExecutionError):
            action.validate_request(
                _request_body(), expected_issue=291, execution_sha="f" * 40
            )
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":291,"issue":291,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"test"}'
        )
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "duplicate JSON key"
        ):
            action.validate_request(
                duplicate, expected_issue=291, execution_sha=EXECUTION_SHA
            )

        nonfinite = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":291,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"test","extra":1e400}'
        )
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "non-finite JSON float"
        ):
            action.validate_request(
                nonfinite, expected_issue=291, execution_sha=EXECUTION_SHA
            )

    def test_profile_validates_exact_candidates_changed_identity_and_authority_ceiling(self) -> None:
        valid = _candidate_profile()
        self.assertIs(action.validate_profile(valid), valid)

        widened = json.loads(json.dumps(valid))
        widened["crs_coordinate_semantics_verified"] = True
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError,
            "crs_coordinate_semantics_verified",
        ):
            action.validate_profile(widened)

        reordered = json.loads(json.dumps(valid))
        reordered["candidate_tree_profiles"].reverse()
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "identity/order"
        ):
            action.validate_profile(reordered)

        mutated = json.loads(json.dumps(valid))
        mutated["changed_blobs"][0]["states"][0]["object_sha1"] = "c" * 40
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError,
            "changed-blob identity does not match",
        ):
            action.validate_profile(mutated)

    def test_profile_rejects_unchanged_blob_and_noncanonical_path(self) -> None:
        valid = _candidate_profile()
        unchanged = json.loads(json.dumps(valid))
        state = unchanged["changed_blobs"][0]["states"][0]
        for observed in unchanged["changed_blobs"][0]["states"]:
            observed["present"] = state["present"]
            observed["mode"] = state["mode"]
            observed["object_sha1"] = state["object_sha1"]
        unchanged["changed_blob_identity_sha256"] = profile._changed_blob_identity_sha256(
            unchanged["changed_blobs"]
        )
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError,
            "unchanged blob was published as changed",
        ):
            action.validate_profile(unchanged)

        traversal = json.loads(json.dumps(valid))
        traversal["changed_blobs"][0]["path"] = "src/../secret.py"
        traversal["changed_blob_identity_sha256"] = profile._changed_blob_identity_sha256(
            traversal["changed_blobs"]
        )
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "canonical POSIX"
        ):
            action.validate_profile(traversal)

        backslash = json.loads(json.dumps(valid))
        backslash["changed_blobs"][0]["path"] = r"src\..\secret.py"
        backslash["changed_blob_identity_sha256"] = profile._changed_blob_identity_sha256(
            backslash["changed_blobs"]
        )
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "canonical POSIX"
        ):
            action.validate_profile(backslash)

    def test_workflow_publisher_fences_changed_paths(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        backslash = chr(92)
        required_fences = (
            '(.path | utf8bytelength) <= 2048',
            '(.path == (.path | gsub("^'
            + backslash * 2
            + 's+|'
            + backslash * 2
            + 's+$"; "")))',
            '(.path | startswith("/") | not)',
            '(.path | contains("' + backslash * 2 + '") | not)',
            '(.path | explode | all(. >= 32 and . != 127))',
            '(.path | split("/") | all(. != "" and . != "." and . != ".."))',
        )
        for fence in required_fences:
            self.assertIn(fence, workflow)

    def test_foreign_head_terminal_is_validated_then_ignored(self) -> None:
        old_result = {
            **action._base_result(execution_sha=OLD_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": _candidate_profile(),
        }
        body = _result_body(old_result)
        self.assertFalse(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        self.assertTrue(action.parse_terminal_result(body, execution_sha=OLD_SHA))

        widened = json.loads(json.dumps(old_result))
        widened["publication_authorized"] = True
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "publication_authorized"
        ):
            action.parse_terminal_result(
                _result_body(widened), execution_sha=EXECUTION_SHA
            )

    def test_blocked_terminal_cannot_carry_partial_profile(self) -> None:
        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "metadata_acquisition_failure",
            "profile": None,
        }
        self.assertTrue(
            action.parse_terminal_result(
                _result_body(blocked), execution_sha=EXECUTION_SHA
            )
        )
        blocked["profile"] = _candidate_profile()
        with self.assertRaisesRegex(
            action.SiteModelCandidateTreeExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(
                _result_body(blocked), execution_sha=EXECUTION_SHA
            )

    def test_terminal_size_limit_counts_marker_newline_and_json_together(self) -> None:
        result = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "result_publication_limit",
            "profile": None,
        }
        body = _result_body(result)
        exact_size = len(body.encode("utf-8"))
        original_limit = action.MAX_TERMINAL_UTF8_BYTES
        try:
            action.MAX_TERMINAL_UTF8_BYTES = exact_size
            self.assertEqual(action._terminal_body(result), body)
            self.assertTrue(
                action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
            )
            action.MAX_TERMINAL_UTF8_BYTES = exact_size - 1
            with self.assertRaisesRegex(
                action.SiteModelCandidateTreeExecutionError,
                "result exceeds publication limit",
            ):
                action._terminal_body(result)
            with self.assertRaisesRegex(
                action.SiteModelCandidateTreeExecutionError,
                "result exceeds publication limit",
            ):
                action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
        finally:
            action.MAX_TERMINAL_UTF8_BYTES = original_limit

    def test_execution_authority_rebind_fails_closed(self) -> None:
        original = action._PROFILE
        try:
            action._PROFILE = lambda: _candidate_profile()
            with self.assertRaisesRegex(
                action.SiteModelCandidateTreeExecutionError,
                "execution authority drifted",
            ):
                action._require_execution_authority()
        finally:
            action._PROFILE = original


if __name__ == "__main__":
    unittest.main()
