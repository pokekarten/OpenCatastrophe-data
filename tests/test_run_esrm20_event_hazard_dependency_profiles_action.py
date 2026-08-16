# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from scripts import acquire_esrm20_event_hazard_dependencies as worker
from scripts import run_esrm20_event_hazard_dependency_profiles_action as subject

SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"


def request(action: str, **updates) -> str:
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": action,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, sort_keys=True, separators=(",", ":"))


def profile(group: int) -> dict:
    spec = worker.bridge.ROOT_SPECS[group]
    return {
        "schema_version": worker.bridge.SCHEMA_VERSION,
        "source_issue": worker.bridge.SOURCE_ISSUE,
        "control_issue": worker.bridge.CONTROL_ISSUE,
        "dataset_id": worker.bridge.DATASET_ID,
        "project_id": worker.bridge.PROJECT_ID,
        "project_path": worker.bridge.PROJECT_PATH,
        "commit_sha": worker.bridge.COMMIT_SHA,
        "group": group,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": spec.receipt_comment_id,
        "parser": worker.bridge.PARSER_ID,
        "dependencies": [
            {
                "section": "calculation",
                "option": "source_model_logic_tree_file",
                "raw_path": f"../Hazard/group{group}_source.xml",
                "resolved_path": f"Hazard/group{group}_source.xml",
            }
        ],
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


class EventHazardDependencyProfileActionTests(unittest.TestCase):
    def test_requests_are_exact_and_have_no_group_or_target_selectors(self):
        for action in (subject.ACTION_GROUP1, subject.ACTION_GROUP2):
            parsed = subject.validate_request(
                request(action), expected_issue=429, execution_sha=SHA
            )
            self.assertEqual(parsed["action"], action)
            for key, value in (
                ("group", 1),
                ("project_id", 269),
                ("path", "other.ini"),
                ("parser", "other"),
                ("dependency", "x"),
                ("url", "https://example.invalid"),
            ):
                with self.subTest(action=action, key=key), self.assertRaises(
                    subject.EventHazardDependencyActionError
                ):
                    subject.validate_request(
                        request(action, **{key: value}), expected_issue=429, execution_sha=SHA
                    )
        with self.assertRaises(subject.EventHazardDependencyActionError):
            subject.validate_request(
                request(subject.ACTION_GROUP1, target_sha="b" * 40),
                expected_issue=429,
                execution_sha=SHA,
            )

    def test_dispatch_is_group_specific_and_dedup_precedes_worker(self):
        calls = {1: 0, 2: 0}

        def one():
            calls[1] += 1
            return profile(1)

        def two():
            calls[2] += 1
            return profile(2)

        with mock.patch.object(subject, "has_terminal_result", return_value=False):
            result = subject.execute_profile(
                repository=REPOSITORY,
                token="t",
                action=subject.ACTION_GROUP1,
                execution_sha=SHA,
                group1_acquirer=one,
                group2_acquirer=two,
                now=lambda: "2026-08-16T20:30:00Z",
            )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(calls, {1: 1, 2: 0})

        calls = {1: 0, 2: 0}
        with mock.patch.object(subject, "has_terminal_result", return_value=True):
            duplicate = subject.execute_profile(
                repository=REPOSITORY,
                token="t",
                action=subject.ACTION_GROUP1,
                execution_sha=SHA,
                group1_acquirer=one,
                group2_acquirer=two,
            )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(calls, {1: 0, 2: 0})

    def test_profile_rebinds_exact_receipt_parser_and_closed_dependencies(self):
        for action, group in ((subject.ACTION_GROUP1, 1), (subject.ACTION_GROUP2, 2)):
            value = profile(group)
            value["profiled_at"] = "2026-08-16T20:30:00Z"
            self.assertEqual(subject.validate_profile(value, action=action), value)

            wrong = copy.deepcopy(value)
            wrong["group"] = 2 if group == 1 else 1
            with self.assertRaises(subject.EventHazardDependencyActionError):
                subject.validate_profile(wrong, action=action)

            widened = copy.deepcopy(value)
            widened["dependencies"][0]["raw_provider_value"] = "secret"
            with self.assertRaises(subject.EventHazardDependencyActionError):
                subject.validate_profile(widened, action=action)

    def test_dependency_normalization_duplicates_and_order_fail_closed(self):
        value = profile(1)
        value["profiled_at"] = "2026-08-16T20:30:00Z"
        value["dependencies"][0]["resolved_path"] = "wrong.xml"
        with self.assertRaises(subject.EventHazardDependencyActionError):
            subject.validate_profile(value, action=subject.ACTION_GROUP1)

        value = profile(1)
        value["profiled_at"] = "2026-08-16T20:30:00Z"
        value["dependencies"].append(copy.deepcopy(value["dependencies"][0]))
        with self.assertRaises(subject.EventHazardDependencyActionError):
            subject.validate_profile(value, action=subject.ACTION_GROUP1)

    def test_failure_is_value_free_and_authority_never_widens(self):
        def fail():
            raise worker.EventHazardDependencyAcquisitionError("PROVIDER_SECRET")

        with mock.patch.object(subject, "has_terminal_result", return_value=False):
            result = subject.execute_profile(
                repository=REPOSITORY,
                token="t",
                action=subject.ACTION_GROUP1,
                execution_sha=SHA,
                group1_acquirer=fail,
                group2_acquirer=lambda: profile(2),
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["profile"])
        self.assertNotIn("PROVIDER_SECRET", json.dumps(result))
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])

    def test_terminal_result_rejects_nested_and_top_level_widening(self):
        value = profile(1)
        value["profiled_at"] = "2026-08-16T20:30:00Z"
        result = {
            **subject._base_result(action=subject.ACTION_GROUP1, execution_sha=SHA),
            "status": "pass",
            "failure_class": None,
            "profile": value,
        }
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(
            subject.validate_terminal_result(body, action=subject.ACTION_GROUP1, execution_sha=SHA)
        )

        for mutation in ("top", "nested"):
            mutated = copy.deepcopy(result)
            if mutation == "top":
                mutated["model_execution_authorized"] = True
            else:
                mutated["profile"]["dependencies"][0]["raw_values"] = ["secret"]
            bad = subject.RESULT_MARKER + "\n" + json.dumps(mutated, sort_keys=True, separators=(",", ":"))
            with self.subTest(mutation=mutation), self.assertRaises(
                subject.EventHazardDependencyActionError
            ):
                subject.validate_terminal_result(
                    bad, action=subject.ACTION_GROUP1, execution_sha=SHA
                )

    def test_trusted_bot_dedup_is_action_and_execution_scoped(self):
        value = profile(1)
        value["profiled_at"] = "2026-08-16T20:30:00Z"
        result = {
            **subject._base_result(action=subject.ACTION_GROUP1, execution_sha=SHA),
            "status": "pass",
            "failure_class": None,
            "profile": value,
        }
        comments = [
            {
                "id": 1,
                "user": {"login": "github-actions[bot]"},
                "body": subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":")),
            }
        ]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments), mock.patch.object(
            subject, "fetch_repository_comments", subject._FETCH_COMMENTS
        ):
            self.assertTrue(
                subject.has_terminal_result(
                    repository=REPOSITORY,
                    token="t",
                    action=subject.ACTION_GROUP1,
                    execution_sha=SHA,
                )
            )
            self.assertFalse(
                subject.has_terminal_result(
                    repository=REPOSITORY,
                    token="t",
                    action=subject.ACTION_GROUP2,
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
