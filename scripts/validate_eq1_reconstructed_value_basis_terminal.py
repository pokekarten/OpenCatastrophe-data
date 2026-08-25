# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compose the EQ1 reconstructed value-basis gate with the terminal consumer.

This additive offline consumer preserves the existing reconstructed-terminal v1 contract.
It only permits a reconstructed reference result to be consumed when the already-reviewed
value-basis gate and reconstructed terminal consumer both pass for the same nested
compatibility evidence. No source/runtime equivalence, insured-value, scientific,
publication, or model-use authority is added.
"""

from __future__ import annotations

from typing import Any, Mapping

from scripts.validate_eq1_reconstructed_terminal import validate_reconstructed_terminal
from scripts.validate_eq1_reconstructed_value_basis_gate import (
    validate_reconstructed_value_basis_gate,
)

SCHEMA_VERSION = "oc-eq1-reconstructed-value-basis-terminal-consumer-v1"

_VALUE_BASIS_FALSE_CEILINGS = (
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
)

_TERMINAL_FALSE_CEILINGS = (
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
)


class ReconstructedValueBasisTerminalConsumerError(ValueError):
    """Raised when the composed reconstructed-terminal evidence drifts."""


def _require_false_ceiling(
    result: Mapping[str, Any], fields: tuple[str, ...], label: str
) -> None:
    for field in fields:
        if result.get(field) is not False:
            raise ReconstructedValueBasisTerminalConsumerError(
                f"{label} authority ceiling drifted: {field}"
            )


def validate_reconstructed_value_basis_terminal(
    terminal_body: object,
    *,
    expected_execution_sha: str,
    value_basis_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Require the bounded value-basis relation before consuming a terminal result."""

    value_basis = validate_reconstructed_value_basis_gate(value_basis_evidence)
    if (
        value_basis.get("run_may_proceed") is not True
        or value_basis.get("bounded_value_basis_relation_verified") is not True
    ):
        raise ReconstructedValueBasisTerminalConsumerError(
            "reconstructed value-basis gate did not pass"
        )
    _require_false_ceiling(
        value_basis,
        _VALUE_BASIS_FALSE_CEILINGS,
        "value-basis",
    )

    terminal = validate_reconstructed_terminal(
        terminal_body,
        expected_execution_sha=expected_execution_sha,
        compatibility_evidence=value_basis_evidence["compatibility"],
    )
    if (
        terminal.get("compatibility_gate_validated") is not True
        or terminal.get("terminal_body_contract_validated") is not True
    ):
        raise ReconstructedValueBasisTerminalConsumerError(
            "reconstructed terminal consumer did not validate both contracts"
        )
    _require_false_ceiling(terminal, _TERMINAL_FALSE_CEILINGS, "terminal")

    if terminal.get("run_label") != value_basis.get("run_label"):
        raise ReconstructedValueBasisTerminalConsumerError(
            "reconstructed run labels disagree"
        )

    terminal_pass = terminal.get("terminal_pass") is True
    terminal_consumable = (
        terminal.get("reconstructed_reference_result_consumable") is True
    )
    if terminal_pass != terminal_consumable:
        raise ReconstructedValueBasisTerminalConsumerError(
            "terminal pass/consumable disposition drifted"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_label": value_basis["run_label"],
        "declared_execution_sha": expected_execution_sha,
        "value_basis_gate_validated": True,
        "bounded_value_basis_relation_verified": True,
        "compatibility_gate_validated": True,
        "terminal_body_contract_validated": True,
        "terminal_pass": terminal_pass,
        "reconstructed_reference_result_consumable": terminal_consumable,
        "trusted_origin_required": True,
        "github_comment_origin_authenticated": False,
        "source_runtime_exact_equivalence_verified": False,
        "source_runtime_transform_verified": False,
        "insured_value_semantics_verified": False,
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
