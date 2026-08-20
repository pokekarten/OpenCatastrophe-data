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
        self.assertTrue(result["xml_content_interpreted"])
        self.assertFalse(result["exact_kosovo_exposure_selected"])
        self.assertFalse(result["value_structural_wiring_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_failures_are_bounded(self):
        failures = [
            (subject.ByteIdentityMismatch("x"), "byte_identity_mismatch"),
            (subject.XmlSemanticProfileError("x"), "xml_profile_failure"),
            (subject.EfehrAcquisitionError("x"), "acquisition_failure"),
        ]
        for exc, failure_class in failures:
            with self.subTest(failure_class=failure_class), mock.patch.object(subject, "profile_runtime_exposure_xml", side_effect=exc):
                result = subject.run_profile(execution_sha=SHA)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["failure_class"], failure_class)
                self.assertFalse(result["xml_content_interpreted"])

    def test_duplicate_json_keys_fail_closed(self):
        body = subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaisesRegex(subject.RuntimeExposureXmlProfileActionError, "duplicate JSON key"):
            subject.validate_request(body, expected_issue=282, execution_sha=SHA)


if __name__ == "__main__":
    unittest.main()
