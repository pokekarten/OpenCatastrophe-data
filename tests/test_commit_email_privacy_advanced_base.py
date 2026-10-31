# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline Git regression for pull_request_target privacy workflow after base moves."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_git(path, *args):
    return subprocess.run(["git", *args], cwd=path, capture_output=True,
                          text=True, check=True).stdout.strip()


def trusted_fetch_script(remote):
    workflow = (ROOT / ".github/workflows/commit-email-privacy.yml").read_text()
    marker = "      - name: Fetch trusted base and candidate commit objects\n        run: |\n"
    end = "\n      - name: Check candidate commit metadata with trusted base code\n"
    if workflow.count(marker) != 1 or end not in workflow.split(marker)[1]:
        raise AssertionError("trusted privacy workflow steps not found")
    block = workflow.split(marker, 1)[1].split(end, 1)[0].rstrip().splitlines()
    if not block or any(not line.startswith("          ") for line in block):
        raise AssertionError("malformed trusted YAML shell block")
    shell = "\n".join(line[10:] for line in block) + "\n"
    expected = 'git remote add origin "https://github.com/' + "$" + '{GITHUB_REPOSITORY}.git"'
    if shell.count(expected) != 1:
        raise AssertionError("unexpected trusted remote")
    return shell.replace(expected, f'git remote add origin "{remote}"')


class AdvancedMainPrivacyWorkflowTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src = self.root / "source"
        self.remote = self.root / "remote.git"
        self.checkout = self.root / "checkout"
        self.src.mkdir()
        self.checkout.mkdir()
        run_git(self.src, "init", "-b", "main", ".")
        run_git(self.src, "config", "user.name", "Synthetic Git Test")
        run_git(self.src, "config", "user.email", "tester@users.noreply.github.com")
        (self.src / "scripts").mkdir()
        shutil.copyfile(ROOT / "scripts/check_commit_email_privacy.py",
                        self.src / "scripts/check_commit_email_privacy.py")
        (self.src / "README.md").write_text("trusted original\n")
        run_git(self.src, "add", ".")
        run_git(self.src, "commit", "-m", "base")
        self.base = run_git(self.src, "rev-parse", "HEAD")
        run_git(self.src, "switch", "-c", "feature")
        (self.src / "feature.md").write_text("candidate\n")
        run_git(self.src, "add", ".")
        run_git(self.src, "commit", "-m", "candidate")
        self.head = run_git(self.src, "rev-parse", "HEAD")
        run_git(self.src, "switch", "main")
        (self.src / "README.md").write_text("new main tip\n")
        run_git(self.src, "add", ".")
        run_git(self.src, "commit", "-m", "main advanced")
        self.new_tip = run_git(self.src, "rev-parse", "HEAD")
        run_git(self.root, "init", "--bare", str(self.remote))
        run_git(self.src, "remote", "add", "origin", str(self.remote))
        run_git(self.src, "push", "origin", "main:refs/heads/main",
                "feature:refs/pull/1/head")

    def execute_workflow(self, *, base=None, head=None):
        env = dict(os.environ)
        env.update({
            "BASE_REF": "main",
            "BASE_SHA": base or self.base,
            "HEAD_SHA": head or self.head,
            "PR_NUMBER": "1",
            "GITHUB_WORKSPACE": str(self.checkout),
            "GIT_CONFIG_GLOBAL": str(self.root / "isolated-gitconfig"),
        })
        return subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c",
             trusted_fetch_script(self.remote)],
            cwd=self.checkout, env=env, capture_output=True, text=True)

    def test_advanced_main_preserves_original_trusted_base(self):
        self.assertNotEqual(self.base, self.new_tip)
        actual = self.execute_workflow()
        self.assertEqual(actual.returncode, 0, actual.stderr)
        self.assertEqual(run_git(self.checkout, "rev-parse", "HEAD"), self.base)
        checked = subprocess.run(
            ["python3", "scripts/check_commit_email_privacy.py",
             self.base, self.head],
            cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("PASS:", checked.stdout)

    def test_valid_unrelated_base_is_rejected(self):
        # PR head is fetched, but it is not an ancestor of advancing main.
        result = self.execute_workflow(base=self.head)
        self.assertNotEqual(result.returncode, 0)

    def test_changed_head_digest_is_rejected(self):
        result = self.execute_workflow(head=self.base)
        self.assertNotEqual(result.returncode, 0)

    def test_script_uses_ancestry_and_event_pinned_checkout(self):
        script = trusted_fetch_script(self.remote)
        self.assertIn("git merge-base --is-ancestor", script)
        self.assertIn('git checkout --detach "' + "$" + '{BASE_SHA}"', script)
        self.assertNotIn("refs/remotes/origin/privacy-base)", script)


if __name__ == "__main__":
    unittest.main()
