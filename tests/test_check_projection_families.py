# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import check_projection_families as guard

ROOT = Path(__file__).resolve().parents[1]


class ProjectionFamilyGuardTests(unittest.TestCase):
    def _root(self, temporary_path: str) -> Path:
        root = Path(temporary_path)
        (root / "scripts").mkdir()
        (root / "scripts/render_public_views.py").write_text("pass\n", encoding="utf-8")
        (root / "scripts/schema_reference.py").write_text("pass\n", encoding="utf-8")
        return root

    def _pair(self, root: Path, relative_json: str) -> None:
        json_path = root / relative_json
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text("{}\n", encoding="utf-8")
        json_path.with_suffix(".md").write_text("generated\n", encoding="utf-8")

    def test_current_repository_inventory_is_fully_registered(self) -> None:
        errors, count = guard.check_inventory(ROOT)
        self.assertEqual(errors, [])
        self.assertGreater(count, 0)

    def test_registered_families_accept_exact_same_basename_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._pair(root, "access/example.json")
            self._pair(root, "manifests/example.json")
            self._pair(root, "landscape/sources-example.json")
            self._pair(root, "schemas/example.schema.json")
            errors, count = guard.check_inventory(root)
            self.assertEqual(errors, [])
            self.assertEqual(count, 4)

    def test_six_named_research_snapshots_are_not_fake_projection_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            for relative, schema in guard.RESEARCH_ONLY_STANDALONE_JSON_SCHEMAS.items():
                p = root / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                if schema == "__SOURCE_DOWNLOAD_RECEIPT_ROWS__":
                    data = [{"file": "synthetic.nc", "url": "https://example.invalid/synthetic.nc",
                             "bytes": 10, "sha256": "a" * 64, "status": "downloaded"}]
                else:
                    data = {"schema": schema}
                p.write_text(json.dumps(data) + "\n", encoding="utf-8")
            errors, count = guard.check_inventory(root)
            self.assertEqual(errors, [])
            self.assertEqual(count, 6)

    def test_named_download_receipt_rejects_fake_sha_or_disallowed_url(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            p = root / "research/observations/xws_downloads_20261115.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            for row in (
                {"file": "x.nc", "url": "http://example.invalid/x.nc",
                 "bytes": 10, "sha256": "a" * 64, "status": "downloaded"},
                {"file": "x.nc", "url": "https://example.invalid/x.nc",
                 "bytes": 10, "sha256": "not-a-digest", "status": "downloaded"},
                {"file": "x.nc", "url": "https://example.invalid/x.nc",
                 "bytes": True, "sha256": "a" * 64, "status": "downloaded"},
            ):
                with self.subTest(row=row):
                    p.write_text(json.dumps([row]) + "\n", encoding="utf-8")
                    errors, count = guard.check_inventory(root)
                    self.assertEqual(count, 1)
                    self.assertTrue(any("receipt mismatch" in error for error in errors))

    def test_named_research_snapshot_schema_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            p = root / "research/observations/knmi_wind_metadata_review.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('{"schema": "WRONG"}\n', encoding="utf-8")
            errors, count = guard.check_inventory(root)
            self.assertEqual(count, 1)
            self.assertTrue(any("schema mismatch" in error for error in errors))

    def test_unlisted_research_json_stays_unregistered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._pair(root, "research/observations/new_unreviewed.json")
            errors, _ = guard.check_inventory(root)
            self.assertTrue(any("unregistered JSON projection family" in error for error in errors))

    def test_unknown_family_fails_even_with_handwritten_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._pair(root, "new-family/example.json")
            errors, count = guard.check_inventory(root)
            self.assertEqual(count, 1)
            self.assertTrue(any("unregistered JSON projection family" in error for error in errors))

    def test_registered_json_without_projection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            path = root / "access/example.json"
            path.parent.mkdir()
            path.write_text("{}\n", encoding="utf-8")
            errors, count = guard.check_inventory(root)
            self.assertEqual(count, 1)
            self.assertTrue(any("lacks same-basename Markdown projection" in error for error in errors))

    def test_nested_or_misnamed_json_does_not_expand_a_family_implicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._pair(root, "access/nested/example.json")
            self._pair(root, "landscape/example.json")
            errors, count = guard.check_inventory(root)
            self.assertEqual(count, 2)
            self.assertEqual(
                sum("unregistered JSON projection family" in error for error in errors),
                2,
            )

    def test_missing_registered_checker_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            self._pair(root, "access/example.json")
            (root / "scripts/render_public_views.py").unlink()
            errors, _ = guard.check_inventory(root)
            self.assertTrue(any("has no checker" in error for error in errors))

    def test_shared_checker_commands_are_deduplicated(self) -> None:
        self.assertEqual(
            guard.checker_commands(),
            (
                ("scripts/render_public_views.py", "--check"),
                ("scripts/schema_reference.py", "--check"),
            ),
        )


if __name__ == "__main__":
    unittest.main()
