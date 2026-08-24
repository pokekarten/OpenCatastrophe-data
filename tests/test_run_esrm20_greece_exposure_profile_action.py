# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest

from scripts import run_esrm20_greece_exposure_profile_action as subject


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
    content = {
        "schema_version": "oc-esrm20-greece-exposure-content-profile-v0",
        "parser": "profile_esrm20_runtime_exposure_xml.profile_xml_bytes",
        "profile": {
            "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
            "exposure_model": {
                "id": "greece",
                "category": "buildings",
                "taxonomy_source": "GEM",
                "description": "Greece exposure",
            },
            "asset_references": ["Exposure_Model_Greece.csv"],
            "cost_types": [
                {"name": "structural", "type": "aggregated", "unit": "EUR"}
            ],
            "area": {"type": "aggregated", "unit": "SQM"},
            "occupancy_periods": ["day", "night"],
            "tag_names": ["occupancy", "admin"],
            "exposure_fields": [
                {"oq": "taxonomy", "input": "TAXONOMY"},
                {"oq": "value", "type": "structural", "input": "STRUCTURAL"},
            ],
            "structural_cost_type_declared": True,
            "structural_value_inputs": ["STRUCTURAL"],
        },
        "source_declarations_profiled": True,
    }
    for field in (
        "raw_xml_returned",
        "referenced_dependency_bytes_receipted",
        "referenced_dependency_content_profiled",
        "crs_semantics_verified",
        "taxonomy_semantics_verified",
        "replacement_cost_semantics_verified",
        "benchmark_agreement_inspected",
        "independent_validation_established",
        "holdout_status_established",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    ):
        content[field] = False
    return {
        "schema_version": "oc-esrm20-greece-exposure-content-profile-v0",
        "source_issue": subject.SOURCE_ISSUE,
        "receipt_issue": subject.RECEIPT_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "release": subject.RELEASE,
        "commit_sha": subject.COMMIT_SHA,
        "consumer_event": subject.CONSUMER_EVENT,
        "repository_path": subject.REPOSITORY_PATH,
        "receipt_comment_id": subject.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": subject.RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": subject.RECEIPT_RETRIEVED_AT,
        "byte_count": subject.EXPECTED_BYTE_COUNT,
        "sha256": subject.EXPECTED_SHA256,
        "content_profile": content,
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
    def test_request_is_bound_to_issue_dataset_action_and_execution_sha(self):
        result = subject.validate_request(
            _request(),
            expected_issue=285,
            execution_sha=SHA,
        )
        self.assertEqual(result["action"], subject.ACTION)
        for bad in (
            _request(issue=286),
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

        nonfinite = _request().replace(
            '"requester":"unit-test"',
            '"requester":NaN',
        )
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

    def test_pass_preserves_exact_identity_declarations_and_authority_ceilings(self):
        result = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=_payload,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            result["exposure_identity"]["repository_path"],
            "Exposure/OQ_Exposure_Input_Greece.xml",
        )
        self.assertEqual(result["exposure_identity"]["byte_count"], 697)
        self.assertEqual(
            result["profile"]["content_profile"]["profile"]["asset_references"],
            ["Exposure_Model_Greece.csv"],
        )
        for field in (
            "referenced_dependency_bytes_receipted",
            "referenced_dependency_content_profiled",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(result[field], False)

    def test_acquisition_and_profile_failures_are_distinct_and_bounded(self):
        def acquisition_fail():
            raise subject.GreeceExposureAcquisitionError("provider unavailable")

        def profile_fail():
            raise subject.GreeceExposureContentError("exact bytes failed parser")

        acquisition = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=acquisition_fail,
        )
        profile = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=profile_fail,
        )
        self.assertEqual(acquisition["failure_class"], "acquisition_failure")
        self.assertEqual(profile["failure_class"], "profile_failure")
        self.assertIsNone(acquisition["profile"])
        self.assertIsNone(profile["profile"])

    def test_contract_failure_is_not_sanitized_as_provider_failure(self):
        def fail():
            raise subject.GreeceExposureContractError("trusted contract drift")

        with self.assertRaises(subject.GreeceExposureContractError):
            subject._run_greece_exposure_profile(
                execution_sha=SHA,
                acquirer=fail,
            )

    def test_profile_contract_widening_fails_closed(self):
        payload = copy.deepcopy(_payload())
        payload["content_profile"]["model_use_authorized"] = True
        with self.assertRaisesRegex(
            subject.GreeceExposureProfileActionError,
            "reviewed worker contract",
        ):
            subject._validate_profile_payload(payload)

    def test_trusted_terminal_parser_is_exact_sha(self):
        self.assertTrue(
            subject._parse_trusted_terminal_result(
                _terminal_body(SHA),
                execution_sha=SHA,
            )
        )
        self.assertFalse(
            subject._parse_trusted_terminal_result(
                _terminal_body(OTHER_SHA),
                execution_sha=SHA,
            )
        )

    def test_malformed_or_widened_trusted_terminal_fails_closed(self):
        with self.assertRaises(subject.GreeceExposureProfileActionError):
            subject._parse_trusted_terminal_result(
                subject.RESULT_MARKER + "\n{}",
                execution_sha=SHA,
            )

        result = subject._run_greece_exposure_profile(
            execution_sha=SHA,
            acquirer=_payload,
        )
        result["model_use_authorized"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result,
            separators=(",", ":"),
        )
        with self.assertRaises(subject.GreeceExposureProfileActionError):
            subject._parse_trusted_terminal_result(body, execution_sha=SHA)


if __name__ == "__main__":
    unittest.main()
