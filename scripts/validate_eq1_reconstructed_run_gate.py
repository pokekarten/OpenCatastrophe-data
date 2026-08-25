# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed compatibility gate for the first reconstructed EQ1 reference run.

This gate does not claim faithful ESRM20 reproduction. It only accepts the already
reviewed state where IMT identity/unit compatibility and site-parameter sufficiency
are proven, while the vulnerability horizontal-component convention remains unknown.
"""

from __future__ import annotations

from typing import Any, Mapping

SCHEMA_VERSION = "oc-eq1-reconstructed-run-gate-v1"
RUN_LABEL = "reconstructed_component_interoperability"
EXPECTED_IMTS = ["PGA", "SA(0.3)", "SA(0.6)", "SA(1.0)"]
EXPECTED_UNIT = "g"
EXPECTED_NATIVE_COMPONENTS = ["GEOMETRIC_MEAN", "RotD50"]
EXPECTED_SITE_PARAMETERS = ["geology", "region", "slope", "vs30", "xvf"]


class ReconstructedRunGateError(ValueError):
    pass


def validate_reconstructed_run_gate(document: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "hazard_imts",
        "vulnerability_imts",
        "hazard_acceleration_unit",
        "vulnerability_intensity_unit",
        "native_components",
        "component_conversion_activated",
        "vulnerability_horizontal_component",
        "required_site_parameters",
        "site_parameter_sufficiency_verified",
        "historical_environment_verified",
        "numerical_hazard_agreement_verified",
        "scientific_validity_verified",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(document) is not dict or set(document) != required:
        raise ReconstructedRunGateError("compatibility evidence fields drifted")
    if document["hazard_imts"] != EXPECTED_IMTS or document["vulnerability_imts"] != EXPECTED_IMTS:
        raise ReconstructedRunGateError("IMT identity compatibility is not proven")
    if document["hazard_acceleration_unit"] != EXPECTED_UNIT or document["vulnerability_intensity_unit"] != EXPECTED_UNIT:
        raise ReconstructedRunGateError("acceleration unit compatibility is not proven")
    if document["native_components"] != EXPECTED_NATIVE_COMPONENTS:
        raise ReconstructedRunGateError("native component evidence drifted")
    if document["component_conversion_activated"] is not False:
        raise ReconstructedRunGateError("implicit component conversion is forbidden")
    if document["vulnerability_horizontal_component"] != "UNKNOWN":
        raise ReconstructedRunGateError("vulnerability component must remain fail-closed")
    if document["required_site_parameters"] != EXPECTED_SITE_PARAMETERS or document["site_parameter_sufficiency_verified"] is not True:
        raise ReconstructedRunGateError("site/GSIM compatibility is not proven")
    for field in (
        "historical_environment_verified",
        "numerical_hazard_agreement_verified",
        "scientific_validity_verified",
        "publication_authorized",
        "model_use_authorized",
    ):
        if document[field] is not False:
            raise ReconstructedRunGateError(f"authority ceiling widened: {field}")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_label": RUN_LABEL,
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
