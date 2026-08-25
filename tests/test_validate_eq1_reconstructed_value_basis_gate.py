# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest

from scripts.validate_eq1_reconstructed_value_basis_gate import (
    ReconstructedValueBasisGateError,
    validate_reconstructed_value_basis_gate,
)


def _compatibility() -> dict[str, object]:
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


def _evidence() -> dict[str, object]:
    return {
        "compatibility": _compatibility(),
        "runtime_exposure_cost": {
            "name": "structural",
            "type": "aggregated",
            "unit": "EUR",
        },
        "source_value_basis": "TOTAL_REPL_COST_EUR",
        "source_value_basis_year": 2020,
        "source_runtime_record_count": 1093,
        "source_runtime_exact_value_count": 1051,
        "source_runtime_non_equal_value_count": 42,
        "source_runtime_max_abs_difference": "0.000000004",
        "source_runtime_transform_verified": False,
        "vulnerability_loss_category": "structural",
        "vulnerability_response_basis": "total_replacement_cost",
        "insured_value_semantics_verified": False,
    }


class ReconstructedValueBasisGateTests(unittest.TestCase):
    def test_accepts_only_bounded_total_replacement_cost_relation(self) -> None:
        result = validate_reconstructed_value_basis_gate(_evidence())

        self.assertTrue(result["run_may_proceed"])
        self.assertTrue(result["bounded_value_basis_relation_verified"])
        for field in (
            "source_runtime_exact_equivalence_verified",
            "source_runtime_transform_verified",
            "insured_value_semantics_verified",
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

    def test_rejects_structural_component_source_basis(self) -> None:
        evidence = _evidence()
        evidence["source_value_basis"] = "COST_STRUCTURAL_EUR"
        with self.assertRaises(ReconstructedValueBasisGateError):
            validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_runtime_cost_contract_drift(self) -> None:
        for field, value in (
            ("name", "TOTAL_REPL_COST_EUR"),
            ("type", "per_area"),
            ("unit", "USD"),
        ):
            evidence = _evidence()
            runtime_cost = dict(evidence["runtime_exposure_cost"])
            runtime_cost[field] = value
            evidence["runtime_exposure_cost"] = runtime_cost
            with self.subTest(field=field):
                with self.assertRaises(ReconstructedValueBasisGateError):
                    validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_decimal_comparison_drift(self) -> None:
        for field, value in (
            ("source_runtime_record_count", 1092),
            ("source_runtime_exact_value_count", 1050),
            ("source_runtime_non_equal_value_count", 43),
            ("source_runtime_max_abs_difference", "0.000000005"),
        ):
            evidence = _evidence()
            evidence[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ReconstructedValueBasisGateError):
                    validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_bool_or_float_integer_evidence(self) -> None:
        for field in (
            "source_value_basis_year",
            "source_runtime_record_count",
            "source_runtime_exact_value_count",
            "source_runtime_non_equal_value_count",
        ):
            for value in (True, float(_evidence()[field])):
                evidence = _evidence()
                evidence[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ReconstructedValueBasisGateError):
                        validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_transform_or_insured_authority_uplift(self) -> None:
        for field in (
            "source_runtime_transform_verified",
            "insured_value_semantics_verified",
        ):
            evidence = _evidence()
            evidence[field] = True
            with self.subTest(field=field):
                with self.assertRaises(ReconstructedValueBasisGateError):
                    validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_vulnerability_value_basis_drift(self) -> None:
        evidence = _evidence()
        evidence["vulnerability_response_basis"] = "structural_component_cost"
        with self.assertRaises(ReconstructedValueBasisGateError):
            validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_failed_reconstructed_compatibility(self) -> None:
        evidence = _evidence()
        compatibility = copy.deepcopy(evidence["compatibility"])
        compatibility["component_conversion_activated"] = True
        evidence["compatibility"] = compatibility
        with self.assertRaises(ValueError):
            validate_reconstructed_value_basis_gate(evidence)

    def test_rejects_unknown_fields(self) -> None:
        evidence = _evidence()
        evidence["tolerance_authorized"] = True
        with self.assertRaises(ReconstructedValueBasisGateError):
            validate_reconstructed_value_basis_gate(evidence)


if __name__ == "__main__":
    unittest.main()
