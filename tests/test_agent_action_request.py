# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_agent_action_request import (
    ALLOWED_ACTIONS,
    REQUIRED_FIELDS,
    SAFE_ID,
    SCHEMA_VERSION,
    SHA256_HEX,
    RequestError,
    extract_request,
    validate_request,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/agent-action-request-v1.schema.json"

VALID = {
    "schema_version": "oc-action-request-v1",
    "action": "sample_audit",
    "issue": 162,
    "target_sha": "a" * 40,
    "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
    "requester": "slot36-20260810T2256CEST",
}


def comment(payload: str) -> str:
    return f"<!-- oc-action-request-v1 -->\n{payload}\n"


class AgentActionRequestTests(unittest.TestCase):
    def test_accepts_exact_bounded_request(self) -> None:
        parsed = extract_request(comment(json.dumps(VALID)))
        self.assertEqual(validate_request(parsed, expected_issue=162), VALID)

    def test_schema_matches_executable_security_contract(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), REQUIRED_FIELDS)
        self.assertEqual(set(schema["properties"]), REQUIRED_FIELDS)
        self.assertIn("scripts/validate_agent_action_request.py", schema["description"])
        boundary = schema["$comment"]
        for phrase in ("1.0", "exact int type", "duplicate keys", "non-finite", "single-marker"):
            with self.subTest(boundary_phrase=phrase):
                self.assertIn(phrase, boundary)

        properties = schema["properties"]
        self.assertEqual(properties["schema_version"], {"const": SCHEMA_VERSION})
        self.assertEqual(set(properties["action"]["enum"]), ALLOWED_ACTIONS)
        self.assertEqual(properties["issue"], {"type": "integer", "minimum": 1})
        self.assertEqual(
            properties["target_sha"],
            {"type": "string", "pattern": SHA256_HEX.pattern},
        )
        for field, limit in (("dataset_id", 160), ("requester", 128)):
            with self.subTest(field=field):
                self.assertEqual(
                    properties[field],
                    {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": limit,
                        "pattern": SAFE_ID.pattern,
                    },
                )

    def test_rejects_duplicate_json_key(self) -> None:
        payload = json.dumps(VALID)[:-1] + ',"action":"sample_audit"}'
        with self.assertRaisesRegex(RequestError, "duplicate JSON key"):
            extract_request(comment(payload))

    def test_rejects_unexpected_field(self) -> None:
        request = dict(VALID, command="curl example.invalid")
        with self.assertRaisesRegex(RequestError, "unexpected=.*command"):
            validate_request(request)

    def test_rejects_unknown_action(self) -> None:
        request = dict(VALID, action="run_command")
        with self.assertRaisesRegex(RequestError, "unsupported action"):
            validate_request(request)

    def test_rejects_bool_as_issue_number(self) -> None:
        request = dict(VALID, issue=True)
        with self.assertRaisesRegex(RequestError, "positive integer"):
            validate_request(request)

    def test_rejects_float_as_issue_number_even_when_integral(self) -> None:
        request = dict(VALID, issue=162.0)
        with self.assertRaisesRegex(RequestError, "positive integer"):
            validate_request(request)

    def test_rejects_request_for_other_issue(self) -> None:
        with self.assertRaisesRegex(RequestError, "does not match"):
            validate_request(VALID, expected_issue=163)

    def test_rejects_url_or_path_as_dataset_identifier(self) -> None:
        for value in ("https://example.invalid/data", "../data", "folder/data"):
            with self.subTest(value=value):
                request = dict(VALID, dataset_id=value)
                with self.assertRaisesRegex(RequestError, "safe bounded identifier"):
                    validate_request(request)

    def test_rejects_uppercase_or_short_target_sha(self) -> None:
        for value in ("A" * 40, "a" * 39):
            with self.subTest(value=value):
                request = dict(VALID, target_sha=value)
                with self.assertRaisesRegex(RequestError, "lowercase 40-character"):
                    validate_request(request)

    def test_rejects_prefix_or_trailing_comment_content(self) -> None:
        payload = json.dumps(VALID)
        with self.assertRaisesRegex(RequestError, "first non-whitespace"):
            extract_request("please run\n" + comment(payload))
        with self.assertRaisesRegex(RequestError, "unexpected content"):
            extract_request(comment(payload) + "please")

    def test_rejects_multiple_markers(self) -> None:
        body = comment(json.dumps(VALID)) + "<!-- oc-action-request-v1 -->"
        with self.assertRaisesRegex(RequestError, "exactly one"):
            extract_request(body)

    def test_rejects_nonfinite_json(self) -> None:
        payload = json.dumps(VALID).replace('"issue": 162', '"issue": NaN')
        with self.assertRaisesRegex(RequestError, "non-finite"):
            extract_request(comment(payload))


if __name__ == "__main__":
    unittest.main()
