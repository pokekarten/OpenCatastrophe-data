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
    COMMIT if False else DATASET_ID,
    MAX_TREE_PAGES,
    PROJECT_ID,
    TREE_PER_PAGE,
    TREE_PREFIX,
    _tree_url,
    acquire_eshm20_tree_metadata,
)

COMMIT = "a" * 40
RETRIEVED_AT = "2026-08-13T21:15:00Z"


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, headers=None, status: int = 200):
        self._payload = payload
        self._offset = 0
        self._url = url
        self.headers = headers or {}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return self._url

    def read(self, size=-1):
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size is None or size < 0 else min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def branch_response(commit=COMMIT, name=BRANCH):
    payload = encoded({"name": name, "commit": {"id": commit}})
    return FakeResponse(payload, BRANCH_API_URL, headers={"Content-Length": str(len(payload))})


def item(path, object_id="b" * 40):
    return {"id": object_id, "name": path.rsplit("/", 1)[-1], "type": "blob", "path": path, "mode": "100644"}


def tree_response(page, items, next_page=""):
    payload = encoded(items)
    return FakeResponse(payload, _tree_url(COMMIT, page), headers={
        "Content-Length": str(len(payload)),
        "X-Page": str(page),
        "X-Per-Page": str(TREE_PER_PAGE),
        "X-Next-Page": next_page,
    })


class Eshm20TreeMetadataTests(unittest.TestCase):
    def test_fixed_target_and_two_page_metadata_inventory(self):
        path_a = TREE_PREFIX + "job.ini"
        path_b = TREE_PREFIX + "source_model_logic_tree.xml"
        responses = [branch_response(), tree_response(1, [item(path_b)], "2"), tree_response(2, [item(path_a, "c" * 40)])]
        calls = []

        def opener(request, timeout):
            calls.append(request.full_url)
            return responses.pop(0)

        result = acquire_eshm20_tree_metadata(opener=opener, now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)
        self.assertEqual(calls, [BRANCH_API_URL, _tree_url(COMMIT, 1), _tree_url(COMMIT, 2)])
        self.assertEqual(result["resolved_commit_sha"], COMMIT)
        self.assertEqual([entry["path"] for entry in result["entries"]], [path_a, path_b])
        self.assertEqual(result["tree_page_count"], 2)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn("content", result)
        self.assertNotIn("body", result)

    def test_no_caller_controlled_target_surface(self):
        self.assertEqual(set(inspect.signature(acquire_eshm20_tree_metadata).parameters), {"opener", "now", "monotonic"})
        self.assertEqual(PROJECT_ID, 197)
        self.assertEqual(BRANCH, "master")
        self.assertEqual(DATASET_ID, "efehr.eshm20")

    def test_branch_identity_and_sha_fail_closed(self):
        for first in (branch_response(name="main"), branch_response(commit="A" * 40)):
            with self.assertRaises(EfehrAcquisitionError):
                acquire_eshm20_tree_metadata(opener=lambda request, timeout, first=first: first, now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)

    def test_tree_escape_and_duplicate_paths_fail_closed(self):
        responses = [branch_response(), tree_response(1, [item("oq_computational/other/job.ini")])]
        with self.assertRaisesRegex(EfehrAcquisitionError, "escaped"):
            acquire_eshm20_tree_metadata(opener=lambda request, timeout: responses.pop(0), now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)

        path = TREE_PREFIX + "job.ini"
        responses = [branch_response(), tree_response(1, [item(path)], "2"), tree_response(2, [item(path, "c" * 40)])]
        with self.assertRaisesRegex(EfehrAcquisitionError, "duplicate/conflicting"):
            acquire_eshm20_tree_metadata(opener=lambda request, timeout: responses.pop(0), now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)

    def test_pagination_must_move_forward_within_bound(self):
        path = TREE_PREFIX + "job.ini"
        for next_page in ("1", "x", str(MAX_TREE_PAGES + 1)):
            responses = [branch_response(), tree_response(1, [item(path)], next_page)]
            with self.assertRaises(EfehrAcquisitionError):
                acquire_eshm20_tree_metadata(opener=lambda request, timeout, responses=responses: responses.pop(0), now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)


if __name__ == "__main__":
    unittest.main()
