# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/esrm20-project278-manual-content-profile.yml"


class Project278ManualContentProfileWorkflowTests(unittest.TestCase):
    def test_workflow_is_trusted_main_fixed_target_and_publishes_no_raw_text(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 291", text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("Checkout trusted default branch", text)
        self.assertIn("Checkout exact trusted execution commit", text)
        self.assertIn("--require-hashes -r requirements-project278-pdf-profile.txt", text)
        self.assertIn("Prove complete issue-local dedup before provider access", text)
        self.assertIn('LATEST_SHA="$(gh api', text)
        self.assertIn('.manual_identity.project_id == 278', text)
        self.assertIn('.manual_identity.byte_count == 2121105', text)
        self.assertIn('.content_profile.raw_text_exposed == false', text)
        self.assertIn(".publication_authorized == false", text)
        self.assertNotIn("pull_request:", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
