# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_esrm20_athens_gmpe_profile_action as subject


class AthensGmpeProfileActionTests(unittest.TestCase):
    def _request(self, sha: str) -> str:
        payload = {
            "schema_version": subject.REQUEST_SCHEMA_VERSION,
            "action": subject.ACTION,
            "issue": subject.CONTROL_ISSUE,
            "target_sha": sha,
            "dataset_id": subject.DATASET_ID,
            "requester": "test",
        }
        return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True)

    def test_request_is_bound_to_execution_sha(self):
        sha = "a" * 40
        request = subject.validate_request(self._request(sha), expected_issue=669, execution_sha=sha)
        self.assertEqual(request["target_sha"], sha)
        with self.assertRaises(subject.AthensGmpeProfileActionError):
            subject.validate_request(self._request("b" * 40), expected_issue=669, execution_sha=sha)

    def test_pass_is_exact_and_keeps_authority_false(self):
        sha = "a" * 40
        profile = {
            "schema_version": "oc-esrm20-scenario-v10-greece-gmpe-logic-tree-profile-v1",
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
            "raw_model_values_returned": False,
            "gmpe_semantics_verified": False,
            "gmpe_applicability_verified": False,
            "numerical_equivalence_verified": False,
            "scenario_selection_authorized": False,
            "independent_validation_established": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
        with mock.patch.object(subject, "_acquire_and_profile", return_value=profile):
            result = subject.run_profile(execution_sha=sha)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_profile_failure_is_bounded(self):
        sha = "a" * 40
        with mock.patch.object(
            subject,
            "_acquire_and_profile",
            side_effect=subject.AthensGmpeProfileActionError("profile_failure"),
        ):
            result = subject.run_profile(execution_sha=sha)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["provider_file_bytes_read"])

    def test_raw_url_is_fixed(self):
        url = subject._raw_file_url()
        self.assertIn("projects/273", url)
        self.assertIn(subject.COMMIT_SHA, url)
        self.assertNotIn("main", url)
        self.assertNotIn("master", url)


if __name__ == "__main__":
    unittest.main()
