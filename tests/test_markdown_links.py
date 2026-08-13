# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_markdown_links.py"
SPEC = importlib.util.spec_from_file_location("check_markdown_links", MODULE_PATH)
assert SPEC and SPEC.loader
links = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = links
SPEC.loader.exec_module(links)


class MarkdownLinkTests(unittest.TestCase):
    def _root(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def _check(self, root: Path, source_relative: str, markdown: str) -> list[str]:
        source = root / source_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(markdown, encoding="utf-8")
        return links.check_markdown_file(source, root=root)

    def test_existing_relative_file_target_passes(self) -> None:
        root = self._root()
        (root / "docs").mkdir()
        (root / "docs" / "target.md").write_text("# Target\n", encoding="utf-8")
        self.assertEqual(self._check(root, "docs/source.md", "[target](target.md)\n"), [])

    def test_existing_root_relative_target_passes(self) -> None:
        root = self._root()
        (root / "README.md").write_text("# Root\n", encoding="utf-8")
        self.assertEqual(self._check(root, "docs/source.md", "[root](/README.md)\n"), [])

    def test_missing_local_target_fails(self) -> None:
        root = self._root()
        problems = self._check(root, "docs/source.md", "[missing](missing.md)\n")
        self.assertEqual(problems, ["missing repository-local target: missing.md"])

    def test_external_and_fragment_only_links_are_skipped(self) -> None:
        root = self._root()
        markdown = "[web](https://example.invalid/path)\n[section](#section)\n"
        self.assertEqual(self._check(root, "docs/source.md", markdown), [])

    def test_parent_traversal_inside_repository_passes(self) -> None:
        root = self._root()
        (root / "README.md").write_text("# Root\n", encoding="utf-8")
        self.assertEqual(self._check(root, "docs/source.md", "[root](../README.md)\n"), [])

    def test_parent_traversal_outside_repository_fails_closed(self) -> None:
        root = self._root()
        problems = self._check(root, "docs/source.md", "[escape](../../outside.md)\n")
        self.assertEqual(
            problems,
            ["repository-local target escapes repository root: ../../outside.md"],
        )

    def test_percent_encoded_local_path_is_decoded(self) -> None:
        root = self._root()
        (root / "docs").mkdir()
        (root / "docs" / "space name.md").write_text("# Target\n", encoding="utf-8")
        self.assertEqual(
            self._check(root, "docs/source.md", "[target](space%20name.md)\n"),
            [],
        )

    def test_fenced_inline_code_and_html_comments_do_not_create_false_links(self) -> None:
        root = self._root()
        markdown = (
            "`[literal](missing-inline.md)`\n"
            "```md\n[example](missing-fenced.md)\n```\n"
            "<!-- [commented](missing-commented.md) -->\n"
        )
        self.assertEqual(self._check(root, "docs/source.md", markdown), [])

    def test_fence_with_info_string_inside_block_is_not_a_closer(self) -> None:
        root = self._root()
        markdown = (
            "```md\n"
            "```python\n"
            "[literal](missing-inside.md)\n"
            "```\n"
            "[real](missing-after.md)\n"
        )
        self.assertEqual(
            self._check(root, "docs/source.md", markdown),
            ["missing repository-local target: missing-after.md"],
        )

    def test_reference_definition_target_is_checked(self) -> None:
        root = self._root()
        problems = self._check(
            root,
            "docs/source.md",
            "[target][missing]\n\n[missing]: missing-reference.md\n",
        )
        self.assertEqual(
            problems,
            ["missing repository-local target: missing-reference.md"],
        )


if __name__ == "__main__":
    unittest.main()
