# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import acquire_efehr_kosovo_taxonomy as worker
from scripts import extract_efehr_kosovo_taxonomy as taxonomy
from scripts import profile_efehr_kosovo_exposure as exposure
from scripts import validate_eq1_kosovo_taxonomy_identity as bridge
from scripts.prepare_agent_action_result import build_acquisition_result


SHA = "a" * 40
REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_kosovo_taxonomy_identity",
    "issue": 363,
    "target_sha": SHA,
    "dataset_id": exposure.DATASET_ID,
    "requester": "eq1-taxonomy-identity-bridge-test",
}


def valid_identity() -> dict[str, object]:
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "worker_identity": worker.WORKER_IDENTITY,
        "retrieved_at": "2026-08-15T12:00:00Z",
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
        "taxonomy_artifact_representation": worker.ARTIFACT_REPRESENTATION,
        "taxonomy_artifact_byte_count": 4096,
        "taxonomy_artifact_sha256": taxonomy.EXPECTED_VALUE_SET_SHA256,
        "taxonomy_values_returned": False,
        "normalization_applied": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "derived_artifact_persisted": False,
        "publication_authorized": False,
    }


def valid_action_result() -> dict[str, object]:
    return build_acquisition_result(
        REQUEST,
        repository="pokekarten/OpenCatastrophe-data",
        execution_sha=SHA,
        source_comment_id=123,
        run_id=456,
        run_attempt=1,
        started_at="2026-08-15T11:59:59Z",
        finished_at="2026-08-15T12:00:01Z",
        receipt=valid_identity(),
    )


def _canonical_passthrough(value: object) -> object:
    """Represent a successful upstream canonical validation in bridge-unit tests."""

    return value


class Eq1KosovoTaxonomyIdentityTests(unittest.TestCase):
    def test_valid_durable_result_reduces_to_path_free_bridge_projection(self) -> None:
        payload = valid_action_result()
        result = bridge.validate_eq1_kosovo_taxonomy_identity(payload)

        self.assertEqual(result["schema_version"], "eq1-kosovo-taxonomy-identity-bridge-v1")
        self.assertEqual(result["source_action"], "efehr_kosovo_taxonomy_identity")
        self.assertEqual(result["source_issue"], 363)
        self.assertEqual(result["source_semantic_request_id"], payload["semantic_request_id"])
        self.assertEqual(result["source_execution_sha"], SHA)
        self.assertEqual(result["taxonomy_count"], 86)
        self.assertEqual(result["taxonomy_artifact_sha256"], taxonomy.EXPECTED_VALUE_SET_SHA256)
        self.assertEqual(result["ledger_authorship_verification"], "external_required")
        self.assertNotIn("repository_path", result)
        self.assertNotIn("project_path", result)
        self.assertNotIn("retrieved_at", result)
        self.assertNotIn("taxonomy_values", result)

    def test_naked_worker_receipt_is_not_bridge_authority(self) -> None:
        with self.assertRaisesRegex(
            bridge.Eq1TaxonomyIdentityError,
            "failed canonical validation",
        ):
            bridge.validate_eq1_kosovo_taxonomy_identity(valid_identity())

    def test_canonical_validation_failure_always_blocks_reduction(self) -> None:
        payload = valid_action_result()
        with patch.object(
            bridge.action_result,
            "validate_result",
            side_effect=bridge.action_result.ResultError("forged durable result"),
        ) as canonical:
            with self.assertRaisesRegex(
                bridge.Eq1TaxonomyIdentityError,
                "failed canonical validation",
            ):
                bridge.validate_eq1_kosovo_taxonomy_identity(payload)
        canonical.assert_called_once_with(payload)

    def test_durable_envelope_authority_drift_fails_closed(self) -> None:
        mutations = (
            ("repository", "someone/other"),
            ("action", "efehr_kosovo_exposure_profile"),
            ("source_issue", 364),
            ("dataset_id", "other.dataset"),
            ("phase", "request_validation"),
            ("status", "blocked"),
            ("external_bytes_persisted", True),
            ("duplicate_result_comment_id", 999),
            ("failure_class", "acquisition_failed"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                payload = valid_action_result()
                payload[field] = value
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "frozen public authority",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_target_and_execution_sha_must_match(self) -> None:
        payload = valid_action_result()
        payload["target_sha"] = "c" * 40
        with patch.object(
            bridge.action_result,
            "validate_result",
            side_effect=_canonical_passthrough,
        ):
            with self.assertRaisesRegex(
                bridge.Eq1TaxonomyIdentityError,
                "target_sha must equal",
            ):
                bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_complete_nonreused_ledger_evidence_is_required(self) -> None:
        for field, value in (
            ("request_validated", False),
            ("ledger_scan_complete", False),
            ("prior_result_reused", True),
        ):
            with self.subTest(field=field):
                payload = valid_action_result()
                payload["evidence"][field] = value  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "frozen public authority",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

        payload = valid_action_result()
        payload["evidence"]["unexpected"] = False  # type: ignore[index]
        with patch.object(
            bridge.action_result,
            "validate_result",
            side_effect=_canonical_passthrough,
        ):
            with self.assertRaisesRegex(
                bridge.Eq1TaxonomyIdentityError,
                "evidence fields drifted",
            ):
                bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_unknown_or_literal_value_receipt_fields_fail_closed(self) -> None:
        for field, value in (
            ("taxonomies", ["invented"]),
            ("taxonomy_values", ["invented"]),
            ("provider_bytes", "abc"),
            ("raw_rows", []),
        ):
            with self.subTest(field=field):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt[field] = value  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "receipt fields drifted",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_source_and_taxonomy_authority_drift_fail_closed(self) -> None:
        mutations = {
            "commit_sha": "0" * 40,
            "source_sha256": "0" * 64,
            "taxonomy_field": "MACRO_TAXONOMY",
            "taxonomy_count": 85,
            "taxonomy_artifact_representation": "other",
            "taxonomy_artifact_sha256": "0" * 64,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt[field] = value  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "frozen public authority",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_bool_int_type_confusion_fails_closed(self) -> None:
        for field in ("control_issue", "project_id", "source_byte_count", "taxonomy_count"):
            with self.subTest(field=field):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt[field] = True  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "frozen public authority",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

        payload = valid_action_result()
        receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
        receipt["taxonomy_artifact_byte_count"] = True  # type: ignore[index]
        with patch.object(
            bridge.action_result,
            "validate_result",
            side_effect=_canonical_passthrough,
        ):
            with self.assertRaisesRegex(
                bridge.Eq1TaxonomyIdentityError,
                "bounded canonical range",
            ):
                bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_every_authority_ceiling_must_remain_exact_false(self) -> None:
        for field in (
            "taxonomy_values_returned",
            "normalization_applied",
            "raw_rows_returned",
            "external_bytes_persisted",
            "derived_artifact_persisted",
            "publication_authorized",
        ):
            with self.subTest(field=field):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt[field] = True  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "authority ceiling",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_timestamp_must_match_worker_second_precision(self) -> None:
        for value in (
            "2026-08-15T12:00:00.1Z",
            "2026-08-15T12:00:00.000001Z",
            "2026-08-15T12:00:00+00:00",
            "2026-08-15 12:00:00Z",
            "2026-13-15T12:00:00Z",
            True,
        ):
            with self.subTest(value=value):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt["retrieved_at"] = value  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "retrieved_at",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)

    def test_artifact_byte_count_is_bounded_and_non_boolean(self) -> None:
        minimum = taxonomy.EXPECTED_DISTINCT_COUNT * 9
        for value in (minimum - 1, exposure.EXPECTED_BYTE_COUNT + 1, 1.5, True):
            with self.subTest(value=value):
                payload = valid_action_result()
                receipt = payload["evidence"]["efehr_kosovo_taxonomy_identity"]  # type: ignore[index]
                receipt["taxonomy_artifact_byte_count"] = value  # type: ignore[index]
                with patch.object(
                    bridge.action_result,
                    "validate_result",
                    side_effect=_canonical_passthrough,
                ):
                    with self.assertRaisesRegex(
                        bridge.Eq1TaxonomyIdentityError,
                        "bounded canonical range",
                    ):
                        bridge.validate_eq1_kosovo_taxonomy_identity(payload)


if __name__ == "__main__":
    unittest.main()
