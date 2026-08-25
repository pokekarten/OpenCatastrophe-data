# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compose the reconstructed-run compatibility gate with the public OQ3.13 terminal validator.

This offline consumer intentionally adds no new source or scientific authority. It only
permits a labelled reconstructed interoperability result to advance when both already-
reviewed contracts pass: the static compatibility evidence and a canonical terminal-body
contract for the expected trusted-main execution SHA.
"""

from __future__ import annotations

from typing import Any, Mapping

from scripts.validate_eq1_oq313_run_result import validate_terminal_body
from scripts.validate_eq1_reconstructed_run_gate import validate_reconstructed_run_gate

SCHEMA_VERSION = "oc-eq1-reconstructed-terminal-consumer-v1"


class ReconstructedTerminalConsumerError(ValueError):
    pass


def validate_reconstructed_terminal(
    terminal_body: object,
    *,
    expected_execution_sha: str,
    compatibility_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate both closed contracts and return a non-promoting consumer disposition."""

    gate = validate_reconstructed_run_gate(compatibility_evidence)
    if gate.get("run_may_proceed") is not True:
        raise ReconstructedTerminalConsumerError("reconstructed compatibility gate did not pass")

    terminal = validate_terminal_body(
        terminal_body,
        expected_execution_sha=expected_execution_sha,
    )

    terminal_pass = (
        terminal.get("declared_terminal_status") == "pass"
        and terminal.get("numerical_receipt_emitted") is True
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_label": gate["run_label"],
        "declared_execution_sha": expected_execution_sha,
        "compatibility_gate_validated": True,
        "terminal_body_contract_validated": True,
        "terminal_pass": terminal_pass,
        "reconstructed_reference_result_consumable": terminal_pass,
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
