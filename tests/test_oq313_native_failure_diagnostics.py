# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


@unittest.skipUnless(hasattr(os, "pread"), "requires POSIX positional reads")
class OQ313NativeFailureDiagnosticsTests(unittest.TestCase):
    def test_nonzero_exit_hashes_file_backed_stderr_without_exposing_content(self) -> None:
        secret = b"Traceback: /provider/private/path secret-value\n"
        command = [
            sys.executable,
            "-c",
            "import sys; "
            + f"sys.stderr.buffer.write({secret!r}); "
            + "sys.stderr.flush(); raise SystemExit(7)",
        ]

        with (
            mock.patch.object(subject, "NATIVE_EXECUTION_TIMEOUT_SECONDS", 5),
            mock.patch.object(subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.1),
        ):
            returncode = subject._execute_native(command, os.environ.copy())

        self.assertEqual(returncode, 7)
        diagnostic = getattr(returncode, "diagnostic")
        self.assertEqual(
            diagnostic,
            {
                "byte_count": len(secret),
                "sha256": hashlib.sha256(secret).hexdigest(),
                "content_exposed": False,
            },
        )
        self.assertNotIn("secret-value", json.dumps(diagnostic))
        self.assertNotIn("/provider/private/path", json.dumps(diagnostic))

    def test_non_utf8_stderr_remains_content_opaque_and_finite(self) -> None:
        expected = (b"\xff\xfe\x00" * 4096) + b"tail"
        command = [
            sys.executable,
            "-c",
            "import sys; "
            "sys.stderr.buffer.write((b'\\xff\\xfe\\x00' * 4096) + b'tail'); "
            "sys.stderr.flush(); raise SystemExit(23)",
        ]

        with (
            mock.patch.object(subject, "NATIVE_EXECUTION_TIMEOUT_SECONDS", 5),
            mock.patch.object(subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.1),
        ):
            returncode = subject._execute_native(command, os.environ.copy())

        diagnostic = getattr(returncode, "diagnostic")
        self.assertEqual(diagnostic["byte_count"], len(expected))
        self.assertEqual(diagnostic["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertIs(diagnostic["content_exposed"], False)
        self.assertEqual(set(diagnostic), {"byte_count", "sha256", "content_exposed"})

    def test_success_keeps_existing_result_shape_without_failure_diagnostic(self) -> None:
        command = [
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('non-published warning'); "
            "sys.stderr.flush(); raise SystemExit(0)",
        ]
        with (
            mock.patch.object(subject, "NATIVE_EXECUTION_TIMEOUT_SECONDS", 5),
            mock.patch.object(subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.1),
        ):
            returncode = subject._execute_native(command, os.environ.copy())

        self.assertEqual(type(returncode), int)
        self.assertEqual(returncode, 0)
        self.assertFalse(hasattr(returncode, "diagnostic"))

    def test_blocked_adapter_publishes_only_bounded_diagnostic_fields(self) -> None:
        config = b"""[general]\ncalculation_mode = ebrisk\nignore_master_seed = true\nminimum_asset_loss = {'structural': 2000}\nrandom_seed = 113\n\n[exposure]\nexposure_file = ../Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml\n\n[site_params]\nsite_model_file = ../Vs30/Site_model_Kosovo.xml\n"""
        evidence = {
            "output": {
                "logical_path": subject.CONFIG_LOGICAL_PATH,
                "byte_count": len(config),
                "sha256": hashlib.sha256(config).hexdigest(),
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
        identity = {
            "repository": subject.OPENQUAKE_REPOSITORY,
            "commit_sha": subject.OPENQUAKE_COMMIT_SHA,
            "openquake_version": subject.OPENQUAKE_SOURCE_VERSION,
            "python_major_minor": subject.PYTHON_MAJOR_MINOR,
            "dependency_versions": dict(subject.EXPECTED_DEPENDENCY_VERSIONS),
            "source_commit_verified": True,
            "bootstrap_image_digest": "sha256:" + "1" * 64,
            "execution_image_id": "sha256:" + "2" * 64,
        }
        runtime = {
            "calculation_mode": "ebrisk",
            "random_seed": subject.RANDOM_SEED,
            "random_seed_provenance": "source_declared",
            "ignore_master_seed": True,
            "ignore_master_seed_provenance": "source_declared",
            "ses_seed": subject.OPENQUAKE_DEFAULT_SES_SEED,
            "ses_seed_provenance": "openquake_default_resolved_from_source_absence",
            "minimum_asset_loss_structural": subject.MINIMUM_ASSET_LOSS_STRUCTURAL,
            "minimum_asset_loss_provenance": "source_declared",
            "concurrent_tasks": 0,
        }
        failure = subject._NativeExitCode(
            9,
            {
                "byte_count": 4,
                "sha256": hashlib.sha256(b"boom").hexdigest(),
                "content_exposed": False,
            },
        )
        with (
            mock.patch.object(subject, "_read_staged_config", return_value=config),
            mock.patch.object(subject, "_execute_native", return_value=failure),
        ):
            payload, _receipt = subject._run_derived_config(
                config,
                evidence,
                runtime_identity=identity,
                resolved_runtime=runtime,
            )

        document = json.loads(payload)
        self.assertEqual(document["status"], "blocked")
        self.assertEqual(document["execution"]["exit_code"], 9)
        self.assertEqual(
            document["native_failure_diagnostic"],
            {
                "byte_count": 4,
                "sha256": hashlib.sha256(b"boom").hexdigest(),
                "content_exposed": False,
            },
        )
        self.assertNotIn("boom", payload.decode("utf-8"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
