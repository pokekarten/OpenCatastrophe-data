# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_root_diagnostic_action as diagnostic

SHA = "a" * 40
NS05 = "http://openquake.org/xmlns/nrml/0.5"
NS04 = "http://openquake.org/xmlns/nrml/0.4"


def _receipt():
    return {
        "retrieved_at": "2026-08-20T17:00:00Z",
        "byte_count": 666,
        "sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "git_blob_sha1": "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
        "content_type": "application/xml",
        "etag": None,
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


def _xml(local="nrml", namespace=NS05):
    return f'<{local} xmlns="{namespace}"></{local}>'.encode()


class GreeceRuptureRootDiagnosticTests(unittest.TestCase):
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
        with self.assertRaisesRegex(diagnostic.RuptureRootDiagnosticError, "duplicate JSON key"):
            diagnostic.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_nrml_expected_namespace_is_classified_without_acceptance_claim(self):
        self.assertEqual(
            diagnostic._classify_root_shape_unbound(_xml()),
            "nrml_root_expected_namespace",
        )

    def test_nrml_legacy_04_is_classified_not_accepted(self):
        self.assertEqual(
            diagnostic._classify_root_shape_unbound(_xml(namespace=NS04)),
            "nrml_root_legacy_04",
        )

    def test_nrml_unknown_namespace_does_not_leak_value(self):
        secret = "https://provider.invalid/SECRET-NAMESPACE"
        root_class = diagnostic._classify_root_shape_unbound(_xml(namespace=secret))
        self.assertEqual(root_class, "nrml_root_unrecognized_namespace")
        self.assertNotIn(secret, root_class)

    def test_direct_rupture_root_is_distinguished(self):
        self.assertEqual(
            diagnostic._classify_root_shape_unbound(
                _xml(local="singlePlaneRupture", namespace=NS05)
            ),
            "direct_rupture_root_expected_namespace",
        )
        self.assertEqual(
            diagnostic._classify_root_shape_unbound(
                _xml(local="singlePlaneRupture", namespace=NS04)
            ),
            "direct_rupture_root_legacy_04",
        )
        self.assertEqual(
            diagnostic._classify_root_shape_unbound(
                _xml(local="singlePlaneRupture", namespace="urn:unknown")
            ),
            "direct_rupture_root_unrecognized_namespace",
        )

    def test_unknown_local_name_does_not_leak_value(self):
        secret = "SecretProviderRoot"
        root_class = diagnostic._classify_root_shape_unbound(_xml(local=secret))
        self.assertEqual(root_class, "unrecognized_root_local_name")
        self.assertNotIn(secret, root_class)

    def test_unsafe_xml_is_collapsed_to_static_parse_failure(self):
        secret = "SECRET_ENTITY_VALUE"
        raw = (
            '<!DOCTYPE nrml [<!ENTITY leak "'
            + secret
            + '">]><nrml xmlns="'
            + NS05
            + '">&leak;</nrml>'
        ).encode()
        with self.assertRaisesRegex(diagnostic.RootShapeParseError, "^root_parse_rejected$") as ctx:
            diagnostic._classify_root_shape_unbound(raw)
        self.assertNotIn(secret, str(ctx.exception))

    def test_successful_classification_is_diagnostic_pass_only(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: "nrml_root_legacy_04",
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["root_class"], "nrml_root_legacy_04")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["root_classified"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_root_parse_failure_preserves_byte_identity_only(self):
        def classifier(_raw):
            raise diagnostic.RootShapeParseError("SECRET_PROVIDER_TEXT")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=classifier,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "root")
        self.assertEqual(result["failure_code"], "root_parse_rejected")
        self.assertNotIn("SECRET_PROVIDER_TEXT", encoded)
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["root_classified"])

    def test_acquisition_failure_does_not_claim_bytes_read(self):
        def fetcher():
            raise diagnostic.base.EfehrAcquisitionError("network")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            classifier=mock.Mock(),
        )
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        self.assertFalse(result["root_classified"])

    def test_byte_identity_failure_stops_before_root_inspection(self):
        def fetcher():
            raise diagnostic.base.RuptureByteIdentityError("mismatch")

        classifier = mock.Mock()
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=fetcher,
            classifier=classifier,
        )
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertEqual(result["failure_code"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        classifier.assert_not_called()

    def test_terminal_validator_rejects_authority_promotion(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: "nrml_root_legacy_04",
        )
        result["model_use_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.RuptureRootDiagnosticError,
            "result model_use_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_terminal_validator_rejects_non_boolean_false_equivalent(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: "nrml_root_legacy_04",
        )
        result["external_bytes_persisted"] = 0
        with self.assertRaisesRegex(
            diagnostic.RuptureRootDiagnosticError,
            "result external_bytes_persisted drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_historical_profile_diagnostic_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-diagnostic-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: "unrecognized_root_local_name",
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
            classifier=lambda _raw: "unrecognized_root_local_name",
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
