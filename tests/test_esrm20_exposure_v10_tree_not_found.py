# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
import urllib.error
from pathlib import Path

from scripts import profile_esrm20_exposure_v10_tree as profile


class FakeHeaders(dict):
    def get(self, key, default=None):
        for observed, value in self.items():
            if observed.casefold() == key.casefold():
                return value
        return default


class FakeResponse:
    def __init__(self, payload: bytes, url: str) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = 200
        self.headers = FakeHeaders()

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


def _tag_payload() -> bytes:
    return json.dumps(
        {
            "name": profile.RELEASE_TAG,
            "target": "f" * 40,
            "commit": {"id": profile.EXPECTED_COMMIT_SHA},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class ExposureTreeNotFoundClassificationTests(unittest.TestCase):
    def _failure_class_for_tree_http_status(self, status: int) -> str | None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(_tag_payload(), request.full_url)
            raise urllib.error.HTTPError(
                request.full_url,
                status,
                "synthetic",
                hdrs=None,
                fp=None,
            )

        with self.assertRaises(profile.ExposureTreeProfileError) as caught:
            profile._profile_v10_tree_for_test(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(calls, 2)
        return caught.exception.failure_class

    def test_fixed_tree_http_404_is_bounded_not_found(self) -> None:
        self.assertEqual(
            self._failure_class_for_tree_http_status(404),
            "tree_metadata_not_found",
        )

    def test_other_tree_http_status_remains_generic_acquisition_failure(self) -> None:
        self.assertEqual(
            self._failure_class_for_tree_http_status(403),
            "tree_metadata_acquisition_failure",
        )

    def test_workflow_publisher_accepts_only_named_bounded_not_found_class(self) -> None:
        workflow = Path(".github/workflows/esrm20-exposure-v10-tree.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('.failure_class == "tree_metadata_not_found"', workflow)
        self.assertNotIn("http_status", workflow)
        self.assertNotIn("exception", workflow)


if __name__ == "__main__":
    unittest.main()
