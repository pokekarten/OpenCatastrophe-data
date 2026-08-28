# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import json
import unittest
import urllib.parse

from scripts import acquire_esrm20_kosovo_runtime_exposure_intro_tree_delta as subject


class FakeResponse:
    def __init__(self, value, url, *, page=1, next_page=""):
        self._payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self._offset = 0
        self._url = url
        self.headers = {
            "Content-Length": str(len(self._payload)),
            "X-Page": str(page),
            "X-Per-Page": str(subject.PER_PAGE),
            "X-Next-Page": next_page,
        }
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


def blob(path: str, object_id: str, mode="100644"):
    return {"id": object_id, "name": path.rsplit("/", 1)[-1], "type": "blob", "path": path, "mode": mode}


def tree(path: str, object_id: str):
    return {"id": object_id, "name": path.rsplit("/", 1)[-1], "type": "tree", "path": path, "mode": "040000"}


class KosovoRuntimeExposureIntroTreeDeltaTests(unittest.TestCase):
    EXECUTION_SHA = "c" * 40

    def _opener(self, *, candidate=True):
        parent = [
            tree("Exposure", "1" * 40),
            blob("README.md", "2" * 40),
            blob("tools/build_exposure.py", "3" * 40),
        ]
        introduced = [
            tree("Exposure", "4" * 40),
            blob("README.md", "2" * 40),
            blob(subject.TARGET_PATH, "5" * 40),
            blob("tools/build_exposure.py", "6" * 40 if candidate else "3" * 40),
            blob("Exposure/OQ_Exposure_Input_Albania_Res.csv", "7" * 40),
        ]

        def opener(request, timeout):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
            ref = query["ref"][0]
            values = parent if ref == subject.PARENT_SHA else introduced
            return FakeResponse(values, request.full_url)

        return opener

    def _request(self):
        return subject.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": subject.REQUEST_SCHEMA_VERSION,
                "action": subject.ACTION,
                "issue": subject.CONTROL_ISSUE,
                "target_sha": self.EXECUTION_SHA,
                "dataset_id": subject.DATASET_ID,
                "requester": "TEST",
            },
            separators=(",", ":"),
        )

    def test_tree_delta_reports_only_changed_blob_paths(self):
        result = subject.compare_trees_for_test(
            opener=self._opener(),
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-28T20:00:00Z",
        )
        self.assertEqual(result["target_change"], "added")
        self.assertEqual(
            result["changed_paths"],
            [
                {"path": "Exposure/OQ_Exposure_Input_Albania_Res.csv", "status": "added"},
                {"path": subject.TARGET_PATH, "status": "added"},
                {"path": "tools/build_exposure.py", "status": "modified"},
            ],
        )
        self.assertEqual(result["plausible_generator_or_spec_paths"], ["tools/build_exposure.py"])
        self.assertIs(result["diffs_requested"], False)
        self.assertIs(result["file_payloads_requested"], False)
        self.assertNotIn("Exposure", [item["path"] for item in result["changed_paths"]])

    def test_no_plausible_sibling_is_a_valid_bounded_result(self):
        result = subject.compare_trees_for_test(
            opener=self._opener(candidate=False),
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-28T20:00:00Z",
        )
        self.assertEqual(result["plausible_generator_or_spec_path_count"], 0)
        self.assertEqual(result["plausible_generator_or_spec_paths"], [])

    def test_target_must_be_added_by_introducing_commit(self):
        def opener(request, timeout):
            values = [blob(subject.TARGET_PATH, "5" * 40)]
            return FakeResponse(values, request.full_url)

        with self.assertRaisesRegex(subject.KosovoRuntimeExposureTreeDeltaError, "target is not added"):
            subject.compare_trees_for_test(
                opener=opener,
                monotonic=lambda: 0.0,
                now=lambda: "2026-08-28T20:00:00Z",
            )

    def test_request_is_exact_execution_sha_bound(self):
        parsed = subject.validate_request(
            self._request(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=self.EXECUTION_SHA,
        )
        self.assertEqual(parsed["target_sha"], self.EXECUTION_SHA)
        with self.assertRaises(subject.KosovoRuntimeExposureTreeDeltaError):
            subject.validate_request(
                self._request(),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha="d" * 40,
            )

    def test_worker_has_no_file_or_diff_endpoint(self):
        source = inspect.getsource(subject)
        self.assertNotIn("repository/files", source)
        self.assertNotIn("/diff", source)
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(subject.INTRODUCING_SHA, "78e3f05af4fc3f285570172807c54774537ee309")
        self.assertEqual(subject.PARENT_SHA, "8d62f10c36ff58ea1ce88d156e315591e66aa0e6")

    def test_terminal_result_preserves_authority_ceiling(self):
        delta = subject.compare_trees_for_test(
            opener=self._opener(),
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-28T20:00:00Z",
        )
        result = subject._base_result(execution_sha=self.EXECUTION_SHA)
        result.update({"status": "pass", "failure_class": None, "delta": delta})
        self.assertTrue(subject._validate_terminal_payload(result, execution_sha=self.EXECUTION_SHA))
        self.assertIs(result["transform_lineage_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)


if __name__ == "__main__":
    unittest.main()
