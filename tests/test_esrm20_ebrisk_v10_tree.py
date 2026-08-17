# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts import run_esrm20_ebrisk_v10_tree_action as action

COMMIT = profile.EXPECTED_COMMIT_SHA
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
        end = len(self._payload) if size is None or size < 0 else min(
            len(self._payload), self._offset + size
        )
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


class EbriskV10TreeProfileTests(unittest.TestCase):
    def _happy_opener(self):
        entries = [
            _entry("Configuration_Files", "tree", "1" * 40),
            _entry("Configuration_Files/config_ebrisk_group1.ini", "blob", "2" * 40),
            _entry("Configuration_Files/config_ebrisk_group2.ini", "blob", "3" * 40),
            _entry("Configuration_Files/conif_ebrisk_group3.ini", "blob", "4" * 40),
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

    def test_profile_freezes_commit_and_exact_case_preserved_template_paths(self) -> None:
        opener, entries, calls = self._happy_opener()
        result = profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(len(calls), 2)
        self.assertIn("/repository/tags/v1.0", calls[0])
        self.assertIn("/repository/tree?", calls[1])
        self.assertNotIn("/repository/files/", "\n".join(calls))
        self.assertEqual(result["project_id"], 269)
        self.assertEqual(result["commit_sha"], COMMIT)
        self.assertEqual(
            [item["path"] for item in result["ebrisk_templates"]],
            [
                "Configuration_Files/config_ebrisk_group1.ini",
                "Configuration_Files/config_ebrisk_group2.ini",
                "Configuration_Files/conif_ebrisk_group3.ini",
            ],
        )
        canonical = "".join(
            f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
            for item in sorted(entries, key=lambda item: (item["path"], item["type"], item["id"]))
        ).encode("utf-8")
        self.assertEqual(result["tree_identity_sha256"], hashlib.sha256(canonical).hexdigest())
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["historical_group_assignment_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_tag_repointing_fails_closed_before_tree_request(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            return FakeResponse(
                _json_bytes({"name": "v1.0", "commit": {"id": "a" * 40}}),
                request.full_url,
            )

        with self.assertRaisesRegex(profile.EbriskTreeProfileError, "frozen commit"):
            profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(calls, 1)

    def test_missing_duplicate_case_drift_or_non_blob_template_fails_closed(self) -> None:
        baseline = [
            _entry("Configuration_Files/config_ebrisk_group1.ini", "blob", "2" * 40),
            _entry("Configuration_Files/config_ebrisk_group2.ini", "blob", "3" * 40),
            _entry("Configuration_Files/conif_ebrisk_group3.ini", "blob", "4" * 40),
        ]
        cases = {
            "missing": baseline[:-1],
            "duplicate": baseline + [_entry("Other/config_ebrisk_group1.ini", "blob", "6" * 40)],
            "case-drift": [
                _entry("Configuration_Files/Config_ebrisk_group1.ini", "blob", "2" * 40),
                *baseline[1:],
            ],
            "tree-not-blob": [
                _entry("Configuration_Files/config_ebrisk_group1.ini", "tree", "2" * 40),
                *baseline[1:],
            ],
        }

        for label, entries in cases.items():
            with self.subTest(label=label):
                calls = 0

                def opener(request, timeout):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return FakeResponse(
                            _json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}),
                            request.full_url,
                        )
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

                with self.assertRaises(profile.EbriskTreeProfileError):
                    profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

    def test_unsafe_paths_and_pagination_gap_fail_closed(self) -> None:
        cases = (
            [
                _entry("../config_ebrisk_group1.ini", "blob", "7" * 40),
                _entry("x/config_ebrisk_group2.ini", "blob", "8" * 40),
                _entry("x/conif_ebrisk_group3.ini", "blob", "9" * 40),
            ],
            [
                {**_entry("x/config_ebrisk_group1.ini", "blob", "7" * 40), "raw_url": "forbidden"},
                _entry("x/config_ebrisk_group2.ini", "blob", "8" * 40),
                _entry("x/conif_ebrisk_group3.ini", "blob", "9" * 40),
            ],
        )
        for entries in cases:
            with self.subTest(entries=entries):
                calls = 0

                def opener(request, timeout):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return FakeResponse(
                            _json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}),
                            request.full_url,
                        )
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

                with self.assertRaises(profile.EbriskTreeProfileError):
                    profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

        calls = 0

        def gap_opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(
                    _json_bytes({"name": "v1.0", "commit": {"id": COMMIT}}),
                    request.full_url,
                )
            return FakeResponse(
                _json_bytes(
                    [
                        _entry("x/config_ebrisk_group1.ini", "blob", "7" * 40),
                        _entry("x/config_ebrisk_group2.ini", "blob", "8" * 40),
                        _entry("x/conif_ebrisk_group3.ini", "blob", "9" * 40),
                    ]
                ),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "3"},
            )

        with self.assertRaisesRegex(profile.EbriskTreeProfileError, "not contiguous"):
            profile.profile_v10_tree(opener=gap_opener, monotonic=lambda: 0.0)


class EbriskV10TreeActionTests(unittest.TestCase):
    def _profile(self) -> dict:
        opener, _, _ = EbriskV10TreeProfileTests()._happy_opener()
        return profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)

    def test_request_is_bound_to_issue_and_execution_sha(self) -> None:
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": action.REQUEST_SCHEMA_VERSION,
                "issue": 281,
                "target_sha": EXECUTION_SHA,
                "requester": "test-runner",
            },
            separators=(",", ":"),
        )
        parsed = action.validate_request(body, expected_issue=281, execution_sha=EXECUTION_SHA)
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(action.EbriskTreeExecutionError):
            action.validate_request(body, expected_issue=281, execution_sha="c" * 40)

    def test_profile_and_terminal_result_reject_authority_or_shape_widening(self) -> None:
        valid_profile = self._profile()
        action.validate_profile(valid_profile)
        widened = dict(valid_profile)
        widened["historical_group_assignment_authorized"] = True
        with self.assertRaisesRegex(
            action.EbriskTreeExecutionError, "historical_group_assignment_authorized"
        ):
            action.validate_profile(widened)

        result = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "profile": valid_profile,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(action.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["unexpected"] = True
        bad = action.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(action.EbriskTreeExecutionError, "fields drifted"):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)

    def test_profile_validator_rejects_path_basename_case_drift(self) -> None:
        valid_profile = self._profile()
        changed = dict(valid_profile)
        changed["ebrisk_templates"] = [dict(item) for item in valid_profile["ebrisk_templates"]]
        changed["ebrisk_templates"][0]["path"] = (
            "Configuration_Files/Config_ebrisk_group1.ini"
        )
        with self.assertRaisesRegex(action.EbriskTreeExecutionError, "path/basename"):
            action.validate_profile(changed)

    def test_blocked_result_cannot_publish_partial_metadata(self) -> None:
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
        with self.assertRaisesRegex(action.EbriskTreeExecutionError, "widened evidence"):
            action.parse_terminal_result(bad, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
