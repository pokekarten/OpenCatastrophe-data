# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import profile_esrm20_scenario_v10_tree as profile
from scripts import run_esrm20_scenario_v10_tree_action as action

COMMIT = "a" * 40
EXECUTION_SHA = "b" * 40


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
        end = len(self._payload) if size is None or size < 0 else min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _entry(path: str, entry_type: str, object_id: str) -> dict[str, str]:
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": "040000" if entry_type == "tree" else "100644",
    }


class ScenarioV10TreeProfileTests(unittest.TestCase):
    def _happy_opener(self):
        entries = [
            _entry("Athens_1999", "tree", "1" * 40),
            _entry("Athens_1999/job.ini", "blob", "2" * 40),
            _entry("Thessaloniki_1978", "tree", "3" * 40),
            _entry("Thessaloniki_1978/rupture.xml", "blob", "4" * 40),
            _entry("README.md", "blob", "5" * 40),
        ]
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                self.assertEqual(request.full_url, profile._tag_url())
                return FakeResponse(
                    _json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}),
                    request.full_url,
                )
            self.assertEqual(request.full_url, profile._tree_url(COMMIT, 1))
            return FakeResponse(
                _json_bytes(entries),
                request.full_url,
                headers={
                    "X-Page": "1",
                    "X-Per-Page": "100",
                    "X-Next-Page": "",
                    "X-Total": str(len(entries)),
                    "X-Total-Pages": "1",
                },
            )

        return opener, entries, calls

    def test_profile_resolves_tag_then_reads_metadata_only_and_fingerprints_inventory(self) -> None:
        opener, entries, calls = self._happy_opener()
        result = profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(len(calls), 2)
        self.assertIn("/repository/tags/v1.0", calls[0])
        self.assertIn("/repository/tree?", calls[1])
        self.assertNotIn("/repository/files/", "\n".join(calls))
        self.assertEqual(result["project_id"], 273)
        self.assertEqual(result["release_tag"], "v1.0")
        self.assertEqual(result["commit_sha"], COMMIT)
        self.assertEqual(result["entry_count"], 5)
        self.assertEqual(result["blob_count"], 3)
        self.assertEqual(result["tree_count"], 2)
        canonical = "".join(
            f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
            for item in sorted(entries, key=lambda item: (item["path"], item["type"], item["id"]))
        ).encode("utf-8")
        self.assertEqual(result["tree_identity_sha256"], hashlib.sha256(canonical).hexdigest())
        self.assertTrue(result["athens_present"])
        self.assertTrue(result["thessaloniki_present"])
        self.assertEqual(
            {item["event_literal"] for item in result["event_literal_candidates"]},
            {"athens", "thessaloniki"},
        )
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_absent_predeclared_events_are_valid_metadata_result_not_fallback_selection(self) -> None:
        calls = 0
        entries = [_entry("Other_Event/job.ini", "blob", "6" * 40)]

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}), request.full_url)
            return FakeResponse(
                _json_bytes(entries),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "", "X-Total": "1", "X-Total-Pages": "1"},
            )

        result = profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertFalse(result["athens_present"])
        self.assertFalse(result["thessaloniki_present"])
        self.assertEqual(result["event_literal_candidates"], [])
        self.assertFalse(result["scenario_selection_authorized"])

    def test_tag_identity_and_commit_sha_fail_closed(self) -> None:
        for tag_object in (
            {"name": "v1.1", "commit": {"id": COMMIT}},
            {"name": "v1.0", "commit": {"id": "main"}},
            {"name": "v1.0"},
        ):
            with self.subTest(tag_object=tag_object):
                def opener(request, timeout, tag_object=tag_object):
                    return FakeResponse(_json_bytes(tag_object), request.full_url)
                with self.assertRaises(profile.ScenarioTreeProfileError):
                    profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

    def test_tree_shape_unsafe_paths_and_pagination_gap_fail_closed(self) -> None:
        cases = (
            [_entry("../escape.xml", "blob", "7" * 40)],
            [{**_entry("Athens_1999/job.ini", "blob", "8" * 40), "raw_url": "forbidden"}],
        )
        for entries in cases:
            with self.subTest(entries=entries):
                calls = 0
                def opener(request, timeout):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return FakeResponse(_json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}), request.full_url)
                    return FakeResponse(
                        _json_bytes(entries), request.full_url,
                        headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "", "X-Total": "1", "X-Total-Pages": "1"},
                    )
                with self.assertRaises(profile.ScenarioTreeProfileError):
                    profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

        calls = 0
        def gap_opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}), request.full_url)
            return FakeResponse(
                _json_bytes([_entry("README.md", "blob", "9" * 40)]), request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "3"},
            )
        with self.assertRaisesRegex(profile.ScenarioTreeProfileError, "not contiguous"):
            profile.profile_v10_tree(opener=gap_opener, monotonic=lambda: 0.0)


class ScenarioV10TreeActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        opener, _, _ = ScenarioV10TreeProfileTests()._happy_opener()
        return profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

    def test_request_is_bound_to_issue_and_execution_sha(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 285,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(body, expected_issue=285, execution_sha=EXECUTION_SHA)
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.ScenarioTreeExecutionError):
            action.validate_request(body, expected_issue=285, execution_sha="c" * 40)

    def test_profile_and_terminal_result_reject_authority_or_shape_widening(self) -> None:
        valid_profile = self._profile()
        action.validate_profile(valid_profile)
        widened = dict(valid_profile)
        widened["scenario_selection_authorized"] = True
        with self.assertRaisesRegex(action.ScenarioTreeExecutionError, "scenario_selection_authorized"):
            action.validate_profile(widened)

        result = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": valid_profile,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["unexpected"] = True
        bad = action.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self.assertRaisesRegex(action.ScenarioTreeExecutionError, "fields drifted"):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)

    def test_blocked_result_cannot_publish_partial_metadata(self) -> None:
        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "metadata_acquisition_failure",
            "profile": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(blocked, sort_keys=True, separators=(",", ":"))
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        blocked["profile"] = self._profile()
        bad = action.RESULT_MARKER + "\n" + json.dumps(blocked, sort_keys=True, separators=(",", ":"))
        with self.assertRaisesRegex(action.ScenarioTreeExecutionError, "widened evidence"):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
