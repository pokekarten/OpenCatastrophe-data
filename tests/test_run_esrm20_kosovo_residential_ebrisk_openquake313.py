# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


def derived_config() -> bytes:
    return b"""[general]
calculation_mode = ebrisk
ignore_master_seed = true
minimum_asset_loss = {'structural': 2000}
random_seed = 113

[exposure]
exposure_file = ../Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml

[site_params]
site_model_file = ../Vs30/Site_model_Kosovo.xml
"""


def config_evidence(payload: bytes) -> dict[str, object]:
    return {
        "output": {
            "logical_path": subject.CONFIG_LOGICAL_PATH,
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "experiment_label": subject.EXPERIMENT_LABEL,
        "scope": subject.SCOPE,
        "full_semantic_diff_verified": True,
        "runtime_settings_preserved": True,
        "minimum_asset_loss_structural_preserved": True,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "vulnerability_horizontal_component_verified": False,
        "horizontal_component_conversion_authorized": False,
        "numerical_loss_reproduction_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def runtime_identity() -> dict[str, object]:
    return {
        "repository": subject.OPENQUAKE_REPOSITORY,
        "commit_sha": subject.OPENQUAKE_COMMIT_SHA,
        "openquake_version": subject.OPENQUAKE_SOURCE_VERSION,
        "python_major_minor": subject.PYTHON_MAJOR_MINOR,
        "dependency_versions": dict(subject.EXPECTED_DEPENDENCY_VERSIONS),
        "source_commit_verified": True,
        "bootstrap_image_digest": "sha256:" + "1" * 64,
        "execution_image_id": "sha256:" + "2" * 64,
    }


def resolved_runtime(*, concurrent_tasks: int = 0) -> dict[str, object]:
    return {
        "calculation_mode": "ebrisk",
        "random_seed": subject.RANDOM_SEED,
        "random_seed_provenance": "source_declared",
        "ignore_master_seed": True,
        "ignore_master_seed_provenance": "source_declared",
        "ses_seed": subject.OPENQUAKE_DEFAULT_SES_SEED,
        "ses_seed_provenance": "openquake_default_resolved_from_source_absence",
        "minimum_asset_loss_structural": subject.MINIMUM_ASSET_LOSS_STRUCTURAL,
        "minimum_asset_loss_provenance": "source_declared",
        "concurrent_tasks": concurrent_tasks,
    }


class KosovoResidentialOQ313RunTests(unittest.TestCase):
    def _run(
        self,
        *,
        payload: bytes | None = None,
        identity: dict[str, object] | None = None,
        runtime: dict[str, object] | None = None,
        returncode: int = 0,
    ) -> tuple[bytes, dict[str, object], mock.Mock]:
        config = payload if payload is not None else derived_config()
        evidence = config_evidence(config)
        execute = mock.Mock(return_value=returncode)
        with (
            mock.patch.object(subject, "_read_staged_config", return_value=config),
            mock.patch.object(subject, "_execute_native", execute),
        ):
            result = subject._run_derived_config(
                config,
                evidence,
                runtime_identity=identity if identity is not None else runtime_identity(),
                resolved_runtime=runtime if runtime is not None else resolved_runtime(),
            )
        return result[0], result[1], execute

    def test_fixed_command_and_preprocess_environment_are_injected(self) -> None:
        seen: dict[str, object] = {}

        def execute(command: object, env: object) -> int:
            seen["command"] = command
            seen["env"] = env
            return 0

        config = derived_config()
        with (
            mock.patch.object(subject, "_read_staged_config", return_value=config),
            mock.patch.object(subject, "_execute_native", side_effect=execute),
            mock.patch.dict(
                os.environ,
                {
                    "OPENBLAS_NUM_THREADS": "99",
                    "OQ_DISTRIBUTE": "processpool",
                },
                clear=False,
            ),
        ):
            payload, receipt = subject._run_derived_config(
                config,
                config_evidence(config),
                runtime_identity=runtime_identity(),
                resolved_runtime=resolved_runtime(concurrent_tasks=0),
            )

        document = json.loads(payload)
        self.assertEqual(tuple(seen["command"]), subject.COMMAND)
        env = seen["env"]
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "1")
        self.assertEqual(env["OQ_DISTRIBUTE"], subject.OQ_DISTRIBUTE)
        self.assertEqual(env["OQ_DISTRIBUTE"], "no")
        self.assertEqual(env["PYTHONPATH"], subject.OPENQUAKE_SOURCE_OVERLAY)
        self.assertEqual(document["execution"]["command"], list(subject.COMMAND))
        self.assertEqual(document["execution"]["oq_distribute"], "no")
        self.assertIs(document["execution"]["preprocess_openblas_injected"], True)
        self.assertIs(
            document["execution"]["preprocess_oq_distribute_injected"],
            True,
        )
        self.assertIs(document["execution"]["distribution_state_receipted"], True)
        self.assertEqual(document["resolved_runtime"]["concurrent_tasks"], 0)
        self.assertEqual(
            document["loss_semantics"],
            {
                "loss_stage": "thresholded_ground_up",
                "loss_type": "structural",
                "minimum_asset_loss_structural": 2000,
                "quantity": "thresholded_ground_up_structural_replacement_cost_loss",
                "threshold_is_deductible": False,
                "threshold_predicate": (
                    "asset_event_loss > minimum_asset_loss_structural"
                ),
                "threshold_source": "exact_group1_provider_config",
                "unit": "EUR",
            },
        )
        self.assertEqual(document["status"], "pass")
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertTrue(payload.endswith(b"\n"))

    def test_native_child_stdout_is_suppressed_and_stderr_is_streamed(self) -> None:
        class EmptyStderr:
            def read(self, size: int = -1) -> bytes:
                self.last_size = size
                return b""

        class Process:
            def __init__(self) -> None:
                self.stderr = EmptyStderr()

            def __enter__(self) -> Process:
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def wait(self) -> int:
                return 0

        process = Process()
        env = {"PATH": "/fixed"}
        with mock.patch.object(subject.subprocess, "Popen", return_value=process) as popen:
            returncode = subject._execute_native(subject.COMMAND, env)

        self.assertEqual(returncode, 0)
        popen.assert_called_once()
        args, kwargs = popen.call_args
        self.assertEqual(args[0], list(subject.COMMAND))
        self.assertEqual(kwargs["env"], env)
        self.assertIs(kwargs["stdout"], subject.subprocess.DEVNULL)
        self.assertIs(kwargs["stderr"], subject.subprocess.PIPE)
        self.assertEqual(
            process.stderr.last_size,
            subject.NATIVE_STDERR_HASH_CHUNK_BYTES,
        )

    def test_runtime_identity_must_pin_exact_oq313_source_before_execution(self) -> None:
        identity = runtime_identity()
        identity["commit_sha"] = "0" * 40
        execute = mock.Mock()
        config = derived_config()
        with (
            mock.patch.object(subject, "_read_staged_config") as read,
            mock.patch.object(subject, "_execute_native", execute),
            self.assertRaisesRegex(
                subject.KosovoResidentialOQ313RunError,
                "^runtime identity commit_sha drifted$",
            ),
        ):
            subject._run_derived_config(
                config,
                config_evidence(config),
                runtime_identity=identity,
                resolved_runtime=resolved_runtime(),
            )
        read.assert_not_called()
        execute.assert_not_called()

    def test_dependency_version_receipt_is_exact(self) -> None:
        identity = runtime_identity()
        dependencies = dict(subject.EXPECTED_DEPENDENCY_VERSIONS)
        dependencies["numpy"] = "9.9.9"
        identity["dependency_versions"] = dependencies
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^runtime dependency version receipt drifted$",
        ):
            subject._validate_runtime_identity(identity)

    def test_ses_seed_must_be_default_resolved_and_source_absent(self) -> None:
        runtime = resolved_runtime()
        runtime["ses_seed_provenance"] = "source_declared"
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^resolved runtime ses_seed_provenance drifted$",
        ):
            subject._validate_resolved_runtime(runtime)

        runtime = resolved_runtime()
        runtime["ses_seed"] = subject.OPENQUAKE_DEFAULT_SES_SEED + 1
        execute = mock.Mock()
        config = derived_config()
        with (
            mock.patch.object(subject, "_read_staged_config") as read,
            mock.patch.object(subject, "_execute_native", execute),
            self.assertRaisesRegex(
                subject.KosovoResidentialOQ313RunError,
                "^resolved runtime ses_seed must equal the pinned OpenQuake 3.13 default$",
            ),
        ):
            subject._run_derived_config(
                config,
                config_evidence(config),
                runtime_identity=runtime_identity(),
                resolved_runtime=runtime,
            )
        read.assert_not_called()
        execute.assert_not_called()

        config = derived_config().replace(
            b"random_seed = 113\n",
            b"random_seed = 113\nses_seed = 42\n",
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^source ses_seed must remain absent for default-derived provenance$",
        ):
            subject._validate_source_runtime_declarations(config)

    def test_source_seed_and_threshold_drift_fail_closed(self) -> None:
        bad_seed = derived_config().replace(b"random_seed = 113", b"random_seed = 114")
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^source random_seed drifted$",
        ):
            subject._validate_source_runtime_declarations(bad_seed)

        bad_threshold = derived_config().replace(
            b"{'structural': 2000}",
            b"{'structural': 2001}",
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^source minimum_asset_loss structural threshold drifted$",
        ):
            subject._validate_source_runtime_declarations(bad_threshold)

    def test_structural_threshold_can_coexist_with_other_loss_type_entries(self) -> None:
        config = derived_config().replace(
            b"{'structural': 2000}",
            b"{'structural': 2000, 'occupants': 0}",
        )
        projected = subject._validate_source_runtime_declarations(config)
        self.assertEqual(projected["minimum_asset_loss_structural"], 2000)
        self.assertEqual(
            projected["minimum_asset_loss_provenance"],
            "source_declared",
        )

    def test_concurrent_tasks_zero_is_valid_but_negative_and_bool_are_rejected(self) -> None:
        self.assertEqual(
            subject._validate_resolved_runtime(resolved_runtime(concurrent_tasks=0))[
                "concurrent_tasks"
            ],
            0,
        )
        for invalid in (-1, True):
            with self.subTest(invalid=invalid):
                runtime = resolved_runtime()
                runtime["concurrent_tasks"] = invalid
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313RunError,
                    "^resolved runtime concurrent_tasks must be a non-negative integer$",
                ):
                    subject._validate_resolved_runtime(runtime)

    def test_staged_config_must_be_byte_identical_before_execution(self) -> None:
        config = derived_config()
        execute = mock.Mock()
        with (
            mock.patch.object(subject, "_read_staged_config", return_value=b"wrong"),
            mock.patch.object(subject, "_execute_native", execute),
            self.assertRaisesRegex(
                subject.KosovoResidentialOQ313RunError,
                "^staged derived config byte identity does not match the verified recipe$",
            ),
        ):
            subject._run_derived_config(
                config,
                config_evidence(config),
                runtime_identity=runtime_identity(),
                resolved_runtime=resolved_runtime(),
            )
        execute.assert_not_called()

    def test_nonzero_engine_exit_is_bounded_not_promoted(self) -> None:
        payload, _receipt, execute = self._run(returncode=17)
        execute.assert_called_once()
        document = json.loads(payload)
        self.assertEqual(document["status"], "blocked")
        self.assertEqual(document["failure_stage"], "openquake_run")
        self.assertEqual(document["failure_code"], "openquake_run_failed")
        self.assertEqual(document["execution"]["exit_code"], 17)
        self.assertNotIn("native_failure_diagnostic", document)
        for field in (
            "historical_environment_verified",
            "reference_base_image_byte_identity_verified",
            "wheel_byte_identity_verified",
            "historical_group_assignment_verified",
            "vulnerability_horizontal_component_verified",
            "horizontal_component_conversion_authorized",
            "project186_value_structural_equivalence_verified",
            "numerical_reference_loss_verified",
            "independent_validation_established",
            "publication_authorized",
            "model_use_authorized",
            "risk_by_event_receipt_emitted",
            "external_provider_bytes_persisted",
        ):
            self.assertIs(document[field], False)

    def test_config_evidence_cannot_promote_scientific_authority(self) -> None:
        config = derived_config()
        evidence = config_evidence(config)
        evidence["publication_authorized"] = True
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313RunError,
            "^config evidence authority boundary publication_authorized drifted$",
        ):
            subject._validate_config_evidence(config, evidence)

    def test_public_entry_builds_exact_recipe_before_native_run(self) -> None:
        source = b"exact-provider-group1"
        config = derived_config()
        evidence = config_evidence(config)
        with (
            mock.patch.object(subject, "_require_authority") as authority,
            mock.patch.object(
                subject.config_builder,
                "build_kosovo_residential_ebrisk_config",
                return_value=(config, evidence),
            ) as build,
            mock.patch.object(
                subject,
                "_run_derived_config",
                return_value=(b"result\n", {"sha256": "a"}),
            ) as run,
        ):
            result = subject.run_kosovo_residential_ebrisk_openquake313(
                source,
                runtime_identity=runtime_identity(),
                resolved_runtime=resolved_runtime(),
            )

        self.assertEqual(result, (b"result\n", {"sha256": "a"}))
        authority.assert_called_once_with()
        build.assert_called_once_with(source)
        run.assert_called_once_with(
            config,
            evidence,
            runtime_identity=runtime_identity(),
            resolved_runtime=resolved_runtime(),
        )

    def test_live_authority_drift_fails_before_builder_or_execution(self) -> None:
        with (
            mock.patch.object(
                subject.risk_receipt,
                "OPENQUAKE_COMMIT_SHA",
                "0" * 40,
            ),
            mock.patch.object(
                subject.config_builder,
                "build_kosovo_residential_ebrisk_config",
            ) as build,
            self.assertRaisesRegex(
                subject.KosovoResidentialOQ313RunError,
                "^risk receipt OpenQuake commit authority drifted$",
            ),
        ):
            subject.run_kosovo_residential_ebrisk_openquake313(
                b"x",
                runtime_identity=runtime_identity(),
                resolved_runtime=resolved_runtime(),
            )
        build.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
