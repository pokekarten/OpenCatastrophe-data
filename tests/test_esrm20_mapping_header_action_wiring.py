# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest

from scripts import acquire_efehr_esrm20_mapping_headers as worker
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment, semantic_request_id
from scripts.prepare_agent_action_result import build_acquisition_result, ledger_issue_for_request, prepare_completed_result
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "c" * 40
ACTION = "esrm20_exposure_vulnerability_mapping_headers"
CONTROL_ISSUE = 410
STARTED = "2026-08-16T12:00:00Z"
FINISHED = "2026-08-16T12:00:02Z"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": CONTROL_ISSUE,
    "target_sha": EXECUTION_SHA,
    "dataset_id": worker._CANONICAL_DATASET_ID,
    "requester": "slot-eq1-mapping-headers",
}
HEADERS = ["synthetic_taxonomy_header", "synthetic_vulnerability_header"]


def header_fingerprint(values: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


DISCLOSURE = {
    "schema_version": worker._CANONICAL_HEADER_SCHEMA_VERSION,
    "decision_issue": worker._CANONICAL_CONTROL_ISSUE,
    "source_issue": worker._CANONICAL_SOURCE_ISSUE,
    "profile_issue": 404,
    "dataset_id": worker._CANONICAL_DATASET_ID,
    "project_id": worker._CANONICAL_PROJECT_ID,
    "project_path": worker._CANONICAL_PROJECT_PATH,
    "commit_sha": worker._CANONICAL_COMMIT_SHA,
    "repository_path": worker._CANONICAL_REPOSITORY_PATH,
    "receipt_comment_id": worker._CANONICAL_RECEIPT_COMMENT_ID,
    "receipt_run_id": worker._CANONICAL_RECEIPT_RUN_ID,
    "receipt_execution_sha": worker._CANONICAL_RECEIPT_EXECUTION_SHA,
    "byte_count": worker._CANONICAL_EXPECTED_BYTE_COUNT,
    "sha256": worker._CANONICAL_EXPECTED_SHA256,
    "column_count": len(HEADERS),
    "ordered_header_sha256": header_fingerprint(HEADERS),
    "headers": HEADERS,
    "disclosure_scope": worker._CANONICAL_DISCLOSURE_SCOPE,
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
RECEIPT = {
    "schema_version": worker._CANONICAL_SCHEMA_VERSION,
    "operation_id": worker._CANONICAL_OPERATION_ID,
    "control_issue": worker._CANONICAL_CONTROL_ISSUE,
    "source_issue": worker._CANONICAL_SOURCE_ISSUE,
    "dataset_id": worker._CANONICAL_DATASET_ID,
    "provider_host": worker._CANONICAL_PROVIDER_HOST,
    "project_id": worker._CANONICAL_PROJECT_ID,
    "project_path": worker._CANONICAL_PROJECT_PATH,
    "commit_sha": worker._CANONICAL_COMMIT_SHA,
    "repository_path": worker._CANONICAL_REPOSITORY_PATH,
    "receipt_comment_id": worker._CANONICAL_RECEIPT_COMMENT_ID,
    "receipt_run_id": worker._CANONICAL_RECEIPT_RUN_ID,
    "receipt_execution_sha": worker._CANONICAL_RECEIPT_EXECUTION_SHA,
    "header_source_commit": worker._CANONICAL_HEADER_SOURCE_COMMIT,
    "header_path": worker._CANONICAL_HEADER_PATH,
    "header_function": worker._CANONICAL_HEADER_FUNCTION,
    "header_git_blob_sha1": worker._CANONICAL_HEADER_GIT_BLOB_SHA1,
    "retrieved_at": "2026-08-16T12:00:01Z",
    "disclosure": DISCLOSURE,
    "raw_bytes_returned": False,
    "external_bytes_persisted": False,
    "derived_bytes_persisted": False,
    "publication_authorized": False,
    "mapping_interpretation_authorized": False,
    "taxonomy_join_authorized": False,
    "vulnerability_selection_authorized": False,
    "model_use_authorized": False,
}


def acquisition_result(receipt=RECEIPT):
    return build_acquisition_result(
        REQUEST,
        repository=REPOSITORY,
        execution_sha=EXECUTION_SHA,
        source_comment_id=100,
        run_id=200,
        run_attempt=1,
        started_at=STARTED,
        finished_at=FINISHED,
        receipt=receipt,
    )


class Esrm20MappingHeaderActionWiringTests(unittest.TestCase):
    def test_request_is_closed_to_issue_410_and_frozen_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=CONTROL_ISSUE), REQUEST)
        for change in ({"issue": 340}, {"dataset_id": "efehr.other"}):
            with self.subTest(change=change), self.assertRaises(RequestError):
                validate_request(dict(REQUEST, **change))

    def test_request_rejects_every_caller_selected_target_or_disclosure_selector(self) -> None:
        for key, value in (
            ("url", "https://example.invalid"),
            ("repository_path", "other.csv"),
            ("project_id", 1),
            ("commit_sha", "d" * 40),
            ("ref", "main"),
            ("parser", "csv"),
            ("helper", "other"),
            ("disclosure_scope", "all_rows"),
            ("headers", ["caller_selected"]),
            ("taxonomy", "caller_selected"),
            ("vulnerability_file", "caller_selected.xml"),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(RequestError, "unexpected"):
                validate_request(dict(REQUEST, **{key: value}))

    def test_network_identity_and_issue_local_ledger_are_bound_before_dispatch(self) -> None:
        semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal"):
            build_acquisition_result(
                REQUEST,
                repository=REPOSITORY,
                execution_sha="d" * 40,
                source_comment_id=99,
                run_id=199,
                run_attempt=1,
                started_at=STARTED,
                finished_at=FINISHED,
                receipt=RECEIPT,
            )
        self.assertEqual(ledger_issue_for_request(REQUEST), CONTROL_ISSUE)

    def test_pass_result_binds_exact_worker_and_bounded_disclosure(self) -> None:
        result = acquisition_result()
        self.assertEqual(validate_result(result), result)
        self.assertEqual(result["source_issue"], CONTROL_ISSUE)
        receipt = result["evidence"][ACTION]
        self.assertEqual(receipt["source_issue"], 283)
        self.assertEqual(receipt["repository_path"], worker._CANONICAL_REPOSITORY_PATH)
        self.assertEqual(receipt["disclosure"]["headers"], HEADERS)
        self.assertFalse(receipt["disclosure"]["taxonomy_join_authorized"])
        self.assertFalse(receipt["vulnerability_selection_authorized"])
        self.assertFalse(receipt["model_use_authorized"])

    def test_result_rejects_identity_drift_widening_extra_fields_and_bool_count(self) -> None:
        outer_mutations = (
            ("operation_id", "other"),
            ("source_issue", 410),
            ("project_id", 1),
            ("commit_sha", "d" * 40),
            ("repository_path", "other.csv"),
            ("header_function", "other"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("mapping_interpretation_authorized", True),
            ("taxonomy_join_authorized", True),
            ("vulnerability_selection_authorized", True),
            ("model_use_authorized", True),
        )
        for key, value in outer_mutations:
            with self.subTest(outer=key), self.assertRaises(ResultError):
                acquisition_result(dict(RECEIPT, **{key: value}))
        with self.assertRaisesRegex(ResultError, "fields drifted"):
            acquisition_result(dict(RECEIPT, provider_body="secret bytes"))

        nested_mutations = (
            ("column_count", True),
            ("ordered_header_sha256", "a" * 64),
            ("headers", [HEADERS[1], HEADERS[0]]),
            ("cell_values_returned", True),
            ("normalization_applied", True),
            ("mapping_interpretation_authorized", True),
            ("taxonomy_join_authorized", True),
            ("vulnerability_selection_authorized", True),
            ("publication_authorized", True),
            ("model_use_authorized", True),
        )
        for key, value in nested_mutations:
            mutated = dict(RECEIPT)
            mutated["disclosure"] = dict(DISCLOSURE, **{key: value})
            with self.subTest(disclosure=key), self.assertRaises(ResultError):
                acquisition_result(mutated)
        mutated = dict(RECEIPT)
        mutated["disclosure"] = dict(DISCLOSURE, provider_row="secret")
        with self.assertRaisesRegex(ResultError, "fields drifted"):
            acquisition_result(mutated)

    def test_dispatcher_calls_only_injected_zero_argument_worker_and_dedup_precedes_it(self) -> None:
        calls = 0

        def worker_once():
            nonlocal calls
            calls += 1
            return RECEIPT

        completed = prepare_completed_result(
            REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            started_at=STARTED,
            esrm20_mapping_headers_acquirer=worker_once,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(completed["status"], "pass")

        prior = acquisition_result()
        calls = 0

        def forbidden_worker():
            nonlocal calls
            calls += 1
            self.fail("deduplicated action must not call provider worker")

        duplicate = prepare_completed_result(
            REQUEST,
            [{"id": 999, "body": canonical_result_comment(prior), "user": {"login": "github-actions[bot]"}}],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            started_at=STARTED,
            esrm20_mapping_headers_acquirer=forbidden_worker,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)

    def test_blocked_failure_is_value_free(self) -> None:
        def blocked_worker():
            raise worker.Esrm20MappingHeaderAcquisitionError("synthetic provider body and URL")

        stderr = StringIO()
        with redirect_stderr(stderr):
            blocked = prepare_completed_result(
                REQUEST,
                [],
                repository=REPOSITORY,
                execution_sha=EXECUTION_SHA,
                source_comment_id=103,
                run_id=203,
                run_attempt=1,
                started_at=STARTED,
                esrm20_mapping_headers_acquirer=blocked_worker,
            )
        self.assertIn("mapping header acquisition failed closed", stderr.getvalue())
        self.assertNotIn("synthetic provider", stderr.getvalue())
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "acquisition_failed")
        self.assertIsNone(blocked["evidence"][ACTION])
        self.assertNotIn("synthetic provider", json.dumps(blocked, sort_keys=True))

    def test_portable_schemas_have_isolated_mapping_header_branches(self) -> None:
        root = Path(__file__).resolve().parents[1]
        request_schema = json.loads((root / "schemas/agent-action-request-v1.schema.json").read_text())
        result_schema = json.loads((root / "schemas/agent-action-result-v1.schema.json").read_text())
        self.assertIn(ACTION, request_schema["properties"]["action"]["enum"])
        self.assertIn(ACTION, result_schema["properties"]["action"]["enum"])
        self.assertIn("esrm20ExposureVulnerabilityMappingHeaders", result_schema["$defs"])
        serialized = json.dumps(result_schema, sort_keys=True)
        self.assertIn(ACTION, serialized)
        self.assertIn(worker._CANONICAL_REPOSITORY_PATH, serialized)

        matches = []
        for branch in result_schema["allOf"]:
            condition = branch.get("if", {})
            properties = condition.get("properties", {})
            if (
                properties.get("phase") == {"const": "acquisition_receipt"}
                and properties.get("action") == {"const": ACTION}
                and "status" not in properties
            ):
                matches.append(branch)
        self.assertEqual(len(matches), 1)
        binding = matches[0]["then"]["properties"]
        self.assertEqual(binding["source_issue"], {"const": CONTROL_ISSUE})
        self.assertEqual(binding["evidence"], {"required": [ACTION]})
        self.assertNotIn(
            "esrm20_exposure_vulnerability_mapping_receipt",
            json.dumps(matches[0], sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
