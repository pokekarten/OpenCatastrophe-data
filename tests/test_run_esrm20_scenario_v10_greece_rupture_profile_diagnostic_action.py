# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_profile_diagnostic_action as diagnostic

SHA = "a" * 40


def _receipt():
    return {
        "retrieved_at": "2026-08-20T11:30:00Z",
        "byte_count": 666,
        "sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "git_blob_sha1": "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
        "content_type": "application/xml",
        "etag": None,
    }


def _profile():
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-rupture-profile-v1",
        "byte_count": 666,
        "sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
        "rupture_element_local_name": "simpleFaultRupture",
        "element_count": 8,
        "max_depth": 5,
        "magnitude_element_count": 1,
        "rake_element_count": 1,
        "hypocenter_element_count": 1,
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _request():
    payload = {
        "schema_version": diagnostic.REQUEST_SCHEMA_VERSION,
        "action": diagnostic.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "receipt_sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "requester": "TEST-RUNNER",
    }
    return diagnostic.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


class GreeceRuptureProfileDiagnosticTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_execution_sha(self):
        parsed = diagnostic.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(parsed["target_sha"], SHA)

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
            + '"receipt_sha256":"bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",'
            + '"requester":"TEST"}'
        )
        with self.assertRaisesRegex(diagnostic.RuptureProfileDiagnosticError, "duplicate JSON key"):
            diagnostic.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_all_parser_owned_messages_have_closed_codes(self):
        for message, expected in diagnostic._PROFILE_ERROR_CODE_BY_MESSAGE.items():
            with self.subTest(message=message):
                exc = diagnostic.base.RuptureProfileError(message)
                self.assertEqual(diagnostic.classify_profile_error(exc), expected)
                self.assertIn(expected, diagnostic.PROFILE_FAILURE_CODES)

    def test_unknown_exception_text_collapses_without_leak(self):
        secret = "provider-secret-xml-fragment"
        exc = diagnostic.base.RuptureProfileError(secret)
        code = diagnostic.classify_profile_error(exc)
        self.assertEqual(code, "unclassified_profile_rejection")
        self.assertNotIn(secret, code)

    def test_profile_rejection_reports_only_closed_stage_and_code(self):
        raw = b"x" * 666

        def profiler(_raw):
            raise diagnostic.base.RuptureProfileError("foreign_xml_namespace")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (raw, _receipt()),
            profiler=profiler,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "profile")
        self.assertEqual(result["failure_code"], "foreign_xml_namespace")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["provider_file_content_profiled"])

    def test_unknown_profile_error_never_serializes_exception_text(self):
        secret = "SECRET_PROVIDER_TEXT_123"

        def profiler(_raw):
            raise diagnostic.base.RuptureProfileError(secret)

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            profiler=profiler,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["failure_code"], "unclassified_profile_rejection")
        self.assertNotIn(secret, encoded)

    def test_acquisition_failure_does_not_claim_bytes_read(self):
        def fetcher():
            raise diagnostic.base.EfehrAcquisitionError("network")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            profiler=lambda _raw: _profile(),
        )
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertEqual(result["failure_code"], "acquisition_failed")
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_byte_identity_failure_stops_before_profile(self):
        def fetcher():
            raise diagnostic.base.RuptureByteIdentityError("mismatch")

        profiler = mock.Mock()
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            profiler=profiler,
        )
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        profiler.assert_not_called()

    def test_pass_requires_existing_profile_validator(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            profiler=lambda _raw: _profile(),
        )
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_stage"])
        self.assertIsNone(result["failure_code"])
        self.assertTrue(result["provider_file_content_profiled"])

    def test_terminal_validator_rejects_authority_promotion(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            profiler=lambda _raw: _profile(),
        )
        result["publication_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.RuptureProfileDiagnosticError,
            "result publication_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_historical_v1_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            profiler=lambda _raw: _profile(),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body}]
        with mock.patch.object(diagnostic.base, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_untrusted_terminal_does_not_deduplicate(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            profiler=lambda _raw: _profile(),
        )
        body = diagnostic.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [{"user": {"login": "pokekarten"}, "body": body}]
        with mock.patch.object(diagnostic.base, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                diagnostic.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
