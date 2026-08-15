# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import acquire_efehr_kosovo_taxonomy as taxonomy
from scripts.agent_action_protocol import ProtocolError
from scripts.prepare_agent_action_result import (
    build_acquisition_result,
    prepare_completed_result,
)
from scripts.validate_agent_action_request import RequestError, validate_request
from scripts.validate_agent_action_result import ResultError, validate_result

SHA = "a" * 40
DATASET = taxonomy.exposure.DATASET_ID
ACTION = "efehr_kosovo_taxonomy_identity"
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": ACTION,
    "issue": 363,
    "target_sha": SHA,
    "dataset_id": DATASET,
    "requester": "slot-eq1-taxonomy-identity",
}


def receipt() -> dict:
    exposure = taxonomy.exposure
    return {
        "schema_version": taxonomy.SCHEMA_VERSION,
        "operation_id": taxonomy.OPERATION_ID,
        "control_issue": taxonomy.CONTROL_ISSUE,
        "worker_identity": taxonomy.WORKER_IDENTITY,
        "retrieved_at": "2026-08-15T12:00:01Z",
        "source_issue": exposure.SOURCE_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "project_id": exposure.PROJECT_ID,
        "project_path": exposure.PROJECT_PATH,
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "receipt_comment_id": exposure.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": exposure.RECEIPT_EXECUTION_SHA,
        "source_byte_count": exposure.EXPECTED_BYTE_COUNT,
        "source_sha256": exposure.EXPECTED_SHA256,
        "taxonomy_field": taxonomy.TAXONOMY_FIELD,
        "taxonomy_count": taxonomy.EXPECTED_DISTINCT_COUNT,
        "taxonomy_artifact_representation": taxonomy.ARTIFACT_REPRESENTATION,
        "taxonomy_artifact_byte_count": taxonomy.EXPECTED_DISTINCT_COUNT * 9,
        "taxonomy_artifact_sha256": taxonomy.EXPECTED_VALUE_SET_SHA256,
        "taxonomy_values_returned": False,
        "normalization_applied": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "derived_artifact_persisted": False,
        "publication_authorized": False,
    }


def result_with(value: dict | None) -> dict:
    return build_acquisition_result(
        REQUEST,
        repository="pokekarten/OpenCatastrophe-data",
        execution_sha=SHA,
        source_comment_id=123,
        run_id=456,
        run_attempt=1,
        started_at="2026-08-15T12:00:00Z",
        finished_at="2026-08-15T12:00:02Z",
        receipt=value,
    )


class KosovoTaxonomyIdentityActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_and_dataset(self) -> None:
        self.assertEqual(validate_request(dict(REQUEST), expected_issue=363), REQUEST)
        for mutation in (
            {"issue": 364},
            {"dataset_id": "other.dataset"},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(RequestError, "restricted"):
                    validate_request(dict(REQUEST, **mutation))

    def test_request_rejects_caller_provider_or_representation_selectors(self) -> None:
        for key, value in (
            ("url", "https://example.invalid"),
            ("repository_path", "other.csv"),
            ("commit_sha", "b" * 40),
            ("representation", "other"),
            ("taxonomy_field", "MACRO_TAXONOMY"),
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(RequestError, "unexpected"):
                    validate_request(dict(REQUEST, **{key: value}))

    def test_semantic_target_must_equal_execution_sha(self) -> None:
        with self.assertRaisesRegex(ProtocolError, "target_sha must equal"):
            build_acquisition_result(
                dict(REQUEST, target_sha="b" * 40),
                repository="pokekarten/OpenCatastrophe-data",
                execution_sha=SHA,
                source_comment_id=123,
                run_id=456,
                run_attempt=1,
                started_at="2026-08-15T12:00:00Z",
                finished_at="2026-08-15T12:00:02Z",
                receipt=receipt(),
            )

    def test_pass_result_is_identity_only(self) -> None:
        result = result_with(receipt())
        self.assertEqual(validate_result(result), result)
        serialized = json.dumps(result, sort_keys=True)
        evidence = result["evidence"]["efehr_kosovo_taxonomy_identity"]
        self.assertNotIn("taxonomies", evidence)
        self.assertNotIn("taxonomy_values", evidence)
        self.assertNotIn("provider_bytes", evidence)
        self.assertNotIn("canonical_bytes", evidence)
        self.assertFalse(evidence["taxonomy_values_returned"])
        self.assertFalse(evidence["external_bytes_persisted"])
        self.assertFalse(evidence["derived_artifact_persisted"])
        self.assertFalse(evidence["publication_authorized"])
        self.assertNotIn("MACRO_TAXONOMY", serialized)

    def test_validator_rejects_identity_and_authority_drift(self) -> None:
        mutations = (
            ("taxonomy_count", taxonomy.EXPECTED_DISTINCT_COUNT + 1),
            ("taxonomy_artifact_representation", "other"),
            ("taxonomy_artifact_sha256", "b" * 64),
            ("source_sha256", "b" * 64),
            ("taxonomy_values_returned", True),
            ("normalization_applied", True),
            ("raw_rows_returned", True),
            ("external_bytes_persisted", True),
            ("derived_artifact_persisted", True),
            ("publication_authorized", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                changed = receipt()
                changed[key] = value
                with self.assertRaises(ResultError):
                    result_with(changed)

    def test_validator_rejects_literal_value_or_other_extra_field(self) -> None:
        for key, value in (
            ("taxonomies", ["secret-source-value"]),
            ("taxonomy_values", ["secret-source-value"]),
            ("provider_bytes", "secret"),
            ("canonical_bytes", "secret"),
        ):
            with self.subTest(key=key):
                changed = receipt()
                changed[key] = value
                with self.assertRaisesRegex(ResultError, "fields mismatch"):
                    result_with(changed)

    def test_validator_rejects_retrieval_outside_action_window(self) -> None:
        changed = receipt()
        changed["retrieved_at"] = "2026-08-15T11:59:59Z"
        with self.assertRaisesRegex(ResultError, "start/finish bounds"):
            result_with(changed)

    def test_worker_failure_persists_only_closed_failure_class(self) -> None:
        def fail() -> dict:
            raise taxonomy.KosovoTaxonomyAcquisitionError("sensitive provider detail")

        result = prepare_completed_result(
            REQUEST,
            [],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=SHA,
            source_comment_id=123,
            run_id=456,
            run_attempt=1,
            started_at="2026-08-15T12:00:00Z",
            kosovo_taxonomy_identity_acquirer=fail,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failed")
        self.assertIsNone(result["evidence"]["efehr_kosovo_taxonomy_identity"])
        self.assertNotIn("sensitive provider detail", json.dumps(result, sort_keys=True))

    def test_dedup_result_prevents_acquirer_execution(self) -> None:
        completed = result_with(receipt())
        comments = [{
            "id": 999,
            "user": {"login": "github-actions[bot]"},
            "body": "<!-- oc-action-result-v1 -->\n" + json.dumps(completed, sort_keys=True, separators=(",", ":")),
        }]
        calls = 0

        def should_not_run() -> dict:
            nonlocal calls
            calls += 1
            return receipt()

        duplicate = prepare_completed_result(
            REQUEST,
            comments,
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=SHA,
            source_comment_id=124,
            run_id=457,
            run_attempt=1,
            started_at="2026-08-15T12:00:00Z",
            kosovo_taxonomy_identity_acquirer=should_not_run,
        )
        self.assertEqual(calls, 0)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 999)


if __name__ == "__main__":
    unittest.main()
