# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import json
import unittest
from unittest.mock import patch

import scripts.acquire_efehr_esrm20_scenario_tree_metadata as scenario_metadata
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_esrm20_scenario_tree_metadata import (
    DATASET_ID,
    PROJECT_ID,
    PROJECT_PATH,
    RELEASE_TAG,
    TAG_API_URL,
    TREE_PER_PAGE,
    _tree_url,
    acquire_esrm20_scenario_tree_metadata,
)

COMMIT = "a" * 40
ANNOTATED_TAG_OBJECT = "c" * 40


class FakeResponse:
    def __init__(self, value, url, *, headers=None, raw=None):
        self._payload = (
            raw
            if raw is not None
            else json.dumps(value, separators=(",", ":")).encode()
        )
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
        end = (
            len(self._payload)
            if size < 0
            else min(len(self._payload), self._offset + size)
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def tag_response(commit=COMMIT, *, name=RELEASE_TAG, target=None):
    return FakeResponse(
        {
            "name": name,
            "target": commit if target is None else target,
            "commit": {"id": commit},
        },
        TAG_API_URL,
    )


def tree_item(path, *, object_id="b" * 40, entry_type="blob", mode="100644"):
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": mode,
    }


def tree_response(items, *, page=1, next_page=""):
    response = FakeResponse(items, _tree_url(COMMIT, page))
    response.headers.update(
        {
            "X-Page": str(page),
            "X-Per-Page": str(TREE_PER_PAGE),
            "X-Next-Page": next_page,
        }
    )
    return response


class Esrm20ScenarioTreeMetadataTests(unittest.TestCase):
    def test_fixed_target_happy_path_is_metadata_only(self):
        responses = [
            tag_response(target=ANNOTATED_TAG_OBJECT),
            tree_response(
                [
                    tree_item("README.md"),
                    tree_item("scenarios", entry_type="tree", mode="040000"),
                    tree_item("scenarios/example/job.ini"),
                ]
            ),
        ]
        result = acquire_esrm20_scenario_tree_metadata(
            opener=lambda request, timeout: responses.pop(0),
            now=lambda: "2026-08-15T17:35:00Z",
            monotonic=lambda: 0.0,
        )

        self.assertEqual(result["resolved_commit_sha"], COMMIT)
        self.assertEqual(
            [entry["path"] for entry in result["entries"]],
            ["README.md", "scenarios", "scenarios/example/job.ini"],
        )
        self.assertEqual(result["tree_page_count"], 1)
        self.assertEqual(result["tree_entry_count"], 3)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("content", result)
        self.assertNotIn("archive", result)

    def test_worker_has_no_caller_target_surface(self):
        self.assertEqual(
            set(inspect.signature(acquire_esrm20_scenario_tree_metadata).parameters),
            {"opener", "now", "monotonic"},
        )
        self.assertEqual(PROJECT_ID, 273)
        self.assertEqual(PROJECT_PATH, "efehr/esrm20_scenario_tests")
        self.assertEqual(RELEASE_TAG, "v1.0")
        self.assertEqual(DATASET_ID, "efehr.esrm20.scenario-tests.v1.0")

        source = inspect.getsource(scenario_metadata)
        self.assertNotIn("repository/archive", source)
        self.assertNotIn("raw_file_api_url", source)
        self.assertNotIn("repository/files", source)

    def test_public_authority_rebinding_fails_before_opener(self):
        cases = (
            ("TAG_API_URL", "https://gitlab.seismo.ethz.ch/api/v4/projects/999/repository/tags/v1.0"),
            ("TREE_API_URL", "https://gitlab.seismo.ethz.ch/api/v4/projects/999/repository/tree"),
            ("RELEASE_TAG", "v1.1"),
            ("PROJECT_ID", 999),
            ("PROJECT_PATH", "efehr/not_the_scenario_repository"),
            ("PROVIDER_HOST", "example.invalid"),
            ("PROVIDER_ROOT", "https://example.invalid"),
        )
        for name, value in cases:
            with self.subTest(name=name):
                calls = []

                def opener(request, timeout):
                    calls.append(request.full_url)
                    raise AssertionError("opener must not be called after authority drift")

                with patch.object(scenario_metadata, name, value):
                    with self.assertRaisesRegex(EfehrAcquisitionError, "authority drifted"):
                        acquire_esrm20_scenario_tree_metadata(
                            opener=opener,
                            now=lambda: "2026-08-15T17:35:00Z",
                            monotonic=lambda: 0.0,
                        )
                self.assertEqual(calls, [])

    def test_tree_request_is_bound_to_resolved_commit_not_mutable_tag(self):
        requested = []
        responses = [
            tag_response(target=ANNOTATED_TAG_OBJECT),
            tree_response([tree_item("README.md")]),
        ]

        def opener(request, timeout):
            requested.append(request.full_url)
            return responses.pop(0)

        acquire_esrm20_scenario_tree_metadata(
            opener=opener,
            now=lambda: "2026-08-15T17:35:00Z",
            monotonic=lambda: 0.0,
        )

        self.assertEqual(requested[0], TAG_API_URL)
        self.assertEqual(requested[1], _tree_url(COMMIT, 1))
        self.assertIn(f"ref={COMMIT}", requested[1])
        self.assertNotIn("ref=v1.0", requested[1])

    def test_wrong_tag_identity_fails_closed(self):
        with self.assertRaisesRegex(EfehrAcquisitionError, "trusted v1.0"):
            acquire_esrm20_scenario_tree_metadata(
                opener=lambda request, timeout: tag_response(name="v1.1"),
                now=lambda: "2026-08-15T17:35:00Z",
                monotonic=lambda: 0.0,
            )

    def test_malformed_tag_target_object_fails_before_tree_request(self):
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls != 1:
                raise AssertionError("tree request must not occur after invalid tag target")
            return tag_response(target="not-a-git-object")

        with self.assertRaisesRegex(EfehrAcquisitionError, "target object id"):
            acquire_esrm20_scenario_tree_metadata(
                opener=opener,
                now=lambda: "2026-08-15T17:35:00Z",
                monotonic=lambda: 0.0,
            )
        self.assertEqual(calls, 1)

    def test_short_or_uppercase_commit_fails_closed_before_tree_request(self):
        for commit in ("a" * 39, "A" * 40):
            with self.subTest(commit=commit):
                with self.assertRaisesRegex(
                    EfehrAcquisitionError, "full lowercase commit SHA"
                ):
                    acquire_esrm20_scenario_tree_metadata(
                        opener=lambda request, timeout, commit=commit: tag_response(
                            commit
                        ),
                        now=lambda: "2026-08-15T17:35:00Z",
                        monotonic=lambda: 0.0,
                    )

    def test_noncanonical_or_malformed_tree_entries_fail_closed(self):
        cases = [
            tree_item("../escape.xml"),
            tree_item("/absolute.xml"),
            tree_item("dir\\file.xml"),
            tree_item("file.xml", object_id="d" * 39),
        ]
        for item in cases:
            with self.subTest(item=item):
                responses = [tag_response(), tree_response([item])]
                with self.assertRaises(EfehrAcquisitionError):
                    acquire_esrm20_scenario_tree_metadata(
                        opener=lambda request, timeout: responses.pop(0),
                        now=lambda: "2026-08-15T17:35:00Z",
                        monotonic=lambda: 0.0,
                    )

    def test_tree_type_mode_semantics_fail_closed(self):
        cases = (
            tree_item("wrong-tree", entry_type="tree", mode="100644"),
            tree_item("wrong-blob", entry_type="blob", mode="040000"),
            tree_item("symlink", entry_type="blob", mode="120000"),
        )
        for item in cases:
            with self.subTest(item=item):
                responses = [tag_response(), tree_response([item])]
                with self.assertRaisesRegex(EfehrAcquisitionError, "type/mode"):
                    acquire_esrm20_scenario_tree_metadata(
                        opener=lambda request, timeout: responses.pop(0),
                        now=lambda: "2026-08-15T17:35:00Z",
                        monotonic=lambda: 0.0,
                    )

    def test_duplicate_tree_path_fails_closed(self):
        item = tree_item("scenario/job.ini")
        responses = [tag_response(), tree_response([item, dict(item)])]
        with self.assertRaisesRegex(EfehrAcquisitionError, "duplicate/conflicting"):
            acquire_esrm20_scenario_tree_metadata(
                opener=lambda request, timeout: responses.pop(0),
                now=lambda: "2026-08-15T17:35:00Z",
                monotonic=lambda: 0.0,
            )

    def test_duplicate_json_key_fails_closed(self):
        raw = (
            b'[{"id":"'
            + b"b" * 40
            + b'","name":"README.md","type":"blob","path":"README.md",'
            + b'"path":"other.md","mode":"100644"}]'
        )
        response = FakeResponse(None, _tree_url(COMMIT, 1), raw=raw)
        response.headers.update(
            {
                "X-Page": "1",
                "X-Per-Page": str(TREE_PER_PAGE),
                "X-Next-Page": "",
            }
        )
        responses = [tag_response(), response]
        with self.assertRaisesRegex(EfehrAcquisitionError, "duplicate scenario-tree"):
            acquire_esrm20_scenario_tree_metadata(
                opener=lambda request, timeout: responses.pop(0),
                now=lambda: "2026-08-15T17:35:00Z",
                monotonic=lambda: 0.0,
            )

    def test_pagination_cannot_skip_a_page(self):
        response = tree_response([tree_item("README.md")], next_page="3")
        responses = [tag_response(), response]
        with self.assertRaisesRegex(EfehrAcquisitionError, "contiguous"):
            acquire_esrm20_scenario_tree_metadata(
                opener=lambda request, timeout: responses.pop(0),
                now=lambda: "2026-08-15T17:35:00Z",
                monotonic=lambda: 0.0,
            )

    def test_missing_pagination_headers_fail_closed(self):
        for header in ("X-Page", "X-Per-Page", "X-Next-Page"):
            with self.subTest(header=header):
                response = tree_response([tree_item("README.md")])
                response.headers.pop(header)
                responses = [tag_response(), response]
                with self.assertRaisesRegex(
                    EfehrAcquisitionError,
                    "pagination headers are incomplete",
                ):
                    acquire_esrm20_scenario_tree_metadata(
                        opener=lambda request, timeout: responses.pop(0),
                        now=lambda: "2026-08-15T17:35:00Z",
                        monotonic=lambda: 0.0,
                    )

    def test_aggregate_metadata_byte_bound_includes_tag_response(self):
        tag = tag_response()
        tree = tree_response([tree_item("README.md")])
        responses = [tag, tree]
        with patch.object(
            scenario_metadata,
            "_CANONICAL_MAX_TOTAL_METADATA_BYTES",
            len(tree._payload),
        ):
            with self.assertRaisesRegex(
                EfehrAcquisitionError,
                "aggregate total byte bound",
            ):
                acquire_esrm20_scenario_tree_metadata(
                    opener=lambda request, timeout: responses.pop(0),
                    now=lambda: "2026-08-15T17:35:00Z",
                    monotonic=lambda: 0.0,
                )


if __name__ == "__main__":
    unittest.main()
