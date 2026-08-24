# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_efehr_greece_exposure_profile_action as subject


SHA = "a" * 40
OTHER_SHA = "c" * 40


def _request(**overrides):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _payload():
    schema_version = subject.worker.profile.SCHEMA_VERSION
    namespace = next(iter(subject.worker.profile.SHARED_ACCEPTED_NRML_NAMESPACES))
    return {
        "schema_version": schema_version,
        "source_issue": 285,
        "receipt_issue": 285,
        "dataset_id": subject.DATASET_ID,
        "project_id": 269,
        "project_path": "efehr/esrm20",
        "release": "v1.0",
        "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        "consumer_event": "Greece_07-9-1999",
        "repository_path": "Exposure/OQ_Exposure_Input_Greece.xml",
        "receipt_comment_id": 5_388_640_521,
        "receipt_execution_sha": "9bf3fee5d80431dfa873ee5ae03e07891e6f154a",
        "receipt_retrieved_at": "2026-08-23T21:47:08Z",
        "byte_count": 697,
        "sha256": "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556",
        "content_profile": {
            "schema_version": schema_version,
            "parser": "profile_esrm20_runtime_exposure_xml.profile_xml_bytes",
            "profile": {
                "nrml_namespace": namespace,
                "exposure_model": {
                    "id": "greece",
                    "category": None,
                    "taxonomy_source": None,
                    "description": "Synthetic action-contract fixture",
                },
                "asset_references": ["Exposure_Model_Greece.csv"],
                "cost_types": [],
                "area": None,
                "occupancy_periods": [],
                "tag_names": [],
                "exposure_fields": [],
                "structural_cost_type_declared": False,
                "structural_value_inputs": [],
            },
            "source_declarations_profiled": True,
            "raw_xml_returned": False,
            "referenced_dependency_bytes_receipted": False,
            "referenced_dependency_content_profiled": False,
            "crs_semantics_verified": False,
            "taxonomy_semantics_verified": False,
            "replacement_cost_semantics_verified": False,
            "benchmark_agreement_inspected": False,
            "independent_validation_established": False,
            "holdout_status_established": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        },
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _terminal_body(execution_sha: str) -> str:
    result = subject._run_greece_exposure_profile(
        execution_sha=execution_sha,
        acquirer=_payload,
    )
    return subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))


class GreeceExposureProfileActionTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_issue_dataset_action_and_execution_sha(self):
        result = subject.validate_request(
            _request(),
            expected_issue=285,
            execution_sha=SHA,
        )
        self.assertEqual(result["action"], subject.ACTION)
        for bad in (
            _request(issue=662),
            _request(dataset_id="other"),
            _request(action="other"),
            _request(target_sha="b" * 40),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(subject.GreeceExposureProfileActionError):
                    subject.validate_request(
                        bad,
                        expected_issue=285,
                        execution_sha=SHA,
                    )

    def test_duplicate_keys_nonfinite_json_and_unsafe_requester_fail_closed(self):
        duplicate = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + subject.ACTION
            + '","issue":285,"target_sha":"'
            + SHA
            + '","dataset_id":"'
            + subject.DATASET_ID
            + '","requester":"x","requester":"y"}'
        )
        with self.assertRaisesRegex(
            subject.GreeceExposureProfileActionError,
            "duplicate",
        ):
            subject.validate_request(
                duplicate,
                expected_issue=285,
                execution_sha=SHA,
            )

        nonfinite = _request().replace('"requester":"unit-test"', '"requester":NaN')
        with self.assertRaises(subject.GreeceExposureProfileActionError):
            subject.validate_request(
                nonfinite,
                expected_issue=285,
                execution_sha=SHA,
            )

        with self.assertRaisesRegex(
            subject.GreeceExposureProfileActionError,
            "requester",
        ):
            subject.validate_request(
                _request(requester="bad\nactor"),
                expected_issue=285,
                execution_sha=SHA,
            )

    def test_pass_preserves_exact_profile_and_authority_ceilings(self):
        result = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=_payload,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["source_issue"], 285)
        self.assertEqual(result["content_issue"], 662)
        self.assertEqual(
            result["profile"]["content_profile"]["profile"]["asset_references"],
            ["Exposure_Model_Greece.csv"],
        )
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertIs(
            result["profile"]["content_profile"]["raw_xml_returned"],
            False,
        )
        self.assertIs(
            result["profile"]["content_profile"]["referenced_dependency_bytes_receipted"],
            False,
        )

    def test_acquisition_failure_is_bounded(self):
        def fail():
            raise subject.worker.GreeceExposureAcquisitionError("provider unavailable")

        result = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=fail,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["profile"])

    def test_profile_failure_is_distinct_and_bounded(self):
        def fail():
            raise subject.worker.GreeceExposureContentError("exact bytes failed parser")

        result = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=fail,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])

    def test_contract_failure_is_not_sanitized_as_provider_failure(self):
        def fail():
            raise subject.worker.GreeceExposureContractError("trusted contract drift")

        with self.assertRaises(subject.worker.GreeceExposureContractError):
            subject._run_greece_exposure_profile(
                execution_sha=SHA,
                acquirer=fail,
            )

    def test_result_rejects_widened_profile_authority(self):
        payload = _payload()
        payload["content_profile"]["publication_authorized"] = True
        with self.assertRaisesRegex(
            subject.GreeceExposureProfileActionError,
            "reviewed worker contract",
        ):
            subject._validate_profile_payload(payload)

    def test_dedup_trusts_only_actions_bot_and_exact_execution(self):
        body = _terminal_body(SHA)
        comments = [
            {"id": 1, "user": {"login": "pokekarten"}, "body": body},
            {
                "id": 2,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": body,
            },
        ]
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ):
            self.assertTrue(
                subject.has_terminal_greece_exposure_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_dedup_skips_prior_sha_and_still_finds_current_sha(self):
        prior = {
            "id": 1,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": _terminal_body(OTHER_SHA),
        }
        current = {
            "id": 2,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": _terminal_body(SHA),
        }
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=[prior],
        ):
            self.assertFalse(
                subject.has_terminal_greece_exposure_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=[prior, current],
        ):
            self.assertTrue(
                subject.has_terminal_greece_exposure_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_malformed_trusted_terminal_result_fails_closed(self):
        comments = [
            {
                "id": 2,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": subject.RESULT_MARKER + "\n{}",
            }
        ]
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ):
            with self.assertRaises(subject.GreeceExposureProfileActionError):
                subject.has_terminal_greece_exposure_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_incomplete_issue_ledger_fails_closed_before_provider(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("incomplete"),
        ):
            with self.assertRaisesRegex(
                subject.GreeceExposureProfileActionError,
                "ledger is incomplete",
            ):
                subject.has_terminal_greece_exposure_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )


if __name__ == "__main__":
    unittest.main()
