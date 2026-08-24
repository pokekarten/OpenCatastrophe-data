# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_esrm20_athens_gmpe_profile_diagnostic_action as diagnostic

SHA = "a" * 40


def _request():
    payload = {
        "schema_version": diagnostic.REQUEST_SCHEMA_VERSION,
        "action": diagnostic.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "receipt_sha256": diagnostic._RECEIPT_SHA256,
        "requester": "TEST-RUNNER",
    }
    return diagnostic.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _content_error(message):
    try:
        raise diagnostic.profile.GmpeLogicTreeProfileError(message)
    except diagnostic.profile.GmpeLogicTreeProfileError as cause:
        raise diagnostic.base.AthensGmpeProfileContentError("collapsed provider profile failure") from cause


class AthensGmpeProfileDiagnosticTests(unittest.TestCase):
    def test_request_is_bound_to_execution_sha_and_receipt(self):
        parsed = diagnostic.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(parsed["target_sha"], SHA)
        self.assertEqual(parsed["receipt_sha256"], diagnostic._RECEIPT_SHA256)

    def test_all_exact_parser_messages_have_closed_codes(self):
        for message, expected in diagnostic._PROFILE_ERROR_CODE_BY_MESSAGE.items():
            with self.subTest(message=message):
                exc = diagnostic.profile.GmpeLogicTreeProfileError(message)
                self.assertEqual(diagnostic.classify_profile_error(exc), expected)
                self.assertIn(expected, diagnostic.PROFILE_FAILURE_CODES)

    def test_dynamic_parser_messages_collapse_to_prefix_codes(self):
        examples = {
            "missing_direct_child:logicTree:logicTreeBranchingLevel": "missing_direct_child",
            "unexpected_direct_child:logicTree:providerSpecific": "unexpected_direct_child",
            "unexpected_leaf_child:uncertaintyModel": "unexpected_leaf_child",
            "non_whitespace_container_text_forbidden:logicTree": "non_whitespace_container_text_forbidden",
            "missing_required_element:logicTreeBranch": "missing_required_element",
        }
        for message, expected in examples.items():
            with self.subTest(message=message):
                code = diagnostic.classify_profile_error(diagnostic.profile.GmpeLogicTreeProfileError(message))
                self.assertEqual(code, expected)
                self.assertNotIn("providerSpecific", code)

    def test_unknown_exception_text_never_leaks(self):
        secret = "SECRET_PROVIDER_MODEL_STRING_123"
        code = diagnostic.classify_profile_error(diagnostic.profile.GmpeLogicTreeProfileError(secret))
        self.assertEqual(code, "unclassified_profile_rejection")
        self.assertNotIn(secret, code)

    def test_profile_failure_uses_parser_cause_without_text_leak(self):
        def acquirer():
            _content_error("unexpected_direct_child:logicTreeBranchSet:providerSpecific")

        result = diagnostic._run_diagnostic_with(execution_sha=SHA, acquirer=acquirer)
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], "unexpected_direct_child")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertNotIn("providerSpecific", encoded)

    def test_sha_mismatch_is_byte_identity_not_structure(self):
        def acquirer():
            _content_error("sha256_mismatch")

        result = diagnostic._run_diagnostic_with(execution_sha=SHA, acquirer=acquirer)
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "profiler_sha256_mismatch")
        self.assertFalse(result["byte_identity_verified"])

    def test_acquisition_failure_keeps_byte_read_state_unknown(self):
        def acquirer():
            raise diagnostic.base.AthensGmpeProfileAcquisitionError("closed")

        result = diagnostic._run_diagnostic_with(execution_sha=SHA, acquirer=acquirer)
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_terminal_validator_rejects_authority_promotion(self):
        def acquirer():
            _content_error("unexpected_nrml_root")

        result = diagnostic._run_diagnostic_with(execution_sha=SHA, acquirer=acquirer)
        result["model_use_authorized"] = True
        with self.assertRaisesRegex(diagnostic.AthensGmpeProfileDiagnosticError, "result model_use_authorized drifted"):
            diagnostic._validate_terminal_result(result)

    def test_trusted_match_does_not_hide_later_malformed_terminal(self):
        def acquirer():
            _content_error("unexpected_nrml_root")

        result = diagnostic._run_diagnostic_with(execution_sha=SHA, acquirer=acquirer)
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [
            {"user": {"login": "github-actions[bot]"}, "body": body},
            {"user": {"login": "github-actions[bot]"}, "body": diagnostic.RESULT_MARKER + "\n{}"},
        ]
        with mock.patch.object(diagnostic.base, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(diagnostic.AthensGmpeProfileDiagnosticError):
                diagnostic.has_terminal_result(repository="pokekarten/OpenCatastrophe-data", token="token", execution_sha=SHA)


if __name__ == "__main__":
    unittest.main()
