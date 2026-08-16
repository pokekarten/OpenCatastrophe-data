# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
import urllib.parse

from scripts import profile_esrm20_scenario_v10_summaries as profile
from scripts import run_esrm20_scenario_v10_summaries_action as action

EXECUTION_SHA = "b" * 40


class FakeHeaders(dict):
    def get(self, key, default=None):
        for observed_key, value in self.items():
            if observed_key.casefold() == key.casefold():
                return value
        return default


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, status: int = 200) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = FakeHeaders(
            {
                "Content-Length": str(len(payload)),
                "Content-Type": "text/csv",
            }
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = (
            len(self._payload)
            if size is None or size < 0
            else min(len(self._payload), self._offset + size)
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


RUPTURE = (
    b"scenario_id,rupture_count,notes\n"
    b"scenario-z,3,provider-summary\n"
    b"scenario-a,1,provider-summary\n"
    b"scenario-z,3,provider-summary\n"
)
SHAKEMAP = (
    b"event_name;shakemap_count;status\n"
    b"Event-B;2;complete\n"
    b"Event-A;4;complete\n"
)


class ScenarioV10SummaryProfileTests(unittest.TestCase):
    def test_profile_summary_bytes_is_strict_bounded_and_returns_only_identity_literals(self) -> None:
        result = profile.profile_summary_bytes(
            profile.SUMMARY_PATHS[0],
            RUPTURE,
            retrieved_at="2026-08-16T23:20:00Z",
        )
        self.assertEqual(result["encoding"], "utf-8")
        self.assertEqual(result["delimiter"], "comma")
        self.assertEqual(result["column_count"], 3)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["headers"], ["scenario_id", "rupture_count", "notes"])
        self.assertEqual(result["identity_columns"], ["scenario_id"])
        self.assertEqual(
            result["identity_values"], {"scenario_id": ["scenario-a", "scenario-z"]}
        )
        expected_identity = hashlib.sha256(
            json.dumps(
                result["identity_values"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(result["identity_set_sha256"], expected_identity)
        self.assertEqual(result["sha256"], hashlib.sha256(RUPTURE).hexdigest())
        self.assertFalse(result["raw_rows_returned"])
        self.assertNotIn("rows", result)

    def test_semicolon_profile_preserves_exact_case_and_values(self) -> None:
        result = profile.profile_summary_bytes(
            profile.SUMMARY_PATHS[1],
            SHAKEMAP,
            retrieved_at="2026-08-16T23:20:01Z",
        )
        self.assertEqual(result["delimiter"], "semicolon")
        self.assertEqual(result["identity_columns"], ["event_name"])
        self.assertEqual(result["identity_values"]["event_name"], ["Event-A", "Event-B"])

    def test_duplicate_header_ragged_rows_nul_and_unknown_path_fail_closed(self) -> None:
        cases = (
            (profile.SUMMARY_PATHS[0], b"scenario_id,SCENARIO_ID\nA,B\n"),
            (profile.SUMMARY_PATHS[0], b"scenario_id,value\nA,1,extra\n"),
            (profile.SUMMARY_PATHS[0], b"scenario_id,value\nA,\x00\n"),
            ("testing_scenarios.xlsx", RUPTURE),
        )
        for path, payload in cases:
            with self.subTest(path=path, payload=payload):
                with self.assertRaises(profile.ScenarioSummaryProfileError):
                    profile.profile_summary_bytes(
                        path, payload, retrieved_at="2026-08-16T23:20:00Z"
                    )

    def test_acquisition_reads_exactly_two_fixed_files_at_immutable_commit(self) -> None:
        payloads = {
            profile.SUMMARY_PATHS[0]: RUPTURE,
            profile.SUMMARY_PATHS[1]: SHAKEMAP,
        }
        calls: list[str] = []
        times = iter(("2026-08-16T23:20:00Z", "2026-08-16T23:20:01Z"))

        def opener(request, timeout):
            calls.append(request.full_url)
            matched_path = None
            for path in profile.SUMMARY_PATHS:
                encoded = urllib.parse.quote(path, safe="")
                if f"/repository/files/{encoded}/raw" in request.full_url:
                    matched_path = path
                    break
            self.assertIsNotNone(matched_path)
            self.assertIn(f"ref={profile.COMMIT_SHA}", request.full_url)
            return FakeResponse(payloads[matched_path], request.full_url)

        result = profile.acquire_and_profile_summaries(
            opener=opener,
            now=lambda: next(times),
            monotonic=lambda: 0.0,
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            [item["repository_path"] for item in result["summaries"]],
            list(profile.SUMMARY_PATHS),
        )
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["scenario_payload_bytes_read"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        joined = "\n".join(calls)
        self.assertNotIn("testing_scenarios.xlsx", joined)
        self.assertNotIn("scenario_ruptures/", joined)
        self.assertNotIn("scenario_shakemaps/", joined)
        self.assertEqual(result["identity_value_count"], 4)


class ScenarioV10SummaryActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        payloads = {
            profile.SUMMARY_PATHS[0]: RUPTURE,
            profile.SUMMARY_PATHS[1]: SHAKEMAP,
        }
        times = iter(("2026-08-16T23:20:00Z", "2026-08-16T23:20:01Z"))

        def opener(request, timeout):
            for path in profile.SUMMARY_PATHS:
                encoded = urllib.parse.quote(path, safe="")
                if f"/repository/files/{encoded}/raw" in request.full_url:
                    return FakeResponse(payloads[path], request.full_url)
            raise AssertionError("unexpected URL")

        return profile.acquire_and_profile_summaries(
            opener=opener,
            now=lambda: next(times),
            monotonic=lambda: 0.0,
        )

    def _blocked_result_body(
        self, *, execution_sha: str, target_sha: str | None = None
    ) -> str:
        result = {
            **action._base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "summary_acquisition_or_profile_failure",
            "profile": None,
        }
        if target_sha is not None:
            result["target_sha"] = target_sha
        return action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )

    def _with_ledger(self, bodies: list[str], callback):
        original = action._FETCH_COMMENTS
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {"user": {"login": action.TRUSTED_RESULT_LOGIN}, "body": body}
            for body in bodies
        ]
        try:
            return callback()
        finally:
            action._FETCH_COMMENTS = original

    def test_request_is_bound_to_issue_and_current_execution_sha(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 488,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(
            body, expected_issue=488, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.ScenarioSummaryExecutionError):
            action.validate_request(
                body, expected_issue=488, execution_sha="c" * 40
            )

    def test_profile_validator_rejects_path_and_authority_widening(self) -> None:
        valid = self._profile()
        action.validate_profile(valid)

        widened = dict(valid)
        widened["scenario_selection_authorized"] = True
        with self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError, "scenario_selection_authorized"
        ):
            action.validate_profile(widened)

        path_drift = json.loads(json.dumps(valid))
        path_drift["summaries"][0]["repository_path"] = "testing_scenarios.xlsx"
        with self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError, "path drifted"
        ):
            action.validate_profile(path_drift)

    def test_terminal_pass_and_blocked_result_are_fail_closed(self) -> None:
        valid = self._profile()
        passed = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": valid,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            passed, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))

        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "summary_acquisition_or_profile_failure",
            "profile": None,
        }
        blocked_body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(
            action.parse_terminal_result(blocked_body, execution_sha=EXECUTION_SHA)
        )
        blocked["profile"] = valid
        bad = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)

    def test_other_valid_sha_is_ignored_for_current_head_dedup(self) -> None:
        historical_sha = "c" * 40
        body = self._blocked_result_body(execution_sha=historical_sha)
        self.assertFalse(
            self._with_ledger(
                [body],
                lambda: action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=EXECUTION_SHA,
                ),
            )
        )

    def test_same_sha_terminal_result_deduplicates(self) -> None:
        body = self._blocked_result_body(execution_sha=EXECUTION_SHA)
        self.assertTrue(
            self._with_ledger(
                [body],
                lambda: action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=EXECUTION_SHA,
                ),
            )
        )

    def test_mismatched_own_target_and_execution_sha_fail_closed(self) -> None:
        body = self._blocked_result_body(
            execution_sha="c" * 40,
            target_sha="d" * 40,
        )
        with self.assertRaisesRegex(
            action.ScenarioSummaryExecutionError,
            "target/execution SHA mismatch",
        ):
            self._with_ledger(
                [body],
                lambda: action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=EXECUTION_SHA,
                ),
            )


if __name__ == "__main__":
    unittest.main()
