# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import json
import unittest

from scripts import acquire_esrm20_kosovo_runtime_exposure_history_metadata as subject


class FakeResponse:
    def __init__(self, value, url):
        self._payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self._offset = 0
        self._url = url
        self.headers = {"Content-Length": str(len(self._payload))}
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return self._url

    def read(self, size=-1):
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size < 0 else min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def commit(commit_id: str, title: str, *, parents=None, date="2021-12-16T12:00:00Z"):
    return {
        "id": commit_id,
        "parent_ids": ["f" * 40] if parents is None else parents,
        "committed_date": date,
        "title": title,
        "message": title + "\n\nignored body",
        "author_name": "ignored",
        "author_email": "ignored@example.invalid",
    }


class KosovoRuntimeExposureHistoryTests(unittest.TestCase):
    SHA = "a" * 40

    def _request(self):
        return subject.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": subject.REQUEST_SCHEMA_VERSION,
                "action": subject.ACTION,
                "issue": subject.CONTROL_ISSUE,
                "target_sha": self.SHA,
                "dataset_id": subject.DATASET_ID,
                "requester": "TEST",
            },
            separators=(",", ":"),
        )

    def test_fixed_history_is_metadata_only_and_path_bound(self):
        requested = []
        items = [
            commit("a" * 40, "Update Kosovo exposure"),
            commit("b" * 40, "Initial OpenQuake exposure format", parents=[]),
        ]

        def opener(request, timeout):
            requested.append(request.full_url)
            return FakeResponse(items, request.full_url)

        history = subject.acquire_history_metadata_for_test(
            opener=opener,
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-28T18:30:00Z",
        )

        self.assertEqual(history["commit_count"], 2)
        self.assertEqual([item["id"] for item in history["commits"]], ["a" * 40, "b" * 40])
        self.assertTrue(history["commits"][1]["title_generator_hint"])
        self.assertIs(history["diffs_requested"], False)
        self.assertIs(history["file_payloads_requested"], False)
        self.assertIn("ref_name=" + subject.REF_SHA, requested[0])
        self.assertIn("path=Exposure%2FOQ_Exposure_Input_Kosovo_Res.csv", requested[0])
        self.assertIn("follow=false", requested[0])
        serialized = json.dumps(history, sort_keys=True)
        self.assertNotIn("author_email", serialized)
        self.assertNotIn("ignored body", serialized)

    def test_worker_has_no_caller_selected_provider_target(self):
        self.assertEqual(
            set(inspect.signature(subject.acquire_history_metadata_for_test).parameters),
            {"opener", "monotonic", "now"},
        )
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(subject.REF_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(subject.REPOSITORY_PATH, "Exposure/OQ_Exposure_Input_Kosovo_Res.csv")
        source = inspect.getsource(subject)
        self.assertNotIn("repository/files", source)
        self.assertNotIn("repository/archive", source)
        self.assertNotIn("commits/{sha}/diff", source)

    def test_request_is_exact_execution_sha_bound(self):
        parsed = subject.validate_request(
            self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=self.SHA
        )
        self.assertEqual(parsed["target_sha"], self.SHA)
        with self.assertRaises(subject.KosovoRuntimeExposureHistoryError):
            subject.validate_request(
                self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha="b" * 40
            )

    def test_duplicate_commit_ids_fail_closed(self):
        items = [commit("a" * 40, "one"), commit("a" * 40, "two")]
        with self.assertRaisesRegex(subject.KosovoRuntimeExposureHistoryError, "duplicate commit"):
            subject.acquire_history_metadata_for_test(
                opener=lambda request, timeout: FakeResponse(items, request.full_url),
                monotonic=lambda: 0.0,
                now=lambda: "2026-08-28T18:30:00Z",
            )

    def test_commit_title_is_single_line_bounded_metadata(self):
        bad = [commit("a" * 40, "bad\nsecond line")]
        with self.assertRaisesRegex(subject.KosovoRuntimeExposureHistoryError, "commit title"):
            subject.acquire_history_metadata_for_test(
                opener=lambda request, timeout: FakeResponse(bad, request.full_url),
                monotonic=lambda: 0.0,
                now=lambda: "2026-08-28T18:30:00Z",
            )

    def test_terminal_result_preserves_authority_ceiling(self):
        history = subject.acquire_history_metadata_for_test(
            opener=lambda request, timeout: FakeResponse(
                [commit("a" * 40, "Format exposure for OpenQuake")], request.full_url
            ),
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-28T18:30:00Z",
        )
        result = subject._base_result(execution_sha=self.SHA)
        result.update({"status": "pass", "failure_class": None, "history": history})
        self.assertTrue(subject._validate_terminal_payload(result, execution_sha=self.SHA))
        self.assertIs(result["external_file_bytes_accessed"], False)
        self.assertIs(result["transform_lineage_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)


if __name__ == "__main__":
    unittest.main()
