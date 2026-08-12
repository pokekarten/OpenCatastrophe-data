# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

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
