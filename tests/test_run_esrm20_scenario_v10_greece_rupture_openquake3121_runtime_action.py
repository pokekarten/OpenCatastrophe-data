# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import http.client
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_openquake3121_runtime_action as runtime

SHA = "a" * 40
IMAGE = "sha256:" + "b" * 64


def _receipt():
    return {
        "retrieved_at": "2026-08-21T06:00:00Z",
        "byte_count": 666,
        "sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "git_blob_sha1": "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
        "content_type": "application/xml",
        "etag": None,
    }


def _request():
    payload = {
        "schema_version": runtime.REQUEST_SCHEMA_VERSION,
        "action": runtime.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": "efehr.esrm20.scenario-tests.v1.0",
        "receipt_sha256": "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        "requester": "TEST-RUNNER",
    }
    return runtime.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _shape():
    return {
        "root_class": "nrml_root_legacy_04",
        "child_class": "single_plane_rupture",
        "child_namespace_class": "legacy_04_namespace",
        "required_structure_class": "oq3121_required_direct_children_present",
    }


def _run(**overrides):
    kwargs = {
        "execution_sha": SHA,
        "image_digest": IMAGE,
        "runtime_verifier": lambda: None,
        "fetcher": lambda: (b"synthetic", _receipt()),
        "identity_checker": lambda _raw: None,
        "shape_checker": lambda _raw: _shape(),
        "converter": lambda _raw: {
            "rupture_class": "BaseRupture",
            "surface_class": "PlanarSurface",
        },
    }
    kwargs.update(overrides)
    return runtime._run_native_with(**kwargs)


class GreeceRuptureOpenQuake3121RuntimeTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_execution_sha(self):
        parsed = runtime.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(parsed["target_sha"], SHA)
        self.assertEqual(parsed["receipt_sha256"], runtime._RECEIPT_SHA256)

    def test_duplicate_request_key_fails_closed(self):
        body = (
            runtime.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"'
            + runtime.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + runtime.ACTION
            + '","issue":285,"target_sha":"'
            + SHA
            + '","target_sha":"'
            + SHA
            + '","dataset_id":"efehr.esrm20.scenario-tests.v1.0",'
            + '"receipt_sha256":"bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",'
            + '"requester":"TEST"}'
        )
        with self.assertRaisesRegex(
            runtime.GreeceRuptureOpenQuake3121RuntimeError,
            "duplicate JSON key",
        ):
            runtime.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_runtime_reference_and_api_fixtures_are_hard_fenced(self):
        self.assertEqual(runtime._OPENQUAKE_TAG, "v3.12.1")
        self.assertEqual(
            runtime._OPENQUAKE_COMMIT,
            "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9",
        )
        self.assertEqual(
            runtime._OPENQUAKE_PARSER_PATH,
            "openquake.commonlib.readinput.get_rupture",
        )
        self.assertEqual(runtime._API_RUPTURE_MESH_SPACING_KM, 1.5)
        self.assertEqual(runtime._API_SES_SEED, 1)

    def test_runtime_identity_is_proved_before_provider_access(self):
        observed = []

        def verify():
            observed.append("runtime")

        def fetch():
            observed.append("provider")
            return b"synthetic", _receipt()

        result = _run(runtime_verifier=verify, fetcher=fetch)
        self.assertEqual(observed, ["runtime", "provider"])
        self.assertEqual(result["status"], "pass")

    def test_runtime_identity_failure_stops_before_provider_access(self):
        fetcher = mock.Mock()

        def verify():
            raise runtime.GreeceRuptureOpenQuake3121RuntimeError("private detail")

        result = _run(runtime_verifier=verify, fetcher=fetcher)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "runtime_identity")
        self.assertEqual(result["failure_code"], "runtime_identity_rejected")
        self.assertFalse(result["runtime_source_commit_verified"])
        self.assertFalse(result["provider_file_bytes_read"])
        fetcher.assert_not_called()
        self.assertNotIn("private detail", json.dumps(result, sort_keys=True))

    def test_acquisition_failure_is_bounded(self):
        def fetcher():
            raise runtime.base.EfehrAcquisitionError("secret transport")

        result = _run(fetcher=fetcher)
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertTrue(result["runtime_source_commit_verified"])
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertNotIn("secret transport", json.dumps(result, sort_keys=True))

    def test_incomplete_http_stream_is_bounded_acquisition_terminal(self):
        def fetcher():
            raise http.client.IncompleteRead(b"partial-provider-bytes", 666)

        result = _run(fetcher=fetcher)
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertEqual(result["failure_code"], "acquisition_failed")
        self.assertTrue(result["runtime_source_commit_verified"])
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        self.assertFalse(result["trusted_shape_precondition_verified"])
        self.assertFalse(result["native_conversion_attempted"])
        self.assertNotIn("partial-provider-bytes", encoded)
        self.assertEqual(runtime._validate_terminal_result(result), SHA)

    def test_byte_identity_failure_stops_before_shape_and_native_conversion(self):
        shape_checker = mock.Mock()
        converter = mock.Mock()

        def identity_checker(_raw):
            raise runtime.base.RuptureByteIdentityError("wrong bytes")

        result = _run(
            identity_checker=identity_checker,
            shape_checker=shape_checker,
            converter=converter,
        )
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])
        shape_checker.assert_not_called()
        converter.assert_not_called()

    def test_shape_precondition_must_match_merged_single_plane_evidence(self):
        converter = mock.Mock()
        wrong = _shape()
        wrong["child_class"] = "simple_fault_rupture"
        result = _run(shape_checker=lambda _raw: wrong, converter=converter)
        self.assertEqual(result["failure_stage"], "shape_precondition")
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["trusted_shape_precondition_verified"])
        converter.assert_not_called()

    def test_native_rejection_is_static_and_preserves_only_upstream_evidence(self):
        def converter(_raw):
            raise runtime.NativeConversionRejected("SECRET_NATIVE_EXCEPTION")

        result = _run(converter=converter)
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "native_conversion")
        self.assertEqual(result["failure_code"], "native_conversion_rejected")
        self.assertTrue(result["runtime_source_commit_verified"])
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["trusted_shape_precondition_verified"])
        self.assertTrue(result["native_conversion_attempted"])
        self.assertFalse(result["legacy_nrml_04_native_acceptance_verified"])
        self.assertNotIn("SECRET_NATIVE_EXCEPTION", encoded)

    def test_native_pass_is_narrow_and_keeps_all_downstream_authority_false(self):
        result = _run()
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["legacy_nrml_04_native_acceptance_verified"])
        self.assertTrue(result["single_plane_native_conversion_verified"])
        self.assertTrue(result["readinput_postconditions_verified"])
        self.assertEqual(result["rupture_class"], "BaseRupture")
        self.assertEqual(result["surface_class"], "PlanarSurface")
        for field in (
            "historical_environment_verified",
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "site_model_compatibility_verified",
            "gsim_compatibility_verified",
            "numerical_hazard_agreement_verified",
            "vulnerability_compatibility_verified",
            "reference_run_verified",
            "scientific_validity_verified",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
            "external_bytes_persisted",
            "output_payload_bytes_read",
        ):
            self.assertFalse(result[field], field)

    def test_native_unbound_uses_only_minimal_get_rupture_contract(self):
        PlanarSurface = type("PlanarSurface", (), {})
        BaseRupture = type("BaseRupture", (), {})
        seen = {}

        def get_rupture(oqparam):
            seen["spacing"] = oqparam.rupture_mesh_spacing
            seen["seed"] = oqparam.ses_seed
            path = Path(oqparam.inputs["rupture_model"])
            seen["payload"] = path.read_bytes()
            rupture = BaseRupture()
            rupture.surface = PlanarSurface()
            rupture.tectonic_region_type = "*"
            rupture.rup_id = oqparam.ses_seed
            return rupture

        result = runtime._native_convert_unbound(b"<nrml/>", get_rupture=get_rupture)
        self.assertEqual(result["rupture_class"], "BaseRupture")
        self.assertEqual(result["surface_class"], "PlanarSurface")
        self.assertEqual(seen["spacing"], 1.5)
        self.assertEqual(seen["seed"], 1)
        self.assertEqual(seen["payload"], b"<nrml/>")

    def test_native_unbound_collapses_exception_text(self):
        def get_rupture(_oqparam):
            raise ValueError("SECRET_XML_OR_ENGINE_DETAIL")

        with self.assertRaisesRegex(
            runtime.NativeConversionRejected,
            "^native_conversion_rejected$",
        ) as ctx:
            runtime._native_convert_unbound(b"<nrml/>", get_rupture=get_rupture)
        self.assertNotIn("SECRET_XML_OR_ENGINE_DETAIL", str(ctx.exception))

    def test_reader_source_must_be_under_exact_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "oq" / "openquake"
            package.mkdir(parents=True)
            good = package / "commonlib" / "readinput.py"
            good.parent.mkdir(parents=True)
            good.write_text("# source\n", encoding="utf-8")
            self.assertEqual(
                runtime._require_source_path(good, package_root=package),
                good.resolve(),
            )
            outside = root / "installed" / "readinput.py"
            outside.parent.mkdir()
            outside.write_text("# wrong\n", encoding="utf-8")
            with self.assertRaisesRegex(
                runtime.GreeceRuptureOpenQuake3121RuntimeError,
                "outside exact checkout",
            ):
                runtime._require_source_path(outside, package_root=package)

    def test_terminal_validator_rejects_authority_promotion(self):
        result = _run()
        result["model_use_authorized"] = True
        with self.assertRaisesRegex(
            runtime.GreeceRuptureOpenQuake3121RuntimeError,
            "result model_use_authorized drifted",
        ):
            runtime._validate_terminal_result(result)

    def test_terminal_validator_rejects_false_equivalent_integer(self):
        result = _run()
        result["external_bytes_persisted"] = 0
        with self.assertRaisesRegex(
            runtime.GreeceRuptureOpenQuake3121RuntimeError,
            "result external_bytes_persisted drifted",
        ):
            runtime._validate_terminal_result(result)

    def test_trusted_bot_terminal_deduplicates_only_exact_execution_sha(self):
        result = _run()
        body = runtime.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body}]
        with mock.patch.object(runtime.base, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                runtime.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )
            self.assertFalse(
                runtime.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha="c" * 40,
                )
            )

    def test_historical_child_terminal_is_not_reinterpreted(self):
        old = (
            "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-child-diagnostic-result-v1 -->\n"
            '{"execution_sha":"' + SHA + '"}'
        )
        self.assertIsNone(runtime.parse_terminal_result(old))


if __name__ == "__main__":
    unittest.main()
