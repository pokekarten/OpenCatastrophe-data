# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_agent_artifact as validator

ROOT = Path(__file__).resolve().parents[1]

REPOSITORY = "pokekarten/OpenCatastrophe-data"
MAIN_SHA = "1" * 40
SHA = "a" * 64


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


class AgentArtifactContractTests(unittest.TestCase):
    def test_schemas_are_closed_draft_2020_12_json(self) -> None:
        for name in ("agent-task-v1.schema.json", "run-evidence-v1.schema.json"):
            payload = validator.load_strict_json(ROOT / "schemas" / name)
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(payload["additionalProperties"])
            self.assertEqual(payload["properties"]["profile_version"]["const"], "1.0.0")

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

    def test_valid_deterministic_run(self) -> None:
        validator.validate_run(valid_run(), expected_repository=REPOSITORY)

    def test_run_cli_executes_directly_and_returns_stable_pass_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.json"
            path.write_text(json.dumps(valid_run()), encoding="utf-8")
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
