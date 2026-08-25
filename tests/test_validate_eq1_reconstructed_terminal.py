# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import validate_eq1_reconstructed_terminal as subject


class ReconstructedTerminalConsumerTests(unittest.TestCase):
    def _gate(self):
        return {
            "schema_version": "oc-eq1-reconstructed-run-gate-v1",
            "run_label": "reconstructed_component_interoperability",
            "run_may_proceed": True,
            "faithful_esrm20_reproduction_verified": False,
            "component_compatibility_verified": False,
            "component_conversion_authorized": False,
            "historical_environment_verified": False,
            "numerical_hazard_agreement_verified": False,
            "scientific_validity_verified": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def _terminal(self, *, status="pass", emitted=True):
        return {
            "validation_scope": "terminal_body_contract_only",
            "body_contract_validated": True,
            "trusted_origin_required": True,
            "github_comment_origin_authenticated": False,
            "origin_precondition": "canonical_public_issue_609_github_actions_bot_or_separately_trusted_channel",
            "adapter_provenance_independently_verified": False,
            "declared_execution_sha": "a" * 40,
            "declared_terminal_status": status,
            "numerical_receipt_emitted": emitted,
            "external_provider_bytes_persisted": False,
            "historical_reproduction_verified": False,
            "numerical_reference_loss_verified": False,
            "independent_validation_established": False,
            "scientific_validity_verified": False,
            "publication_authorized": False,
            "model_use_authorized": False,
            "oq_datastore_persisted": False,
        }

    def test_pass_requires_both_closed_contracts_and_keeps_authority_ceiling(self):
        with (
            mock.patch.object(subject, "validate_reconstructed_run_gate", return_value=self._gate()),
            mock.patch.object(subject, "validate_terminal_body", return_value=self._terminal()),
        ):
            result = subject.validate_reconstructed_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                compatibility_evidence={},
            )

        self.assertTrue(result["compatibility_gate_validated"])
        self.assertTrue(result["terminal_body_contract_validated"])
        self.assertTrue(result["terminal_pass"])
        self.assertTrue(result["reconstructed_reference_result_consumable"])
        for field in (
            "github_comment_origin_authenticated",
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

    def test_blocked_terminal_is_valid_but_not_consumable(self):
        with (
            mock.patch.object(subject, "validate_reconstructed_run_gate", return_value=self._gate()),
            mock.patch.object(
                subject,
                "validate_terminal_body",
                return_value=self._terminal(status="blocked", emitted=False),
            ),
        ):
            result = subject.validate_reconstructed_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                compatibility_evidence={},
            )

        self.assertFalse(result["terminal_pass"])
        self.assertFalse(result["reconstructed_reference_result_consumable"])

    def test_compatibility_gate_must_explicitly_authorize_reconstructed_run(self):
        gate = self._gate()
        gate["run_may_proceed"] = False
        with (
            mock.patch.object(subject, "validate_reconstructed_run_gate", return_value=gate),
            mock.patch.object(subject, "validate_terminal_body") as terminal,
        ):
            with self.assertRaisesRegex(subject.ReconstructedTerminalConsumerError, "did not pass"):
                subject.validate_reconstructed_terminal(
                    "terminal",
                    expected_execution_sha="a" * 40,
                    compatibility_evidence={},
                )
        terminal.assert_not_called()

    def test_terminal_without_numerical_receipt_cannot_be_consumed(self):
        with (
            mock.patch.object(subject, "validate_reconstructed_run_gate", return_value=self._gate()),
            mock.patch.object(
                subject,
                "validate_terminal_body",
                return_value=self._terminal(status="pass", emitted=False),
            ),
        ):
            result = subject.validate_reconstructed_terminal(
                "terminal",
                expected_execution_sha="a" * 40,
                compatibility_evidence={},
            )
        self.assertFalse(result["reconstructed_reference_result_consumable"])


if __name__ == "__main__":
    unittest.main()
