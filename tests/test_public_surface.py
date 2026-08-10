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
        workflow_files = self._workflow_files()
        self.assertTrue(workflow_files, "at least one tracked GitHub Actions workflow is expected")
        uses = []
        for path in workflow_files:
            workflow = path.read_text(encoding="utf-8")
            for item in re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE):
                uses.append((path.relative_to(ROOT).as_posix(), item))

        checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
        setup_python = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
        dependency_review = "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294"
        allowed = {checkout, setup_python, dependency_review}

        for workflow_path, item in uses:
            with self.subTest(workflow=workflow_path, uses=item):
                self.assertRegex(item, r"^[^@\s]+@[0-9a-f]{40}$")
                self.assertIn(item, allowed)

    def test_workflow_is_read_only_and_has_stable_required_job(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("name: Required", workflow)
        self.assertIn(
            "needs: [check, glofas-acquisition, reuse, dependency-review]",
            workflow,
        )
        self.assertIn("GLOFAS_ACQUISITION_RESULT", workflow)
        self.assertNotIn("PR_FILE_COLLISIONS_RESULT", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("GITHUB_TOKEN", workflow)
        self.assertNotIn("check_pr_file_collisions.py", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*(?:contents|pull-requests|issues|actions):\s*write\s*$")

    def test_pr_collision_workflow_is_metadata_only_base_trusted_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github/workflows/pr-file-collision.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("permissions:\n  contents: read\n  pull-requests: read", workflow)
        self.assertIn("name: PR file collision check", workflow)
        trusted_checkout = """      - name: Checkout trusted default branch
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: ${{ github.event.repository.default_branch }}
          fetch-depth: 1
          persist-credentials: false
"""
        self.assertIn(trusted_checkout, workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)
        self.assertEqual(
            re.findall(r"^\s*run:\s*(.+)$", workflow, flags=re.MULTILINE),
            ["python scripts/check_pr_file_collisions.py"],
        )
        for forbidden in (
            "github.event.pull_request.head",
            "github.head_ref",
            "refs/pull/",
            "allow-unsafe-pr-checkout",
            "github.workflow_sha",
            "secrets.",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*(?:contents|pull-requests|issues|actions):\s*write\s*$")

    def _workflow_files(self) -> list[Path]:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", ".github/workflows"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        )
        paths = []
        for raw in result.stdout.split(b"\0"):
            if not raw:
                continue
            relative = Path(raw.decode("utf-8"))
            if relative.suffix.lower() in {".yml", ".yaml"}:
                paths.append(ROOT / relative)
        return sorted(paths)

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
