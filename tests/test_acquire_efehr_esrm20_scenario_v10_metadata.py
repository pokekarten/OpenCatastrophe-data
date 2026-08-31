# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import unittest

from scripts import acquire_efehr_esrm20_scenario_v10_metadata as subject


_COMMIT = "a" * 40


class _Response:
    def __init__(self, url: str, payload: object, headers: dict[str, str] | None = None):
        self.status = 200
        self._url = url
        self._raw = io.BytesIO(
            payload
            if type(payload) is bytes
            else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        self.headers = headers or {}

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        return self._raw.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _Opener:
    def __init__(
        self,
        *,
        tag_payload: object,
        tree_pages: list[list[dict[str, str]]],
        header_overrides: dict[int, dict[str, str]] | None = None,
    ):
        self.tag_payload = tag_payload
        self.tree_pages = tree_pages
        self.header_overrides = header_overrides or {}
        self.urls: list[str] = []

    def __call__(self, request, timeout: float):
        self.urls.append(request.full_url)
        if request.full_url == subject.TAG_API_URL:
            return _Response(request.full_url, self.tag_payload)
        for page, payload in enumerate(self.tree_pages, start=1):
            expected = subject._tree_url(_COMMIT, page)
            if request.full_url == expected:
                headers = {
                    "X-Page": str(page),
                    "X-Per-Page": str(subject.PER_PAGE),
                    "X-Next-Page": "" if page == len(self.tree_pages) else str(page + 1),
                }
                headers.update(self.header_overrides.get(page, {}))
                return _Response(request.full_url, payload, headers)
        raise AssertionError(f"unexpected URL: {request.full_url}")


def _blob(path: str, token: str = "b") -> dict[str, str]:
    return {
        "id": token * 40,
        "name": path.rsplit("/", 1)[-1],
        "type": "blob",
        "path": path,
        "mode": "100644",
    }


def _tree(path: str, token: str = "c") -> dict[str, str]:
    return {
        "id": token * 40,
        "name": path.rsplit("/", 1)[-1],
        "type": "tree",
        "path": path,
        "mode": "040000",
    }


def _tag(commit: str = _COMMIT) -> dict[str, object]:
    return {"name": "v1.0", "commit": {"id": commit}}


class ScenarioV10MetadataTests(unittest.TestCase):
    def _acquire(self, opener: _Opener) -> dict[str, object]:
        return subject.acquire_metadata_for_test(
            opener=opener,
            monotonic=lambda: 0.0,
            now=lambda: "2026-08-31T08:00:00Z",
        )

    def test_resolves_full_tag_and_inventory_without_payload_authority(self) -> None:
        opener = _Opener(
            tag_payload=_tag(),
            tree_pages=[
                [
                    _tree("scenarios"),
                    _blob("scenarios/Thessaloniki_1978/input.ini"),
                    _blob("README.md", "d"),
                ]
            ],
        )
        result = self._acquire(opener)

        self.assertEqual(result["commit_sha"], _COMMIT)
        self.assertEqual(result["entry_count"], 3)
        self.assertEqual(
            [entry["path"] for entry in result["entries"]],
            ["README.md", "scenarios", "scenarios/Thessaloniki_1978/input.ini"],
        )
        self.assertEqual(
            result["event_candidate_paths"],
            ["scenarios/Thessaloniki_1978/input.ini"],
        )
        self.assertIs(result["recursive_tree_complete_within_bounds"], True)
        self.assertIs(result["file_payloads_requested"], False)
        self.assertIs(result["archive_bytes_requested"], False)
        self.assertIs(result["commit_diffs_requested"], False)
        self.assertIs(result["scientific_validation_verified"], False)
        self.assertIs(result["untouched_holdout_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertTrue(all("/repository/files/" not in url for url in opener.urls))
        self.assertTrue(all("/archive" not in url for url in opener.urls))

    def test_inventory_identity_is_stable_under_provider_entry_order(self) -> None:
        entries = [_blob("z.txt"), _tree("scenarios"), _blob("a.txt", "d")]
        first = self._acquire(_Opener(tag_payload=_tag(), tree_pages=[entries]))
        second = self._acquire(
            _Opener(tag_payload=_tag(), tree_pages=[list(reversed(entries))])
        )
        self.assertEqual(first["inventory_metadata_sha256"], second["inventory_metadata_sha256"])
        self.assertEqual(first["entries"], second["entries"])

    def test_multi_page_inventory_requires_explicit_pagination_and_stays_complete(self) -> None:
        page_one = [_blob(f"p/{index:03d}.txt") for index in range(subject.PER_PAGE)]
        page_two = [_blob("p/final.txt", "d")]
        result = self._acquire(
            _Opener(tag_payload=_tag(), tree_pages=[page_one, page_two])
        )
        self.assertEqual(result["entry_count"], subject.PER_PAGE + 1)
        self.assertIs(result["recursive_tree_complete_within_bounds"], True)

    def test_short_or_non_lowercase_tag_commit_fails_closed(self) -> None:
        for commit in ("a" * 39, "A" * 40):
            with self.subTest(commit=commit):
                with self.assertRaisesRegex(
                    subject.ScenarioV10MetadataError,
                    "full lowercase commit SHA",
                ):
                    self._acquire(
                        _Opener(tag_payload=_tag(commit), tree_pages=[[_blob("a")]])
                    )

    def test_duplicate_json_key_in_tag_response_fails_closed(self) -> None:
        raw = (
            b'{"name":"v1.0","name":"v1.0","commit":{"id":"'
            + _COMMIT.encode()
            + b'"}}'
        )
        opener = _Opener(tag_payload=raw, tree_pages=[[_blob("a")]])
        with self.assertRaisesRegex(subject.ScenarioV10MetadataError, "duplicate JSON key"):
            self._acquire(opener)

    def test_pagination_header_drift_fails_closed(self) -> None:
        entries = [_blob(f"p/{index:03d}.txt") for index in range(subject.PER_PAGE)]
        opener = _Opener(
            tag_payload=_tag(),
            tree_pages=[entries, [_blob("p/final.txt", "d")]],
            header_overrides={1: {"X-Next-Page": "3"}},
        )
        with self.assertRaisesRegex(
            subject.ScenarioV10MetadataError,
            "pagination left bounded sequence",
        ):
            self._acquire(opener)

    def test_duplicate_path_across_pages_fails_closed(self) -> None:
        first = [_blob(f"p/{index:03d}.txt") for index in range(subject.PER_PAGE)]
        duplicate = _blob("p/000.txt", "d")
        opener = _Opener(tag_payload=_tag(), tree_pages=[first, [duplicate]])
        with self.assertRaisesRegex(subject.ScenarioV10MetadataError, "duplicate tree path"):
            self._acquire(opener)

    def test_unsupported_tree_entry_type_fails_closed(self) -> None:
        bad = {
            "id": "b" * 40,
            "name": "submodule",
            "type": "commit",
            "path": "submodule",
            "mode": "160000",
        }
        with self.assertRaisesRegex(
            subject.ScenarioV10MetadataError,
            "entry type is outside bounded policy",
        ):
            self._acquire(_Opener(tag_payload=_tag(), tree_pages=[[bad]]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
