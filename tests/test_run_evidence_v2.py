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
SHA_A = "a" * 64
SHA_B = "b" * 64
MANIFEST = "manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json"
SOURCE_REVIEW = "docs/source-reviews/dwd-extreme-wind-v24.03.md"


def valid_run_v2() -> dict[str, object]:
    return {
        "profile_version": "2.0.0",
        "run_id": "synthetic-model-evidence-smoke",
        "repository": {"name": REPOSITORY, "commit": MAIN_SHA, "dirty": False},
        "execution": {
            "commands": [{"argv": ["python", "scripts/check_all.py"], "purpose": "Run repository checks."}],
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
                "sha256": SHA_A,
            }
        ],
        "randomness": {"mode": "deterministic"},
        "outputs": [
            {
                "path": "evidence/result.json",
                "sha256": SHA_B,
                "byte_size": 123,
                "media_type": "application/json",
            }
        ],
        "validation": [{"check": "repository-checks", "status": "pass"}],
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


class RunEvidenceV2Tests(unittest.TestCase):
    def test_schema_is_closed_versioned_json(self) -> None:
        schema = validator.load_strict_json(ROOT / "schemas/run-evidence-v2.schema.json")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["profile_version"]["const"], validator.RUN_PROFILE_V2)

    def test_valid_v2_run_records_roles_and_resolvable_claims(self) -> None:
        validator.validate_run(valid_run_v2(), expected_repository=REPOSITORY)

    def test_v2_cli_executes_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-v2.json"
            path.write_text(json.dumps(valid_run_v2()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/validate_agent_artifact.py", "run", str(path), "--expected-repository", REPOSITORY],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("PASS: valid run artifact:"), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_data_requires_admitted_manifest_and_exact_hash(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [
            {"id": "training", "kind": "data", "identity": "dataset:train", "scientific_role": "training", "sha256": SHA_A}
        ]
        with self.assertRaisesRegex(validator.ContractError, "requires admitted manifest and exact sha256"):
            validator.validate_run(payload)

        payload["inputs"][0]["manifest"] = MANIFEST
        del payload["inputs"][0]["sha256"]
        with self.assertRaisesRegex(validator.ContractError, "requires admitted manifest and exact sha256"):
            validator.validate_run(payload)

    def test_non_data_input_cannot_claim_manifest_admission(self) -> None:
        payload = valid_run_v2()
        payload["inputs"][0]["manifest"] = MANIFEST
        with self.assertRaisesRegex(validator.ContractError, "manifest is only valid for kind data"):
            validator.validate_run(payload)

    def test_scientific_role_must_match_input_kind(self) -> None:
        payload = valid_run_v2()
        payload["inputs"][0]["scientific_role"] = "training"
        with self.assertRaisesRegex(validator.ContractError, "scientific_role"):
            validator.validate_run(payload)

    def test_same_exact_bytes_cannot_cross_training_and_holdout_roles(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [
            data_input(input_id="training", identity="dataset:train", role="training", sha256=SHA_A),
            data_input(input_id="holdout", identity="dataset:holdout", role="holdout", sha256=SHA_A),
        ]
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "training"}]
        with self.assertRaisesRegex(validator.ContractError, "duplicate exact input content sha256"):
            validator.validate_run(payload)

    def test_data_manifest_must_resolve_to_repository_admission(self) -> None:
        payload = valid_run_v2()
        payload["inputs"] = [data_input(input_id="training", identity="dataset:train", role="training", sha256=SHA_A)]
        payload["inputs"][0]["manifest"] = "manifests/not-admitted.json"
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "training"}]
        with self.assertRaisesRegex(validator.ContractError, "existing repository file"):
            validator.validate_run(payload)

    def test_claim_references_must_resolve_and_scope_must_be_bounded(self) -> None:
        payload = valid_run_v2()
        payload["claims"][0]["references"] = [{"kind": "input", "ref": "missing-input"}]
        with self.assertRaisesRegex(validator.ContractError, "does not resolve"):
            validator.validate_run(payload)

        payload = valid_run_v2()
        payload["claims"][0]["scope"] = {}
        with self.assertRaisesRegex(validator.ContractError, "scope must contain at least one"):
            validator.validate_run(payload)

    def test_claim_can_resolve_manifest_review_and_repository_evidence(self) -> None:
        self.assertTrue((ROOT / MANIFEST).is_file(), MANIFEST)
        self.assertTrue((ROOT / SOURCE_REVIEW).is_file(), SOURCE_REVIEW)
        payload = valid_run_v2()
        payload["claims"][0]["references"] = [
            {"kind": "manifest", "ref": MANIFEST},
            {"kind": "source_review", "ref": SOURCE_REVIEW},
            {"kind": "repository_path", "ref": "SCIENTIFIC_METHOD.md"},
        ]
        validator.validate_run(payload)

    def test_external_evidence_rejects_signed_reference(self) -> None:
        payload = valid_run_v2()
        payload["claims"][0]["evidence_class"] = "external_evidence"
        payload["claims"][0]["references"] = [
            {"kind": "external_uri", "ref": "https://example.invalid/source?token=" + "a" * 30}
        ]
        with self.assertRaisesRegex(validator.ContractError, "credential or signature query parameters"):
            validator.validate_run(payload)


if __name__ == "__main__":
    unittest.main()
