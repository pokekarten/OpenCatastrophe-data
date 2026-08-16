# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from scripts import acquire_efehr_esrm20_mapping_headers as worker
from scripts import agent_action_protocol as protocol
from scripts import prepare_agent_action_result as prepare
from scripts import profile_efehr_esrm20_mapping_structure as structure
from scripts import validate_agent_action_request as request_validator
from scripts import validate_agent_action_result as result_validator
from scripts import validate_agent_action_result_mapping_headers as mapping_headers_validator

ACTION = "esrm20_exposure_vulnerability_mapping_headers"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": 410,
    "target_sha": "a" * 40,
    "dataset_id": "efehr.esrm20.risk-inputs.v1.0",
    "requester": "issue410-builder",
}


def receipt() -> dict[str, object]:
    headers = ["EXPOSURE", "VULNERABILITY"]
    fingerprint = mapping_headers_validator._length_prefixed_sha256(headers)
    disclosure = {
        "schema_version": "oc-esrm20-mapping-header-disclosure-v1",
        "decision_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "profile_issue": 404,
        "dataset_id": worker.DATASET_ID,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "receipt_comment_id": worker.RECEIPT_COMMENT_ID,
        "receipt_run_id": worker.RECEIPT_RUN_ID,
        "receipt_execution_sha": worker.RECEIPT_EXECUTION_SHA,
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "column_count": len(headers),
        "ordered_header_sha256": fingerprint,
        "headers": headers,
        "disclosure_scope": "exact_header_strings_only",
        "header_strings_returned": True,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "receipt_comment_id": worker.RECEIPT_COMMENT_ID,
        "receipt_run_id": worker.RECEIPT_RUN_ID,
        "receipt_execution_sha": worker.RECEIPT_EXECUTION_SHA,
        "header_source_commit": worker.HEADER_SOURCE_COMMIT,
        "header_path": worker.HEADER_PATH,
        "header_function": worker.HEADER_FUNCTION,
        "header_git_blob_sha1": worker.HEADER_GIT_BLOB_SHA1,
        "retrieved_at": "2026-08-16T08:00:01Z",
        "disclosure": disclosure,
        "raw_bytes_returned": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }


def bind_headers(disclosure: dict[str, object], headers: list[str]) -> None:
    disclosure["headers"] = headers
    disclosure["column_count"] = len(headers)
    disclosure["ordered_header_sha256"] = mapping_headers_validator._length_prefixed_sha256(headers)


class Esrm20MappingHeadersActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_no_selectors(self) -> None:
        self.assertEqual(request_validator.validate_request(dict(REQUEST)), REQUEST)
        self.assertIn(ACTION, protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(ACTION, prepare.NETWORK_ACTIONS)
        for field, value in (("issue", 411), ("dataset_id", "other.dataset")):
            with self.subTest(field=field), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(dict(REQUEST, **{field: value}))
        for selector in (
            "provider", "project_id", "commit_sha", "repository_path", "headers",
            "parser", "disclosure_scope", "taxonomy", "vulnerability",
        ):
            with self.subTest(selector=selector), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(dict(REQUEST, **{selector: "attacker"}))

    def test_receipt_contract_is_exact_and_rebinds_ordered_headers(self) -> None:
        base = receipt()
        self.assertEqual(result_validator.validate_esrm20_mapping_headers(copy.deepcopy(base)), base)
        mutations: list[dict[str, object]] = []
        widened = copy.deepcopy(base); widened["taxonomy_join_authorized"] = True; mutations.append(widened)
        bool_count = copy.deepcopy(base); bool_count["disclosure"]["column_count"] = True; mutations.append(bool_count)
        duplicate = copy.deepcopy(base); bind_headers(duplicate["disclosure"], ["X", "X"]); mutations.append(duplicate)
        changed = copy.deepcopy(base); changed["disclosure"]["headers"] = ["EXPOSURE", "OTHER"]; mutations.append(changed)
        extra = copy.deepcopy(base); extra["disclosure"]["mapping_rows"] = []; mutations.append(extra)
        below_min = copy.deepcopy(base); bind_headers(below_min["disclosure"], ["ONLY_ONE"]); mutations.append(below_min)
        above_max = copy.deepcopy(base); bind_headers(above_max["disclosure"], [f"H{i}" for i in range(structure.MAX_COLUMNS + 1)]); mutations.append(above_max)
        oversized_field = copy.deepcopy(base); bind_headers(oversized_field["disclosure"], ["A" * (structure.MAX_HEADER_FIELD_BYTES + 1), "B"]); mutations.append(oversized_field)
        multibyte_overflow = copy.deepcopy(base); bind_headers(multibyte_overflow["disclosure"], ["é" * (structure.MAX_HEADER_FIELD_BYTES // 2 + 1), "B"]); mutations.append(multibyte_overflow)
        for mutated in mutations:
            with self.subTest(mutated=mutated), self.assertRaises(result_validator.ResultError):
                result_validator.validate_esrm20_mapping_headers(mutated)

    def test_dispatcher_calls_only_injected_zero_argument_worker_after_dedup(self) -> None:
        calls: list[str] = []
        result = prepare.prepare_completed_result(
            dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=1, run_id=2, run_attempt=1, started_at="2026-08-16T08:00:00Z",
            esrm20_mapping_headers_acquirer=lambda: (calls.append("called") or receipt()),
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["evidence"][ACTION]["disclosure"]["headers"], ["EXPOSURE", "VULNERABILITY"])

        prior = [{
            "id": 9,
            "body": protocol.canonical_result_comment(result),
            "user": {"login": "github-actions[bot]"},
        }]
        duplicate = prepare.prepare_completed_result(
            dict(REQUEST), prior, repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
            source_comment_id=3, run_id=4, run_attempt=1, started_at="2026-08-16T08:00:00Z",
            esrm20_mapping_headers_acquirer=lambda: self.fail("worker ran on duplicate"),
        )
        self.assertEqual(duplicate["status"], "duplicate")

    def test_failure_is_sanitized_and_target_mismatch_precedes_worker(self) -> None:
        def failed():
            raise worker.Esrm20MappingHeaderAcquisitionError("PRIVATE_PROVIDER_URL_AND_BODY")

        stream = io.StringIO()
        with redirect_stderr(stream):
            blocked = prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="a" * 40,
                source_comment_id=5, run_id=6, run_attempt=1, started_at="2026-08-16T08:00:00Z",
                esrm20_mapping_headers_acquirer=failed,
            )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertNotIn("PRIVATE_PROVIDER", stream.getvalue())

        with self.assertRaises(prepare.ProtocolError):
            prepare.prepare_completed_result(
                dict(REQUEST), [], repository="pokekarten/OpenCatastrophe-data", execution_sha="b" * 40,
                source_comment_id=7, run_id=8, run_attempt=1, started_at="2026-08-16T08:00:00Z",
                esrm20_mapping_headers_acquirer=lambda: self.fail("worker must not run"),
            )

    def test_portable_request_schema_is_closed(self) -> None:
        schema = json.loads(Path("schemas/agent-action-request-v1.schema.json").read_text(encoding="utf-8"))
        self.assertIn(ACTION, schema["properties"]["action"]["enum"])
        branch = next(
            item for item in schema["allOf"]
            if item.get("if", {}).get("properties", {}).get("action", {}).get("const") == ACTION
        )
        properties = branch["then"]["properties"]
        self.assertEqual(properties["issue"]["const"], 410)
        self.assertEqual(properties["dataset_id"]["const"], "efehr.esrm20.risk-inputs.v1.0")


if __name__ == "__main__":
    unittest.main()
