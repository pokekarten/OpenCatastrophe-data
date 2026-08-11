# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-public-views.yml"


class PublicViewWorkflowSecurityTests(unittest.TestCase):
    def test_branch_validation_is_read_only_and_check_only(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read\n", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("actions: write", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("persist-credentials: true", text)

        self.assertIn(
            "python scripts/render_public_views.py --check --scope all",
            text,
        )
        self.assertNotIn(
            "python scripts/render_public_views.py --write --scope all",
            text,
        )
        self.assertNotIn("git push", text)
        self.assertNotIn("gh workflow run", text)
        self.assertNotIn("git commit", text)

    def test_workflow_never_exposes_a_write_capability(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        forbidden = (
            "write-all",
            "contents: write",
            "actions: write",
            "pull-requests: write",
            "issues: write",
            "id-token: write",
        )
        for capability in forbidden:
            with self.subTest(capability=capability):
                self.assertNotIn(capability, text)


if __name__ == "__main__":
    unittest.main()
