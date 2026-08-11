# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SYNC_WORKFLOW = WORKFLOWS / "sync-public-views.yml"
CHECK_ALL = ROOT / "scripts" / "check_all.py"


class PublicViewWorkflowSecurityTests(unittest.TestCase):
    def test_branch_controlled_sync_workflow_is_not_present(self):
        self.assertFalse(
            SYNC_WORKFLOW.exists(),
            "public-view generation must not be performed by a branch-controlled write workflow",
        )

    def test_definition_of_done_checks_public_views_fail_closed(self):
        text = CHECK_ALL.read_text(encoding="utf-8")
        self.assertIn('"scripts/render_public_views.py", "--check"', text)

    def test_any_workflow_using_renderer_is_read_only_and_check_only(self):
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow.read_text(encoding="utf-8")
            if "render_public_views.py" not in text:
                continue
            with self.subTest(workflow=workflow.name):
                self.assertNotIn("contents: write", text)
                self.assertNotIn("actions: write", text)
                self.assertNotIn("persist-credentials: true", text)
                self.assertNotIn("render_public_views.py --write", text)
                self.assertIn("render_public_views.py --check", text)


if __name__ == "__main__":
    unittest.main()
