# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicSurfaceTests(unittest.TestCase):
    def test_no_private_history_or_retired_project_references(self) -> None:
        forbidden = ("private-archive", "FFBK", "Rim-", "RIM", "OpenCAT-data")
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
        self.assertEqual(len(uses), 4)
        allowed = {
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        }
        self.assertTrue(all(item in allowed for item in uses))
        self.assertEqual(uses.count("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"), 2)
        self.assertEqual(uses.count("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"), 2)

    def test_workflow_is_read_only_and_has_stable_required_job(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("name: Required", workflow)
        self.assertNotIn("pull_request_target", workflow)

    def test_public_tree_has_no_high_risk_payload_files(self) -> None:
        result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True)
        blocked = {".csv", ".parquet", ".zip", ".pdf", ".xlsx", ".sqlite", ".geojson"}
        for name in result.stdout.splitlines():
            with self.subTest(path=name):
                self.assertNotIn(Path(name).suffix.lower(), blocked)

    def test_scoped_agent_instructions_are_present(self) -> None:
        for relative, required in (
            ("manifests/AGENTS.md", "source-rights scope"),
            ("schemas/AGENTS.md", "durable machine contract"),
        ):
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            text = path.read_text(encoding="utf-8").lower()
            self.assertIn(required, text)
            self.assertIn("python scripts/check_all.py", text)

    def test_agent_skills_are_provider_neutral_and_fail_closed(self) -> None:
        for relative in (
            ".github/skills/dataset-admission/SKILL.md",
            ".github/skills/reproducibility-run/SKILL.md",
        ):
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            text = path.read_text(encoding="utf-8").lower()
            self.assertIn("license: apache-2.0", text)
            self.assertIn("python scripts/check_all.py", text)
            self.assertNotIn("target: github-copilot", text)
            self.assertNotIn("private repository", text)

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
