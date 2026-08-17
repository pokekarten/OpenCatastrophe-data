# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts import run_esrm20_ebrisk_v10_tree_action as action

EXECUTION_SHA = "d" * 40


class FakeHeaders(dict):
    def get(self, key, default=None):
        for observed_key, value in self.items():
            if observed_key.casefold() == key.casefold():
                return value
        return default


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, headers=None) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = 200
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


def _tag_payload(extra: str = "") -> bytes:
    suffix = f",{extra}" if extra else ""
    return (
        '{"name":"v1.0","commit":{"id":"'
        + profile.EXPECTED_COMMIT_SHA
        + '"}'
        + suffix
        + "}"
    ).encode("utf-8")


def _entry(path: str, object_id: str) -> dict[str, str]:
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": "blob",
        "path": path,
        "mode": "100644",
    }


def _tree_payload(*, omit_last: bool = False) -> bytes:
    entries = [
        _entry("Configuration_Files/config_ebrisk_group1.ini", "1" * 40),
        _entry("Configuration_Files/config_ebrisk_group2.ini", "2" * 40),
        _entry("Configuration_Files/conif_ebrisk_group3.ini", "3" * 40),
    ]
    if omit_last:
        entries.pop()
    return json.dumps(entries, separators=(",", ":")).encode("utf-8")


def _tree_headers(entry_count: int) -> dict[str, str]:
    return {
        "X-Page": "1",
        "X-Per-Page": str(profile.PER_PAGE),
        "X-Next-Page": "",
        "X-Total": str(entry_count),
        "X-Total-Pages": "1",
    }


class EbriskFailureClassificationTests(unittest.TestCase):
    def test_tag_network_failure_is_classified(self) -> None:
        def opener(request, timeout):
            raise OSError("synthetic network failure")

        with self.assertRaises(profile.EbriskTreeProfileError) as caught:
            profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(
            caught.exception.failure_class, "tag_metadata_acquisition_failure"
        )

    def test_tag_validation_and_float_overflow_are_classified(self) -> None:
        payloads = (
            b'{"name":"wrong","commit":{"id":"' + profile.EXPECTED_COMMIT_SHA.encode() + b'"}}',
            _tag_payload('"ignored":1e400'),
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                def opener(request, timeout, payload=payload):
                    return FakeResponse(payload, request.full_url)

                with self.assertRaises(profile.EbriskTreeProfileError) as caught:
                    profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
                self.assertEqual(
                    caught.exception.failure_class,
                    "tag_metadata_validation_failure",
                )

    def test_tree_network_failure_is_classified(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_tag_payload(), request.full_url)
            raise OSError("synthetic tree network failure")

        with self.assertRaises(profile.EbriskTreeProfileError) as caught:
            profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(
            caught.exception.failure_class, "tree_metadata_acquisition_failure"
        )

    def test_tree_validation_failure_is_classified(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_tag_payload(), request.full_url)
            return FakeResponse(
                _tree_payload(),
                request.full_url,
                headers={
                    "X-Page": "1",
                    "X-Per-Page": str(profile.PER_PAGE),
                    "X-Next-Page": "3",
                },
            )

        with self.assertRaises(profile.EbriskTreeProfileError) as caught:
            profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(
            caught.exception.failure_class, "tree_metadata_validation_failure"
        )

    def test_template_resolution_failure_is_classified(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_tag_payload(), request.full_url)
            payload = _tree_payload(omit_last=True)
            return FakeResponse(
                payload,
                request.full_url,
                headers=_tree_headers(2),
            )

        with self.assertRaises(profile.EbriskTreeProfileError) as caught:
            profile.profile_v10_tree(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(
            caught.exception.failure_class, "template_resolution_failure"
        )


class EbriskFailurePublicationTests(unittest.TestCase):
    def _execute_with_failure(self, failure_class: str) -> dict:
        def failing_profile():
            raise profile.EbriskTreeProfileError(
                "synthetic classified failure",
                failure_class=failure_class,
            )

        with (
            mock.patch.object(action, "has_terminal_result", return_value=False),
            mock.patch.object(profile, "profile_v10_tree", failing_profile),
            mock.patch.object(action, "_PROFILE", failing_profile),
        ):
            return action.execute_profile(
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                execution_sha=EXECUTION_SHA,
            )

    def test_each_safe_failure_class_is_published_without_partial_profile(self) -> None:
        for failure_class in sorted(profile.FAILURE_CLASSES):
            with self.subTest(failure_class=failure_class):
                result = self._execute_with_failure(failure_class)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["failure_class"], failure_class)
                self.assertIsNone(result["profile"])

    def test_unclassified_profiler_error_is_not_published_as_bounded_evidence(self) -> None:
        def failing_profile():
            raise profile.EbriskTreeProfileError("unclassified programming failure")

        with (
            mock.patch.object(action, "has_terminal_result", return_value=False),
            mock.patch.object(profile, "profile_v10_tree", failing_profile),
            mock.patch.object(action, "_PROFILE", failing_profile),
        ):
            with self.assertRaisesRegex(
                action.EbriskTreeExecutionError,
                "not safely classified",
            ):
                action.execute_profile(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )

    def test_legacy_blocked_terminal_remains_valid_historical_evidence(self) -> None:
        historical_sha = "a" * 40
        legacy = {
            **action._base_result(execution_sha=historical_sha),
            "status": "blocked",
            "failure_class": action.LEGACY_BLOCKED_FAILURE_CLASS,
            "profile": None,
        }
        comment = {
            "user": {"login": action.TRUSTED_RESULT_LOGIN},
            "body": action.RESULT_MARKER
            + "\n"
            + json.dumps(legacy, sort_keys=True, separators=(",", ":")),
        }
        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=[comment]):
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )

    def test_unknown_failure_class_is_rejected(self) -> None:
        blocked = {
            **action._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "provider_error_details_leaked",
            "profile": None,
        }
        body = action.RESULT_MARKER + "\n" + json.dumps(
            blocked, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(action.EbriskTreeExecutionError, "widened evidence"):
            action.parse_terminal_result(body, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
