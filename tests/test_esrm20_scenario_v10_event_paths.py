# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from scripts import acquire_efehr_esrm20_scenario_tree_metadata as tree
from scripts import profile_esrm20_scenario_v10_event_paths as profile
from scripts import run_esrm20_scenario_v10_event_paths_action as action

EXECUTION_SHA = "b" * 40
FOREIGN_SHA = "c" * 40


def _entry(path: str, *, kind: str = "blob", object_id: str = "a" * 40) -> dict:
    return {
        "path": path,
        "type": kind,
        "id": object_id,
        "mode": "040000" if kind == "tree" else "100644",
    }


def _receipt(entries: list[dict] | None = None) -> dict:
    values = entries or [
        _entry("ruptures", kind="tree", object_id="1" * 40),
        _entry(
            f"ruptures/{profile.TARGET_EVENT_ID}.xml",
            object_id="2" * 40,
        ),
        _entry("shakemaps", kind="tree", object_id="3" * 40),
        _entry(
            f"shakemaps/{profile.TARGET_EVENT_ID}.csv",
            object_id="4" * 40,
        ),
        _entry("README.md", object_id="5" * 40),
    ]
    return {
        "schema_version": tree.SCHEMA_VERSION,
        "operation_id": tree.OPERATION_ID,
        "source_issue": 285,
        "dataset_id": tree.DATASET_ID,
        "provider_host": tree.PROVIDER_HOST,
        "project_id": 273,
        "project_path": "efehr/esrm20_scenario_tests",
        "release_tag": "v1.0",
        "tag_api_url": tree.TAG_API_URL,
        "resolved_commit_sha": profile.EXPECTED_COMMIT_SHA,
        "retrieved_at": "2026-08-17T21:30:00Z",
        "tree_page_count": 1,
        "tree_entry_count": len(values),
        "metadata_byte_count": 1024,
        "entries": values,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _tree_identity(entries: list[dict]) -> str:
    canonical = "".join(
        f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
        for item in sorted(
            entries, key=lambda item: (item["path"], item["type"], item["id"])
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class ScenarioV10EventPathProfileTests(unittest.TestCase):
    def test_profile_resolves_only_fixed_identifier_below_two_fixed_roots(self) -> None:
        receipt = _receipt()
        result = profile.profile_event_paths(acquire=lambda: receipt)

        self.assertEqual(result["target_event_id"], "Greece_07-9-1999")
        self.assertEqual(result["commit_sha"], profile.EXPECTED_COMMIT_SHA)
        self.assertEqual(result["tree_identity_sha256"], _tree_identity(receipt["entries"]))
        self.assertEqual(result["matched_blob_count"], 2)
        self.assertEqual(
            result["root_blob_counts"], {"ruptures": 1, "shakemaps": 1}
        )
        self.assertEqual(
            [item["root"] for item in result["matches"]],
            ["ruptures", "shakemaps"],
        )
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_profile_requires_both_roots_and_rejects_identifier_outside_them(self) -> None:
        missing_shakemap = _receipt(
            [
                _entry("ruptures", kind="tree", object_id="1" * 40),
                _entry(
                    f"ruptures/{profile.TARGET_EVENT_ID}.xml",
                    object_id="2" * 40,
                ),
            ]
        )
        with self.assertRaisesRegex(
            profile.ScenarioEventPathProfileError, "both fixed roots"
        ):
            profile.profile_event_paths(acquire=lambda: missing_shakemap)

        outside = _receipt(
            _receipt()["entries"]
            + [_entry(f"plots/{profile.TARGET_EVENT_ID}.png", object_id="6" * 40)]
        )
        with self.assertRaisesRegex(
            profile.ScenarioEventPathProfileError, "outside fixed scenario roots"
        ):
            profile.profile_event_paths(acquire=lambda: outside)

    def test_profile_rejects_commit_path_and_duplicate_drift(self) -> None:
        wrong_commit = _receipt()
        wrong_commit["resolved_commit_sha"] = "f" * 40
        with self.assertRaisesRegex(
            profile.ScenarioEventPathProfileError, "resolved_commit_sha"
        ):
            profile.profile_event_paths(acquire=lambda: wrong_commit)

        for bad_path in (
            f"ruptures/../{profile.TARGET_EVENT_ID}.xml",
            f"ruptures//{profile.TARGET_EVENT_ID}.xml",
            f"ruptures/{profile.TARGET_EVENT_ID}.xml/",
            f"ruptures\\{profile.TARGET_EVENT_ID}.xml",
        ):
            with self.subTest(path=bad_path):
                noncanonical = _receipt()
                noncanonical["entries"][1]["path"] = bad_path
                with self.assertRaisesRegex(
                    profile.ScenarioEventPathProfileError, "canonical relative POSIX"
                ):
                    profile.profile_event_paths(acquire=lambda: noncanonical)

        duplicate = _receipt()
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][1]))
        duplicate["tree_entry_count"] += 1
        with self.assertRaisesRegex(
            profile.ScenarioEventPathProfileError, "paths are not unique"
        ):
            profile.profile_event_paths(acquire=lambda: duplicate)

    def test_profile_revalidates_git_type_mode_binding(self) -> None:
        mismatched = _receipt()
        mismatched["entries"][1]["mode"] = "040000"
        with self.assertRaisesRegex(
            profile.ScenarioEventPathProfileError, "type/mode binding"
        ):
            profile.profile_event_paths(acquire=lambda: mismatched)

    def test_profile_rejects_authority_widening(self) -> None:
        for field in (
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                mutated = _receipt()
                mutated[field] = True
                with self.assertRaisesRegex(
                    profile.ScenarioEventPathProfileError, field
                ):
                    profile.profile_event_paths(acquire=lambda: mutated)


class ScenarioV10EventPathActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        return profile.profile_event_paths(acquire=lambda: _receipt())

    def _result_body(self, execution_sha: str, value: dict) -> str:
        return action.RESULT_MARKER + "\n" + json.dumps(
            value, sort_keys=True, separators=(",", ":")
        )

    def test_request_is_strict_and_bound_to_current_execution_sha(self) -> None:
        request = {
            "schema_version": action.REQUEST_SCHEMA_VERSION,
            "issue": 285,
            "target_sha": EXECUTION_SHA,
            "requester": "test-runner",
        }
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            request, separators=(",", ":")
        )
        parsed = action.validate_request(
            body, expected_issue=285, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)

        extra = dict(request, event_id=profile.TARGET_EVENT_ID)
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError, "fields drifted"
        ):
            action.validate_request(
                action.REQUEST_MARKER + "\n" + json.dumps(extra),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
            )
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":285,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError, "duplicate JSON key"
        ):
            action.validate_request(
                duplicate, expected_issue=285, execution_sha=EXECUTION_SHA
            )

    def test_profile_validator_rejects_extra_fields_and_semantic_widening(self) -> None:
        valid = self._profile()
        action.validate_profile(valid)

        extra = copy.deepcopy(valid)
        extra["matches"][0]["city"] = "Athens"
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError, "match shape drifted"
        ):
            action.validate_profile(extra)

        widened = copy.deepcopy(valid)
        widened["event_location_inference_authorized"] = True
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError,
            "event_location_inference_authorized",
        ):
            action.validate_profile(widened)

        bad_root = copy.deepcopy(valid)
        bad_root["matches"][0]["root"] = "plots"
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError, "root drifted"
        ):
            action.validate_profile(bad_root)

    def test_profile_validator_rejects_noncanonical_durable_match_paths(self) -> None:
        for bad_path in (
            f"ruptures/../shakemaps/{profile.TARGET_EVENT_ID}.xml",
            f"ruptures//{profile.TARGET_EVENT_ID}.xml",
            f"ruptures/{profile.TARGET_EVENT_ID}.xml/",
        ):
            with self.subTest(path=bad_path):
                mutated = copy.deepcopy(self._profile())
                mutated["matches"][0]["path"] = bad_path
                mutated["relation_sha256"] = action._relation_sha(mutated["matches"])
                with self.assertRaisesRegex(
                    action.ScenarioEventPathExecutionError,
                    "canonical relative POSIX",
                ):
                    action.validate_profile(mutated)

    def test_terminal_result_blocks_evidence_on_failure(self) -> None:
        valid = self._profile()
        passed = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": valid,
        }
        self.assertTrue(
            action.parse_terminal_result(
                self._result_body(EXECUTION_SHA, passed),
                execution_sha=EXECUTION_SHA,
            )
        )

        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "event_path_resolution_failure",
            "profile": None,
        }
        self.assertTrue(
            action.parse_terminal_result(
                self._result_body(EXECUTION_SHA, blocked),
                execution_sha=EXECUTION_SHA,
            )
        )
        blocked["profile"] = valid
        with self.assertRaisesRegex(
            action.ScenarioEventPathExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(
                self._result_body(EXECUTION_SHA, blocked),
                execution_sha=EXECUTION_SHA,
            )

    def test_foreign_sha_terminal_is_validated_but_does_not_deduplicate_current(self) -> None:
        valid = self._profile()
        foreign = {
            **action._base_result(execution_sha=FOREIGN_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": valid,
        }
        original = action._FETCH_COMMENTS
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": self._result_body(FOREIGN_SHA, foreign),
            }
        ]
        try:
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )
        finally:
            action._FETCH_COMMENTS = original

        malformed = copy.deepcopy(foreign)
        malformed["profile"]["publication_authorized"] = True
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": self._result_body(FOREIGN_SHA, malformed),
            }
        ]
        try:
            with self.assertRaisesRegex(
                action.ScenarioEventPathExecutionError, "publication_authorized"
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
        finally:
            action._FETCH_COMMENTS = original

        noncanonical = copy.deepcopy(foreign)
        noncanonical["profile"]["matches"][0]["path"] = (
            f"ruptures/../shakemaps/{profile.TARGET_EVENT_ID}.xml"
        )
        noncanonical["profile"]["relation_sha256"] = action._relation_sha(
            noncanonical["profile"]["matches"]
        )
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": self._result_body(FOREIGN_SHA, noncanonical),
            }
        ]
        try:
            with self.assertRaisesRegex(
                action.ScenarioEventPathExecutionError, "canonical relative POSIX"
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
        finally:
            action._FETCH_COMMENTS = original

    def test_workflow_publication_job_is_checkoutless_and_closed(self) -> None:
        workflow = Path(
            ".github/workflows/esrm20-scenario-v10-event-paths.yml"
        ).read_text(encoding="utf-8")
        publish = workflow.split("publish-event-paths:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn('keys == [', publish)
        self.assertIn('"Greece_07-9-1999"', publish)
        self.assertIn("event_location_inference_authorized == false", publish)
        self.assertIn("PurePosixPath", publish)
        self.assertIn('parts = path.split("/")', publish)
        self.assertIn('part in ("", ".", "..")', publish)
        self.assertNotIn("upload-artifact", workflow)


if __name__ == "__main__":
    unittest.main()
