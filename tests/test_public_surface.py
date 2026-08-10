# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicSurfaceTests(unittest.TestCase):
    def test_no_private_or_retired_project_references_in_tracked_text(self) -> None:
        forbidden = ("private-archive", "FFBK", "Rim-", "OpenCAT-data")
        for path in self._text_files():
            if path == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path, token=token):
                    self.assertNotIn(token, text)

    def test_workflow_actions_are_exactly_pinned(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        uses = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
        checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
        setup_python = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
        dependency_review = "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294"
        allowed = {checkout, setup_python, dependency_review}
        self.assertEqual(len(uses), 8)
        self.assertTrue(all(item in allowed for item in uses))
        self.assertEqual(uses.count(checkout), 4)
        self.assertEqual(uses.count(setup_python), 3)
        self.assertEqual(uses.count(dependency_review), 1)

    def test_workflow_is_read_only_and_has_stable_required_job(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("name: Required", workflow)
        self.assertIn("needs: [check, glofas-acquisition, reuse, dependency-review]", workflow)
        self.assertIn("GLOFAS_ACQUISITION_RESULT", workflow)
        self.assertNotIn("pull_request_target", workflow)

    def _text_files(self) -> list[Path]:
        result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, check=True)
        paths = []
        for raw in result.stdout.split(b"\0"):
            if not raw:
                continue
            path = ROOT / raw.decode("utf-8")
            if path.suffix.lower() not in {".txt"} and path.name in {"LICENSE"}:
                continue
            try:
                path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            paths.append(path)
        return paths


if __name__ == "__main__":
    unittest.main()
