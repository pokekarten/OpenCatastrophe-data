# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from scripts import acquire_eshm20_gsim_resource_profile as gmm
from scripts import run_eshm20_gsim_reference_runtime as base_runtime
from scripts import run_esrm20_gsim_reference_runtime as subject

EXECUTION_SHA = "1" * 40
IMAGE_DIGEST = "sha256:" + "a" * 64


class KothaClass:
    REQUIRES_SITES_PARAMETERS = frozenset({"vs30", "vs30measured", "slope", "geology"})


class HydroClass:
    REQUIRES_SITES_PARAMETERS = frozenset({"vs30"})


class CratonClass:
    REQUIRES_SITES_PARAMETERS = frozenset({"vs30"})


class LanzanoClass:
    REQUIRES_SITES_PARAMETERS = frozenset({"vs30"})


def _branches() -> list[dict[str, object]]:
    tokens = list(subject.EXPECTED_REQUESTED_TOKENS)
    resolved = {
        "BCHydroESHM20SInter": "HydroClass",
        "BCHydroESHM20SSlab": "HydroClass",
        "ESHM20Craton": "CratonClass",
        "KothaEtAl2020ESHM20SlopeGeology": "KothaClass",
        "LanzanoLuzi2019shallow": "LanzanoClass",
    }
    rows: list[dict[str, object]] = []
    for index in range(subject.EXPECTED_BRANCH_COUNT):
        token = tokens[index % len(tokens)]
        rows.append(
            {
                "branch_set_id": f"bs-{index // 20}",
                "branch_id": f"b-{index}",
                "requested_gsim_token": token,
                "argument_keys": [],
                "alias_expanded": token != resolved[token],
                "resolved_gsim_class": resolved[token],
                "runtime_argument_keys_after_alias": [],
                "registry_contains_class": True,
                "constructor_succeeded": True,
            }
        )
    return rows


def _runtime_result() -> dict[str, object]:
    rows = _branches()
    classes = sorted({str(row["resolved_gsim_class"]) for row in rows})
    return {
        "schema_version": base_runtime.SCHEMA_VERSION,
        "source_issue": base_runtime.SOURCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "execution_sha": EXECUTION_SHA,
        "openquake_reference": {"commit": subject.OPENQUAKE_COMMIT},
        "runtime_observation": {"image_digest": IMAGE_DIGEST},
        "gmm_identity": {
            "project_id": subject.PROJECT_ID,
            "project_path": subject.PROJECT_PATH,
            "commit_sha": subject.COMMIT_SHA,
            "repository_path": subject.REPOSITORY_PATH,
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
        },
        "branch_count": subject.EXPECTED_BRANCH_COUNT,
        "unique_resolved_gsim_classes": classes,
        "branches": rows,
        "reconstructed_reference_recipe_verified": True,
        "gsim_alias_registry_constructor_compatible": True,
        "historical_environment_identity_proven": False,
        "numerical_hazard_agreement_verified": False,
        "full_reference_run_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class Esrm20RuntimeAdapterTests(unittest.TestCase):
    def test_binding_is_scoped_and_restores_existing_eshm20_constants(self) -> None:
        original = (
            gmm.DATASET_ID,
            gmm.PROJECT_ID,
            gmm.COMMIT_SHA,
            gmm.REPOSITORY_PATH,
            base_runtime.SOURCE_ISSUE,
            base_runtime.REQUEST_MARKER,
        )
        with subject.esrm20_binding():
            subject.assert_esrm20_binding()
            self.assertEqual(gmm.DATASET_ID, subject.DATASET_ID)
            self.assertEqual(gmm.PROJECT_ID, subject.PROJECT_ID)
            self.assertEqual(base_runtime.SOURCE_ISSUE, subject.SOURCE_ISSUE)
            self.assertEqual(base_runtime.REQUEST_MARKER, subject.REQUEST_MARKER)
        restored = (
            gmm.DATASET_ID,
            gmm.PROJECT_ID,
            gmm.COMMIT_SHA,
            gmm.REPOSITORY_PATH,
            base_runtime.SOURCE_ISSUE,
            base_runtime.REQUEST_MARKER,
        )
        self.assertEqual(restored, original)

    def test_site_requirement_evidence_is_derived_only_from_verified_classes(self) -> None:
        result = _runtime_result()
        registry = {
            "KothaClass": KothaClass,
            "HydroClass": HydroClass,
            "CratonClass": CratonClass,
            "LanzanoClass": LanzanoClass,
        }
        evidence = subject._site_parameter_evidence(result, registry)
        self.assertEqual(
            evidence["required_site_parameters"],
            ["geology", "slope", "vs30", "vs30measured"],
        )
        self.assertEqual(len(evidence["per_resolved_gsim_class"]), 4)
        self.assertNotIn("coefficients", str(evidence).lower())

    def test_site_requirement_evidence_rejects_source_or_alias_argument_widening(self) -> None:
        registry = {
            "KothaClass": KothaClass,
            "HydroClass": HydroClass,
            "CratonClass": CratonClass,
            "LanzanoClass": LanzanoClass,
        }
        result = _runtime_result()
        result["branches"][0]["argument_keys"] = ["gmpe_table"]
        with self.assertRaisesRegex(subject.Esrm20GsimReferenceRuntimeError, "unexpectedly requires"):
            subject._site_parameter_evidence(result, registry)

        result = _runtime_result()
        result["branches"][0]["runtime_argument_keys_after_alias"] = ["gmpe_table"]
        with self.assertRaisesRegex(subject.Esrm20GsimReferenceRuntimeError, "alias expansion"):
            subject._site_parameter_evidence(result, registry)

    def test_wrapper_preserves_false_scientific_ceilings_and_adds_site_requirements(self) -> None:
        result = _runtime_result()
        registry = {
            "KothaClass": KothaClass,
            "HydroClass": HydroClass,
            "CratonClass": CratonClass,
            "LanzanoClass": LanzanoClass,
        }
        with mock.patch.object(subject, "_BASE_RUN_REFERENCE_RUNTIME", return_value=result), mock.patch.object(
            subject._gate,
            "_load_verified_openquake_runtime",
            return_value=SimpleNamespace(registry=registry),
        ):
            output = subject.run_reference_runtime(
                execution_sha=EXECUTION_SHA,
                image_digest=IMAGE_DIGEST,
            )
        self.assertEqual(output["schema_version"], subject.SCHEMA_VERSION)
        self.assertEqual(output["source_issue"], 493)
        self.assertEqual(output["requested_gsim_tokens"], list(subject.EXPECTED_REQUESTED_TOKENS))
        self.assertTrue(output["site_parameter_requirements_derived"])
        self.assertEqual(
            output["site_parameter_requirements"]["required_site_parameters"],
            ["geology", "slope", "vs30", "vs30measured"],
        )
        self.assertFalse(output["site_model_compatibility_verified"])
        self.assertFalse(output["imt_component_unit_compatibility_verified"])
        self.assertFalse(output["numerical_hazard_agreement_verified"])
        self.assertFalse(output["full_hazard_compatibility_verified"])
        self.assertFalse(output["model_use_authorized"])

    def test_request_validation_uses_esrm20_outer_identity_without_persisting_binding(self) -> None:
        body = subject.REQUEST_MARKER + "\n" + (
            '{"schema_version":"%s","issue":493,"target_sha":"%s","requester":"unit-test"}'
            % (subject.REQUEST_SCHEMA_VERSION, EXECUTION_SHA)
        )
        original_issue = base_runtime.SOURCE_ISSUE
        parsed = subject.validate_request(
            body, expected_issue=493, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["issue"], 493)
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        self.assertEqual(base_runtime.SOURCE_ISSUE, original_issue)


if __name__ == "__main__":
    unittest.main()
