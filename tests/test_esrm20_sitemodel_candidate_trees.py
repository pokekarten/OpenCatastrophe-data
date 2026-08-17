# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import profile_esrm20_sitemodel_candidate_trees as profile


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


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _entry(path: str, object_id: str, *, entry_type: str = "blob") -> dict[str, str]:
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": "040000" if entry_type == "tree" else "100644",
    }


def _headers(count: int) -> dict[str, str]:
    return {
        "X-Page": "1",
        "X-Per-Page": str(profile.PER_PAGE),
        "X-Next-Page": "",
        "X-Total": str(count),
        "X-Total-Pages": "1",
    }


class SiteModelCandidateTreeTests(unittest.TestCase):
    def _candidate_entries(self) -> list[list[dict[str, str]]]:
        return [
            [
                _entry("README.md", "1" * 40),
                _entry("exposure2site.py", "2" * 40),
                _entry("docs", "3" * 40, entry_type="tree"),
            ],
            [
                _entry("README.md", "1" * 40),
                _entry("exposure2site.py", "4" * 40),
                _entry("docs", "5" * 40, entry_type="tree"),
                _entry("docs/guide.md", "6" * 40),
            ],
            [
                _entry("README.md", "1" * 40),
                _entry("exposure2site.py", "2" * 40),
                _entry("docs", "3" * 40, entry_type="tree"),
            ],
        ]

    def _happy_opener(self):
        entries_by_commit = dict(
            zip(
                [item["commit_sha"] for item in profile.CANDIDATE_HISTORY],
                self._candidate_entries(),
                strict=True,
            )
        )
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            for commit_sha, entries in entries_by_commit.items():
                if request.full_url == profile._tree_url(commit_sha, 1):
                    return FakeResponse(
                        _json_bytes(entries),
                        request.full_url,
                        headers=_headers(len(entries)),
                    )
            raise AssertionError(f"unexpected URL: {request.full_url}")

        return opener, entries_by_commit, calls

    def test_profile_is_fixed_to_three_candidates_and_returns_changed_blobs_only(self) -> None:
        opener, entries_by_commit, calls = self._happy_opener()
        result = profile.profile_candidate_trees(
            opener=opener,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(len(calls), 3)
        for history_item in profile.CANDIDATE_HISTORY:
            commit_sha = history_item["commit_sha"]
            self.assertIn(profile._tree_url(commit_sha, 1), calls)
        joined = "\n".join(calls)
        self.assertNotIn("/repository/files/", joined)
        self.assertNotIn("/repository/commits/", joined)
        self.assertNotIn("/archive", joined)
        self.assertNotIn("/raw/", joined)

        self.assertEqual(result["project_id"], 278)
        self.assertEqual(
            result["history_identity_sha256"],
            profile.HISTORY_IDENTITY_SHA256,
        )
        self.assertEqual(
            [item["commit_sha"] for item in result["candidate_tree_profiles"]],
            [item["commit_sha"] for item in profile.CANDIDATE_HISTORY],
        )
        self.assertEqual(
            [item["path"] for item in result["changed_blobs"]],
            ["docs/guide.md", "exposure2site.py"],
        )
        self.assertEqual(result["changed_blob_count"], 2)
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["exact_kosovo_generator_commit_verified"])
        self.assertFalse(result["crs_coordinate_semantics_verified"])
        self.assertFalse(result["missingness_semantics_verified"])
        self.assertFalse(result["site_model_compatibility_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

        first_entries = entries_by_commit[profile.CANDIDATE_HISTORY[0]["commit_sha"]]
        canonical = "".join(
            f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
            for entry in sorted(
                first_entries,
                key=lambda item: (item["path"], item["type"], item["id"]),
            )
        ).encode("utf-8")
        self.assertEqual(
            result["candidate_tree_profiles"][0]["tree_identity_sha256"],
            hashlib.sha256(canonical).hexdigest(),
        )

    def test_history_receipt_drift_fails_before_network(self) -> None:
        original = profile.HISTORY_IDENTITY_SHA256
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            raise AssertionError("network must not be reached")

        try:
            profile.HISTORY_IDENTITY_SHA256 = "0" * 64
            with self.assertRaisesRegex(
                profile.SiteModelCandidateTreeError,
                "history candidate identity drifted",
            ):
                profile.profile_candidate_trees(
                    opener=opener,
                    monotonic=lambda: 0.0,
                )
        finally:
            profile.HISTORY_IDENTITY_SHA256 = original
        self.assertEqual(calls, 0)

    def test_noncanonical_or_widened_tree_entry_fails_closed(self) -> None:
        bad_cases = [
            _entry("../writer.py", "a" * 40),
            {**_entry("writer.py", "a" * 40), "raw_url": "forbidden"},
            {**_entry("writer.py", "a" * 40), "mode": "10064"},
            {**_entry("writer.py", "a" * 40), "id": "A" * 40},
        ]
        first_commit = profile.CANDIDATE_HISTORY[0]["commit_sha"]
        for bad_entry in bad_cases:
            with self.subTest(bad_entry=bad_entry):
                calls = 0

                def opener(request, timeout):
                    nonlocal calls
                    calls += 1
                    self.assertEqual(request.full_url, profile._tree_url(first_commit, 1))
                    return FakeResponse(
                        _json_bytes([bad_entry]),
                        request.full_url,
                        headers=_headers(1),
                    )

                with self.assertRaises(profile.SiteModelCandidateTreeError):
                    profile.profile_candidate_trees(
                        opener=opener,
                        monotonic=lambda: 0.0,
                    )
                self.assertEqual(calls, 1)

    def test_duplicate_path_fails_closed(self) -> None:
        first_commit = profile.CANDIDATE_HISTORY[0]["commit_sha"]

        def opener(request, timeout):
            self.assertEqual(request.full_url, profile._tree_url(first_commit, 1))
            entries = [
                _entry("writer.py", "a" * 40),
                _entry("writer.py", "b" * 40),
            ]
            return FakeResponse(
                _json_bytes(entries),
                request.full_url,
                headers=_headers(len(entries)),
            )

        with self.assertRaisesRegex(
            profile.SiteModelCandidateTreeError,
            "duplicate path",
        ):
            profile.profile_candidate_trees(
                opener=opener,
                monotonic=lambda: 0.0,
            )

    def test_pagination_gap_fails_closed(self) -> None:
        first_commit = profile.CANDIDATE_HISTORY[0]["commit_sha"]

        def opener(request, timeout):
            self.assertEqual(request.full_url, profile._tree_url(first_commit, 1))
            return FakeResponse(
                _json_bytes([_entry("writer.py", "a" * 40)]),
                request.full_url,
                headers={
                    "X-Page": "1",
                    "X-Per-Page": str(profile.PER_PAGE),
                    "X-Next-Page": "3",
                },
            )

        with self.assertRaisesRegex(
            profile.SiteModelCandidateTreeError,
            "not contiguous",
        ):
            profile.profile_candidate_trees(
                opener=opener,
                monotonic=lambda: 0.0,
            )

    def test_changed_blob_output_is_bounded(self) -> None:
        original = profile.MAX_CHANGED_BLOBS
        try:
            profile.MAX_CHANGED_BLOBS = 1
            trees = [
                (
                    "a" * 40,
                    [
                        _entry("one.py", "1" * 40),
                        _entry("two.py", "2" * 40),
                    ],
                ),
                (
                    "b" * 40,
                    [
                        _entry("one.py", "3" * 40),
                        _entry("two.py", "4" * 40),
                    ],
                ),
            ]
            with self.assertRaisesRegex(
                profile.SiteModelCandidateTreeError,
                "changed-blob set exceeds policy",
            ):
                profile._changed_blobs(trees)
        finally:
            profile.MAX_CHANGED_BLOBS = original


if __name__ == "__main__":
    unittest.main()
