# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import urllib.parse
import unittest

from scripts.prepare_agent_action_result import (
    PER_PAGE,
    LedgerError,
    fetch_repository_comments,
    ledger_issue_for_request,
)

REPOSITORY = "pokekarten/OpenCatastrophe-data"

ROOT_REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": "efehr_eshm20_root_config_receipt",
    "issue": 335,
    "target_sha": "a" * 40,
    "dataset_id": "efehr.eshm20",
    "requester": "test",
}
SAMPLE_REQUEST = dict(ROOT_REQUEST, action="sample_audit")


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self.payload


class AgentActionLedgerScopeTests(unittest.TestCase):
    def test_network_action_uses_validator_bound_issue_scope(self) -> None:
        self.assertEqual(ledger_issue_for_request(ROOT_REQUEST), 335)
        self.assertIsNone(ledger_issue_for_request(SAMPLE_REQUEST))

    def test_issue_scoped_ledger_reads_only_that_issue_until_short_page(self) -> None:
        calls: list[tuple[str, int, dict[str, list[str]]]] = []

        def opener(request, timeout):
            parsed = urllib.parse.urlsplit(request.full_url)
            query = urllib.parse.parse_qs(parsed.query)
            page = int(query["page"][0])
            calls.append((parsed.path, page, query))
            if page == 1:
                return FakeResponse([{"id": index} for index in range(PER_PAGE)])
            return FakeResponse([{"id": PER_PAGE + 1}])

        comments = fetch_repository_comments(
            REPOSITORY,
            "token",
            issue=335,
            opener=opener,
            max_pages=3,
        )
        expected_path = f"/repos/{REPOSITORY}/issues/335/comments"
        self.assertEqual([(path, page) for path, page, _ in calls], [(expected_path, 1), (expected_path, 2)])
        self.assertNotIn("sort", calls[0][2])
        self.assertNotIn("direction", calls[0][2])
        self.assertEqual(len(comments), PER_PAGE + 1)

    def test_non_network_ledger_keeps_repository_wide_endpoint_and_order(self) -> None:
        seen: list[tuple[str, dict[str, list[str]]]] = []

        def opener(request, timeout):
            parsed = urllib.parse.urlsplit(request.full_url)
            seen.append((parsed.path, urllib.parse.parse_qs(parsed.query)))
            return FakeResponse([])

        self.assertEqual(fetch_repository_comments(REPOSITORY, "token", opener=opener), [])
        self.assertEqual(seen[0][0], f"/repos/{REPOSITORY}/issues/comments")
        self.assertEqual(seen[0][1]["sort"], ["created"])
        self.assertEqual(seen[0][1]["direction"], ["desc"])

    def test_issue_scope_is_type_strict_and_still_fails_closed_at_bound(self) -> None:
        with self.assertRaisesRegex(LedgerError, "positive integer"):
            fetch_repository_comments(REPOSITORY, "token", issue=True)

        def opener(request, timeout):
            return FakeResponse([{"id": index} for index in range(PER_PAGE)])

        with self.assertRaisesRegex(LedgerError, "exceeds the fail-closed scan bound"):
            fetch_repository_comments(
                REPOSITORY,
                "token",
                issue=335,
                opener=opener,
                max_pages=1,
            )


if __name__ == "__main__":
    unittest.main()
