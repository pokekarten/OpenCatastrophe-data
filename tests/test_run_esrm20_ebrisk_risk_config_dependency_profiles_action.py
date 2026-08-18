# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import shutil
import subprocess
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


def publisher_payload() -> dict[str, object]:
    profiles: list[dict[str, object]] = []
    for spec in bridge.CONFIG_SPECS:
        item = profile_for(spec)
        item["profiled_at"] = NOW
        profiles.append(item)
    return {
        **action._base_result(execution_sha=SHA),
        "status": "pass",
        "failure_class": None,
        "profiles": profiles,
    }


def publisher_jq_program() -> str:
    workflow = Path(
        ".github/workflows/esrm20-ebrisk-risk-config-dependency-profiles.yml"
    ).read_text(encoding="utf-8")
    marker = "          printf '%s' \"$RESULT_JSON\" | jq -e --arg sha \"$EXECUTION_SHA\" '\n"
    if marker not in workflow:
        raise AssertionError("publisher jq validation marker is absent")
    program = workflow.split(marker, 1)[1].split("\n          ' >/dev/null", 1)[0]
    return "\n".join(
        line[12:] if line.startswith("            ") else line
        for line in program.splitlines()
    )


class EbriskDependencyProfilesActionTests(unittest.TestCase):
    def test_request_is_closed_and_has_no_candidate_selector(self) -> None:
        parsed = action.validate_request(
            request_body(), expected_issue=281, execution_sha=SHA
        )
        self.assertEqual(parsed["action"], action.ACTION)
        with self.assertRaisesRegex(
            action.EbriskDependencyProfilesActionError, "fields drifted"
        ):
            action.validate_request(
                request_body(candidate="group1"), expected_issue=281, execution_sha=SHA
            )

    def test_public_production_entry_points_have_no_injection_seams(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(action.execute_profiles).parameters),
            ("repository", "token", "execution_sha"),
        )
        for worker in (
            action.worker.acquire_group1_dependencies,
            action.worker.acquire_group2_dependencies,
            action.worker.acquire_iceland_dependencies,
        ):
            self.assertEqual(tuple(inspect.signature(worker).parameters), ())

    def test_inner_verified_parser_rebinding_fails_before_provider_io(self) -> None:
        forged = lambda *args, **kwargs: {"forged": True}
        with mock.patch.object(
            action.worker.bridge,
            "extract_verified_ebrisk_dependencies",
            forged,
        ):
            with self.assertRaisesRegex(
                action.worker.EbriskDependencyAcquisitionError,
                "verified parser drifted",
            ):
                action.worker.acquire_group1_dependencies()

    def test_action_acquirer_tuple_rebinding_fails_closed(self) -> None:
        rebound = tuple(list(action._ACQUIRERS))
        self.assertIsNot(rebound, action._CANONICAL_ACQUIRERS)
        with mock.patch.object(action, "_ACQUIRERS", rebound):
            with self.assertRaisesRegex(
                action.EbriskDependencyProfilesActionError,
                "acquirer tuple drifted",
            ):
                action.validate_request(
                    request_body(), expected_issue=281, execution_sha=SHA
                )

    def test_pass_requires_exact_three_ordered_profiles_and_preserves_ceilings(self) -> None:
        result = publisher_payload()
        validated = action.validate_terminal_result(result, execution_sha=SHA)
        self.assertEqual(
            [p["candidate_key"] for p in validated["profiles"]],
            ["group1", "group2", "iceland"],
        )
        self.assertFalse(validated["historical_group_assignment_verified"])
        self.assertFalse(validated["dependency_inventory_authorized"])
        self.assertFalse(validated["runtime_compatibility_verified"])
        self.assertFalse(validated["model_use_authorized"])

    def test_swapped_profiles_fail_closed(self) -> None:
        result = publisher_payload()
        result["profiles"][0], result["profiles"][1] = (
            result["profiles"][1],
            result["profiles"][0],
        )
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
        with self.assertRaisesRegex(
            action.EbriskDependencyProfilesActionError, "fields drifted"
        ):
            action.validate_terminal_result(result, execution_sha=SHA)

    def test_dependency_values_are_strictly_revalidated(self) -> None:
        spec = bridge.CONFIG_SPECS[0]
        base = profile_for(spec)["dependencies"][0]
        for field, value in (
            ("raw_path", "${MODEL}/exposure.xml"),
            ("raw_path", "../../outside.xml"),
            ("raw_path", "/tmp/exposure.xml"),
            ("raw_path", "..\\Exposure\\exposure.xml"),
            ("resolved_path", "Elsewhere/exposure.xml"),
            ("section", "input\nforged"),
        ):
            row = dict(base)
            row[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(action.EbriskDependencyProfilesActionError):
                    action._validate_dependency(row, config_path=spec.repository_path)

    def test_late_acquisition_failure_is_atomic(self) -> None:
        first = mock.Mock(return_value=profile_for(bridge.CONFIG_SPECS[0]))
        second = mock.Mock(
            side_effect=action.worker.EbriskDependencyAcquisitionError("boom")
        )
        third = mock.Mock(return_value=profile_for(bridge.CONFIG_SPECS[2]))
        result = action._execute_profiles(
            repository="pokekarten/OpenCatastrophe-data",
            token="token",
            execution_sha=SHA,
            acquirers=(first, second, third),
            now=lambda: NOW,
            fetch_comments=lambda *args, **kwargs: [],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profiles"])
        first.assert_called_once_with()
        second.assert_called_once_with()
        third.assert_not_called()

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
        self.assertTrue(
            action._has_terminal_result(
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                execution_sha=SHA,
                fetch_comments=fake_comments,
            )
        )

    def test_privileged_publisher_declares_independent_semantic_fences(self) -> None:
        workflow = Path(
            ".github/workflows/esrm20-ebrisk-risk-config-dependency-profiles.yml"
        ).read_text(encoding="utf-8")
        publisher = workflow.split("publish-dependency-profiles:", 1)[1]
        required_fences = (
            "test \"$(printf '%s' \"$RESULT_JSON\" | wc -c)\" -le 96000",
            "def bounded_text:",
            "def canonical_utc:",
            "def safe_raw_path:",
            "def normalize_ref($config; $raw):",
            "def dependency_set_valid:",
            ".resolved_path == normalize_ref($config; .raw_path)",
            "sort_by([.resolved_path,.section,.option,.raw_path])",
            "map([.section,.option,.resolved_path]) | unique | length",
        )
        for fence in required_fences:
            with self.subTest(fence=fence):
                self.assertIn(fence, publisher)

    @unittest.skipUnless(shutil.which("jq"), "jq required for publisher boundary mutation tests")
    def test_checkoutless_publisher_rejects_dependency_evidence_mutations(self) -> None:
        program = publisher_jq_program()

        def jq_accepts(payload: dict[str, object]) -> bool:
            completed = subprocess.run(
                ["jq", "-e", "--arg", "sha", SHA, program],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return completed.returncode == 0

        base = publisher_payload()
        self.assertTrue(jq_accepts(base))

        mutations: list[tuple[str, dict[str, object]]] = []
        for name, field, value in (
            ("resolved mismatch", "resolved_path", "Elsewhere/exposure.xml"),
            ("repository escape", "raw_path", "../../outside.xml"),
            ("placeholder", "raw_path", "${MODEL}/exposure.xml"),
            ("absolute path", "raw_path", "/tmp/exposure.xml"),
            ("backslash path", "raw_path", "..\\Exposure\\exposure.xml"),
            ("control character", "section", "input\nforged"),
        ):
            candidate = copy.deepcopy(base)
            candidate["profiles"][0]["dependencies"][0][field] = value
            mutations.append((name, candidate))

        invalid_time = copy.deepcopy(base)
        invalid_time["profiles"][0]["profiled_at"] = "2026-02-30T12:00:00Z"
        mutations.append(("invalid timestamp", invalid_time))

        duplicate = copy.deepcopy(base)
        duplicate["profiles"][0]["dependencies"] *= 2
        mutations.append(("duplicate dependency", duplicate))

        unordered = copy.deepcopy(base)
        unordered["profiles"][0]["dependencies"] = [
            {
                "section": "input",
                "option": "z_file",
                "raw_path": "../Z/z.xml",
                "resolved_path": "Z/z.xml",
            },
            {
                "section": "input",
                "option": "a_file",
                "raw_path": "../A/a.xml",
                "resolved_path": "A/a.xml",
            },
        ]
        mutations.append(("non-canonical dependency order", unordered))

        for name, candidate in mutations:
            with self.subTest(name=name):
                self.assertFalse(jq_accepts(candidate))


if __name__ == "__main__":
    unittest.main()
