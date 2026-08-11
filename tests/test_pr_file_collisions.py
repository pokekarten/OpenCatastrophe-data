# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_pr_file_collisions.py"
SPEC = importlib.util.spec_from_file_location("check_pr_file_collisions", MODULE_PATH)
assert SPEC and SPEC.loader
collisions = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = collisions
SPEC.loader.exec_module(collisions)


class PaginationTests(unittest.TestCase):
    def test_full_page_is_followed_until_short_page(self) -> None:
        pages = {
            1: [{"number": index + 1} for index in range(collisions.PER_PAGE)],
            2: [{"number": 101}],
        }
        result = collisions.collect_paginated(
            lambda page: pages[page],
            max_pages=3,
            label="fixture",
        )
        self.assertEqual(len(result), 101)
        self.assertEqual(result[-1], {"number": 101})

    def test_completeness_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(collisions.CollisionCheckError, "completeness limit"):
            collisions.collect_paginated(
                lambda _page: [{} for _ in range(collisions.PER_PAGE)],
                max_pages=2,
                label="fixture",
            )

    def test_non_array_page_fails_closed(self) -> None:
        with self.assertRaisesRegex(collisions.CollisionCheckError, "must be a JSON array"):
            collisions.collect_paginated(
                lambda _page: {"unexpected": True},
                max_pages=1,
                label="fixture",
            )


class GithubShapeTests(unittest.TestCase):
    def test_repository_and_api_url_are_strict(self) -> None:
        self.assertEqual(collisions.require_repository("pokekarten/OpenCatastrophe-data"), "pokekarten/OpenCatastrophe-data")
        self.assertEqual(collisions.require_api_url("https://api.github.com/"), "https://api.github.com")
        for value in ("pokekarten", " pokekarten/OpenCatastrophe-data", "https://github.com/pokekarten/OpenCatastrophe-data"):
            with self.subTest(value=value), self.assertRaises(collisions.CollisionCheckError):
                collisions.require_repository(value)
        for value in (
            "http://api.github.com",
            "https://api.github.com?token=bad",
            "https://api.github.com#fragment",
            "https://api.github.com/v3",
            "https://api.github.com:443",
            "https://user:pass@api.github.com",
            "https://example.invalid",
            "api.github.com",
        ):
            with self.subTest(value=value), self.assertRaises(collisions.CollisionCheckError):
                collisions.require_api_url(value)

    def test_event_payload_requires_pull_request_number(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"pull_request": {"number": 87}}), encoding="utf-8")
            self.assertEqual(collisions.read_event_pull_request_number(path), 87)
            path.write_text(json.dumps({"pull_request": {"number": True}}), encoding="utf-8")
            with self.assertRaisesRegex(collisions.CollisionCheckError, "positive integer"):
                collisions.read_event_pull_request_number(path)

    def test_open_pull_requests_are_paginated_and_unique(self) -> None:
        seen: list[str] = []

        def fake_get_json(url: str, *, token: str) -> object:
            self.assertEqual(token, "fixture-token")
            seen.append(url)
            return [{"number": 9}, {"number": 3}] if "page=1" in url else []

        result = collisions.list_open_pull_request_numbers(
            "pokekarten/OpenCatastrophe-data",
            api_url="https://api.github.com",
            token="fixture-token",
            get_json=fake_get_json,
        )
        self.assertEqual(result, (3, 9))
        self.assertEqual(len(seen), 1)
        self.assertIn("state=open", seen[0])
        self.assertIn("per_page=100", seen[0])

    def test_duplicate_open_pull_request_numbers_fail_closed(self) -> None:
        def fake_get_json(_url: str, *, token: str) -> object:
            self.assertEqual(token, "fixture-token")
            return [{"number": 9}, {"number": 9}]

        with self.assertRaisesRegex(collisions.CollisionCheckError, "duplicate"):
            collisions.list_open_pull_request_numbers(
                "pokekarten/OpenCatastrophe-data",
                api_url="https://api.github.com",
                token="fixture-token",
                get_json=fake_get_json,
            )

    def test_renamed_file_claims_old_and_new_paths(self) -> None:
        def fake_get_json(_url: str, *, token: str) -> object:
            self.assertEqual(token, "fixture-token")
            return [
                {
                    "filename": "docs/new-name.md",
                    "previous_filename": "docs/old-name.md",
                },
                {"filename": "scripts/new.py"},
            ]

        result = collisions.list_pull_request_file_surfaces(
            "pokekarten/OpenCatastrophe-data",
            12,
            api_url="https://api.github.com",
            token="fixture-token",
            get_json=fake_get_json,
        )
        self.assertEqual(
            result,
            frozenset({"docs/new-name.md", "docs/old-name.md", "scripts/new.py"}),
        )

    def test_invalid_changed_file_record_fails_closed(self) -> None:
        def fake_get_json(_url: str, *, token: str) -> object:
            self.assertEqual(token, "fixture-token")
            return [{"filename": " valid.md "}]

        with self.assertRaisesRegex(collisions.CollisionCheckError, "trimmed path"):
            collisions.list_pull_request_file_surfaces(
                "pokekarten/OpenCatastrophe-data",
                12,
                api_url="https://api.github.com",
                token="fixture-token",
                get_json=fake_get_json,
            )


class CollisionDetectionTests(unittest.TestCase):
    def test_exact_overlap_blocks_and_current_pr_is_not_compared_to_itself(self) -> None:
        surfaces = {
            10: frozenset({"scripts/a.py", "tests/test_a.py"}),
            11: frozenset({"docs/independent.md"}),
            12: frozenset({"tests/test_a.py", "scripts/b.py"}),
        }
        loaded: list[int] = []

        def load(number: int) -> frozenset[str]:
            loaded.append(number)
            return surfaces[number]

        current, overlap = collisions.find_collisions(10, (10, 11, 12), load)
        self.assertEqual(current, surfaces[10])
        self.assertEqual(overlap, {12: ("tests/test_a.py",)})
        self.assertEqual(loaded.count(10), 1)

    def test_independent_prs_pass(self) -> None:
        surfaces = {
            20: frozenset({"scripts/collision.py"}),
            21: frozenset({"scripts/hydrology.py"}),
        }
        current, overlap = collisions.find_collisions(20, (20, 21), surfaces.__getitem__)
        self.assertEqual(current, surfaces[20])
        self.assertEqual(overlap, {})

    def test_duplicate_open_pr_numbers_fail_closed(self) -> None:
        with self.assertRaisesRegex(collisions.CollisionCheckError, "duplicates"):
            collisions.find_collisions(
                20,
                (20, 21, 21),
                lambda _number: frozenset(),
            )

    def test_surface_loader_contract_fails_closed(self) -> None:
        with self.assertRaisesRegex(collisions.CollisionCheckError, "frozenset"):
            collisions.find_collisions(
                20,
                (20,),
                lambda _number: {"scripts/a.py"},  # type: ignore[return-value]
            )


if __name__ == "__main__":
    unittest.main()
