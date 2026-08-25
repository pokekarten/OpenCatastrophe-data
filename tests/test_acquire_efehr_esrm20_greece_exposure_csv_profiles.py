# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_greece_exposure_csv_profiles as action
from scripts import profile_efehr_esrm20_greece_exposure_csvs as profile

SHA = "a" * 40


def request_body(**changes: object) -> str:
    request: dict[str, object] = {
        "schema_version": action.REQUEST_SCHEMA_VERSION,
        "action": action.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": profile.DATASET_ID,
        "requester": "test-greece-three-csv-profile",
    }
    request.update(changes)
    return action.REQUEST_MARKER + "\n" + json.dumps(request, sort_keys=True)


def nested_profile() -> dict[str, object]:
    raw = b"id,taxonomy,value\n1,A,100\n2,B,200\n"
    return profile.generic_csv.profile_verified_csv_bytes(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


def valid_bundle() -> dict[str, object]:
    files = [
        {
            "repository_path": path,
            "byte_count": byte_count,
            "sha256": sha256,
            "profile": nested_profile(),
        }
        for path, byte_count, sha256 in profile.RECEIPTS
    ]
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": profile.SOURCE_ISSUE,
        "parent_consumer_issue": profile.PARENT_CONSUMER_ISSUE,
        "dataset_id": profile.DATASET_ID,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.COMMIT_SHA,
        "consumer_event_id": profile.CONSUMER_EVENT_ID,
        "parent_exposure_path": profile.PARENT_EXPOSURE_PATH,
        "receipt_comment_id": profile.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": profile.RECEIPT_EXECUTION_SHA,
        "files": files,
        "provider_file_content_profiled": True,
        "content_semantics_verified": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "raw_rows_returned": False,
        "exact_field_values_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class GreeceExposureCsvTrustedProfileTests(unittest.TestCase):
    def test_contract_is_exactly_bound_to_trusted_receipts_and_merged_profiler(self) -> None:
        action._require_contract()
        self.assertEqual(profile.SOURCE_ISSUE, 285)
        self.assertEqual(profile.PARENT_CONSUMER_ISSUE, 287)
        self.assertEqual(profile.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(profile.PROJECT_ID, 269)
        self.assertEqual(profile.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(profile.RELEASE_TAG, "v1.0")
        self.assertEqual(
            profile.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(profile.RECEIPT_COMMENT_ID, 5397480571)
        self.assertEqual(
            profile.RECEIPT_EXECUTION_SHA,
            "4b1d3c41a5df739b9686303eb753577ca39ec58e",
        )
        self.assertEqual(profile.RECEIPTS, action._canonical_receipts())

    def test_request_is_closed_to_issue_dataset_action_and_execution_sha(self) -> None:
        parsed = action.validate_request(
            request_body(), expected_issue=285, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)
        mutations = (
            {"issue": 287},
            {"dataset_id": "other.dataset"},
            {"action": "other_action"},
            {"target_sha": "b" * 40},
            {"url": "https://example.invalid"},
            {"repository_path": profile.RECEIPTS[0][0]},
        )
        for change in mutations:
            with self.subTest(change=change), self.assertRaises(
                action.GreeceExposureCsvProfileContractError
            ):
                action.validate_request(
                    request_body(**change), expected_issue=285, execution_sha=SHA
                )

    def test_request_rejects_duplicate_keys_nonfinite_and_trailing_content(self) -> None:
        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","schema_version":"x","action":"'
            + action.ACTION
            + '","issue":285,"target_sha":"'
            + SHA
            + '","dataset_id":"'
            + profile.DATASET_ID
            + '","requester":"x"}'
        )
        with self.assertRaisesRegex(
            action.GreeceExposureCsvProfileContractError, "duplicate JSON key"
        ):
            action.validate_request(duplicate, expected_issue=285, execution_sha=SHA)

        nonfinite = request_body().replace('"issue": 285', '"issue": NaN')
        with self.assertRaises(action.GreeceExposureCsvProfileContractError):
            action.validate_request(nonfinite, expected_issue=285, execution_sha=SHA)

        with self.assertRaises(action.GreeceExposureCsvProfileContractError):
            action.validate_request(
                request_body() + " trailing", expected_issue=285, execution_sha=SHA
            )

    def test_pass_result_binds_profile_and_keeps_authority_ceiling_false(self) -> None:
        result = action._run(execution_sha=SHA, acquirer=valid_bundle)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["provider_file_bytes_read"], True)
        self.assertIs(result["provider_file_content_profiled"], True)
        self.assertIs(result["byte_identity_verified"], True)
        self.assertEqual(result["profile"]["receipt_comment_id"], 5397480571)
        self.assertEqual(
            [item["repository_path"] for item in result["profile"]["files"]],
            [path for path, _, _ in profile.RECEIPTS],
        )
        for field in (
            "content_semantics_verified",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "vulnerability_imt_selection_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(result[field], False)

    def test_acquisition_failure_is_atomic_and_does_not_claim_reads(self) -> None:
        def blocked() -> dict[str, object]:
            raise action.GreeceExposureCsvProfileAcquisitionError("synthetic")

        result = action._run(execution_sha=SHA, acquirer=blocked)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["profile"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["provider_file_content_profiled"], False)
        self.assertIs(result["byte_identity_verified"], False)

    def test_profile_failure_is_atomic_after_complete_transient_reads(self) -> None:
        def blocked() -> dict[str, object]:
            raise action.GreeceExposureCsvProfileContentError("synthetic")

        result = action._run(execution_sha=SHA, acquirer=blocked)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])
        self.assertIs(result["provider_file_bytes_read"], True)
        self.assertIs(result["provider_file_content_profiled"], False)
        self.assertIs(result["byte_identity_verified"], False)

    def test_result_rejects_identity_authority_and_nested_profile_mutations(self) -> None:
        result = action._run(execution_sha=SHA, acquirer=valid_bundle)
        mutations: list[tuple[str, object]] = [
            ("publication_authorized", True),
            ("vulnerability_imt_selection_verified", True),
            ("execution_sha", "b" * 40),
        ]
        for field, replacement in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(result)
                mutated[field] = replacement
                with self.assertRaises(action.GreeceExposureCsvProfileContractError):
                    action._validate_terminal_result(mutated, execution_sha=SHA)

        mutated = copy.deepcopy(result)
        mutated["profile"]["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            action.GreeceExposureCsvProfileContractError, "file profile drifted at sha256"
        ):
            action._validate_terminal_result(mutated, execution_sha=SHA)

        mutated = copy.deepcopy(result)
        mutated["profile"]["files"][0]["profile"]["raw_rows_returned"] = True
        with self.assertRaisesRegex(
            action.GreeceExposureCsvProfileContractError, "leaked rows"
        ):
            action._validate_terminal_result(mutated, execution_sha=SHA)

        mutated = copy.deepcopy(result)
        mutated["profile"]["files"][0]["profile"]["header"] = ["id", "id"]
        with self.assertRaisesRegex(
            action.GreeceExposureCsvProfileContractError, "header invalid"
        ):
            action._validate_terminal_result(mutated, execution_sha=SHA)

    def test_trusted_terminal_dedup_accepts_only_valid_bot_result_on_same_sha(self) -> None:
        result = action._run(execution_sha=SHA, acquirer=valid_bundle)
        body = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        comments = [
            {"id": 1, "user": {"login": "pokekarten"}, "body": body},
            {"id": 2, "user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body},
        ]
        with mock.patch.object(action, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha="b" * 40,
                )
            )

    def test_malformed_trusted_terminal_fails_closed(self) -> None:
        comments = [
            {
                "id": 2,
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": action.RESULT_MARKER + "\n{}",
            }
        ]
        with mock.patch.object(action, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(action.GreeceExposureCsvProfileContractError):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )

    def test_production_identity_rejects_profiler_monkeypatch(self) -> None:
        with mock.patch.object(profile, "profile_verified_bundle", lambda value: value):
            with self.assertRaisesRegex(
                action.GreeceExposureCsvProfileContractError,
                "production merged profiler drifted",
            ):
                action._require_production_identity()


if __name__ == "__main__":
    unittest.main()
