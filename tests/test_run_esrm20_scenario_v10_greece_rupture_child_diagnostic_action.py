# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_child_diagnostic_action as diagnostic

SHA = "a" * 40
NS04 = "http://openquake.org/xmlns/nrml/0.4"
NS05 = "http://openquake.org/xmlns/nrml/0.5"


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


def _rupture(
    local="simpleFaultRupture",
    geometry="simpleFaultGeometry",
    *,
    child_namespace=NS04,
    include_magnitude=True,
    include_rake=True,
    include_hypocenter=True,
):
    pieces = []
    if include_magnitude:
        pieces.append("<magnitude>6.0</magnitude>")
    if include_rake:
        pieces.append("<rake>0</rake>")
    if include_hypocenter:
        pieces.append('<hypocenter lon="0" lat="0" depth="10"/>')
    if geometry:
        pieces.append(f"<{geometry}/>")
    body = "".join(pieces)
    return (
        f'<nrml xmlns="{NS04}">'
        f'<{local} xmlns="{child_namespace}">{body}</{local}>'
        "</nrml>"
    ).encode()


class GreeceRuptureChildDiagnosticTests(unittest.TestCase):
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
        with self.assertRaisesRegex(diagnostic.RuptureChildDiagnosticError, "duplicate JSON key"):
            diagnostic.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_supported_simple_fault_child_and_required_direct_structure(self):
        result = diagnostic._classify_child_shape_unbound(_rupture())
        self.assertEqual(result["root_class"], "nrml_root_legacy_04")
        self.assertEqual(result["child_class"], "simple_fault_rupture")
        self.assertEqual(result["child_namespace_class"], "legacy_04_namespace")
        self.assertEqual(
            result["required_structure_class"],
            "oq3121_required_direct_children_present",
        )

    def test_supported_child_namespace_is_classified_not_normalized(self):
        result = diagnostic._classify_child_shape_unbound(
            _rupture(child_namespace=NS05)
        )
        self.assertEqual(result["child_class"], "simple_fault_rupture")
        self.assertEqual(result["child_namespace_class"], "expected_05_namespace")

    def test_missing_core_field_is_bounded_structure_failure(self):
        result = diagnostic._classify_child_shape_unbound(
            _rupture(include_hypocenter=False)
        )
        self.assertEqual(
            result["required_structure_class"],
            "oq3121_required_direct_children_missing_or_ambiguous",
        )

    def test_multi_planes_accepts_one_or_more_planar_surfaces(self):
        raw = (
            f'<nrml xmlns="{NS04}"><multiPlanesRupture>'
            "<magnitude>6</magnitude><rake>0</rake>"
            '<hypocenter lon="0" lat="0" depth="10"/>'
            "<planarSurface/><planarSurface/>"
            "</multiPlanesRupture></nrml>"
        ).encode()
        result = diagnostic._classify_child_shape_unbound(raw)
        self.assertEqual(result["child_class"], "multi_planes_rupture")
        self.assertEqual(
            result["required_structure_class"],
            "oq3121_required_direct_children_present",
        )

    def test_multi_planes_mixed_geometry_is_ambiguous(self):
        raw = (
            f'<nrml xmlns="{NS04}"><multiPlanesRupture>'
            "<magnitude>6</magnitude><rake>0</rake>"
            '<hypocenter lon="0" lat="0" depth="10"/>'
            "<planarSurface/><kiteSurface/>"
            "</multiPlanesRupture></nrml>"
        ).encode()
        result = diagnostic._classify_child_shape_unbound(raw)
        self.assertEqual(
            result["required_structure_class"],
            "oq3121_required_direct_children_missing_or_ambiguous",
        )

    def test_unknown_child_does_not_leak_local_name(self):
        secret = "SecretProviderRupture"
        result = diagnostic._classify_child_shape_unbound(
            _rupture(local=secret, geometry=None)
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["child_class"], "unsupported_rupture_child")
        self.assertEqual(result["required_structure_class"], "not_assessed")
        self.assertNotIn(secret, encoded)

    def test_top_level_cardinality_is_classified_without_names(self):
        raw = (
            f'<nrml xmlns="{NS04}">'
            "<simpleFaultRupture/><complexFaultRupture/>"
            "</nrml>"
        ).encode()
        result = diagnostic._classify_child_shape_unbound(raw)
        self.assertEqual(result["child_class"], "top_level_cardinality_not_one")
        self.assertIsNone(result["child_namespace_class"])
        self.assertEqual(result["required_structure_class"], "not_assessed")

    def test_non_legacy_root_fails_closed_instead_of_widening(self):
        raw = (
            f'<nrml xmlns="{NS05}"><simpleFaultRupture/></nrml>'
        ).encode()
        with self.assertRaisesRegex(
            diagnostic.ChildShapeParseError, "^child_shape_parse_rejected$"
        ):
            diagnostic._classify_child_shape_unbound(raw)

    def test_unsafe_xml_is_collapsed_to_static_parse_failure(self):
        secret = "SECRET_ENTITY_VALUE"
        raw = (
            '<!DOCTYPE nrml [<!ENTITY leak "'
            + secret
            + f'">]><nrml xmlns="{NS04}">&leak;</nrml>'
        ).encode()
        with self.assertRaisesRegex(
            diagnostic.ChildShapeParseError, "^child_shape_parse_rejected$"
        ) as ctx:
            diagnostic._classify_child_shape_unbound(raw)
        self.assertNotIn(secret, str(ctx.exception))

    def test_successful_classification_is_diagnostic_pass_only(self):
        classification = diagnostic._classify_child_shape_unbound(_rupture())
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: classification,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["child_class"], "simple_fault_rupture")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["child_shape_classified"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_child_parse_failure_preserves_byte_identity_only(self):
        def classifier(_raw):
            raise diagnostic.ChildShapeParseError("SECRET_PROVIDER_TEXT")

        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=classifier,
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "child_shape")
        self.assertEqual(result["failure_code"], "child_shape_parse_rejected")
        self.assertNotIn("SECRET_PROVIDER_TEXT", encoded)
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["child_shape_classified"])

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
        self.assertFalse(result["child_shape_classified"])

    def test_byte_identity_failure_stops_before_child_inspection(self):
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
        classification = diagnostic._classify_child_shape_unbound(_rupture())
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: classification,
        )
        result["model_use_authorized"] = True
        with self.assertRaisesRegex(
            diagnostic.RuptureChildDiagnosticError,
            "result model_use_authorized drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_terminal_validator_rejects_non_boolean_false_equivalent(self):
        classification = diagnostic._classify_child_shape_unbound(_rupture())
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: classification,
        )
        result["external_bytes_persisted"] = 0
        with self.assertRaisesRegex(
            diagnostic.RuptureChildDiagnosticError,
            "result external_bytes_persisted drifted",
        ):
            diagnostic._validate_terminal_result(result)

    def test_historical_root_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-root-diagnostic-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(diagnostic.parse_terminal_result(old))

    def test_trusted_bot_terminal_deduplicates_exact_execution_sha(self):
        classification = diagnostic._classify_child_shape_unbound(_rupture())
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: classification,
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
        classification = diagnostic._classify_child_shape_unbound(_rupture())
        result = diagnostic._run_diagnostic_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x" * 666, _receipt()),
            classifier=lambda _raw: classification,
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
