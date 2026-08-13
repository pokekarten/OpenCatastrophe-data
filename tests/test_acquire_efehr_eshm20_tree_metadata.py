# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import json
import unittest

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_eshm20_tree_metadata import (
    BRANCH,
    BRANCH_API_URL,
    DATASET_ID,
    PROJECT_ID,
    TREE_PER_PAGE,
    TREE_PREFIX,
    _tree_url,
    acquire_eshm20_tree_metadata,
)

COMMIT = "a" * 40


class FakeResponse:
    def __init__(self, value, url, *, headers=None):
        self._payload = json.dumps(value, separators=(",", ":")).encode()
        self._offset = 0
        self._url = url
        self.headers = headers or {"Content-Length": str(len(self._payload))}
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


def branch_response(commit=COMMIT, name=BRANCH):
    return FakeResponse({"name": name, "commit": {"id": commit}}, BRANCH_API_URL)


def tree_response(path):
    value = [{"id": "b" * 40, "name": path.rsplit("/", 1)[-1], "type": "blob", "path": path, "mode": "100644"}]
    response = FakeResponse(value, _tree_url(COMMIT, 1))
    response.headers.update({"X-Page": "1", "X-Per-Page": str(TREE_PER_PAGE), "X-Next-Page": ""})
    return response


class Eshm20TreeMetadataTests(unittest.TestCase):
    def test_fixed_target_happy_path_is_metadata_only(self):
        path = TREE_PREFIX + "job.ini"
        responses = [branch_response(), tree_response(path)]
        result = acquire_eshm20_tree_metadata(
            opener=lambda request, timeout: responses.pop(0),
            now=lambda: "2026-08-13T21:15:00Z",
            monotonic=lambda: 0.0,
        )
        self.assertEqual(result["resolved_commit_sha"], COMMIT)
        self.assertEqual(result["entries"][0]["path"], path)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn("content", result)

    def test_worker_has_no_caller_target_surface(self):
        self.assertEqual(set(inspect.signature(acquire_eshm20_tree_metadata).parameters), {"opener", "now", "monotonic"})
        self.assertEqual(PROJECT_ID, 197)
        self.assertEqual(DATASET_ID, "efehr.eshm20")
        self.assertEqual(BRANCH, "master")

    def test_wrong_branch_or_prefix_fails_closed(self):
        with self.assertRaises(EfehrAcquisitionError):
            acquire_eshm20_tree_metadata(
                opener=lambda request, timeout: branch_response(name="main"),
                now=lambda: "2026-08-13T21:15:00Z",
                monotonic=lambda: 0.0,
            )
        responses = [branch_response(), tree_response("oq_computational/other/job.ini")]
        with self.assertRaisesRegex(EfehrAcquisitionError, "escaped"):
            acquire_eshm20_tree_metadata(
                opener=lambda request, timeout: responses.pop(0),
                now=lambda: "2026-08-13T21:15:00Z",
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
