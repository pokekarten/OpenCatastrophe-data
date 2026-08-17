# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import profile_esrm20_sitemodel_history as profile
from scripts import run_esrm20_sitemodel_history_action as action

EXECUTION_SHA = "e" * 40


class FakeHeaders(dict):
    def get(self, key, default=None):
        for observed_key, value in self.items():
            if observed_key.casefold() == key.casefold():
                return value
        return default


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, headers=None, status: int = 200) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = FakeHeaders(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size is None or size < 0 else min(
            len(self._payload), self._offset + size
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _commit(sha_char: str, committed: str, parents: tuple[str, ...] = ()) -> dict:
    return {
        "id": sha_char * 40,
        "short_id": sha_char * 8,
        "created_at": committed,
        "parent_ids": list(parents),
        "title": "ignored metadata",
        "message": "ignored metadata",
        "author_name": "ignored",
        "author_email": "ignored@example.invalid",
        "committed_date": committed,
    }


class SiteModelHistoryProfileTests(unittest.TestCase):
    def _happy_opener(self):
        page1 = [
            _commit("c", "2021-12-16T12:30:00+00:00", ("b" * 40,)),
            _commit("b", "2021-12-10T08:00:00Z", ("a" * 40,)),
        ]
        page2 = [_commit("a", "2021-12-06T01:02:03+00:00")]
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            page = len(calls)
            expected = profile._commits_url(page)
            self.assertEqual(request.full_url, expected)
            payload = page1 if page == 1 else page2
            return FakeResponse(
                _json_bytes(payload),
                request.full_url,
                headers={
                    "X-Page": str(page),
                    "X-Per-Page": str(profile.PER_PAGE),
                    "X-Next-Page": "2" if page == 1 else "",
                },
            )

        return opener, calls

    def test_profile_reads_only_fixed_commit_metadata_and_emits_canonical_receipt(self) -> None:
        opener, calls = self._happy_opener()
        result = profile.profile_history(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(len(calls), 2)
        for url in calls:
            self.assertIn("/api/v4/projects/278/repository/commits?", url)
            self.assertIn("ref_name=main", url)
            self.assertIn("since=2021-12-06T00%3A00%3A00Z", url)
            self.assertIn("until=2021-12-16T23%3A59%3A59Z", url)
            self.assertNotIn("/repository/files/", url)
            self.assertNotIn("/archive", url)
        self.assertEqual(result["project_id"], 278)
        self.assertEqual(result["project_path"], "efehr/esrm20_sitemodel")
        self.assertEqual(result["ref_name"], "main")
        self.assertEqual(result["candidate_commit_count"], 3)
        self.assertEqual(
            [item["commit_sha"] for item in result["candidate_commits"]],
            ["c" * 40, "b" * 40, "a" * 40],
        )
        canonical = "".join(
            f"{item['commit_sha']}\t{item['committed_at_utc']}\t{','.join(item['parent_shas'])}\n"
            for item in result["candidate_commits"]
        ).encode("utf-8")
        self.assertEqual(
            result["history_identity_sha256"], hashlib.sha256(canonical).hexdigest()
        )
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["exact_kosovo_generator_commit_verified"])
        self.assertFalse(result["crs_coordinate_semantics_verified"])
        self.assertFalse(result["missingness_semantics_verified"])
        self.assertFalse(result["site_model_compatibility_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("author_name", json.dumps(result))
        self.assertNotIn("author_email", json.dumps(result))
        self.assertNotIn("message", json.dumps(result))

    def test_input_order_is_canonicalized_by_committed_time_then_sha(self) -> None:
        values = [
            _commit("b", "2021-12-10T08:00:00Z"),
            _commit("a", "2021-12-10T08:00:00Z"),
            _commit("c", "2021-12-15T08:00:00Z"),
        ]

        def opener(request, timeout):
            return FakeResponse(
                _json_bytes(values),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
            )

        result = profile.profile_history(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(
            [item["commit_sha"] for item in result["candidate_commits"]],
            ["c" * 40, "a" * 40, "b" * 40],
        )

    def test_malformed_commit_identity_date_parent_or_duplicate_fails_closed(self) -> None:
        invalid_values = (
            [{**_commit("a", "2021-12-10T00:00:00Z"), "id": "main"}],
            [_commit("a", "2021-12-17T00:00:00Z")],
            [{**_commit("a", "2021-12-10T00:00:00Z"), "committed_date": "2021-12-10T00:00:00"}],
            [{**_commit("a", "2021-12-10T00:00:00Z"), "parent_ids": ["main"]}],
            [_commit("a", "2021-12-10T00:00:00Z"), _commit("a", "2021-12-09T00:00:00Z")],
        )
        for values in invalid_values:
            with self.subTest(values=values):
                def opener(request, timeout, values=values):
                    return FakeResponse(
                        _json_bytes(values),
                        request.full_url,
                        headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
                    )
                with self.assertRaises(profile.SiteModelHistoryProfileError):
                    profile.profile_history(opener=opener, monotonic=lambda: 0.0)

    def test_empty_nonarray_duplicate_json_key_and_nonfinite_fail_closed(self) -> None:
        raw_cases = (
            b"{}",
            b'[{"id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]',
            b"[NaN]",
            b'[{"id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","parent_ids":[],"committed_date":"2021-12-10T00:00:00Z","ignored":1e400}]',
        )
        for payload in raw_cases:
            with self.subTest(payload=payload):
                def opener(request, timeout, payload=payload):
                    return FakeResponse(
                        payload,
                        request.full_url,
                        headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
                    )
                with self.assertRaises(profile.SiteModelHistoryProfileError):
                    profile.profile_history(opener=opener, monotonic=lambda: 0.0)

        def empty_opener(request, timeout):
            return FakeResponse(
                b"[]",
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
            )
        with self.assertRaisesRegex(profile.SiteModelHistoryProfileError, "window is empty"):
            profile.profile_history(opener=empty_opener, monotonic=lambda: 0.0)

    def test_pagination_gap_and_authority_drift_fail_before_evidence(self) -> None:
        def gap_opener(request, timeout):
            return FakeResponse(
                _json_bytes([_commit("a", "2021-12-10T00:00:00Z")]),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "3"},
            )
        with self.assertRaisesRegex(profile.SiteModelHistoryProfileError, "not contiguous"):
            profile.profile_history(opener=gap_opener, monotonic=lambda: 0.0)

        original = profile.PROJECT_ID
        calls = 0
        try:
            profile.PROJECT_ID = 279
            def never_open(request, timeout):
                nonlocal calls
                calls += 1
                raise AssertionError("network must not be reached after authority drift")
            with self.assertRaisesRegex(profile.SiteModelHistoryProfileError, "authority drifted"):
                profile.profile_history(opener=never_open, monotonic=lambda: 0.0)
            self.assertEqual(calls, 0)
        finally:
            profile.PROJECT_ID = original


class SiteModelHistoryActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        opener, _ = SiteModelHistoryProfileTests()._happy_opener()
        return profile.profile_history(opener=opener, monotonic=lambda: 0.0)

    def test_request_is_exact_head_bound(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 291,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(body, expected_issue=291, execution_sha=EXECUTION_SHA)
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.SiteModelHistoryExecutionError):
            action.validate_request(body, expected_issue=291, execution_sha="f" * 40)

    def test_profile_rejects_authority_widening_or_identity_mutation(self) -> None:
        valid = self._profile()
        action.validate_profile(valid)
        widened = dict(valid)
        widened["exact_kosovo_generator_commit_verified"] = True
        with self.assertRaisesRegex(
            action.SiteModelHistoryExecutionError, "exact_kosovo_generator_commit_verified"
        ):
            action.validate_profile(widened)

        mutated = json.loads(json.dumps(valid))
        mutated["candidate_commits"][0]["commit_sha"] = "d" * 40
        with self.assertRaisesRegex(action.SiteModelHistoryExecutionError, "identity"):
            action.validate_profile(mutated)

    def test_old_head_terminal_result_is_ignored_not_treated_as_current_duplicate(self) -> None:
        old_sha = "d" * 40
        result = {
            **action._base_result(execution_sha=old_sha),
            "status": "pass",
            "failure_class": None,
            "profile": self._profile(),
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertFalse(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        self.assertTrue(action.parse_terminal_result(body, execution_sha=old_sha))

    def test_blocked_result_cannot_publish_partial_profile(self) -> None:
        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "metadata_acquisition_failure",
            "profile": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        blocked["profile"] = self._profile()
        bad = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(action.SiteModelHistoryExecutionError, "widened evidence"):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
