# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
import urllib.parse

from scripts import profile_esrm20_kosovo_site_file_history as profile
from scripts import run_esrm20_kosovo_site_file_history_action as action

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


class KosovoSiteFileHistoryProfileTests(unittest.TestCase):
    def _happy_opener(self):
        page1 = [
            _commit("c", "2021-12-15T12:30:00+00:00", ("b" * 40,)),
            _commit("b", "2021-10-10T08:00:00Z", ("a" * 40,)),
        ]
        page2 = [_commit("a", "2021-08-14T01:02:03+00:00")]
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            page = len(calls)
            self.assertEqual(request.full_url, profile._commits_url(page))
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

    def test_profile_is_fixed_to_project_release_ref_and_exact_kosovo_path(self) -> None:
        opener, calls = self._happy_opener()
        result = profile.profile_history(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(len(calls), 2)
        for url in calls:
            parsed = urllib.parse.urlsplit(url)
            query = urllib.parse.parse_qs(parsed.query)
            self.assertEqual(parsed.path, "/api/v4/projects/269/repository/commits")
            self.assertEqual(query["ref_name"], [profile.REF_NAME])
            self.assertEqual(query["path"], ["Vs30/Site_model_Kosovo.xml"])
            self.assertEqual(query["follow"], ["false"])
            self.assertEqual(query["since"], ["2021-08-13T00:00:00Z"])
            self.assertEqual(query["until"], ["2021-12-16T23:59:59Z"])
            self.assertEqual(query["with_stats"], ["false"])
            self.assertNotIn("/repository/files/", url)
            self.assertNotIn("/diff", url)
            self.assertNotIn("/archive", url)
            self.assertNotIn("/raw", url)

        self.assertEqual(result["project_id"], 269)
        self.assertEqual(result["project_path"], "efehr/esrm20")
        self.assertEqual(result["ref_name"], profile.REF_NAME)
        self.assertEqual(result["file_path"], "Vs30/Site_model_Kosovo.xml")
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
            result["file_history_identity_sha256"],
            hashlib.sha256(canonical).hexdigest(),
        )
        for field in (
            "provider_file_bytes_read",
            "provider_diff_bytes_read",
            "external_bytes_persisted",
            "output_to_invocation_lineage_verified",
            "exact_kosovo_generator_commit_verified",
            "crs_coordinate_semantics_verified",
            "missingness_semantics_verified",
            "site_model_compatibility_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[field])
        encoded = json.dumps(result)
        self.assertNotIn("author_name", encoded)
        self.assertNotIn("author_email", encoded)
        self.assertNotIn("message", encoded)

    def test_input_order_is_canonicalized_by_time_then_sha(self) -> None:
        values = [
            _commit("b", "2021-10-10T08:00:00Z"),
            _commit("a", "2021-10-10T08:00:00Z"),
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

    def test_bad_identity_date_parent_and_duplicate_commit_fail_closed(self) -> None:
        invalid_values = (
            [{**_commit("a", "2021-10-10T00:00:00Z"), "id": "main"}],
            [_commit("a", "2021-12-17T00:00:00Z")],
            [{**_commit("a", "2021-10-10T00:00:00Z"), "committed_date": "2021-10-10T00:00:00"}],
            [{**_commit("a", "2021-10-10T00:00:00Z"), "parent_ids": ["main"]}],
            [_commit("a", "2021-10-10T00:00:00Z"), _commit("a", "2021-10-09T00:00:00Z")],
        )
        for values in invalid_values:
            with self.subTest(values=values):
                def opener(request, timeout, values=values):
                    return FakeResponse(
                        _json_bytes(values),
                        request.full_url,
                        headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
                    )

                with self.assertRaises(profile.KosovoSiteFileHistoryProfileError):
                    profile.profile_history(opener=opener, monotonic=lambda: 0.0)

    def test_invalid_json_empty_history_and_nonfinite_values_fail_closed(self) -> None:
        raw_cases = (
            b"{}",
            b'[{"id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]',
            b"[NaN]",
            b'[{"id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","parent_ids":[],"committed_date":"2021-10-10T00:00:00Z","ignored":1e400}]',
        )
        for payload in raw_cases:
            with self.subTest(payload=payload):
                def opener(request, timeout, payload=payload):
                    return FakeResponse(
                        payload,
                        request.full_url,
                        headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
                    )

                with self.assertRaises(profile.KosovoSiteFileHistoryProfileError):
                    profile.profile_history(opener=opener, monotonic=lambda: 0.0)

        def empty_opener(request, timeout):
            return FakeResponse(
                b"[]",
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": ""},
            )

        with self.assertRaisesRegex(
            profile.KosovoSiteFileHistoryProfileError, "history is empty"
        ):
            profile.profile_history(opener=empty_opener, monotonic=lambda: 0.0)

    def test_pagination_gap_and_fixed_authority_drift_fail_closed(self) -> None:
        def gap_opener(request, timeout):
            return FakeResponse(
                _json_bytes([_commit("a", "2021-10-10T00:00:00Z")]),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "3"},
            )

        with self.assertRaisesRegex(
            profile.KosovoSiteFileHistoryProfileError, "outside policy"
        ):
            profile.profile_history(opener=gap_opener, monotonic=lambda: 0.0)

        original_path = profile.FILE_PATH
        original_follow = profile.FOLLOW_RENAMES
        calls = 0

        def never_open(request, timeout):
            nonlocal calls
            calls += 1
            raise AssertionError("network must not be reached after authority drift")

        try:
            profile.FILE_PATH = "Vs30/Site_model_Iceland.xml"
            with self.assertRaisesRegex(
                profile.KosovoSiteFileHistoryProfileError, "authority drifted"
            ):
                profile.profile_history(opener=never_open, monotonic=lambda: 0.0)
            self.assertEqual(calls, 0)
        finally:
            profile.FILE_PATH = original_path

        try:
            profile.FOLLOW_RENAMES = True
            with self.assertRaisesRegex(
                profile.KosovoSiteFileHistoryProfileError, "authority drifted"
            ):
                profile.profile_history(opener=never_open, monotonic=lambda: 0.0)
            self.assertEqual(calls, 0)
        finally:
            profile.FOLLOW_RENAMES = original_follow


class KosovoSiteFileHistoryActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        opener, _ = KosovoSiteFileHistoryProfileTests()._happy_opener()
        return profile.profile_history(opener=opener, monotonic=lambda: 0.0)

    def _oversized_profile(self) -> dict:
        result = self._profile()
        candidates = [
            {
                "commit_sha": f"{index:040x}",
                "committed_at_utc": "2021-10-10T08:00:00Z",
                "parent_shas": [],
            }
            for index in range(profile.MAX_COMMITS)
        ]
        result["pages_read"] = profile.MAX_PAGES
        result["candidate_commit_count"] = len(candidates)
        result["candidate_commits"] = candidates
        result["file_history_identity_sha256"] = profile._history_sha256(candidates)
        return result

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
        parsed = action.validate_request(
            body, expected_issue=291, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.KosovoSiteFileHistoryExecutionError):
            action.validate_request(
                body, expected_issue=291, execution_sha="f" * 40
            )

    def test_profile_rejects_evidence_or_authority_widening(self) -> None:
        valid = self._profile()
        action.validate_profile(valid)
        for field in (
            "provider_file_bytes_read",
            "provider_diff_bytes_read",
            "output_to_invocation_lineage_verified",
            "exact_kosovo_generator_commit_verified",
            "crs_coordinate_semantics_verified",
            "missingness_semantics_verified",
            "site_model_compatibility_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            widened = dict(valid)
            widened[field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    action.KosovoSiteFileHistoryExecutionError, field
                ):
                    action.validate_profile(widened)

    def test_mutated_candidate_breaks_deterministic_receipt(self) -> None:
        mutated = json.loads(json.dumps(self._profile()))
        mutated["candidate_commits"][0]["commit_sha"] = "d" * 40
        with self.assertRaisesRegex(
            action.KosovoSiteFileHistoryExecutionError, "identity"
        ):
            action.validate_profile(mutated)

    def test_old_head_result_does_not_deduplicate_current_main(self) -> None:
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
        self.assertFalse(
            action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=old_sha))

    def test_blocked_result_cannot_publish_partial_evidence(self) -> None:
        for failure_class in (
            "metadata_acquisition_failure",
            "result_publication_limit_exceeded",
        ):
            blocked = {
                **action._base_result(execution_sha=EXECUTION_SHA),
                "status": "blocked",
                "failure_class": failure_class,
                "profile": None,
            }
            body = action.RESULT_MARKER + "\n" + json.dumps(
                blocked, sort_keys=True, separators=(",", ":")
            )
            self.assertTrue(
                action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
            )
            blocked["profile"] = self._profile()
            bad = action.RESULT_MARKER + "\n" + json.dumps(
                blocked, sort_keys=True, separators=(",", ":")
            )
            with self.assertRaisesRegex(
                action.KosovoSiteFileHistoryExecutionError, "widened evidence"
            ):
                action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)

        invalid = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "unexpected_failure",
            "profile": None,
        }
        with self.assertRaisesRegex(
            action.KosovoSiteFileHistoryExecutionError, "widened evidence"
        ):
            action.parse_terminal_result(
                action.RESULT_MARKER
                + "\n"
                + json.dumps(invalid, sort_keys=True, separators=(",", ":")),
                execution_sha=EXECUTION_SHA,
            )

    def test_oversized_valid_profile_terminalizes_and_deduplicates(self) -> None:
        oversized = self._oversized_profile()
        action.validate_profile(oversized)
        oversized_pass = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": oversized,
        }
        self.assertGreater(
            len(
                json.dumps(
                    oversized_pass, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ),
            action.MAX_RESULT_UTF8_BYTES,
        )

        profile_calls = 0
        comments: list[dict[str, object]] = []
        original_profile_function = profile.profile_history
        original_profile_authority = action._PROFILE
        original_fetch_function = action.fetch_repository_comments
        original_fetch_authority = action._FETCH_COMMENTS

        def fake_profile() -> dict:
            nonlocal profile_calls
            profile_calls += 1
            return oversized

        def fake_fetch(*args, **kwargs):
            return list(comments)

        try:
            profile.profile_history = fake_profile
            action._PROFILE = fake_profile
            action.fetch_repository_comments = fake_fetch
            action._FETCH_COMMENTS = fake_fetch

            blocked = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="test-token",
                execution_sha=EXECUTION_SHA,
            )
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(
                blocked["failure_class"], "result_publication_limit_exceeded"
            )
            self.assertIsNone(blocked["profile"])
            blocked_json = json.dumps(
                blocked, sort_keys=True, separators=(",", ":")
            )
            self.assertLessEqual(
                len(blocked_json.encode("utf-8")), action.MAX_RESULT_UTF8_BYTES
            )
            body = action.RESULT_MARKER + "\n" + blocked_json
            self.assertTrue(
                action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
            )
            comments.append(
                {
                    "user": {"login": action.TRUSTED_RESULT_LOGIN},
                    "body": body,
                }
            )

            duplicate = action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="test-token",
                execution_sha=EXECUTION_SHA,
            )
            self.assertEqual(duplicate["status"], "duplicate")
            self.assertIsNone(duplicate["profile"])
            self.assertEqual(profile_calls, 1)
        finally:
            profile.profile_history = original_profile_function
            action._PROFILE = original_profile_authority
            action.fetch_repository_comments = original_fetch_function
            action._FETCH_COMMENTS = original_fetch_authority


if __name__ == "__main__":
    unittest.main()
