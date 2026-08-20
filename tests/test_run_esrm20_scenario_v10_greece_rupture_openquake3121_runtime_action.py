# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_openquake3121_runtime_action as subject


SHA = "1" * 40
IMAGE = "sha256:" + "a" * 64


def request_body(**overrides):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "receipt_sha256": subject.RECEIPT_SHA256,
        "openquake_tag": subject.OPENQUAKE_TAG,
        "openquake_commit": subject.OPENQUAKE_COMMIT,
        "requester": "test-agent",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    )


class NativeRuptureGateRequestTests(unittest.TestCase):
    def test_valid_request_is_exactly_fenced(self):
        parsed = subject.validate_request(
            request_body(), expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
        )
        self.assertEqual(parsed["openquake_commit"], subject.OPENQUAKE_COMMIT)
        self.assertEqual(parsed["receipt_sha256"], subject.RECEIPT_SHA256)

    def test_wrong_target_sha_is_rejected(self):
        with self.assertRaises(subject.NativeRuptureGateError):
            subject.validate_request(
                request_body(target_sha="2" * 40),
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=SHA,
            )

    def test_duplicate_json_key_is_rejected(self):
        body = subject.REQUEST_MARKER + "\n" + (
            '{"schema_version":"%s","schema_version":"%s"}'
            % (subject.REQUEST_SCHEMA_VERSION, subject.REQUEST_SCHEMA_VERSION)
        )
        with self.assertRaises(subject.NativeRuptureGateError):
            subject.validate_request(
                body, expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
            )

    def test_nonfinite_json_is_rejected(self):
        body = request_body().replace('"requester":"test-agent"', '"requester":NaN')
        with self.assertRaises(subject.NativeRuptureGateError):
            subject.validate_request(
                body, expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
            )

    def test_extra_request_field_is_rejected(self):
        with self.assertRaises(subject.NativeRuptureGateError):
            subject.validate_request(
                request_body(extra="not-authorized"),
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=SHA,
            )


class NativeRuptureGateRunTests(unittest.TestCase):
    def test_pass_is_bounded_to_runtime_class_metadata(self):
        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=lambda: (b"verified", {}),
            converter=lambda raw: {
                "openquake_version": "3.12.1-git0bb8441",
                "rupture_class": subject.RUPTURE_CLASS,
                "surface_class": subject.SURFACE_CLASS,
            },
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["legacy_nrml_04_native_acceptance_verified"])
        self.assertTrue(result["single_plane_native_conversion_verified"])
        self.assertFalse(result["site_gsim_compatibility_established"])
        self.assertFalse(result["numerical_hazard_agreement_established"])
        self.assertFalse(result["vulnerability_compatibility_established"])
        self.assertFalse(result["reference_run_established"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("receipt", result)
        self.assertNotIn("raw", result)

    def test_acquisition_failure_does_not_claim_byte_identity(self):
        def fail():
            raise subject.base.EfehrAcquisitionError("offline")

        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=fail,
            converter=lambda raw: {},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_stage"], "acquisition")
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_byte_identity_failure_does_not_enter_runtime(self):
        called = False

        def fail():
            raise subject.base.RuptureByteIdentityError("drift")

        def converter(raw):
            nonlocal called
            called = True
            return {}

        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=fail,
            converter=converter,
        )
        self.assertFalse(called)
        self.assertEqual(result["failure_stage"], "byte_identity")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["byte_identity_verified"])

    def test_native_rejection_stays_blocked_without_partial_runtime_metadata(self):
        def reject(raw):
            raise subject.NativeRuptureGateError("native reject")

        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=lambda: (b"verified", {}),
            converter=reject,
        )
        self.assertEqual(result["failure_stage"], "openquake_runtime")
        self.assertTrue(result["byte_identity_verified"])
        self.assertIsNone(result["openquake_version"])
        self.assertIsNone(result["rupture_class"])
        self.assertIsNone(result["surface_class"])
        self.assertFalse(result["legacy_nrml_04_native_acceptance_verified"])

    def test_converter_cannot_widen_metadata(self):
        with self.assertRaises(subject.NativeRuptureGateError):
            subject._run_with(
                execution_sha=SHA,
                image_digest=IMAGE,
                fetcher=lambda: (b"verified", {}),
                converter=lambda raw: {
                    "openquake_version": "3.12.1",
                    "rupture_class": subject.RUPTURE_CLASS,
                    "surface_class": subject.SURFACE_CLASS,
                    "magnitude": "forbidden",
                },
            )

    def test_terminal_result_rejects_authority_widening(self):
        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=lambda: (b"verified", {}),
            converter=lambda raw: {
                "openquake_version": "3.12.1",
                "rupture_class": subject.RUPTURE_CLASS,
                "surface_class": subject.SURFACE_CLASS,
            },
        )
        result["model_use_authorized"] = True
        with self.assertRaises(subject.NativeRuptureGateError):
            subject._validate_terminal_result(result)

    def test_terminal_envelope_round_trips(self):
        result = subject._run_with(
            execution_sha=SHA,
            image_digest=IMAGE,
            fetcher=lambda: (b"verified", {}),
            converter=lambda raw: {
                "openquake_version": "3.12.1",
                "rupture_class": subject.RUPTURE_CLASS,
                "surface_class": subject.SURFACE_CLASS,
            },
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertEqual(subject.parse_terminal_result(body), SHA)


class NativeOpenQuakeConversionTests(unittest.TestCase):
    def _fake_modules(self, root: Path, *, version="3.12.1-git0bb8441"):
        oq = types.ModuleType("openquake")
        baselib = types.ModuleType("openquake.baselib")
        baselib.__version__ = version
        commonlib = types.ModuleType("openquake.commonlib")
        readinput = types.ModuleType("openquake.commonlib.readinput")
        readinput.__file__ = str(root / "openquake" / "commonlib" / "readinput.py")
        captured = {}

        PlanarSurface = type("PlanarSurface", (), {})
        BaseRupture = type("BaseRupture", (), {})

        def get_rupture(oqparam):
            path = Path(oqparam.inputs["rupture_model"])
            captured["path"] = path
            captured["bytes"] = path.read_bytes()
            captured["mesh"] = oqparam.rupture_mesh_spacing
            captured["seed"] = oqparam.ses_seed
            rupture = BaseRupture()
            rupture.surface = PlanarSurface()
            return rupture

        readinput.get_rupture = get_rupture
        oq.baselib = baselib
        oq.commonlib = commonlib
        commonlib.readinput = readinput
        modules = {
            "openquake": oq,
            "openquake.baselib": baselib,
            "openquake.commonlib": commonlib,
            "openquake.commonlib.readinput": readinput,
        }
        return modules, captured

    def test_native_converter_uses_model_era_reader_and_deletes_temp_bytes(self):
        expected_shape = {
            "root_class": "nrml_root_legacy_04",
            "child_class": "single_plane_rupture",
            "child_namespace_class": "legacy_04_namespace",
            "required_structure_class": "oq3121_required_direct_children_present",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            modules, captured = self._fake_modules(root)
            with (
                mock.patch.dict(sys.modules, modules, clear=False),
                mock.patch.dict(os.environ, {"OC_OQ_CHECKOUT_ROOT": str(root)}),
                mock.patch.object(
                    subject.childdiag,
                    "classify_fixed_child_shape",
                    return_value=expected_shape,
                ),
            ):
                metadata = subject._native_convert(b"exact-provider-bytes")

        self.assertEqual(metadata["rupture_class"], subject.RUPTURE_CLASS)
        self.assertEqual(metadata["surface_class"], subject.SURFACE_CLASS)
        self.assertEqual(captured["bytes"], b"exact-provider-bytes")
        self.assertEqual(captured["mesh"], subject.API_RUPTURE_MESH_SPACING)
        self.assertEqual(captured["seed"], subject.API_SES_SEED)
        self.assertFalse(captured["path"].exists())

    def test_native_converter_rejects_source_outside_pinned_checkout(self):
        expected_shape = {
            "root_class": "nrml_root_legacy_04",
            "child_class": "single_plane_rupture",
            "child_namespace_class": "legacy_04_namespace",
            "required_structure_class": "oq3121_required_direct_children_present",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrong = root / "wrong"
            expected = root / "expected"
            modules, _ = self._fake_modules(wrong)
            with (
                mock.patch.dict(sys.modules, modules, clear=False),
                mock.patch.dict(os.environ, {"OC_OQ_CHECKOUT_ROOT": str(expected)}),
                mock.patch.object(
                    subject.childdiag,
                    "classify_fixed_child_shape",
                    return_value=expected_shape,
                ),
                self.assertRaises(subject.NativeRuptureGateError),
            ):
                subject._native_convert(b"exact-provider-bytes")

    def test_native_converter_rejects_modern_openquake_version(self):
        expected_shape = {
            "root_class": "nrml_root_legacy_04",
            "child_class": "single_plane_rupture",
            "child_namespace_class": "legacy_04_namespace",
            "required_structure_class": "oq3121_required_direct_children_present",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            modules, _ = self._fake_modules(root, version="3.14.0")
            with (
                mock.patch.dict(sys.modules, modules, clear=False),
                mock.patch.dict(os.environ, {"OC_OQ_CHECKOUT_ROOT": str(root)}),
                mock.patch.object(
                    subject.childdiag,
                    "classify_fixed_child_shape",
                    return_value=expected_shape,
                ),
                self.assertRaises(subject.NativeRuptureGateError),
            ):
                subject._native_convert(b"exact-provider-bytes")


if __name__ == "__main__":
    unittest.main()
