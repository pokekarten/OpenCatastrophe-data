# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts import project_oq313_risk_by_event_receipt as numerical_contract
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject

EXECUTION_SHA = "a" * 40


def _adapter_payload(*, status: str = "pass") -> tuple[bytes, dict[str, Any]]:
    blocked = status == "blocked"
    document = {
        "schema_version": runner.SCHEMA_VERSION,
        "issues": {
            "control": runner.CONTROL_ISSUE,
            "parent_consumer": runner.PARENT_CONSUMER_ISSUE,
        },
        "experiment_label": runner.EXPERIMENT_LABEL,
        "scope": runner.SCOPE,
        "openquake": {
            "repository": runner.OPENQUAKE_REPOSITORY,
            "version": runner.OPENQUAKE_VERSION,
            "source_version": runner.OPENQUAKE_SOURCE_VERSION,
            "commit_sha": runner.OPENQUAKE_COMMIT_SHA,
        },
        "config": {
            "logical_path": runner.CONFIG_LOGICAL_PATH,
            "byte_count": 1,
            "sha256": "b" * 64,
            "staged_byte_identity_verified": True,
        },
        "loss_semantics": {},
        "source_runtime": {},
        "resolved_runtime": {},
        "execution": {
            "command": list(runner.COMMAND),
            "exit_code": 9 if blocked else 0,
            "numerical_execution_attempted": True,
        },
        "status": status,
        "failure_stage": "openquake_run" if blocked else None,
        "failure_code": "openquake_run_failed" if blocked else None,
        "external_provider_bytes_persisted": False,
        "risk_by_event_receipt_emitted": False,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "historical_group_assignment_verified": False,
        "vulnerability_horizontal_component_verified": False,
        "horizontal_component_conversion_authorized": False,
        "project186_value_structural_equivalence_verified": False,
        "numerical_reference_loss_verified": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    payload = (
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _numerical_payload() -> tuple[bytes, dict[str, Any]]:
    document = {
        "schema_version": numerical_contract.SCHEMA_VERSION,
        "experiment_label": numerical_contract.EXPERIMENT_LABEL,
        "insurance_scope": "none",
        "openquake": {
            "version": runner.OPENQUAKE_VERSION,
            "commit_sha": runner.OPENQUAKE_COMMIT_SHA,
        },
        "quantity": {
            "loss_type": numerical_contract.LOSS_TYPE,
            "minimum_asset_loss_structural": numerical_contract.MINIMUM_ASSET_LOSS_STRUCTURAL,
            "name": numerical_contract.QUANTITY,
            "unit": numerical_contract.UNIT,
        },
        "rows": [
            {
                "event_id": 1,
                "rup_id": 2,
                "loss_f32_be_hex": "3f800000",
                "variance_f32_be_hex": "00000000",
            }
        ],
        "runtime": {"concurrent_tasks": 0},
        "selection": {"portfolio_agg_id": 3, "structural_loss_id": 0},
        "source_dataset": numerical_contract.SOURCE_DATASET,
    }
    payload = (
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


class OQ313NumericalReceiptActionIntegrationTests(unittest.TestCase):
    def test_pass_uses_fresh_datadir_and_embeds_receipt(self) -> None:
        observed: dict[str, Path] = {}

        def execute(
            source_group1_config: bytes,
            *,
            runtime_identity: object,
            resolved_runtime: object,
        ) -> tuple[bytes, dict[str, Any]]:
            self.assertEqual(source_group1_config, b"source")
            self.assertEqual(runtime_identity, {"runtime": "fixed"})
            self.assertEqual(resolved_runtime, {"resolved": "fixed"})
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            observed["datadir"] = datadir
            self.assertTrue(datadir.is_dir())
            self.assertEqual(list(datadir.iterdir()), [])
            (datadir / "calc_7.hdf5").write_bytes(b"fixture")
            return _adapter_payload()

        def project_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
            self.assertEqual(path, observed["datadir"] / "calc_7.hdf5")
            return _numerical_payload()

        with mock.patch.dict(
            os.environ,
            {subject.OQ_DATADIR_ENV: "/preexisting/oqdata"},
            clear=False,
        ):
            result = subject.run_action_with_numerical_receipt(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={"runtime": "fixed"},
                resolved_runtime={"resolved": "fixed"},
                execute=execute,
                project_datastore=project_datastore,
            )
            self.assertEqual(
                os.environ[subject.OQ_DATADIR_ENV],
                "/preexisting/oqdata",
            )

        self.assertFalse(observed["datadir"].exists())
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["numerical_receipt_emitted"], True)
        self.assertIsNone(result["numerical_receipt_failure_stage"])
        self.assertIsNone(result["numerical_receipt_failure_code"])
        self.assertIs(result["oq_datastore_persisted"], False)
        self.assertEqual(
            result["numerical_receipt"]["schema_version"],
            numerical_contract.SCHEMA_VERSION,
        )
        payload, identity = _numerical_payload()
        self.assertEqual(result["numerical_receipt_identity"], identity)
        self.assertEqual(
            identity["sha256"],
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertIs(result["historical_reproduction_verified"], False)
        self.assertIs(result["scientific_validity_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_pass_terminalizes_multiple_calculation_datastores(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"one")
            (datadir / "calc_2.hdf5").write_bytes(b"two")
            return _adapter_payload()

        result = subject.run_action_with_numerical_receipt(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
            project_datastore=lambda path: _numerical_payload(),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_stage"],
            "risk_by_event_receipt",
        )
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "calculation_datastore_cardinality_invalid",
        )
        self.assertEqual(result["adapter_result"]["status"], "pass")

    def test_blocked_does_not_project_partial_datastore(self) -> None:
        observed: dict[str, Path] = {}

        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            observed["datadir"] = datadir
            (datadir / "calc_1.hdf5").write_bytes(b"partial")
            return _adapter_payload(status="blocked")

        def project_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
            raise AssertionError(f"projector must not run for BLOCKED: {path}")

        result = subject.run_action_with_numerical_receipt(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
            project_datastore=project_datastore,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertIs(result["oq_datastore_persisted"], False)
        self.assertFalse(observed["datadir"].exists())

    def test_pass_terminalizes_numerical_receipt_digest_drift(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"fixture")
            return _adapter_payload()

        def project_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
            self.assertEqual(path.name, "calc_1.hdf5")
            payload, identity = _numerical_payload()
            identity["sha256"] = "0" * 64
            return payload, identity

        result = subject.run_action_with_numerical_receipt(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
            project_datastore=project_datastore,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIs(result["numerical_receipt_emitted"], False)
        self.assertEqual(
            result["numerical_receipt_failure_stage"],
            "risk_by_event_receipt",
        )
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "numerical_receipt_validation_failed",
        )
        self.assertEqual(result["adapter_result"]["status"], "pass")

    def test_pass_terminalizes_projector_failure_without_exposing_details(self) -> None:
        def execute(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
            del args, kwargs
            datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
            (datadir / "calc_1.hdf5").write_bytes(b"fixture")
            return _adapter_payload()

        def project_datastore(path: Path) -> tuple[bytes, dict[str, Any]]:
            self.assertEqual(path.name, "calc_1.hdf5")
            raise subject.KosovoResidentialOQ313ActionError(
                "sensitive source-native detail must not escape"
            )

        result = subject.run_action_with_numerical_receipt(
            execution_sha=EXECUTION_SHA,
            source_group1_config=b"source",
            runtime_identity={},
            resolved_runtime={},
            execute=execute,
            project_datastore=project_datastore,
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "risk_by_event_selection_failed",
        )
        self.assertNotIn("sensitive source-native detail", serialized)


if __name__ == "__main__":
    unittest.main()
