# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import acquire_eshm20_gsim_resource_profile as worker
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment
from scripts.prepare_agent_action_result import ledger_issue_for_request, prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

ACTION = "efehr_eshm20_gsim_resource_profile"
DATASET = "efehr.eshm20"
SHA = "a" * 40


def request(**updates):
    value = {
        "schema_version": "oc-action-request-v1",
        "action": ACTION,
        "issue": 376,
        "target_sha": SHA,
        "dataset_id": DATASET,
        "requester": "test-376",
    }
    value.update(updates)
    return value


def profile():
    resolved = (
        "oq_computational/oq_configuration_eshm20_v12e_region_main/"
        "eshm20_site_model_v06d.csv"
    )
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "source_issue": worker.SOURCE_ISSUE,
        "control_issue": worker.CONTROL_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "openquake_reference": worker.OPENQUAKE_REFERENCE,
        "inventory_receipt_comment_id": worker.INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": worker.ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": worker.ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_result_comment_id": worker.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": worker.FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": worker.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "first_order_receipt_retrieved_at": worker.FIRST_ORDER_RECEIPT_RETRIEVED_AT,
        "branch_set_count": 1,
        "branch_count": 1,
        "resource_reference_count": 1,
        "resources": [
            {
                "argument_key": "site_model_file",
                "relative_path": "eshm20_site_model_v06d.csv",
                "resolved_path": resolved,
                "selected_prefix_inventory_member": True,
                "comment_prefixed": False,
                "origins": [{"branch_set_id": "bs1", "branch_id": "b1"}],
            }
        ],
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class Eshm20GsimResourceActionWiringTests(unittest.TestCase):
    def completed(self, value=None):
        return prepare_completed_result(
            request(),
            [],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=SHA,
            source_comment_id=1,
            run_id=1,
            run_attempt=1,
            started_at="2026-08-15T12:20:00Z",
            eshm20_gsim_resource_acquirer=lambda: profile() if value is None else value,
        )

    def test_request_and_ledger_are_closed_to_issue_and_dataset(self):
        self.assertEqual(validate_request(request(), expected_issue=376), request())
        self.assertEqual(ledger_issue_for_request(request()), 376)
        with self.assertRaises(RequestError):
            validate_request(request(issue=375), expected_issue=375)
        with self.assertRaises(RequestError):
            validate_request(request(dataset_id="other.dataset"), expected_issue=376)

    def test_target_sha_must_equal_trusted_execution_sha_before_worker(self):
        called = False

        def explode():
            nonlocal called
            called = True
            raise AssertionError("worker must not run")

        with self.assertRaises(ProtocolError):
            prepare_completed_result(
                request(target_sha="b" * 40),
                [],
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha=SHA,
                source_comment_id=1,
                run_id=1,
                run_attempt=1,
                started_at="2026-08-15T12:20:00Z",
                eshm20_gsim_resource_acquirer=explode,
            )
        self.assertFalse(called)

    def test_dedup_happens_before_provider_work(self):
        first = self.completed()
        called = False

        def explode():
            nonlocal called
            called = True
            raise AssertionError("provider must not run")

        duplicate = prepare_completed_result(
            request(),
            [{
                "id": 99,
                "body": canonical_result_comment(first),
                "user": {"login": "github-actions[bot]"},
            }],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=SHA,
            source_comment_id=2,
            run_id=2,
            run_attempt=1,
            started_at="2026-08-15T12:21:00Z",
            eshm20_gsim_resource_acquirer=explode,
        )
        self.assertFalse(called)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 99)

    def test_worker_failure_is_closed_and_payload_is_not_durable(self):
        sentinel = "<provider-payload-must-not-persist>"

        def blocked():
            raise worker.Eshm20GsimResourceProfileError(sentinel)

        result = prepare_completed_result(
            request(),
            [],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=SHA,
            source_comment_id=1,
            run_id=1,
            run_attempt=1,
            started_at="2026-08-15T12:20:00Z",
            eshm20_gsim_resource_acquirer=blocked,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][ACTION])
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertNotIn(sentinel, json.dumps(result, sort_keys=True))

    def test_result_rebinds_provenance_counts_and_all_authority_ceilings(self):
        base = self.completed()
        self.assertEqual(base["status"], "pass")
        mutations = {
            "source_issue": worker.SOURCE_ISSUE + 1,
            "control_issue": worker.CONTROL_ISSUE + 1,
            "commit_sha": "b" * 40,
            "byte_count": worker.EXPECTED_BYTE_COUNT + 1,
            "sha256": "b" * 64,
            "openquake_reference": "other",
            "first_order_receipt_result_comment_id": worker.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID + 1,
            "first_order_receipt_execution_sha": "b" * 40,
            "dependency_inventory_authorized": True,
            "dependency_receipt_authorized": True,
            "external_bytes_persisted": True,
            "publication_authorized": True,
            "model_use_authorized": True,
        }
        for field, bad in mutations.items():
            mutated = copy.deepcopy(base)
            mutated["evidence"][ACTION][field] = bad
            with self.subTest(field=field), self.assertRaises(ResultError):
                validate_result(mutated)

    def test_resource_path_inventory_origin_and_order_are_independently_validated(self):
        base = self.completed()
        cases = []

        forged_member = copy.deepcopy(base)
        forged_member["evidence"][ACTION]["resources"][0]["selected_prefix_inventory_member"] = False
        cases.append(forged_member)

        mismatched = copy.deepcopy(base)
        mismatched["evidence"][ACTION]["resources"][0]["resolved_path"] = "outside.csv"
        cases.append(mismatched)

        unsafe = copy.deepcopy(base)
        unsafe["evidence"][ACTION]["resources"][0]["relative_path"] = "../escape.csv"
        cases.append(unsafe)

        bad_origin = copy.deepcopy(base)
        bad_origin["evidence"][ACTION]["resources"][0]["origins"][0]["branch_id"] = " bad "
        cases.append(bad_origin)

        duplicate = copy.deepcopy(base)
        duplicate["evidence"][ACTION]["resources"].append(
            copy.deepcopy(duplicate["evidence"][ACTION]["resources"][0])
        )
        duplicate["evidence"][ACTION]["resource_reference_count"] = 2
        cases.append(duplicate)

        count_mismatch = copy.deepcopy(base)
        count_mismatch["evidence"][ACTION]["resource_reference_count"] = 2
        cases.append(count_mismatch)

        for mutated in cases:
            with self.assertRaises(ResultError):
                validate_result(mutated)

    def test_bool_int_confusion_and_profile_time_escape_fail_closed(self):
        base = self.completed()
        for field in ("branch_set_count", "branch_count", "resource_reference_count"):
            mutated = copy.deepcopy(base)
            mutated["evidence"][ACTION][field] = True
            with self.subTest(field=field), self.assertRaises(ResultError):
                validate_result(mutated)

        mutated = copy.deepcopy(base)
        mutated["evidence"][ACTION]["profiled_at"] = "2026-08-15T12:19:59Z"
        with self.assertRaises(ResultError):
            validate_result(mutated)

    def test_portable_result_schema_has_complete_376_phase_contract(self):
        schema = json.loads(
            (Path(__file__).resolve().parents[1] / "schemas/agent-action-result-v1.schema.json")
            .read_text(encoding="utf-8")
        )
        self.assertIn(ACTION, schema["properties"]["action"]["enum"])
        evidence = schema["properties"]["evidence"]["oneOf"]
        self.assertTrue(any(ACTION in branch.get("required", []) for branch in evidence))

        guards = schema["allOf"]
        phase_guard = next(
            branch for branch in guards
            if branch.get("if", {}).get("properties") == {"phase": {"const": "acquisition_receipt"}}
        )
        self.assertIn(ACTION, phase_guard["then"]["properties"]["action"]["enum"])

        expected = {"phase": {"const": "acquisition_receipt"}, "action": {"const": ACTION}}
        binding = next(
            branch for branch in guards
            if branch.get("if", {}).get("properties") == expected
        )
        self.assertEqual(binding["then"]["properties"]["source_issue"], {"const": 376})
        self.assertEqual(binding["then"]["properties"]["dataset_id"], {"const": DATASET})
        self.assertEqual(binding["then"]["properties"]["evidence"], {"required": [ACTION]})


if __name__ == "__main__":
    unittest.main()
