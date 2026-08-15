# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import acquire_eshm20_root_dependencies as worker
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment
from scripts.prepare_agent_action_result import prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

ACTION = "efehr_eshm20_root_dependency_profile"
DATASET = "efehr.eshm20"
SHA = "a" * 40


def request(**updates):
    value = {"schema_version": "oc-action-request-v1", "action": ACTION, "issue": 353, "target_sha": SHA, "dataset_id": DATASET, "requester": "test-353"}
    value.update(updates)
    return value


def profile():
    bridge = worker.bridge
    return {
        "schema_version": bridge.SCHEMA_VERSION, "source_issue": bridge.SOURCE_ISSUE,
        "dataset_id": bridge.DATASET_ID, "project_id": bridge.PROJECT_ID, "project_path": bridge.PROJECT_PATH,
        "commit_sha": bridge.COMMIT_SHA, "repository_path": bridge.REPOSITORY_PATH,
        "byte_count": bridge.EXPECTED_BYTE_COUNT, "sha256": bridge.EXPECTED_SHA256, "parser": bridge.PARSER_ID,
        "inventory_receipt_comment_id": bridge.INVENTORY_RECEIPT_COMMENT_ID,
        "root_receipt_comment_id": worker.ROOT_RECEIPT_COMMENT_ID, "root_receipt_run_id": worker.ROOT_RECEIPT_RUN_ID,
        "root_receipt_execution_sha": worker.ROOT_RECEIPT_EXECUTION_SHA,
        "dependencies": [{"section": "site_model", "option": "site_model_file", "raw_path": "eshm20_site_model_v06d.csv", "resolved_path": bridge.PREFIX + "eshm20_site_model_v06d.csv"}],
        "dependency_inventory_authorized": False, "profiled_at": "2026-08-15T09:10:01Z",
        "external_bytes_persisted": False, "publication_authorized": False,
    }


class Eshm20RootDependencyActionWiringTests(unittest.TestCase):
    def test_request_is_closed_to_issue_and_dataset(self):
        self.assertEqual(validate_request(request(), expected_issue=353), request())
        with self.assertRaises(RequestError):
            validate_request(request(issue=352), expected_issue=352)
        with self.assertRaises(RequestError):
            validate_request(request(dataset_id="other.dataset"), expected_issue=353)

    def test_target_sha_must_equal_trusted_execution_sha(self):
        with self.assertRaises(ProtocolError):
            prepare_completed_result(request(target_sha="b" * 40), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=lambda: profile())

    def test_dedup_happens_before_provider_work(self):
        first = prepare_completed_result(request(), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=lambda: profile())
        called = False
        def explode():
            nonlocal called
            called = True
            raise AssertionError("provider must not run")
        duplicate = prepare_completed_result(request(), [{"id": 99, "body": canonical_result_comment(first), "user": {"login": "github-actions[bot]"}}], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=2, run_id=2, run_attempt=1, started_at="2026-08-15T09:11:00Z", eshm20_root_dependency_acquirer=explode)
        self.assertFalse(called)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 99)

    def test_worker_failure_is_closed_and_carries_no_payload(self):
        def blocked():
            raise worker.Eshm20RootDependencyAcquisitionError("bounded failure")
        result = prepare_completed_result(request(), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=blocked)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][ACTION])
        self.assertEqual(result["failure_class"], "acquisition_failed")

    def test_result_rebinds_exact_provenance_and_authority_ceiling(self):
        base = prepare_completed_result(request(), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=lambda: profile())
        self.assertEqual(base["status"], "pass")
        for field, bad in (("root_receipt_comment_id", worker.ROOT_RECEIPT_COMMENT_ID + 1), ("root_receipt_run_id", worker.ROOT_RECEIPT_RUN_ID + 1), ("root_receipt_execution_sha", "b" * 40), ("parser", "other.parser"), ("sha256", "b" * 64), ("byte_count", worker.bridge.EXPECTED_BYTE_COUNT + 1), ("dependency_inventory_authorized", True), ("external_bytes_persisted", True), ("publication_authorized", True)):
            mutated = copy.deepcopy(base)
            mutated["evidence"][ACTION][field] = bad
            with self.subTest(field=field), self.assertRaises(ResultError):
                validate_result(mutated)

    def test_dependency_shape_inventory_sort_and_type_fail_closed(self):
        base = prepare_completed_result(request(), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=lambda: profile())
        mutations = []
        a = copy.deepcopy(base); a["evidence"][ACTION]["dependencies"][0]["resolved_path"] = "outside.xml"; mutations.append(a)
        b = copy.deepcopy(base); b["evidence"][ACTION]["dependencies"][0]["section"] = []; mutations.append(b)
        c = copy.deepcopy(base); c["evidence"][ACTION]["dependencies"].append(copy.deepcopy(c["evidence"][ACTION]["dependencies"][0])); mutations.append(c)
        for mutated in mutations:
            with self.assertRaises(ResultError):
                validate_result(mutated)


    def test_portable_result_schema_matches_closed_353_phase_contract(self):
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/agent-action-result-v1.schema.json").read_text(encoding="utf-8"))
        self.assertIn(ACTION, schema["properties"]["action"]["enum"])
        evidence = schema["properties"]["evidence"]["oneOf"]
        self.assertTrue(any(ACTION in branch.get("required", []) for branch in evidence))

        guards = schema["allOf"]
        phase_guard = next(
            branch for branch in guards
            if branch.get("if", {}).get("properties") == {"phase": {"const": "acquisition_receipt"}}
        )
        self.assertIn(ACTION, phase_guard["then"]["properties"]["action"]["enum"])

        def guard_for(status=None):
            expected = {"phase": {"const": "acquisition_receipt"}, "action": {"const": ACTION}}
            if status is not None:
                expected["status"] = {"const": status}
            return next(branch for branch in guards if branch.get("if", {}).get("properties") == expected)

        binding = guard_for()
        self.assertEqual(binding["then"]["properties"]["source_issue"], {"const": 353})
        self.assertEqual(binding["then"]["properties"]["dataset_id"], {"const": DATASET})
        self.assertEqual(binding["then"]["properties"]["evidence"], {"required": [ACTION]})
        self.assertEqual(
            guard_for("pass")["then"]["properties"]["evidence"]["properties"][ACTION],
            {"$ref": "#/$defs/efehrEshm20RootDependencyProfile"},
        )
        self.assertEqual(
            guard_for("blocked")["then"]["properties"]["evidence"]["properties"][ACTION],
            {"type": "null"},
        )

    def test_profiled_at_is_bounded_by_action_time(self):
        base = prepare_completed_result(request(), [], repository="pokekarten/OpenCatastrophe-data", execution_sha=SHA, source_comment_id=1, run_id=1, run_attempt=1, started_at="2026-08-15T09:10:00Z", eshm20_root_dependency_acquirer=lambda: profile())
        mutated = copy.deepcopy(base)
        mutated["evidence"][ACTION]["profiled_at"] = "2026-08-15T09:09:59Z"
        with self.assertRaises(ResultError):
            validate_result(mutated)


if __name__ == "__main__":
    unittest.main()
