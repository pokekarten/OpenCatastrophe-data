# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from pathlib import Path
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
        "receipt_sha256": "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78",
        "requester": "TEST-RUNNER",
    }
    return diagnostic.REQUEST_MARKER + "\n" + json.dumps(
        payload,
        separators=(",", ":"),
    )


def _content_acquirer(message):
    def acquirer():
        try:
            raise diagnostic.profile.GmpeLogicTreeProfileError(message)
        except diagnostic.profile.GmpeLogicTreeProfileError as cause:
            raise diagnostic.acquisition.AthensGmpeProfileContentError(
                "exact Athens GMPE bytes failed profile"
            ) from cause

    return acquirer


class AthensGmpeProfileDiagnosticTests(unittest.TestCase):
    def test_request_is_bound_to_execution_sha_and_receipt(self):
        parsed = diagnostic.validate_request(
            _request(),
            expected_issue=285,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["target_sha"], SHA)
        self.assertEqual(
            parsed["receipt_sha256"],
            "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78",
        )

    def test_duplicate_request_key_fails_closed(self):
        body = (
            diagnostic.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"'
            + diagnostic.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + diagnostic.ACTION
            + '","issue":285,"target_sha":"'
            + SHA
            + '","target_sha":"'
            + SHA
            + '","dataset_id":"efehr.esrm20.scenario-tests.v1.0",'
            + '"receipt_sha256":"3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78",'
            + '"requester":"TEST"}'
        )
        with self.assertRaisesRegex(
            diagnostic.AthensGmpeProfileDiagnosticError,
            "duplicate JSON key",
        ):
            diagnostic.validate_request(
                body,
                expected_issue=285,
                execution_sha=SHA,
            )

    def test_exact_profiler_messages_have_closed_codes(self):
        for message, expected in diagnostic._PROFILE_ERROR_CODE_BY_MESSAGE.items():
            with self.subTest(message=message):
                exc = diagnostic.profile.GmpeLogicTreeProfileError(message)
                self.assertEqual(diagnostic.classify_profile_error(exc), expected)
                self.assertIn(expected, diagnostic.PROFILE_FAILURE_CODES)

    def test_dynamic_profiler_messages_collapse_suffixes(self):
        samples = {
            "missing_direct_child:logicTree:SECRET": "missing_direct_child",
            "unexpected_direct_child:logicTreeBranchSet:SECRET": "unexpected_direct_child",
            "unexpected_leaf_child:uncertaintyModel:SECRET": "unexpected_leaf_child",
            "non_whitespace_container_text_forbidden:SECRET": (
                "non_whitespace_container_text_forbidden"
            ),
            "missing_required_element:SECRET": "missing_required_element",
        }
        for message, expected in samples.items():
            with self.subTest(message=message):
                exc = diagnostic.profile.GmpeLogicTreeProfileError(message)
                code = diagnostic.classify_profile_error(exc)
                self.assertEqual(code, expected)
                self.assertNotIn("SECRET", code)

    def test_known_logic_tree_branch_set_pair_gets_closed_schema_code(self):
        message = "unexpected_direct_child:logicTree:logicTreeBranchSet"
        exc = diagnostic.profile.GmpeLogicTreeProfileError(message)
        code = diagnostic.classify_profile_error(exc)
        self.assertEqual(code, "logic_tree_branch_set_direct_child")
        self.assertIn(code, diagnostic.STRUCTURAL_PROFILE_FAILURE_CODES)

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer(message),
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], code)
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertNotIn("unexpected_direct_child:", encoded)

    def test_unknown_exception_text_collapses_without_leak(self):
        secret = "SECRET_PROVIDER_XML_OR_MODEL_TEXT"
        exc = diagnostic.profile.GmpeLogicTreeProfileError(secret)
        code = diagnostic.classify_profile_error(exc)
        self.assertEqual(code, "unclassified_profile_rejection")
        self.assertNotIn(secret, code)

    def test_structural_profile_rejection_reports_closed_code(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("unexpected_nrml_root"),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], "unexpected_nrml_root")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["provider_file_content_profiled"])

    def test_dynamic_profile_rejection_never_serializes_suffix(self):
        secret = "SECRET_CHILD"
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer(
                "unexpected_direct_child:logicTreeBranchSet:" + secret
            ),
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_code"], "unexpected_direct_child")
        self.assertNotIn(secret, encoded)

    def test_sha_mismatch_is_byte_identity_failure(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("sha256_mismatch"),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "profiler_sha256_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_unknown_profile_error_does_not_claim_identity(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("NEW_SECRET_FAILURE"),
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], "unclassified_profile_rejection")
        self.assertFalse(result["byte_identity_verified"])
        self.assertNotIn("NEW_SECRET_FAILURE", encoded)

    def test_acquisition_failure_does_not_claim_byte_read(self):
        def acquirer():
            raise diagnostic.acquisition.AthensGmpeProfileAcquisitionError(
                "network or fixed response failure"
            )

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=acquirer,
        )
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertEqual(result["failure_code"], "acquisition_failed")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_pass_requires_existing_evidence_validator(self):
        evidence = {"bounded": True}
        with mock.patch.object(
            diagnostic.base,
            "_validate_evidence",
            return_value=evidence,
        ) as validator:
            result = diagnostic._run_diagnostic_with(
                execution_sha=SHA,
                acquirer=lambda: evidence,
            )
        validator.assert_called_once_with(evidence)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_stage"])
        self.assertIsNone(result["failure_code"])
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertTrue(result["byte_identity_verified"])

    def test_terminal_validator_rejects_authority_promotion(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("unexpected_logic_tree_root"),
        )
        result["publication_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.AthensGmpeProfileDiagnosticError,
            "result publication_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_historical_v1_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-athens-gmpe-profile-result-v1 -->\n"
            + '{"execution_sha":"'
            + SHA
            + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("unexpected_nrml_root"),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(
            result,
            separators=(",", ":"),
        )
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body}]
        with mock.patch.object(
            diagnostic.base,
            "fetch_repository_comments",
            return_value=comments,
        ):
            self.assertTrue(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_matching_terminal_does_not_short_circuit_later_malformed_trusted_result(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("unexpected_nrml_root"),
        )
        valid = diagnostic.RESULT_MARKER + "\n" + json.dumps(
            result,
            separators=(",", ":"),
        )
        malformed = diagnostic.RESULT_MARKER + "\n{}"
        comments = [
            {"user": {"login": "github-actions[bot]"}, "body": valid},
            {"user": {"login": "github-actions[bot]"}, "body": malformed},
        ]
        with mock.patch.object(
            diagnostic.base,
            "fetch_repository_comments",
            return_value=comments,
        ):
            with self.assertRaisesRegex(
                diagnostic.AthensGmpeProfileDiagnosticError,
                "result fields drifted",
            ):
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )

    def test_untrusted_terminal_does_not_deduplicate(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            acquirer=_content_acquirer("unexpected_nrml_root"),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(
            result,
            separators=(",", ":"),
        )
        comments = [{"user": {"login": "pokekarten"}, "body": body}]
        with mock.patch.object(
            diagnostic.base,
            "fetch_repository_comments",
            return_value=comments,
        ):
            self.assertFalse(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_workflow_keeps_provider_execution_on_trusted_main(self):
        workflow = Path(
            ".github/workflows/esrm20-athens-gmpe-profile-diagnostic.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("Checkout trusted default branch", workflow)
        self.assertIn("Checkout exact trusted execution commit", workflow)
        self.assertGreaterEqual(workflow.count("persist-credentials: false"), 2)
        self.assertIn(diagnostic.REQUEST_MARKER, workflow)
        self.assertIn(diagnostic.RESULT_MARKER, workflow)
        self.assertIn("issues: write", workflow)
        module_entrypoint = (
            "python -m scripts.run_esrm20_athens_gmpe_profile_diagnostic_action"
        )
        direct_entrypoint = (
            "python scripts/run_esrm20_athens_gmpe_profile_diagnostic_action.py"
        )
        self.assertEqual(workflow.count(module_entrypoint), 2)
        self.assertNotIn(direct_entrypoint, workflow)
        self.assertNotIn("pull_request_target:", workflow)


if __name__ == "__main__":
    unittest.main()
