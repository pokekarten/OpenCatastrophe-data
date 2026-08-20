# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_runtime_exposure_xml_profile_action as subject

SHA = "a" * 40


def request_body(**updates):
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": 282,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "receipt_sha256": subject.EXPECTED_SHA256,
        "requester": "CHAT-TEST",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, separators=(",", ":"))


def evidence():
    return {
        "receipt": {"retrieved_at": "2026-08-19T22:00:00Z", "byte_count": 664, "sha256": subject.EXPECTED_SHA256, "content_type": "text/plain; charset=utf-8", "etag": None},
        "profile": {
            "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
            "exposure_model": {"id": "k", "category": "buildings", "taxonomy_source": "GEM", "description": "x"},
            "asset_references": ["Exposure_Kosovo.csv"], "cost_types": [], "area": None,
            "occupancy_periods": [], "tag_names": [], "exposure_fields": [],
            "structural_cost_type_declared": False, "structural_value_inputs": [],
        },
    }


class ActionTests(unittest.TestCase):
    def test_request_is_exact_head_and_receipt_bound(self):
        self.assertEqual(subject.validate_request(request_body(), expected_issue=282, execution_sha=SHA)["requester"], "CHAT-TEST")
        for updates in ({"target_sha": "b" * 40}, {"receipt_sha256": "0" * 64}, {"issue": 999}):
            with self.assertRaises(subject.RuntimeExposureXmlProfileActionError):
                subject.validate_request(request_body(**updates), expected_issue=282, execution_sha=SHA)

    def test_pass_preserves_authority_ceilings(self):
        with mock.patch.object(subject, "profile_runtime_exposure_xml", return_value=evidence()):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_code"])
        self.assertTrue(result["xml_content_interpreted"])
        self.assertFalse(result["exact_kosovo_exposure_selected"])
        self.assertFalse(result["value_structural_wiring_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_failures_are_bounded(self):
        failures = [
            (subject.ByteIdentityMismatch("x"), "byte_identity_mismatch", None),
            (
                subject.XmlSemanticProfileError("runtime exposure NRML root namespace drifted"),
                "xml_profile_failure",
                "nrml_root_namespace_drifted",
            ),
            (subject.EfehrAcquisitionError("x"), "acquisition_failure", None),
            (subject.RuntimeExposureXmlProfileError("x"), "profile_failure", None),
        ]
        for exc, failure_class, failure_code in failures:
            with self.subTest(failure_class=failure_class), mock.patch.object(subject, "profile_runtime_exposure_xml", side_effect=exc):
                result = subject.run_profile(execution_sha=SHA)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["failure_class"], failure_class)
                self.assertEqual(result["failure_code"], failure_code)
                self.assertFalse(result["xml_content_interpreted"])

    def test_root_first_divergence_codes_are_closed_and_static(self):
        cases = [
            ("runtime exposure NRML root local name drifted", "nrml_root_local_name_drifted"),
            ("runtime exposure NRML root namespace drifted", "nrml_root_namespace_drifted"),
            ("runtime exposure NRML root attributes present", "nrml_root_attributes_present"),
        ]
        for message, code in cases:
            with self.subTest(code=code), mock.patch.object(
                subject,
                "profile_runtime_exposure_xml",
                side_effect=subject.XmlSemanticProfileError(message),
            ):
                result = subject.run_profile(execution_sha=SHA)
            self.assertEqual(result["failure_class"], "xml_profile_failure")
            self.assertEqual(result["failure_code"], code)
            self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_unknown_xml_error_cannot_leak_exception_text(self):
        secret = "provider-value-that-must-never-be-published"
        with mock.patch.object(
            subject,
            "profile_runtime_exposure_xml",
            side_effect=subject.XmlSemanticProfileError(secret),
        ):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["failure_class"], "xml_profile_failure")
        self.assertEqual(result["failure_code"], "unclassified_xml_profile_failure")
        self.assertNotIn(secret, json.dumps(result, sort_keys=True))

    def test_terminal_rejects_arbitrary_xml_failure_code(self):
        result = subject._base_result(SHA)
        result["failure_class"] = "xml_profile_failure"
        result["failure_code"] = "provider-derived-secret"
        with self.assertRaisesRegex(subject.RuntimeExposureXmlProfileActionError, "invalid XML failure code"):
            subject._validate_terminal_result(result)

    def test_result_v3_rejects_retired_v2_root_code(self):
        result = subject._base_result(SHA)
        result["failure_class"] = "xml_profile_failure"
        result["failure_code"] = "nrml_root_drifted"
        with self.assertRaisesRegex(subject.RuntimeExposureXmlProfileActionError, "invalid XML failure code"):
            subject._validate_terminal_result(result)

    def test_non_xml_failure_rejects_diagnostic_code(self):
        result = subject._base_result(SHA)
        result["failure_class"] = "acquisition_failure"
        result["failure_code"] = "nrml_root_namespace_drifted"
        with self.assertRaisesRegex(subject.RuntimeExposureXmlProfileActionError, "non-XML failure"):
            subject._validate_terminal_result(result)

    def test_legacy_result_v1_and_v2_terminals_are_ignored_by_v3_dedup(self):
        for version in (1, 2):
            with self.subTest(version=version):
                legacy = f'<!-- oc-eq1-esrm20-runtime-exposure-xml-profile-result-v{version} -->\n{{"legacy":true}}'
                self.assertIsNone(subject.parse_terminal_result(legacy))
        self.assertTrue(subject.RESULT_MARKER.endswith("result-v3 -->"))
        self.assertTrue(subject.RESULT_SCHEMA_VERSION.endswith("result-v3"))

    def test_duplicate_json_keys_fail_closed(self):
        body = subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaisesRegex(subject.RuntimeExposureXmlProfileActionError, "duplicate JSON key"):
            subject.validate_request(body, expected_issue=282, execution_sha=SHA)


if __name__ == "__main__":
    unittest.main()
