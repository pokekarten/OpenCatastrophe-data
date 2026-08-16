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
    argument_keys = list(subject.EXPECTED_SOURCE_ARGUMENT_KEYS)
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
        key = argument_keys[index % len(argument_keys)]
        rows.append(
            {
                "branch_set_id": f"bs-{index // 20}",
                "branch_id": f"b-{index}",
                "requested_gsim_token": token,
                "argument_keys": [key],
                "alias_expansion_applied": token != resolved[token],
                "resolved_gsim_class": resolved[token],
                "runtime_argument_keys_after_alias": [key],
                "constructor_accepted": True,
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
        "status": "pass",
        "target_sha": EXECUTION_SHA,
        "execution_sha": EXECUTION_SHA,
        "execution_container_image_digest": IMAGE_DIGEST,
        "openquake_reference": {"commit": subject.OPENQUAKE_COMMIT},
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
        "same_process_runtime_observation_collected": True,
        "executing_environment_matches_reconstructed_reference_recipe_fields": True,
        "gsim_request_reference_recipe_runtime_compatibility_verified": True,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "numerical_hazard_agreement_verified": False,
        "imt_component_unit_compatibility_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class Esrm20RuntimeAdapterTests(unittest.TestCase):
    def _registry(self) -> dict[str, type]:
        return {
            "KothaClass": KothaClass,
            "HydroClass": HydroClass,
            "CratonClass": CratonClass,
            "LanzanoClass": LanzanoClass,
        }

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

    def test_argument_evidence_preserves_canonical_nonempty_source_shape_without_values(self) -> None:
        evidence = subject._gsim_argument_evidence(_branches())
        self.assertEqual(
            evidence["source_argument_keys"], list(subject.EXPECTED_SOURCE_ARGUMENT_KEYS)
        )
        self.assertEqual(
            evidence["runtime_argument_keys_after_alias"],
            list(subject.EXPECTED_SOURCE_ARGUMENT_KEYS),
        )
        self.assertEqual(evidence["external_resource_argument_keys"], [])
        self.assertFalse(evidence["argument_values_returned"])
        self.assertEqual(
            evidence["source_profile_result_comment_id"],
            subject.CANONICAL_PROFILE_RESULT_COMMENT_ID,
        )
        self.assertNotIn("argument_values", evidence)

    def test_argument_evidence_rejects_missing_canonical_key_or_external_resource(self) -> None:
        rows = _branches()
        for row in rows:
            if row["argument_keys"] == ["a"]:
                row["argument_keys"] = []
            if row["runtime_argument_keys_after_alias"] == ["a"]:
                row["runtime_argument_keys_after_alias"] = []
        with self.assertRaisesRegex(
            subject.Esrm20GsimReferenceRuntimeError, "argument-key set drifted"
        ):
            subject._gsim_argument_evidence(rows)

        rows = _branches()
        rows[0]["runtime_argument_keys_after_alias"] = ["coefficient_file"]
        with self.assertRaisesRegex(
            subject.Esrm20GsimReferenceRuntimeError, "external resources"
        ):
            subject._gsim_argument_evidence(rows)

    def test_site_requirement_evidence_is_derived_only_from_verified_classes(self) -> None:
        result = _runtime_result()
        evidence = subject._site_parameter_evidence(result, self._registry())
        self.assertEqual(
            evidence["required_site_parameters"],
            ["geology", "slope", "vs30", "vs30measured"],
        )
        self.assertEqual(len(evidence["per_resolved_gsim_class"]), 4)
        self.assertNotIn("coefficients", str(evidence).lower())

    def test_wrapper_preserves_runtime_ceilings_and_adds_argument_and_site_evidence(self) -> None:
        result = _runtime_result()
        with mock.patch.object(subject, "_BASE_RUN_REFERENCE_RUNTIME", return_value=result), mock.patch.object(
            subject._gate,
            "_load_verified_openquake_runtime",
            return_value=SimpleNamespace(registry=self._registry()),
        ):
            output = subject.run_reference_runtime(
                execution_sha=EXECUTION_SHA,
                image_digest=IMAGE_DIGEST,
            )
        self.assertEqual(output["schema_version"], subject.SCHEMA_VERSION)
        self.assertEqual(output["source_issue"], 493)
        self.assertEqual(
            output["source_profile_result_comment_id"], 5310194089
        )
        self.assertEqual(output["requested_gsim_tokens"], list(subject.EXPECTED_REQUESTED_TOKENS))
        self.assertEqual(
            output["gsim_argument_evidence"]["source_argument_keys"],
            list(subject.EXPECTED_SOURCE_ARGUMENT_KEYS),
        )
        self.assertFalse(output["gsim_argument_evidence"]["argument_values_returned"])
        self.assertTrue(output["site_parameter_requirements_derived"])
        self.assertEqual(
            output["site_parameter_requirements"]["required_site_parameters"],
            ["geology", "slope", "vs30", "vs30measured"],
        )
        self.assertTrue(
            output["executing_environment_matches_reconstructed_reference_recipe_fields"]
        )
        self.assertTrue(output["gsim_request_reference_recipe_runtime_compatibility_verified"])
        self.assertFalse(output["historical_environment_verified"])
        self.assertFalse(output["reference_run_verified"])
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
