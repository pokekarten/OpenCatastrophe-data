# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for EBRISK dependency acquisition production authority."""

from __future__ import annotations

import unittest
from unittest import mock

from scripts import acquire_esrm20_ebrisk_risk_config_dependencies as worker
from scripts import verify_esrm20_ebrisk_risk_config_dependencies as bridge


class EbriskDependencyAcquisitionAuthorityTests(unittest.TestCase):
    def test_spec_map_value_mutation_fails_before_acquisition(self) -> None:
        original = bridge._SPEC_BY_KEY["group1"]
        forged = bridge.ConfigSpec(
            key=original.key,
            operation_id="forged-operation",
            repository_path="Configuration_files/config_ebrisk_Group2.ini",
            byte_count=2832,
            sha256="80cf566003cdb5e12dde820d5cba3db8ea5a6ba2db31e7089f3453f921852625",
        )
        with mock.patch.dict(bridge._SPEC_BY_KEY, {"group1": forged}, clear=False):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "spec-map values drifted",
            ):
                worker._require_production_identity()

    def test_spec_map_rebinding_fails_before_acquisition(self) -> None:
        rebound = dict(bridge._SPEC_BY_KEY)
        self.assertIsNot(rebound, bridge._SPEC_BY_KEY)
        with mock.patch.object(bridge, "_SPEC_BY_KEY", rebound):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "spec map drifted",
            ):
                worker._require_production_identity()

    def test_inner_payload_verifier_rebinding_fails_before_acquisition(self) -> None:
        forged = lambda payload, spec: spec.sha256
        with mock.patch.object(bridge, "_verify_payload_identity", forged):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "payload verifier drifted",
            ):
                worker._require_production_identity()

    def test_inner_dependency_parser_rebinding_fails_before_acquisition(self) -> None:
        forged = lambda config_text, *, repository_path: []
        with mock.patch.object(
            bridge,
            "extract_dependencies_from_verified_text",
            forged,
        ):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "dependency parser bridge drifted",
            ):
                worker._require_production_identity()

    def test_openquake_parser_rebinding_fails_before_acquisition(self) -> None:
        forged = lambda config_text, *, config_path: []
        with mock.patch.object(
            bridge,
            "extract_openquake_config_references",
            forged,
        ):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "OpenQuake dependency parser drifted",
            ):
                worker._require_production_identity()

    def test_sha256_rebinding_fails_before_acquisition(self) -> None:
        forged = lambda payload=b"": None
        with mock.patch.object(bridge.hashlib, "sha256", forged):
            with self.assertRaisesRegex(
                worker.EbriskDependencyAcquisitionError,
                "SHA-256 authority drifted",
            ):
                worker._require_production_identity()


if __name__ == "__main__":
    unittest.main()
