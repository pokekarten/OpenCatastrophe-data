# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_agent_artifact.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_artifact", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

REPOSITORY = "pokekarten/OpenCatastrophe-data"
MAIN_SHA = "1" * 40
SHA = "a" * 64
MANIFEST = "manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json"
SOURCE_REVIEW = "docs/source-reviews/dwd-cdc-obsgermany-climate-10min-extreme-wind-v24.03.md"


def valid_task() -> dict[str, object]:
    return {
        "profile_version": "1.0.0",
        "task_id": "agent-contract-smoke",
        "repository": REPOSITORY,
        "state": "ready",
        "agent_ready": True,
        "workstream": "agent-coordination",
        "reviewed_against": {
            "ref": "refs/heads/main",
            "commit": MAIN_SHA,
            "checked_at": "2026-08-10T01:10:00+02:00",
        },
        "shared_surfaces": ["schemas/agent-task-v1.schema.json"],
        "dependencies": [],
        "next_action": "Validate one repository-owned agent task artifact.",
        "hard_stop": "Stop if current main differs from reviewed_against.commit.",
        "acceptance": {
            "criteria": ["The strict validator accepts the artifact."],
            "commands": [
                {
                    "argv": ["python", "scripts/validate_agent_artifact.py", "task", "task.json"],
                    "purpose": "Validate the task contract.",
                    "cwd": ".github",
                }
            ],
            "evidence": ["evidence/task-validation.txt"],
        },
        "data_boundary": {"bytes_policy": "synthetic_only"},
    }


def valid_run() -> dict[str, object]:
    return {
        "profile_version": "1.0.0",
        "run_id": "synthetic-data-smoke",
        "repository": {"name": REPOSITORY, "commit": MAIN_SHA, "dirty": False},
        "execution": {
            "commands": [
                {
                    "argv": ["python", "scripts/check_all.py"],
                    "purpose": "Run repository acceptance checks.",
                }
            ],
            "started_at": "2026-08-10T00:00:00Z",
            "ended_at": "2026-08-10T00:01:00Z",
            "exit_code": 0,
        },
        "inputs": [
            {
                "id": "synthetic-fixture",
                "kind": "fixture",
                "identity": "fixture:synthetic-v1",
                "sha256": SHA,
            }
        ],
        "randomness": {"mode": "deterministic"},
        "outputs": [
            {
                "path": "evidence/result.json",
                "sha256": SHA,
                "byte_size": 123,
                "media_type": "application/json",
            }
        ],
        "validation": [{"check": "repository-checks", "status": "pass", "evidence": "repository checks"}],
        "status": "pass",
        "claims": [
            {
                "statement": "The recorded synthetic transformation is reproducible from pinned inputs.",
                "evidence_class": "repository_source",
                "references": ["SCIENTIFIC_METHOD.md"],
            }
        ],
        "limitations": ["Synthetic evidence does not authorize or validate any external dataset."],
        "environment": {"os": "linux", "architecture": "x86_64", "runtime": "Python 3.12"},
        "interoperability": [
            {
                "target": "RDLS",
                "version": "1.0.0",
                "role": "metadata",
                "status": "planned",
                "profile": "dataset-metadata",
                "evidence": [],
            }
        ],
    }


def valid_run_v2() -> dict[str, object]:
    return {
        "profile_version": "2.0.0",
        "run_id": "synthetic-model-evidence-smoke",
        "repository": {"name": REPOSITORY, "commit": MAIN_SHA, "dirty": False},
        "execution": {
            "commands": [
                {
                    "argv": ["python", "scripts/check_all.py"],
                    "purpose": "Run repository acceptance checks.",
                }
            ],
            "started_at": "2026-08-10T00:00:00Z",
            "ended_at": "2026-08-10T00:01:00Z",
            "exit_code": 0,
        },
        "inputs": [
            {
                "id": "synthetic-fixture",
                "kind": "fixture",
                "identity": "fixture:synthetic-v2",
                "scientific_role": "test_fixture",
                "sha256": SHA,
            }
        ],
        "randomness": {"mode": "deterministic"},
        "outputs": [
            {
                "path": "evidence/result.json",
                "sha256": "b" * 64,
                "byte_size": 123,
                "media_type": "application/json",
            }
        ],
        "validation": [{"check": "repository-checks", "status": "pass", "evidence": "repository checks"}],
        "status": "pass",
        "claims": [
            {
                "statement": "The synthetic contract smoke run is reproducible from its recorded fixture.",
                "evidence_class": "repository_source",
                "references": [{"kind": "input", "ref": "synthetic-fixture"}],
                "scope": {"model_context": "synthetic contract validation"},
                "limitations": ["This synthetic run does not establish external-data fitness."],
            }
        ],
        "limitations": ["Synthetic evidence only."],
    }


def data_input(*, input_id: str, identity: str, role: str, sha256: str) -> dict[str, object]:
    return {
        "id": input_id,
        "kind": "data",
        "identity": identity,
        "scientific_role": role,
        "manifest": MANIFEST,
        "sha256": sha256,
    }


class AgentArtifactContractTests(unittest.TestCase):
    def test_schemas_are_closed_draft_2020_12_json(self) -> None:
        expected = {
            "agent-task-v1.schema.json": "1.0.0",
            "run-evidence-v1.schema.json": "1.0.0",
            "run-evidence-v2.schema.json": "2.0.0",
        }
        for name, profile_version in expected.items():
            payload = validator.load_strict_json(ROOT / "schemas" / name)
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(payload["additionalProperties"])
            self.assertEqual(payload["properties"]["profile_version"]["const"], profile_version)

    def test_valid_task_accepts_exact_main(self) -> None:
        validator.validate_task(valid_task(), expected_repository=REPOSITORY, expected_main_sha=MAIN_SHA)

    def test_stale_task_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.ContractError, "task is stale"):
            validator.validate_task(valid_task(), expected_repository=REPOSITORY, expected_main_sha="2" * 40)

    def test_task_path_traversal_is_rejected(self) -> None:
        payload = valid_task()
        payload["shared_surfaces"] = ["../private.txt"]
        with self.assertRaises(validator.ContractError):
            validator.validate_task(payload)

    def test_blocked_task_cannot_be_agent_ready(self) -> None:
        payload = valid_task()
        payload["state"] = "blocked"
        with self.assertRaisesRegex(validator.ContractError, "agent_ready"):
            validator.validate_task(payload)

    def test_valid_v1_run_remains_supported(self) -> None:
        validator.validate_run(valid_run(), expected_repository=REPOSITORY)

    def test_valid_v2_run_records_scientific_roles_and_resolvable_claims(self) -> None:
        validator.validate_run(valid_run_v2(), expected_repository=REPOSITORY)

    def test_run_cli_executes_directly_and_returns_stable_pass_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(valid_run_v2()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_agent_artifact.py",
                    "run",
                    str(path),
                    "--expected-repository",
                    REPOSITORY,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("PASS: valid run artifact:"), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_v2_data_requires_admitted_manifest_and_exact_hash(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [
            {
                "id": "training-data",
                "kind": "data",
                "identity": "dataset:training-window",
                "scientific_role": "training",
                "sha256": SHA,
            }
        ]
        with self.assertRaisesRegex(validator.ContractError, "requires admitted manifest and exact sha256"):
            validator.validate_run(payload)
        payload["inputs"][0]["manifest"] = MANIFEST
        del payload["inputs"][0]["sha256"]
        with self.assertRaisesRegex(validator.ContractError, "requires admitted manifest and exact sha256"):
            validator.validate_run(payload)

    def test_v2_non_data_input_cannot_claim_manifest_admission(self) -> None:
        payload = valid_run_v2()
        payload["inputs"][0]["manifest"] = MANIFEST
        with self.assertRaisesRegex(validator.ContractError, "manifest is only valid for kind data"):
            validator.validate_run(payload)

    def test_v2_scientific_role_must_match_input_kind(self) -> None:
        payload = valid_run_v2()
        payload["inputs"][0]["scientific_role"] = "training"
        with self.assertRaisesRegex(validator.ContractError, "scientific_role"):
            validator.validate_run(payload)

    def test_v2_same_exact_bytes_cannot_cross_training_and_holdout_roles(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [
            data_input(input_id="training", identity="dataset:train", role="training", sha256=SHA),
            data_input(input_id="holdout", identity="dataset:holdout", role="holdout", sha256=SHA),
        ]
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "training"}]
        with self.assertRaisesRegex(validator.ContractError, "duplicate exact input content sha256"):
            validator.validate_run(payload)

    def test_v2_data_manifest_must_resolve_to_repository_admission(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [
            data_input(
                input_id="training",
                identity="dataset:train",
                role="training",
                sha256=SHA,
            )
        ]
        payload["inputs"][0]["manifest"] = "manifests/not-admitted.json"
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "training"}]
        with self.assertRaisesRegex(validator.ContractError, "existing repository file"):
            validator.validate_run(payload)

    def test_v2_claim_reference_must_resolve(self) -> None:
        payload = valid_run_v2()
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "missing-input"}]
        with self.assertRaisesRegex(validator.ContractError, "does not resolve"):
            validator.validate_run(payload)

    def test_v2_claim_can_resolve_manifest_review_and_repository_evidence(self) -> None:
        self.assertTrue((ROOT / SOURCE_REVIEW).is_file(), SOURCE_REVIEW)
        payload = valid_run_v2()
        payload["claims"][0]["references"] = [
            {"kind": "manifest", "ref": MANIFEST},
            {"kind": "source_review", "ref": SOURCE_REVIEW},
            {"kind": "repository_path", "ref": "SCIENTIFIC_METHOD.md"},
        ]
        validator.validate_run(payload)

    def test_v2_external_evidence_rejects_signed_or_private_reference(self) -> None:
        payload = valid_run_v2()
        payload["claims"][0]["evidence_class"] = "external_evidence"
        payload["claims"][0]["references"] = [
            {"kind": "external_uri", "ref": "https://example.invalid/source?token=" + "a" * 30}
        ]
        with self.assertRaisesRegex(validator.ContractError, "credential or signature query parameters"):
            validator.validate_run(payload)

    def test_v2_claim_scope_cannot_be_empty(self) -> None:
        payload = valid_run_v2()
        payload["claims"][0]["scope"] = {}
        with self.assertRaisesRegex(validator.ContractError, "scope must contain at least one"):
            validator.validate_run(payload)

    def test_pass_run_cannot_hide_blocked_validation(self) -> None:
        payload = valid_run()
        payload["validation"] = [{"check": "licence", "status": "blocked"}]
        with self.assertRaisesRegex(validator.ContractError, "every validation check"):
            validator.validate_run(payload)

    def test_pass_run_requires_zero_exit_code(self) -> None:
        payload = valid_run()
        payload["execution"]["exit_code"] = 2
        with self.assertRaisesRegex(validator.ContractError, "exit_code 0"):
            validator.validate_run(payload)

    def test_duplicate_input_ids_are_rejected(self) -> None:
        payload = valid_run()
        payload["inputs"] = [payload["inputs"][0], dict(payload["inputs"][0])]
        with self.assertRaisesRegex(validator.ContractError, "duplicate run input id"):
            validator.validate_run(payload)

    def test_duplicate_output_paths_are_rejected(self) -> None:
        payload = valid_run()
        payload["outputs"] = [payload["outputs"][0], dict(payload["outputs"][0])]
        with self.assertRaisesRegex(validator.ContractError, "duplicate run output path"):
            validator.validate_run(payload)

    def test_stochastic_run_requires_full_stream_provenance(self) -> None:
        payload = valid_run()
        payload["randomness"] = {"mode": "stochastic", "algorithm": "PCG64", "seed_material": "42"}
        with self.assertRaisesRegex(validator.ContractError, "missing required"):
            validator.validate_run(payload)

    def test_boolean_is_not_an_integer_byte_size(self) -> None:
        payload = valid_run()
        payload["outputs"][0]["byte_size"] = True
        with self.assertRaisesRegex(validator.ContractError, "must be an integer"):
            validator.validate_run(payload)

    def test_tested_interoperability_requires_exact_version_and_evidence(self) -> None:
        payload = valid_run()
        payload["interoperability"] = [
            {
                "target": "external-standard",
                "version": "latest",
                "role": "metadata",
                "status": "tested",
                "evidence": [],
            }
        ]
        with self.assertRaises(validator.ContractError):
            validator.validate_run(payload)

    def test_external_evidence_claim_requires_reference(self) -> None:
        payload = valid_run()
        payload["claims"] = [
            {
                "statement": "External source supports this interpretation.",
                "evidence_class": "external_evidence",
                "references": [],
            }
        ]
        with self.assertRaisesRegex(validator.ContractError, "require at least one reference"):
            validator.validate_run(payload)

    def test_duplicate_json_keys_and_non_finite_numbers_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(validator.ContractError):
                validator.load_strict_json(path)
            path.write_text('{"a": NaN}', encoding="utf-8")
            with self.assertRaises(validator.ContractError):
                validator.load_strict_json(path)


if __name__ == "__main__":
    unittest.main()
