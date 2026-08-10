# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import validate_agent_artifact as validator

REPOSITORY = "pokekarten/OpenCatastrophe-data"
COMMIT = "1" * 40


def valid_run() -> dict[str, object]:
    return {
        "profile_version": "1.0.0",
        "run_id": "semantic-parity-smoke",
        "repository": {"name": REPOSITORY, "commit": COMMIT, "dirty": False},
        "execution": {
            "commands": [{"argv": ["python", "scripts/check_all.py"], "purpose": "Validate repository state."}],
            "started_at": "2026-08-10T00:00:00Z",
            "ended_at": "2026-08-10T00:01:00Z",
            "exit_code": 0,
        },
        "inputs": [],
        "randomness": {"mode": "deterministic"},
        "outputs": [],
        "validation": [{"check": "repository-checks", "status": "pass"}],
        "status": "pass",
        "claims": [],
        "limitations": [],
    }


class AgentRunSemanticParityTests(unittest.TestCase):
    def test_valid_loss_stage_is_accepted(self) -> None:
        payload = valid_run()
        payload["semantics"] = {"loss_stage": "net", "currency": "EUR"}
        validator.validate_run(payload, expected_repository=REPOSITORY)

    def test_unknown_loss_stage_is_rejected(self) -> None:
        payload = valid_run()
        payload["semantics"] = {"loss_stage": "after_everything"}
        with self.assertRaisesRegex(validator.ContractError, "loss_stage"):
            validator.validate_run(payload, expected_repository=REPOSITORY)

    def test_valid_interoperability_comparison_mode_is_accepted(self) -> None:
        payload = valid_run()
        payload["interoperability"] = [
            {
                "target": "external-engine",
                "version": "1.0.0",
                "role": "compare",
                "status": "experimental",
                "comparison_mode": "common_innovations",
                "evidence": [],
            }
        ]
        validator.validate_run(payload, expected_repository=REPOSITORY)

    def test_unknown_interoperability_comparison_mode_is_rejected(self) -> None:
        payload = valid_run()
        payload["interoperability"] = [
            {
                "target": "external-engine",
                "version": "1.0.0",
                "role": "compare",
                "status": "experimental",
                "comparison_mode": "same_seed_means_same_stream",
                "evidence": [],
            }
        ]
        with self.assertRaisesRegex(validator.ContractError, "comparison mode"):
            validator.validate_run(payload, expected_repository=REPOSITORY)


if __name__ == "__main__":
    unittest.main()
