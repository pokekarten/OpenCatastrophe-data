# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.parse
import unittest
from pathlib import Path

from scripts.agent_action_protocol import RESULT_MARKER, canonical_result_comment, semantic_request_id
from scripts.post_agent_action_result import PostError, post_result
from scripts.prepare_agent_action_result import (
    PER_PAGE,
    LedgerError,
    build_result,
    fetch_repository_comments,
    find_existing_result,
)
from scripts.validate_agent_action_result import ResultError, validate_result

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/agent-action-dispatch.yml"
SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED = "2026-08-11T08:00:00Z"
FINISHED = "2026-08-11T08:00:01Z"

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


def result_for(**kwargs):
    parameters = {
        "repository": REPOSITORY,
        "execution_sha": EXECUTION_SHA,
        "source_comment_id": 100,
        "run_id": 200,
        "run_attempt": 1,
        "started_at": STARTED,
        "finished_at": FINISHED,
    }
    parameters.update(kwargs)
    return build_result(REQUEST, **parameters)


class AgentActionProtocolTests(unittest.TestCase):
    def test_semantic_identity_ignores_transport_only_fields(self) -> None:
        first = semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        changed = dict(REQUEST, issue=165, requester="slot12-run-b")
        self.assertEqual(first, semantic_request_id(changed, EXECUTION_SHA, REPOSITORY))

    def test_semantic_identity_changes_with_execution_code_or_repository(self) -> None:
        baseline = semantic_request_id(REQUEST, EXECUTION_SHA, REPOSITORY)
        self.assertNotEqual(baseline, semantic_request_id(REQUEST, "c" * 40, REPOSITORY))
        self.assertNotEqual(baseline, semantic_request_id(REQUEST, EXECUTION_SHA, "pokekarten/OtherRepo"))

    def test_pass_duplicate_and_blocked_results_are_closed(self) -> None:
        passed = result_for()
        self.assertEqual(passed["status"], "pass")
        self.assertFalse(passed["external_bytes_persisted"])
        self.assertEqual(
            passed["evidence"],
            {"request_validated": True, "ledger_scan_complete": True, "prior_result_reused": False},
        )

        duplicate = result_for(
            source_comment_id=101,
            run_id=201,
            duplicate_result_comment_id=99,
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["failure_class"], "duplicate_request")
        self.assertTrue(duplicate["evidence"]["prior_result_reused"])

        blocked = result_for(
            source_comment_id=102,
            run_id=202,
            ledger_incomplete=True,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["failure_class"], "ledger_incomplete")
        self.assertFalse(blocked["evidence"]["ledger_scan_complete"])

    def test_result_validator_rejects_bool_as_integer_and_external_bytes(self) -> None:
        result = result_for()
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

    def test_result_validator_recomputes_semantic_binding(self) -> None:
        result = result_for()
        for field, value in (
            ("semantic_request_id", "0" * 64),
            ("dataset_id", "other.dataset"),
            ("target_sha", "c" * 40),
            ("execution_sha", "d" * 40),
            ("repository", "pokekarten/OtherRepo"),
        ):
            with self.subTest(field=field):
                mutated = dict(result)
                mutated[field] = value
                with self.assertRaisesRegex(ResultError, "semantic_request_id"):
                    validate_result(mutated)

    def test_result_validator_rejects_time_reversal_and_evidence_drift(self) -> None:
        result = result_for()
        reversed_time = dict(result, started_at=FINISHED, finished_at=STARTED)
        with self.assertRaisesRegex(ResultError, "must not precede"):
            validate_result(reversed_time)

        wrong_state = dict(result)
        wrong_state["evidence"] = dict(result["evidence"], prior_result_reused=True)
        with self.assertRaisesRegex(ResultError, "pass result requires"):
            validate_result(wrong_state)

        type_confused = dict(result)
        type_confused["evidence"] = dict(result["evidence"], ledger_scan_complete=1)
        with self.assertRaisesRegex(ResultError, "must be boolean"):
            validate_result(type_confused)

    def test_cross_thread_dedup_accepts_only_trusted_valid_results(self) -> None:
        result = result_for()
        semantic_id = result["semantic_request_id"]
        comments = [
            {"id": 10, "body": canonical_result_comment(result), "user": {"login": "untrusted-user"}},
            {"id": 11, "body": canonical_result_comment(result), "user": {"login": "github-actions[bot]"}},
        ]
        self.assertEqual(find_existing_result(comments, semantic_id, owner_login="pokekarten"), 11)

    def test_semantically_forged_trusted_result_fails_closed(self) -> None:
        result = result_for()
        forged = dict(result, dataset_id="other.dataset")
        comments = [
            {"id": 11, "body": canonical_result_comment(forged), "user": {"login": "github-actions[bot]"}}
        ]
        with self.assertRaisesRegex(LedgerError, "fails result validation"):
            find_existing_result(comments, result["semantic_request_id"], owner_login="pokekarten")

    def test_malformed_trusted_result_fails_closed_but_untrusted_lookalike_is_ignored(self) -> None:
        malformed = RESULT_MARKER + "\n{not-json}"
        self.assertIsNone(
            find_existing_result(
                [{"id": 10, "body": malformed, "user": {"login": "untrusted-user"}}],
                "a" * 64,
                owner_login="pokekarten",
            )
        )
        with self.assertRaises(LedgerError):
            find_existing_result(
                [{"id": 11, "body": malformed, "user": {"login": "github-actions[bot]"}}],
                "a" * 64,
                owner_login="pokekarten",
            )

    def test_repository_comment_ledger_reads_until_short_page(self) -> None:
        calls = []

        def opener(request, timeout):
            page = int(urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)["page"][0])
            calls.append(page)
            if page == 1:
                return FakeResponse([{"id": index} for index in range(PER_PAGE)])
            return FakeResponse([{"id": PER_PAGE + 1}])

        comments = fetch_repository_comments(REPOSITORY, "token", opener=opener, max_pages=3)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(len(comments), PER_PAGE + 1)

    def test_repository_comment_ledger_fails_closed_at_completeness_bound(self) -> None:
        def opener(request, timeout):
            return FakeResponse([{"id": index} for index in range(PER_PAGE)])

        with self.assertRaisesRegex(LedgerError, "exceeds the fail-closed scan bound"):
            fetch_repository_comments(REPOSITORY, "token", opener=opener, max_pages=1)

    def test_result_schema_matches_self_contained_observability_boundary(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["external_bytes_persisted"], {"const": False})
        self.assertEqual(schema["properties"]["phase"], {"const": "request_validation"})
        self.assertEqual(set(schema["properties"]["status"]["enum"]), {"pass", "duplicate", "blocked"})
        self.assertIn("repository", schema["required"])
        self.assertIn("started_at", schema["required"])
        self.assertIn("finished_at", schema["required"])
        self.assertIn("evidence", schema["required"])
        self.assertFalse(schema["properties"]["evidence"]["additionalProperties"])
        self.assertIn("scripts/validate_agent_action_result.py", schema["description"])

    def test_poster_revalidates_receipt_repository_and_posts_only_canonical_body(self) -> None:
        result = result_for()
        seen = {}

        def opener(request, timeout):
            seen["url"] = request.full_url
            seen["body"] = json.loads(request.data.decode("utf-8"))
            seen["authorization"] = request.headers.get("Authorization")
            return FakeResponse({"id": 321})

        comment_id = post_result(
            result,
            repository=REPOSITORY,
            expected_issue=162,
            token="test-token",
            opener=opener,
        )
        self.assertEqual(comment_id, 321)
        self.assertEqual(seen["url"], f"https://api.github.com/repos/{REPOSITORY}/issues/162/comments")
        self.assertEqual(seen["body"], {"body": canonical_result_comment(result)})
        self.assertEqual(seen["authorization"], "Bearer test-token")

        with self.assertRaisesRegex(PostError, "repository does not match"):
            post_result(
                result,
                repository="pokekarten/OtherRepo",
                expected_issue=162,
                token="test-token",
                opener=opener,
            )

    def test_workflow_serializes_only_action_lane_and_isolates_write_permission(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("group: agent-action-dispatch-v1", workflow)
        self.assertNotIn("group: agent-action-request-${{ github.event.comment.id }}", workflow)
        self.assertIn("name: Validate and classify authorized action request", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("name: Publish validated action result", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("execution_sha: ${{ steps.prepare-result.outputs.execution_sha }}", workflow)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", workflow)
        self.assertIn("python scripts/post_agent_action_result.py", workflow)
        self.assertNotIn("run_command", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("github.event.pull_request.head", workflow)
        self.assertNotIn(RESULT_MARKER, "<!-- oc-action-request-v1 -->")


if __name__ == "__main__":
    unittest.main()
