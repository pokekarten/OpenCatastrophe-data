# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest

from scripts.validate_eq1_reconstructed_run_gate import (
    ReconstructedRunGateError,
    validate_reconstructed_run_gate,
)


def _evidence():
    return {
        "hazard_imts": ["PGA", "SA(0.3)", "SA(0.6)", "SA(1.0)"],
        "vulnerability_imts": ["PGA", "SA(0.3)", "SA(0.6)", "SA(1.0)"],
        "hazard_acceleration_unit": "g",
        "vulnerability_intensity_unit": "g",
        "native_components": ["GEOMETRIC_MEAN", "RotD50"],
        "component_conversion_activated": False,
        "vulnerability_horizontal_component": "UNKNOWN",
        "required_site_parameters": ["geology", "region", "slope", "vs30", "xvf"],
        "site_parameter_sufficiency_verified": True,
        "historical_environment_verified": False,
        "numerical_hazard_agreement_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class ReconstructedRunGateTests(unittest.TestCase):
    def test_allows_only_labelled_reconstructed_interoperability_run(self):
        result = validate_reconstructed_run_gate(_evidence())
        self.assertTrue(result["run_may_proceed"])
        self.assertEqual(result["run_label"], "reconstructed_component_interoperability")
        for field in (
            "faithful_esrm20_reproduction_verified",
            "component_compatibility_verified",
            "component_conversion_authorized",
            "historical_environment_verified",
            "numerical_hazard_agreement_verified",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_rejects_implicit_component_conversion(self):
        evidence = _evidence()
        evidence["component_conversion_activated"] = True
        with self.assertRaises(ReconstructedRunGateError):
            validate_reconstructed_run_gate(evidence)

    def test_rejects_claimed_vulnerability_component(self):
        evidence = _evidence()
        evidence["vulnerability_horizontal_component"] = "RotD50"
        with self.assertRaises(ReconstructedRunGateError):
            validate_reconstructed_run_gate(evidence)

    def test_rejects_imt_or_unit_drift(self):
        for field, value in (
            ("hazard_imts", ["PGA"]),
            ("hazard_acceleration_unit", "m/s2"),
        ):
            evidence = _evidence()
            evidence[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ReconstructedRunGateError):
                    validate_reconstructed_run_gate(evidence)

    def test_rejects_site_requirement_drift(self):
        evidence = _evidence()
        evidence["required_site_parameters"] = ["vs30"]
        with self.assertRaises(ReconstructedRunGateError):
            validate_reconstructed_run_gate(evidence)

    def test_rejects_authority_uplift(self):
        for field in (
            "historical_environment_verified",
            "numerical_hazard_agreement_verified",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            evidence = _evidence()
            evidence[field] = True
            with self.subTest(field=field):
                with self.assertRaises(ReconstructedRunGateError):
                    validate_reconstructed_run_gate(evidence)

    def test_rejects_unknown_fields(self):
        evidence = copy.deepcopy(_evidence())
        evidence["faithful_esrm20_reproduction_verified"] = True
        with self.assertRaises(ReconstructedRunGateError):
            validate_reconstructed_run_gate(evidence)


if __name__ == "__main__":
    unittest.main()
