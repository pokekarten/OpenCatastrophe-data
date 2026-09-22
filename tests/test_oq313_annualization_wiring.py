# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from typing import Any

from scripts import project_oq313_annualization_evidence as projector
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject


EXECUTION_SHA = "a" * 40


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _identity(payload: bytes) -> dict[str, Any]:
    return {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _annualization_document() -> dict[str, Any]:
    return {
        "schema_version": projector.SCHEMA_VERSION,
        "source_datasets": {
            "events": projector.EVENTS_DATASET,
            "weights": projector.WEIGHTS_DATASET,
            "avg_losses": projector.AVG_LOSSES_DATASET,
        },
        "loss_type": projector.LOSS_TYPE,
        "structural_loss_id": 0,
        "runtime": {},
        "events": {},
        "weights": {},
        "avg_losses": {},
        "policy_present": False,
        "insured_loss_present": False,
        "datastore_rows_returned": False,
        "external_provider_bytes_persisted": False,
        "annualization_evidence_projected": True,
        "reference_loss_comparison_performed": False,
        "reference_loss_agreement_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _adapter_document() -> dict[str, Any]:
    return {
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
        "resolved_runtime": {"concurrent_tasks": 2},
        "execution": {
            "command": list(runner.COMMAND),
            "exit_code": 0,
            "numerical_execution_attempted": True,
        },
        "status": "pass",
        "failure_stage": None,
        "failure_code": None,
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


def _execute_with_datastore(*args: Any, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
    del args, kwargs
    datadir = Path(os.environ[subject.OQ_DATADIR_ENV])
    (datadir / "calc_1.hdf5").write_bytes(b"synthetic-datastore-placeholder")
    payload = _canonical_bytes(_adapter_document())
    return payload, _identity(payload)


def _fail_numerical(_path: Path) -> tuple[bytes, dict[str, Any]]:
    raise subject.KosovoResidentialOQ313ActionError("synthetic numerical failure")


class OQ313AnnualizationWiringTests(unittest.TestCase):
    def test_pass_terminal_preserves_authority_ceiling(self) -> None:
        payload = _canonical_bytes(_annualization_document())
        terminal = subject._annualization_terminal(
            execution_sha=EXECUTION_SHA,
            payload=payload,
            identity=_identity(payload),
        )
        self.assertEqual(
            terminal["schema_version"],
            subject.ANNUALIZATION_RESULT_SCHEMA_VERSION,
        )
        self.assertEqual(terminal["status"], "pass")
        self.assertTrue(terminal["evidence_emitted"])
        self.assertFalse(terminal["oq_datastore_persisted"])
        self.assertFalse(terminal["reference_loss_comparison_performed"])
        self.assertFalse(terminal["reference_loss_agreement_verified"])
        self.assertFalse(terminal["scientific_validity_verified"])
        self.assertFalse(terminal["publication_authorized"])
        self.assertFalse(terminal["model_use_authorized"])

    def test_evidence_authority_promotion_is_rejected(self) -> None:
        document = _annualization_document()
        document["model_use_authorized"] = True
        payload = _canonical_bytes(document)
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "model_use_authorized",
        ):
            subject._annualization_terminal(
                execution_sha=EXECUTION_SHA,
                payload=payload,
                identity=_identity(payload),
            )

    def test_evidence_digest_drift_is_rejected(self) -> None:
        payload = _canonical_bytes(_annualization_document())
        identity = _identity(payload)
        identity["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "digest drifted",
        ):
            subject._annualization_terminal(
                execution_sha=EXECUTION_SHA,
                payload=payload,
                identity=identity,
            )

    def test_annualization_pass_is_written_before_independent_numerical_failure(self) -> None:
        payload = _canonical_bytes(_annualization_document())

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "annualization.json"
            result = subject.run_action_with_numerical_receipt(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=_execute_with_datastore,
                project_datastore=_fail_numerical,
                annualization_output=output,
                project_annualization=lambda _path: (payload, _identity(payload)),
            )

            terminal = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["numerical_receipt_failure_code"],
            "risk_by_event_selection_failed",
        )
        self.assertEqual(terminal["status"], "pass")
        self.assertTrue(terminal["evidence_emitted"])
        self.assertFalse(terminal["reference_loss_agreement_verified"])

    def test_annualization_projection_failure_writes_bounded_blocked_terminal(self) -> None:
        def fail_annualization(_path: Path) -> tuple[bytes, dict[str, Any]]:
            raise subject.KosovoResidentialOQ313ActionError(
                "synthetic annualization failure"
            )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "annualization.json"
            subject.run_action_with_numerical_receipt(
                execution_sha=EXECUTION_SHA,
                source_group1_config=b"source",
                runtime_identity={},
                resolved_runtime={},
                execute=_execute_with_datastore,
                project_datastore=_fail_numerical,
                annualization_output=output,
                project_annualization=fail_annualization,
            )
            terminal = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(terminal["status"], "blocked")
        self.assertFalse(terminal["evidence_emitted"])
        self.assertEqual(
            terminal["failure_stage"],
            "annualization_evidence",
        )
        self.assertEqual(
            terminal["failure_code"],
            "annualization_projection_failed",
        )
        self.assertFalse(terminal["publication_authorized"])
        self.assertFalse(terminal["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
