# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_agent_action_request import ALLOWED_ACTIONS as REQUEST_ALLOWED_ACTIONS
from scripts.validate_agent_action_result import ALLOWED_ACTIONS as RESULT_ALLOWED_ACTIONS

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = ROOT / "schemas/agent-action-request-v1.schema.json"
RESULT_SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"


def _schema_actions(path: Path) -> list[str]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    actions = schema["properties"]["action"]["enum"]
    if not isinstance(actions, list) or not all(type(action) is str for action in actions):
        raise AssertionError(f"{path.name} action enum must contain only strings")
    return actions


class AgentActionActionSetConsistencyTests(unittest.TestCase):
    def test_request_and_result_validators_share_one_closed_action_set(self) -> None:
        self.assertEqual(RESULT_ALLOWED_ACTIONS, REQUEST_ALLOWED_ACTIONS)

    def test_request_schema_action_enum_matches_closed_action_set(self) -> None:
        actions = _schema_actions(REQUEST_SCHEMA)
        self.assertEqual(len(actions), len(set(actions)), "request schema action enum contains duplicates")
        self.assertEqual(set(actions), REQUEST_ALLOWED_ACTIONS)

    def test_result_schema_action_enum_matches_closed_action_set(self) -> None:
        actions = _schema_actions(RESULT_SCHEMA)
        self.assertEqual(len(actions), len(set(actions)), "result schema action enum contains duplicates")
        self.assertEqual(set(actions), RESULT_ALLOWED_ACTIONS)


if __name__ == "__main__":
    unittest.main()
