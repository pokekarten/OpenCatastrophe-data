# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import validate_eq1_reconstructed_value_basis_terminal as subject


class ReconstructedValueBasisTerminalConsumerTests(unittest.TestCase):
    def _value_basis(self):
        return {
            "schema_version": "oc-eq1-reconstructed-value-basis-gate-v1",
            "run_label": "reconstructed_component_interoperability",
            "run_may_proceed": True,
            "bounded_value_basis_relation_verified": True,
            "source_runtime_exact_equivalence_verified": False,
            "source_runtime_transform_verified": False,
            "insured_value_semantics_verified": False,
            "faithful_esrm20_reproduction_verified": False,
            "component_compatibility_verified": False,
            "component_conversion_authorized": False,
            "historical_environment_verified": False,
            "numerical_hazard_agreement_verified": False,
            "scientific_validity_verified": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def _real_value_basis_evidence(self):
        return {
            "compatibility": {
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
            },
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

    def _terminal(self, *, terminal_pass=True, consumable=True):
        return {
            "schema_version": "oc-eq1-reconstructed-terminal-consumer-v1",
            "run_label": "reconstructed_component_interoperability",
            "declared_execution_sha": "a" * 40,
            "compatibility_gate_validated": True,
            "terminal_body_contract_validated": True,
            "terminal_pass": terminal_pass,
            "reconstructed_reference_result_consumable": consumable,
            "trusted_origin_required": True,
            "github_comment_origin_authenticated": False,
            "faithful_esrm20_reproduction_verified": False,
            "component_compatibility_verified": False,
            "component_conversion_authorized": False,
            "historical_environment_verified": False,
            "numerical_hazard_agreement_verified": False,
            "numerical_reference_loss_verified": False,
            "independent_validation_established": False,
            "scientific_validity_verified": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def test_pass_requires_value_basis_and_terminal_and_keeps_authority_ceiling(self):
        compatibility = {"compatibility": "evidence"}
        evidence = {"compatibility": compatibility}
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=self._terminal(),
            ) as terminal,
        ):
            result = subject.validate_reconstructed_value_basis_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                value_basis_evidence=evidence,
            )

        terminal.assert_called_once_with(
            "terminal",
            expected_execution_sha="a" * 40,
            compatibility_evidence=compatibility,
        )
        self.assertTrue(result["value_basis_gate_validated"])
        self.assertTrue(result["bounded_value_basis_relation_verified"])
        self.assertTrue(result["terminal_pass"])
        self.assertTrue(result["reconstructed_reference_result_consumable"])
        for field in (
            "github_comment_origin_authenticated",
            "source_runtime_exact_equivalence_verified",
            "source_runtime_transform_verified",
            "insured_value_semantics_verified",
            "faithful_esrm20_reproduction_verified",
            "component_compatibility_verified",
            "component_conversion_authorized",
            "historical_environment_verified",
            "numerical_hazard_agreement_verified",
            "numerical_reference_loss_verified",
            "independent_validation_established",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_real_value_basis_gate_is_composed_before_terminal_consumer(self):
        evidence = self._real_value_basis_evidence()
        with mock.patch.object(
            subject,
            "validate_reconstructed_terminal",
            return_value=self._terminal(),
        ) as terminal:
            result = subject.validate_reconstructed_value_basis_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                value_basis_evidence=evidence,
            )

        terminal.assert_called_once_with(
            "terminal",
            expected_execution_sha="a" * 40,
            compatibility_evidence=evidence["compatibility"],
        )
        self.assertTrue(result["bounded_value_basis_relation_verified"])

    def test_value_basis_failure_short_circuits_terminal_consumer(self):
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                side_effect=ValueError("value-basis drift"),
            ),
            mock.patch.object(subject, "validate_reconstructed_terminal") as terminal,
        ):
            with self.assertRaisesRegex(ValueError, "value-basis drift"):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )
        terminal.assert_not_called()

    def test_blocked_terminal_is_valid_but_not_consumable(self):
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=self._terminal(terminal_pass=False, consumable=False),
            ),
        ):
            result = subject.validate_reconstructed_value_basis_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                value_basis_evidence={"compatibility": {}},
            )

        self.assertFalse(result["terminal_pass"])
        self.assertFalse(result["reconstructed_reference_result_consumable"])

    def test_run_label_drift_fails_closed(self):
        terminal_result = self._terminal()
        terminal_result["run_label"] = "different-run"
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=terminal_result,
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "run labels disagree",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )

    def test_value_basis_authority_uplift_fails_closed(self):
        value_basis = self._value_basis()
        value_basis["source_runtime_transform_verified"] = True
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=value_basis,
            ),
            mock.patch.object(subject, "validate_reconstructed_terminal") as terminal,
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "value-basis authority ceiling drifted",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )
        terminal.assert_not_called()

    def test_terminal_authority_uplift_fails_closed(self):
        terminal_result = self._terminal()
        terminal_result["publication_authorized"] = True
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=terminal_result,
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "terminal authority ceiling drifted",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )

    def test_terminal_execution_sha_must_match_requested_execution(self):
        terminal_result = self._terminal()
        terminal_result["declared_execution_sha"] = "b" * 40
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=terminal_result,
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "execution SHA disagrees",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )

    def test_terminal_must_preserve_trusted_origin_precondition(self):
        terminal_result = self._terminal()
        terminal_result["trusted_origin_required"] = False
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=terminal_result,
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "trusted-origin precondition drifted",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )

    def test_terminal_pass_and_consumable_types_must_be_boolean(self):
        terminal_result = self._terminal()
        terminal_result["terminal_pass"] = "blocked"
        terminal_result["reconstructed_reference_result_consumable"] = False
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=terminal_result,
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "types drifted",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )

    def test_terminal_pass_and_consumable_must_agree(self):
        with (
            mock.patch.object(
                subject,
                "validate_reconstructed_value_basis_gate",
                return_value=self._value_basis(),
            ),
            mock.patch.object(
                subject,
                "validate_reconstructed_terminal",
                return_value=self._terminal(terminal_pass=True, consumable=False),
            ),
        ):
            with self.assertRaisesRegex(
                subject.ReconstructedValueBasisTerminalConsumerError,
                "pass/consumable disposition drifted",
            ):
                subject.validate_reconstructed_value_basis_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    value_basis_evidence={"compatibility": {}},
                )


if __name__ == "__main__":
    unittest.main()
