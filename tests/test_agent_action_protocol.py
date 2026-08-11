# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.agent_action_protocol import RESULT_MARKER, canonical_result_comment, semantic_request_id
from scripts.post_agent_action_result import post_result
from scripts.prepare_agent_action_result import LedgerError, build_result, find_existing_result
from scripts.validate_agent_action_result import ResultError, validate_result

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/agent-action-dispatch.yml"
SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"

REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "sample_audit",
    "issue": 162,
    "target_sha": "a" * 40,
    "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
    "requester": "slot36-run-a",
}
EXECUTION_SHA = "b" * 40


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self.payload


class AgentActionProtocolTests(unittest.TestCase):
    def test_semantic_identity_ignores_transport_only_fields(self) -> None:
        first = semantic_request_id(REQUEST, EXECUTION_SHA)
        changed = dict(REQUEST, issue=165, requester="slot12-run-b")
        self.assertEqual(first, semantic_request_id(changed, EXECUTION_SHA))

    def test_semantic_identity_changes_with_execution_code(self) -> None:
        self.assertNotEqual(
            semantic_request_id(REQUEST, EXECUTION_SHA),
            semantic_request_id(REQUEST, "c" * 40),
        )

    def test_pass_duplicate_and_blocked_results_are_closed(self) -> None:
        passed = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
        )
        self.assertEqual(passed["status"], "pass")
        self.assertFalse(passed["external_bytes_persisted"])

        duplicate = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            duplicate_result_comment_id=99,
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["failure_class"], "duplicate_request")

        blocked = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            ledger_incomplete=True,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "ledger_incomplete")

    def test_result_validator_rejects_bool_as_integer_and_external_bytes(self) -> None:
        result = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
        )
        for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = True
                with self.assertRaises(ResultError):
                    validate_result(mutated)
        mutated = dict(result)
        mutated["external_bytes_persisted"] = True
        with self.assertRaises(ResultError):
            validate_result(mutated)

    def test_cross_thread_dedup_accepts_only_trusted_valid_results(self) -> None:
        result = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
        )
        semantic_id = result["semantic_request_id"]
        comments = [
            {
                "id": 10,
                "body": canonical_result_comment(result),
                "user": {"login": "untrusted-user"},
            },
            {
                "id": 11,
                "body": canonical_result_comment(result),
                "user": {"login": "github-actions[bot]"},
            },
        ]
        self.assertEqual(find_existing_result(comments, semantic_id, owner_login="pokekarten"), 11)

    def test_malformed_trusted_result_fails_closed(self) -> None:
        comments = [
            {
                "id": 11,
                "body": RESULT_MARKER + "\n{not-json}",
                "user": {"login": "github-actions[bot]"},
            }
        ]
        with self.assertRaises(LedgerError):
            find_existing_result(comments, "a" * 64, owner_login="pokekarten")

    def test_result_schema_matches_initial_observability_boundary(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(schema["properties"]["phase"], {"const": "request_validation"})
        self.assertEqual(set(schema["properties"]["status"]["enum"]), {"pass", "duplicate", "blocked"})
        self.assertIn("scripts/validate_agent_action_result.py", schema["description"])

    def test_poster_revalidates_and_posts_only_canonical_body(self) -> None:
        result = build_result(
            REQUEST,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
        )
        seen = {}

        def opener(request, timeout):
            seen["url"] = request.full_url
            seen["body"] = json.loads(request.data.decode("utf-8"))
            seen["authorization"] = request.headers.get("Authorization")
            return FakeResponse({"id": 321})

        comment_id = post_result(
            result,
            repository="pokekarten/OpenCatastrophe-data",
            expected_issue=162,
            token="test-token",
            opener=opener,
        )
        self.assertEqual(comment_id, 321)
        self.assertEqual(seen["url"], "https://api.github.com/repos/pokekarten/OpenCatastrophe-data/issues/162/comments")
        self.assertEqual(seen["body"], {"body": canonical_result_comment(result)})
        self.assertEqual(seen["authorization"], "Bearer test-token")

    def test_workflow_serializes_only_action_lane_and_isolates_write_permission(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("group: agent-action-dispatch-v1", workflow)
        self.assertNotIn("github.event.comment.id }}", workflow)
        self.assertIn("name: Validate and classify authorized action request", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("name: Publish validated action result", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("python scripts/post_agent_action_result.py", workflow)
        self.assertNotIn("run_command", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("github.event.pull_request.head", workflow)


if __name__ == "__main__":
    unittest.main()
