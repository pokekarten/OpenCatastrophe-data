# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest

from scripts import validate_eshm20_openquake_runtime as runtime


def reference_packages() -> dict[str, str]:
    contract = runtime.reference_runtime_contract()
    return {
        item["name"]: item["version"]
        for item in contract["requirements_recipe"]["packages"]
    }


def nominal_observation() -> dict[str, object]:
    return {
        "engine_commit": runtime.ENGINE_COMMIT,
        "engine_version": runtime.ENGINE_VERSION,
        "python_version": "3.8.13",
        "platform_system": "Linux",
        "platform_machine": "x86_64",
        "openblas_num_threads": "1",
        "packages": reference_packages(),
        "container_image_digest": None,
    }


class Eshm20OpenQuakeRuntimeTests(unittest.TestCase):
    def test_reference_contract_is_frozen_to_official_v314_sources(self) -> None:
        contract = runtime.reference_runtime_contract()
        self.assertEqual(contract["schema_version"], runtime.SCHEMA_VERSION)
        self.assertEqual(contract["source_issue"], 281)
        self.assertEqual(contract["dataset_id"], "efehr.eshm20")
        self.assertEqual(
            contract["engine"],
            {
                "repository": "gem/oq-engine",
                "tag": "v3.14.0",
                "commit": "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
                "version": "3.14.0",
            },
        )
        self.assertEqual(
            contract["docker_recipe"]["git_blob_sha1"],
            "3f2966d212286e033e38ccd7111c554c7bfa77ce",
        )
        self.assertEqual(contract["docker_recipe"]["base_image_tag"], "python:3.8-slim")
        self.assertIs(contract["docker_recipe"]["base_image_digest_pinned"], False)
        self.assertEqual(
            contract["requirements_recipe"]["git_blob_sha1"],
            "0ebb7e5042cce16005603a3961824797ef72397f",
        )
        self.assertIs(contract["requirements_recipe"]["wheel_sha256_pinned"], False)
        self.assertEqual(
            contract["baselib_reference"]["git_blob_sha1"],
            "a2432f3dacea07537f8b8c851f76a63c1de870c1",
        )
        self.assertEqual(contract["baselib_reference"]["openblas_num_threads"], "1")
        self.assertEqual(len(contract["requirements_recipe"]["packages"]), 32)

    def test_nominal_observation_reduces_to_bounded_reference_evidence(self) -> None:
        reduced = runtime.validate_runtime_observation(nominal_observation())
        self.assertIs(reduced["reference_recipe_match"], True)
        self.assertEqual(reduced["observation"]["python_version"], "3.8.13")
        self.assertEqual(len(reduced["observation"]["packages"]), 32)
        self.assertIs(reduced["observed_container_digest_recorded"], False)
        for field in (
            "historical_environment_verified",
            "reference_base_image_byte_identity_verified",
            "wheel_byte_identity_verified",
            "benchmark_execution_authorized",
            "model_use_authorized",
            "publication_authorized",
        ):
            self.assertIs(reduced[field], False, field)

    def test_package_input_order_does_not_change_output(self) -> None:
        first = nominal_observation()
        second = nominal_observation()
        second["packages"] = dict(reversed(list(second["packages"].items())))
        self.assertEqual(
            runtime.validate_runtime_observation(first),
            runtime.validate_runtime_observation(second),
        )

    def test_engine_python_platform_and_thread_drift_fail_closed(self) -> None:
        mutations = (
            ("engine_commit", "a" * 40),
            ("engine_version", "3.14.1"),
            ("python_version", "3.9.0"),
            ("platform_system", "Darwin"),
            ("platform_machine", "aarch64"),
            ("openblas_num_threads", "2"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                observation = nominal_observation()
                observation[field] = value
                with self.assertRaises(runtime.ReferenceRuntimeError):
                    runtime.validate_runtime_observation(observation)

    def test_python_version_is_strict_but_patch_component_is_observational(self) -> None:
        for accepted in ("3.8", "3.8.0", "3.8.19"):
            with self.subTest(accepted=accepted):
                observation = nominal_observation()
                observation["python_version"] = accepted
                reduced = runtime.validate_runtime_observation(observation)
                self.assertEqual(reduced["observation"]["python_version"], accepted)

        for rejected in ("3.80", "3.8.x", " 3.8", 3.8, True):
            with self.subTest(rejected=rejected):
                observation = nominal_observation()
                observation["python_version"] = rejected
                with self.assertRaises(runtime.ReferenceRuntimeError):
                    runtime.validate_runtime_observation(observation)

    def test_package_set_version_and_key_ambiguity_fail_closed(self) -> None:
        missing = nominal_observation()
        missing["packages"].pop("numpy")

        extra = nominal_observation()
        extra["packages"]["unknown-package"] = "1.0.0"

        wrong = nominal_observation()
        wrong["packages"]["scipy"] = "1.7.4"

        noncanonical = nominal_observation()
        noncanonical["packages"].pop("numpy")
        noncanonical["packages"]["NumPy"] = "1.20.0"

        duplicate_normalized = nominal_observation()
        duplicate_normalized["packages"]["NumPy"] = "1.20.0"

        bad_type = nominal_observation()
        bad_type["packages"]["numpy"] = True

        for label, observation in (
            ("missing", missing),
            ("extra", extra),
            ("wrong", wrong),
            ("noncanonical", noncanonical),
            ("duplicate_normalized", duplicate_normalized),
            ("bad_type", bad_type),
        ):
            with self.subTest(label=label):
                with self.assertRaises(runtime.ReferenceRuntimeError):
                    runtime.validate_runtime_observation(observation)

    def test_bool_int_and_outer_shape_confusion_fail_closed(self) -> None:
        observation = nominal_observation()
        observation["openblas_num_threads"] = 1
        with self.assertRaises(runtime.ReferenceRuntimeError):
            runtime.validate_runtime_observation(observation)

        observation = nominal_observation()
        observation["container_image_digest"] = False
        with self.assertRaises(runtime.ReferenceRuntimeError):
            runtime.validate_runtime_observation(observation)

        observation = nominal_observation()
        observation["unexpected"] = False
        with self.assertRaises(runtime.ReferenceRuntimeError):
            runtime.validate_runtime_observation(observation)

        with self.assertRaises(runtime.ReferenceRuntimeError):
            runtime.validate_runtime_observation([])

    def test_observed_container_digest_is_recorded_but_not_promoted(self) -> None:
        observation = nominal_observation()
        digest = "sha256:" + "a" * 64
        observation["container_image_digest"] = digest
        reduced = runtime.validate_runtime_observation(observation)
        self.assertEqual(reduced["observation"]["container_image_digest"], digest)
        self.assertIs(reduced["observed_container_digest_recorded"], True)
        self.assertIs(reduced["reference_base_image_byte_identity_verified"], False)
        self.assertIs(reduced["historical_environment_verified"], False)

        for malformed in (
            "a" * 64,
            "sha256:" + "A" * 64,
            "sha256:" + "a" * 63,
            "sha512:" + "a" * 64,
            1,
        ):
            with self.subTest(malformed=malformed):
                bad = nominal_observation()
                bad["container_image_digest"] = malformed
                with self.assertRaises(runtime.ReferenceRuntimeError):
                    runtime.validate_runtime_observation(bad)

    def test_reference_contract_returns_fresh_mutable_copies(self) -> None:
        first = runtime.reference_runtime_contract()
        second = runtime.reference_runtime_contract()
        first["requirements_recipe"]["packages"].append({"name": "bad", "version": "1"})
        self.assertEqual(len(second["requirements_recipe"]["packages"]), 32)


if __name__ == "__main__":
    unittest.main()
