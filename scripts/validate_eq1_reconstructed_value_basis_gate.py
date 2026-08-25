# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed value-basis gate for the reconstructed EQ1 reference run."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.validate_eq1_reconstructed_run_gate import (
    validate_reconstructed_run_gate,
)

SCHEMA_VERSION = "oc-eq1-reconstructed-value-basis-gate-v1"
EXPECTED_RUNTIME_COST = {
    "name": "structural",
    "type": "aggregated",
    "unit": "EUR",
}
EXPECTED_SOURCE_VALUE_BASIS = "TOTAL_REPL_COST_EUR"
EXPECTED_SOURCE_VALUE_BASIS_YEAR = 2020
EXPECTED_RECORD_COUNT = 1093
EXPECTED_EXACT_VALUE_COUNT = 1051
EXPECTED_NON_EQUAL_VALUE_COUNT = 42
EXPECTED_MAX_ABS_DIFFERENCE = "0.000000004"
EXPECTED_VULNERABILITY_LOSS_CATEGORY = "structural"
EXPECTED_VULNERABILITY_RESPONSE_BASIS = "total_replacement_cost"


class ReconstructedValueBasisGateError(ValueError):
    """Raised when reconstructed-run value-basis evidence drifts."""


def _require_exact_int(value: object, expected: int, label: str) -> None:
    if type(value) is not int or value != expected:
        raise ReconstructedValueBasisGateError(f"{label} evidence drifted")


def validate_reconstructed_value_basis_gate(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    """Compose runtime compatibility with the bounded exposure/value relation."""

    required = {
        "compatibility",
        "runtime_exposure_cost",
        "source_value_basis",
        "source_value_basis_year",
        "source_runtime_record_count",
        "source_runtime_exact_value_count",
        "source_runtime_non_equal_value_count",
        "source_runtime_max_abs_difference",
        "source_runtime_transform_verified",
        "vulnerability_loss_category",
        "vulnerability_response_basis",
        "insured_value_semantics_verified",
    }
    if type(document) is not dict or set(document) != required:
        raise ReconstructedValueBasisGateError("value-basis evidence fields drifted")

    compatibility = validate_reconstructed_run_gate(document["compatibility"])
    if compatibility.get("run_may_proceed") is not True:
        raise ReconstructedValueBasisGateError(
            "reconstructed-run compatibility gate did not pass"
        )

    if document["runtime_exposure_cost"] != EXPECTED_RUNTIME_COST:
        raise ReconstructedValueBasisGateError("runtime exposure cost basis drifted")
    if document["source_value_basis"] != EXPECTED_SOURCE_VALUE_BASIS:
        raise ReconstructedValueBasisGateError("source exposure value basis drifted")
    _require_exact_int(
        document["source_value_basis_year"],
        EXPECTED_SOURCE_VALUE_BASIS_YEAR,
        "source value-basis year",
    )
    _require_exact_int(
        document["source_runtime_record_count"],
        EXPECTED_RECORD_COUNT,
        "source/runtime record count",
    )
    _require_exact_int(
        document["source_runtime_exact_value_count"],
        EXPECTED_EXACT_VALUE_COUNT,
        "source/runtime exact-value count",
    )
    _require_exact_int(
        document["source_runtime_non_equal_value_count"],
        EXPECTED_NON_EQUAL_VALUE_COUNT,
        "source/runtime non-equal-value count",
    )
    if document["source_runtime_max_abs_difference"] != EXPECTED_MAX_ABS_DIFFERENCE:
        raise ReconstructedValueBasisGateError(
            "source/runtime maximum absolute difference drifted"
        )
    if document["source_runtime_transform_verified"] is not False:
        raise ReconstructedValueBasisGateError(
            "unproved source/runtime transform authority is forbidden"
        )
    if (
        document["vulnerability_loss_category"]
        != EXPECTED_VULNERABILITY_LOSS_CATEGORY
        or document["vulnerability_response_basis"]
        != EXPECTED_VULNERABILITY_RESPONSE_BASIS
    ):
        raise ReconstructedValueBasisGateError(
            "vulnerability total-replacement-cost basis drifted"
        )
    if document["insured_value_semantics_verified"] is not False:
        raise ReconstructedValueBasisGateError(
            "insured-value semantics remain outside the reconstructed run"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_label": compatibility["run_label"],
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
